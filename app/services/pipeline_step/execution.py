from typing import Any, Dict, Optional

from fastapi import HTTPException
from fastapi import status as HttpStatus
from postgrest.base_request_builder import APIResponse

from app.schemas.pipeline_step import PipelineStepRunCreate, PipelineStepRunUpdate

from .base import BasePipelineStepService


class PipelineStepExecutionService(BasePipelineStepService):
    """Service for pipeline step execution and runs"""

    async def create_step_run(
        self, step_run_in: PipelineStepRunCreate
    ) -> Dict[str, Any]:
        """Create a new pipeline step run"""
        try:
            supabase = await self.get_supabase()

            step_run_data = step_run_in.model_dump(exclude_unset=True)

            # Process datetime fields
            if "start_time" in step_run_data and step_run_data["start_time"]:
                step_run_data["start_time"] = step_run_data["start_time"].isoformat()
            if "end_time" in step_run_data and step_run_data["end_time"]:
                step_run_data["end_time"] = step_run_data["end_time"].isoformat()

            response = (
                await supabase.from_("pipeline_step_runs")
                .insert(step_run_data)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline step run",
                )

            return response.data[0]

        except Exception as e:
            self.logger.error(f"Error creating pipeline step run: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline step run: {str(e)}",
            )

    async def get_pipeline_step_run(self, step_run_id: str) -> Dict[str, Any]:
        """Get a pipeline step run by ID"""
        try:
            supabase = await self.get_supabase()
            response = (
                await supabase.from_("pipeline_step_runs")
                .select("*")
                .filter("id", "eq", step_run_id)
                .maybe_single()
                .execute()
            )

            if not response:
                raise HTTPException(
                    status_code=HttpStatus.HTTP_404_NOT_FOUND,
                    detail="Pipeline step run not found",
                )

            return response.data

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving pipeline step run {step_run_id}: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline step run: {str(e)}",
            )

    async def update_pipeline_step_run(
        self,
        step_run_id: str,
        step_run_update: PipelineStepRunUpdate,
    ) -> Dict[str, Any]:
        """Update a pipeline step run"""
        try:
            supabase = await self.get_supabase()

            update_data = step_run_update.model_dump(exclude_unset=True)

            # Process datetime fields
            if "start_time" in update_data and update_data["start_time"]:
                update_data["start_time"] = update_data["start_time"]
            if "end_time" in update_data and update_data["end_time"]:
                update_data["end_time"] = update_data["end_time"]

            response = (
                await supabase.from_("pipeline_step_runs")
                .update(update_data)
                .eq("id", step_run_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline step run",
                )

            return response.data[0]

        except Exception as e:
            self.logger.error(f"Error updating pipeline step run {step_run_id}: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline step run: {str(e)}",
            )

    async def delete_pipeline_step_run(self, step_run_id: str) -> Dict[str, Any]:
        """Delete a pipeline step run"""
        try:
            # Check if step run exists
            await self.get_pipeline_step_run(step_run_id)

            supabase = await self.get_supabase()
            await supabase.from_("pipeline_step_runs").delete().eq(
                "id", step_run_id
            ).execute()

            return {"success": True, "message": "Pipeline step run deleted"}

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting pipeline step run {step_run_id}: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting pipeline step run: {str(e)}",
            )

    async def get_pipeline_step_runs(
        self,
        pipeline_run_id: str,
        step_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get pipeline step runs with filtering and pagination"""
        try:
            supabase = await self.get_supabase()
            query = (
                supabase.from_("pipeline_step_runs")
                .select("*")
                .filter("pipeline_run_id", "eq", pipeline_run_id)
            )

            # Apply filters
            if step_id:
                query = query.filter("step_id", "eq", step_id)
            if status:
                query = query.filter("status", "eq", status)

            response = (
                await query.order("created_at", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )

            # Process complex JSON fields if they exist
            # if response.data:
            #     for step_run in response.data:
            #         # Keep JSON fields as they are (already parsed by Supabase)
            #         pass

            return response

        except Exception as e:
            self.logger.error(f"Error retrieving pipeline step runs: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline step runs: {str(e)}",
            )
