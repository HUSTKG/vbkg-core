from typing import Dict, List

from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import QualityDimension
from app.services.quality.base import QualityAssessor


class CompletenessAssessor(QualityAssessor):
    """Assess data completeness"""

    def get_dimension(self) -> QualityDimension:
        return QualityDimension.COMPLETENESS

    async def assess(self, **kwargs) -> float:
        """Assess completeness based on required attributes"""
        supabase = await get_supabase()

        entities = await self._get_all_entities(supabase)
        if not entities:
            return 1.0

        required_attributes = self._get_required_attributes()
        complete_entities = 0

        for entity in entities:
            if self._is_entity_complete(entity, required_attributes):
                complete_entities += 1

        return complete_entities / len(entities)

    def _get_required_attributes(self) -> Dict[str, List[str]]:
        """Define required attributes per entity type"""
        return {
            "PERSON": ["full_name", "date_of_birth"],
            "ORGANIZATION": ["name", "type"],
            "LOCATION": ["name", "coordinates"],
        }

    def _is_entity_complete(self, entity: Dict, required_attrs: Dict) -> bool:
        """Check if entity has all required attributes"""
        properties = entity.get("properties", {})
        entity_type = entity.get("entity_type", "")

        required = required_attrs.get(entity_type, [])
        if not required:
            return bool(properties)  # If no requirements, just need some properties

        return all(
            attr in properties
            and properties[attr] is not None
            and str(properties[attr]).strip()
            for attr in required
        )

    async def _get_all_entities(self, supabase):
        """Get all active entities"""
        response = (
            await supabase.table("kg_entities")
            .select("properties, entity_type")
            .eq("is_active", True)
            .execute()
        )
        return response.data
