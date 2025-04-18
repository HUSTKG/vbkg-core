from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Any, List, Optional, Dict
from pydantic import UUID4

from app.schemas.pipeline import (
    Pipeline, PipelineCreate, PipelineUpdate,
    PipelineRun, PipelineRunCreate, PipelineRunStatus
)
from app.schemas.user import User
from app.api.deps import get_current_user_with_permission
from app.services.data_extraction import run_pipeline

router = APIRouter()

@router.get("/", response_model=List[Pipeline])
async def read_pipelines(
    skip: int = 0,
    limit: int = 100,
    pipeline_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user_with_permission("pipeline:read")),
) -> Any:
    """
    Retrieve pipelines.
    """
    from app.services.data_extraction import get_pipelines
    
    pipelines = await get_pipelines(
        skip=skip,
        limit=limit,
        pipeline_type=pipeline_type,
        is_active=is_active
    )
    return pipelines

@router.post("/", response_model=Pipeline)
async def create_pipeline(
    pipeline_in: PipelineCreate,
    current_user: User = Depends(get_current_user_with_permission("pipeline:write")),
) -> Any:
    """
    Create new pipeline.
    """
    from app.services.data_extraction import create_pipeline
    
    pipeline = await create_pipeline(
        pipeline_in=pipeline_in,
        created_by=current_user.id
    )
    return pipeline

@router.get("/{pipeline_id}", response_model=Pipeline)
async def read_pipeline(
    pipeline_id: UUID4,
    current_user: User = Depends(get_current_user_with_permission("pipeline:read")),
) -> Any:
    """
    Get a specific pipeline.
    """
    from app.services.data_extraction import get_pipeline
    
    pipeline = await get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )
    return pipeline

@router.put("/{pipeline_id}", response_model=Pipeline)
async def update_pipeline(
    pipeline_id: UUID4,
    pipeline_in: PipelineUpdate,
    current_user: User = Depends(get_current_user_with_permission("pipeline:write")),
) -> Any:
    """
    Update a pipeline.
    """
    from app.services.data_extraction import update_pipeline, get_pipeline
    
    pipeline = await get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )
    
    pipeline = await update_pipeline(
        pipeline_id=pipeline_id,
        pipeline_in=pipeline_in
    )
    return pipeline

@router.delete("/{pipeline_id}", response_model=Pipeline)
async def delete_pipeline(
    pipeline_id: UUID4,
    current_user: User = Depends(get_current_user_with_permission("pipeline:write")),
) -> Any:
    """
    Delete a pipeline.
    """
    from app.services.data_extraction import delete_pipeline, get_pipeline
    
    pipeline = await get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )
    
    pipeline = await delete_pipeline(pipeline_id=pipeline_id)
    return pipeline

@router.post("/{pipeline_id}/run", response_model=PipelineRun)
async def run_pipeline_endpoint(
    pipeline_id: UUID4,
    background_tasks: BackgroundTasks,
    params: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user_with_permission("pipeline:write")),
) -> Any:
    """
    Run a pipeline.
    """
    from app.services.data_extraction import get_pipeline, create_pipeline_run
    
    pipeline = await get_pipeline(pipeline_id=pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )
    
    # Create pipeline run record
    pipeline_run_in = PipelineRunCreate(
        pipeline_id=pipeline_id,
        status="pending",
        triggered_by=current_user.id,
        stats={"parameters": params or {}}
    )
    
    pipeline_run = await create_pipeline_run(pipeline_run_in=pipeline_run_in)
    
    # Run pipeline in background
    background_tasks.add_task(
        run_pipeline,
        pipeline_id=pipeline_id,
        pipeline_run_id=pipeline_run["id"],
        params=params
    )
    
    return pipeline_run

@router.get("/runs/", response_model=List[PipelineRun])
async def read_pipeline_runs(
    skip: int = 0,
    limit: int = 100,
    pipeline_id: Optional[UUID4] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user_with_permission("pipeline:read")),
) -> Any:
    """
    Retrieve pipeline runs.
    """
    from app.services.data_extraction import get_pipeline_runs
    
    pipeline_runs = await get_pipeline_runs(
        skip=skip,
        limit=limit,
        pipeline_id=pipeline_id,
        status=status
    )
    return pipeline_runs

@router.get("/runs/{run_id}", response_model=PipelineRun)
async def read_pipeline_run(
    run_id: UUID4,
    current_user: User = Depends(get_current_user_with_permission("pipeline:read")),
) -> Any:
    """
    Get a specific pipeline run.
    """
    from app.services.data_extraction import get_pipeline_run
    
    pipeline_run = await get_pipeline_run(run_id=run_id)
    if not pipeline_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline run not found",
        )
    return pipeline_run

@router.get("/runs/{run_id}/status", response_model=PipelineRunStatus)
async def get_pipeline_run_status(
    run_id: UUID4,
    current_user: User = Depends(get_current_user_with_permission("pipeline:read")),
) -> Any:
    """
    Get the status of a pipeline run.
    """
    from app.services.data_extraction import get_pipeline_run
    
    pipeline_run = await get_pipeline_run(run_id=run_id)
    if not pipeline_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline run not found",
        )
    
    return {
        "status": pipeline_run["status"],
        "start_time": pipeline_run["start_time"],
        "end_time": pipeline_run["end_time"],
        "duration": pipeline_run["duration"],
        "stats": pipeline_run["stats"]
    }

@router.post("/runs/{run_id}/cancel")
async def cancel_pipeline_run(
    run_id: UUID4,
    current_user: User = Depends(get_current_user_with_permission("pipeline:write")),
) -> Any:
    """
    Cancel a running pipeline.
    """
    from app.services.data_extraction import cancel_pipeline_run, get_pipeline_run
    
    pipeline_run = await get_pipeline_run(run_id=run_id)
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
    
    return {"message": "Pipeline run cancelled successfully"}
