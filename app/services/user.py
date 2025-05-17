from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.core.supabase import get_supabase
from app.schemas.user import UserUpdate


class UserService:
    """Service for managing users and their roles."""

    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get a user by ID"""
        try:
            supabase = await get_supabase()
            # Get profile from profiles table
            profile_response = (
                await supabase.from_("profiles")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )

            if not profile_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )

            profile = profile_response.data

            # Get user roles
            roles = await self._get_user_roles(user_id)

            # Combine data
            return {
                "id": profile["id"],
                "email": profile.get("email"),
                "full_name": profile.get("full_name"),
                "department": profile.get("department"),
                "position": profile.get("position"),
                "bio": profile.get("bio"),
                "avatar_url": profile.get("avatar_url"),
                "is_active": True,  # Assuming profile exists means user is active
                "roles": roles,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving user: {str(e)}",
            )

    async def update_user(self, user_id: str, user_data: UserUpdate) -> Dict[str, Any]:
        """Update a user's information"""
        try:
            supabase = await get_supabase()
            # Update profile data
            update_data = user_data.dict(exclude_unset=True, exclude={"roles"})

            if update_data:
                await supabase.from_("profiles").update(update_data).eq(
                    "id", user_id
                ).execute()

            # Update roles if provided
            if user_data.roles is not None:
                await self._update_user_roles(user_id, user_data.roles)

            # Return updated user
            return await self.get_user_by_id(user_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not update user: {str(e)}",
            )

    async def get_users(
        self, skip: int = 0, limit: int = 100
    ) -> APIResponse[Dict[str, Any]]:
        """Get a list of users with pagination"""
        try:
            supabase = await get_supabase()
            # Get profiles with pagination
            response = (
                await supabase.from_("profiles")
                .select("*", count=CountMethod.exact)
                .range(skip, skip + limit - 1)
                .execute()
            )

            if not response.data:
                return APIResponse(
                    data=[],
                    count=0,
                )

            # Get roles for each user
            users = []
            for profile in response.data:
                user_id = profile["id"]
                roles = await self._get_user_roles(user_id)

                users.append(
                    {
                        "id": user_id,
                        "email": profile.get("email"),
                        "full_name": profile.get("full_name"),
                        "department": profile.get("department"),
                        "position": profile.get("position"),
                        "bio": profile.get("bio"),
                        "avatar_url": profile.get("avatar_url"),
                        "is_active": True,  # Assuming profile exists means user is active
                        "roles": roles,
                    }
                )

            return APIResponse(
                data=users,
                count=response.count,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving users: {str(e)}",
            )

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user"""
        try:
            supabase = await get_supabase()
            # Check if user exists
            user = await self.get_user_by_id(user_id)

            # Delete user in auth system (will cascade to profile)
            await supabase.auth.admin.delete_user(user_id)

            return {"detail": "User successfully deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not delete user: {str(e)}",
            )

    async def _get_user_roles(self, user_id: str) -> List[str]:
        """Get roles for a user"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("user_roles")
                .select("role:role_id(name)")
                .eq("user_id", user_id)
                .execute()
            )

            return [item["role"]["name"] for item in response.data]
        except Exception as e:
            print(f"Error getting roles: {e}")
            return []

    async def _update_user_roles(self, user_id: str, role_names: List[str]) -> None:
        """Update roles for a user"""
        try:
            supabase = await get_supabase()
            # Get current user roles
            current_roles = await self._get_user_roles(user_id)

            # Delete all current roles
            await supabase.from_("user_roles").delete().eq("user_id", user_id).execute()

            # Add new roles
            for role_name in role_names:
                role_response = (
                    await supabase.from_("roles")
                    .select("id")
                    .eq("name", role_name)
                    .execute()
                )

                if role_response.data and len(role_response.data) > 0:
                    role_id = role_response.data[0]["id"]

                    await supabase.from_("user_roles").insert(
                        {"user_id": user_id, "role_id": role_id}
                    ).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not update user roles: {str(e)}",
            )

    async def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission"""
        try:
            supabase = await get_supabase()
            print(user_id)
            # Call the database function to check permission
            response = await supabase.rpc(
                "check_user_permission",
                {"user_id": user_id, "permission_name": permission},
            ).execute()

            print(response)

            return response.data
        except Exception as e:
            print(f"Error checking permission: {e}")
            return False

    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all available roles"""
        try:
            supabase = await get_supabase()
            response = await supabase.from_("roles").select("*").execute()
            return response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving roles: {str(e)}",
            )

    async def get_all_permissions(self) -> List[Dict[str, Any]]:
        """Get all available permissions"""
        try:
            supabase = await get_supabase()
            response = await supabase.from_("permissions").select("*").execute()
            return response.data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving permissions: {str(e)}",
            )
