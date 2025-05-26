import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from app.schemas.worker import (CeleryStats, FlowerDashboardResponse,
                                SystemInfo, TaskInfo, WorkerInfo, WorkerStats)

logger = logging.getLogger(__name__)


class FlowerService:
    def __init__(self, flower_url: str = "http://localhost:5555"):
        self.flower_url = flower_url.rstrip("/")
        self.timeout = 10.0

    async def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make HTTP request to Flower API"""
        url = f"{self.flower_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling Flower API {url}: {e}")
            raise HTTPException(
                status_code=e.response.status_code, detail=f"Flower API error: {e}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error calling Flower API {url}: {e}")
            raise HTTPException(status_code=503, detail="Cannot connect to Flower API")
        except Exception as e:
            logger.error(f"Unexpected error calling Flower API {url}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    def _parse_worker_stats(self, worker_data: Dict[str, Any]) -> SystemInfo:
        """Parse worker system statistics"""
        stats = worker_data.get("stats", {})

        # Parse CPU usage
        cpu_usage = 0.0
        if "rusage" in stats:
            # Calculate CPU usage from rusage if available
            rusage = stats["rusage"]
            if "utime" in rusage and "stime" in rusage:
                cpu_usage = min((rusage["utime"] + rusage["stime"]) * 100 / 60, 100.0)

        # Parse memory usage
        memory_usage = 0.0
        memory_total = 0
        if "rusage" in stats and "maxrss" in stats["rusage"]:
            # maxrss is in KB on Linux, convert to MB
            memory_used_mb = stats["rusage"]["maxrss"] / 1024
            # Estimate total memory (this is a rough estimate)
            memory_total = max(int(memory_used_mb * 2), 1024)  # Assume used is 50% max
            memory_usage = min((memory_used_mb / memory_total) * 100, 100.0)

        # Parse load average
        load_avg = stats.get("load_avg", [0.0, 0.0, 0.0])
        if not isinstance(load_avg, list) or len(load_avg) != 3:
            load_avg = [0.0, 0.0, 0.0]

        # Calculate uptime
        uptime = "0m"
        if "clock" in stats:
            uptime_seconds = int(stats["clock"])
            if uptime_seconds > 0:
                days = uptime_seconds // 86400
                hours = (uptime_seconds % 86400) // 3600
                minutes = (uptime_seconds % 3600) // 60

                if days > 0:
                    uptime = f"{days}d {hours}h {minutes}m"
                elif hours > 0:
                    uptime = f"{hours}h {minutes}m"
                else:
                    uptime = f"{minutes}m"

        return SystemInfo(
            cpu_usage=round(cpu_usage, 1),
            memory_usage=round(memory_usage, 1),
            memory_total=memory_total,
            disk_usage=0.0,  # Flower doesn't provide disk usage by default
            uptime=uptime,
        )

    def _calculate_heartbeat_delta(self, heartbeat_timestamp: Optional[float]) -> int:
        """Calculate seconds since last heartbeat"""
        if not heartbeat_timestamp:
            return 999999  # Very large number for offline workers

        now = datetime.now(timezone.utc).timestamp()
        return max(0, int(now - heartbeat_timestamp))

    async def get_workers(self) -> List[WorkerInfo]:
        """Get all workers information"""
        workers_data = await self._make_request("/api/workers")
        worker_status = await self._make_request("/api/workers?status=true")
        workers = []

        for worker_name, worker_info in workers_data.items():
            # Determine worker status based on heartbeat
            heartbeat_timestamp = worker_info.get("timestamp")
            heartbeat_delta = self._calculate_heartbeat_delta(heartbeat_timestamp)

            # Consider worker offline if no heartbeat in last 60 seconds
            status = "online" if worker_status[worker_name] else "offline"

            # Parse heartbeat datetime
            heartbeat = None
            if heartbeat_timestamp:
                heartbeat = datetime.fromtimestamp(heartbeat_timestamp, tz=timezone.utc)

            # Get active and processed tasks
            active_tasks = len(worker_info.get("active", []))
            processed_pipeline_tasks = (
                worker_info.get("stats", {}).get("total", {}).get("run_pipeline", 0)
            )
            processed_step_tasks = (
                worker_info.get("stats", {})
                .get("total", {})
                .get("run_pipeline_step", 0)
            )

            processed_complete_tasks = (
                worker_info.get("stats", {})
                .get("total", {})
                .get("complete_pipeline", 0)
            )

            processed_tasks = (
                processed_pipeline_tasks
                + processed_step_tasks
                + processed_complete_tasks
            )

            # Parse system stats
            system_info = self._parse_worker_stats(worker_info)

            # Get load average from stats
            load_avg = worker_info.get("stats", {}).get("load_avg", [0.0, 0.0, 0.0])
            if not isinstance(load_avg, list) or len(load_avg) != 3:
                load_avg = [0.0, 0.0, 0.0]

            worker = WorkerInfo(
                name=worker_name,
                status=status,
                active_tasks=active_tasks,
                processed_tasks=processed_tasks,
                load_avg=[round(x, 2) for x in load_avg],
                system_info=system_info,
                heartbeat=heartbeat,
                last_heartbeat_delta=heartbeat_delta,
            )
            workers.append(worker)

        return workers

    async def get_worker_stats(self) -> WorkerStats:
        """Get worker statistics summary"""
        workers = await self.get_workers()
        online_count = sum(1 for w in workers if w.status == "online")
        offline_count = len(workers) - online_count

        return WorkerStats(
            total=len(workers), online=online_count, offline=offline_count
        )

    async def get_tasks(self, limit: int = 100) -> List[TaskInfo]:
        """Get recent tasks"""
        try:
            tasks_data = await self._make_request(f"/api/tasks?limit={limit}")
            tasks = []

            for task_id, task_info in tasks_data.items():
                # Parse task timestamp
                timestamp = datetime.now(timezone.utc)
                if "timestamp" in task_info:
                    try:
                        timestamp = datetime.fromtimestamp(
                            task_info["timestamp"], tz=timezone.utc
                        )
                    except (ValueError, TypeError):
                        pass

                # Calculate runtime
                runtime = 0.0
                if "runtime" in task_info:
                    runtime = float(task_info.get("runtime", 0))
                elif "started" in task_info and "succeeded" in task_info:
                    try:
                        runtime = task_info["succeeded"] - task_info["started"]
                    except (ValueError, TypeError):
                        pass

                task = TaskInfo(
                    id=task_id,
                    name=task_info.get("name", "Unknown"),
                    state=task_info.get("state", "UNKNOWN"),
                    runtime=round(runtime, 2),
                    timestamp=timestamp,
                    worker=task_info.get("worker"),
                    args=task_info.get("args", "()"),
                    kwargs=task_info.get("kwargs", "{}"),
                )
                tasks.append(task)

            # Sort by timestamp, newest first
            tasks.sort(key=lambda x: x.timestamp, reverse=True)
            return tasks[:limit]

        except Exception as e:
            logger.warning(f"Could not fetch tasks: {e}")
            return []

    async def get_celery_stats(self) -> CeleryStats:
        """Get Celery task statistics"""
        try:
            tasks = await self.get_tasks(limit=1000)  # Get more tasks for stats

            success_count = sum(1 for t in tasks if t.state == "SUCCESS")
            running_count = sum(
                1 for t in tasks if t.state in ["PENDING", "STARTED", "RUNNING"]
            )
            failed_count = sum(
                1 for t in tasks if t.state in ["FAILURE", "RETRY", "REVOKED"]
            )

            return CeleryStats(
                success=success_count,
                running=running_count,
                failed=failed_count,
                total=len(tasks),
            )
        except Exception as e:
            logger.warning(f"Could not get Celery stats: {e}")
            return CeleryStats()

    async def get_dashboard_data(self) -> FlowerDashboardResponse:
        """Get all dashboard data in one call"""
        # Run all requests concurrently
        workers_task = self.get_workers()
        tasks_task = self.get_tasks(50)

        workers, tasks = await asyncio.gather(
            workers_task, tasks_task, return_exceptions=True
        )

        # Handle exceptions
        if isinstance(workers, Exception):
            logger.error(f"Failed to get workers: {workers}")
            workers = []

        if isinstance(tasks, Exception):
            logger.error(f"Failed to get tasks: {tasks}")
            tasks = []

        # Calculate stats
        online_count = sum(1 for w in workers if w.status == "online")
        worker_stats = WorkerStats(
            total=len(workers), online=online_count, offline=len(workers) - online_count
        )

        # Calculate Celery stats from tasks
        success_count = sum(1 for t in tasks if t.state == "SUCCESS")
        running_count = sum(
            1 for t in tasks if t.state in ["PENDING", "STARTED", "RUNNING"]
        )
        failed_count = sum(
            1 for t in tasks if t.state in ["FAILURE", "RETRY", "REVOKED"]
        )

        celery_stats = CeleryStats(
            success=success_count,
            running=running_count,
            failed=failed_count,
            total=len(tasks),
        )

        return FlowerDashboardResponse(
            workers=workers,
            worker_stats=worker_stats,
            celery_stats=celery_stats,
            tasks=tasks,
        )
