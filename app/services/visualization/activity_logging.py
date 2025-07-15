from typing import Any, Dict, Optional

from app.services.user import UserService

from .base import BaseVisualizationService


class VisualizationActivityService(BaseVisualizationService):
    """Service for logging visualization-related user activities"""
    
    def __init__(self):
        super().__init__()
        self.user_service = UserService()
    
    async def log_visualization_created(
        self, 
        user_id: str, 
        visualization: Dict[str, Any]
    ):
        """Log visualization creation activity"""
        
        await self.user_service._log_user_activity(
            user_id,
            action="create_visualization",
            resource_id=visualization["id"],
            resource_type="visualization",
            details={
                "visualization_id": visualization["id"],
                "name": visualization["name"],
                "type": visualization.get("visualization_type"),
            },
        )
    
    async def log_visualization_viewed(
        self, 
        user_id: str, 
        visualization: Dict[str, Any]
    ):
        """Log visualization view activity"""
        
        await self.user_service._log_user_activity(
            user_id=user_id,
            action="view_visualization",
            resource_id=visualization["id"],
            resource_type="visualization",
            details={
                "visualization_id": visualization["id"],
                "name": visualization["name"],
            },
        )
    
    async def log_visualization_updated(
        self, 
        user_id: str, 
        visualization: Dict[str, Any]
    ):
        """Log visualization update activity"""
        
        await self.user_service._log_user_activity(
            user_id=user_id,
            action="update_visualization",
            resource_id=visualization["id"],
            resource_type="visualization",
            details={
                "visualization_id": visualization["id"],
                "name": visualization["name"],
            },
        )
    
    async def log_visualization_deleted(
        self, 
        user_id: str, 
        visualization_id: str
    ):
        """Log visualization deletion activity"""
        
        await self.user_service._log_user_activity(
            user_id=user_id,
            action="delete_visualization",
            resource_id=visualization_id,
            resource_type="visualization",
            details={"visualization_id": visualization_id},
        )
    
    async def log_visualizations_listed(
        self, 
        user_id: Optional[str], 
        filters: Dict[str, Any]
    ):
        """Log visualization listing activity"""
        
        if user_id:
            await self.user_service._log_user_activity(
                user_id=user_id,
                action="list_visualizations",
                resource_type="visualization",
                details={
                    "filter": filters,
                },
            )
    
    async def log_visualization_data_viewed(
        self, 
        user_id: str, 
        visualization: Dict[str, Any], 
        record_count: int
    ):
        """Log visualization data view activity"""
        
        await self.user_service._log_user_activity(
            user_id=user_id,
            action="view_visualization_data",
            resource_id=visualization["id"],
            resource_type="visualization",
            details={
                "visualization_id": visualization["id"],
                "name": visualization["name"],
                "type": visualization.get("visualization_type"),
                "record_count": record_count,
            },
        )
