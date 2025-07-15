from typing import Any, Dict

from .base import IncrementalConflictConfig
from .pipeline_integration import PipelineIntegrationService
from .storage import ConflictStorageService


class EnhancedKnowledgeExtractorExecutor:
    """Enhanced knowledge extractor with automatic conflict detection"""

    def __init__(self, step_config, step_metadata, graph_state=None):
        self.config = step_config
        self.metadata = step_metadata
        self.graph_state = graph_state

        # Initialize incremental conflict services
        conflict_config = IncrementalConflictConfig(
            enable_llm_resolution=step_config.get(
                "enable_llm_conflict_resolution", True
            ),
            confidence_threshold=step_config.get("conflict_confidence_threshold", 0.8),
        )
        self.pipeline_service = PipelineIntegrationService(conflict_config)
        self.storage_service = ConflictStorageService(conflict_config)

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge extraction with automatic conflict detection"""

        # Original knowledge extraction logic
        from app.tasks.kg_extraction import KgExtractionTask

        kg_extraction_task = KgExtractionTask()

        # Execute extraction (existing logic would go here)
        result = await kg_extraction_task.execute(input_data)

        # After extraction, detect conflicts
        conflicts = []
        if result.get("entities"):
            conflicts = (
                await self.pipeline_service.process_knowledge_extraction_conflicts(
                    result, self.metadata.get("step_id", "unknown")
                )
            )

            # Store conflicts in database if any found
            if conflicts:
                await self.storage_service.store_conflicts(conflicts)
                logger.info(
                    f"Detected {len(conflicts)} conflicts during knowledge extraction"
                )

        # Add conflict information to result
        result["detected_conflicts"] = {
            "count": len(conflicts),
            "conflicts": [conflict.model_dump() for conflict in conflicts],
            "detection_method": "incremental_batch",
        }

        return result
