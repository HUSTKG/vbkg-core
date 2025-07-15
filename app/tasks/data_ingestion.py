import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from app.core.supabase import get_supabase
from app.tasks.executors import StepLogger
from app.utils.file_processor import process_file


class DataIngestionTask:
    """Task for handling various data ingestion operations"""

    def __init__(self, logger: StepLogger):
        self.logger = logger

    async def ingest_file(
        self,
        file_id: Optional[str],
        file_name: str,
        datasource_id: UUID,
        encoding: str = "utf-8",
        extract_metadata: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Ingest a file into the system.

        Args:
            file_id: File upload id
            file_name: Original file name
            datasource_id: ID of the data source
            encoding: File encoding
            extract_metadata: Whether to extract metadata

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
                await self.logger.error(f"Data source {datasource_id} not found")
                return None

            # Update file status to pending
            file_record = (
                await supabase.table("file_uploads")
                .update({"upload_status": "pending"})
                .eq("id", file_id)
                .execute()
            )

            # Process file content
            text_content = await process_file(UUID(file_id))

            file_record = file_record.data[0] if file_record.data else None

            # Create file record
            file_record = {
                "id": file_id,
                "file_name": file_name,
                "datasource_id": str(datasource_id),
                "upload_status": "processed",
                "text_content": text_content,
                "encoding": encoding,
                "metadata": {
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "content_length": len(text_content) if text_content else 0,
                },
            }

            await self.logger.info(f"Successfully ingested file {file_name}")
            return file_record

        except Exception as e:
            await self.logger.error(f"Error ingesting file {file_name}: {str(e)}")
            return None

    async def ingest_multiple_files(
        self,
        datasource_id: UUID,
        encoding: str = "utf-8",
        extract_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest multiple files from a data source.

        Args:
            datasource_id: ID of the data source
            encoding: File encoding
            extract_metadata: Whether to extract metadata

        Returns:
            Dictionary with ingestion results
        """
        try:
            from app.services.file_upload import UploadService

            upload_service = UploadService()

            await self.logger.info(
                f"Starting file ingestion for data source {datasource_id}"
            )

            # Get file uploads for the data source
            file_uploads = await upload_service.get_file_uploads(
                data_source_id=datasource_id
            )

            await self.logger.info(
                f"Retrieved {len(file_uploads.data)} file uploads for data source {datasource_id}"
            )

            processed_files = []
            failed_files = []

            # Process each file
            for file in file_uploads.data:
                try:
                    file_record = await self.ingest_file(
                        file_id=file["id"],
                        file_name=file["file_name"],
                        datasource_id=datasource_id,
                        encoding=encoding,
                        extract_metadata=extract_metadata,
                    )

                    if file_record:
                        processed_files.append(file_record)
                        await self.logger.info(
                            f"Successfully processed file {file['file_name']}"
                        )
                    else:
                        failed_files.append(
                            {
                                "file_id": file["id"],
                                "file_name": file["file_name"],
                                "error": "Processing failed",
                            }
                        )

                except Exception as e:
                    await self.logger.error(
                        f"Error processing file {file['file_name']}: {e}"
                    )
                    failed_files.append(
                        {
                            "file_id": file["id"],
                            "file_name": file["file_name"],
                            "error": str(e),
                        }
                    )

            return {
                "processed_files": processed_files,
                "failed_files": failed_files,
                "total_files": len(file_uploads.data),
                "successful_files": len(processed_files),
                "failed_count": len(failed_files),
                "metadata": {
                    "ingestion_time": datetime.now(timezone.utc).isoformat(),
                    "datasource_id": str(datasource_id),
                },
            }

        except Exception as e:
            await self.logger.error(f"Error in multiple file ingestion: {str(e)}")
            return {
                "processed_files": [],
                "failed_files": [],
                "total_files": 0,
                "successful_files": 0,
                "failed_count": 0,
                "error": str(e),
            }

    async def ingest_api_data(
        self,
        api_url: str,
        data_format: str,
        datasource_id: UUID,
        user_id: Optional[UUID] = None,
        auth_params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
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
                await self.logger.error(f"Data source {datasource_id} not found")
                return None

            # Make API request
            async with httpx.AsyncClient(timeout=30.0) as client:
                request_headers = headers or {}
                request_params = query_params or {}

                # Add authentication if provided
                if auth_params:
                    self._add_authentication(
                        client, request_headers, request_params, auth_params
                    )

                # Make the request
                response = await client.get(
                    api_url, headers=request_headers, params=request_params
                )

                # Check response
                if not response.is_success:
                    await self.logger.error(
                        f"API request failed: {response.status_code} - {response.text}"
                    )
                    return None

                # Save response content to a temporary file
                now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                file_name = f"api_data_{now}.{data_format}"

                # Store in supabase storage
                upload_response = await upload_service.upload_file(
                    file=response.content,
                    file_name=file_name,
                    file_type=data_format,
                    datasource_id=str(datasource_id),
                    user_id=str(user_id) if user_id else None,
                    metadata={
                        "source_url": api_url,
                        "content_length": len(response.content),
                        "http_status": response.status_code,
                        "headers": dict(response.headers),
                    },
                )

                # Ingest the file
                return await self.ingest_file(
                    file_id=upload_response["id"],
                    file_name=file_name,
                    datasource_id=datasource_id,
                )

        except Exception as e:
            await self.logger.error(
                f"Error ingesting API data from {api_url}: {str(e)}"
            )
            return None

    async def ingest_database_data(
        self,
        connection_string: str,
        query: str,
        datasource_id: UUID,
        user_id: Optional[UUID] = None,
        output_format: str = "csv",
    ) -> Optional[Dict[str, Any]]:
        """
        Ingest data from a database.

        Args:
            connection_string: Database connection string
            query: SQL query to execute
            datasource_id: ID of the data source
            user_id: ID of the user initiating the ingestion
            output_format: Format to save the data (csv, json)

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
                await self.logger.error(f"Data source {datasource_id} not found")
                return None

            # Create engine and execute query
            engine = create_engine(connection_string)

            with engine.connect() as connection:
                result = connection.execute(text(query))
                df = pd.DataFrame(result.fetchall(), columns=result.keys())

                # Save to file
                now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                file_name = f"db_export_{now}.{output_format}"
                temp_path = os.path.join(os.getcwd(), "temp", file_name)

                os.makedirs(os.path.dirname(temp_path), exist_ok=True)

                # Save data in specified format
                content_type = self._save_dataframe(df, temp_path, output_format)

                # Read file content
                with open(temp_path, "rb") as f:
                    file_content = f.read()

                # Store in supabase storage
                upload_response = await upload_service.upload_file(
                    file=file_content,
                    file_name=file_name,
                    file_type=content_type,
                    datasource_id=str(datasource_id),
                    user_id=str(user_id) if user_id else None,
                    metadata={
                        "row_count": len(df),
                        "column_count": len(df.columns),
                        "columns": df.columns.tolist(),
                        "query": query,
                    },
                )

                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

                # Ingest the file
                return await self.ingest_file(
                    file_id=upload_response["id"],
                    file_name=file_name,
                    datasource_id=datasource_id,
                )

        except Exception as e:
            await self.logger.error(
                f"Error ingesting database data with query {query}: {str(e)}"
            )
            return None

    def _add_authentication(
        self,
        client: "httpx.AsyncClient",
        headers: Dict[str, str],
        params: Dict[str, Any],
        auth_params: Dict[str, Any],
    ) -> None:
        """Add authentication to the HTTP client"""
        auth_type = auth_params.get("type", "").lower()

        if auth_type == "basic":
            client.auth = (
                auth_params.get("username", ""),
                auth_params.get("password", ""),
            )
        elif auth_type == "bearer":
            headers["Authorization"] = f"Bearer {auth_params.get('token', '')}"
        elif auth_type == "api_key":
            key_name = auth_params.get("key_name", "api_key")
            key_value = auth_params.get("key_value", "")

            if auth_params.get("in_header", True):
                headers[key_name] = key_value
            else:
                params[key_name] = key_value

    def _save_dataframe(
        self, df: "pd.DataFrame", file_path: str, output_format: str
    ) -> str:
        """Save dataframe in the specified format"""
        if output_format == "csv":
            df.to_csv(file_path, index=False)
            return "text/csv"
        elif output_format == "parquet":
            df.to_parquet(file_path, index=False)
            return "application/parquet"
        else:  # json
            df.to_json(file_path, orient="records")
            return "application/json"
