from typing import Dict

from app.schemas.conflict_resolution import (
    ConflictCreate,
    ConflictSeverity,
    ConflictType,
)

from .base import BaseConflictService


class ConflictFactoryService(BaseConflictService):
    """Service for creating conflict objects"""

    def create_conflict(
        self,
        entity1: Dict,
        entity2: Dict,
        similarity: float,
        conflict_type: ConflictType,
    ) -> ConflictCreate:
        """Create a conflict object"""

        severity = self._determine_severity(similarity, conflict_type)

        return ConflictCreate(
            conflict_type=conflict_type,
            severity=severity,
            description=f"{conflict_type.value}: '{entity1['entity_text']}' vs '{entity2['entity_text']}'",
            confidence_score=similarity,
            source_entity_id=entity1["id"],
            target_entity_id=entity2["id"],
            conflicting_attributes=self._extract_conflicting_attributes(
                entity1, entity2
            ),
            context_data={
                "similarity_score": similarity,
                "entity1_confidence": entity1.get("confidence", 0.5),
                "entity2_confidence": entity2.get("confidence", 0.5),
                "detection_method": "incremental_batch",
            },
            detected_by="incremental_system",
        )

    def create_duplicate_conflict(
        self, entity1: Dict, entity2: Dict, similarity: float, method: str
    ) -> ConflictCreate:
        """Create a duplicate entity conflict"""

        return ConflictCreate(
            conflict_type=ConflictType.DUPLICATE_ENTITY,
            severity=ConflictSeverity.HIGH,
            description=f"Duplicate entity detected: '{entity1['entity_text']}'",
            confidence_score=similarity,
            source_entity_id=entity1["id"],
            target_entity_id=entity2["id"],
            conflicting_attributes={
                "text_match": "exact" if method == "exact_match" else "fuzzy",
                "similarity_score": str(similarity),
            },
            context_data={
                "detection_method": method,
                "entity1": entity1,
                "entity2": entity2,
            },
            detected_by="incremental_system",
        )

    def _determine_severity(
        self, similarity: float, conflict_type: ConflictType
    ) -> ConflictSeverity:
        """Determine conflict severity based on similarity and type"""

        if conflict_type == ConflictType.DUPLICATE_ENTITY:
            if similarity >= 0.98:
                return ConflictSeverity.CRITICAL
            elif similarity >= 0.95:
                return ConflictSeverity.HIGH
            else:
                return ConflictSeverity.MEDIUM

        elif conflict_type == ConflictType.TEMPORAL_CONFLICT:
            return ConflictSeverity.HIGH

        elif conflict_type == ConflictType.ATTRIBUTE_MISMATCH:
            if similarity >= 0.95:
                return ConflictSeverity.HIGH
            else:
                return ConflictSeverity.MEDIUM

        else:
            return ConflictSeverity.MEDIUM

    def _extract_conflicting_attributes(
        self, entity1: Dict, entity2: Dict
    ) -> Dict[str, str]:
        """Extract specific conflicting attributes between two entities"""

        props1 = entity1.get("properties", {})
        props2 = entity2.get("properties", {})
        conflicts = {}

        # Find common keys with different values
        common_keys = set(props1.keys()) & set(props2.keys())
        for key in common_keys:
            if props1[key] != props2[key]:
                conflicts[f"{key}_entity1"] = str(props1[key])
                conflicts[f"{key}_entity2"] = str(props2[key])

        # Add text comparison
        if entity1["entity_text"] != entity2["entity_text"]:
            conflicts["text_entity1"] = entity1["entity_text"]
            conflicts["text_entity2"] = entity2["entity_text"]

        return conflicts
