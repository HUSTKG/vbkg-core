from typing import Annotated, Any, Dict, List

from fastapi import HTTPException
from fastapi import UploadFile as File
from fastapi import status

from app.core.config import settings
from app.core.supabase import get_supabase
from app.schemas.file_upload import (FileUpload, FileUploadCreate,
                                     FileUploadStatus, FileUploadUpdate)
from app.utils.file_handler import get_file_type
from app.utils.supabase_utils import (create_signed_upload_url,
                                      upload_file_to_signed_url)


class UploadService:
    def __init__(self):
        pass

    async def upload_file(
        self,
        file_path: Annotated[str, "file_path in bucket"],
        user_id: Annotated[str, "user_id"],
        file: File,
    ) -> FileUpload:
        """
        Upload a file to Supabase storage.
        """
        try:
            # Upload file to Supabase storage
            folder = "usercont/"
            # check start with / or not
            if not file_path.startswith("/"):
                file_path = folder + file_path
            else:
                file_path = folder + file_path[1:]

            file_name = file.filename if file.filename else "untitled"
            file_size = file.size if file.size else 0

            file_type = get_file_type(file_name, file.content_type)

            # create file upload record
            draft_file = await self.create_file_upload(
                file_upload_in=FileUploadCreate(
                    file_name=file_name,
                    file_type=file_type,
                    file_size=file_size,
                    storage_path=file_path,
                    uploaded_by=user_id,
                )
            )

            if not draft_file:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create file upload record",
                )

            initData = await create_signed_upload_url(file_path)

            if not initData:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create signed URL",
                )

            file_to_upload = await file.read()

            is_uploaded = await upload_file_to_signed_url(
                file_path=file_path,
                signed_url=initData["signed_url"],
                file=file_to_upload,
            )

            if not is_uploaded:
                file_upload = await self.update_file_upload(
                    file_upload_id=draft_file["id"],
                    user_id=user_id,
                    file_upload_in=FileUploadUpdate(
                        upload_status=FileUploadStatus.FAILED
                    ),
                )

            else:
                file_upload = await self.update_file_upload(
                    file_upload_id=draft_file["id"],
                    user_id=user_id,
                    file_upload_in=FileUploadUpdate(
                        upload_status=FileUploadStatus.COMPLETED
                    ),
                )

            if not file_upload:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update file upload record",
                )

            return FileUpload(**file_upload)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading file: {str(e)}",
            )

    async def create_file_upload(
        self,
        file_upload_in: Annotated[FileUploadCreate, "File upload data"],
    ) -> Dict[str, Any] | None:
        """
        Create a record in the file_uploads table.
        """
        try:
            supabase = await get_supabase()

            file_upload_dict = file_upload_in.model_dump()

            response = (
                await supabase.from_("file_uploads").insert(file_upload_dict).execute()
            )

            return response.data[0]

        except Exception as e:
            print(f"Error creating file upload record: {str(e)}")
            return None

    async def delete_file_upload(
        self,
        file_upload_id: Annotated[str, "file upload id"],
    ) -> None:
        """
        Delete a record in the file_uploads table.
        """
        try:
            supabase = await get_supabase()
            await supabase.from_("file_uploads").delete().eq(
                "id", file_upload_id
            ).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting file upload record: {str(e)}",
            )

    async def get_file_upload_url(
        self,
        file_upload_id: Annotated[str, "file upload id"],
        user_id: Annotated[str, "user id"],
    ) -> str:
        """
        Get a signed URL for a file upload.
        """

        try:
            supabase = await get_supabase()
            file_upload = await self.get_file_upload(
                file_upload_id=file_upload_id,
                user_id=user_id,
            )
            if not file_upload:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File upload record not found",
                )
            response = await supabase.storage.from_(
                settings.S3_BUCKET_NAME
            ).get_public_url(file_upload["storage_path"])
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting public URL: {str(e)}",
            )

    async def get_file_uploads(
        self,
        user_id: Annotated[str, "user id"],
        skip: Annotated[int, "skip"],
        limit: Annotated[int, "limit"],
    ) -> List[Dict[str, Any]]:
        """
        Read file uploads for a user.
        """
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("file_uploads")
                .select("*")
                .eq("uploaded_by", user_id)
                .range(skip, skip + limit)
                .execute()
            )
            return response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error reading file uploads: {str(e)}",
            )

    async def get_file_upload(
        self,
        file_upload_id: Annotated[str, "file upload id"],
        user_id: Annotated[str, "user id"],
    ) -> Dict[str, Any]:
        """
        Get a file upload record by ID.
        """
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("file_uploads")
                .select("*")
                .or_(f"id.eq.{file_upload_id},and(uploaded_by.eq.{user_id})")
                .execute()
            )
            data = response.data[0] if response.data else None

            if not data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File upload record not found",
                )
            return data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting file upload record: {str(e)}",
            )

    async def update_file_upload(
        self,
        file_upload_id: Annotated[str, "file upload id"],
        user_id: Annotated[str, "user id"],
        file_upload_in: Annotated[FileUploadUpdate, "file upload data"],
    ) -> Dict[str, Any] | None:
        """
        Update a file upload record.
        """
        try:
            supabase = await get_supabase()
            file_upload_dict = file_upload_in.model_dump()
            response = (
                await supabase.from_("file_uploads")
                .update(file_upload_dict)
                .eq("id", file_upload_id)
                .eq("uploaded_by", user_id)
                .execute()
            )

            data = response.data[0] if response.data else None

            if not data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File upload record not found",
                )

            return data

        except Exception as e:
            print(f"Error updating file upload record: {str(e)}")
            return None
