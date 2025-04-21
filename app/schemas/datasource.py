from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class SourceType(str, Enum):
    FILE = "file"
    API = "api"
    DATABASE = "database"
    URL = "url"


class ConnectionConfig(BaseModel):
    """Base model for connection details that will be extended by specific source types"""
    pass


class FileConnectionConfig(ConnectionConfig):
    """Configuration for file data sources"""
    file_path: Optional[str] = None
    file_format: str = Field(..., description="Format of the file (e.g., csv, json, txt, pdf)")
    encoding: str = "utf-8"
    delimiter: Optional[str] = None  # For CSV files


class ApiConnectionConfig(ConnectionConfig):
    """Configuration for API data sources"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    query_params: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None


class DatabaseConnectionConfig(ConnectionConfig):
    """Configuration for database data sources"""
    host: str
    port: int
    database: str
    username: str
    password: Optional[str] = None
    db_type: str = Field(..., description="Type of database (e.g., postgres, mysql, mssql)")
    ssl: bool = False
    query: Optional[str] = None
    table: Optional[str] = None


class UrlConnectionConfig(ConnectionConfig):
    """Configuration for URL data sources"""
    url: str
    scrape_config: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None


class DataSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_type: SourceType
    connection_details: Dict[str, Any] = Field(..., description="Connection details specific to the source type")
    
    @field_validator('connection_details')
    def validate_connection_details(cls, v, values):
        source_type = values.get('source_type')
        if source_type == SourceType.FILE:
            FileConnectionConfig(**v)
        elif source_type == SourceType.API:
            ApiConnectionConfig(**v)
        elif source_type == SourceType.DATABASE:
            DatabaseConnectionConfig(**v)
        elif source_type == SourceType.URL:
            UrlConnectionConfig(**v)
        return v


class DataSourceCreate(DataSourceBase):
    credentials: Optional[Dict[str, Any]] = None


class DataSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    connection_details: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DataSource(DataSourceBase):
    id: str
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FileUploadBase(BaseModel):
    data_source_id: str
    file_name: str
    file_type: str
    file_size: int
    storage_path: str


class FileUploadCreate(FileUploadBase):
    metadata: Optional[Dict[str, Any]] = None


class FileUploadStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileUpload(FileUploadBase):
    id: str
    upload_status: FileUploadStatus = FileUploadStatus.PENDING
    processed: bool = False
    metadata: Optional[Dict[str, Any]] = None
    uploaded_by: Optional[str] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True
