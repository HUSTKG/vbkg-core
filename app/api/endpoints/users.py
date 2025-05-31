from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (RequireAPIAccess, RequireUserManagement,
                          get_current_user)
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.user import User, UserUpdate
from app.services.user import UserService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[Dict[str, Any]])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    role_filter: Optional[str] = Query(None, description="Filter by role"),
    department_filter: Optional[str] = Query(None, description="Filter by department"),
    current_user: Dict[str, Any] = Depends(RequireUserManagement),
) -> PaginatedResponse[Dict[str, Any]]:
    """
    Retrieve users with advanced filtering. Only admins can access this endpoint.
    """
    user_service = UserService()
    response = await user_service.get_users(
        skip=skip,
        limit=limit,
        role_filter=role_filter,
        department_filter=department_filter,
    )

    return PaginatedResponse(
        data=response.data,
        meta=PaginatedMeta(
            total=response.count,
            skip=skip,
            limit=limit,
        ),
        status=status.HTTP_200_OK,
        message="Users retrieved successfully",
    )


@router.get("/me", response_model=ApiResponse[Dict[str, Any]])
async def read_user_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ApiResponse[Dict[str, Any]]:
    """
    Get current user with enhanced information including permissions.
    """
    print("Current user:", current_user)  # Debugging line
    return ApiResponse(
        data=current_user,
        status=status.HTTP_200_OK,
        message="Current user retrieved successfully",
    )


@router.patch("/me", response_model=ApiResponse[User])
async def update_user_me(
    user_in: UserUpdate, current_user: Dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[User]:
    """
    Update current user information. Users cannot change their own roles.
    """
    user_service = UserService()

    # Prevent a user from changing their own roles
    if hasattr(user_in, "roles") and user_in.roles is not None:
        user_in.roles = None

    response = await user_service.update_user(current_user["id"], user_in)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Current user updated successfully",
    )


@router.get("/permissions", response_model=ApiResponse[List[Dict[str, Any]]])
async def read_permissions(
    current_user: Dict[str, Any] = Depends(RequireUserManagement),
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    Get all available permissions. Only admins can access this endpoint.
    """
    user_service = UserService()
    response = await user_service.get_all_permissions()
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Permissions retrieved successfully",
    )



# Role Management Endpoints
@router.get("/roles", response_model=ApiResponse[List[Dict[str, Any]]])
async def read_roles(
    current_user: Dict[str, Any] = Depends(RequireUserManagement),
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    Get all available roles. Only admins can access this endpoint.
    """
    user_service = UserService()
    response = await user_service.get_all_roles()
    return ApiResponse(
        data=response, status=status.HTTP_200_OK, message="Roles retrieved successfully"
    )


@router.get("/{user_id}", response_model=ApiResponse[User])
async def read_user(
    user_id: str, current_user: Dict[str, Any] = Depends(RequireUserManagement)
) -> ApiResponse[User]:
    """
    Get a specific user by id. Only admins can access this endpoint.
    """
    user_service = UserService()
    user = await user_service.get_user_by_id(user_id)
    return ApiResponse(
        data=user, status=status.HTTP_200_OK, message="User retrieved successfully"
    )


@router.patch("/{user_id}", response_model=ApiResponse[User])
async def update_user(
    user_id: str,
    user_in: UserUpdate,
    current_user: Dict[str, Any] = Depends(RequireUserManagement),
) -> ApiResponse[User]:
    """
    Update a user including roles. Only admins can access this endpoint.
    """
    user_service = UserService()
    user = await user_service.update_user(user_id, user_in)
    return ApiResponse(
        data=user, status=status.HTTP_200_OK, message="User updated successfully"
    )


@router.delete("/{user_id}", response_model=ApiResponse[None])
async def delete_user(
    user_id: str, current_user: Dict[str, Any] = Depends(RequireUserManagement)
) -> ApiResponse[None]:
    """
    Delete a user. Only admins can access this endpoint.
    """
    from app.services.user import UserService

    user_service = UserService()  # Use original service for deletion
    response = await user_service.delete_user(user_id)
    return ApiResponse(
        data=None, status=status.HTTP_200_OK, message="User deleted successfully"
    )


# API Key Management Endpoints
@router.post("/api-keys", response_model=ApiResponse[Dict[str, Any]])
async def create_api_key(
    name: str,
    description: Optional[str] = None,
    expires_days: Optional[int] = None,
    rate_limit: int = 1000,
    current_user: Dict[str, Any] = Depends(RequireAPIAccess),
) -> ApiResponse[Dict[str, Any]]:
    """
    Create new API key for current user.
    """
    from datetime import datetime, timedelta

    user_service = UserService()

    expires_at = None
    if expires_days:
        expires_at = datetime.now() + timedelta(days=expires_days)

    api_key = await user_service.create_api_key(
        user_id=current_user["id"],
        name=name,
        description=description,
        expires_at=expires_at,
        rate_limit=rate_limit,
    )

    return ApiResponse(
        data=api_key,
        status=status.HTTP_201_CREATED,
        message="API key created successfully",
    )


@router.get("/api-keys", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_user_api_keys(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    Get current user's API keys.
    """
    user_service = UserService()
    api_keys = await user_service.get_user_api_keys(current_user["id"])

    return ApiResponse(
        data=api_keys,
        status=status.HTTP_200_OK,
        message="API keys retrieved successfully",
    )


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[Dict[str, str]]:
    """
    Revoke API key.
    """
    user_service = UserService()
    success = await user_service.revoke_api_key(api_key_id, current_user["id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    return ApiResponse(
        data={"message": "API key revoked successfully"},
        status=status.HTTP_200_OK,
        message="API key revoked",
    )


@router.get("/me/activity", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_my_activity(
    limit: int = 50,
    skip: int = 0,
    action_filter: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    Get current user's activity history.
    """
    user_service = UserService()
    activities = await user_service.get_user_activity(
        user_id=current_user["id"], limit=limit, skip=skip, action_filter=action_filter
    )

    return ApiResponse(
        data=activities,
        status=status.HTTP_200_OK,
        message="User activity retrieved successfully",
    )


@router.get("/{user_id}/activity", response_model=ApiResponse[List[Dict[str, Any]]])
async def get_user_activity(
    user_id: str,
    limit: int = 50,
    skip: int = 0,
    action_filter: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(RequireUserManagement),
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    Get specific user's activity history. Admin only.
    """
    user_service = UserService()
    activities = await user_service.get_user_activity(
        user_id=user_id, limit=limit, skip=skip, action_filter=action_filter
    )

    return ApiResponse(
        data=activities,
        status=status.HTTP_200_OK,
        message="User activity retrieved successfully",
    )



@router.post("/{user_id}/roles/{role_name}")
async def assign_role_to_user(
    user_id: str,
    role_name: str,
    current_user: Dict[str, Any] = Depends(RequireUserManagement),
) -> ApiResponse[Dict[str, str]]:
    """
    Assign a role to user. Admin only.
    """
    user_service = UserService()
    success = await user_service.assign_role_to_user(user_id, role_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to assign role"
        )

    return ApiResponse(
        data={"message": f"Role '{role_name}' assigned successfully"},
        status=status.HTTP_200_OK,
        message="Role assigned",
    )


@router.delete("/{user_id}/roles/{role_name}")
async def remove_role_from_user(
    user_id: str,
    role_name: str,
    current_user: Dict[str, Any] = Depends(RequireUserManagement),
) -> ApiResponse[Dict[str, str]]:
    """
    Remove a role from user. Admin only.
    """
    user_service = UserService()
    success = await user_service.remove_role_from_user(user_id, role_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to remove role"
        )

    return ApiResponse(
        data={"message": f"Role '{role_name}' removed successfully"},
        status=status.HTTP_200_OK,
        message="Role removed",
    )


# System Statistics (Admin Dashboard)
@router.get("/admin/stats", response_model=ApiResponse[Dict[str, Any]])
async def get_system_stats(
    current_user: Dict[str, Any] = Depends(RequireUserManagement),
) -> ApiResponse[Dict[str, Any]]:
    """
    Get system statistics for admin dashboard.
    """
    user_service = UserService()
    stats = await user_service.get_system_stats()

    return ApiResponse(
        data=stats,
        status=status.HTTP_200_OK,
        message="System statistics retrieved successfully",
    )
