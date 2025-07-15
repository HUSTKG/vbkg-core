import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class QualityMonitoringExecutor(BaseStepExecutor):
    """Enhanced Quality monitoring với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Quality monitoring cần entities hoặc relationships"""
        entities = self._get_best_entities()
        relationships = self._get_best_relationships()
        if not entities and not relationships:
            logger.warning(
                "No entities or relationships available for quality monitoring"
            )
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.entity_enrichment import EntityEnrichmentTask
            from app.tasks.executors.step_logger import StepLogger
            from app.tasks.kg_extraction import KgExtractionTask
            from app.tasks.quality_monitoring import QualityMonitoringTask

            step_service = PipelineStepService()

            self.logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            quality_threshold = self.config.get("quality_threshold", 0.8)
            generate_recommendations = self.config.get("generate_recommendations", True)

            # Get entities and relationships từ graph state
            entities = self._get_best_entities()
            relationships = self._get_best_relationships()

            # Create task and execute
            task = QualityMonitoringTask(logger=self.logger)
            result = await task.monitor_quality(
                entities=entities,
                relationships=relationships,
                step_id=self.step_id,
                pipeline_run_id=self.pipeline_run_id,
                quality_threshold=quality_threshold,
                generate_recommendations=generate_recommendations,
            )

            return {
                "quality_result": self._track_provenance(result),
                "monitored_entity_count": len(entities),
                "monitored_relationship_count": len(relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "quality_monitoring",
                    "quality_threshold": quality_threshold,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Quality monitoring execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state metadata với quality results"""
        if "quality_result" in step_result:
            quality_data = step_result["quality_result"]
            if "data" in quality_data:
                # Store quality results in metadata
                self.graph_state.metadata["quality_monitoring"] = quality_data["data"]
