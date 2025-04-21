from typing import Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.api.deps import get_current_user, get_current_active_admin
from app.schemas.user import User, UserUpdate
from app.services.user import UserService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> Any:
    """
    Retrieve users. Only admins can access this endpoint.
    """
    user_service = UserService()
    return await user_service.get_users(skip=skip, limit=limit)


@router.get("/me", response_model=User)
async def read_user_me(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.patch("/me", response_model=User)
async def update_user_me(
    user_in: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Update current user information.
    """
    user_service = UserService()
    # Prevent a user from changing their own roles
    if hasattr(user_in, "roles") and user_in.roles is not None:
        user_in.roles = None
    
    return await user_service.update_user(current_user["id"], user_in)


@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> Any:
    """
    Get a specific user by id. Only admins can access this endpoint.
    """
    user_service = UserService()
    user = await user_service.get_user_by_id(user_id)
    return user


@router.patch("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> Any:
    """
    Update a user. Only admins can access this endpoint.
    """
    user_service = UserService()
    user = await user_service.update_user(user_id, user_in)
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> Any:
    """
    Delete a user. Only admins can access this endpoint.
    """
    user_service = UserService()
    return await user_service.delete_user(user_id)


@router.get("/roles", response_model=List[Dict[str, Any]])
async def read_roles(
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> Any:
    """
    Get all available roles. Only admins can access this endpoint.
    """
    user_service = UserService()
    return await user_service.get_all_roles()


@router.get("/permissions", response_model=List[Dict[str, Any]])
async def read_permissions(
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> Any:
    """
    Get all available permissions. Only admins can access this endpoint.
    """
    user_service = UserService()
    return await user_service.get_all_permissions()
