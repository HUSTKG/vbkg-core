from typing import Dict

from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import QualityDimension
from app.services.quality.base import QualityAssessor


class ValidityAssessor(QualityAssessor):
    """Assess data validity based on schema compliance"""

    def get_dimension(self) -> QualityDimension:
        return QualityDimension.VALIDITY

    async def assess(self, **kwargs) -> float:
        """Assess validity based on schema compliance"""
        supabase = await get_supabase()

        entities = await self._get_entities_with_schema(supabase)
        if not entities:
            return 1.0

        schemas = self._get_entity_schemas()
        valid_entities = sum(
            1 for entity in entities if self._is_valid_entity(entity, schemas)
        )

        return valid_entities / len(entities)

    def _get_entity_schemas(self) -> Dict[str, Dict]:
        """Define entity schemas for validation"""
        return {
            "PERSON": {
                "required_type": str,
                "optional_fields": ["age", "occupation", "nationality"],
            },
            "ORGANIZATION": {
                "required_type": str,
                "optional_fields": ["industry", "founded_year", "headquarters"],
            },
        }

    def _is_valid_entity(self, entity: Dict, schemas: Dict) -> bool:
        """Check if entity complies with schema"""
        entity_type = entity.get("entity_type", "")
        properties = entity.get("properties", {})

        schema = schemas.get(entity_type)
        if not schema:
            return True  # No schema = valid

        # Basic schema validation
        for field, expected_type in schema.items():
            if field in properties and not isinstance(properties[field], expected_type):
                return False

        return True

    async def _get_entities_with_schema(self, supabase):
        response = (
            await supabase.table("kg_entities")
            .select("entity_type, properties")
            .eq("is_active", True)
            .execute()
        )
        return response.data
