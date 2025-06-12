import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.supabase import get_supabase
from app.utils.file_processor import process_file

logger = logging.getLogger(__name__)


async def ingest_file(
    file_id: Optional[str],
    file_name: str,
    datasource_id: UUID,
) -> Optional[Dict[str, Any]]:
    """
    Ingest a file into the system.

    Args:
        file_id: File upload id
        file_name: Original file name
        datasource_id: ID of the data source
        process_immediately: Whether to process the file immediately

    Returns:
        File record or None if ingestion failed
    """
    try:
        from app.services.file_upload import UploadService

        file_service = UploadService()
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


        file_record = await supabase.table("file_uploads").update({"upload_status": "pending"}).eq(
            "id", file_id 
        ).execute()

        text_content = await process_file(UUID(file_id))

        file_record = file_record.data[0] if file_record.data else None

        file_record = {
                "id": file_id,
                "file_name": file_name,
                "datasource_id": str(datasource_id),
                "upload_status": "processed",
                "text_content": text_content,
        }

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

        from app.services.file_upload import UploadService

        supabase = await get_supabase()

        upload_service = UploadService()

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
            now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            file_name = f"api_data_{now}.{data_format}"
            temp_path = os.path.join(os.getcwd(), "temp", file_name)

            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            with open(temp_path, "wb") as f:
                f.write(response.content)

            # store in supabase storage and update the file_uploads
            upload_response = await upload_service.upload_file(
                file=response.content,
                file_name=file_name,
                file_type=data_format,
                datasource_id=str(datasource_id),
                user_id=str(user_id),
                metadata={
                    "source_url": api_url,
                    "content_length": len(response.content),
                    "http_status": response.status_code,
                    "headers": dict(response.headers),
                },
            )

            # Ingest the file
            return await ingest_file(
                file_id=upload_response["id"],
                file_name=file_name,
                datasource_id=datasource_id,
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
        import pandas as pd
        import sqlalchemy
        from sqlalchemy import create_engine, text

        from app.services.file_upload import UploadService

        upload_service = UploadService()

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
            now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            file_name = f"db_export_{now}.{output_format}"
            temp_path = os.path.join(os.getcwd(), "temp", file_name)

            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            if output_format == "csv":
                df.to_csv(temp_path, index=False)
                content_type = "text/csv"
            elif output_format == "parquet":
                df.to_parquet(temp_path, index=False)
                content_type = "application/parquet"
            else:
                df.to_json(temp_path, orient="records")
                content_type = "application/json"

            # read file
            with open(temp_path, "rb") as f:
                file_content = f.read()

            # store in supabase storage and update the file_uploads
            upload_response = await upload_service.upload_file(
                file=file_content,
                file_name=file_name,
                file_type=content_type,
                datasource_id=str(datasource_id),
                user_id=str(user_id),
                metadata={
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "columns": df.columns.tolist(),
                    "query": query,
                },
            )

            # Ingest the file
            return await ingest_file(
                file_id=upload_response["id"],
                file_name=file_name,
                datasource_id=datasource_id,
            )

    except Exception as e:
        logger.error(f"Error ingesting database data with query {query}: {str(e)}")
        return None
