import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.tasks.executors.step_logger import StepLogger

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class ConflictDetectionExecutor(BaseStepExecutor):
    """Enhanced Conflict Detection executor với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Conflict detection cần entities"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for conflict detection")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService

            step_service = PipelineStepService()

            logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            from app.tasks.conflict_detection import ConflictDetectionTask

            # Initialize ConflictDetectionTask
            conflict_task = ConflictDetectionTask(logger=logger)

            # Get configuration
            detection_types = self.config.get("detection_types", ["comprehensive"])
            threshold = self.config.get("threshold", 0.75)
            batch_size = self.config.get("batch_size", 100)
            entity_types = self.config.get("entity_types")
            include_relationships = self.config.get("include_relationships", True)
            include_temporal = self.config.get("include_temporal", True)

            # Get entities từ graph state
            entities = self._get_best_entities()
            entity_ids = [e["id"] for e in entities if e.get("id")]

            detection_results = {}
            total_conflicts = 0

            await logger.info(
                f"Starting conflict detection for {entity_ids} entities with types: {detection_types}"
            )

            # Run comprehensive detection or specific types
            if "comprehensive" in detection_types:
                await logger.info("Running comprehensive conflict detection")
                result = await conflict_task.run_comprehensive_conflict_detection(
                    entity_ids=entity_ids,
                    batch_size=batch_size,
                    include_relationships=include_relationships,
                    include_temporal=include_temporal,
                )
                detection_results["comprehensive"] = result
                total_conflicts = result.get("total_conflicts_detected", 0)
            else:
                # Run specific detection types
                if "entity_conflicts" in detection_types:
                    await logger.info("Running entity conflict detection")
                    entity_result = await conflict_task.detect_entity_conflicts(
                        threshold=threshold,
                        batch_size=batch_size,
                        entity_types=entity_types,
                        entity_ids=entity_ids,
                    )
                    detection_results["entity_conflicts"] = entity_result
                    total_conflicts += entity_result.get("conflicts_detected", 0)

                if "relationship_conflicts" in detection_types:
                    await logger.info("Running relationship conflict detection")
                    rel_result = await conflict_task.detect_relationship_conflicts(
                        batch_size=batch_size,
                    )
                    detection_results["relationship_conflicts"] = rel_result
                    total_conflicts += rel_result.get("conflicts_detected", 0)

                if "temporal_conflicts" in detection_types:
                    await logger.info("Running temporal conflict detection")
                    temporal_result = await conflict_task.detect_temporal_conflicts(
                        entity_ids=entity_ids,
                        batch_size=batch_size,
                    )
                    detection_results["temporal_conflicts"] = temporal_result
                    total_conflicts += temporal_result.get("conflicts_detected", 0)

            await logger.info(
                f"Conflict detection completed. Total conflicts detected: {total_conflicts}"
            )

            await logger.info(
                f"Conflict detection completed with {total_conflicts} total conflicts"
            )

            return {
                "conflict_detection_result": self._track_provenance(
                    {
                        "detection_results": detection_results,
                        "total_conflicts_detected": total_conflicts,
                        "entity_count": len(entities),
                        "detection_types": detection_types,
                        "threshold": threshold,
                    }
                ),
                "total_conflicts": total_conflicts,
                "entity_count": len(entities),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "conflict_detection",
                    "detection_types": detection_types,
                    "threshold": threshold,
                    "batch_size": batch_size,
                    "entity_types": entity_types,
                },
            }

        except Exception as e:
            await logger.error(f"Conflict detection execution failed: {str(e)}")
            raise PipelineExecutionError(f"Conflict detection execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với actual conflicts từ detection results"""
        if "conflict_detection_result" in step_result:
            conflict_data = step_result["conflict_detection_result"]
            if "data" in conflict_data:
                data = conflict_data["data"]

                # Store conflict detection results in metadata
                self.graph_state.metadata["conflict_detection"] = data

                # Extract actual conflicts từ detection results
                all_conflicts = []

                # Handle comprehensive detection results
                if "comprehensive" in data["detection_results"]:
                    # Comprehensive detection format
                    detailed_results = data["detection_results"]["comprehensive"][
                        "detailed_results"
                    ]
                    for detection_type, result in detailed_results.items():
                        if (
                            result.get("status") == "completed"
                            and "conflicts" in result
                        ):
                            conflicts = result["conflicts"]
                            for conflict in conflicts:
                                # Add detection type to conflict
                                conflict["detection_type"] = detection_type
                                all_conflicts.append(conflict)
                else:
                    # Individual detection types format
                    detection_results = data.get("detection_results", {})
                    for detection_type, result in detection_results.items():
                        if (
                            result.get("status") == "completed"
                            and "conflicts" in result
                        ):
                            conflicts = result["conflicts"]
                            for conflict in conflicts:
                                # Add detection type to conflict
                                conflict["detection_type"] = detection_type
                                all_conflicts.append(conflict)

                # Add actual conflicts vào graph state
                if all_conflicts:
                    self.graph_state.add_conflicts(all_conflicts, self.step_name)

                # Log summary
                total_conflicts = data.get("total_conflicts_detected", 0)
                logger.info(
                    f"Added {len(all_conflicts)} actual conflicts to graph state (total detected: {total_conflicts})"
                )

                # Log breakdown by detection type
                if "detailed_results" in data:
                    for detection_type, result in data["detailed_results"].items():
                        conflicts_count = result.get("conflicts_detected", 0)
                        if conflicts_count > 0:
                            logger.info(
                                f"  - {detection_type}: {conflicts_count} conflicts"
                            )
                else:
                    for detection_type, result in data.get(
                        "detection_results", {}
                    ).items():
                        conflicts_count = result.get("conflicts_detected", 0)
                        if conflicts_count > 0:
                            logger.info(
                                f"  - {detection_type}: {conflicts_count} conflicts"
                            )
