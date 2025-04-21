from typing import Annotated, Dict, Any, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.services.auth import AuthService
from app.services.user import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Validate token and return current user.
    """
    auth_service = AuthService()
    return await auth_service.get_current_user(token)


async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Get current active user.
    """
    if not current_user.get("is_active", False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_admin(current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)]) -> Dict[str, Any]:
    """
    Get current active admin.
    """
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    return current_user

class PermissionChecker:
    """
    Dependency to check if the user has a specific permission.
    """
    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(self, current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
        user_service = UserService()
        has_permission = await user_service.check_permission(current_user["id"], self.permission)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User doesn't have the required permission: {self.permission}"
            )
        
        return current_user
