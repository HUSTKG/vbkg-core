from typing import Optional, List
from pydantic import BaseModel, UUID4, Field
from datetime import datetime

class NotificationBase(BaseModel):
    """Base model for notification data."""
    title: str
    message: str
    icon: Optional[str] = None
    link: Optional[str] = None

class NotificationCreate(NotificationBase):
    """Model for creating a new notification."""
    user_id: UUID4
    is_read: Optional[bool] = False

class NotificationUpdate(BaseModel):
    """Model for updating an existing notification."""
    title: Optional[str] = None
    message: Optional[str] = None
    icon: Optional[str] = None
    link: Optional[str] = None
    is_read: Optional[bool] = None

class Notification(NotificationBase):
    """Complete notification model returned from API."""
    id: UUID4
    user_id: UUID4
    is_read: bool = False
    created_at: datetime
    
    class Config:
        orm_mode = True

class NotificationInDB(Notification):
    """Model for notification stored in database."""
    pass

class BatchNotificationCreate(BaseModel):
    """Model for creating notifications for multiple users."""
    user_ids: List[UUID4]
    notification: NotificationBase

class NotificationCount(BaseModel):
    """Model for notification count."""
    total: int
    unread: int

class MarkNotificationsAsRead(BaseModel):
    """Model for marking multiple notifications as read."""
    notification_ids: List[UUID4]
