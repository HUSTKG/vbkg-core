from typing import Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.api.deps import get_current_user, get_current_active_admin
from app.schemas.api import ApiResponse, PaginatedResponse
from app.schemas.user import User, UserUpdate
from app.services.user import UserService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


@router.get("/", response_model=PaginatedResponse[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> PaginatedResponse[User]:
    """
    Retrieve users. Only admins can access this endpoint.
    """
    user_service = UserService()
    response = await user_service.get_users(skip=skip, limit=limit)
    return PaginatedResponse(
        data=response.data,
        meta={
            "total": response.count,
            "skip": skip,
            "limit": limit,
        },
        status=status.HTTP_200_OK,
        message="Users retrieved successfully"
    )

@router.get("/me", response_model=ApiResponse[User])
async def read_user_me(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[User]:
    """
    Get current user.
    """
    return ApiResponse( 
        data=current_user,
        status=status.HTTP_200_OK,
        message="Current user retrieved successfully"
    )


@router.patch("/me", response_model=ApiResponse[User])
async def update_user_me(
    user_in: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[User]:
    """
    Update current user information.
    """
    user_service = UserService()
    # Prevent a user from changing their own roles
    if hasattr(user_in, "roles") and user_in.roles is not None:
        user_in.roles = None
    
    response = await user_service.update_user(current_user["id"], user_in)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Current user updated successfully"
    )


@router.get("/{user_id}", response_model=ApiResponse[User])
async def read_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> ApiResponse[User]:
    """
    Get a specific user by id. Only admins can access this endpoint.
    """
    user_service = UserService()
    user = await user_service.get_user_by_id(user_id)
    return ApiResponse(
        data=user,
        status=status.HTTP_200_OK,
        message="User retrieved successfully"
    )

@router.patch("/{user_id}", response_model=ApiResponse[User])
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> ApiResponse[User]:
    """
    Update a user. Only admins can access this endpoint.
    """
    user_service = UserService()
    user = await user_service.update_user(user_id, user_in)
    return ApiResponse(
        data=user,
        status=status.HTTP_200_OK,
        message="User updated successfully"
    )


@router.delete("/{user_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete a user. Only admins can access this endpoint.
    """
    user_service = UserService()
    response = await user_service.delete_user(user_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="User deleted successfully"
    )


@router.get("/roles", response_model=ApiResponse[List[Dict[str, Any]]])
async def read_roles(
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    Get all available roles. Only admins can access this endpoint.
    """
    user_service = UserService()
    response = await user_service.get_all_roles()
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Roles retrieved successfully"
    )

@router.get("/permissions", response_model=ApiResponse[List[Dict[str, Any]]])
async def read_permissions(
    current_user: Dict[str, Any] = Depends(get_current_active_admin)
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    Get all available permissions. Only admins can access this endpoint.
    """
    user_service = UserService()
    response = await user_service.get_all_permissions()
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Permissions retrieved successfully"
    )
