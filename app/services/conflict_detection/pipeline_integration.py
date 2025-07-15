from typing import Any, Dict, List

from app.schemas.conflict_resolution import ConflictCreate

from .base import BaseConflictService
from .incremental import IncrementalConflictService
from .storage import ConflictStorageService


class PipelineIntegrationService(BaseConflictService):
    """Service for integrating conflict detection with pipeline steps"""

    def __init__(self, config=None):
        super().__init__(config)
        self.incremental_service = IncrementalConflictService(config)
        self.storage_service = ConflictStorageService(config)

    async def process_knowledge_extraction_conflicts(
        self, extraction_result: Dict[str, Any], step_id: str
    ) -> List[ConflictCreate]:
        """Integration point for knowledge extraction step"""

        entities = extraction_result.get("entities", [])
        if not entities:
            return []

        # Extract entity IDs from extraction result
        entity_ids = [entity.get("id") for entity in entities if entity.get("id")]

        if not entity_ids:
            return []

        # Run incremental conflict detection
        conflicts = await self.incremental_service.detect_incremental_conflicts(
            entity_ids, pipeline_step=f"knowledge_extraction_{step_id}"
        )

        return conflicts

    async def process_entity_resolution_conflicts(
        self, resolution_result: Dict[str, Any], step_id: str
    ) -> List[ConflictCreate]:
        """Integration point for entity resolution step"""

        resolved_entities = resolution_result.get("resolved_entities", [])
        if not resolved_entities:
            return []

        entity_ids = [
            entity.get("id") for entity in resolved_entities if entity.get("id")
        ]

        conflicts = await self.incremental_service.detect_incremental_conflicts(
            entity_ids, pipeline_step=f"entity_resolution_{step_id}"
        )

        return conflicts
