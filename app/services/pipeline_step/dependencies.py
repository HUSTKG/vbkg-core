from typing import Any, Dict, List

from fastapi import HTTPException
from fastapi import status as HttpStatus

from .base import BasePipelineStepService


class PipelineStepDependencyService(BasePipelineStepService):
    """Service for managing step dependencies and execution order"""

    async def validate_step_dependencies(self, depends_on: List[str], pipeline_id: str):
        """Validate that all dependencies exist in the pipeline"""
        if not depends_on:
            return

        supabase = await self.get_supabase()
        response = (
            await supabase.from_("pipeline_steps")
            .select("id")
            .eq("pipeline_id", pipeline_id)
            .in_("id", depends_on)
            .execute()
        )

        found_ids = {step["id"] for step in response.data}
        missing_ids = set(depends_on) - found_ids

        if missing_ids:
            raise HTTPException(
                status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                detail=f"Dependency steps not found: {list(missing_ids)}",
            )

    async def get_dependent_steps(
        self, step_id: str, pipeline_id: str
    ) -> List[Dict[str, Any]]:
        """Get steps that depend on the given step"""
        supabase = await self.get_supabase()
        response = (
            await supabase.from_("pipeline_steps")
            .select("id, name")
            .eq("pipeline_id", pipeline_id)
            .contains("depends_on", [step_id])
            .execute()
        )

        return response.data

    async def get_step_execution_order(self, pipeline_id: str) -> List[List[str]]:
        """Get steps organized by execution order, considering dependencies"""
        try:
            from .management import PipelineStepManagementService

            management_service = PipelineStepManagementService()
            steps_response = await management_service.get_pipeline_steps(pipeline_id)
            steps = steps_response.data

            # Build dependency graph
            dependency_graph = {}
            all_steps = {}

            for step in steps:
                if not step["enabled"]:
                    continue

                step_id = step["id"]
                all_steps[step_id] = step
                dependency_graph[step_id] = step.get("depends_on", [])

            # Topological sort to determine execution order
            execution_levels = []
            remaining_steps = set(all_steps.keys())

            while remaining_steps:
                # Find steps with no unresolved dependencies
                ready_steps = []
                for step_id in remaining_steps:
                    dependencies = dependency_graph[step_id]
                    if not dependencies or all(
                        dep not in remaining_steps for dep in dependencies
                    ):
                        ready_steps.append(step_id)

                if not ready_steps:
                    # Circular dependency detected
                    raise HTTPException(
                        status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                        detail="Circular dependency detected in pipeline steps",
                    )

                execution_levels.append(ready_steps)
                remaining_steps -= set(ready_steps)

            return execution_levels

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(
                f"Error determining execution order for pipeline {pipeline_id}: {e}"
            )
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error determining execution order: {str(e)}",
            )
