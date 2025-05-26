import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse

from app.core.supabase import get_supabase
from app.schemas.user import UserUpdate


class UserService:
    """User Service with Knowledge Graph specific features"""

    async def get_user_by_id(self, user_id: str) -> Dict[str, Any]:
        """Get a user by ID with enhanced data including permissions"""
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

            # Get user roles and permissions
            roles = await self._get_user_roles(user_id)
            permissions = await self._get_user_permissions(user_id)

            return {
                "id": profile["id"],
                "email": profile.get("email"),
                "full_name": profile.get("full_name"),
                "department": profile.get("department"),
                "position": profile.get("position"),
                "bio": profile.get("bio"),
                "avatar_url": profile.get("avatar_url"),
                "is_active": True,
                "roles": roles,
                "permissions": permissions,
                "last_sign_in_at": profile.get("last_sign_in_at"),
                "created_at": profile.get("created_at"),
                "updated_at": profile.get("updated_at"),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving user: {str(e)}",
            )

    async def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission"""
        try:
            supabase = await get_supabase()
            response = await supabase.rpc(
                "check_user_permission",
                {"user_id": user_id, "permission_name": permission},
            ).execute()
            return response.data
        except Exception as e:
            print(f"Error checking permission: {e}")
            return False

    async def has_role(self, user_id: str, role_name: str) -> bool:
        """Check if user has a specific role"""
        try:
            supabase = await get_supabase()
            response = await supabase.rpc(
                "user_has_role",
                {"user_id": user_id, "role_name": role_name},
            ).execute()
            return response.data
        except Exception as e:
            print(f"Error checking role: {e}")
            return False

    async def assign_role_to_user(self, user_id: str, role_name: str) -> bool:
        """Assign a role to user"""
        try:
            supabase = await get_supabase()

            # Get role ID
            role_response = (
                await supabase.from_("roles")
                .select("id")
                .eq("name", role_name)
                .single()
                .execute()
            )
            if not role_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Role '{role_name}' not found",
                )

            role_id = role_response.data["id"]

            # Check if assignment already exists
            existing = (
                await supabase.from_("user_roles")
                .select("id")
                .eq("user_id", user_id)
                .eq("role_id", role_id)
                .execute()
            )

            if existing.data:
                return True  # Already assigned

            # Create role assignment
            await supabase.from_("user_roles").insert(
                {"user_id": user_id, "role_id": role_id}
            ).execute()

            # Log activity
            await self._log_user_activity(
                user_id=user_id, action="assign_role", details={"role": role_name}
            )

            return True

        except Exception as e:
            print(f"Error assigning role: {e}")
            return False

    async def remove_role_from_user(self, user_id: str, role_name: str) -> bool:
        """Remove a role from user"""
        try:
            supabase = await get_supabase()

            # Get role ID
            role_response = (
                await supabase.from_("roles")
                .select("id")
                .eq("name", role_name)
                .single()
                .execute()
            )
            if not role_response.data:
                return True  # Role doesn't exist, consider it removed

            role_id = role_response.data["id"]

            # Remove role assignment
            await supabase.from_("user_roles").delete().eq("user_id", user_id).eq(
                "role_id", role_id
            ).execute()

            # Log activity
            await self._log_user_activity(
                user_id=user_id, action="remove_role", details={"role": role_name}
            )

            return True

        except Exception as e:
            print(f"Error removing role: {e}")
            return False

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user and their associated data"""
        try:
            supabase = await get_supabase()
            # Delete user roles
            await supabase.from_("user_roles").delete().eq("user_id", user_id).execute()
            # Delete API keys
            await supabase.from_("api_keys").delete().eq("user_id", user_id).execute()
            # Delete user activity logs
            await supabase.from_("user_activity_log").delete().eq(
                "user_id", user_id
            ).execute()
            # Delete profile
            response = (
                await supabase.from_("profiles").delete().eq("id", user_id).execute()
            )
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
                )
            # Log activity
            await self._log_user_activity(
                user_id=user_id, action="delete_user", details={"deleted": True}
            )
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    # API Key Management
    async def create_api_key(
        self,
        user_id: str,
        name: str,
        description: str = None,
        expires_at: datetime = None,
        rate_limit: int = 1000,
        allowed_ips: List[str] = None,
    ) -> Dict[str, Any]:
        """Create new API key for user"""

        supabase = await get_supabase()

        # Generate secure API key
        api_key = f"kg_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        api_key_data = {
            "name": name,
            "description": description,
            "key_hash": key_hash,
            "key_prefix": api_key[:10],  # kg_xxxxxxxx
            "user_id": user_id,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "rate_limit": rate_limit,
            "allowed_ips": allowed_ips or [],
        }

        response = await supabase.table("api_keys").insert(api_key_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create API key",
            )

        # Log activity
        await self._log_user_activity(
            user_id=user_id,
            action="create_api_key",
            resource_type="api_key",
            resource_id=response.data[0]["id"],
            details={"name": name},
        )

        return {
            **response.data[0],
            "token": api_key,  # Return full token only on creation
        }

    async def get_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all API keys for a user"""

        supabase = await get_supabase()

        response = (
            await supabase.table("api_keys")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        # Don't return the actual key hash
        for key in response.data:
            key.pop("key_hash", None)

        return response.data

    async def revoke_api_key(self, api_key_id: str, user_id: str) -> bool:
        """Revoke API key"""

        supabase = await get_supabase()

        response = (
            await supabase.table("api_keys")
            .update({"is_active": False, "updated_at": datetime.now().isoformat()})
            .eq("id", api_key_id)
            .eq("user_id", user_id)
            .execute()
        )

        if response.data:
            await self._log_user_activity(
                user_id=user_id,
                action="revoke_api_key",
                resource_type="api_key",
                resource_id=api_key_id,
            )

        return bool(response.data)

    async def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return user info"""

        supabase = await get_supabase()

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Get API key record
        api_response = (
            await supabase.table("api_keys")
            .select("*")
            .eq("key_hash", key_hash)
            .eq("is_active", True)
            .execute()
        )

        if not api_response.data:
            return None

        api_key_data = api_response.data[0]

        # Check expiry
        if api_key_data["expires_at"]:
            expire_time = datetime.fromisoformat(api_key_data["expires_at"])
            if datetime.now() > expire_time:
                return None

        # Update usage stats
        await supabase.table("api_keys").update(
            {
                "last_used": datetime.now().isoformat(),
                "usage_count": api_key_data["usage_count"] + 1,
            }
        ).eq("id", api_key_data["id"]).execute()

        # Get user info
        user = await self.get_user_by_id(api_key_data["user_id"])
        return {
            **user,
            "api_key_info": {
                "id": api_key_data["id"],
                "name": api_key_data["name"],
                "rate_limit": api_key_data["rate_limit"],
                "allowed_ips": api_key_data["allowed_ips"],
            },
        }

    async def get_user_activity(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0,
        action_filter: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Get user activity history"""

        supabase = await get_supabase()

        query = supabase.table("user_activity_log").select("*").eq("user_id", user_id)

        if action_filter:
            query = query.eq("action", action_filter)

        response = (
            await query.order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        return response.data

    async def update_user_roles(self, user_id: str, role_names: List[str]) -> bool:
        """Update all roles for a user (replaces existing roles)"""
        try:
            supabase = await get_supabase()

            # Remove all existing roles
            await supabase.from_("user_roles").delete().eq("user_id", user_id).execute()

            # Add new roles
            for role_name in role_names:
                await self.assign_role_to_user(user_id, role_name)

            # Log activity
            await self._log_user_activity(
                user_id=user_id,
                action="update_roles",
                details={"new_roles": role_names},
            )

            return True

        except Exception as e:
            print(f"Error updating user roles: {e}")
            return False

    # Enhanced existing methods
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Dict[str, Any]:
        """Update a user's information"""
        try:
            supabase = await get_supabase()

            # Update profile data (exclude roles)
            update_data = user_data.dict(exclude_unset=True, exclude={"roles"})

            if update_data:
                await supabase.from_("profiles").update(update_data).eq(
                    "id", user_id
                ).execute()

            # Update roles if provided
            if user_data.roles is not None:
                await self.update_user_roles(user_id, user_data.roles)

            # Log activity
            await self._log_user_activity(
                user_id=user_id, action="update_profile", details=update_data
            )

            # Return updated user
            return await self.get_user_by_id(user_id)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not update user: {str(e)}",
            )

    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role_filter: Optional[str] = None,
        department_filter: Optional[str] = None,
    ) -> APIResponse[Dict[str, Any]]:
        """Get a list of users with pagination and filters"""
        try:
            supabase = await get_supabase()

            # Base query
            query = supabase.from_("profiles").select("*")

            # Apply filters
            if department_filter:
                query = query.eq("department", department_filter)

            response = await query.range(skip, skip + limit - 1).execute()

            if not response.data:
                return APIResponse(data=[], count=0)

            # Get roles for each user and apply role filter
            users = []
            for profile in response.data:
                user_id = profile["id"]
                roles = await self._get_user_roles(user_id)
                permissions = await self._get_user_permissions(user_id)

                # Apply role filter
                if role_filter and role_filter not in roles:
                    continue

                users.append(
                    {
                        "id": user_id,
                        "email": profile.get("email"),
                        "full_name": profile.get("full_name"),
                        "department": profile.get("department"),
                        "position": profile.get("position"),
                        "bio": profile.get("bio"),
                        "avatar_url": profile.get("avatar_url"),
                        "is_active": True,
                        "roles": roles,
                        "permissions": permissions,
                        "last_sign_in_at": profile.get("last_sign_in_at"),
                        "created_at": profile.get("created_at"),
                        "updated_at": profile.get("updated_at"),
                    }
                )

            return APIResponse(data=users, count=len(users))

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving users: {str(e)}",
            )

    # Helper methods
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for a user"""
        try:
            supabase = await get_supabase()
            response = await supabase.rpc(
                "get_user_permissions", {"user_id": user_id}
            ).execute()

            return (
                [item["permission_name"] for item in response.data]
                if response.data
                else []
            )
        except Exception as e:
            print(f"Error getting permissions: {e}")
            return []

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

    async def _log_user_activity(
        self,
        user_id: str,
        action: str,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None,
    ):
        """Log user activity"""
        try:
            supabase = await get_supabase()

            await supabase.rpc(
                "log_user_activity",
                {
                    "p_user_id": user_id,
                    "p_action": action,
                    "p_resource_type": resource_type,
                    "p_resource_id": resource_id,
                    "p_ip_address": ip_address,
                    "p_user_agent": user_agent,
                    "p_details": details,
                },
            ).execute()
        except Exception as e:
            # Don't let logging failures affect the main operation
            print(f"Failed to log activity: {e}")

    # Admin functions
    async def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all available roles"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("roles")
                .select("*, role_permissions(permissions(name))")
                .execute()
            )
            response.data = [
                {
                    "id": role["id"],
                    "name": role["name"],
                    "description": role.get("description"),
                    "permissions": [perm["permissions"]["name"] for perm in role["role_permissions"]],
                }
                for role in response.data
            ]
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

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics for admin dashboard"""
        try:
            supabase = await get_supabase()

            # Get user counts by role
            user_stats = {}
            roles = await self.get_all_roles()

            for role in roles:
                count_response = (
                    await supabase.from_("user_roles")
                    .select("*", count="exact")
                    .eq("role_id", role["id"])
                    .execute()
                )
                user_stats[role["name"]] = count_response.count or 0

            # Get API key usage stats
            api_keys_response = (
                await supabase.table("api_keys")
                .select("*", count="exact")
                .eq("is_active", True)
                .execute()
            )
            active_api_keys = api_keys_response.count or 0

            # Get recent activity count
            recent_activity_response = (
                await supabase.table("user_activity_log")
                .select("*", count="exact")
                .gte("created_at", (datetime.now() - timedelta(days=7)).isoformat())
                .execute()
            )
            recent_activity = recent_activity_response.count or 0

            return {
                "user_counts_by_role": user_stats,
                "active_api_keys": active_api_keys,
                "recent_activity_count": recent_activity,
                "total_users": sum(user_stats.values()),
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving system stats: {str(e)}",
            )
