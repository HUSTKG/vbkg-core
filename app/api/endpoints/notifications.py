from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Any, List, Optional

from app.schemas.notification import Notification, NotificationCreate, NotificationUpdate
from app.schemas.user import User
from app.services.notification import (
    get_notifications, get_notification, create_notification, 
    update_notification, delete_notification, mark_as_read
)
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[Notification])
async def read_notifications(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve notifications for current user.
    """
    notifications = await get_notifications(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    return notifications

@router.get("/{notification_id}", response_model=Notification)
async def read_notification(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific notification.
    """
    notification = await get_notification(notification_id=notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )
    return notification

@router.post("/", response_model=Notification)
async def create_notification_endpoint(
    notification_in: NotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new notification (admin only).
    """
    # Check if user has admin role
    if "admin" not in [role.name for role in current_user.roles]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions",
        )
    
    notification = await create_notification(notification_in=notification_in)
    return notification

@router.put("/{notification_id}/read", response_model=Notification)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Mark a notification as read.
    """
    notification = await get_notification(notification_id=notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )
    
    notification = await mark_as_read(notification_id=notification_id)
    return notification

@router.put("/{notification_id}", response_model=Notification)
async def update_notification_endpoint(
    notification_id: str,
    notification_in: NotificationUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a notification (admin only).
    """
    # Check if user has admin role
    if "admin" not in [role.name for role in current_user.roles]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions",
        )
    
    notification = await get_notification(notification_id=notification_id)
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )
    
    notification = await update_notification(
        notification_id=notification_id, 
        notification_in=notification_in
    )
    return notification

@router.delete("/{notification_id}", response_model=Notification)
async def delete_notification_endpoint(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a notification (admin only).
    """
    # Check if user has admin role
    if "admin" not in [role.name for role in current_user.roles]:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions",
        )
    
    notification = await get_notification(notification_id=notification_id)
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )
    
    notification = await delete_notification(notification_id=notification_id)
    return notification
