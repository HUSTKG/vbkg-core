from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.core.config import settings
from app.core.supabase import get_supabase
from app.schemas.datasource import DataSourceCreate, DataSourceUpdate
from app.schemas.user import ResourceType, UserAction
from app.services.user import UserService


class DataSourceService:
    def __init__(self):
        self.user_service = UserService()

    async def create_datasource(
        self, datasource_in: DataSourceCreate, user_id: str
    ) -> Dict[str, Any]:
        """Create a new data source with trust score"""
        try:
            supabase = await get_supabase()
            data = datasource_in.model_dump()
            data["created_by"] = user_id

            # Convert Enum to string
            data["source_type"] = data["source_type"].value

            # Set default trust score if not provided

            if "trust_score" not in data or data["trust_score"] is None:
                data["trust_score"] = self._calculate_default_trust_score(data)

            # Handle sensitive credentials - encrypt if needed
            if data.get("credentials"):
                encrypted_data = await supabase.rpc(
                    "encrypt_data_source_credentials",
                    {
                        "p_credentials": data["credentials"],
                        "p_encryption_key": settings.ENCRYPTION_KEY,
                    },
                ).execute()
                data["encrypted_credentials"] = encrypted_data.data

            # pop the credentials
            data.pop("credentials", None)

            response = await supabase.from_("data_sources").insert(data).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create data source",
                )

            await self.user_service._log_user_activity(
                user_id=user_id,
                action=UserAction.DATASOURCE_CREATE.value,
                resource_type=ResourceType.DATASOURCE.value,
                resource_id=response.data[0]["id"],
                details={
                    "name": response.data[0]["name"],
                    "trust_score": response.data[0]["trust_score"],
                },
            )
            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating data source: {str(e)}",
            )

    def _calculate_default_trust_score(self, data: Dict[str, Any]) -> float:
        """Calculate default trust score based on source characteristics"""
        base_score = 0.5

        # Premium sources get higher trust scores
        premium_sources = {
            "wikipedia.org": 0.9,
            "dbpedia.org": 0.95,
            "wikidata.org": 0.9,
            "worldbank.org": 0.85,
            "gov": 0.8,  # Government domains
            "edu": 0.75,  # Educational domains
        }

        source_type = data.get("source_type", "")
        connection_details = data.get("connection_details", {})

        if source_type == "api":
            url = connection_details.get("url", "").lower()
            for domain, score in premium_sources.items():
                if domain in url:
                    return score
        elif source_type == "database":
            # Structured data sources get higher trust
            return 0.7
        elif source_type == "file":
            # File format affects trust
            file_format = connection_details.get("file_format", "").lower()
            if file_format in ["csv", "json", "xml", "txt"]:
                return 0.6
            elif file_format in ["pdf", "doc", "docx"]:
                return 0.4
            else:
                return 0.3

        return base_score

    async def get_datasources_by_trust_score(
        self,
        min_trust_score: float = 0.0,
        max_trust_score: float = 1.0,
        skip: int = 0,
        limit: int = 100,
    ) -> APIResponse[Dict[str, Any]]:
        """Get data sources filtered by trust score range"""
        try:
            supabase = await get_supabase()

            response = (
                await supabase.from_("data_sources")
                .select("*", count=CountMethod.exact)
                .gte("trust_score", min_trust_score)
                .lte("trust_score", max_trust_score)
                .order("trust_score", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )

            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data sources by trust score: {str(e)}",
            )

    async def update_trust_score(
        self, datasource_id: str, new_trust_score: float, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update trust score for a data source"""
        try:
            if not 0.0 <= new_trust_score <= 1.0:
                raise ValueError("Trust score must be between 0.0 and 1.0")

            supabase = await get_supabase()

            # Update trust score
            response = (
                await supabase.from_("data_sources")
                .update(
                    {
                        "trust_score": new_trust_score,
                        "trust_score_updated_at": "now()",
                        "trust_score_reason": reason,
                    }
                )
                .eq("id", datasource_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Data source not found",
                )

            # Log the trust score update
            await self.user_service._log_user_activity(
                user_id=response.data[0]["created_by"],
                action=UserAction.DATASOURCE_UPDATE.value,
                resource_type=ResourceType.DATASOURCE.value,
                resource_id=datasource_id,
                details={
                    "old_trust_score": response.data[0].get("trust_score"),
                    "new_trust_score": new_trust_score,
                    "reason": reason,
                },
            )

            return {
                "success": True,
                "datasource_id": datasource_id,
                "old_trust_score": response.data[0].get("trust_score"),
                "new_trust_score": new_trust_score,
                "reason": reason,
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating trust score: {str(e)}",
            )

    async def get_datasource_with_credentials(
        self, datasource_id: str
    ) -> Dict[str, Any]:
        """Get a data source by ID"""
        try:
            supabase = await get_supabase()
            response = await self.get_datasource(datasource_id)

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Data source not found",
                )

            # Decrypt credentials if they exist
            if response.get("encrypted_credentials"):
                decrypted_credentials = await supabase.rpc(
                    "decrypt_data_source_credentials",
                    {
                        "p_id": datasource_id,
                        "p_encryption_key": settings.ENCRYPTION_KEY,
                    },
                ).execute()

                if decrypted_credentials.data:
                    response["credentials"] = decrypted_credentials.data

            return response
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data source: {str(e)}",
            )

    async def get_datasource(self, datasource_id: str) -> Dict[str, Any]:
        """Get a data source by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.table("data_sources")
                .select(
                    "*, created_by:created_by(id, full_name, roles:user_roles!user_roles_user_id_fkey1(role:role_id(name)))"
                )
                .eq("id", datasource_id)
                .maybe_single()
                .execute()
            )

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Data source not found",
                )

            created_by = response.data.get("created_by", {})
            if created_by:
                # Ensure created_by is a dict with expected fields
                response.data["created_by"] = {
                    "id": created_by.get("id"),
                    "full_name": created_by.get("full_name"),
                    "roles": [
                        role["role"]["name"]
                        for role in created_by.get("roles", [])
                        if "role" in role
                    ],
                }

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

            # Set trust score if provided, otherwise keep existing
            if "trust_score" in data:
                if not (0.0 <= data["trust_score"] <= 1.0):
                    raise ValueError("Trust score must be between 0.0 and 1.0")
                data["trust_score"] = float(data["trust_score"])

            if "credentials" in data:
                encrypted_data = await supabase.rpc(
                    "encrypt_data_source_credentials",
                    {
                        "p_credentials": data["credentials"],
                        "p_encryption_key": settings.ENCRYPTION_KEY,
                    },
                ).execute()

                data["encrypted_credentials"] = encrypted_data.data

            # remove the original credentials field if it exists
            if "credentials" in data:
                data.pop("credentials")

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

            # Log the update activity
            await self.user_service._log_user_activity(
                user_id=response.data[0]["created_by"],
                action=UserAction.DATASOURCE_UPDATE.value,
                resource_type=ResourceType.DATASOURCE.value,
                resource_id=datasource_id,
                details={
                    "name": response.data[0]["name"],
                    "trust_score": response.data[0]["trust_score"],
                },
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

            # Log the delete activity
            await self.user_service._log_user_activity(
                user_id=datasource_id,  # Assuming the user ID is stored in the datasource
                action=UserAction.DATASOURCE_DELETE.value,
                resource_type=ResourceType.DATASOURCE.value,
                resource_id=datasource_id,
                details={"datasource_id": datasource_id},
            )

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
                await query.order("created_at", desc=True)
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
