from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status as httpStatus,
    BackgroundTasks,
)
from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
from pydantic import UUID4

from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.pipeline import (
    Pipeline,
    PipelineCreate,
    PipelineRunStatus,
    PipelineUpdate,
    PipelineRun,
    PipelineRunCreate,
    PipelineRunStatus,
)
from app.schemas.user import User
from app.api.deps import PermissionChecker
from app.services.pipeline import PipelineService

router = APIRouter()

check_read_permission = PermissionChecker("pipeline:read")
check_write_permission = PermissionChecker("pipeline:write")


@router.get("/", response_model=PaginatedResponse[List[Pipeline]])
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


@router.post("/", response_model=ApiResponse[Pipeline])
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
        user_id=current_user["id"],
        pipeline_in=pipeline_in,
    )

    return ApiResponse(
        data=Pipeline(**pipeline),
        status=httpStatus.HTTP_201_CREATED,
        message="Pipeline created successfully",
    )


@router.get("/{pipeline_id}", response_model=ApiResponse[Pipeline])
async def read_pipeline(
    pipeline_id: UUID4,
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
    pipeline_id: UUID4,
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
    pipeline_id: UUID4,
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


@router.post("/{pipeline_id}/run", response_model=ApiResponse[PipelineRun])
async def run_pipeline_endpoint(
    pipeline_id: UUID4,
    background_tasks: BackgroundTasks,
    params: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[PipelineRun]:
    """
    Run a pipeline.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline = await pipeline_service.get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )

    # TODO: Execute Pipeline
    pipeline_run = await pipeline_service.execute_pipeline(
        pipeline_id=pipeline_id,
        user_id=current_user["id"],
    )

    return ApiResponse(
        data=PipelineRun(**pipeline_run),
        status=httpStatus.HTTP_201_CREATED,
        message="Pipeline run started successfully",
    )


@router.get("/runs", response_model=PaginatedResponse[PipelineRun])
async def read_pipeline_runs(
    skip: int = 0,
    limit: int = 100,
    pipeline_id: Optional[UUID4] = None,
    status: Optional[str] = None,
    current_user: User = Depends(check_read_permission),
) -> PaginatedResponse[PipelineRun]:
    """
    Retrieve pipeline runs.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline_runs = await pipeline_service.get_pipeline_runs(
        skip=skip, limit=limit, pipeline_id=str(pipeline_id)
    )
    return PaginatedResponse(
        data=[PipelineRun(**data) for data in pipeline_runs.data],
        meta=PaginatedMeta(
            skip=skip,
            limit=limit,
            total=pipeline_runs.count if pipeline_runs.count else 0,
        ),
        status=httpStatus.HTTP_200_OK,
        message="Read Pipeline Runs Success",
    )


@router.get("/runs/{run_id}", response_model=ApiResponse[PipelineRun])
async def read_pipeline_run(
    run_id: UUID4,
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


@router.get("/runs/{run_id}/status", response_model=ApiResponse[PipelineRun])
async def get_pipeline_run_status(
    run_id: UUID4,
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[PipelineRun]:
    """
    Get the status of a pipeline run.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline_run = await pipeline_service.get_pipeline_run(run_id=run_id)
    if not pipeline_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline run not found",
        )

    pipeline_run = PipelineRun(**pipeline_run)

    return ApiResponse(
        data=pipeline_run,
        status=httpStatus.HTTP_200_OK,
        message="Pipeline run status retrieved successfully",
    )


@router.post("/runs/{run_id}/cancel", response_model=ApiResponse[None])
async def cancel_pipeline_run(
    run_id: UUID4,
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[None]:
    """
    Cancel a running pipeline.
    """
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    pipeline_run = await pipeline_service.get_pipeline_run(run_id=run_id)
    if not pipeline_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline run not found",
        )

    if pipeline_run["status"] not in ["pending", "running"]:
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline run has status '{pipeline_run['status']}' and cannot be cancelled",
        )

    success = await cancel_pipeline_run(run_id=run_id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel pipeline run",
        )

    return ApiResponse(
        data=None,
        status=httpStatus.HTTP_200_OK,
        message="Pipeline run cancelled successfully",
    )
