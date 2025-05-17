from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile, status

from app.api.deps import get_current_active_user
from app.schemas.api import ApiResponse
from app.schemas.user import User
from app.services.file_upload import UploadService

router = APIRouter()


@router.post("", response_model=ApiResponse[str])
async def upload_file(
    bucket_name: Annotated[str, Form()],
    file_path: Annotated[str, Form()],
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ApiResponse[str]:
    """
    Upload a file to Supabase storage.
    """

    upload_service = UploadService()
    response = await upload_service.upload_file(
        bucket_name=bucket_name,
        file_path=file_path,
        file=file,
        user_id=current_user.id,
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="File uploaded successfully",
    )
