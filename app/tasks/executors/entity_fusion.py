import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class EntityFusionExecutor(BaseStepExecutor):
    """Enhanced Entity fusion với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Entity fusion cần resolved entities"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for entity fusion")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.entity_enrichment import EntityEnrichmentTask
            from app.tasks.executors.step_logger import StepLogger

            step_service = PipelineStepService()

            logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            from app.tasks.entity_fusion import EntityFusionTask

            fusion_strategy = self.config.get("fusion_strategy", "most_recent")
            preserve_provenance = self.config.get("preserve_provenance", True)
            conflict_resolution = self.config.get(
                "conflict_resolution", "highest_confidence"
            )
            auto_save = self.config.get("auto_save", True)
            user_id = self.config.get("user_id")

            # Get entities từ graph state thay vì từ input
            entities = self._get_best_entities()

            # Create simple clusters from entities if not available
            entity_clusters = [{"entities": entities, "cluster_id": "default"}]

            # Create task and execute
            task = EntityFusionTask(logger=logger)
            result = await task.fuse_entities(
                resolved_entities=entities,
                entity_clusters=entity_clusters,
                fusion_strategy=fusion_strategy,
                preserve_provenance=preserve_provenance,
                conflict_resolution=conflict_resolution,
                auto_save=auto_save,
                user_id=user_id,
            )

            return {
                "fusion_result": self._track_provenance(result),
                "input_entity_count": len(entities),
                "fused_entity_count": len(result.get("fused_entities", [])),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "entity_fusion",
                    "fusion_strategy": fusion_strategy,
                    "conflict_resolution": conflict_resolution,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Entity fusion execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với fused entities"""
        if "fusion_result" in step_result:
            fusion_data = step_result["fusion_result"]

            if "data" in fusion_data:
                data = fusion_data["data"]

                # Update entities với fused versions
                fused_entities = data.get("fused_entities", [])
                if fused_entities:
                    self.graph_state.add_entities(fused_entities, self.step_name)
