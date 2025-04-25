from typing import Any, Dict, List, Optional
import uuid

from fastapi import HTTPException, UploadFile, status
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.core.supabase import get_supabase
from app.schemas.datasource import (
    DataSourceCreate,
    DataSourceUpdate,
    FileUploadCreate,
    FileUploadStatus,
)

class DataSourceService:

    async def create_datasource(
        self, 
        datasource_in: DataSourceCreate, 
        user_id: str
    ) -> Dict[str, Any]:
        """Create a new data source"""
        try:
            supabase = await get_supabase()
            data = datasource_in.dict()
            data["created_by"] = user_id
            
            # Convert Enum to string
            data["source_type"] = data["source_type"].value
            
            # Handle sensitive credentials - encrypt if needed
            if data.get("credentials"):
                # In a real implementation, you might want to encrypt this
                pass

            print(data)
            
            response = await supabase.from_("data_sources").insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create data source"
                )
                
            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating data source: {str(e)}"
            )

    async def get_datasource(self, datasource_id: str) -> Dict[str, Any]:
        """Get a data source by ID"""
        try:
            supabase = await get_supabase()
            response = await supabase.from_("data_sources").select("*").eq("id", datasource_id).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Data source not found"
                )
                
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data source: {str(e)}"
            )

    async def update_datasource(
        self, 
        datasource_id: str, 
        datasource_in: DataSourceUpdate
    ) -> Dict[str, Any]:
        """Update a data source"""
        try:
            supabase = await get_supabase()
            # First check if data source exists
            await self.get_datasource(datasource_id)
            
            # Update the data source
            data = datasource_in.dict(exclude_unset=True)
            
            # Convert Enum to string if present
            if "source_type" in data:
                data["source_type"] = str(data["source_type"])
            
            response = await supabase.from_("data_sources").update(data).eq("id", datasource_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update data source"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating data source: {str(e)}"
            )

    async def delete_datasource(self, datasource_id: str) -> Dict[str, Any]:
        """Delete a data source"""
        try:
            supabase = await get_supabase()
            # First check if data source exists
            await self.get_datasource(datasource_id)
            
            # Delete the data source
            await supabase.from_("data_sources").delete().eq("id", datasource_id).execute()
            
            return {"success": True, "message": "Data source deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting data source: {str(e)}"
            )

    async def get_datasources(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        source_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> APIResponse[Dict[str, Any]]:
        """Get all data sources with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("data_sources").select("*", count=CountMethod.exact)
            
            if source_type:
                query = query.eq("source_type", source_type)
                
            if is_active is not None:
                query = query.eq("is_active", is_active)
                
            response = await query.order("created_at", desc=False).range(skip, skip + limit - 1).execute()
            
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data sources: {str(e)}"
            )

    async def upload_file(
        self, 
        file: UploadFile, 
        data_source_id: str, 
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload a file to Supabase storage and register it in the database"""
        try:
            supabase = await get_supabase()
            # First check if data source exists
            datasource = await self.get_datasource(data_source_id)
            
            if datasource["source_type"] != "file":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Data source is not of type 'file'"
                )

            if not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File name is required"
                )
            
            # Generate a unique file path in storage
            file_ext = file.filename.split(".")[-1] if "." in file.filename else ""
            storage_path = f"{data_source_id}/{uuid.uuid4()}.{file_ext}"
            
            # Read file content
            file_content = await file.read()
            
            # Upload to Supabase Storage
            storage_response = await supabase.storage.from_("documents").upload(
                storage_path,
                file_content
            )
            
            if not storage_response:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to upload file to storage"
                )
            
            # Register in database
            file_upload = FileUploadCreate(
                data_source_id=data_source_id,
                file_name=file.filename,
                file_type=file.content_type or f".{file_ext}",
                file_size=len(file_content),
                storage_path=storage_path,
                metadata=metadata or {}
            )
            
            upload_data = file_upload.dict()
            upload_data["uploaded_by"] = user_id
            
            response = await supabase.from_("file_uploads").insert(upload_data).execute()
            
            if not response.data:
                # If database insert fails, try to delete from storage
                await supabase.storage.from_("documents").remove([storage_path])
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to register file upload"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading file: {str(e)}"
            )

    async def get_file_uploads(
        self, 
        data_source_id: Optional[str] = None,
        _status: Optional[str] = None,
        processed: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> APIResponse[Dict[str, Any]]:
        """Get file uploads with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("file_uploads").select("*", count=CountMethod.exact)
            
            if data_source_id:
                query = query.eq("data_source_id", data_source_id)
                
            if _status:
                query = query.eq("upload_status", _status)
                
            if processed is not None:
                query = query.eq("processed", processed)
                
            response = await query.order("uploaded_at", desc=True).range(skip, skip + limit - 1).execute()
            
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving file uploads: {str(e)}"
            )

    async def get_file_upload(self, file_upload_id: str) -> Dict[str, Any]:
        """Get a file upload by ID"""
        try:
            supabase = await get_supabase()
            response = await supabase.from_("file_uploads").select("*").eq("id", file_upload_id).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File upload not found"
                )
                
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving file upload: {str(e)}"
            )

    async def update_file_status(
        self, 
        file_upload_id: str, 
        fileStatus: FileUploadStatus,
        processed: Optional[bool] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a file upload status"""
        try:
            supabase = await get_supabase()
            # First check if file upload exists
            await self.get_file_upload(file_upload_id)
            
            # Update the file status
            data: dict  = {"upload_status": fileStatus}
            
            if processed is not None:
                data["processed"] = processed                
            if error_message:
                # Store error message in metadata
                file_upload = await self.get_file_upload(file_upload_id)
                metadata = file_upload.get("metadata", {}) or {}
                metadata["error_message"] = error_message
                data["metadata"] = metadata
            
            response = await supabase.from_("file_uploads").update(data).eq("id", file_upload_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update file status"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating file status: {str(e)}"
            )

    async def delete_file_upload(self, file_upload_id: str) -> Dict[str, Any]:
        """Delete a file upload and remove from storage"""
        try:
            supabase = await get_supabase()
            # First get the file upload to get storage path
            file_upload = await self.get_file_upload(file_upload_id)
            storage_path = file_upload.get("storage_path")
            
            # Delete from storage if path exists
            if storage_path:
                try:
                    await supabase.storage.from_("documents").remove([storage_path])
                except Exception as e:
                    # Log error but continue with deletion from database
                    print(f"Error removing file from storage: {e}")
            
            # Delete from database
            await supabase.from_("file_uploads").delete().eq("id", file_upload_id).execute()
            
            return {"success": True, "message": "File upload deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting file upload: {str(e)}"
            )

    async def get_file_content(self, file_upload_id: str) -> bytes:
        """Get the content of a file from storage"""
        try:
            supabase = await get_supabase()
            # Get the file upload to get storage path
            file_upload = await self.get_file_upload(file_upload_id)
            storage_path = file_upload.get("storage_path")
            
            if not storage_path:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File storage path not found"
                )
            
            # Get from storage
            try:
                response = await supabase.storage.from_("documents").download(storage_path)
                return response
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"File not found in storage: {str(e)}"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving file content: {str(e)}"
            )
