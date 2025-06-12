import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import pandas as pd
from storage3.types import FileOptions

from app.core.supabase import get_supabase
from app.utils.file_handler import FileHandler, parse_file_content

logger = logging.getLogger(__name__)


class FileProcessor:
    """Enhanced file processor with type-based storage strategy"""

    def __init__(self):
        self.file_processor = FileHandler()

        # Define file type categories
        self.structured_types = {
            "text/csv",
            "application/json",
            "application/xml",
            "text/xml",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # Excel
            "application/vnd.ms-excel",
        }

        self.unstructured_types = {
            "text/plain",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # Word
            "application/msword",
            "text/html",
            "text/markdown",
        }

    def is_structured_file(self, content_type: str) -> bool:
        """Check if file contains structured data"""
        return content_type in self.structured_types

    def is_unstructured_file(self, content_type: str) -> bool:
        """Check if file contains unstructured data"""
        return content_type in self.unstructured_types

    async def process_structured_file(
        self, file_path: str, content_type: str
    ) -> Dict[str, Any]:
        """Process structured file and convert to Parquet"""

        try:
            # Process file to get structured data
            result = await self.file_processor.process_file(file_path, content_type)

            if not result.get("success"):
                raise Exception(f"Failed to process file: {result.get('error')}")

            content = result["content"]

            # Convert to DataFrame based on file type
            if content_type == "text/csv":
                df = self._csv_to_dataframe(content)
            elif content_type in ["application/json"]:
                df = self._json_to_dataframe(content)
            elif content_type in ["application/xml", "text/xml"]:
                df = self._xml_to_dataframe(content)
            elif "spreadsheet" in content_type:  # Excel
                df = self._excel_to_dataframe(content)
            else:
                raise Exception(f"Unsupported structured type: {content_type}")

            # Save as Parquet
            temp_parquet_path = file_path.replace(Path(file_path).suffix, ".parquet")
            df.to_parquet(temp_parquet_path, index=False, engine="pyarrow")

            return {
                "success": True,
                "storage_format": "parquet",
                "parquet_path": temp_parquet_path,
                "dataframe_info": {
                    "shape": df.shape,
                    "columns": df.columns.tolist(),
                    "dtypes": df.dtypes.to_dict(),
                    "memory_usage": df.memory_usage(deep=True).sum(),
                },
                "original_content": content,
            }

        except Exception as e:
            logger.error(f"Error processing structured file {file_path}: {e}")
            return {"success": False, "error": str(e)}

    async def process_unstructured_file(
        self, file_path: str, content_type: str
    ) -> Dict[str, Any]:
        """Process unstructured file and extract text"""

        try:
            # Extract text content
            text_content = await parse_file_content(file_path, content_type)

            if not text_content:
                raise Exception("No text content extracted")

            # Save as text file
            temp_text_path = file_path.replace(Path(file_path).suffix, ".txt")
            with open(temp_text_path, "w", encoding="utf-8") as f:
                f.write(text_content)

            return {
                "success": True,
                "storage_format": "text",
                "text_path": temp_text_path,
                "text_info": {
                    "char_count": len(text_content),
                    "word_count": len(text_content.split()),
                    "line_count": text_content.count("\n") + 1,
                },
                "text_content": text_content,
            }

        except Exception as e:
            logger.error(f"Error processing unstructured file {file_path}: {e}")
            return {"success": False, "error": str(e)}

    def _csv_to_dataframe(self, content: Dict[str, Any]) -> pd.DataFrame:
        """Convert CSV content to DataFrame"""

        headers = content.get("headers", [])
        rows = content.get("sample_rows", [])  # Use all rows in real implementation

        if not headers or not rows:
            raise Exception("No valid CSV data found")

        # Create DataFrame
        df = pd.DataFrame(rows, columns=headers)

        # Infer data types
        df = df.infer_objects()

        return df

    def _json_to_dataframe(self, content: Dict[str, Any]) -> pd.DataFrame:
        """Convert JSON content to DataFrame"""

        json_data = content.get("json_data")

        if isinstance(json_data, list):
            # Array of objects
            df = pd.DataFrame(json_data)
        elif isinstance(json_data, dict):
            # Single object or nested structure
            if all(isinstance(v, (list, dict)) for v in json_data.values()):
                # Nested structure - flatten
                df = pd.json_normalize(json_data)
            else:
                # Simple object
                df = pd.DataFrame([json_data])
        else:
            raise Exception("Unsupported JSON structure for DataFrame conversion")

        return df

    def _xml_to_dataframe(self, content: Dict[str, Any]) -> pd.DataFrame:
        """Convert XML content to DataFrame"""

        # For XML, we'll create a simple structure
        # In practice, you might want more sophisticated XML parsing

        text_content = content.get("text", "")
        lines = [line.strip() for line in text_content.split("\n") if line.strip()]

        # Create simple DataFrame from XML text representation
        data = []
        for i, line in enumerate(lines):
            data.append({"line_number": i + 1, "content": line})

        return pd.DataFrame(data)

    def _excel_to_dataframe(self, content: Dict[str, Any]) -> pd.DataFrame:
        """Convert Excel content to DataFrame"""

        # This is a simplified version
        # In practice, you'd want to handle multiple sheets

        text_content = content.get("text", "")
        lines = [line.strip() for line in text_content.split("\n") if line.strip()]

        # Parse sheet data (simplified)
        data = []
        current_sheet = None

        for line in lines:
            if line.startswith("Sheet:"):
                current_sheet = line.replace("Sheet:", "").strip()
                continue

            if "|" in line:
                row_data = [cell.strip() for cell in line.split("|")]
                data.append({"sheet": current_sheet, "row_data": "|".join(row_data)})

        return pd.DataFrame(data)


async def process_file(file_id: UUID) -> str:
    """
    Enhanced file processing with type-based storage strategy.

    Args:
        file_id: ID of the file to process

    Returns:
        True if processing was successful, False otherwise
    """

    supabase = await get_supabase()

    try:
        processor = FileProcessor()

        # Get file information
        response = (
            await supabase.table("file_uploads")
            .select("*")
            .eq("id", str(file_id))
            .execute()
        )

        if not response.data:
            logger.error(f"File {file_id} not found")
            raise FileNotFoundError(f"File {file_id} not found")

        file_info = response.data[0]

        # Update status to processing
        await supabase.table("file_uploads").update({"upload_status": "processing"}).eq(
            "id", str(file_id)
        ).execute()

        # Download file from current storage (S3 or local)
        storage_path = file_info["storage_path"]
        local_path = await download_file_from_current_storage(storage_path)

        if not local_path or not os.path.exists(local_path):
            logger.error(f"Failed to download file: {storage_path}")
            await update_file_status(
                supabase, file_id, "failed", "Failed to download file"
            )
            raise FileNotFoundError(f"Failed to download file: {storage_path}")

        # Determine processing strategy based on file type
        content_type = file_info["file_type"]

        if processor.is_structured_file(content_type):
            # Process structured file → Parquet
            result = await processor.process_structured_file(local_path, content_type)

            if not result["success"]:
                await update_file_status(
                    supabase, file_id, "failed", result.get("error")
                )
                raise Exception(
                    f"Failed to process structured file: {result.get('error')}"
                )

            # Upload Parquet to Supabase Storage
            parquet_path = result["parquet_path"]
            storage_url = await supabase.storage.from_("vbkg").upload(
                path=f"structured/{file_id}.parquet",
                file=parquet_path,
            )

            # Store DataFrame metadata
            metadata = {
                **file_info.get("metadata", {}),
                "processing_type": "structured",
                "storage_format": "parquet",
                "dataframe_info": result["dataframe_info"],
                "processed_at": datetime.now().isoformat(),
            }

        elif processor.is_unstructured_file(content_type):
            # Process unstructured file → Text
            result = await processor.process_unstructured_file(local_path, content_type)

            if not result["success"]:
                await update_file_status(
                    supabase, file_id, "failed", result.get("error")
                )
                raise Exception(
                    f"Failed to process unstructured file: {result.get('error')}"
                )

            # Upload text to Supabase Storage
            text_path = result["text_path"]
            is_exist = await supabase.storage.from_("vbkg").exists(
                path=f"unstructured/{file_id}.txt"
            )
            if is_exist:
                storage_url = await supabase.storage.from_("vbkg").update(
                    path=f"unstructured/{file_id}.txt",
                    file=text_path,
                )
            else:
                storage_url = await supabase.storage.from_("vbkg").upload(
                    path=f"unstructured/{file_id}.txt",
                    file=text_path,
                )

            # Store text metadata
            metadata = {
                **file_info.get("metadata", {}),
                "processing_type": "unstructured",
                "storage_format": "text",
                "text_info": result["text_info"],
                "processed_at": datetime.now().isoformat(),
            }

        else:
            await update_file_status(
                supabase, file_id, "failed", f"Unsupported file type: {content_type}"
            )
            raise Exception(f"Unsupported file type: {content_type}")

        # Update file record with new storage info
        await supabase.table("file_uploads").update(
            {
                "upload_status": "completed",
                "processed": True,
                "processed_storage_path": storage_url.path,
                "metadata": metadata,
            }
        ).eq("id", str(file_id)).execute()

        # Cleanup temp files
        cleanup_files([local_path, result.get("parquet_path"), result.get("text_path")])

        logger.info(
            f"Successfully processed file {file_id} as {metadata['processing_type']}"
        )
        return result["text_content"]

    except Exception as e:
        logger.error(f"Error processing file {file_id}: {str(e)}")
        await update_file_status(supabase, file_id, "failed", str(e))
        raise Exception(f"Error processing file {file_id}: {str(e)}")


async def download_file_from_current_storage(storage_path: str) -> Optional[str]:
    """Download file from current storage location"""

    try:
        supabase = await get_supabase()
        # Download file from Supabase Storage
        file_content = await supabase.storage.from_("vbkg").download(path=storage_path)
        if not file_content:
            logger.error(f"File {storage_path} not found in storage")
            return None
        local_path = f"/tmp/{Path(storage_path).name}"
        with open(local_path, "wb") as f:
            f.write(file_content)
        return local_path
    except Exception as e:
        logger.error(f"Error downloading file {storage_path}: {e}")
        return None


async def update_file_status(
    supabase, file_id: UUID, status: str, error: Optional[str] = None
):
    """Update file processing status"""

    update_data: Dict[str, Any] = {"upload_status": status}

    if error:
        update_data["metadata"] = {
            "error": error,
            "failed_at": datetime.now().isoformat(),
        }

    await supabase.table("file_uploads").update(update_data).eq(
        "id", str(file_id)
    ).execute()


def cleanup_files(file_paths: List[Optional[str]]):
    """Cleanup temporary files"""

    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup file {file_path}: {e}")


async def load_processed_dataframe(file_id: UUID) -> Optional[pd.DataFrame]:
    """Load processed structured data as DataFrame"""

    try:
        supabase = await get_supabase()

        # Get file info
        response = (
            await supabase.table("file_uploads")
            .select("*")
            .eq("id", str(file_id))
            .execute()
        )

        if not response.data:
            return None

        file_info = response.data[0]
        metadata = file_info.get("metadata", {})

        if metadata.get("processing_type") != "structured":
            logger.warning(f"File {file_id} is not structured data")
            return None

        # Download parquet file
        storage_path = file_info["storage_path"]
        file_content = await supabase.storage.from_("vbkg").download(path=storage_path)

        local_path = f"/tmp/{file_id}.parquet"

        with open(local_path, "wb") as f:
            f.write(file_content)

        if not local_path:
            return None

        # Load DataFrame
        df = pd.read_parquet(local_path)

        # Cleanup
        if os.path.exists(local_path):
            os.remove(local_path)

        return df

    except Exception as e:
        logger.error(f"Error loading DataFrame for file {file_id}: {e}")
        return None


async def load_processed_text(file_id: UUID) -> Optional[str]:
    """Load processed text content"""

    try:
        supabase = await get_supabase()

        # Get file info
        response = (
            await supabase.table("file_uploads")
            .select("*")
            .eq("id", str(file_id))
            .execute()
        )

        if not response.data:
            return None

        file_info = response.data[0]
        metadata = file_info.get("metadata", {})

        if metadata.get("processing_type") != "unstructured":
            logger.warning(f"File {file_id} is not unstructured data")
            return None

        # Download text file
        storage_path = file_info["storage_path"]
        file_content = await supabase.storage.from_("vbkg").download(path=storage_path)

        local_path = f"/tmp/{file_id}.parquet"

        with open(local_path, "wb") as f:
            f.write(file_content)

        if not local_path:
            return None

        # Read text content
        with open(local_path, "r", encoding="utf-8") as f:
            text_content = f.read()

        # Cleanup
        if os.path.exists(local_path):
            os.remove(local_path)

        return text_content

    except Exception as e:
        logger.error(f"Error loading text for file {file_id}: {e}")
        return None
