from datetime import datetime
from typing import Dict, List

from app.schemas.conflict_resolution import ConflictCreate

from .base import BaseConflictService


class ConflictStorageService(BaseConflictService):
    """Service for storing and retrieving conflict data"""

    async def store_conflicts(self, conflicts: List[ConflictCreate]):
        """Store detected conflicts in database"""

        if not conflicts:
            return

        supabase = await self.get_supabase()

        conflict_records = []
        for conflict in conflicts:
            conflict_data = conflict.model_dump()
            conflict_data["detected_at"] = datetime.now().isoformat()
            conflict_data["status"] = "detected"
            conflict_records.append(conflict_data)

        # Batch insert conflicts
        try:
            await supabase.table("conflicts").insert(conflict_records).execute()
            self.logger.info(f"Stored {len(conflict_records)} conflicts in database")
        except Exception as e:
            self.logger.error(f"Failed to store conflicts: {e}")
            raise

    async def get_entities_batch(self, entity_ids: List[str]) -> List[Dict]:
        """Get entities data in batch"""

        if not entity_ids:
            return []

        supabase = await self.get_supabase()

        # Process in chunks to avoid URL length limits
        chunk_size = 50
        all_entities = []

        for i in range(0, len(entity_ids), chunk_size):
            chunk_ids = entity_ids[i : i + chunk_size]

            response = (
                await supabase.table("kg_entities")
                .select(
                    "id, entity_text, entity_type, properties, confidence, created_at, embedding, source_document_id"
                )
                .in_("id", chunk_ids)
                .eq("is_active", True)
                .execute()
            )

            if response.data:
                all_entities.extend(response.data)

        return all_entities

    async def get_existing_entities_by_type(
        self, entity_type: str, cutoff_time: datetime
    ) -> List[Dict]:
        """Get existing entities of a specific type within time window"""

        supabase = await self.get_supabase()

        response = (
            await supabase.table("kg_entities")
            .select(
                "id, entity_text, entity_type, properties, confidence, created_at, embedding"
            )
            .eq("entity_type", entity_type)
            .eq("is_active", True)
            .gte("updated_at", cutoff_time.isoformat())
            .execute()
        )

        return response.data
