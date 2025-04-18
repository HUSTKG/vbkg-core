from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List, Optional

from app.schemas.user import User, UserCreate, UserUpdate, UserWithRoles
from app.schemas.auth import RoleCreate, Role, RoleUpdate, Permission
from app.services.user import (
    get_users, get_user, update_user, delete_user,
    get_roles, create_role, update_role, delete_role,
    assign_role_to_user, remove_role_from_user,
    get_permissions, assign_permission_to_role, remove_permission_from_role
)
from app.api.deps import get_current_active_user, get_current_admin_user

router = APIRouter()

# User management endpoints
@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Retrieve users.
    """
    users = await get_users(skip=skip, limit=limit)
    return users

@router.get("/me", response_model=UserWithRoles)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.get("/{user_id}", response_model=UserWithRoles)
async def read_user(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Get a specific user by id.
    """
    user = await get_user(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return user

@router.put("/{user_id}", response_model=User)
async def update_user_endpoint(
    user_id: str,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Update a user.
    """
    user = await get_user(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    user = await update_user(user_id=user_id, user_in=user_in)
    return user

@router.delete("/{user_id}", response_model=User)
async def delete_user_endpoint(
    user_id: str,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Delete a user.
    """
    user = await get_user(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    user = await delete_user(user_id=user_id)
    return user

# Role management endpoints
@router.get("/roles/", response_model=List[Role])
async def read_roles(
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Retrieve roles.
    """
    roles = await get_roles()
    return roles

@router.post("/roles/", response_model=Role)
async def create_role_endpoint(
    role_in: RoleCreate,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Create new role.
    """
    role = await create_role(role_in=role_in)
    return role

@router.put("/roles/{role_id}", response_model=Role)
async def update_role_endpoint(
    role_id: int,
    role_in: RoleUpdate,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Update a role.
    """
    role = await update_role(role_id=role_id, role_in=role_in)
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found",
        )
    return role

@router.delete("/roles/{role_id}", response_model=Role)
async def delete_role_endpoint(
    role_id: int,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Delete a role.
    """
    role = await delete_role(role_id=role_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found",
        )
    return role

# User-role assignments
@router.post("/{user_id}/roles/{role_id}", response_model=UserWithRoles)
async def assign_role(
    user_id: str,
    role_id: int,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Assign a role to a user.
    """
    user = await assign_role_to_user(user_id=user_id, role_id=role_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User or role not found",
        )
    return user

@router.delete("/{user_id}/roles/{role_id}", response_model=UserWithRoles)
async def remove_role(
    user_id: str,
    role_id: int,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Remove a role from a user.
    """
    user = await remove_role_from_user(user_id=user_id, role_id=role_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User or role not found",
        )
    return user

# Permission management
@router.get("/permissions/", response_model=List[Permission])
async def read_permissions(
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Retrieve permissions.
    """
    permissions = await get_permissions()
    return permissions

@router.post("/roles/{role_id}/permissions/{permission_id}")
async def assign_permission(
    role_id: int,
    permission_id: int,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Assign a permission to a role.
    """
    success = await assign_permission_to_role(role_id=role_id, permission_id=permission_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Role or permission not found",
        )
    return {"message": "Permission assigned successfully"}

@router.delete("/roles/{role_id}/permissions/{permission_id}")
async def remove_permission(
    role_id: int,
    permission_id: int,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Remove a permission from a role.
    """
    success = await remove_permission_from_role(role_id=role_id, permission_id=permission_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Role or permission not found",
        )
    return {"message": "Permission removed successfully"}
