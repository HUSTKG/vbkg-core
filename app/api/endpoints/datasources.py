from typing import Annotated, Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Query, Path
from pydantic import parse_obj_as
import json

from app.api.deps import get_current_user, PermissionChecker 
from app.schemas.datasource import (
    DataSource, 
    DataSourceCreate, 
    DataSourceUpdate, 
    SourceType,
    FileUpload,
    FileUploadStatus
)
from app.services.datasource import DataSourceService

router = APIRouter()

check_read_permission = PermissionChecker("datasource:read")
check_write_permission = PermissionChecker("datasource:write")


@router.post("/", response_model=DataSource, status_code=status.HTTP_201_CREATED)
async def create_datasource(
    datasource_in: DataSourceCreate,
    current_user: Annotated[Dict[str, Any], Depends(check_write_permission)],
) -> Any:
    """
    Create new data source.
    """
    datasource_service = DataSourceService()
    return await datasource_service.create_datasource(
        datasource_in=datasource_in,
        user_id=current_user["id"]
    )


@router.get("/", response_model=List[DataSource])
async def read_datasources(
    skip: int = 0,
    limit: int = 100,
    source_type: Optional[SourceType] = None,
    is_active: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Retrieve data sources with filtering options.
    """
    datasource_service = DataSourceService()
    return await datasource_service.get_datasources(
        skip=skip,
        limit=limit,
        source_type=source_type.value if source_type else None,
        is_active=is_active
    )


@router.get("/{datasource_id}", response_model=DataSource)
async def read_datasource(
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Get specific data source by ID.
    """
    datasource_service = DataSourceService()
    return await datasource_service.get_datasource(datasource_id=datasource_id)


@router.patch("/{datasource_id}", response_model=DataSource)
async def update_datasource(
    datasource_in: DataSourceUpdate,
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Update a data source.
    """
    datasource_service = DataSourceService()
    return await datasource_service.update_datasource(
        datasource_id=datasource_id,
        datasource_in=datasource_in
    )


@router.delete("/{datasource_id}", response_model=Dict[str, Any])
async def delete_datasource(
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Delete a data source.
    """
    datasource_service = DataSourceService()
    return await datasource_service.delete_datasource(datasource_id=datasource_id)


@router.post("/{datasource_id}/upload", response_model=FileUpload, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Upload a file to a data source.
    """
    datasource_service = DataSourceService()
    
    # Parse metadata if provided
    metadata_dict = {}
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid metadata JSON format"
            )
    
    return await datasource_service.upload_file(
        file=file,
        data_source_id=datasource_id,
        user_id=current_user["id"],
        metadata=metadata_dict
    )


@router.get("/files", response_model=List[FileUpload])
async def read_file_uploads(
    datasource_id: Optional[str] = None,
    status: Optional[FileUploadStatus] = None,
    processed: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Retrieve file uploads with filtering options.
    """
    datasource_service = DataSourceService()
    return await datasource_service.get_file_uploads(
        data_source_id=datasource_id,
        processed=processed,
        skip=skip,
        limit=limit
    )


@router.get("/files/{file_id}", response_model=FileUpload)
async def read_file_upload(
    file_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Get specific file upload by ID.
    """
    datasource_service = DataSourceService()
    return await datasource_service.get_file_upload(file_upload_id=file_id)


@router.patch("/files/{file_id}/status", response_model=FileUpload)
async def update_file_status(
    status: FileUploadStatus,
    processed: Optional[bool] = None,
    error_message: Optional[str] = None,
    file_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Update status of a file upload.
    """
    datasource_service = DataSourceService()
    return await datasource_service.update_file_status(
        file_upload_id=file_id,
        fileStatus=status,
        processed=processed,
        error_message=error_message
    )


@router.delete("/files/{file_id}", response_model=Dict[str, Any])
async def delete_file_upload(
    file_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Delete a file upload.
    """
    datasource_service = DataSourceService()
    return await datasource_service.delete_file_upload(file_upload_id=file_id)


@router.get("/files/{file_id}/content")
async def get_file_content(
    file_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Get the content of a file.
    """
    datasource_service = DataSourceService()
    
    # Get file info to determine content type
    file_info = await datasource_service.get_file_upload(file_upload_id=file_id)
    content = await datasource_service.get_file_content(file_upload_id=file_id)
    
    # Return file content with appropriate content type
    from fastapi.responses import Response
    return Response(
        content=content,
        media_type=file_info.get("file_type", "application/octet-stream")
    )
