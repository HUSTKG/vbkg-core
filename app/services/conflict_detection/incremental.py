from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Set

from app.schemas.conflict_resolution import ConflictCreate

from .base import BaseConflictService
from .entity_comparison import EntityComparisonService
from .llm_analysis import LLMAnalysisService
from .storage import ConflictStorageService


class IncrementalConflictService(BaseConflictService):
    """Service for incremental conflict detection"""

    def __init__(self, config=None):
        super().__init__(config)
        self.comparison_service = EntityComparisonService(config)
        self.llm_service = LLMAnalysisService(config)
        self.storage_service = ConflictStorageService(config)

        # Cache for recently processed entities
        self.processed_entities: Set[str] = set()
        self.entity_cache_ttl = timedelta(hours=self.config.temporal_window_hours)
        self.last_cleanup = datetime.now()

    async def detect_incremental_conflicts(
        self, new_entity_ids: List[str], pipeline_step: str = "incremental_update"
    ) -> List[ConflictCreate]:
        """Main entry point for incremental conflict detection"""

        if not new_entity_ids:
            return []

        self.logger.info(
            f"Starting incremental conflict detection for {len(new_entity_ids)} entities"
        )

        # Cleanup old cache entries periodically
        await self._cleanup_cache()

        # Filter out recently processed entities
        entities_to_process = [
            eid for eid in new_entity_ids if eid not in self.processed_entities
        ]

        if not entities_to_process:
            self.logger.info("No new entities to process (all recently processed)")
            return []

        # Get new entities data
        new_entities = await self.storage_service.get_entities_batch(
            entities_to_process
        )
        if not new_entities:
            return []

        # Detect conflicts in batches
        all_conflicts = await self._process_entities_in_batches(new_entities)

        # Enhanced LLM resolution for high-priority conflicts
        if self.config.enable_llm_resolution and all_conflicts:
            await self.llm_service.enhance_conflicts_with_llm(all_conflicts)

        self.logger.info(
            f"Incremental conflict detection completed. Found {len(all_conflicts)} conflicts"
        )
        return all_conflicts

    async def _process_entities_in_batches(
        self, new_entities: List[Dict]
    ) -> List[ConflictCreate]:
        """Process entities in batches to detect conflicts"""

        all_conflicts = []

        for i in range(0, len(new_entities), self.config.batch_size):
            batch = new_entities[i : i + self.config.batch_size]

            batch_conflicts = await self._detect_conflicts_for_batch(batch)
            all_conflicts.extend(batch_conflicts)

            # Mark entities as processed
            for entity in batch:
                self.processed_entities.add(entity["id"])

            # Break if we hit conflict limit for this run
            if len(all_conflicts) >= self.config.max_conflicts_per_batch:
                self.logger.warning(
                    f"Hit conflict limit ({self.config.max_conflicts_per_batch}), stopping batch processing"
                )
                break

        return all_conflicts

    async def _detect_conflicts_for_batch(
        self, new_entities: List[Dict]
    ) -> List[ConflictCreate]:
        """Detect conflicts for a batch of new entities"""

        conflicts = []

        # Group entities by type for efficiency
        entities_by_type = defaultdict(list)
        for entity in new_entities:
            entities_by_type[entity["entity_type"]].append(entity)

        # Process each type separately
        for entity_type, type_entities in entities_by_type.items():
            type_conflicts = await self._find_conflicts_within_type(
                entity_type, type_entities
            )
            conflicts.extend(type_conflicts)

        return conflicts

    async def _find_conflicts_within_type(
        self, entity_type: str, new_entities: List[Dict]
    ) -> List[ConflictCreate]:
        """Find conflicts between new entities and existing entities of the same type"""

        # Get existing entities of the same type (with temporal window optimization)
        cutoff_time = datetime.now() - self.entity_cache_ttl
        existing_entities = await self.storage_service.get_existing_entities_by_type(
            entity_type, cutoff_time
        )

        if not existing_entities:
            return []

        # Use comparison service to find conflicts
        return await self.comparison_service.find_conflicts_for_entities(
            new_entities, existing_entities
        )

    async def _cleanup_cache(self):
        """Cleanup old cache entries periodically"""

        now = datetime.now()
        if now - self.last_cleanup > timedelta(hours=1):
            # In a real implementation, you'd want to persist this cache
            # For now, just clear it periodically
            self.processed_entities.clear()
            self.last_cleanup = now
            self.logger.info("Cleaned up entity processing cache")
