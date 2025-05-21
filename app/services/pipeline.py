import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse

from app.core.supabase import get_supabase
from app.schemas.pipeline import (Pipeline, PipelineCreate, PipelineRunCreate,
                                  PipelineRunStatus, PipelineRunUpdate,
                                  PipelineUpdate)


class PipelineService:
    """Service for managing pipelines and their execution."""

    async def create_pipeline(
        self, pipeline_in: PipelineCreate, user_id: str
    ) -> Dict[str, Any]:
        """Create a new pipeline"""
        try:
            supabase = await get_supabase()

            pipeline_dict = pipeline_in.model_dump()

            pipeline_response = (
                await supabase.from_("pipelines")
                .insert(
                    {
                        "name": pipeline_dict["name"],
                        "description": pipeline_dict["description"],
                        "pipeline_type": pipeline_dict["pipeline_type"],
                        "schedule": pipeline_dict["schedule"],
                        "is_active": pipeline_dict["is_active"],
                        "created_by": user_id,
                    }
                )
                .execute()
            )

            if pipeline_dict.get("steps"):
                # create pipeline_steps
                # I want to map pipeline["steps"] array with pipeline_id
                # and insert them into pipeline_steps table

                print(pipeline_dict["steps"])

                pipeline_dict["steps"] = [
                    {
                        "id": step["id"],
                        "name": step["name"],
                        "step_type": step["step_type"],
                        "config": json.dumps(step["config"]),
                        "inputs": "".join(step["inputs"]),
                        "run_order": step["run_order"],
                        "pipeline_id": pipeline_response.data[0]["id"],
                    }
                    for step in pipeline_dict["steps"]
                ]

                # Insert pipeline steps
                response = (
                    await supabase.from_("pipeline_steps")
                    .insert(pipeline_dict["steps"])
                    .execute()
                )

                if not response.data:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create pipeline steps",
                    )

            if not pipeline_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline",
                )

            return pipeline_response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline: {str(e)}",
            )

    async def get_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
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
        self, pipeline_id: str, pipeline_in: PipelineUpdate
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

    async def delete_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
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
        pipeline_id: str,
        user_id: Optional[str] = None,
        input_parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a pipeline"""
        try:
            from app.tasks.worker import run_pipeline_task

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
                input_parameters=input_parameters or {},
            )

            run = await self.create_pipeline_run(run_data)

            # Start the pipeline task asynchronously
            task = run_pipeline_task.delay(
                pipeline_id=pipeline_id, run_id=run["id"], user_id=user_id
            ).get(timeout=1)

            # Update run with celery task ID
            await self.update_pipeline_run(
                run_id=run["id"],
                pipeline_id=pipeline_id,
                run_update=PipelineRunUpdate(celery_task_id=task.id),
            )

            return {
                **run,
                "celery_task_id": task.id,
                "message": f"Pipeline {pipeline_id} execution started",
            }

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

    async def get_pipeline_run(self, run_id: str, pipeline_id: str) -> Dict[str, Any]:
        """Get a pipeline run by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_runs")
                .select("*")
                .filter("id", "eq", run_id)
                .filter("pipeline_id", "eq", pipeline_id)
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
        self, run_id: str, pipeline_id: str, run_update: PipelineRunUpdate
    ) -> Dict[str, Any]:
        """Update a pipeline run"""
        try:
            supabase = await get_supabase()
            # Check if run exists
            await self.get_pipeline_run(run_id, pipeline_id)

            # Update run
            data = run_update.model_dump(exclude_unset=True)

            # Calculate duration if not provided
            if (
                run_update.status
                in [PipelineRunStatus.COMPLETED, PipelineRunStatus.FAILED]
                and run_update.end_time
                and not run_update.duration
            ):
                run = await self.get_pipeline_run(run_id, pipeline_id)
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

    async def cancel_pipeline_run(self, run_id: str, pipeline_id: str) -> bool:
        """Cancel a pipeline run"""

        try:
            from app.tasks.worker import cancel_pipeline_run_task

            # Check if pipeline run exists and can be cancelled
            pipeline_run = await self.get_pipeline_run(run_id, pipeline_id)

            if not pipeline_run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline run not found",
                )
            if pipeline_run["pipeline_id"] != pipeline_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pipeline ID does not match the run's pipeline ID",
                )

            if pipeline_run["status"] in [
                PipelineRunStatus.COMPLETED,
                PipelineRunStatus.FAILED,
                PipelineRunStatus.CANCELLED,
            ]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel pipeline run with status: {pipeline_run['status']}",
                )

            # Cancel via Celery task
            cancel_pipeline_run_task.delay(run_id)

            return True

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error cancelling pipeline: {str(e)}"
            )
