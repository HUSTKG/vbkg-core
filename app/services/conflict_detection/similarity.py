from datetime import datetime
from typing import Dict, Optional

from app.schemas.conflict_resolution import ConflictType
from app.utils.similarity import calculate_similarity

from .base import BaseConflictService


class SimilarityCalculationService(BaseConflictService):
    """Service for calculating entity similarities and determining conflict types"""

    def calculate_text_similarity(
        self, text1: str, text2: str, method: str = "fuzzy"
    ) -> float:
        """Calculate similarity between two text strings"""
        text1_clean = text1.lower().strip()
        text2_clean = text2.lower().strip()

        if text1_clean == text2_clean:
            return 1.0

        return calculate_similarity(text1_clean, text2_clean, method=method)

    async def determine_conflict_type(
        self, entity1: Dict, entity2: Dict, similarity: float
    ) -> Optional[ConflictType]:
        """Determine the specific type of conflict between two entities"""

        props1 = entity1.get("properties", {})
        props2 = entity2.get("properties", {})

        # 1. Exact duplicates
        if similarity >= 0.95:
            return ConflictType.DUPLICATE_ENTITY

        # 2. Attribute mismatches (same entity, different attributes)
        if similarity >= 0.9:
            if self._has_attribute_conflicts(props1, props2):
                return ConflictType.ATTRIBUTE_MISMATCH

        # 3. Source conflicts
        if self._has_source_conflicts(entity1, entity2, similarity):
            return ConflictType.SOURCE_CONFLICT

        # 4. Temporal conflicts
        if await self._has_temporal_conflicts(props1, props2):
            return ConflictType.TEMPORAL_CONFLICT

        return None

    def _has_attribute_conflicts(self, props1: Dict, props2: Dict) -> bool:
        """Check if two property sets have conflicting attributes"""
        common_keys = set(props1.keys()) & set(props2.keys())
        if common_keys:
            mismatches = [key for key in common_keys if props1[key] != props2[key]]
            return len(mismatches) > 0
        return False

    def _has_source_conflicts(
        self, entity1: Dict, entity2: Dict, similarity: float
    ) -> bool:
        """Check if entities have source-based conflicts"""
        return (
            entity1.get("source_document_id") != entity2.get("source_document_id")
            and similarity >= 0.85
        )

    async def _has_temporal_conflicts(self, props1: Dict, props2: Dict) -> bool:
        """Check if two entities have temporal conflicts"""
        temporal_fields = ["date", "start_date", "end_date"]

        for field in temporal_fields:
            if field in props1 and field in props2:
                try:
                    date1 = datetime.fromisoformat(
                        str(props1[field]).replace("Z", "+00:00")
                    )
                    date2 = datetime.fromisoformat(
                        str(props2[field]).replace("Z", "+00:00")
                    )

                    # Check for significant temporal differences (more than 1 day)
                    if abs((date1 - date2).days) > 1:
                        return True

                except (ValueError, TypeError):
                    continue

        return False
