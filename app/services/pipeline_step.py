import json
from typing import Any, Dict

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse

from app.core.supabase import get_supabase
from app.schemas.pipeline_step import PipelineStepCreate


class PipelineStepService:
    """Service for managing pipeline steps and their execution."""

    # Manage pipeline steps
    async def create_pipeline_step(
        self, step_in: PipelineStepCreate, pipeline_id: str
    ) -> Dict[str, Any]:
        """Create a new pipeline step"""
        try:
            supabase = await get_supabase()
            step_dict = step_in.model_dump()
            if pipeline_id:
                step_dict["pipeline_id"] = pipeline_id

            response = (
                await supabase.from_("pipeline_steps").insert(step_dict).execute()
            )
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline step",
                )
            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline step: {str(e)}",
            )

    async def get_pipeline_step(self, step_id: str, pipeline_id: str) -> Dict[str, Any]:
        """Get a pipeline step by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_steps")
                .select("*")
                .filter("id", "eq", step_id)
                .filter("pipeline_id", "eq", pipeline_id)
                .single()
                .execute()
            )
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline step not found",
                )
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline step: {str(e)}",
            )

    async def update_pipeline_step(
        self, step_id: str, step_in: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a pipeline step"""
        try:
            supabase = await get_supabase()
            # Check if step exists
            await self.get_pipeline_step(
                step_id=step_id, pipeline_id=step_in["pipeline_id"]
            )
            # Update step
            response = (
                await supabase.from_("pipeline_steps")
                .update(step_in)
                .eq("id", step_id)
                .execute()
            )
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline step",
                )
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline step: {str(e)}",
            )

    async def delete_pipeline_step(self, step_id: str, pipeline_id: str) -> Dict[str, Any]:
        """Delete a pipeline step"""
        try:
            supabase = await get_supabase()
            # Check if step exists
            await self.get_pipeline_step(step_id, pipeline_id)
            # Delete step
            await supabase.from_("pipeline_steps").delete().eq("id", step_id).execute()
            return {"success": True, "message": "Pipeline step deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting pipeline step: {str(e)}",
            )

    async def get_pipeline_steps(
        self, pipeline_id: str, limit: int = 100, skip: int = 0
    ) -> APIResponse[Dict[str, Any]]:
        """Get pipeline steps with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = (
                supabase.from_("pipeline_steps")
                .select("*")
                .eq("pipeline_id", pipeline_id)
            )
            response = (
                await query.order("created_at", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )
            data = [
                {
                    "name": data["name"],
                    "step_type": data["step_type"],
                    "config": json.loads(data["config"]),
                    "run_order": data["run_order"],
                    # split string into list
                    "inputs": [
                        input.strip()
                        for input in data["inputs"].split(",")
                        if input.strip()
                    ],
                    "enabled": data["enabled"],
                    "id": data["id"],
                    "pipeline_id": data["pipeline_id"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                }
                for data in response.data
            ]  # Convert to PipelineStep model
            return APIResponse(data=data, count=response.count)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline steps: {str(e)}",
            )

    async def get_pipeline_step_runs(
        self, pipeline_run_id: str, limit: int = 100, skip: int = 0
    ) -> APIResponse[Dict[str, Any]]:
        """Get pipeline step runs with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = (
                supabase.from_("pipeline_step_runs")
                .select("*")
                .eq("pipeline_run_id", pipeline_run_id)
            )
            response = (
                await query.order("created_at", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline step runs: {str(e)}",
            )

    async def get_pipeline_step_run(
        self, pipeline_run_id: str, step_run_id: str
    ) -> Dict[str, Any]:
        """Get a pipeline step run by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_step_runs")
                .select("*")
                .filter("id", "eq", step_run_id)
                .filter("pipeline_run_id", "eq", pipeline_run_id)
                .single()
                .execute()
            )
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline step run not found",
                )
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline step run: {str(e)}",
            )

    async def create_step_run(self, step_run_in: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pipeline step run"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_step_runs").insert(step_run_in).execute()
            )
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline step run",
                )
            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline step run: {str(e)}",
            )

    async def update_pipeline_step_run(
        self, step_run_id: str, pipeline_run_id: str, step_run_in: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a pipeline step run"""
        try:
            supabase = await get_supabase()
            # Check if step run exists
            await self.get_pipeline_step_run(step_run_id, pipeline_run_id)
            # Update step run
            response = (
                await supabase.from_("pipeline_step_runs")
                .update(step_run_in)
                .eq("id", step_run_id)
                .execute()
            )
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline step run",
                )
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline step run: {str(e)}",
            )

    async def delete_pipeline_step_run(self, step_run_id: str, pipeline_run_id: str) -> Dict[str, Any]:
        """Delete a pipeline step run"""
        try:
            supabase = await get_supabase()
            # Check if step run exists
            await self.get_pipeline_step_run(step_run_id, pipeline_run_id)
            # Delete step run
            await supabase.from_("pipeline_step_runs").delete().eq(
                "id", step_run_id
            ).execute()
            return {"success": True, "message": "Pipeline step run deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting pipeline step run: {str(e)}",
            )
