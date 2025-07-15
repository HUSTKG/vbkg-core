from collections import defaultdict
from typing import Dict, List

from app.schemas.conflict_resolution import ConflictCreate

from .base import BaseConflictService
from .conflict_factory import ConflictFactoryService
from .similarity import SimilarityCalculationService


class EntityComparisonService(BaseConflictService):
    """Service for comparing entities and finding conflicts"""

    def __init__(self, config=None):
        super().__init__(config)
        self.similarity_service = SimilarityCalculationService(config)
        self.factory_service = ConflictFactoryService(config)

    async def find_conflicts_for_entities(
        self, new_entities: List[Dict], existing_entities: List[Dict]
    ) -> List[ConflictCreate]:
        """Find conflicts between new and existing entities"""

        conflicts = []

        # Group entities by type for efficiency
        existing_by_type = defaultdict(list)
        for entity in existing_entities:
            existing_by_type[entity["entity_type"]].append(entity)

        # Process new entities by type
        new_by_type = defaultdict(list)
        for entity in new_entities:
            new_by_type[entity["entity_type"]].append(entity)

        # Compare within each entity type
        for entity_type, new_type_entities in new_by_type.items():
            existing_type_entities = existing_by_type.get(entity_type, [])

            if existing_type_entities:
                type_conflicts = await self._find_conflicts_within_type(
                    new_type_entities, existing_type_entities
                )
                conflicts.extend(type_conflicts)

        return conflicts

    async def _find_conflicts_within_type(
        self, new_entities: List[Dict], existing_entities: List[Dict]
    ) -> List[ConflictCreate]:
        """Find conflicts between new and existing entities of the same type"""

        conflicts = []

        # Compare each new entity against existing ones
        for new_entity in new_entities:
            entity_conflicts = await self._find_conflicts_for_single_entity(
                new_entity, existing_entities
            )
            conflicts.extend(entity_conflicts)

        return conflicts

    async def _find_conflicts_for_single_entity(
        self, new_entity: Dict, existing_entities: List[Dict]
    ) -> List[ConflictCreate]:
        """Find conflicts for a single new entity against existing entities"""

        conflicts = []
        new_text = new_entity["entity_text"]

        for existing_entity in existing_entities:
            # Skip self-comparison
            if new_entity["id"] == existing_entity["id"]:
                continue

            existing_text = existing_entity["entity_text"]

            # Quick exact match check
            if new_text.lower().strip() == existing_text.lower().strip():
                conflict = self.factory_service.create_duplicate_conflict(
                    new_entity, existing_entity, 1.0, "exact_match"
                )
                conflicts.append(conflict)
                continue

            # Fuzzy similarity check
            text_similarity = self.similarity_service.calculate_text_similarity(
                new_text, existing_text
            )

            if text_similarity >= self.config.similarity_threshold:
                # Determine conflict type
                conflict_type = await self.similarity_service.determine_conflict_type(
                    new_entity, existing_entity, text_similarity
                )

                if conflict_type:
                    conflict = self.factory_service.create_conflict(
                        new_entity, existing_entity, text_similarity, conflict_type
                    )
                    conflicts.append(conflict)

        return conflicts
