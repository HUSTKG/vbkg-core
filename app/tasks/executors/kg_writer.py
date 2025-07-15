import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class KgWriterExecutor(BaseStepExecutor):
    """Enhanced KG writer with updated logic for Neo4j sync since entities/relationships are already in Supabase"""

    def _check_prerequisites(self) -> bool:
        """KG writer needs entities or relationships"""
        entities = self._get_best_entities()
        relationships = self._get_best_relationships()
        if not entities and not relationships:
            logger.warning("No entities or relationships available for KG writing")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.entity_enrichment import EntityEnrichmentTask
            from app.tasks.executors.step_logger import StepLogger
            from app.tasks.kg_writer import KnowledgeGraphWriterTask

            step_service = PipelineStepService()

            logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            graph_format = self.config.get("graph_format", "neo4j")
            batch_size = self.config.get("batch_size", 1000)
            validate_before_write = self.config.get("validate_before_write", True)
            user_id = self.config.get("user_id")

            # Get entities and relationships from graph state (they should already have database IDs)
            entities = self._get_best_entities()
            relationships = self._get_best_relationships()

            await logger.info(
                f"Writing {len(entities)} entities and {len(relationships)} relationships to {graph_format}"
            )

            # Create task and execute
            task = KnowledgeGraphWriterTask(logger=logger)
            result = await task.write_knowledge_graph(
                entities=entities,
                relationships=relationships,
                graph_format=graph_format,
                batch_size=batch_size,
                validate_before_write=validate_before_write,
                user_id=user_id,
            )

            return {
                "write_result": self._track_provenance(result),
                "written_entity_count": len(entities),
                "written_relationship_count": len(relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "kg_writer",
                    "graph_format": graph_format,
                    "batch_size": batch_size,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"KG writer execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state metadata with write results (entities/relationships are already saved)"""
        if "write_result" in step_result:
            write_data = step_result["write_result"]
            if "data" in write_data:
                # Store write results in metadata
                self.graph_state.metadata["kg_writer"] = write_data["data"]

                # For Neo4j sync, entities and relationships should already be in graph state
                # We just update metadata about the sync process
                write_result = write_data["data"].get("write_result", {})
                entities_synced = write_result.get("entities_synced", 0)
                relationships_synced = write_result.get("relationships_synced", 0)

                logger.info(
                    f"Neo4j sync completed: {entities_synced} entities, {relationships_synced} relationships synced"
                )

                # Note: Entities and relationships are already in graph state with database IDs
                # The Neo4j sync updates the neo4j_id field in Supabase but doesn't change the entities/relationships
                # that are already in our graph state. This is by design since the data is already saved.
