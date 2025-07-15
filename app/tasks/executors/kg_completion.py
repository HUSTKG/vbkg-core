import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class KgCompletionExecutor(BaseStepExecutor):
    """Enhanced KG completion với graph state support"""

    def _check_prerequisites(self) -> bool:
        """KG completion cần entities"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for KG completion")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.entity_enrichment import EntityEnrichmentTask
            from app.tasks.executors.step_logger import StepLogger
            from app.tasks.kg_completion import KnowledgeGraphCompletionTask

            step_service = PipelineStepService()

            logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            completion_types = self.config.get(
                "completion_types", ["missing_entities", "missing_relationships"]
            )
            auto_apply_suggestions = self.config.get("auto_apply_suggestions", False)
            confidence_threshold = self.config.get("confidence_threshold", 0.8)
            user_id = self.config.get("user_id")

            # Get entities and relationships từ graph state
            entities = self._get_best_entities()
            relationships = self._get_best_relationships()

            # Create task and execute
            task = KnowledgeGraphCompletionTask(logger=logger)
            result = await task.complete_knowledge_graph(
                entities=entities,
                relationships=relationships,
                completion_types=completion_types,
                auto_apply_suggestions=auto_apply_suggestions,
                confidence_threshold=confidence_threshold,
                user_id=user_id,
            )

            return {
                "completion_result": self._track_provenance(result),
                "input_entity_count": len(entities),
                "input_relationship_count": len(relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "kg_completion",
                    "completion_types": completion_types,
                    "confidence_threshold": confidence_threshold,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"KG completion execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với completion suggestions"""
        if "completion_result" in step_result:
            completion_data = step_result["completion_result"]

            if "data" in completion_data:
                data = completion_data["data"]

                # Add suggested entities if any
                suggested_entities = data.get("suggested_entities", [])
                if suggested_entities:
                    self.graph_state.add_entities(suggested_entities, self.step_name)

                # Add suggested relationships if any
                suggested_relationships = data.get("suggested_relationships", [])
                if suggested_relationships:
                    self.graph_state.add_relationships(
                        suggested_relationships, self.step_name
                    )
