from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from datetime import datetime, timezone
from postgrest.base_request_builder import APIResponse
from pydantic import UUID4
from app.core.supabase import get_supabase
from app.schemas.pipeline import (
    Pipeline,
    PipelineCreate,
    PipelineStep,
    PipelineUpdate,
    PipelineRunStatus,
    PipelineRunCreate,
    PipelineRunUpdate,
)


class PipelineService:
    """Service for managing pipelines and their execution."""

    async def create_pipeline(self, pipeline_in: PipelineCreate) -> Dict[str, Any]:
        """Create a new pipeline"""
        try:
            supabase = await get_supabase()

            pipeline_dict = pipeline_in.model_dump()

            response = await supabase.from_("pipelines").insert(pipeline_dict).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline",
                )

            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline: {str(e)}",
            )

    async def get_pipeline(self, pipeline_id: UUID4) -> Dict[str, Any]:
        """Get a pipeline by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipelines")
                .select("*")
                .eq("id", pipeline_id)
                .single()
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline: {str(e)}",
            )

    async def update_pipeline(
        self, pipeline_id: UUID4, pipeline_in: PipelineUpdate
    ) -> Dict[str, Any]:
        """Update a pipeline"""
        try:
            supabase = await get_supabase()
            # Check if pipeline exists
            await self.get_pipeline(pipeline_id)

            # Update pipeline
            data = pipeline_in.model_dump(exclude_unset=True)

            response = (
                await supabase.from_("pipelines")
                .update(data)
                .eq("id", pipeline_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline: {str(e)}",
            )

    async def delete_pipeline(self, pipeline_id: UUID4) -> Dict[str, Any]:
        """Delete a pipeline"""
        try:
            supabase = await get_supabase()
            # Check if pipeline exists
            await self.get_pipeline(pipeline_id)

            # Delete pipeline
            await supabase.from_("pipelines").delete().eq("id", pipeline_id).execute()

            return {"success": True, "message": "Pipeline deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting pipeline: {str(e)}",
            )

    async def get_pipelines(
        self,
        pipeline_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_by: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Pipeline]:
        """Get pipelines with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("pipelines").select("*")

            if pipeline_type:
                query = query.eq("pipeline_type", pipeline_type)

            if is_active is not None:
                query = query.eq("is_active", is_active)

            if created_by:
                query = query.eq("created_by", created_by)

            response = (
                await query.order("created_at", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )

            return APIResponse(
                data=[Pipeline(**data) for data in response.data], count=response.count
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipelines: {str(e)}",
            )

    async def execute_pipeline(
        self,
        pipeline_id: UUID4,
        user_id: Optional[UUID4] = None,
    ) -> Dict[str, Any]:
        from app.tasks.worker import run_pipeline_task

        """Execute a pipeline"""
        try:
            # Check if pipeline exists and is active
            pipeline = await self.get_pipeline(pipeline_id)

            if not pipeline["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pipeline is not active",
                )

            # Create pipeline run
            run_data = PipelineRunCreate(
                pipeline_id=pipeline_id,
                status=PipelineRunStatus.PENDING,
                start_time=datetime.now(timezone.utc),
                triggered_by=user_id,
            )

            run = await self.create_pipeline_run(run_data)

            # Trigger worker
            # TODO: Trigger Worker
            await run_pipeline_task.delay(
                pipeline_id=pipeline_id,
                run_id=run["id"],
                user_id=user_id,
            )

            return run
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing pipeline: {str(e)}",
            )

    async def create_pipeline_run(self, run_in: PipelineRunCreate) -> Dict[str, Any]:
        """Create a new pipeline run"""
        try:
            supabase = await get_supabase()
            data = run_in.model_dump()
            data["start_time"] = datetime.now(timezone.utc).isoformat()

            response = await supabase.from_("pipeline_runs").insert(data).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline run",
                )

            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline run: {str(e)}",
            )

    async def get_pipeline_run(self, run_id: UUID4) -> Dict[str, Any]:
        """Get a pipeline run by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_runs")
                .select("*")
                .eq("id", run_id)
                .single()
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline run not found",
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline run: {str(e)}",
            )

    async def update_pipeline_run(
        self, run_id: UUID4, run_update: PipelineRunUpdate
    ) -> Dict[str, Any]:
        """Update a pipeline run"""
        try:
            supabase = await get_supabase()
            # Check if run exists
            await self.get_pipeline_run(run_id)

            # Update run
            data = run_update.model_dump(exclude_unset=True)

            # Calculate duration if not provided
            if (
                run_update.status
                in [PipelineRunStatus.COMPLETED, PipelineRunStatus.FAILED]
                and run_update.end_time
                and not run_update.duration
            ):
                run = await self.get_pipeline_run(run_id)
                start_time = datetime.fromisoformat(run["start_time"])
                end_time = datetime.fromisoformat(str(run_update.end_time))
                data["duration"] = int((end_time - start_time).total_seconds())

            response = (
                await supabase.from_("pipeline_runs")
                .update(data)
                .eq("id", run_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline run",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline run: {str(e)}",
            )

    async def get_pipeline_runs(
        self,
        pipeline_id: Optional[str] = None,
        _status: Optional[str] = None,
        triggered_by: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get pipeline runs with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("pipeline_runs").select("*")

            if pipeline_id:
                query = query.eq("pipeline_id", pipeline_id)

            if _status:
                query = query.eq("status", _status)

            if triggered_by:
                query = query.eq("triggered_by", triggered_by)

            response = (
                await query.order("created_at", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )

            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline runs: {str(e)}",
            )

    async def get_pipeline_run_logs(self, run_id: str) -> Dict[str, Any]:
        """Get detailed logs for a pipeline run"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_run_logs")
                .select("*")
                .eq("run_id", run_id)
                .single()
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline run logs not found",
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline run logs: {str(e)}",
            )

    # Manage pipeline steps
    async def create_pipeline_step(
        self, step_in: Dict[str, Any], pipeline_id: UUID4
    ) -> Dict[str, Any]:
        """Create a new pipeline step"""
        try:
            supabase = await get_supabase()
            step_in["pipeline_id"] = str(pipeline_id)
            response = await supabase.from_("pipeline_steps").insert(step_in).execute()
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

    async def get_pipeline_step(self, step_id: UUID4) -> Dict[str, Any]:
        """Get a pipeline step by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_steps")
                .select("*")
                .eq("id", step_id)
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
        self, step_id: UUID4, step_in: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a pipeline step"""
        try:
            supabase = await get_supabase()
            # Check if step exists
            await self.get_pipeline_step(step_id)
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

    async def delete_pipeline_step(self, step_id: UUID4) -> Dict[str, Any]:
        """Delete a pipeline step"""
        try:
            supabase = await get_supabase()
            # Check if step exists
            await self.get_pipeline_step(step_id)
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
    ) -> APIResponse[PipelineStep]:
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
                PipelineStep(**data) for data in response.data
            ]  # Convert to PipelineStep model
            return APIResponse(data=data, count=response.count)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline steps: {str(e)}",
            )

    async def get_pipeline_step_runs(
        self, pipeline_run_id: UUID4, limit: int = 100, skip: int = 0
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

    async def get_pipeline_step_run(self, step_run_id: UUID4) -> Dict[str, Any]:
        """Get a pipeline step run by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_step_runs")
                .select("*")
                .eq("id", step_run_id)
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

    async def update_pipeline_step_run(
        self, step_run_id: UUID4, step_run_in: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a pipeline step run"""
        try:
            supabase = await get_supabase()
            # Check if step run exists
            await self.get_pipeline_step_run(step_run_id)
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

    async def delete_pipeline_step_run(self, step_run_id: UUID4) -> Dict[str, Any]:
        """Delete a pipeline step run"""
        try:
            supabase = await get_supabase()
            # Check if step run exists
            await self.get_pipeline_step_run(step_run_id)
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
