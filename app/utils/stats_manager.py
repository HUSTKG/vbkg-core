import json
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, Dict
from uuid import UUID

import psutil
from supabase._async.client import AsyncClient as Client

# ---- Context Managers for Metrics Collection ----


@contextmanager
def measure_time():
    """Context manager to measure execution time."""
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        return duration_ms


@contextmanager
def measure_resources():
    """Context manager to measure resource usage."""
    process = psutil.Process()
    start_cpu_time = process.cpu_times()
    start_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time

        end_cpu_time = process.cpu_times()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB

        cpu_usage = (end_cpu_time.user - start_cpu_time.user) / duration * 100
        memory_usage = end_memory
        memory_increase = end_memory - start_memory

        return {
            "cpu_utilization_percent": round(cpu_usage, 2),
            "memory_utilization_mb": round(memory_usage, 2),
            "memory_increase_mb": round(memory_increase, 2),
        }


# ---- Stats Manager Class ----


class StatsManager:
    """Manager for collecting, updating and storing pipeline statistics."""

    def __init__(self, pipeline_run_id: UUID, db: Client | None = None):
        self.pipeline_run_id = pipeline_run_id
        self.db = db
        self.stats = {
            "performance": {
                "total_duration_ms": 0,
                "step_durations": {},
                "cpu_utilization_percent": 0,
                "memory_utilization_mb": 0,
                "throughput": {"records_per_second": 0, "bytes_per_second": 0},
            },
            "data": {
                "records": {
                    "input": 0,
                    "processed": 0,
                    "output": 0,
                    "skipped": 0,
                    "failed": 0,
                },
                "sizes": {"input_bytes": 0, "output_bytes": 0},
            },
            "steps": {},
            "quality": {
                "success_rate": 0,
                "error_counts": {
                    "validation_errors": 0,
                    "timeout_errors": 0,
                    "parsing_errors": 0,
                },
                "warnings": 0,
            },
            "runtime": {
                "start_timestamp": datetime.now().isoformat(),
                "end_timestamp": None,
                "worker_id": None,
                "retries": 0,
            },
        }

    @contextmanager
    def measure_step(self, step_id: UUID):
        """Measure execution time and resources for a pipeline step."""
        step_start_time = time.time()
        process = psutil.Process()
        start_cpu = process.cpu_percent()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Initialize step stats if not already present
        if str(step_id) not in self.stats["steps"]:
            self.stats["steps"][str(step_id)] = {
                "duration_ms": 0,
                "cpu_percent": 0,
                "memory_mb": 0,
                "records_processed": 0,
            }

        try:
            yield self  # Allow access to self within the context
        finally:
            step_end_time = time.time()
            duration_ms = int((step_end_time - step_start_time) * 1000)

            # Record step duration
            self.stats["performance"]["step_durations"][str(step_id)] = duration_ms
            self.stats["steps"][str(step_id)]["duration_ms"] = duration_ms

            # Record resource usage
            end_cpu = process.cpu_percent()
            end_memory = process.memory_info().rss / 1024 / 1024

            self.stats["steps"][str(step_id)]["cpu_percent"] = end_cpu - start_cpu
            self.stats["steps"][str(step_id)]["memory_mb"] = end_memory

    def update_step_stats(self, step_id: UUID, metrics: Dict[str, Any]):
        """Update step-specific statistics."""
        if str(step_id) not in self.stats["steps"]:
            self.stats["steps"][str(step_id)] = {}

        # Merge the provided metrics into the step stats
        self.stats["steps"][str(step_id)].update(metrics)

    def increment_counters(self, counter_path: str, value: int = 1):
        """Increment a counter at the specified path."""
        parts = counter_path.split(".")
        current = self.stats

        # Navigate to the nested counter
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Increment the counter
        last_part = parts[-1]
        if last_part not in current:
            current[last_part] = 0
        current[last_part] += value

    def finalize_stats(self):
        """Calculate final statistics and update derived values."""
        # Set end timestamp
        self.stats["runtime"]["end_timestamp"] = datetime.utcnow().isoformat()

        # Calculate total duration
        if (
            self.stats["runtime"]["start_timestamp"]
            and self.stats["runtime"]["end_timestamp"]
        ):
            start = datetime.fromisoformat(self.stats["runtime"]["start_timestamp"])
            end = datetime.fromisoformat(self.stats["runtime"]["end_timestamp"])
            self.stats["performance"]["total_duration_ms"] = int(
                (end - start).total_seconds() * 1000
            )

        # Calculate success rate
        total_records = self.stats["data"]["records"]["input"]
        if total_records > 0:
            successful = self.stats["data"]["records"]["output"]
            self.stats["quality"]["success_rate"] = round(successful / total_records, 4)

        # Calculate throughput
        duration_seconds = self.stats["performance"]["total_duration_ms"] / 1000
        if duration_seconds > 0:
            records_processed = self.stats["data"]["records"]["processed"]
            bytes_processed = self.stats["data"]["sizes"]["input_bytes"]

            self.stats["performance"]["throughput"]["records_per_second"] = round(
                records_processed / duration_seconds, 2
            )
            self.stats["performance"]["throughput"]["bytes_per_second"] = round(
                bytes_processed / duration_seconds, 2
            )

    async def save_stats(self):
        """Save the statistics to the database."""
        if not self.db:
            return

        # Finalize stats before saving
        self.finalize_stats()

        # Save to the database
        stats_data = json.dumps(self.stats)

        await self.db.table("pipeline_runs").update({"stats": stats_data}).eq(
            "id", str(self.pipeline_run_id)
        ).execute()


# ---- Decorator for Celery Tasks ----


def track_stats(func):
    """Decorator to track statistics for pipeline step execution."""

    @wraps(func)
    async def wrapper(step_id, pipeline_run_id, *args, **kwargs):
        from app.core.supabase import get_supabase

        supabase = await get_supabase()
        # Initialize stats manager
        stats_manager = StatsManager(pipeline_run_id, supabase)

        try:
            # Execute the step with stats tracking
            with stats_manager.measure_step(step_id):
                # Get initial record count if available in context
                if (
                    "pipeline_context" in kwargs
                    and "data" in kwargs["pipeline_context"]
                ):
                    input_records = len(
                        kwargs["pipeline_context"]["data"].get("records", [])
                    )
                    stats_manager.stats["data"]["records"]["input"] = input_records

                # Run the actual task function
                result = func(
                    step_id,
                    pipeline_run_id,
                    *args,
                    **kwargs,
                )

                # Record output record count if available in result
                if isinstance(result, tuple) and len(result) == 3:
                    _, _, context = result
                    if "data" in context and "records" in context["data"]:
                        output_records = len(context["data"]["records"])
                        stats_manager.stats["data"]["records"][
                            "output"
                        ] = output_records

                return result
        except Exception as e:
            # Record the error
            stats_manager.increment_counters("quality.error_counts.total")
            error_type = type(e).__name__
            if "timeout" in error_type.lower():
                stats_manager.increment_counters("quality.error_counts.timeout_errors")
            elif "validation" in error_type.lower():
                stats_manager.increment_counters(
                    "quality.error_counts.validation_errors"
                )
            elif "parse" in error_type.lower() or "syntax" in error_type.lower():
                stats_manager.increment_counters("quality.error_counts.parsing_errors")

            # Re-raise the exception after recording stats
            raise
        finally:
            # Save stats to the database
            stats_manager.finalize_stats()
            await supabase.table("pipeline_runs").update(
                {"stats": json.dumps(stats_manager.stats)}
            ).eq("id", str(pipeline_run_id)).execute()

    return wrapper
