from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse

from app.schemas.visualization import (VisualizationCreate, VisualizationType,
                                       VisualizationUpdate)

from .base import BaseVisualizationService


class VisualizationManagementService(BaseVisualizationService):
    """Service for visualization CRUD operations"""
    
    async def create_visualization(
        self, 
        visualization_in: VisualizationCreate, 
        user_id: str
    ) -> Dict[str, Any]:
        """Create a new visualization"""
        try:
            # Validate input
            self._validate_visualization_input(visualization_in)
            
            supabase = await self.get_supabase()
            
            # Prepare data
            data = visualization_in.model_dump()
            data["created_by"] = user_id
            
            # Insert into database
            response = await supabase.from_("visualizations").insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create visualization"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error creating visualization: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating visualization: {str(e)}"
            )
    
    async def get_visualization(self, visualization_id: str) -> Dict[str, Any]:
        """Get a visualization by ID"""
        try:
            supabase = await self.get_supabase()
            response = await supabase.from_("visualizations").select("*").eq("id", visualization_id).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Visualization not found"
                )
            
            return response.data
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving visualization {visualization_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving visualization: {str(e)}"
            )
    
    async def update_visualization(
        self, 
        visualization_id: str, 
        visualization_in: VisualizationUpdate
    ) -> Dict[str, Any]:
        """Update a visualization"""
        try:
            # Check if visualization exists
            await self.get_visualization(visualization_id)
            
            supabase = await self.get_supabase()
            
            # Update visualization
            data = visualization_in.model_dump(exclude_unset=True)
            response = await supabase.from_("visualizations").update(data).eq("id", visualization_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update visualization"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating visualization {visualization_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating visualization: {str(e)}"
            )
    
    async def delete_visualization(self, visualization_id: str) -> Dict[str, Any]:
        """Delete a visualization"""
        try:
            # Check if visualization exists
            await self.get_visualization(visualization_id)
            
            supabase = await self.get_supabase()
            
            # Delete visualization
            await supabase.from_("visualizations").delete().eq("id", visualization_id).execute()
            
            return {"success": True, "message": "Visualization deleted"}
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting visualization {visualization_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting visualization: {str(e)}"
            )
    
    async def get_visualizations(
        self,
        user_id: Optional[str] = None,
        type: Optional[VisualizationType] = None,
        is_public: Optional[bool] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get visualizations with filtering and pagination"""
        try:
            supabase = await self.get_supabase()
            query = supabase.from_("visualizations").select("*")
            
            # Apply filters
            filters = {
                "created_by": user_id,
                "is_public": is_public
            }
            
            for field, value in filters.items():
                if value is not None:
                    query = query.eq(field, value)
            
            if type:
                query = query.eq("config->>type", type.value)
            
            # Apply pagination and order
            response = await query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error retrieving visualizations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving visualizations: {str(e)}"
            )
    
    def _validate_visualization_input(self, visualization_in: VisualizationCreate):
        """Validate visualization input"""
        if (
            not visualization_in.query_id
            and not visualization_in.cypher_query
            and not visualization_in.entity_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of query_id, cypher_query, or entity_id must be provided"
            )
