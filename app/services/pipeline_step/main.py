from typing import Any, Dict, List, Optional

from postgrest.base_request_builder import APIResponse

from app.schemas.pipeline_step import (
    PipelineStepCreate,
    PipelineStepRunCreate,
    PipelineStepRunUpdate,
    PipelineStepUpdate,
)

from .configuration import PipelineStepConfigurationService
from .dependencies import PipelineStepDependencyService
from .execution import PipelineStepExecutionService
from .logging import PipelineStepLoggingService
from .management import PipelineStepManagementService
from .template import PipelineStepTemplateService


class PipelineStepService:
    """Main facade service for all pipeline step operations"""

    def __init__(self):
        self.management_service = PipelineStepManagementService()
        self.execution_service = PipelineStepExecutionService()
        self.dependency_service = PipelineStepDependencyService()
        self.config_service = PipelineStepConfigurationService()
        self.logging_service = PipelineStepLoggingService()
        self.template_service = PipelineStepTemplateService()

    # Step Management - delegate to ManagementService
    async def create_pipeline_step(
        self, step_in: PipelineStepCreate, pipeline_id: str
    ) -> Dict[str, Any]:
        return await self.management_service.create_pipeline_step(step_in, pipeline_id)

    async def get_pipeline_step(self, step_id: str, pipeline_id: str) -> Dict[str, Any]:
        return await self.management_service.get_pipeline_step(step_id, pipeline_id)

    async def update_pipeline_step(
        self, step_id: str, step_update: PipelineStepUpdate, pipeline_id: str
    ) -> Dict[str, Any]:
        return await self.management_service.update_pipeline_step(
            step_id, step_update, pipeline_id
        )

    async def delete_pipeline_step(
        self, step_id: str, pipeline_id: str
    ) -> Dict[str, Any]:
        return await self.management_service.delete_pipeline_step(step_id, pipeline_id)

    async def get_pipeline_steps(
        self, pipeline_id: str, limit: int = 100, skip: int = 0
    ) -> APIResponse[Dict[str, Any]]:
        return await self.management_service.get_pipeline_steps(
            pipeline_id, limit, skip
        )

    # Step Execution - delegate to ExecutionService
    async def create_step_run(
        self, step_run_in: PipelineStepRunCreate
    ) -> Dict[str, Any]:
        return await self.execution_service.create_step_run(step_run_in)

    async def get_pipeline_step_run(self, step_run_id: str) -> Dict[str, Any]:
        return await self.execution_service.get_pipeline_step_run(step_run_id)

    async def update_pipeline_step_run(
        self, step_run_id: str, step_run_update: PipelineStepRunUpdate
    ) -> Dict[str, Any]:
        return await self.execution_service.update_pipeline_step_run(
            step_run_id, step_run_update
        )

    async def delete_pipeline_step_run(self, step_run_id: str) -> Dict[str, Any]:
        return await self.execution_service.delete_pipeline_step_run(step_run_id)

    async def get_pipeline_step_runs(
        self,
        pipeline_run_id: str,
        step_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        return await self.execution_service.get_pipeline_step_runs(
            pipeline_run_id, step_id, status, limit, skip
        )

    # Dependencies - delegate to DependencyService
    async def get_step_execution_order(self, pipeline_id: str) -> List[List[str]]:
        return await self.dependency_service.get_step_execution_order(pipeline_id)

    # Logging - delegate to LoggingService
    async def get_step_execution_logs(
        self,
        step_run_id: Optional[str] = None,
        log_level: Optional[str] = None,
        start_time: Optional[str] = None,
        search: Optional[str] = None,
        end_time: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> APIResponse[Dict[str, Any]]:
        return await self.logging_service.get_step_execution_logs(
            step_run_id, log_level, start_time, end_time, search, skip, limit
        )

    async def create_step_execution_log(
        self, pipeline_run_id: str, step_run_id: str, log_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self.logging_service.create_step_execution_log(
            pipeline_run_id, step_run_id, log_data
        )

    # Templates - delegate to TemplateService
    async def _generate_steps_from_template(
        self,
        datasource: Dict[str, Any],
        template: Dict[str, Any],
        custom_options: Dict[str, Any],
    ) -> List[PipelineStepCreate]:
        return await self.template_service.generate_steps_from_template(
            datasource, template, custom_options
        )
