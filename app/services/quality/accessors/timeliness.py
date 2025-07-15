import asyncio
from datetime import datetime, timezone
from typing import Dict, List

from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import QualityDimension
from app.services.quality.base import QualityAssessor


class TimelinessAssessor(QualityAssessor):
    """Assess data timeliness based on recency and update frequency"""

    def get_dimension(self) -> QualityDimension:
        return QualityDimension.TIMELINESS

    async def assess(self, **kwargs) -> float:
        """Assess timeliness based on data freshness and update patterns"""
        supabase = await get_supabase()

        entities = await self._get_entities_with_timestamps(supabase)
        if not entities:
            return 1.0

        current_time = datetime.now(timezone.utc)
        total_score = sum(
            self._calculate_entity_timeliness(entity, current_time)
            for entity in entities
        )

        return total_score / len(entities)

    def _calculate_entity_timeliness(
        self, entity: Dict, current_time: datetime
    ) -> float:
        """Calculate timeliness score for a single entity"""
        updated_at = entity.get("updated_at")
        created_at = entity.get("created_at")

        if not updated_at:
            return 0.0

        # Parse timestamp (handle both string and datetime)
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except ValueError:
                return 0.0

        # Calculate age in days
        age_days = (current_time - updated_at).total_seconds() / (24 * 3600)

        # Apply decay function based on entity type and age
        entity_type = entity.get("entity_type", "")
        decay_factor = self._get_decay_factor(entity_type)

        # Exponential decay: score = e^(-age_days * decay_factor)
        import math

        score = math.exp(-age_days * decay_factor)

        # Bonus for recently updated data (within 7 days)
        if age_days <= 7:
            score = min(1.0, score * 1.1)

        # Penalty for very old data (over 365 days)
        if age_days > 365:
            score *= 0.5

        return max(0.0, min(1.0, score))

    def _get_decay_factor(self, entity_type: str) -> float:
        """Get decay factor based on entity type - how quickly data becomes stale"""
        decay_factors = {
            "PERSON": 0.002,  # People data can be relevant for longer
            "ORGANIZATION": 0.003,  # Org data changes more frequently
            "LOCATION": 0.001,  # Location data is most stable
            "EVENT": 0.01,  # Event data becomes stale quickly
            "PRODUCT": 0.005,  # Product data has medium decay
        }
        return decay_factors.get(entity_type, 0.003)  # Default medium decay

    async def _get_entities_with_timestamps(self, supabase) -> List[Dict]:
        """Get all active entities with their timestamp information"""
        response = (
            await supabase.table("kg_entities")
            .select("entity_type, updated_at, created_at")
            .eq("is_active", True)
            .execute()
        )
        return response.data

    def _calculate_update_frequency_score(self, entity: Dict) -> float:
        """Calculate score based on update frequency (optional enhancement)"""
        # This could be implemented to consider how often an entity is updated
        # relative to its expected update frequency
        # For now, return neutral score
        return 0.5

    async def get_timeliness_metrics(self) -> Dict:
        """Get detailed timeliness metrics for monitoring"""
        supabase = await get_supabase()
        entities = await self._get_entities_with_timestamps(supabase)

        if not entities:
            return {
                "total_entities": 0,
                "avg_age_days": 0,
                "stale_entities": 0,
                "fresh_entities": 0,
            }

        current_time = datetime.now(timezone.utc)
        ages = []
        stale_count = 0
        fresh_count = 0

        for entity in entities:
            updated_at = entity.get("updated_at")
            if updated_at:
                if isinstance(updated_at, str):
                    try:
                        updated_at = datetime.fromisoformat(
                            updated_at.replace("Z", "+00:00")
                        )
                    except ValueError:
                        continue

                age_days = (current_time - updated_at).total_seconds() / (24 * 3600)
                ages.append(age_days)

                if age_days > 90:  # Consider data older than 90 days as stale
                    stale_count += 1
                elif age_days <= 7:  # Consider data newer than 7 days as fresh
                    fresh_count += 1

        avg_age = sum(ages) / len(ages) if ages else 0

        return {
            "total_entities": len(entities),
            "avg_age_days": round(avg_age, 2),
            "stale_entities": stale_count,
            "fresh_entities": fresh_count,
            "stale_percentage": (
                round((stale_count / len(entities)) * 100, 2) if entities else 0
            ),
            "fresh_percentage": (
                round((fresh_count / len(entities)) * 100, 2) if entities else 0
            ),
        }
