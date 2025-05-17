import json
from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, UploadFile
from fastapi import status as HttpStatus

from app.api.deps import PermissionChecker
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.datasource import (
    DataSource,
    DataSourceCreate,
    DataSourceUpdate,
    SourceType,
)
from app.schemas.file_upload import FileUpload, FileUploadStatus
from app.schemas.user import User
from app.services.datasource import DataSourceService

router = APIRouter()

check_read_permission = PermissionChecker("datasource:read")
check_write_permission = PermissionChecker("datasource:write")


@router.post(
    "", response_model=ApiResponse[DataSource], status_code=HttpStatus.HTTP_201_CREATED
)
async def create_datasource(
    datasource_in: DataSourceCreate,
    current_user: Annotated[User, Depends(check_write_permission)],
) -> ApiResponse[DataSource]:
    """
    Create new data source.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.create_datasource(
        datasource_in=datasource_in, user_id=current_user.id
    )
    return ApiResponse(
        data=DataSource(**response),
        status=HttpStatus.HTTP_201_CREATED,
        message="Data source created successfully",
    )


@router.get("", response_model=PaginatedResponse[Dict[str, Any]])
async def read_datasources(
    skip: int = 0,
    limit: int = 100,
    source_type: Optional[SourceType] = None,
    is_active: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[Dict[str, Any]]:
    """
    Retrieve data sources with filtering options.
    """

    datasource_service = DataSourceService()

    response = await datasource_service.get_datasources(
        skip=skip,
        limit=limit,
        source_type=source_type.value if source_type else None,
        is_active=is_active,
    )

    return PaginatedResponse(
        data=response.data,
        meta=PaginatedMeta(
            total=response.count if response.count else 0,
            skip=skip,
            limit=limit,
        ),
        message="Data sources retrieved successfully",
        status=HttpStatus.HTTP_200_OK,
    )


@router.get("/{datasource_id}", response_model=ApiResponse[DataSource])
async def read_datasource(
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[DataSource]:
    """
    Get specific data source by ID.
    """
    datasource_service = DataSourceService()

    response = await datasource_service.get_datasource(datasource_id=datasource_id)

    return ApiResponse(
        data=DataSource(**response),
        status=HttpStatus.HTTP_200_OK,
        message="Data source retrieved successfully",
    )


@router.patch("/{datasource_id}", response_model=ApiResponse[DataSource])
async def update_datasource(
    datasource_in: DataSourceUpdate,
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[DataSource]:
    """
    Update a data source.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.update_datasource(
        datasource_id=datasource_id, datasource_in=datasource_in
    )
    return ApiResponse(
        data=DataSource(**response),
        status=HttpStatus.HTTP_200_OK,
        message="Data source updated successfully",
    )


@router.delete("/{datasource_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_datasource(
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete a data source.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.delete_datasource(datasource_id=datasource_id)

    return ApiResponse(
        data=response,
        status=HttpStatus.HTTP_200_OK,
        message="Data source deleted successfully",
    )


@router.post(
    "/{datasource_id}/upload",
    response_model=ApiResponse[FileUpload],
    status_code=HttpStatus.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[FileUpload]:
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
                status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                detail="Invalid metadata JSON format",
            )

    response = await datasource_service.upload_file(
        file=file,
        data_source_id=datasource_id,
        user_id=current_user["id"],
        metadata=metadata_dict,
    )

    return ApiResponse(
        data=FileUpload(**response),
        message="File uploaded successfully",
        status=HttpStatus.HTTP_201_CREATED,
    )


@router.get("/files", response_model=PaginatedResponse[FileUpload])
async def read_file_uploads(
    datasource_id: Optional[str] = None,
    status: Optional[FileUploadStatus] = None,
    processed: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[FileUpload]:
    """
    Retrieve file uploads with filtering options.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.get_file_uploads(
        data_source_id=datasource_id,
        processed=processed,
        _status=status,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse(
        data=[FileUpload(**data) for data in response.data],
        meta=PaginatedMeta(
            total=response.count if response.count else 0,
            skip=skip,
            limit=limit,
        ),
        message="File uploads retrieved successfully",
        status=HttpStatus.HTTP_200_OK,
    )


@router.get("/files/{file_id}", response_model=ApiResponse[FileUpload])
async def read_file_upload(
    file_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[FileUpload]:
    """
    Get specific file upload by ID.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.get_file_upload(file_upload_id=file_id)

    return ApiResponse(
        data=FileUpload(**response),
        status=HttpStatus.HTTP_200_OK,
        message="File upload retrieved successfully",
    )


@router.patch("/files/{file_id}/status", response_model=ApiResponse[FileUpload])
async def update_file_status(
    status: FileUploadStatus,
    processed: Optional[bool] = None,
    error_message: Optional[str] = None,
    file_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[FileUpload]:
    """
    Update status of a file upload.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.update_file_status(
        file_upload_id=file_id,
        fileStatus=status,
        processed=processed,
        error_message=error_message,
    )
    return ApiResponse(
        data=FileUpload(**response),
        status=HttpStatus.HTTP_200_OK,
        message="File upload status updated successfully",
    )


@router.delete("/files/{file_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_file_upload(
    file_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete a file upload.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.delete_file_upload(file_upload_id=file_id)
    return ApiResponse(
        data=response,
        status=HttpStatus.HTTP_200_OK,
        message="File upload deleted successfully",
    )


@router.get("/files/{file_id}/content")
async def get_file_content(
    file_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission),
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
        media_type=file_info.get("file_type", "application/octet-stream"),
    )
