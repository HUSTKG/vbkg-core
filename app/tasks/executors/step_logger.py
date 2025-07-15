from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.services.pipeline_step import PipelineStepService


@dataclass
class StepLogger:
    def __init__(
        self,
        step_name: str,
        pipeline_run_id: str,
        step_run_id: str,
        step_service: Optional[PipelineStepService] = None,
    ):
        """
        Initialize StepLogger với thông tin step và dịch vụ log
        """

        self.step_name = step_name
        self.step_run_id = step_run_id
        self.pipeline_run_id = pipeline_run_id
        self.step_service = step_service

    async def info(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Log info message"""
        if self.step_service and self.step_run_id:
            await self.step_service.create_step_execution_log(
                step_run_id=self.step_run_id,
                pipeline_run_id=self.pipeline_run_id,
                log_data={"log_level": "INFO", "message": message, "details": details},
            )

    async def debug(self, message: str, details: Dict[str, Any] = None):
        """Log debug message"""
        if self.step_service and self.step_run_id:
            await self.step_service.create_step_execution_log(
                step_run_id=self.step_run_id,
                pipeline_run_id=self.pipeline_run_id,
                log_data={"log_level": "DEBUG", "message": message, "details": details},
            )

    async def warning(self, message: str, details: Dict[str, Any] = None):
        """Log warning message"""
        if self.step_service and self.step_run_id:
            await self.step_service.create_step_execution_log(
                step_run_id=self.step_run_id,
                pipeline_run_id=self.pipeline_run_id,
                log_data={"log_level": "WARN", "message": message, "details": details},
            )

    async def error(self, message: str, details: Dict[str, Any] = None):
        """Log error message"""
        if self.step_service and self.step_run_id:
            await self.step_service.create_step_execution_log(
                step_run_id=self.step_run_id,
                pipeline_run_id=self.pipeline_run_id,
                log_data={"log_level": "ERROR", "message": message, "details": details},
            )
