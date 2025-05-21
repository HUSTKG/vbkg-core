import json

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Path,
                     UploadFile)
from fastapi import status as HttpStatus
from gotrue import Any, Dict, Optional

from app.api.deps import get_current_user
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.file_upload import FileUpload, FileUploadStatus
from app.services.file_upload import UploadService

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse[FileUpload],
    status_code=HttpStatus.HTTP_201_CREATED,
)
async def upload_file(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    datasource_id: Optional[str] = Form(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ApiResponse[FileUpload]:
    """
    Upload a file to a data source.
    """
    upload_service = UploadService()
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

    response = await upload_service.upload_file(
        file=file,
        datasource_id=datasource_id,
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> PaginatedResponse[FileUpload]:
    """
    Retrieve file uploads with filtering options.
    """
    upload_service = UploadService()
    response = await upload_service.get_file_uploads(
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ApiResponse[FileUpload]:
    """
    Get specific file upload by ID.
    """
    upload_service = UploadService()
    response = await upload_service.get_file_upload(file_upload_id=file_id)

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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ApiResponse[FileUpload]:
    """
    Update status of a file upload.
    """
    upload_service = UploadService()
    response = await upload_service.update_file_status(
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
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete a file upload.
    """
    upload_service = UploadService()
    response = await upload_service.delete_file_upload(file_upload_id=file_id)
    return ApiResponse(
        data=response,
        status=HttpStatus.HTTP_200_OK,
        message="File upload deleted successfully",
    )


@router.put("/files/{file_id}/metadata", response_model=ApiResponse[Dict[str, Any]])
async def update_file_metadata(
    file_id: str = Path(...),
    metadata: Dict[str, Any] = {},
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ApiResponse[Dict[str, Any]]:
    """
    Get metadata of a file upload.
    """
    upload_service = UploadService()
    response = await upload_service.update_file_metadata(
        file_upload_id=file_id, metadata=metadata
    )
    return ApiResponse(
        data=response,
        status=HttpStatus.HTTP_200_OK,
        message="File metadata retrieved successfully",
    )


@router.get("/files/{file_id}/public", response_model=ApiResponse[str])
async def get_file_public(
    file_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ApiResponse[str]:
    """
    Get public URL of a file upload.
    """
    upload_service = UploadService()
    response = await upload_service.get_file_public_url(file_upload_id=file_id)
    return ApiResponse(
        data=response,
        status=HttpStatus.HTTP_200_OK,
        message="File public URL retrieved successfully",
    )


@router.get("/files/{file_id}/content")
async def get_file_content(
    file_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Any:
    """
    Get the content of a file.
    """
    upload_service = UploadService()

    # Get file info to determine content type
    file_info = await upload_service.get_file_upload(file_upload_id=file_id)
    content = await upload_service.get_file_content(file_upload_id=file_id)

    # Return file content with appropriate content type
    from fastapi.responses import Response

    return Response(
        content=content,
        media_type=file_info.get("file_type", "application/octet-stream"),
    )
