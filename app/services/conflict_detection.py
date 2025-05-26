import asyncio
import logging
from typing import Dict, List, Optional

from app.core.supabase import get_supabase
from app.nlp.embeddings import get_text_embedding
from app.schemas.conflict_resolution import (Conflict, ConflictCreate,
                                             ConflictSeverity, ConflictType)
from app.utils.similarity import calculate_similarity

logger = logging.getLogger(__name__)


class ConflictDetectionService:
    """Advanced conflict detection for knowledge graph entities and relationships"""

    def __init__(self):
        self.similarity_thresholds = {
            ConflictType.DUPLICATE_ENTITY: 0.85,
            ConflictType.CONTRADICTORY_RELATIONSHIP: 0.7,
            ConflictType.ATTRIBUTE_MISMATCH: 0.6,
            ConflictType.TEMPORAL_CONFLICT: 0.8,
        }

    async def detect_all_conflicts(
        self, entity_ids: Optional[List[str]] = None, batch_size: int = 100
    ) -> List[ConflictCreate]:
        """Detect all types of conflicts in the knowledge graph"""

        all_conflicts = []

        # Run different conflict detection methods
        detection_tasks = [
            self.detect_duplicate_entities(entity_ids, batch_size),
            self.detect_contradictory_relationships(batch_size),
            self.detect_attribute_mismatches(entity_ids, batch_size),
            self.detect_temporal_conflicts(batch_size),
            self.detect_source_conflicts(batch_size),
        ]

        conflict_results = await asyncio.gather(
            *detection_tasks, return_exceptions=True
        )

        for result in conflict_results:
            if isinstance(result, Exception):
                logger.error(f"Conflict detection failed: {result}")
            else:
                all_conflicts.extend(result)

        return all_conflicts

    async def detect_duplicate_entities(
        self, entity_ids: Optional[List[str]] = None, batch_size: int = 100
    ) -> List[ConflictCreate]:
        """Detect potential duplicate entities using multiple methods"""

        supabase = await get_supabase()
        conflicts = []

        # Get entities to check
        query = supabase.table("kg_entities").select(
            "id, entity_text, entity_type, properties, embedding"
        )

        if entity_ids:
            # Check specific entities
            for i in range(0, len(entity_ids), 50):
                batch_ids = [str(id) for id in entity_ids[i : i + 50]]
                query = query.in_("id", batch_ids)
        else:
            # Check all entities in batches
            query = query.limit(batch_size)

        response = await query.execute()
        entities = response.data

        # Group entities by type for more efficient comparison
        entities_by_type = {}
        for entity in entities:
            entity_type = entity["entity_type"]
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # Detect duplicates within each type
        for entity_type, type_entities in entities_by_type.items():
            type_conflicts = await self._detect_duplicates_in_group(type_entities)
            conflicts.extend(type_conflicts)

        return conflicts

    async def _detect_duplicates_in_group(
        self, entities: List[Dict]
    ) -> List[ConflictCreate]:
        """Detect duplicates within a group of entities of the same type"""

        conflicts = []

        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):
                entity1, entity2 = entities[i], entities[j]

                # Multiple similarity checks
                similarities = await self._calculate_entity_similarities(
                    entity1, entity2
                )

                # Determine if it's a conflict
                max_similarity = max(similarities.values())
                if (
                    max_similarity
                    >= self.similarity_thresholds[ConflictType.DUPLICATE_ENTITY]
                ):

                    severity = self._determine_severity(max_similarity, similarities)

                    # convert similarities from float to string
                    similarities = {k: str(v) for k, v in similarities.items()}

                    conflict = ConflictCreate(
                        conflict_type=ConflictType.DUPLICATE_ENTITY,
                        severity=severity,
                        description=f"Potential duplicate entities detected: '{entity1['entity_text']}' and '{entity2['entity_text']}'",
                        confidence_score=max_similarity,
                        source_entity_id=entity1["id"],
                        target_entity_id=entity2["id"],
                        conflicting_attributes={
                            "text_similarity": similarities.get("text", "0"),
                            "semantic_similarity": similarities.get("semantic", "0"),
                            "attribute_similarity": similarities.get("attributes", "0"),
                        },
                        context_data={
                            "entity1_text": entity1["entity_text"],
                            "entity2_text": entity2["entity_text"],
                            "entity_type": entity1["entity_type"],
                            "similarity_scores": similarities,
                        },
                        detected_by="system",
                    )

                    conflicts.append(conflict)

        return conflicts

    async def _calculate_entity_similarities(
        self, entity1: Dict, entity2: Dict
    ) -> Dict[str, float]:
        """Calculate various similarity scores between two entities"""

        similarities = {}

        # Text similarity (exact and fuzzy)
        text1, text2 = entity1["entity_text"], entity2["entity_text"]
        similarities["exact"] = 1.0 if text1.lower() == text2.lower() else 0.0
        similarities["text"] = calculate_similarity(text1, text2, method="fuzzy")

        # Semantic similarity using embeddings
        if entity1.get("embedding") and entity2.get("embedding"):
            similarities["semantic"] = calculate_similarity(
                entity1["embedding"], entity2["embedding"], method="cosine"
            )
        else:
            # Generate embeddings if not available
            try:
                emb1 = await get_text_embedding(text1)
                emb2 = await get_text_embedding(text2)
                similarities["semantic"] = calculate_similarity(
                    emb1, emb2, method="cosine"
                )
            except Exception as e:
                logger.warning(f"Failed to generate embeddings: {e}")
                similarities["semantic"] = 0.0

        # Attribute similarity
        props1 = entity1.get("properties", {})
        props2 = entity2.get("properties", {})
        similarities["attributes"] = self._calculate_property_similarity(props1, props2)

        return similarities

    async def detect_contradictory_relationships(
        self, batch_size: int = 100
    ) -> List[ConflictCreate]:
        """Detect contradictory relationships between entities"""

        supabase = await get_supabase()
        conflicts = []

        # Get relationships with their entities
        response = (
            await supabase.table("kg_relationships")
            .select(
                "id, relationship_type, source_entity_id, target_entity_id, properties, confidence"
            )
            .limit(batch_size)
            .execute()
        )

        relationships = response.data

        # Group relationships by entity pairs
        entity_pair_relationships = {}
        for rel in relationships:
            source_id = rel["source_entity_id"]
            target_id = rel["target_entity_id"]
            pair_key = f"{source_id}_{target_id}"

            if pair_key not in entity_pair_relationships:
                entity_pair_relationships[pair_key] = []
            entity_pair_relationships[pair_key].append(rel)

        # Check for contradictions within each pair
        for pair_key, pair_relationships in entity_pair_relationships.items():
            if len(pair_relationships) > 1:
                contradictions = await self._detect_relationship_contradictions(
                    pair_relationships
                )
                conflicts.extend(contradictions)

        return conflicts

    async def _detect_relationship_contradictions(
        self, relationships: List[Dict]
    ) -> List[ConflictCreate]:
        """Detect contradictions within relationships between the same entity pair"""

        conflicts = []
        contradictory_types = {
            # Define contradictory relationship types
            "EMPLOYED_BY": ["UNEMPLOYED", "RETIRED_FROM"],
            "MARRIED_TO": ["DIVORCED_FROM", "SINGLE"],
            "OWNS": ["SOLD", "DOES_NOT_OWN"],
            "LOCATED_IN": ["NOT_LOCATED_IN", "MOVED_FROM"],
        }

        for i in range(len(relationships)):
            for j in range(i + 1, len(relationships)):
                rel1, rel2 = relationships[i], relationships[j]

                type1, type2 = rel1["relationship_type"], rel2["relationship_type"]

                # Check for direct contradictions
                is_contradictory = type1 in contradictory_types.get(
                    type2, []
                ) or type2 in contradictory_types.get(type1, [])

                if is_contradictory:
                    confidence = min(
                        rel1.get("confidence", 0.5), rel2.get("confidence", 0.5)
                    )

                    conflict = ConflictCreate(
                        conflict_type=ConflictType.CONTRADICTORY_RELATIONSHIP,
                        severity=ConflictSeverity.HIGH,
                        description=f"Contradictory relationships: {type1} vs {type2}",
                        confidence_score=confidence,
                        source_relationship_id=rel1["id"],
                        target_relationship_id=rel2["id"],
                        context_data={
                            "relationship1": rel1,
                            "relationship2": rel2,
                            "contradiction_type": "direct_contradiction",
                        },
                        detected_by="system",
                    )

                    conflicts.append(conflict)

        return conflicts

    async def detect_attribute_mismatches(
        self, entity_ids: Optional[List[str]] = None, batch_size: int = 100
    ) -> List[ConflictCreate]:
        """Detect attribute mismatches in similar entities"""

        conflicts = []

        # Get entities with similar text but different attributes
        duplicates = await self.detect_duplicate_entities(entity_ids, batch_size)

        for duplicate_conflict in duplicates:
            # For each potential duplicate, check attribute consistency
            if (
                duplicate_conflict.source_entity_id
                and duplicate_conflict.target_entity_id
            ):
                attribute_conflicts = await self._detect_attribute_inconsistencies(
                    duplicate_conflict.source_entity_id,
                    duplicate_conflict.target_entity_id,
                )
                conflicts.extend(attribute_conflicts)

        return conflicts

    async def detect_temporal_conflicts(
        self, batch_size: int = 100
    ) -> List[ConflictCreate]:
        """Detect temporal inconsistencies in relationships and events"""

        supabase = await get_supabase()
        conflicts = []

        # Get relationships with temporal information
        response = (
            await supabase.table("kg_relationships")
            .select(
                "id, relationship_type, source_entity_id, target_entity_id, properties"
            )
            .execute()
        )

        relationships = response.data

        # Group by entity to check temporal consistency
        entity_timelines = {}
        for rel in relationships:
            props = rel.get("properties", {})
            if "start_date" in props or "end_date" in props or "date" in props:
                source_id = rel["source_entity_id"]
                if source_id not in entity_timelines:
                    entity_timelines[source_id] = []
                entity_timelines[source_id].append(rel)

        # Check temporal consistency for each entity
        for entity_id, timeline in entity_timelines.items():
            temporal_conflicts = await self._detect_timeline_conflicts(timeline)
            conflicts.extend(temporal_conflicts)

        return conflicts

    async def detect_source_conflicts(
        self, batch_size: int = 100
    ) -> List[ConflictCreate]:
        """Detect conflicts between information from different sources"""

        supabase = await get_supabase()
        conflicts = []

        # Get entities grouped by source document
        response = (
            await supabase.table("kg_entities")
            .select(
                "id, entity_text, entity_type, source_document_id, properties, confidence"
            )
            .execute()
        )

        entities = response.data

        # Group entities by text and type but different sources
        entity_groups = {}
        for entity in entities:
            key = f"{entity['entity_text'].lower()}_{entity['entity_type']}"
            if key not in entity_groups:
                entity_groups[key] = []
            entity_groups[key].append(entity)

        # Check for conflicts between different sources
        for group in entity_groups.values():
            if len(group) > 1:
                source_conflicts = await self._detect_inter_source_conflicts(group)
                conflicts.extend(source_conflicts)

        return conflicts

    def _determine_severity(
        self, max_similarity: float, similarities: Dict[str, float]
    ) -> ConflictSeverity:
        """Determine conflict severity based on similarity scores"""

        if max_similarity >= 0.95:
            return ConflictSeverity.CRITICAL
        elif max_similarity >= 0.9:
            return ConflictSeverity.HIGH
        elif max_similarity >= 0.8:
            return ConflictSeverity.MEDIUM
        else:
            return ConflictSeverity.LOW

    def _calculate_property_similarity(self, props1: Dict, props2: Dict) -> float:
        """Calculate similarity between entity properties"""

        if not props1 and not props2:
            return 1.0

        if not props1 or not props2:
            return 0.0

        common_keys = set(props1.keys()) & set(props2.keys())
        if not common_keys:
            return 0.0

        similarities = []
        for key in common_keys:
            val1, val2 = str(props1[key]), str(props2[key])
            if val1 == val2:
                similarities.append(1.0)
            else:
                similarities.append(calculate_similarity(val1, val2, method="fuzzy"))

        return sum(similarities) / len(similarities) if similarities else 0.0

    async def _detect_attribute_inconsistencies(
        self, entity1_id: str, entity2_id: str
    ) -> None:
        """Detect specific attribute inconsistencies between two entities"""
        # Implementation for detailed attribute analysis
        pass

    async def _detect_timeline_conflicts(self, timeline: List[Dict]) -> None:
        """Detect temporal inconsistencies in entity timeline"""
        # Implementation for temporal conflict detection
        pass

    async def _detect_inter_source_conflicts(self, entities: List[Dict]) -> None:
        """Detect conflicts between entities from different sources"""
        # Implementation for source conflict detection
        pass
