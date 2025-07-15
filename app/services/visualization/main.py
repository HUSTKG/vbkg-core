from typing import Any, Dict, Optional

from postgrest.base_request_builder import APIResponse

from app.schemas.visualization import (VisualizationCreate, VisualizationData,
                                       VisualizationType, VisualizationUpdate)

from .activity_logging import VisualizationActivityService
from .configuration import VisualizationConfigService
from .data_fetching import VisualizationDataService
from .management import VisualizationManagementService
from .transformation import VisualizationTransformationService


class VisualizationService:
    """Main facade service for all visualization operations"""

    def __init__(self):
        self.management_service = VisualizationManagementService()
        self.data_service = VisualizationDataService()
        self.transformation_service = VisualizationTransformationService()
        self.config_service = VisualizationConfigService()
        self.activity_service = VisualizationActivityService()

    # Visualization Management - delegate to ManagementService
    async def create_visualization(
        self, visualization_in: VisualizationCreate, user_id: str
    ) -> Dict[str, Any]:
        visualization = await self.management_service.create_visualization(
            visualization_in, user_id
        )

        # Log activity
        await self.activity_service.log_visualization_created(user_id, visualization)

        return visualization

    async def get_visualization(self, visualization_id: str) -> Dict[str, Any]:
        visualization = await self.management_service.get_visualization(
            visualization_id
        )

        # Log activity
        await self.activity_service.log_visualization_viewed(
            visualization["created_by"], visualization
        )

        return visualization

    async def update_visualization(
        self, visualization_id: str, visualization_in: VisualizationUpdate
    ) -> Dict[str, Any]:
        visualization = await self.management_service.update_visualization(
            visualization_id, visualization_in
        )

        # Log activity
        await self.activity_service.log_visualization_updated(
            visualization["created_by"], visualization
        )

        return visualization

    async def delete_visualization(self, visualization_id: str) -> Dict[str, Any]:
        # Get visualization before deletion for logging
        visualization = await self.management_service.get_visualization(
            visualization_id
        )

        result = await self.management_service.delete_visualization(visualization_id)

        # Log activity
        await self.activity_service.log_visualization_deleted(
            visualization["created_by"], visualization_id
        )

        return result

    async def get_visualizations(
        self,
        user_id: Optional[str] = None,
        type: Optional[VisualizationType] = None,
        is_public: Optional[bool] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        result = await self.management_service.get_visualizations(
            user_id, type, is_public, limit, skip
        )

        # Log activity
        filters = {
            "user_id": user_id,
            "type": type,
            "is_public": is_public,
            "limit": limit,
            "skip": skip,
        }
        await self.activity_service.log_visualizations_listed(user_id, filters)

        return result

    # Visualization Data - delegate to DataService and TransformationService
    async def get_visualization_data(
        self, visualization_id: str, params: Optional[Dict[str, Any]] = None
    ) -> VisualizationData:
        # Get visualization configuration
        visualization = await self.management_service.get_visualization(
            visualization_id
        )

        # Fetch raw data
        raw_data = await self.data_service.fetch_visualization_data(
            visualization, params
        )

        # Transform data for visualization
        result = self.transformation_service.transform_data_for_visualization(
            raw_data, visualization
        )

        # Log activity
        await self.activity_service.log_visualization_data_viewed(
            visualization["created_by"],
            visualization,
            result.metadata.get("record_count", 0),
        )

        return result
