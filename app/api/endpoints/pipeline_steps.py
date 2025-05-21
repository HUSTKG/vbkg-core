from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi import status as httpStatus

from app.api.deps import PermissionChecker
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.pipeline_step import (
    PipelineStep,
    PipelineStepCreate,
    PipelineStepRun,
    PipelineStepRunUpdate,
    PipelineStepUpdate,
)
from app.schemas.user import User

router = APIRouter()

check_read_permission = PermissionChecker("pipeline:read")
check_write_permission = PermissionChecker("pipeline:write")


@router.post("/runs/{step_run_id}/cancel", response_model=ApiResponse[None])
async def cancel_pipeline_step_run(
    step_run_id: Annotated[str, Path()],
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[None]:
    """
    Cancel a running pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    pipeline_step_run = await pipeline_step_service.get_pipeline_step_run(
        step_run_id=step_run_id
    )
    if not pipeline_step_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step run not found",
        )
    if pipeline_step_run["status"] not in ["pending", "running"]:
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline step run has status '{pipeline_step_run['status']}' and cannot be cancelled",
        )
    success = await pipeline_step_service.cancel_pipeline_step_run(
        step_run_id=step_run_id
    )
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel pipeline step run",
        )
    return ApiResponse(
        data=None,
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step run cancelled successfully",
    )


@router.post("/{pipeline_id}", response_model=ApiResponse[PipelineStep])
async def add_pipeline_step(
    pipeline_id: Annotated[str, Path()],
    step_in: PipelineStepCreate,
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[PipelineStep]:
    """
    Add a step to a pipeline.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    pipeline = await pipeline_step_service.get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )
    step = await pipeline_step_service.create_pipeline_step(
        pipeline_id=pipeline_id, step_in=step_in
    )
    return ApiResponse(
        data=PipelineStep(**step),
        status=httpStatus.HTTP_201_CREATED,
        message="Pipeline step added successfully",
    )


@router.get("/{step_id}", response_model=PaginatedResponse[PipelineStep])
async def get_pipeline_step(
    step_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[PipelineStep]:
    """
    Get a specific pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step = await pipeline_step_service.get_pipeline_step(step_id=step_id)
    if not step:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step not found",
        )
    return ApiResponse(
        data=PipelineStep(**step),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step retrieved successfully",
    )


@router.get("", response_model=PaginatedResponse[PipelineStep])
async def get_pipeline_steps(
    pipeline_id: Optional[str] = None,
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


@router.put("/{step_id}", response_model=ApiResponse[PipelineStep])
async def update_pipeline_step(
    step_id: Annotated[str, Path()],
    step_in: PipelineStepUpdate,
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[PipelineStep]:
    """
    Update a pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step = await pipeline_step_service.update_pipeline_step(
        step_id=step_id, step_in=step_in.model_dump()
    )
    if not step:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step not found",
        )
    return ApiResponse(
        data=PipelineStep(**step),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step updated successfully",
    )


@router.delete("/{step_id}", response_model=ApiResponse[PipelineStep])
async def delete_pipeline_step(
    step_id: Annotated[str, Path()],
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[PipelineStep]:
    """
    Delete a pipeline step.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    step = await pipeline_step_service.delete_pipeline_step(step_id=step_id)
    if not step:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step not found",
        )
    return ApiResponse(
        data=PipelineStep(**step),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step deleted successfully",
    )


@router.get("/runs", response_model=PaginatedResponse[PipelineStepRun])
async def read_pipeline_step_runs(
    pipeline_run_id: Optional[str] = None,
    current_user: User = Depends(check_write_permission),
) -> PaginatedResponse[PipelineStepRun]:
    """
    Read pipeline step runs.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    pipeline_runs = await pipeline_step_service.get_pipeline_step_runs(
        pipeline_run_id=pipeline_run_id,
    )

    if not pipeline_runs:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step runs not found",
        )

    return PaginatedResponse(
        data=[PipelineStepRun(**data) for data in pipeline_runs.data],
        meta=PaginatedMeta(
            skip=0,
            limit=100,
            total=pipeline_runs.count if pipeline_runs.count else 0,
        ),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step runs retrieved successfully",
    )


@router.get(
    "/runs/{step_run_id}",
    response_model=ApiResponse[PipelineStepRun],
)
async def read_pipeline_step_run(
    step_run_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[PipelineStepRun]:
    """
    Get a specific pipeline step run.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    pipeline_step_run = await pipeline_step_service.get_pipeline_step_run(
        step_run_id=step_run_id
    )
    if not pipeline_step_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step run not found",
        )
    return ApiResponse(
        data=PipelineStepRun(**pipeline_step_run),
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step run retrieved successfully",
    )


@router.put(
    "/runs/{step_run_id}",
    response_model=ApiResponse[None],
)
async def update_pipeline_step_run(
    step_run_id: Annotated[str, Path()],
    step_run_in: PipelineStepRunUpdate,
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[None]:
    """
    Update a pipeline step run.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    pipeline_step_run = await pipeline_step_service.update_pipeline_step_run(
        step_run_id=step_run_id, step_run_in=step_run_in.model_dump()
    )
    if not pipeline_step_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step run not found",
        )
    return ApiResponse(
        data=None,
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step run updated successfully",
    )


@router.delete(
    "/runs/{step_run_id}",
    response_model=ApiResponse[None],
)
async def delete_pipeline_step_run(
    step_run_id: Annotated[str, Path()],
    current_user: User = Depends(check_write_permission),
) -> ApiResponse[None]:
    """
    Delete a pipeline step run.
    """
    from app.services.pipeline_step import PipelineStepService

    pipeline_step_service = PipelineStepService()
    pipeline_step_run = await pipeline_step_service.delete_pipeline_step_run(
        step_run_id=step_run_id
    )
    if not pipeline_step_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline step run not found",
        )
    return ApiResponse(
        data=None,
        status=httpStatus.HTTP_200_OK,
        message="Pipeline step run deleted successfully",
    )


@router.post("/runs/{step_run_id}/run", response_model=ApiResponse[PipelineStepRun])
async def run_pipeline_step(
    pipeline_id: Annotated[str, Path()],
    params: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[PipelineStepRun]:
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
        data=PipelineStepRun(**pipeline_run),
        status=httpStatus.HTTP_201_CREATED,
        message="Pipeline run started successfully",
    )


@router.get("/runs/{run_id}/status", response_model=ApiResponse[PipelineStepRun])
async def get_pipeline_run_status(
    run_id: Annotated[str, Path()],
    current_user: User = Depends(check_read_permission),
) -> ApiResponse[PipelineStepRun]:
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

    pipeline_run = PipelineStepRun(**pipeline_run)

    return ApiResponse(
        data=pipeline_run,
        status=httpStatus.HTTP_200_OK,
        message="Pipeline run status retrieved successfully",
    )
