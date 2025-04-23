from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Any, List, Optional

from app.schemas.notification import Notification, NotificationCreate, NotificationUpdate
from app.schemas.user import User
from app.schemas.api import ApiResponse, PaginatedResponse
from app.services.notification import NotificationService 
from app.api.deps import get_current_active_admin, get_current_active_user

router = APIRouter()

notification_service = NotificationService()
@router.get("/", response_model=PaginatedResponse[Notification])
async def read_notifications(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
) -> PaginatedResponse[Notification]:
    """
    Retrieve notifications for current user.
    """
    notifications = await notification_service.get_user_notifications(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    return PaginatedResponse(
        data=notifications.data,
        meta={
            "total": notifications.count,
            "skip": skip,
            "limit": limit,
        },
        status=status.HTTP_200_OK,
        message="Notifications retrieved successfully"
    )

@router.get("/{notification_id}", response_model=ApiResponse[Notification])
async def read_notification(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
) -> ApiResponse[Notification]:
    """
    Get a specific notification.
    """
    notification = await notification_service.get_notification(
        user_id=current_user.id,
        notification_id=notification_id
    )

    return ApiResponse(
        data=notification,
        status=status.HTTP_200_OK,
        message="Notification retrieved successfully"
    )

@router.post("/", response_model=ApiResponse[Notification])
async def create_notification_endpoint(
    notification_in: NotificationCreate,
    current_user: User = Depends(get_current_active_admin),
) -> ApiResponse[Notification]:
    """
    Create new notification (admin only).
    """
    
    notification = await notification_service.create_notification(
        user_id=current_user.id,
        title=notification_in.title,
        message=notification_in.message,
        icon=notification_in.icon,
    )
    return ApiResponse(
        data=notification,
        status=status.HTTP_201_CREATED,
        message="Notification created successfully"
    )

@router.put("/{notification_id}/read", response_model=ApiResponse[Notification])
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user),
) -> ApiResponse[Notification]:
    """
    Mark a notification as read.
    """
    notification = await notification_service.get_notification(
        user_id=current_user.id,
        notification_id=notification_id
    )
    
    notification = await notification_service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.id
    )
    return ApiResponse(
        data=notification,
        status=status.HTTP_200_OK,
        message="Notification marked as read successfully"
    )

@router.put("/{notification_id}", response_model=ApiResponse[Notification])
async def update_notification_endpoint(
    notification_id: str,
    notification_in: NotificationUpdate,
    current_user: User = Depends(get_current_active_admin),
) -> ApiResponse[Notification]:
    """
    Update a notification (admin only).
    """
    
    notification = await notification_service.get_notification(
        user_id=current_user.id,
        notification_id=notification_id
    )
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )
    
    notification = await notification_service.update_notification(
        notification_id=notification_id, 
        title=notification_in.title,
        message=notification_in.message,
        icon=notification_in.icon,
        is_read=notification_in.is_read,
        user_id=current_user.id,
    )
    return ApiResponse(
        data=notification,
        status=status.HTTP_200_OK,
        message="Notification updated successfully"
    )

@router.delete("/{notification_id}", response_model=ApiResponse[Notification])
async def delete_notification_endpoint(
    notification_id: str,
    current_user: User = Depends(get_current_active_admin),
) -> ApiResponse[Notification]:
    """
    Delete a notification (admin only).
    """
    
    notification = await notification_service.get_notification(
        user_id=current_user.id,
        notification_id=notification_id
    )
    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )
    
    notification = await notification_service.delete_notification(
        user_id=current_user.id,
        notification_id=notification_id
    )
    return ApiResponse(
        data=notification,
        status=status.HTTP_200_OK,
        message="Notification deleted successfully"
    )
