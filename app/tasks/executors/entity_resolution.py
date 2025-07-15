import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class EntityResolutionExecutor(BaseStepExecutor):
    """Enhanced Entity Resolution với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Entity resolution cần entities"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for entity resolution")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.entity_enrichment import EntityEnrichmentTask
            from app.tasks.entity_resolution import EntityResolutionTask
            from app.tasks.executors.step_logger import StepLogger

            step_service = PipelineStepService()

            logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            resolution_strategy = self.config.get("resolution_strategy", "fuzzy_match")
            similarity_threshold = self.config.get("similarity_threshold", 0.8)
            clustering_method = self.config.get("clustering_method", "single_linkage")
            auto_save = self.config.get("auto_save", True)
            user_id = self.config.get("user_id")

            step_run_id = self.config.get("step_run_id")
            # Get entities từ graph state
            entities = self._get_best_entities()

            # Create task and execute
            task = EntityResolutionTask(logger=logger)
            result = await task.resolve_entities(
                entities=entities,
                resolution_strategy=resolution_strategy,
                step_run_id=step_run_id,
                similarity_threshold=similarity_threshold,
                clustering_method=clustering_method,
                auto_save=auto_save,
                user_id=user_id,
            )

            return {
                "resolution_result": self._track_provenance(result),
                "input_entity_count": len(entities),
                "resolved_entity_count": len(result.get("resolved_entities", [])),
                "cluster_count": len(result.get("entity_clusters", [])),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "entity_resolution",
                    "resolution_strategy": resolution_strategy,
                    "similarity_threshold": similarity_threshold,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Entity resolution execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với resolved entities"""

        if "resolution_result" in step_result:
            resolution_data = step_result["resolution_result"]

            if "data" in resolution_data:
                data = resolution_data["data"]

                # Update entities với resolved versions
                resolved_entities = data.get("resolved_entities", [])
                if resolved_entities:
                    self.graph_state.add_entities(resolved_entities, self.step_name)
