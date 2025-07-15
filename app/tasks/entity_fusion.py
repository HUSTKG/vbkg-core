from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.supabase import get_supabase
from app.tasks.executors import StepLogger


class EntityFusionTask:
    """
    Task for entity fusion with Vietnamese support and conflict resolution
    """

    def __init__(self, logger: Optional[StepLogger] = None):
        self.logger = logger

    async def fuse_entities(
        self,
        resolved_entities: List[Dict[str, Any]],
        entity_clusters: List[Dict[str, Any]],
        fusion_strategy: str = "most_recent",
        preserve_provenance: bool = True,
        conflict_resolution: str = "highest_confidence",
        auto_save: bool = True,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fuse entities based on clusters and strategy

        Args:
            resolved_entities: List of resolved entities
            entity_clusters: List of entity clusters
            fusion_strategy: Strategy for fusion (most_recent, highest_confidence, merge_all)
            preserve_provenance: Whether to preserve provenance information
            conflict_resolution: How to resolve conflicts (highest_confidence, most_recent, merge_all)
            auto_save: Whether to save results automatically
            user_id: User performing fusion

        Returns:
            Dictionary containing fusion results
        """
        try:
            # Perform entity fusion
            fused_entities = await self._fuse_entities_by_clusters(
                resolved_entities,
                entity_clusters,
                fusion_strategy,
                preserve_provenance,
                conflict_resolution,
            )

            # Auto-save results if requested
            saved_data = None
            if auto_save:
                saved_data = await self._save_fusion_results(fused_entities, user_id)

            result = {
                "fused_entities": fused_entities,
                "fusion_stats": {
                    "input_entities": len(resolved_entities),
                    "input_clusters": len(entity_clusters),
                    "fused_entities": len(fused_entities),
                    "fusion_strategy": fusion_strategy,
                    "conflict_resolution": conflict_resolution,
                },
                "saved_data": saved_data,
                "success": True,
            }

            await self.logger.info(
                f"Entity fusion completed: {len(resolved_entities)} -> {len(fused_entities)} entities"
            )
            return result

        except Exception as e:
            await self.logger.error(f"Error in entity fusion: {e}")
            return {
                "fused_entities": [],
                "error": str(e),
                "success": False,
            }

    async def _fuse_entities_by_clusters(
        self,
        resolved_entities: List[Dict[str, Any]],
        entity_clusters: List[Dict[str, Any]],
        fusion_strategy: str,
        preserve_provenance: bool,
        conflict_resolution: str,
    ) -> List[Dict[str, Any]]:
        """Fuse entities based on clusters and strategy"""
        fused_entities = []

        # Process clustered entities
        for cluster in entity_clusters:
            cluster_entities = cluster.get("cluster_entities", [])
            if not cluster_entities:
                continue

            # Fuse entities in the cluster
            fused_entity = await self._fuse_entity_cluster(
                cluster_entities,
                fusion_strategy,
                preserve_provenance,
                conflict_resolution,
            )

            # Add cluster metadata
            fused_entity["is_fused"] = True
            fused_entity["source_entities_count"] = len(cluster_entities)
            fused_entity["cluster_id"] = cluster.get("cluster_id")
            fused_entity["fusion_timestamp"] = datetime.now(timezone.utc).isoformat()

            fused_entities.append(fused_entity)

        # Add standalone entities (not in clusters)
        for entity in resolved_entities:
            if entity.get("cluster_id") is None:
                entity_copy = entity.copy()
                entity_copy["is_fused"] = False
                entity_copy["source_entities_count"] = 1
                entity_copy["fusion_timestamp"] = datetime.now(timezone.utc).isoformat()
                fused_entities.append(entity_copy)

        return fused_entities

    async def _fuse_entity_cluster(
        self,
        cluster_entities: List[Dict[str, Any]],
        fusion_strategy: str,
        preserve_provenance: bool,
        conflict_resolution: str,
    ) -> Dict[str, Any]:
        """Fuse a cluster of entities into a single entity with Vietnamese-aware processing"""
        if not cluster_entities:
            return {}

        if len(cluster_entities) == 1:
            return cluster_entities[0].copy()

        # Start with the base entity based on strategy
        if fusion_strategy == "highest_confidence":
            base_entity = max(cluster_entities, key=lambda e: e.get("confidence", 0))
        elif fusion_strategy == "most_recent":
            base_entity = max(
                cluster_entities,
                key=lambda e: self._parse_timestamp(
                    e.get("timestamp", e.get("created_at", "1970-01-01"))
                ),
            )
        else:
            base_entity = cluster_entities[0]

        fused_entity = base_entity.copy()

        # Merge properties from all entities with Vietnamese-aware handling
        all_properties = {}
        provenance_info = []

        for entity in cluster_entities:
            # Collect properties
            entity_properties = entity.get("properties", {})
            for key, value in entity_properties.items():
                if key not in all_properties:
                    all_properties[key] = []
                all_properties[key].append(
                    {
                        "value": value,
                        "source_entity": entity.get("id"),
                        "confidence": entity.get("confidence", 0),
                        "timestamp": entity.get("timestamp", entity.get("created_at")),
                        "extraction_method": entity.get("extraction_method"),
                    }
                )

            # Collect provenance
            if preserve_provenance:
                provenance_info.append(
                    {
                        "entity_id": entity.get("id"),
                        "text": entity.get("text", entity.get("entity_text", "")),
                        "confidence": entity.get("confidence", 0),
                        "extraction_method": entity.get("extraction_method"),
                        "timestamp": entity.get("timestamp", entity.get("created_at")),
                        "provenance": entity.get("provenance", {}),
                    }
                )

        # Resolve conflicts in properties using Vietnamese-aware methods
        resolved_properties = {}
        for key, value_list in all_properties.items():
            if len(value_list) == 1:
                resolved_properties[key] = value_list[0]["value"]
            else:
                # Apply conflict resolution strategy
                resolved_value = self._resolve_property_conflict(
                    key, value_list, conflict_resolution
                )
                resolved_properties[key] = resolved_value

        # Update fused entity
        fused_entity["properties"] = resolved_properties

        if preserve_provenance:
            fused_entity["fusion_provenance"] = provenance_info

        # Calculate combined confidence with Vietnamese text consideration
        confidences = [e.get("confidence", 0) for e in cluster_entities]
        fused_entity["confidence"] = sum(confidences) / len(confidences)

        # Merge Vietnamese-specific fields
        fused_entity = self._merge_vietnamese_fields(
            fused_entity, cluster_entities, conflict_resolution
        )

        return fused_entity

    def _resolve_property_conflict(
        self,
        property_key: str,
        value_list: List[Dict[str, Any]],
        conflict_resolution: str,
    ) -> Any:
        """Resolve conflicts in property values with Vietnamese-aware handling"""
        if conflict_resolution == "highest_confidence":
            best_value = max(value_list, key=lambda v: v.get("confidence", 0))
            return best_value["value"]
        elif conflict_resolution == "most_recent":
            best_value = max(
                value_list,
                key=lambda v: self._parse_timestamp(v.get("timestamp", "1970-01-01")),
            )
            return best_value["value"]
        elif conflict_resolution == "merge_all":
            # Special handling for Vietnamese text fields
            if property_key in ["entity_text", "text", "name"]:
                return self._merge_vietnamese_text_values(
                    [v["value"] for v in value_list]
                )
            else:
                return [v["value"] for v in value_list]
        else:
            # Default to first value
            return value_list[0]["value"]

    def _merge_vietnamese_text_values(self, text_values: List[str]) -> str:
        """Merge Vietnamese text values intelligently"""
        if not text_values:
            return ""

        # Remove duplicates while preserving order
        unique_values = []
        seen = set()

        for value in text_values:
            normalized = self._normalize_vietnamese_text(str(value))
            if normalized not in seen:
                seen.add(normalized)
                unique_values.append(str(value))

        if len(unique_values) == 1:
            return unique_values[0]

        # If multiple unique values, choose the longest (most descriptive)
        return max(unique_values, key=len)

    def _normalize_vietnamese_text(self, text: str) -> str:
        """Normalize Vietnamese text for comparison"""
        import re

        text = text.lower().strip()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common Vietnamese prefixes/suffixes
        text = re.sub(r"^(ông|bà|anh|chị|em|cô|chú|bác)\s+", "", text)
        text = re.sub(r"\s+(ạ|à|ơi|nhé)$", "", text)

        return text

    def _merge_vietnamese_fields(
        self,
        fused_entity: Dict[str, Any],
        cluster_entities: List[Dict[str, Any]],
        conflict_resolution: str,
    ) -> Dict[str, Any]:
        """Merge Vietnamese-specific fields"""
        # Merge entity text with Vietnamese-aware logic
        entity_texts = []
        for entity in cluster_entities:
            text = entity.get("text", entity.get("entity_text", ""))
            if text:
                entity_texts.append(text)

        if entity_texts:
            if conflict_resolution == "merge_all":
                fused_entity["text"] = self._merge_vietnamese_text_values(entity_texts)
            else:
                # Use the text from the base entity selected by strategy
                fused_entity["text"] = entity_texts[0]

        # Merge Vietnamese entity types
        entity_types = list(
            set(
                [
                    e.get("entity_type", "")
                    for e in cluster_entities
                    if e.get("entity_type")
                ]
            )
        )
        if len(entity_types) == 1:
            fused_entity["entity_type"] = entity_types[0]
        elif len(entity_types) > 1:
            # Prefer more specific Vietnamese banking types
            preferred_types = ["Person", "Bank", "Account", "Money", "Transaction"]
            for preferred in preferred_types:
                if preferred in entity_types:
                    fused_entity["entity_type"] = preferred
                    break
            else:
                fused_entity["entity_type"] = entity_types[0]

        return fused_entity

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime object"""
        try:
            if isinstance(timestamp_str, str):
                # Handle various timestamp formats
                timestamp_str = timestamp_str.replace("Z", "+00:00")
                return datetime.fromisoformat(timestamp_str)
            return datetime.fromisoformat("1970-01-01T00:00:00+00:00")
        except:
            return datetime.fromisoformat("1970-01-01T00:00:00+00:00")

    async def _save_fusion_results(
        self,
        fused_entities: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save fusion results to database"""
        try:
            supabase = await get_supabase()

            # Save fused entities
            entity_ids = []
            for entity in fused_entities:
                if entity.get("is_fused", False):
                    # Create new fused entity record
                    entity_data = {
                        "entity_text": entity.get(
                            "text", entity.get("entity_text", "")
                        ),
                        "entity_type": entity.get("entity_type", ""),
                        "ontology_class_id": entity.get("ontology_class_id"),
                        "confidence": entity.get("confidence", 0),
                        "extraction_confidence": entity.get("confidence", 0),
                        "is_verified": False,
                        "validation_status": "fused",
                        "created_by": user_id,
                        "properties": {
                            **entity.get("properties", {}),
                            "is_fused": True,
                            "source_entities_count": entity.get(
                                "source_entities_count", 1
                            ),
                            "cluster_id": entity.get("cluster_id"),
                            "fusion_timestamp": entity.get("fusion_timestamp"),
                            "fusion_provenance": entity.get("fusion_provenance", []),
                        },
                    }

                    response = (
                        await supabase.from_("kg_entities")
                        .insert(entity_data)
                        .execute()
                    )
                    if response.data:
                        entity_ids.append(response.data[0]["id"])

            return {
                "fused_entities_saved": len(entity_ids),
                "entity_ids": entity_ids,
            }

        except Exception as e:
            await self.logger.error(f"Error saving fusion results: {e}")
            return {"error": str(e)}

    async def detect_fusion_conflicts(
        self,
        cluster_entities: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Detect and analyze conflicts in entity clusters for Vietnamese entities"""
        conflicts = {
            "property_conflicts": [],
            "text_conflicts": [],
            "type_conflicts": [],
            "confidence_conflicts": [],
            "total_conflicts": 0,
        }

        if len(cluster_entities) < 2:
            return conflicts

        # Analyze property conflicts
        all_properties = {}
        for entity in cluster_entities:
            for key, value in entity.get("properties", {}).items():
                if key not in all_properties:
                    all_properties[key] = []
                all_properties[key].append(
                    {
                        "value": value,
                        "entity_id": entity.get("id"),
                        "confidence": entity.get("confidence", 0),
                    }
                )

        for prop_key, prop_values in all_properties.items():
            unique_values = set(str(v["value"]) for v in prop_values)
            if len(unique_values) > 1:
                conflicts["property_conflicts"].append(
                    {
                        "property": prop_key,
                        "values": list(unique_values),
                        "conflict_count": len(unique_values),
                    }
                )

        # Analyze text conflicts (Vietnamese-aware)
        entity_texts = []
        for entity in cluster_entities:
            text = entity.get("text", entity.get("entity_text", ""))
            if text:
                entity_texts.append(
                    {
                        "text": text,
                        "normalized": self._normalize_vietnamese_text(text),
                        "entity_id": entity.get("id"),
                        "confidence": entity.get("confidence", 0),
                    }
                )

        normalized_texts = set(t["normalized"] for t in entity_texts)
        if len(normalized_texts) > 1:
            conflicts["text_conflicts"] = entity_texts

        # Analyze type conflicts
        entity_types = list(
            set(
                [
                    e.get("entity_type", "")
                    for e in cluster_entities
                    if e.get("entity_type")
                ]
            )
        )
        if len(entity_types) > 1:
            conflicts["type_conflicts"] = entity_types

        # Analyze confidence conflicts
        confidences = [e.get("confidence", 0) for e in cluster_entities]
        confidence_variance = max(confidences) - min(confidences)
        if confidence_variance > 0.3:  # Significant confidence difference
            conflicts["confidence_conflicts"] = {
                "min_confidence": min(confidences),
                "max_confidence": max(confidences),
                "variance": confidence_variance,
            }

        conflicts["total_conflicts"] = (
            len(conflicts["property_conflicts"])
            + (1 if conflicts["text_conflicts"] else 0)
            + (1 if len(conflicts["type_conflicts"]) > 1 else 0)
            + (1 if conflicts["confidence_conflicts"] else 0)
        )

        return conflicts

    async def get_fusion_statistics(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get statistics about entity fusion"""
        try:
            supabase = await get_supabase()

            # Get fusion statistics
            entity_response = await supabase.from_("kg_entities").select("*").execute()
            entities = entity_response.data

            total_entities = len(entities)
            fused_entities = len(
                [e for e in entities if e.get("properties", {}).get("is_fused", False)]
            )

            # Calculate fusion ratios
            fusion_ratio = (
                (fused_entities / total_entities * 100) if total_entities > 0 else 0
            )

            # Get average source entities count for fused entities
            fused_entity_data = [
                e for e in entities if e.get("properties", {}).get("is_fused", False)
            ]
            avg_source_count = 0
            if fused_entity_data:
                source_counts = [
                    e.get("properties", {}).get("source_entities_count", 1)
                    for e in fused_entity_data
                ]
                avg_source_count = sum(source_counts) / len(source_counts)

            return {
                "total_entities": total_entities,
                "fused_entities": fused_entities,
                "unfused_entities": total_entities - fused_entities,
                "fusion_ratio": fusion_ratio,
                "avg_source_entities_per_fusion": avg_source_count,
                "domain": domain,
            }

        except Exception as e:
            await self.logger.error(f"Error getting fusion statistics: {e}")
            return {}
