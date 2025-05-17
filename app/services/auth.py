from typing import Any, Dict, List

from fastapi import HTTPException, status

from app.core.supabase import get_supabase
from app.schemas.user import UserCreate, UserLogin


class AuthService:
    async def login(self, user_data: UserLogin) -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        try:
            supabase = await get_supabase()
            response = await supabase.auth.sign_in_with_password(
                {"email": user_data.email, "password": user_data.password}
            )

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return {
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                },
                "user": {
                    "id": response.user.id,
                    "roles": await self._get_user_roles(response.user.id),
                    "email": response.user.email,
                    "is_active": response.user.confirmed_at is not None,
                    "full_name": response.user.user_metadata.get("full_name"),
                },
            }
        except Exception as _:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def register(self, user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user"""
        try:
            supabase = await get_supabase()
            # Check if user already exists
            user_exists = await self._check_user_exists(user_data.email)
            if user_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

            # Register user in auth system
            response = await supabase.auth.sign_up(
                {
                    "email": user_data.email,
                    "password": user_data.password,
                    "options": {"data": {"full_name": user_data.full_name}},
                }
            )

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User registration failed",
                )

            # Assign roles to user
            user_id = response.user.id
            await self._assign_roles(user_id, user_data.roles)

            return {
                "id": user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "roles": user_data.roles,
                "is_active": False,  # User needs to confirm email
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration error: {str(e)}",
            )

    async def logout(self, _: str) -> Dict[str, Any]:
        """Logout a user"""
        try:
            supabase = await get_supabase()
            await supabase.auth.sign_out()
            return {"detail": "Successfully logged out"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Logout error: {str(e)}",
            )

    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """Get current user from token"""
        try:
            supabase = await get_supabase()
            response = await supabase.auth.get_user(token)
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user = response.user

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Get roles for user
            roles = await self._get_user_roles(user.id)

            return {
                "id": user.id,
                "email": user.email,
                "full_name": user.user_metadata.get("full_name"),
                "is_active": user.confirmed_at is not None,
                "roles": roles,
            }
        except Exception as _:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def _check_user_exists(self, email: str) -> bool:
        """Check if a user with the given email exists"""
        try:
            supabase = await get_supabase()
            # Query the profile to see if user exists
            response = (
                await supabase.from_("profiles")
                .select("id")
                .eq("email", email)
                .execute()
            )
            return len(response.data) > 0
        except Exception:
            return False

    async def _assign_roles(self, user_id: str, role_names: List[str]) -> None:
        """Assign roles to a user"""
        try:
            supabase = await get_supabase()
            # Get role IDs from role names
            for role_name in role_names:
                response = (
                    await supabase.table("roles")
                    .select("id")
                    .eq("name", role_name)
                    .execute()
                )

                if response.data and len(response.data) > 0:
                    role_id = response.data[0]["id"]

                    # Assign role to user
                    await supabase.table("user_roles").insert(
                        {"user_id": user_id, "role_id": role_id}
                    ).execute()
        except Exception as e:
            print(f"Error assigning roles: {e}")

    async def _get_user_roles(self, user_id: str) -> List[str]:
        """Get roles for a user"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.table("user_roles")
                .select("roles:role_id(name)")
                .eq("user_id", user_id)
                .execute()
            )

            return [item["roles"]["name"] for item in response.data]
        except Exception as e:
            print(f"Error getting roles: {e}")
            return []
