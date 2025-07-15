import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class OntologyEnrichmentExecutor(BaseStepExecutor):
    """Enhanced Ontology Enrichment với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Ontology enrichment cần entities từ knowledge extraction"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for ontology enrichment")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.entity_enrichment import EntityEnrichmentTask
            from app.tasks.executors.step_logger import StepLogger
            from app.tasks.kg_extraction import KgExtractionTask
            from app.tasks.ontology_enrichment import OntologyEnrichmentTask

            step_service = PipelineStepService()

            self.logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            ontology_task = OntologyEnrichmentTask(logger=self.logger)

            domain = self.config.get("domain")
            user_id = self.config.get("user_id")
            auto_apply_suggestions = self.config.get("auto_apply_suggestions", False)
            confidence_threshold = self.config.get("confidence_threshold", 0.8)
            use_existing_mappings = self.config.get("use_existing_mappings", True)
            enable_ontology_extensions = self.config.get(
                "enable_ontology_extensions", False
            )

            # Get entities and relationships từ graph state
            entities = self._get_best_entities()
            relationships = self._get_best_relationships()

            if not entities and not relationships:
                await self.logger.warning(
                    "No entities or relationships found for ontology enrichment"
                )
                return {
                    "ontology_result": self._track_provenance(
                        {
                            "enriched_entities": [],
                            "enriched_relationships": [],
                            "entity_mapping_suggestions": [],
                            "relationship_mapping_suggestions": [],
                            "current_ontology": {},
                            "updated_ontology": {},
                        }
                    ),
                    "entity_count": 0,
                    "relationship_count": 0,
                    "mapping_suggestions_count": 0,
                    "metadata": {
                        "execution_time": datetime.now(timezone.utc).isoformat(),
                        "step_type": "ontology_enrichment",
                    },
                }

            # Perform ontology enrichment
            enrichment_result = await ontology_task.enrich_with_ontology_mapping(
                entities=entities,
                relationships=relationships,
                domain=domain,
                user_id=user_id if user_id else None,
                auto_apply_suggestions=auto_apply_suggestions,
                confidence_threshold=confidence_threshold,
                use_existing_mappings=use_existing_mappings,
            )

            # Generate extension suggestions if enabled
            extension_suggestions = []
            if enable_ontology_extensions:
                extension_result = await ontology_task.suggest_ontology_extensions(
                    entities=entities,
                    relationships=relationships,
                    domain=domain,
                    user_id=user_id if user_id else None,
                )
                extension_suggestions = extension_result.get(
                    "extension_suggestions", []
                )

            enriched_entities = enrichment_result.get("enriched_entities", [])
            enriched_relationships = enrichment_result.get("enriched_relationships", [])
            entity_mapping_suggestions = enrichment_result.get(
                "entity_mapping_suggestions", []
            )
            relationship_mapping_suggestions = enrichment_result.get(
                "relationship_mapping_suggestions", []
            )

            total_suggestions = len(entity_mapping_suggestions) + len(
                relationship_mapping_suggestions
            )

            return {
                "ontology_result": self._track_provenance(
                    {
                        "enriched_entities": enriched_entities,
                        "enriched_relationships": enriched_relationships,
                        "entity_mapping_suggestions": entity_mapping_suggestions,
                        "relationship_mapping_suggestions": relationship_mapping_suggestions,
                        "current_ontology": enrichment_result.get(
                            "current_ontology", {}
                        ),
                        "updated_ontology": enrichment_result.get(
                            "updated_ontology", {}
                        ),
                        "extension_suggestions": extension_suggestions,
                        "mapping_record_id": enrichment_result.get("mapping_record_id"),
                        "statistics": enrichment_result.get("statistics", {}),
                    }
                ),
                "entity_count": len(enriched_entities),
                "relationship_count": len(enriched_relationships),
                "mapping_suggestions_count": total_suggestions,
                "extension_suggestions_count": len(extension_suggestions),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "ontology_enrichment",
                    "domain": domain,
                    "auto_apply_suggestions": auto_apply_suggestions,
                    "confidence_threshold": confidence_threshold,
                    "ontology_extensions_enabled": enable_ontology_extensions,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Ontology enrichment execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với enriched entities/relationships"""

        if "ontology_result" in step_result:
            ontology_data = step_result["ontology_result"]

            if "data" in ontology_data:
                data = ontology_data["data"]

                # Update entities in graph state
                enriched_entities = data.get("enriched_entities", [])
                if enriched_entities:
                    self.graph_state.add_entities(enriched_entities, self.step_name)

                # Update relationships in graph state
                enriched_relationships = data.get("enriched_relationships", [])
                if enriched_relationships:
                    self.graph_state.add_relationships(
                        enriched_relationships, self.step_name
                    )
