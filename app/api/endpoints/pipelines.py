from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path
from fastapi import status as httpStatus

from app.api.deps import PermissionChecker
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.pipeline import (Pipeline, PipelineCreate, PipelineRun,
                                  PipelineRunStatus, PipelineUpdate,
                                  StartPipelineRequest)
from app.schemas.pipeline_step import PipelineStep, PipelineStepRun
from app.schemas.user import User
from app.services.pipeline import PipelineService
from app.services.pipeline_step import PipelineStepService

router = APIRouter()

check_read_permission = PermissionChecker("pipeline:read")
check_write_permission = PermissionChecker("pipeline:write")


@router.get("", response_model=PaginatedResponse[Pipeline])
async def read_pipelines(
    skip: int = 0,
    limit: int = 100,
    pipeline_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(check_read_permission),
) -> PaginatedResponse[Pipeline]:
    """
    Retrieve pipelines.
    """
    pipeline_service = PipelineService()

    pipelines = await pipeline_service.get_pipelines(
        skip=skip, limit=limit, pipeline_type=pipeline_type, is_active=is_active
    )
    return PaginatedResponse(
        data=pipelines.data,
        meta=PaginatedMeta(
            skip=skip,
            limit=limit,
            total=pipelines.count if pipelines.count else 0,
        ),
        status=httpStatus.HTTP_200_OK,
        message="Pipelines retrieved successfully",
    )


@router.post("", response_model=ApiResponse[Pipeline])
async def create_pipeline(
    pipeline_in: PipelineCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Pipeline]:
    """
    Create new pipeline.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline = await pipeline_service.create_pipeline(
        pipeline_in=pipeline_in,
        user_id=current_user["id"],
    )

    return ApiResponse(
        data=Pipeline(**pipeline),
        status=httpStatus.HTTP_201_CREATED,
        message="Pipeline created successfully",
    )


@router.get("/{pipeline_id}/runs")
async def get_pipeline_runs(
    pipeline_id: Annotated[str, Path()],
    status: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    pipeline_service: PipelineService = Depends(lambda: PipelineService()),
) -> PaginatedResponse[PipelineRun]:
    """
    Get pipeline run history with optional filtering
    """
    try:
        runs_response = await pipeline_service.get_pipeline_runs(
            pipeline_id=pipeline_id, _status=status, limit=limit, skip=skip
        )

        return PaginatedResponse(
            data=[PipelineRun(**data) for data in runs_response.data],
            meta=PaginatedMeta(
                total=runs_response.count if runs_response.count else 0,
                limit=limit,
                skip=skip,
            ),
            status=httpStatus.HTTP_200_OK,
            message="Pipeline runs retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline runs: {str(e)}"
        )


@router.get("/runs/{run_id}", response_model=ApiResponse[PipelineRun])
async def read_pipeline_run(
    run_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[PipelineRun]:
    """
    Get a specific pipeline run.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline_run = await pipeline_service.get_pipeline_run(run_id=run_id)
    if not pipeline_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline run not found",
        )
    return ApiResponse(
        data=PipelineRun(**pipeline_run),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline run retrieved successfully",
    )


@router.get("/{pipeline_id}/runs/{run_id}/logs")
async def get_pipeline_run_logs(
    pipeline_id: str,
    run_id: str,
    pipeline_service: PipelineService = Depends(lambda: PipelineService()),
) -> Dict[str, Any]:
    """
    Get detailed logs for a pipeline run
    """
    try:
        logs = await pipeline_service.get_pipeline_run_logs(run_id)
        return logs

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline logs: {str(e)}"
        )


@router.get("/{pipeline_id}/runs/{run_id}/status")
async def get_pipeline_run_status(
    pipeline_id: str,
    run_id: str,
    pipeline_service: PipelineService = Depends(lambda: PipelineService()),
    step_service: PipelineStepService = Depends(lambda: PipelineStepService()),
) -> Dict[str, Any]:
    """
    Get the detailed status of a pipeline run including step progress
    """
    try:
        # Get pipeline run details
        pipeline_run = await pipeline_service.get_pipeline_run(run_id)

        # Get step runs for this pipeline run
        step_runs_response = await step_service.get_pipeline_step_runs(run_id)
        step_runs = step_runs_response.data

        # Calculate progress
        total_steps = len(step_runs) if step_runs else 0
        completed_steps = (
            len([s for s in step_runs if s["status"] == "completed"])
            if step_runs
            else 0
        )
        failed_steps = (
            len([s for s in step_runs if s["status"] == "failed"]) if step_runs else 0
        )
        running_steps = (
            len([s for s in step_runs if s["status"] == "running"]) if step_runs else 0
        )

        progress_percentage = (
            (completed_steps / total_steps * 100) if total_steps > 0 else 0
        )

        return {
            "pipeline_run": pipeline_run,
            "step_runs": step_runs,
            "progress": {
                "percentage": round(progress_percentage, 2),
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "running_steps": running_steps,
            },
            "overall_status": pipeline_run["status"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching pipeline run status: {str(e)}"
        )


@router.post("/{pipeline_id}/runs/{run_id}/cancel")
async def cancel_pipeline_run(
    pipeline_id: str,
    run_id: str,
    pipeline_service: PipelineService = Depends(lambda: PipelineService()),
) -> ApiResponse[None]:
    """
    Cancel a running pipeline
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    isCanceled = await pipeline_service.cancel_pipeline_run(
        run_id=run_id, pipeline_id=pipeline_id
    )
    if not isCanceled:
        raise HTTPException(
            status_code=httpStatus.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )
    return ApiResponse(
        data=None,
        status=httpStatus.HTTP_200_OK,
        message="Pipeline retrieved successfully",
    )


@router.get("/{pipeline_id}", response_model=ApiResponse[Pipeline])
async def read_pipeline(
    pipeline_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[Pipeline]:
    """
    Get a specific pipeline.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline = await pipeline_service.get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=httpStatus.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )
    return ApiResponse(
        data=Pipeline(**pipeline),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline retrieved successfully",
    )


@router.put("/{pipeline_id}", response_model=ApiResponse[Pipeline])
async def update_pipeline(
    pipeline_id: Annotated[str, Path()],
    pipeline_in: PipelineUpdate,
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[Pipeline]:
    """
    Update a pipeline.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline = await pipeline_service.get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )

    pipeline = await pipeline_service.update_pipeline(
        pipeline_id=pipeline_id, pipeline_in=pipeline_in
    )
    return ApiResponse(
        data=Pipeline(**pipeline),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline updated successfully",
    )


@router.delete("/{pipeline_id}", response_model=ApiResponse[Pipeline])
async def delete_pipeline(
    pipeline_id: Annotated[str, Path()],
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[Pipeline]:
    """
    Delete a pipeline.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline = await pipeline_service.get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )

    pipeline = await pipeline_service.delete_pipeline(pipeline_id=pipeline_id)

    return ApiResponse(
        data=Pipeline(**pipeline),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline deleted successfully",
    )


@router.post("/{pipeline_id}/run", response_model=Dict[str, Any])
async def execute_pipeline(
    pipeline_id: str,
    request: StartPipelineRequest,
    current_user: Dict[str, Any] = Depends(check_write_permission),
    pipeline_service: PipelineService = Depends(lambda: PipelineService()),
) -> Dict[str, Any]:
    """
    Execute a pipeline with optional input parameters
    """
    try:
        result = await pipeline_service.execute_pipeline(
            pipeline_id=pipeline_id,
            user_id=current_user["id"],
            input_parameters=request.input_parameters,
        )

        return {
            "success": True,
            "pipeline_run_id": result["id"],
            "celery_task_id": result["celery_task_id"],
            "status": result["status"],
            "message": result["message"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to execute pipeline: {str(e)}"
        )


@router.get("/{pipeline_id}/steps", response_model=PaginatedResponse[PipelineStep])
async def get_pipeline_steps(
    pipeline_id: Annotated[str, Path()],
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_read_permission),
) -> PaginatedResponse[PipelineStep]:
    """
    Get a specific pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step = await pipeline_step_service.get_pipeline_steps(
        pipeline_id=pipeline_id, skip=skip, limit=limit
    )
    if not step.data:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step not found",
        )
    return PaginatedResponse(
        data=[PipelineStep(**data) for data in step.data],
        meta=PaginatedMeta(
            total=step.count if step.count else 0,
            limit=limit,
            skip=skip,
        ),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step retrieved successfully",
    )


@router.get("/{pipeline_id}/steps/{step_id}", response_model=ApiResponse[PipelineStep])
async def get_pipeline_step(
    pipeline_id: Annotated[str, Path()],
    step_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[PipelineStep]:
    """
    Get a specific pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step = await pipeline_step_service.get_pipeline_step(
        pipeline_id=pipeline_id, step_id=step_id
    )
    if not step.data:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step not found",
        )
    return ApiResponse(
        data=PipelineStep(**step),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step retrieved successfully",
    )


@router.get(
    "/runs/{pipeline_run_id}/steps", response_model=PaginatedResponse[PipelineStepRun]
)
async def get_pipeline_step_runs(
    pipeline_run_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_read_permission),
) -> PaginatedResponse[PipelineStepRun]:
    """
    Get a specific pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step = await pipeline_step_service.get_pipeline_step_runs(
        pipeline_run_id=pipeline_run_id, skip=skip, limit=limit
    )
    if not step.data:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step not found",
        )
    return PaginatedResponse(
        data=[PipelineStep(**data) for data in step.data],
        meta=PaginatedMeta(
            total=step.count if step.count else 0,
            limit=limit,
            skip=skip,
        ),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step retrieved successfully",
    )


@router.get(
    "/runs/{pipeline_run_id}/steps/{step_run_id}",
    response_model=ApiResponse[PipelineStepRun],
)
async def get_pipeline_step_run(
    pipeline_run_id: Annotated[str, Path()],
    step_run_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[PipelineStep]:
    """
    Get a specific pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step_run = await pipeline_step_service.get_pipeline_step_run(
        step_run_id=step_run_id, pipeline_run_id=pipeline_run_id
    )
    if not step_run.data:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step run not found",
        )
    return ApiResponse(
        data=PipelineStep(**step_run),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step retrieved successfully",
    )
