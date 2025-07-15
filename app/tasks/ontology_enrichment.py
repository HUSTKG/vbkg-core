import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.llm_client import get_llm_client
from app.core.supabase import get_supabase
from app.services.ontology import OntologyService
from app.tasks.executors import StepLogger


class OntologyEnrichmentTask:
    """Task for enriching entities and relationships with ontology mapping using AI suggestions"""

    def __init__(self, logger: StepLogger):
        self.logger = logger
        self.ontology_service = OntologyService()
        self.llm_client = get_llm_client()

    async def enrich_with_ontology_mapping(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        domain: Optional[str] = None,
        user_id: Optional[str] = None,
        auto_apply_suggestions: bool = False,
        confidence_threshold: float = 0.8,
        use_existing_mappings: bool = True,
    ) -> Dict[str, Any]:
        """
        Enrich entities and relationships with ontology mapping suggestions.
        """
        start_time = time.time()

        try:
            await self.logger.info(
                f"Starting ontology enrichment for {len(entities)} entities and {len(relationships)} relationships"
            )

            # Get ontology context
            ontology_context = await self._get_ontology_context(domain)

            # Enrich entities
            enriched_entities = await self._enrich_entities(
                entities, ontology_context, auto_apply_suggestions, confidence_threshold
            )

            # Enrich relationships
            enriched_relationships = await self._enrich_relationships(
                relationships,
                ontology_context,
                auto_apply_suggestions,
                confidence_threshold,
            )

            # Save mappings to database
            saved_mappings = await self._save_mappings_to_db(
                enriched_entities, enriched_relationships, domain, user_id
            )

            # Calculate statistics
            statistics = self._calculate_statistics(
                entities,
                relationships,
                enriched_entities,
                enriched_relationships,
                saved_mappings,
                start_time,
            )

            return {
                "enriched_entities": enriched_entities,
                "enriched_relationships": enriched_relationships,
                "saved_mappings": saved_mappings,
                "statistics": statistics,
                "success": True,
            }

        except Exception as e:
            error_message = str(e)
            await self.logger.error(f"Error in ontology enrichment: {error_message}")

            return {
                "enriched_entities": entities,
                "enriched_relationships": relationships,
                "saved_mappings": {
                    "entity_mappings_saved": 0,
                    "relationship_mappings_saved": 0,
                },
                "error": error_message,
                "success": False,
                "statistics": self._get_error_statistics(
                    entities, relationships, start_time
                ),
            }

    async def _get_ontology_context(self, domain: Optional[str]) -> Dict[str, Any]:
        """Get ontology context for mapping"""
        try:
            # Get classes and properties from ontology service
            classes_context = (
                await self.ontology_service.get_ontology_context_with_class_properties(
                    domain
                )
            )
            properties_context = (
                await self.ontology_service.get_object_properties_context(domain)
            )

            return {
                "classes": classes_context.get("classes", {}),
                "object_properties": properties_context.get("object_properties", {}),
                "class_datatype_properties": classes_context.get(
                    "class_datatype_properties", {}
                ),
            }
        except Exception as e:
            await self.logger.error(f"Error getting ontology context: {e}")
            return {
                "classes": {},
                "object_properties": {},
                "class_datatype_properties": {},
            }

    async def _enrich_entities(
        self,
        entities: List[Dict[str, Any]],
        ontology_context: Dict[str, Any],
        auto_apply: bool,
        confidence_threshold: float,
    ) -> List[Dict[str, Any]]:
        """Enrich entities with ontology mapping"""
        enriched_entities = []

        for entity in entities:
            enriched_entity = entity.copy()
            entity_type = entity.get("entity_type", "")

            # Try exact match first
            ontology_mapping = self._find_exact_class_match(
                entity_type, ontology_context["classes"]
            )

            if ontology_mapping:
                # Found exact match
                enriched_entity.update(
                    {
                        "ontology_class_id": ontology_mapping["class_id"],
                        "ontology_class_uri": ontology_mapping["class_uri"],
                        "ontology_class_label": ontology_mapping["class_label"],
                        "is_mapped": True,
                        "mapping_confidence": 1.0,
                        "mapping_method": "exact_match",
                    }
                )
            else:
                # No exact match, generate AI suggestions
                enriched_entity.update(
                    {
                        "is_mapped": False,
                        "is_novel": True,
                    }
                )

                # Generate AI suggestions
                # suggestions = await self._generate_entity_suggestions(
                #     entity, ontology_context["classes"]
                # )
                suggestions = []
                enriched_entity["mapping_suggestions"] = suggestions

                # Auto-apply if conditions are met
                # if auto_apply and suggestions:
                #     best_suggestion = max(
                #         suggestions, key=lambda x: x.get("confidence", 0)
                #     )
                #     if best_suggestion.get("confidence", 0) >= confidence_threshold:
                #         self._apply_entity_suggestion(
                #             enriched_entity,
                #             best_suggestion,
                #             ontology_context["classes"],
                #         )

            enriched_entities.append(enriched_entity)

        return enriched_entities

    async def _enrich_relationships(
        self,
        relationships: List[Dict[str, Any]],
        ontology_context: Dict[str, Any],
        auto_apply: bool,
        confidence_threshold: float,
    ) -> List[Dict[str, Any]]:
        """Enrich relationships with ontology mapping"""
        enriched_relationships = []

        for relationship in relationships:
            enriched_relationship = relationship.copy()
            relationship_type = relationship.get("relationship_type", "")

            # Try exact match first
            ontology_mapping = self._find_exact_property_match(
                relationship_type, ontology_context["object_properties"]
            )

            if ontology_mapping:
                # Found exact match
                enriched_relationship.update(
                    {
                        "ontology_property_id": ontology_mapping["property_id"],
                        "ontology_property_uri": ontology_mapping["property_uri"],
                        "ontology_property_label": ontology_mapping["property_label"],
                        "is_mapped": True,
                        "mapping_confidence": 1.0,
                        "mapping_method": "exact_match",
                    }
                )
            else:
                # No exact match, generate AI suggestions
                enriched_relationship.update(
                    {
                        "is_mapped": False,
                        "is_novel": True,
                    }
                )

                # Generate AI suggestions
                # suggestions = await self._generate_relationship_suggestions(
                #     relationship, ontology_context["object_properties"]
                # )
                suggestions = []
                enriched_relationship["mapping_suggestions"] = suggestions

                # Auto-apply if conditions are met
                # if auto_apply and suggestions:
                #     best_suggestion = max(
                #         suggestions, key=lambda x: x.get("confidence", 0)
                #     )
                #     if best_suggestion.get("confidence", 0) >= confidence_threshold:
                #         self._apply_relationship_suggestion(
                #             enriched_relationship,
                #             best_suggestion,
                #             ontology_context["object_properties"],
                #         )

            enriched_relationships.append(enriched_relationship)

        return enriched_relationships

    def _find_exact_class_match(
        self, entity_type: str, classes: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find exact match for entity class"""
        entity_type_lower = entity_type.lower()

        for class_id, class_info in classes.items():
            class_label = class_info.get("label", "").lower()
            if class_label == entity_type_lower:
                return {
                    "class_id": class_id,
                    "class_uri": class_info.get("uri"),
                    "class_label": class_info.get("label"),
                }

        return None

    def _find_exact_property_match(
        self, relationship_type: str, properties: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find exact match for relationship property"""
        relationship_type_lower = relationship_type.lower()

        for prop_id, prop_info in properties.items():
            prop_label = prop_info.get("label", "").lower()
            if prop_label == relationship_type_lower:
                return {
                    "property_id": prop_id,
                    "property_uri": prop_info.get("uri"),
                    "property_label": prop_info.get("label"),
                }

        return None

    async def _generate_entity_suggestions(
        self, entity: Dict[str, Any], classes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AI suggestions for entity mapping"""
        try:
            if not self.llm_client:
                return []

            entity_text = entity.get("text", "")
            entity_type = entity.get("entity_type", "")

            available_classes = [
                {
                    "label": info.get("label", ""),
                    "description": info.get("description", ""),
                }
                for info in classes.values()
            ]

            prompt = f"""
            Bạn là chuyên gia ánh xạ ontology. Tôi cần đề xuất để ánh xạ một entity được trích xuất với các lớp ontology hiện có.

            Entity được trích xuất:
            - Văn bản: "{entity_text}"
            - Loại: "{entity_type}"

            Các lớp Ontology có sẵn:
            {json.dumps(available_classes[:20], indent=2)}

            Vui lòng cung cấp đề xuất ánh xạ theo định dạng JSON:
            {{
                "suggestions": [
                    {{
                        "suggested_class": "NHÃN_LỚP" // là tên class mới hoặc id của class cũ,
                        "confidence": 0.85,
                        "reasoning": "Lý do tại sao ánh xạ này có ý nghĩa",
                        "is_new_class": false
                    }}
                ]
            }}

            Nếu không có kết quả phù hợp nào, hãy đề xuất tạo lớp mới với "is_new_class": true.
            Cung cấp tối đa 3 đề xuất được sắp xếp theo độ tin cậy.
            """

            response = await self._call_ai_service(prompt)
            if response and "suggestions" in response:
                return response["suggestions"]

            return []

        except Exception as e:
            await self.logger.error(f"Error generating entity suggestions: {e}")
            return []

    async def _generate_relationship_suggestions(
        self, relationship: Dict[str, Any], properties: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AI suggestions for relationship mapping"""
        try:
            if not self.llm_client:
                return []

            relationship_type = relationship.get("relationship_type", "")
            source_entity_type = relationship.get("source_entity_type", "")
            target_entity_type = relationship.get("target_entity_type", "")

            available_properties = [
                {
                    "label": info.get("label", ""),
                    "description": info.get("description", ""),
                }
                for info in properties.values()
            ]

            prompt = f"""
            Bạn là chuyên gia ánh xạ ontology. Tôi cần đề xuất để ánh xạ một mối quan hệ được trích xuất với các thuộc tính ontology hiện có.

            Mối quan hệ được trích xuất:
            - Loại: "{relationship_type}"
            - Loại Entity nguồn: "{source_entity_type}"
            - Loại Entity đích: "{target_entity_type}"

            Các thuộc tính Ontology có sẵn:
            {json.dumps(available_properties[:20], indent=2)}

            Vui lòng cung cấp đề xuất ánh xạ theo định dạng JSON:
            {{
                "suggestions": [
                    {{
                        "suggested_property": "NHÃN_THUỘC_TÍNH",
                        "confidence": 0.85,
                        "reasoning": "Lý do tại sao ánh xạ này có ý nghĩa",
                        "is_new_property": false
                    }}
                ]
            }}

            Nếu không có kết quả phù hợp nào, hãy đề xuất tạo thuộc tính mới với "is_new_property": true.
            Cung cấp tối đa 3 đề xuất được sắp xếp theo độ tin cậy.
            """

            response = await self._call_ai_service(prompt)
            if response and "suggestions" in response:
                return response["suggestions"]

            return []

        except Exception as e:
            await self.logger.error(f"Error generating relationship suggestions: {e}")
            return []

    def _apply_entity_suggestion(
        self,
        entity: Dict[str, Any],
        suggestion: Dict[str, Any],
        classes: Dict[str, Any],
    ):
        """Apply AI suggestion to entity"""
        suggested_class = suggestion.get("suggested_class", "")

        for class_id, class_info in classes.items():
            if class_info.get("label", "") == suggested_class:
                entity.update(
                    {
                        "ontology_class_id": class_id,
                        "ontology_class_uri": class_info.get("uri"),
                        "ontology_class_label": class_info.get("label"),
                        "is_mapped": True,
                        "mapping_confidence": suggestion.get("confidence", 0.0),
                        "mapping_method": "auto_applied_ai_suggestion",
                        "auto_applied": True,
                    }
                )
                break

    def _apply_relationship_suggestion(
        self,
        relationship: Dict[str, Any],
        suggestion: Dict[str, Any],
        properties: Dict[str, Any],
    ):
        """Apply AI suggestion to relationship"""
        suggested_property = suggestion.get("suggested_property", "")

        for prop_id, prop_info in properties.items():
            if prop_info.get("label", "") == suggested_property:
                relationship.update(
                    {
                        "ontology_property_id": prop_id,
                        "ontology_property_uri": prop_info.get("uri"),
                        "ontology_property_label": prop_info.get("label"),
                        "is_mapped": True,
                        "mapping_confidence": suggestion.get("confidence", 0.0),
                        "mapping_method": "auto_applied_ai_suggestion",
                        "auto_applied": True,
                    }
                )
                break

    async def _save_mappings_to_db(
        self,
        enriched_entities: List[Dict[str, Any]],
        enriched_relationships: List[Dict[str, Any]],
        domain: Optional[str],
        user_id: Optional[str],
    ) -> Dict[str, int]:
        """Save all mappings to database tables using new schema"""
        try:
            supabase = await get_supabase()
            entity_mappings_saved = 0
            relationship_mappings_saved = 0

            # Save ALL entity mappings
            for entity in enriched_entities:
                try:
                    entity_type = entity.get("entity_type", "")
                    if not entity_type:
                        continue

                    # Check if mapping already exists (by entity_type for backward compatibility)
                    existing = (
                        await supabase.table("entity_mappings")
                        .select("*")
                        .eq("entity_type", entity_type)
                        .execute()
                    )

                    if not existing.data:
                        # Determine mapping status based on whether it's mapped
                        is_mapped = entity.get("is_mapped", False)
                        ontology_class_id = entity.get("ontology_class_id")

                        mapping_record = {
                            "entity_type": entity_type,  # Legacy field
                            "ontology_class_id": ontology_class_id,
                            "confidence": entity.get("mapping_confidence", 0.0),
                            "is_verified": False,  # Always starts as unverified
                            "mapping_status": "mapped" if is_mapped else "pending",
                            "suggestions": entity.get("mapping_suggestions", {}),
                            "mapping_notes": "",
                            "auto_mapped": entity.get("auto_applied", False),
                            "created_by": user_id,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }

                        # Only include ontology_class_id if it's actually mapped
                        if not is_mapped:
                            mapping_record["ontology_class_id"] = None

                        await supabase.table("entity_mappings").insert(
                            mapping_record
                        ).execute()
                        entity_mappings_saved += 1
                        await self.logger.info(
                            f"Saved entity mapping: {entity_type} (status: {mapping_record['mapping_status']})"
                        )

                except Exception as e:
                    await self.logger.error(
                        f"Error saving entity mapping for {entity.get('entity_type')}: {e}"
                    )

            # Save ALL relationship mappings
            for relationship in enriched_relationships:
                try:
                    relationship_type = relationship.get("relationship_type", "")
                    if not relationship_type:
                        continue

                    # Check if mapping already exists (by relationship_type for backward compatibility)
                    existing = (
                        await supabase.table("relationship_mappings")
                        .select("*")
                        .eq("relationship_type", relationship_type)
                        .execute()
                    )

                    if not existing.data:
                        # Determine mapping status based on whether it's mapped
                        is_mapped = relationship.get("is_mapped", False)
                        ontology_property_id = relationship.get("ontology_property_id")

                        mapping_record = {
                            "relationship_type": relationship_type,  # Legacy field
                            "ontology_property_id": ontology_property_id,
                            "confidence": relationship.get("mapping_confidence", 0.0),
                            "is_verified": False,  # Always starts as unverified
                            "mapping_status": "mapped" if is_mapped else "pending",
                            "suggestions": relationship.get("mapping_suggestions", []),
                            "mapping_notes": "",
                            "auto_mapped": relationship.get("auto_applied", False),
                            "created_by": user_id,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }

                        # Only include ontology_property_id if it's actually mapped
                        if not is_mapped:
                            mapping_record["ontology_property_id"] = None

                        await supabase.table("relationship_mappings").insert(
                            mapping_record
                        ).execute()
                        relationship_mappings_saved += 1
                        await self.logger.info(
                            f"Saved relationship mapping: {relationship_type} (status: {mapping_record['mapping_status']})"
                        )

                except Exception as e:
                    await self.logger.error(
                        f"Error saving relationship mapping for {relationship.get('relationship_type')}: {e}"
                    )

            await self.logger.info(
                f"Saved {entity_mappings_saved} entity mappings and {relationship_mappings_saved} relationship mappings"
            )

            return {
                "entity_mappings_saved": entity_mappings_saved,
                "relationship_mappings_saved": relationship_mappings_saved,
            }

        except Exception as e:
            await self.logger.error(f"Error saving mappings: {e}")
            return {"entity_mappings_saved": 0, "relationship_mappings_saved": 0}

    def _calculate_statistics(
        self,
        original_entities: List[Dict[str, Any]],
        original_relationships: List[Dict[str, Any]],
        enriched_entities: List[Dict[str, Any]],
        enriched_relationships: List[Dict[str, Any]],
        saved_mappings: Dict[str, int],
        start_time: float,
    ) -> Dict[str, Any]:
        """Calculate enrichment statistics"""
        execution_time = int((time.time() - start_time) * 1000)

        # Count mappings
        mapped_entities = sum(1 for e in enriched_entities if e.get("is_mapped"))
        unmapped_entities = sum(1 for e in enriched_entities if not e.get("is_mapped"))
        mapped_relationships = sum(
            1 for r in enriched_relationships if r.get("is_mapped")
        )
        unmapped_relationships = sum(
            1 for r in enriched_relationships if not r.get("is_mapped")
        )

        # Calculate average confidence for mapped items only
        entity_confidences = [
            e.get("mapping_confidence", 0.0)
            for e in enriched_entities
            if e.get("is_mapped")
        ]
        relationship_confidences = [
            r.get("mapping_confidence", 0.0)
            for r in enriched_relationships
            if r.get("is_mapped")
        ]

        return {
            "total_entities": len(original_entities),
            "total_relationships": len(original_relationships),
            "mapped_entities": mapped_entities,
            "unmapped_entities": unmapped_entities,
            "mapped_relationships": mapped_relationships,
            "unmapped_relationships": unmapped_relationships,
            "entity_mapping_confidence_avg": (
                sum(entity_confidences) / len(entity_confidences)
                if entity_confidences
                else 0.0
            ),
            "relationship_mapping_confidence_avg": (
                sum(relationship_confidences) / len(relationship_confidences)
                if relationship_confidences
                else 0.0
            ),
            "total_mapping_records_saved": saved_mappings["entity_mappings_saved"]
            + saved_mappings["relationship_mappings_saved"],
            "entity_mapping_records_saved": saved_mappings["entity_mappings_saved"],
            "relationship_mapping_records_saved": saved_mappings[
                "relationship_mappings_saved"
            ],
            "execution_time_ms": execution_time,
            "enrichment_time": datetime.now(timezone.utc).isoformat(),
        }

    def _get_error_statistics(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        start_time: float,
    ) -> Dict[str, Any]:
        """Get statistics for error cases"""
        execution_time = int((time.time() - start_time) * 1000)

        return {
            "total_entities": len(entities),
            "total_relationships": len(relationships),
            "mapped_entities": 0,
            "novel_entities": 0,
            "mapped_relationships": 0,
            "novel_relationships": 0,
            "entity_mapping_confidence_avg": 0.0,
            "relationship_mapping_confidence_avg": 0.0,
            "saved_entity_mappings": 0,
            "saved_relationship_mappings": 0,
            "execution_time_ms": execution_time,
            "enrichment_time": datetime.now(timezone.utc).isoformat(),
        }

    async def _call_ai_service(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call AI service for suggestions"""
        try:
            if not self.llm_client:
                await self.logger.error("LLM client not initialized")
                return None

            content = await self.llm_client.extract_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return content

        except Exception as e:
            await self.logger.error(f"Error calling AI service: {e}")
            return None

    # ============================================
    # LEGACY METHODS FOR COMPATIBILITY
    # ============================================

    async def suggest_ontology_extensions(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        domain: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Legacy method for ontology extension suggestions"""
        try:
            # Simple pattern analysis
            entity_types = {
                e.get("entity_type") for e in entities if e.get("entity_type")
            }
            relationship_types = {
                r.get("relationship_type")
                for r in relationships
                if r.get("relationship_type")
            }

            extensions = []

            # Suggest new entity types
            for entity_type in entity_types:
                extensions.append(
                    {
                        "type": "entity_type",
                        "name": entity_type,
                        "confidence": 0.8,
                        "reasoning": f"Entity type '{entity_type}' found in extracted data",
                    }
                )

            # Suggest new relationship types
            for rel_type in relationship_types:
                extensions.append(
                    {
                        "type": "relationship_type",
                        "name": rel_type,
                        "confidence": 0.8,
                        "reasoning": f"Relationship type '{rel_type}' found in extracted data",
                    }
                )

            return {
                "extension_suggestions": extensions,
                "entity_patterns": {"type_frequency": {et: 1 for et in entity_types}},
                "relationship_patterns": {
                    "type_frequency": {rt: 1 for rt in relationship_types}
                },
            }

        except Exception as e:
            await self.logger.error(f"Error generating ontology extensions: {e}")
            return {
                "extension_suggestions": [],
                "entity_patterns": {},
                "relationship_patterns": {},
                "error": str(e),
            }
