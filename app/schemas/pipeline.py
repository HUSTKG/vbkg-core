from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.pipeline_step import (PipelineStep, PipelineStepBase,
                                       PipelineStepRun)


# Enums
class PipelineType(str, Enum):
    EXTRACTION = "extraction"
    TRANSFORMATION = "transformation"
    LOADING = "loading"
    COMPLETE = "complete"


class PipelineRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    pipeline_type: PipelineType
    schedule: Optional[str] = None
    is_active: bool = True
    steps: List[PipelineStepBase]  # Steps data to be inserted in pipeline_steps table


class PipelineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    pipeline_type: PipelineType
    schedule: Optional[str] = None  # CRON expression
    is_active: bool = True


class Pipeline(PipelineBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PipelineRunBase(BaseModel):
    pipeline_id: str
    status: PipelineRunStatus = PipelineRunStatus.PENDING
    start_time: datetime
    input_parameters: Optional[Dict[str, Any]] = None
    triggered_by: Optional[str] = None


class PipelineRunCreate(PipelineRunBase):
    celery_task_id: Optional[str] = None


class PipelineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    pipeline_type: Optional[PipelineType] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None


class PipelineRunUpdate(BaseModel):
    status: Optional[PipelineRunStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    log: Optional[str] = None
    error_message: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    celery_task_id: Optional[str] = None


class PipelineRun(PipelineRunBase):
    id: str
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    log: Optional[str] = None
    error_message: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    celery_task_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Extended Response Models (with relationships)
class PipelineWithSteps(Pipeline):
    steps: List[PipelineStep] = []


class PipelineRunWithSteps(PipelineRun):
    step_runs: List[PipelineStepRun] = []


class StartPipelineRequest(BaseModel):
    input_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PipelineRunResult(BaseModel):
    pipeline_run_id: str
    celery_task_id: Optional[str] = None
    status: PipelineRunStatus
    message: str
