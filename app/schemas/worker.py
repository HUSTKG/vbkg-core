from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SystemInfo(BaseModel):
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_total: int = 0
    disk_usage: float = 0.0
    uptime: str = "0m"


class WorkerInfo(BaseModel):
    name: str
    status: str  # online, offline
    active_tasks: int = 0
    processed_tasks: int = 0
    load_avg: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    system_info: SystemInfo
    heartbeat: Optional[datetime] = None
    last_heartbeat_delta: int = 0  # seconds


class WorkerStats(BaseModel):
    total: int
    online: int
    offline: int


class TaskInfo(BaseModel):
    id: str
    name: str
    state: str
    runtime: float = 0.0
    timestamp: datetime
    worker: Optional[str] = None
    args: str
    kwargs: str


class CeleryStats(BaseModel):
    success: int = 0
    running: int = 0
    failed: int = 0
    total: int = 0


class FlowerDashboardResponse(BaseModel):
    workers: List[WorkerInfo]
    worker_stats: WorkerStats
    celery_stats: CeleryStats
    tasks: List[TaskInfo]
