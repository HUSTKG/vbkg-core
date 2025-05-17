import logging
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
import os
import json
from datetime import datetime
import asyncio

from app.core.supabase import get_supabase
from app.utils.s3 import upload_file_to_s3
from app.utils.file_handler import save_upload_file
from app.tasks.extraction import process_file

logger = logging.getLogger(__name__)


async def ingest_file(
    file_path: str,
    file_name: str,
    content_type: str,
    datasource_id: UUID,
    user_id: Optional[UUID] = None,
    metadata: Optional[Dict[str, Any]] = None,
    process_immediately: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Ingest a file into the system.

    Args:
        file_path: Path to the local file
        file_name: Original file name
        content_type: MIME type of the file
        datasource_id: ID of the data source
        user_id: ID of the user uploading the file
        metadata: Additional metadata
        process_immediately: Whether to process the file immediately

    Returns:
        File record or None if ingestion failed
    """
    try:
        supabase = await get_supabase()

        # Check if data source exists
        response = (
            await supabase.table("data_sources")
            .select("*")
            .eq("id", str(datasource_id))
            .execute()
        )

        if not response.data:
            logger.error(f"Data source {datasource_id} not found")
            return None

        # Calculate file size
        file_size = os.path.getsize(file_path)

        # Upload to S3
        s3_object_name = f"uploads/{datasource_id}/{file_name}"
        s3_path = await upload_file_to_s3(
            file_path=file_path,
            bucket_name="knowledge-graph-files",
            object_name=s3_object_name,
        )

        if not s3_path:
            logger.error(f"Failed to upload file to S3: {file_path}")
            return None

        # Create file upload record
        file_data = {
            "data_source_id": str(datasource_id),
            "file_name": file_name,
            "file_type": content_type,
            "file_size": file_size,
            "storage_path": s3_path,
            "upload_status": "pending" if process_immediately else "uploaded",
            "processed": False,
            "metadata": metadata or {},
            "uploaded_by": str(user_id) if user_id else None,
        }

        response = await supabase.table("file_uploads").insert(file_data).execute()

        if not response.data:
            logger.error(f"Failed to create file upload record for {file_name}")
            return None

        file_record = response.data[0]

        # Process file immediately if requested
        if process_immediately:
            # Update status
            await supabase.table("file_uploads").update({"upload_status": "queued"}).eq(
                "id", file_record["id"]
            ).execute()

            # Start processing
            asyncio.create_task(process_file(UUID(file_record["id"])))

        return file_record

    except Exception as e:
        logger.error(f"Error ingesting file {file_name}: {str(e)}")
        return None


async def ingest_api_data(
    api_url: str,
    data_format: str,
    datasource_id: UUID,
    user_id: Optional[UUID] = None,
    auth_params: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    process_immediately: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Ingest data from an API.

    Args:
        api_url: URL of the API
        data_format: Format of the data (json, xml, etc.)
        datasource_id: ID of the data source
        user_id: ID of the user initiating the ingestion
        auth_params: Authentication parameters
        query_params: Query parameters
        headers: Request headers
        process_immediately: Whether to process the data immediately

    Returns:
        Data record or None if ingestion failed
    """
    try:
        import httpx

        supabase = await get_supabase()

        # Check if data source exists
        response = (
            await supabase.table("data_sources")
            .select("*")
            .eq("id", str(datasource_id))
            .execute()
        )

        if not response.data:
            logger.error(f"Data source {datasource_id} not found")
            return None

        # Make API request
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Prepare request
            request_headers = headers or {}
            request_params = query_params or {}

            # Add authentication if provided
            if auth_params:
                auth_type = auth_params.get("type", "").lower()

                if auth_type == "basic":
                    client.auth = (
                        auth_params.get("username", ""),
                        auth_params.get("password", ""),
                    )

                elif auth_type == "bearer":
                    request_headers["Authorization"] = (
                        f"Bearer {auth_params.get('token', '')}"
                    )

                elif auth_type == "api_key":
                    key_name = auth_params.get("key_name", "api_key")
                    key_value = auth_params.get("key_value", "")

                    if auth_params.get("in_header", True):
                        request_headers[key_name] = key_value
                    else:
                        request_params[key_name] = key_value

            # Make the request
            response = await client.get(
                api_url, headers=request_headers, params=request_params
            )

            # Check response
            if not response.is_success:
                logger.error(
                    f"API request failed: {response.status_code} - {response.text}"
                )
                return None

            # Save response content to a temporary file
            now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            file_name = f"api_data_{now}.{data_format}"
            temp_path = os.path.join(os.getcwd(), "temp", file_name)

            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            with open(temp_path, "wb") as f:
                f.write(response.content)

            # Ingest the file
            return await ingest_file(
                file_path=temp_path,
                file_name=file_name,
                content_type=f"application/{data_format}",
                datasource_id=datasource_id,
                user_id=user_id,
                metadata={
                    "source_url": api_url,
                    "content_length": len(response.content),
                    "http_status": response.status_code,
                    "headers": dict(response.headers),
                },
                process_immediately=process_immediately,
            )

    except Exception as e:
        logger.error(f"Error ingesting API data from {api_url}: {str(e)}")
        return None


async def ingest_database_data(
    connection_string: str,
    query: str,
    datasource_id: UUID,
    user_id: Optional[UUID] = None,
    output_format: str = "csv",
    process_immediately: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Ingest data from a database.

    Args:
        connection_string: Database connection string
        query: SQL query to execute
        datasource_id: ID of the data source
        user_id: ID of the user initiating the ingestion
        output_format: Format to save the data (csv, json)
        process_immediately: Whether to process the data immediately

    Returns:
        Data record or None if ingestion failed
    """
    try:
        import sqlalchemy
        import pandas as pd
        from sqlalchemy import create_engine, text

        supabase = await get_supabase()

        # Check if data source exists
        response = (
            await supabase.table("data_sources")
            .select("*")
            .eq("id", str(datasource_id))
            .execute()
        )

        if not response.data:
            logger.error(f"Data source {datasource_id} not found")
            return None

        # Create engine
        engine = create_engine(connection_string)

        # Execute query
        with engine.connect() as connection:
            result = connection.execute(text(query))

            # Convert to DataFrame
            df = pd.DataFrame(result.fetchall(), columns=result.keys())

            # Save to file
            now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            file_name = f"db_export_{now}.{output_format}"
            temp_path = os.path.join(os.getcwd(), "temp", file_name)

            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            if output_format == "csv":
                df.to_csv(temp_path, index=False)
                content_type = "text/csv"
            else:
                df.to_json(temp_path, orient="records")
                content_type = "application/json"

            # Ingest the file
            return await ingest_file(
                file_path=temp_path,
                file_name=file_name,
                content_type=content_type,
                datasource_id=datasource_id,
                user_id=user_id,
                metadata={
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "query": query,
                },
                process_immediately=process_immediately,
            )

    except Exception as e:
        logger.error(f"Error ingesting database data with query {query}: {str(e)}")
        return None
