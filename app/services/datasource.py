from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.core.config import settings
from app.core.supabase import get_supabase
from app.schemas.datasource import DataSourceCreate, DataSourceUpdate


class DataSourceService:

    async def create_datasource(
        self, datasource_in: DataSourceCreate, user_id: str
    ) -> Dict[str, Any]:
        """Create a new data source"""
        try:
            supabase = await get_supabase()
            data = datasource_in.model_dump()
            data["created_by"] = user_id

            # Convert Enum to string
            data["source_type"] = data["source_type"].value

            # Handle sensitive credentials - encrypt if needed
            if data.get("credentials"):
                encrypted_data = await supabase.rpc(
                    "encrypt_data_source_credentials",
                    {
                        "p_credentials": data["credentials"],
                        "p_encryption_key": settings.ENCRYPTION_KEY,
                    },
                ).execute()
                data["credentials"] = encrypted_data.data[0]["encrypted_credentials"]

            response = await supabase.from_("data_sources").insert(data).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create data source",
                )

            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating data source: {str(e)}",
            )

    async def get_datasource(self, datasource_id: str) -> Dict[str, Any]:
        """Get a data source by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.table("data_sources")
                .select("*")
                .eq("id", datasource_id)
                .maybe_single()
                .execute()
            )

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Data source not found",
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data source: {str(e)}",
            )

    async def update_datasource(
        self, datasource_id: str, datasource_in: DataSourceUpdate
    ) -> Dict[str, Any]:
        """Update a data source"""
        try:
            supabase = await get_supabase()
            # First check if data source exists
            await self.get_datasource(datasource_id)

            # Update the data source
            data = datasource_in.model_dump(exclude_unset=True)

            # Convert Enum to string if present
            if "source_type" in data:
                data["source_type"] = str(data["source_type"])

            if "credentials" in data:
                encrypted_data = await supabase.rpc(
                    "encrypt_data_source_credentials",
                    {
                        "p_credentials": data["credentials"],
                        "p_encryption_key": settings.ENCRYPTION_KEY,
                    },
                ).execute()

                data["encrypted_credentials"] = encrypted_data.data[0]

            response = (
                await supabase.from_("data_sources")
                .update(data)
                .eq("id", datasource_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update data source",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating data source: {str(e)}",
            )

    async def delete_datasource(self, datasource_id: str) -> Dict[str, Any]:
        """Delete a data source"""
        try:
            supabase = await get_supabase()
            # First check if data source exists
            await self.get_datasource(datasource_id)

            # Delete the data source
            await supabase.from_("data_sources").delete().eq(
                "id", datasource_id
            ).execute()

            return {"success": True, "message": "Data source deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting data source: {str(e)}",
            )

    async def get_datasources(
        self,
        skip: int = 0,
        limit: int = 100,
        source_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> APIResponse[Dict[str, Any]]:
        """Get all data sources with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("data_sources").select("*", count=CountMethod.exact)

            if source_type:
                query = query.eq("source_type", source_type)

            if is_active is not None:
                query = query.eq("is_active", is_active)

            response = (
                await query.order("created_at", desc=False)
                .range(skip, skip + limit - 1)
                .execute()
            )

            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data sources: {str(e)}",
            )

    async def get_data_source_credentials(
        self,
        data_source_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get the credentials for a data source"""
        try:
            supabase = await get_supabase()
            # Get the data source
            datasource = await self.get_datasource(data_source_id)
            if not datasource:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Data source not found",
                )
            # Decrypt credentials if they exist
            if datasource.get("credentials"):
                encrypted_credentials = datasource["credentials"]
                decrypted_credentials = await supabase.rpc(
                    "decrypt_data_source_credentials",
                    {
                        "p_encrypted_credentials": encrypted_credentials,
                        "p_encryption_key": settings.ENCRYPTION_KEY,
                    },
                ).execute()
                return decrypted_credentials.data["decrypted_credentials"]
            return None
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data source credentials: {str(e)}",
            )
