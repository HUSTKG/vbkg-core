from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from datetime import datetime

from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.core.supabase import get_supabase


class NotificationService:
    """Service for managing notifications."""

    async def create_notification(
        self, 
        user_id: str, 
        title: str, 
        message: str, 
        icon: Optional[str] = None,
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new notification for a user"""
        try:
            supabase = await get_supabase() 
            data = {
                "user_id": user_id,
                "title": title,
                "message": message,
                "is_read": False,
                "created_at": datetime.utcnow().isoformat()
            }
            
            if icon:
                data["icon"] = icon
                
            if link:
                data["link"] = link
            
            response = await supabase.from_("notifications").insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create notification"
                )
                
            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating notification: {str(e)}"
            )

    async def get_user_notifications(
        self, 
        user_id: str, 
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> APIResponse[Dict[str, Any]]:
        """Get notifications for a user"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("notifications").select("*").eq("user_id", user_id)
            
            if unread_only:
                query = query.eq("is_read", False)
                
            response = await query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
            
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving notifications: {str(e)}"
            )
    async def get_notification(self, notification_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific notification for a user"""
        try:
            supabase = await get_supabase()
            response = await supabase.from_("notifications").select("*").eq("id", notification_id).eq("user_id", user_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving notification: {str(e)}"
            )

    async def mark_as_read(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        """Mark a notification as read"""
        try:
            supabase = await get_supabase()
            # First verify the notification belongs to the user
            check_response = await supabase.from_("notifications").select("id").eq("id", notification_id).eq("user_id", user_id).execute()
            
            if not check_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found"
                )
            
            response = await supabase.from_("notifications").update({"is_read": True}).eq("id", notification_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update notification"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating notification: {str(e)}"
            )

    async def update_notification(
        self,
        notification_id: str,
        user_id: str,
        title: Optional[str] = None,
        message: Optional[str] = None,
        icon: Optional[str] = None,
        is_read: Optional[bool] = None,
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a notification"""
        try:
            supabase = await get_supabase()
            # First verify the notification belongs to the user
            check_response = await supabase.from_("notifications").select("id").eq("id", notification_id).eq("user_id", user_id).execute()
            
            if not check_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found"
                )
            
            data = {}
            if title:
                data["title"] = title
            if message:
                data["message"] = message
            if icon:
                data["icon"] = icon
            if is_read is not None:
                data["is_read"] = is_read
            if link:
                data["link"] = link
            
            response = await supabase.from_("notifications").update(data).eq("id", notification_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update notification"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating notification: {str(e)}"
            )

    async def mark_all_as_read(self, user_id: str) -> Dict[str, Any]:
        """Mark all notifications for a user as read"""
        try:
            supabase = await get_supabase()
            await supabase.from_("notifications").update({"is_read": True}).eq("user_id", user_id).eq("is_read", False).execute()
            
            return {"success": True, "message": "All notifications marked as read"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating notifications: {str(e)}"
            )

    async def delete_notification(self, notification_id: str, user_id: str) -> Dict[str, Any]:
        """Delete a notification"""
        try:
            supabase = await get_supabase()
            # First verify the notification belongs to the user
            check_response = await supabase.from_("notifications").select("id").eq("id", notification_id).eq("user_id", user_id).execute()
            
            if not check_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Notification not found"
                )
            
            await supabase.from_("notifications").delete().eq("id", notification_id).execute()
            
            return {"success": True, "message": "Notification deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting notification: {str(e)}"
            )

    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        try:
            supabase = await get_supabase() 
            response = await supabase.from_("notifications").select("id", count=CountMethod.exact).eq("user_id", user_id).eq("is_read", False).execute()
            
            return response.count or 0
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error counting notifications: {str(e)}"
            )
