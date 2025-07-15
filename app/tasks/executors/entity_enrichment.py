import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class EntityEnrichmentExecutor(BaseStepExecutor):
    """Enhanced Entity enrichment với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Entity enrichment cần entities"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for entity enrichment")
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

            # Initialize EntityEnrichmentTask
            enrichment_task = EntityEnrichmentTask(logger=logger)

            enrichment_sources = self.config.get("enrichment_sources", [])
            enrichment_types = self.config.get("enrichment_types", ["embeddings"])
            batch_size = self.config.get("batch_size", 100)
            force_update = self.config.get("force_update", False)

            # Get entities từ graph state
            entities = self._get_best_entities()

            enrichment_results = {}
            enriched_entities = []  # Start with original entities

            # Add embeddings if requested
            if "embeddings" in enrichment_types and entities:
                entity_ids = [e["id"] for e in entities if e.get("id")]
                embedding_result = (
                    await enrichment_task.enrich_entities_with_embeddings(
                        entity_ids=entity_ids,
                        batch_size=batch_size,
                        force_update=force_update,
                    )
                )

                if embedding_result["status"] == "failed":
                    raise PipelineExecutionError(
                        f"Embedding enrichment failed: {embedding_result['error']}"
                    )
                enrichment_results["embeddings"] = embedding_result
                enriched_entities = embedding_result.get("enriched_entities", entities)

            # Sync to Neo4j if requested
            if "neo4j_sync" in enrichment_types and entities:
                entity_ids = [e["id"] for e in entities if e.get("id")]
                if entity_ids:
                    neo4j_result = await enrichment_task.sync_entities_to_neo4j(
                        entity_ids=entity_ids,
                        batch_size=batch_size,
                    )
                    enrichment_results["neo4j_sync"] = neo4j_result

            # External data enrichment if requested
            if "external_data" in enrichment_types and entities and enrichment_sources:
                entity_ids = [e["id"] for e in entities if e.get("id")]
                if entity_ids:
                    external_result = (
                        await enrichment_task.enrich_entities_with_external_data(
                            entity_ids=entity_ids,
                            enrichment_sources=enrichment_sources,
                            batch_size=batch_size,
                        )
                    )
                    enrichment_results["external_data"] = external_result

            return {
                "enrichment_result": self._track_provenance(
                    {
                        "enriched_entities": enriched_entities,
                        "enrichment_stats": enrichment_results,
                    }
                ),
                "entity_count": len(enriched_entities),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "entity_enrichment",
                    "enrichment_types": enrichment_types,
                    "enrichment_sources": enrichment_sources,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Entity enrichment execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với enriched entities"""
        if "enrichment_result" in step_result:
            enrichment_data = step_result["enrichment_result"]

            if "data" in enrichment_data:
                data = enrichment_data["data"]

                # Update entities với enriched versions
                enriched_entities = data.get("enriched_entities", [])
                if enriched_entities:
                    self.graph_state.add_entities(enriched_entities, self.step_name)
