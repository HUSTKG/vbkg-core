import logging
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class KnowledgeExtractorExecutor(BaseStepExecutor):
    """Enhanced Knowledge Extractor with updated graph state support for saved entities/relationships"""

    def _check_prerequisites(self) -> bool:
        """Knowledge extraction needs text data"""
        text_data = self._get_best_text_data()
        if not text_data:
            logger.warning("No text data available for knowledge extraction")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.entity_enrichment import EntityEnrichmentTask
            from app.tasks.executors.step_logger import StepLogger
            from app.tasks.kg_extraction import KgExtractionTask

            step_service = PipelineStepService()

            self.logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            kg_extraction_task = KgExtractionTask(logger=self.logger)

            domain = self.config.get("domain")
            user_id = self.config.get("user_id")
            confidence_threshold = self.config.get("confidence_threshold", 0.7)
            auto_save = self.config.get("auto_save", True)

            # Get text data from graph state
            text_data = self._get_best_text_data()
            if not text_data:
                await self.logger.warning("No text data found for knowledge extraction")
                return {
                    "extraction_result": self._track_provenance(
                        {
                            "entities": [],
                            "relationships": [],
                            "extraction_id": None,
                        }
                    ),
                    "entity_count": 0,
                    "relationship_count": 0,
                    "metadata": {
                        "execution_time": datetime.now(timezone.utc).isoformat(),
                        "step_type": "knowledge_extraction",
                    },
                }

            logger.info(
                f"Starting knowledge extraction for {len(text_data)} text items"
            )

            # Process based on data type
            if len(text_data) > 1 or any("chunk_id" in item for item in text_data):

                await self.logger.info(
                    f"Extracting knowledge from {len(text_data)} text chunks"
                )
                # Process as chunks
                result = await kg_extraction_task.extract_knowledge_from_chunks(
                    text_chunks=text_data,
                    domain=domain,
                    user_id=UUID(user_id) if user_id else None,
                    confidence_threshold=confidence_threshold,
                    auto_save=auto_save,
                    step_id=self.step_id,
                    pipeline_id=self.pipeline_id,
                )
            else:
                # Process as single text
                text_content = text_data[0].get("text", "") or text_data[0].get(
                    "content", ""
                )

                await self.logger.info(
                    f"Extracting knowledge from text content: {text_content[:100]}..."
                )

                result = await kg_extraction_task.extract_knowledge_from_text(
                    text_content=text_content,
                    domain=domain,
                    user_id=UUID(user_id) if user_id else None,
                    confidence_threshold=confidence_threshold,
                    auto_save=auto_save,
                    step_id=self.step_id,
                    pipeline_id=self.pipeline_id,
                    incremental_config=self.config.get("incremental_config"),
                )

            logger.info(
                f"Knowledge extraction completed with {len(result.get('entities', []))} entities "
            )

            entities = result.get("entities", [])
            relationships = result.get("relationships", [])
            extraction_id = result.get("extraction_id")

            return {
                "extraction_result": self._track_provenance(
                    {
                        "entities": entities,
                        "relationships": relationships,
                        "extraction_id": extraction_id,
                        "statistics": result.get("statistics", {}),
                    }
                ),
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "knowledge_extraction",
                    "domain": domain,
                    "confidence_threshold": confidence_threshold,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Knowledge extraction execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state with extracted entities/relationships (now with database IDs)"""

        if "extraction_result" in step_result:
            extraction_data = step_result["extraction_result"]

            if "data" in extraction_data:
                data = extraction_data["data"]

                # Add entities to graph state (they now have database IDs from Supabase)
                entities = data.get("entities", [])
                if entities:
                    logger.info(
                        f"Adding {len(entities)} entities with database IDs to graph state"
                    )
                    self.graph_state.add_entities(entities, self.step_name)

                # Add relationships to graph state (they now have database IDs from Supabase)
                relationships = data.get("relationships", [])
                if relationships:
                    logger.info(
                        f"Adding {len(relationships)} relationships with database IDs to graph state"
                    )
                    self.graph_state.add_relationships(relationships, self.step_name)
