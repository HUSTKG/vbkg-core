from typing import Dict

from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import QualityDimension
from app.services.quality.base import QualityAssessor


class AccuracyAssessor(QualityAssessor):
    """Assess data accuracy based on confidence and verification"""

    def get_dimension(self) -> QualityDimension:
        return QualityDimension.ACCURACY

    async def assess(self, **kwargs) -> float:
        """Assess accuracy based on confidence scores and verification status"""
        supabase = await get_supabase()

        entities = await self._get_entities_with_confidence(supabase)
        if not entities:
            return 1.0

        total_score = sum(
            self._calculate_entity_accuracy(entity) for entity in entities
        )
        return total_score / len(entities)

    def _calculate_entity_accuracy(self, entity: Dict) -> float:
        """Calculate accuracy score for single entity"""
        confidence = entity.get("confidence", 0.5)
        is_verified = entity.get("is_verified", False)

        # Boost score for verified entities
        score = confidence
        if is_verified:
            score = min(1.0, score * 1.2)

        return score

    async def _get_entities_with_confidence(self, supabase):
        """Get entities with confidence scores"""
        response = (
            await supabase.table("kg_entities")
            .select("confidence, is_verified")
            .eq("is_active", True)
            .execute()
        )
        return response.data
