import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException
from fastapi import status as HttpStatus
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from .base import BasePipelineStepService


class PipelineStepLoggingService(BasePipelineStepService):
    """Service for step execution logging"""

    async def get_step_execution_logs(
        self,
        step_run_id: Optional[str] = None,
        log_level: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> APIResponse[Dict[str, Any]]:
        """Get execution logs for a specific pipeline step run"""
        try:
            supabase = await self.get_supabase()

            # Build query
            query = supabase.from_("step_execution_logs").select(
                "*", count=CountMethod.exact
            )

            if step_run_id:
                query = query.eq("step_run_id", step_run_id)

            # Apply filters
            if log_level:
                if log_level not in ["DEBUG", "INFO", "WARN", "ERROR"]:
                    raise HTTPException(
                        status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                        detail="Invalid log_level. Must be one of: DEBUG, INFO, WARN, ERROR",
                    )
                query = query.eq("log_level", log_level)

            if start_time:
                query = query.gte("timestamp", start_time)

            if end_time:
                query = query.lte("timestamp", end_time)

            if search:
                query = query.ilike("message", f"%{search}%")

            # Execute query with pagination
            response = (
                await query.order("timestamp", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )

            # Parse details field if it exists
            for log_entry in response.data:
                if log_entry.get("details"):
                    try:
                        # Details should already be parsed as JSONB field
                        pass
                    except (json.JSONDecodeError, TypeError):
                        # Keep as string if not valid JSON
                        pass

            return response

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving step execution logs: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving step execution logs: {str(e)}",
            )

    async def create_step_execution_log(
        self, pipeline_run_id: str, step_run_id: str, log_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new execution log entry for a pipeline step run"""
        try:
            supabase = await self.get_supabase()

            # Prepare log entry data
            log_entry = {
                "step_run_id": step_run_id,
                "pipeline_run_id": pipeline_run_id,
                "log_level": log_data["log_level"],
                "message": log_data["message"],
                "timestamp": log_data.get(
                    "timestamp", datetime.now(timezone.utc).isoformat()
                ),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            # Add details if provided (JSONB field)
            if "details" in log_data and log_data["details"]:
                log_entry["details"] = log_data["details"]

            # Insert log entry
            response = (
                await supabase.from_("step_execution_logs").insert(log_entry).execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create step execution log",
                )

            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error creating step execution log: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating step execution log: {str(e)}",
            )
