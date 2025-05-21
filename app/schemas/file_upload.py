from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class FileUploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileUploadBase(BaseModel):
    """Model for file upload data."""

    data_source_id: Optional[str] = None
    file_name: str = Field(..., description="Name of the file")
    file_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., description="Size of the file in bytes")
    storage_path: str


class FileUpload(FileUploadBase):
    """Complete file upload model returned from API."""

    id: str = Field(..., description="Unique identifier for the file upload")

    storage_path: str = Field(..., description="Path where the file is stored")
    upload_status: FileUploadStatus = Field(
        FileUploadStatus.PENDING, description="Status of the file upload"
    )
    processed: bool = Field(False, description="Whether the file has been processed")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata about the file"
    )
    uploaded_by: Optional[str] = Field(
        None, description="ID of the user who uploaded the file"
    )
    uploaded_at: datetime = Field(
        ..., description="Timestamp when the file was uploaded"
    )

    class Config:
        from_attributes = True


class FileUploadCreate(FileUploadBase):
    """Model for creating a new file upload."""

    metadata: dict = Field(
        default_factory=dict, description="Additional metadata about the file"
    )
    uploaded_by: str = Field(..., description="ID of the user who uploaded the file")


class FileUploadUpdate(BaseModel):
    """Model for updating an existing file upload."""

    file_name: Optional[str] = ""
    upload_status: Optional[FileUploadStatus] = None
    processed: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = None
