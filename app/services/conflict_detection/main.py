import asyncio
import json
import logging
from typing import Dict, List, Optional

from app.core.supabase import get_supabase
from app.nlp.embeddings import get_text_embedding
from app.schemas.conflict_resolution import (ConflictCreate, ConflictSeverity,
                                             ConflictType)
from app.utils.similarity import calculate_similarity

logger = logging.getLogger(__name__)


class ConflictDetectionService:
    """Advanced conflict detection for knowledge graph entities and relationships"""

    def __init__(self):
        self.similarity_thresholds = {
            ConflictType.DUPLICATE_ENTITY: 0.75,
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
            self.detect_relationship_conflicts(
                batch_size=batch_size,
            ),
        ]

        conflict_results = await asyncio.gather(
            *detection_tasks, return_exceptions=True
        )

        for result in conflict_results:
            if isinstance(result, Exception):
                logger.error(f"Conflict detection failed: {result}")
            else:
                all_conflicts.extend(result)

        # Filter out conflicts that already exist in database
        filtered_conflicts = await self._filter_existing_conflicts(all_conflicts)

        return filtered_conflicts

    async def _filter_existing_conflicts(
        self, conflicts: List[ConflictCreate]
    ) -> List[ConflictCreate]:
        """Filter out conflicts that already exist in the database"""

        if not conflicts:
            return conflicts

        supabase = await get_supabase()
        filtered_conflicts = []

        # Get all existing conflicts in batch for efficiency
        existing_conflicts_response = (
            await supabase.table("conflicts")
            .select(
                "conflict_type, source_entity_id, target_entity_id, source_relationship_id, target_relationship_id"
            )
            .in_(
                "status",
                ["detected", "under_review", "resolved_auto", "resolved_manual"],
            )
            .execute()
        )

        existing_conflicts = existing_conflicts_response.data

        # Create lookup sets for different conflict types
        duplicate_entity_conflicts = set()
        relationship_conflicts = set()
        attribute_conflicts = set()

        for existing in existing_conflicts:
            conflict_type = existing["conflict_type"]

            if conflict_type == "duplicate_entity":
                # For duplicate entity conflicts, check both directions
                if existing["source_entity_id"] and existing["target_entity_id"]:
                    source_id = existing["source_entity_id"]
                    target_id = existing["target_entity_id"]
                    duplicate_entity_conflicts.add((source_id, target_id))
                    duplicate_entity_conflicts.add(
                        (target_id, source_id)
                    )  # Both directions

            elif conflict_type in ["contradictory_relationship", "temporal_conflict"]:
                if (
                    existing["source_relationship_id"]
                    and existing["target_relationship_id"]
                ):
                    rel1_id = existing["source_relationship_id"]
                    rel2_id = existing["target_relationship_id"]
                    relationship_conflicts.add((rel1_id, rel2_id))
                    relationship_conflicts.add((rel2_id, rel1_id))  # Both directions

            elif conflict_type in ["attribute_mismatch", "source_conflict"]:
                if existing["source_entity_id"] and existing["target_entity_id"]:
                    source_id = existing["source_entity_id"]
                    target_id = existing["target_entity_id"]
                    attribute_conflicts.add((conflict_type, source_id, target_id))
                    attribute_conflicts.add(
                        (conflict_type, target_id, source_id)
                    )  # Both directions

        # Filter new conflicts
        for conflict in conflicts:
            should_add = True

            if conflict.conflict_type == ConflictType.DUPLICATE_ENTITY:
                if (
                    conflict.source_entity_id
                    and conflict.target_entity_id
                    and (conflict.source_entity_id, conflict.target_entity_id)
                    in duplicate_entity_conflicts
                ):
                    should_add = False
                    logger.debug(
                        f"Skipping duplicate entity conflict: {conflict.source_entity_id} -> {conflict.target_entity_id}"
                    )

            elif conflict.conflict_type in [
                ConflictType.CONTRADICTORY_RELATIONSHIP,
                ConflictType.TEMPORAL_CONFLICT,
            ]:
                if (
                    conflict.source_relationship_id
                    and conflict.target_relationship_id
                    and (
                        conflict.source_relationship_id,
                        conflict.target_relationship_id,
                    )
                    in relationship_conflicts
                ):
                    should_add = False
                    logger.debug(
                        f"Skipping relationship conflict: {conflict.source_relationship_id} -> {conflict.target_relationship_id}"
                    )

            elif conflict.conflict_type in [
                ConflictType.ATTRIBUTE_MISMATCH,
                ConflictType.SOURCE_CONFLICT,
            ]:
                conflict_key = (
                    conflict.conflict_type.value,
                    conflict.source_entity_id,
                    conflict.target_entity_id,
                )
                if conflict_key in attribute_conflicts:
                    should_add = False
                    logger.debug(
                        f"Skipping attribute/source conflict: {conflict.conflict_type.value} - {conflict.source_entity_id} -> {conflict.target_entity_id}"
                    )

            if should_add:
                filtered_conflicts.append(conflict)

        logger.info(
            f"Filtered {len(conflicts) - len(filtered_conflicts)} existing conflicts. New conflicts: {len(filtered_conflicts)}"
        )
        return filtered_conflicts

    async def detect_relationship_conflicts(
        self,
        relationship_ids: Optional[List[str]] = None,
        batch_size: int = 100,
        conflict_types: Optional[List[ConflictType]] = None,
    ) -> List[ConflictCreate]:
        """Detect conflicts specifically related to relationships

        Args:
            relationship_ids: Specific relationship IDs to check. If None, checks all relationships
            batch_size: Size of batches for processing
            conflict_types: Types of conflicts to detect. If None, detects all relationship-related conflicts

        Returns:
            List of detected conflicts related to relationships
        """

        if conflict_types is None:
            # Default to all relationship-related conflict types
            conflict_types = [
                ConflictType.CONTRADICTORY_RELATIONSHIP,
                ConflictType.TEMPORAL_CONFLICT,
                ConflictType.ATTRIBUTE_MISMATCH,
                ConflictType.SOURCE_CONFLICT,
            ]

        all_conflicts = []

        # Run different relationship conflict detection methods based on specified types
        detection_tasks = []

        if ConflictType.CONTRADICTORY_RELATIONSHIP in conflict_types:
            detection_tasks.append(
                self._detect_contradictory_relationships_filtered(
                    relationship_ids, batch_size
                )
            )

        if ConflictType.TEMPORAL_CONFLICT in conflict_types:
            detection_tasks.append(
                self._detect_temporal_conflicts_filtered(relationship_ids, batch_size)
            )

        if ConflictType.ATTRIBUTE_MISMATCH in conflict_types:
            detection_tasks.append(
                self._detect_relationship_attribute_conflicts(
                    relationship_ids, batch_size
                )
            )

        if ConflictType.SOURCE_CONFLICT in conflict_types:
            detection_tasks.append(
                self._detect_relationship_source_conflicts(relationship_ids, batch_size)
            )

        # Execute all detection tasks
        if detection_tasks:
            conflict_results = await asyncio.gather(
                *detection_tasks, return_exceptions=True
            )

            for result in conflict_results:
                if isinstance(result, Exception):
                    logger.error(f"Relationship conflict detection failed: {result}")
                else:
                    all_conflicts.extend(result)

        # Filter out conflicts that already exist in database
        filtered_conflicts = await self._filter_existing_conflicts(all_conflicts)

        logger.info(f"Detected {len(filtered_conflicts)} new relationship conflicts")
        return filtered_conflicts

    async def _detect_contradictory_relationships_filtered(
        self, relationship_ids: Optional[List[str]], batch_size: int
    ) -> List[ConflictCreate]:
        """Detect contradictory relationships with optional filtering"""

        supabase = await get_supabase()
        conflicts = []

        if relationship_ids:
            # Process specific relationships in batches
            for i in range(0, len(relationship_ids), batch_size):
                batch_ids = [str(id) for id in relationship_ids[i : i + batch_size]]

                response = (
                    await supabase.table("kg_relationships")
                    .select(
                        "id, relationship_type, source_entity_id, target_entity_id, properties, confidence"
                    )
                    .in_("id", batch_ids)
                    .eq("is_active", True)
                    .execute()
                )

                relationships = response.data
                batch_conflicts = await self._process_contradictory_relationships_batch(
                    relationships
                )
                conflicts.extend(batch_conflicts)
        else:
            # Use existing detect_contradictory_relationships method
            conflicts = await self.detect_contradictory_relationships(batch_size)

        return conflicts

    async def _detect_temporal_conflicts_filtered(
        self, relationship_ids: Optional[List[str]], batch_size: int
    ) -> List[ConflictCreate]:
        """Detect temporal conflicts with optional filtering"""

        supabase = await get_supabase()
        conflicts = []

        if relationship_ids:
            # Process specific relationships in batches
            for i in range(0, len(relationship_ids), batch_size):
                batch_ids = [str(id) for id in relationship_ids[i : i + batch_size]]

                response = (
                    await supabase.table("kg_relationships")
                    .select(
                        "id, relationship_type, source_entity_id, target_entity_id, properties"
                    )
                    .in_("id", batch_ids)
                    .eq("is_active", True)
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
        else:
            # Use existing detect_temporal_conflicts method
            conflicts = await self.detect_temporal_conflicts(batch_size)

        return conflicts

    async def _detect_relationship_attribute_conflicts(
        self, relationship_ids: Optional[List[str]], batch_size: int
    ) -> List[ConflictCreate]:
        """Detect attribute conflicts in relationships"""

        supabase = await get_supabase()
        conflicts = []

        if relationship_ids:
            # Process specific relationships in batches
            for i in range(0, len(relationship_ids), batch_size):
                batch_ids = [str(id) for id in relationship_ids[i : i + batch_size]]

                response = (
                    await supabase.table("kg_relationships")
                    .select(
                        "id, relationship_type, source_entity_id, target_entity_id, properties, confidence"
                    )
                    .in_("id", batch_ids)
                    .eq("is_active", True)
                    .execute()
                )

                relationships = response.data

                # Group relationships by entity pairs and relationship type
                relationship_groups = {}
                for rel in relationships:
                    source_id = rel["source_entity_id"]
                    target_id = rel["target_entity_id"]
                    rel_type = rel["relationship_type"]

                    key = f"{source_id}_{target_id}_{rel_type}"
                    if key not in relationship_groups:
                        relationship_groups[key] = []
                    relationship_groups[key].append(rel)

                # Check for attribute conflicts within each group
                for group in relationship_groups.values():
                    if len(group) > 1:
                        group_conflicts = (
                            await self._detect_relationship_attribute_inconsistencies(
                                group
                            )
                        )
                        conflicts.extend(group_conflicts)

        return conflicts

    async def _detect_relationship_source_conflicts(
        self, relationship_ids: Optional[List[str]], batch_size: int
    ) -> List[ConflictCreate]:
        """Detect source conflicts in relationships"""

        supabase = await get_supabase()
        conflicts = []

        if relationship_ids:
            # Process specific relationships in batches
            for i in range(0, len(relationship_ids), batch_size):
                batch_ids = [str(id) for id in relationship_ids[i : i + batch_size]]

                response = (
                    await supabase.table("kg_relationships")
                    .select(
                        "id, relationship_type, source_entity_id, target_entity_id, properties, confidence, source_document_id"
                    )
                    .in_("id", batch_ids)
                    .eq("is_active", True)
                    .execute()
                )

                relationships = response.data

                # Group relationships by entity pairs and type but different sources
                relationship_groups = {}
                for rel in relationships:
                    source_id = rel["source_entity_id"]
                    target_id = rel["target_entity_id"]
                    rel_type = rel["relationship_type"]

                    key = f"{source_id}_{target_id}_{rel_type}"
                    if key not in relationship_groups:
                        relationship_groups[key] = []
                    relationship_groups[key].append(rel)

                # Check for source conflicts within each group
                for group in relationship_groups.values():
                    if len(group) > 1:
                        source_conflicts = (
                            await self._detect_inter_relationship_source_conflicts(
                                group
                            )
                        )
                        conflicts.extend(source_conflicts)

        return conflicts

    async def _process_contradictory_relationships_batch(
        self, relationships: List[Dict]
    ) -> List[ConflictCreate]:
        """Process a batch of relationships for contradiction detection"""

        conflicts = []

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

    async def _detect_relationship_attribute_inconsistencies(
        self, relationships: List[Dict]
    ) -> List[ConflictCreate]:
        """Detect attribute inconsistencies between similar relationships"""

        conflicts = []

        for i in range(len(relationships)):
            for j in range(i + 1, len(relationships)):
                rel1, rel2 = relationships[i], relationships[j]

                props1 = rel1.get("properties", {})
                props2 = rel2.get("properties", {})

                # Find conflicting attributes
                conflicting_attrs = {}
                for key in set(props1.keys()) & set(props2.keys()):
                    if props1[key] != props2[key]:
                        conflicting_attrs[key] = {
                            "relationship1_value": props1[key],
                            "relationship2_value": props2[key],
                        }

                if conflicting_attrs:
                    conflict = ConflictCreate(
                        conflict_type=ConflictType.ATTRIBUTE_MISMATCH,
                        severity=ConflictSeverity.MEDIUM,
                        description=f"Attribute mismatch in {rel1['relationship_type']} relationships",
                        confidence_score=0.7,
                        source_relationship_id=rel1["id"],
                        target_relationship_id=rel2["id"],
                        conflicting_attributes=conflicting_attrs,
                        context_data={
                            "relationship1": rel1,
                            "relationship2": rel2,
                            "mismatched_attributes": list(conflicting_attrs.keys()),
                        },
                        detected_by="system",
                    )
                    conflicts.append(conflict)

        return conflicts

    async def _detect_inter_relationship_source_conflicts(
        self, relationships: List[Dict]
    ) -> List[ConflictCreate]:
        """Detect conflicts between relationships from different sources"""

        conflicts = []

        # Group by source document
        by_source = {}
        for rel in relationships:
            source_id = rel.get("source_document_id", "unknown")
            if source_id not in by_source:
                by_source[source_id] = []
            by_source[source_id].append(rel)

        # Only check if we have relationships from different sources
        if len(by_source) > 1:
            source_list = list(by_source.keys())

            for i in range(len(source_list)):
                for j in range(i + 1, len(source_list)):
                    source1_rels = by_source[source_list[i]]
                    source2_rels = by_source[source_list[j]]

                    # Compare relationships between different sources
                    for rel1 in source1_rels:
                        for rel2 in source2_rels:
                            props1 = rel1.get("properties", {})
                            props2 = rel2.get("properties", {})

                            # Check for conflicting properties
                            has_conflicts = False
                            conflicting_attrs = {}

                            for key in set(props1.keys()) & set(props2.keys()):
                                if props1[key] != props2[key]:
                                    has_conflicts = True
                                    conflicting_attrs[key] = {
                                        "source1_value": props1[key],
                                        "source2_value": props2[key],
                                    }

                            if has_conflicts:
                                conflict = ConflictCreate(
                                    conflict_type=ConflictType.SOURCE_CONFLICT,
                                    severity=ConflictSeverity.MEDIUM,
                                    description=f"Source conflict in {rel1['relationship_type']} relationship",
                                    confidence_score=0.6,
                                    source_relationship_id=rel1["id"],
                                    target_relationship_id=rel2["id"],
                                    conflicting_attributes=conflicting_attrs,
                                    context_data={
                                        "source1_document": source_list[i],
                                        "source2_document": source_list[j],
                                        "relationship1": rel1,
                                        "relationship2": rel2,
                                    },
                                    detected_by="system",
                                )
                                conflicts.append(conflict)

        return conflicts

    async def detect_duplicate_entities(
        self, entity_ids: Optional[List[str]] = None, batch_size: int = 100
    ) -> List[ConflictCreate]:
        """Detect potential duplicate entities using multiple methods"""

        supabase = await get_supabase()
        conflicts = []

        # Get entities to check
        query = (
            supabase.table("kg_entities")
            .select("id, entity_text, entity_type, properties, embedding")
            .eq("is_active", True)
        )

        if entity_ids:
            # Check specific entities in batches
            for i in range(0, len(entity_ids), 50):
                batch_ids = [str(id) for id in entity_ids[i : i + 50]]
                batch_query = query.in_("id", batch_ids)
                response = await batch_query.execute()
                entities = response.data

                # Process this batch
                batch_conflicts = await self._process_entity_batch(entities)
                conflicts.extend(batch_conflicts)
        else:
            # Check all entities in batches
            offset = 0
            while True:
                batch_query = query.range(offset, offset + batch_size - 1)
                response = await batch_query.execute()
                entities = response.data

                if not entities:
                    break

                # Process this batch
                batch_conflicts = await self._process_entity_batch(entities)
                conflicts.extend(batch_conflicts)

                offset += batch_size

                # If we got fewer than batch_size, we're done
                if len(entities) < batch_size:
                    break

        return conflicts

    async def _process_entity_batch(self, entities: List[Dict]) -> List[ConflictCreate]:
        """Process a batch of entities for duplicate detection"""

        conflicts = []

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
                avg_similarity = sum(similarities.values()) / len(similarities)
                if (
                    avg_similarity
                    >= self.similarity_thresholds[ConflictType.DUPLICATE_ENTITY]
                ):

                    severity = self._determine_severity(avg_similarity, similarities)

                    # convert similarities from float to string
                    similarities = {k: str(v) for k, v in similarities.items()}

                    conflict = ConflictCreate(
                        conflict_type=ConflictType.DUPLICATE_ENTITY,
                        severity=severity,
                        description=f"Potential duplicate entities detected: '{entity1['entity_text']}' and '{entity2['entity_text']}'",
                        confidence_score=avg_similarity,
                        source_entity_id=entity1["id"],
                        target_entity_id=entity2["id"],
                        conflicting_attributes={
                            "text_similarity": similarities.get("text", "0"),
                            "semantic_similarity": similarities.get("semantic", "0"),
                            "attribute_similarity": similarities.get("attributes", "0"),
                            "abbreviated_similarity": similarities.get(
                                "abbreviated", "0"
                            ),
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
        abbreviated_text1 = entity1.get("abbreviated_text", "")
        abbreviated_text2 = entity2.get("abbreviated_text", "")
        # check if text1 is abbreviate of text2 or vice versa

        if (abbreviated_text1 and abbreviated_text1 == text2) or (
            abbreviated_text2 and abbreviated_text2 == text1
        ):
            similarities["abbreviated"] = 1.0
        else:
            similarities["abbreviated"] = calculate_similarity(
                abbreviated_text1, abbreviated_text2, method="fuzzy"
            )

        similarities["exact"] = 1.0 if text1.lower() == text2.lower() else 0.0
        similarities["text"] = calculate_similarity(text1, text2, method="fuzzy")

        # Semantic similarity using embeddings
        if entity1.get("embedding") and entity2.get("embedding"):
            similarities["semantic"] = calculate_similarity(
                json.loads(entity1["embedding"]),
                json.loads(entity2["embedding"]),
                method="cosine",
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

        offset = 0
        while True:
            # Get relationships with their entities in batches
            response = (
                await supabase.table("kg_relationships")
                .select(
                    "id, relationship_type, source_entity_id, target_entity_id, properties, confidence"
                )
                .eq("is_active", True)
                .range(offset, offset + batch_size - 1)
                .execute()
            )

            relationships = response.data

            if not relationships:
                break

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

            offset += batch_size

            # If we got fewer than batch_size, we're done
            if len(relationships) < batch_size:
                break

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
        self,
        batch_size: int = 100,
        entity_ids: Optional[List[str]] = None,
        time_window_days: Optional[int] = None,
    ) -> List[ConflictCreate]:
        """Detect temporal inconsistencies in relationships and events

        Args:
            batch_size: Size of batches for processing relationships
            entity_ids: Optional list of entity IDs to check. If None, checks all entities
            time_window_days: Optional time window in days. If provided, only checks
                             relationships within this many days from today

        Returns:
            List of detected temporal conflicts
        """

        supabase = await get_supabase()
        conflicts = []

        # Build base query
        query = (
            supabase.table("kg_relationships")
            .select(
                "id, relationship_type, source_entity_id, target_entity_id, properties"
            )
            .eq("is_active", True)
        )

        # Apply entity_ids filter if provided
        if entity_ids:
            # Convert to strings to ensure consistency
            entity_ids_str = [str(eid) for eid in entity_ids]
            # We want relationships where either source or target entity is in our list
            # Note: Supabase doesn't support OR with different columns directly,
            # so we'll filter after fetching the data
            pass  # We'll handle this in the processing logic

        # Apply time window filter if provided
        if time_window_days:
            from datetime import datetime, timedelta

            cutoff_date = datetime.now() - timedelta(days=time_window_days)
            cutoff_str = cutoff_date.isoformat()

            # Note: This is a simplified filter. In practice, you might need more complex
            # JSON querying depending on how dates are stored in properties
            # For now, we'll filter after fetching the data

        if entity_ids:
            # Process specific entities in batches
            entity_ids_str = [str(eid) for eid in entity_ids]

            # Split entity_ids into chunks for efficient querying
            for i in range(0, len(entity_ids_str), 50):  # Process 50 entities at a time
                batch_entity_ids = entity_ids_str[i : i + 50]

                # Get relationships where source_entity_id is in our list
                source_response = await query.in_(
                    "source_entity_id", batch_entity_ids
                ).execute()
                source_relationships = source_response.data

                # Get relationships where target_entity_id is in our list
                target_response = await query.in_(
                    "target_entity_id", batch_entity_ids
                ).execute()
                target_relationships = target_response.data

                # Combine and deduplicate
                all_relationships = source_relationships + target_relationships
                seen_ids = set()
                unique_relationships = []
                for rel in all_relationships:
                    if rel["id"] not in seen_ids:
                        seen_ids.add(rel["id"])
                        unique_relationships.append(rel)

                # Filter by time window if specified
                if time_window_days:
                    unique_relationships = self._filter_by_time_window(
                        unique_relationships, time_window_days
                    )

                # Process this batch
                batch_conflicts = await self._process_temporal_relationships_batch(
                    unique_relationships, entity_ids_str
                )
                conflicts.extend(batch_conflicts)
        else:
            # Process all relationships in batches
            offset = 0
            while True:
                # Get relationships with temporal information
                response = await query.range(offset, offset + batch_size - 1).execute()
                relationships = response.data

                if not relationships:
                    break

                # Filter by time window if specified
                if time_window_days:
                    relationships = self._filter_by_time_window(
                        relationships, time_window_days
                    )

                # Process this batch
                batch_conflicts = await self._process_temporal_relationships_batch(
                    relationships
                )
                conflicts.extend(batch_conflicts)

                offset += batch_size

                # If we got fewer than batch_size, we're done
                if len(relationships) < batch_size:
                    break

        return conflicts

    def _filter_by_time_window(
        self, relationships: List[Dict], time_window_days: int
    ) -> List[Dict]:
        """Filter relationships by time window"""

        from datetime import datetime, timedelta

        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        filtered_relationships = []

        for rel in relationships:
            props = rel.get("properties", {})

            # Check various date fields
            date_fields = ["start_date", "end_date", "date", "created_at", "updated_at"]
            has_recent_date = False

            for field in date_fields:
                if field in props:
                    try:
                        date_val = props[field]
                        # Handle various date formats
                        if isinstance(date_val, str):
                            # Remove timezone info for parsing
                            date_str = date_val.replace("Z", "+00:00")
                            parsed_date = datetime.fromisoformat(date_str)
                        else:
                            parsed_date = datetime.fromisoformat(str(date_val))

                        # Check if date is within our time window
                        if parsed_date >= cutoff_date:
                            has_recent_date = True
                            break

                    except (ValueError, TypeError) as e:
                        logger.debug(f"Failed to parse date {date_val}: {e}")
                        continue

            # Include relationships with recent dates or no dates (to be safe)
            if has_recent_date or not any(field in props for field in date_fields):
                filtered_relationships.append(rel)

        return filtered_relationships

    async def _process_temporal_relationships_batch(
        self, relationships: List[Dict], target_entity_ids: Optional[List[str]] = None
    ) -> List[ConflictCreate]:
        """Process a batch of relationships for temporal conflict detection"""

        conflicts = []

        # Group by entity to check temporal consistency
        entity_timelines = {}
        for rel in relationships:
            props = rel.get("properties", {})
            if "start_date" in props or "end_date" in props or "date" in props:
                source_id = rel["source_entity_id"]
                target_id = rel["target_entity_id"]

                # If we're filtering by specific entities, only include relevant ones
                if target_entity_ids:
                    if (
                        source_id not in target_entity_ids
                        and target_id not in target_entity_ids
                    ):
                        continue

                # Add to source entity timeline
                if source_id not in entity_timelines:
                    entity_timelines[source_id] = []
                entity_timelines[source_id].append(rel)

                # Add to target entity timeline if different from source
                if target_id != source_id:
                    if target_id not in entity_timelines:
                        entity_timelines[target_id] = []
                    entity_timelines[target_id].append(rel)

        # Check temporal consistency for each entity
        for entity_id, timeline in entity_timelines.items():
            if (
                len(timeline) > 1
            ):  # Only check if entity has multiple temporal relationships
                temporal_conflicts = await self._detect_timeline_conflicts(timeline)
                conflicts.extend(temporal_conflicts)

        return conflicts

    async def detect_source_conflicts(
        self, batch_size: int = 100
    ) -> List[ConflictCreate]:
        """Detect conflicts between information from different sources"""

        supabase = await get_supabase()
        conflicts = []

        offset = 0
        while True:
            # Get entities grouped by source document
            response = (
                await supabase.table("kg_entities")
                .select(
                    "id, entity_text, entity_type, source_document_id, properties, confidence"
                )
                .eq("is_active", True)
                .range(offset, offset + batch_size - 1)
                .execute()
            )

            entities = response.data

            if not entities:
                break

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

            offset += batch_size

            # If we got fewer than batch_size, we're done
            if len(entities) < batch_size:
                break

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
    ) -> List[ConflictCreate]:
        """Detect specific attribute inconsistencies between two entities"""

        supabase = await get_supabase()
        conflicts = []

        # Get both entities
        entity1_response = (
            await supabase.table("kg_entities")
            .select("*")
            .eq("id", entity1_id)
            .maybe_single()
            .execute()
        )

        if not entity1_response:
            return conflicts

        entity2_response = (
            await supabase.table("kg_entities")
            .select("*")
            .eq("id", entity2_id)
            .maybe_single()
            .execute()
        )

        if not entity2_response:
            return conflicts

        entity1 = entity1_response.data
        entity2 = entity2_response.data

        props1 = entity1.get("properties", {})
        props2 = entity2.get("properties", {})

        # Find conflicting attributes
        conflicting_attrs = {}
        for key in set(props1.keys()) & set(props2.keys()):
            if props1[key] != props2[key]:
                conflicting_attrs[key] = {
                    "entity1_value": props1[key],
                    "entity2_value": props2[key],
                }

        if conflicting_attrs:
            conflict = ConflictCreate(
                conflict_type=ConflictType.ATTRIBUTE_MISMATCH,
                severity=ConflictSeverity.MEDIUM,
                description=f"Attribute mismatch between '{entity1['entity_text']}' and '{entity2['entity_text']}'",
                confidence_score=0.8,
                source_entity_id=entity1_id,
                target_entity_id=entity2_id,
                conflicting_attributes=conflicting_attrs,
                context_data={
                    "entity1": entity1,
                    "entity2": entity2,
                    "mismatched_attributes": list(conflicting_attrs.keys()),
                },
                detected_by="system",
            )
            conflicts.append(conflict)

        return conflicts

    async def _detect_timeline_conflicts(
        self, timeline: List[Dict]
    ) -> List[ConflictCreate]:
        """Detect temporal inconsistencies in entity timeline"""

        conflicts = []

        # Sort by date fields
        dated_relationships = []
        for rel in timeline:
            props = rel.get("properties", {})
            date_val = None

            if "start_date" in props:
                date_val = props["start_date"]
            elif "date" in props:
                date_val = props["date"]
            elif "end_date" in props:
                date_val = props["end_date"]

            if date_val:
                try:
                    from datetime import datetime

                    parsed_date = datetime.fromisoformat(
                        str(date_val).replace("Z", "+00:00")
                    )
                    dated_relationships.append((rel, parsed_date))
                except:
                    continue

        # Check for temporal inconsistencies
        dated_relationships.sort(key=lambda x: x[1])

        for i in range(len(dated_relationships) - 1):
            rel1, date1 = dated_relationships[i]
            rel2, date2 = dated_relationships[i + 1]

            # Check for logical inconsistencies
            if self._are_temporally_conflicting(rel1, rel2, date1, date2):
                conflict = ConflictCreate(
                    conflict_type=ConflictType.TEMPORAL_CONFLICT,
                    severity=ConflictSeverity.HIGH,
                    description=f"Temporal conflict between {rel1['relationship_type']} and {rel2['relationship_type']}",
                    confidence_score=0.7,
                    source_relationship_id=rel1["id"],
                    target_relationship_id=rel2["id"],
                    context_data={
                        "relationship1": rel1,
                        "relationship2": rel2,
                        "date1": date1.isoformat(),
                        "date2": date2.isoformat(),
                    },
                    detected_by="system",
                )
                conflicts.append(conflict)

        return conflicts

    def _are_temporally_conflicting(self, rel1: Dict, rel2: Dict, date1, date2) -> bool:
        """Check if two relationships are temporally conflicting"""

        type1 = rel1["relationship_type"]
        type2 = rel2["relationship_type"]

        # Define conflicting temporal patterns
        temporal_conflicts = {
            "BORN": ["DIED"],  # Can't die before being born
            "STARTED_WORK": ["RETIRED"],  # Can't retire before starting work
            "MARRIED": ["DIVORCED"],  # Must marry before divorce
        }

        # Check if the later relationship conflicts with earlier one
        if type1 in temporal_conflicts and type2 in temporal_conflicts[type1]:
            return date2 <= date1  # Conflict if later event happens before earlier

        return False

    async def _detect_inter_source_conflicts(
        self, entities: List[Dict]
    ) -> List[ConflictCreate]:
        """Detect conflicts between entities from different sources"""

        conflicts = []

        # Group by source document
        by_source = {}
        for entity in entities:
            source_id = entity.get("source_document_id", "unknown")
            if source_id not in by_source:
                by_source[source_id] = []
            by_source[source_id].append(entity)

        # Only check if we have entities from different sources
        if len(by_source) > 1:
            source_list = list(by_source.keys())

            for i in range(len(source_list)):
                for j in range(i + 1, len(source_list)):
                    source1_entities = by_source[source_list[i]]
                    source2_entities = by_source[source_list[j]]

                    # Compare entities between different sources
                    for entity1 in source1_entities:
                        for entity2 in source2_entities:
                            # Check if they refer to the same thing but have different info
                            text_similarity = calculate_similarity(
                                entity1["entity_text"],
                                entity2["entity_text"],
                                method="fuzzy",
                            )

                            if (
                                text_similarity > 0.8
                            ):  # Similar entities from different sources
                                props1 = entity1.get("properties", {})
                                props2 = entity2.get("properties", {})

                                # Check for conflicting properties
                                has_conflicts = False
                                conflicting_attrs = {}

                                for key in set(props1.keys()) & set(props2.keys()):
                                    if props1[key] != props2[key]:
                                        has_conflicts = True
                                        conflicting_attrs[key] = {
                                            "source1_value": props1[key],
                                            "source2_value": props2[key],
                                        }

                                if has_conflicts:
                                    conflict = ConflictCreate(
                                        conflict_type=ConflictType.SOURCE_CONFLICT,
                                        severity=ConflictSeverity.MEDIUM,
                                        description=f"Source conflict for '{entity1['entity_text']}'",
                                        confidence_score=text_similarity,
                                        source_entity_id=entity1["id"],
                                        target_entity_id=entity2["id"],
                                        conflicting_attributes=conflicting_attrs,
                                        context_data={
                                            "source1_document": source_list[i],
                                            "source2_document": source_list[j],
                                            "text_similarity": text_similarity,
                                            "entity1": entity1,
                                            "entity2": entity2,
                                        },
                                        detected_by="system",
                                    )
                                    conflicts.append(conflict)

        return conflicts
