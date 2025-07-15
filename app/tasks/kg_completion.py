from typing import Any, Dict, List, Optional

from app.core.supabase import get_supabase
from app.services.knowledge_graph import KnowledgeGraphService
from app.tasks.executors import StepLogger


class KnowledgeGraphCompletionTask:
    """
    Task for knowledge graph completion with Vietnamese banking domain support
    Now delegates to KnowledgeGraphService for database operations
    """

    def __init__(self, logger: StepLogger):
        self.kg_service = KnowledgeGraphService()
        self.logger = logger

    async def complete_knowledge_graph(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        completion_types: List[str] = None,
        auto_apply_suggestions: bool = False,
        confidence_threshold: float = 0.8,
        user_id: Optional[str] = None,
        entity_ids: Optional[List[str]] = None,
        limit_entities: Optional[int] = None,
        limit_relationships: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Complete knowledge graph by suggesting missing entities and relationships
        Uses KnowledgeGraphService for database operations

        Args:
            entities: List of existing entities
            relationships: List of existing relationships
            completion_types: Types of completion (missing_entities, missing_relationships)
            auto_apply_suggestions: Whether to automatically apply high-confidence suggestions
            confidence_threshold: Minimum confidence for auto-application
            user_id: User performing completion
            entity_ids: Specific entity IDs to complete around
            limit_entities: Maximum number of entities to analyze
            limit_relationships: Maximum number of relationships to analyze

        Returns:
            Dictionary containing completion results
        """
        try:
            if completion_types is None:
                completion_types = ["missing_entities", "missing_relationships"]

            await self.logger.info(
                f"Starting knowledge graph completion with {len(entities)} entities and {len(relationships)} relationships"
            )

            # Apply limits if specified
            if limit_entities and len(entities) > limit_entities:
                entities = entities[:limit_entities]
            if limit_relationships and len(relationships) > limit_relationships:
                relationships = relationships[:limit_relationships]

            # Generate completion suggestions
            suggestions = await self._generate_completion_suggestions(
                entities, relationships, completion_types
            )

            # Save suggestions to database via service
            saved_suggestions = await self.kg_service.save_completion_suggestions(
                suggestions, user_id
            )

            # Auto-apply suggestions if requested
            applied_suggestions = None
            if auto_apply_suggestions:
                applied_suggestions = (
                    await self.kg_service.apply_high_confidence_suggestions(
                        saved_suggestions, confidence_threshold, user_id
                    )
                )

            result = {
                "suggestions": saved_suggestions,
                "applied_suggestions": applied_suggestions,
                "completion_stats": {
                    "input_entities": len(entities),
                    "input_relationships": len(relationships),
                    "suggested_entities": len(
                        [
                            s
                            for s in saved_suggestions
                            if s["suggestion_type"] == "entity"
                        ]
                    ),
                    "suggested_relationships": len(
                        [
                            s
                            for s in saved_suggestions
                            if s["suggestion_type"] == "relationship"
                        ]
                    ),
                    "auto_applied": (
                        len(applied_suggestions.get("applied_suggestions", []))
                        if applied_suggestions
                        else 0
                    ),
                },
                "success": True,
            }

            await self.logger.info(
                f"Knowledge graph completion completed with {result['completion_stats']['suggested_entities']} entity and {result['completion_stats']['suggested_relationships']} relationship suggestions"
            )
            return result

        except Exception as e:
            await self.logger.error(f"Error in knowledge graph completion: {e}")
            return {
                "suggestions": [],
                "error": str(e),
                "success": False,
            }

    # =============================================
    # SUGGESTION GENERATION METHODS
    # =============================================

    async def _generate_completion_suggestions(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        completion_types: List[str],
    ) -> Dict[str, Any]:
        """Generate completion suggestions based on Vietnamese banking patterns"""
        suggestions = {
            "missing_entities": [],
            "missing_relationships": [],
            "completion_stats": {},
        }

        if "missing_entities" in completion_types:
            missing_entities = await self._suggest_missing_entities(
                entities, relationships
            )
            suggestions["missing_entities"] = missing_entities

        if "missing_relationships" in completion_types:
            missing_relationships = await self._suggest_missing_relationships(
                entities, relationships
            )
            suggestions["missing_relationships"] = missing_relationships

        suggestions["completion_stats"] = {
            "entities_analyzed": len(entities),
            "relationships_analyzed": len(relationships),
            "entity_suggestions": len(suggestions["missing_entities"]),
            "relationship_suggestions": len(suggestions["missing_relationships"]),
        }

        return suggestions

    async def _suggest_missing_entities(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest missing entities based on Vietnamese banking patterns"""
        suggestions = []

        # Find entities mentioned in relationships but not in entity list
        entity_texts = set(
            self._normalize_vietnamese_text(e.get("text", e.get("entity_text", "")))
            for e in entities
        )

        relationship_entities = set()
        for relationship in relationships:
            source_entity = self._normalize_vietnamese_text(
                relationship.get("source_entity", "")
            )
            target_entity = self._normalize_vietnamese_text(
                relationship.get("target_entity", "")
            )

            if source_entity:
                relationship_entities.add(source_entity)
            if target_entity:
                relationship_entities.add(target_entity)

        # Suggest entities mentioned in relationships but missing from entity list
        for rel_entity in relationship_entities:
            if rel_entity not in entity_texts and rel_entity.strip():
                entity_type = self._infer_vietnamese_entity_type(rel_entity)
                suggestions.append(
                    {
                        "suggested_text": rel_entity,
                        "suggested_type": entity_type,
                        "reason": "Referenced in relationships but not in entity list",
                        "confidence": 0.8,
                        "priority": "high",
                        "source": "relationship_reference",
                    }
                )

        # Suggest entities based on Vietnamese banking patterns
        banking_suggestions = await self._suggest_vietnamese_banking_entities(entities)
        suggestions.extend(banking_suggestions)

        # Remove duplicates
        suggestions = self._deduplicate_entity_suggestions(suggestions)

        return suggestions

    async def _suggest_missing_relationships(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest missing relationships based on Vietnamese banking patterns"""
        suggestions = []

        # Group entities by type for pattern-based suggestions
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.get("entity_type", "Unknown")
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # Vietnamese banking relationship patterns
        relationship_patterns = [
            {
                "source_type": "Person",
                "target_type": "Bank",
                "relationship": "is_customer_of",
                "confidence": 0.7,
                "reason": "People are typically customers of banks in Vietnamese banking",
            },
            {
                "source_type": "Person",
                "target_type": "Account",
                "relationship": "owns_account",
                "confidence": 0.8,
                "reason": "People own accounts in Vietnamese banking",
            },
            {
                "source_type": "Bank",
                "target_type": "Product",
                "relationship": "offers_product",
                "confidence": 0.6,
                "reason": "Banks offer financial products",
            },
            {
                "source_type": "Person",
                "target_type": "Product",
                "relationship": "uses_product",
                "confidence": 0.6,
                "reason": "People use financial products",
            },
            {
                "source_type": "Account",
                "target_type": "Bank",
                "relationship": "belongs_to_bank",
                "confidence": 0.9,
                "reason": "Accounts belong to specific banks",
            },
            {
                "source_type": "Transaction",
                "target_type": "Account",
                "relationship": "involves_account",
                "confidence": 0.8,
                "reason": "Transactions involve accounts",
            },
        ]

        # Create existing relationship lookup
        existing_relationships = set()
        for rel in relationships:
            source = self._normalize_vietnamese_text(rel.get("source_entity", ""))
            target = self._normalize_vietnamese_text(rel.get("target_entity", ""))
            rel_type = rel.get("relationship_type", "")
            existing_relationships.add((source, target, rel_type))

        # Suggest relationships based on patterns
        for pattern in relationship_patterns:
            source_entities = entities_by_type.get(pattern["source_type"], [])
            target_entities = entities_by_type.get(pattern["target_type"], [])

            for source_entity in source_entities:
                for target_entity in target_entities:
                    source_text = self._normalize_vietnamese_text(
                        source_entity.get("text", source_entity.get("entity_text", ""))
                    )
                    target_text = self._normalize_vietnamese_text(
                        target_entity.get("text", target_entity.get("entity_text", ""))
                    )

                    # Check if this relationship already exists
                    if (
                        source_text,
                        target_text,
                        pattern["relationship"],
                    ) not in existing_relationships:
                        # Additional filtering for Vietnamese banking logic
                        if self._is_valid_vietnamese_banking_relationship(
                            source_entity, target_entity, pattern["relationship"]
                        ):
                            suggestions.append(
                                {
                                    "source_entity": source_entity.get(
                                        "text", source_entity.get("entity_text", "")
                                    ),
                                    "target_entity": target_entity.get(
                                        "text", target_entity.get("entity_text", "")
                                    ),
                                    "suggested_type": pattern["relationship"],
                                    "reason": pattern["reason"],
                                    "confidence": pattern["confidence"],
                                    "priority": "medium",
                                    "source_entity_type": pattern["source_type"],
                                    "target_entity_type": pattern["target_type"],
                                }
                            )

        # Suggest relationships based on co-occurrence patterns
        cooccurrence_suggestions = await self._suggest_cooccurrence_relationships(
            entities
        )
        suggestions.extend(cooccurrence_suggestions)

        # Remove duplicates and low-confidence suggestions
        suggestions = self._deduplicate_relationship_suggestions(suggestions)

        return suggestions

    async def _suggest_vietnamese_banking_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest Vietnamese banking entities based on domain knowledge"""
        suggestions = []

        # Analyze existing entities to understand the domain
        entity_types = [e.get("entity_type", "") for e in entities]

        # Vietnamese banking entity suggestions based on common patterns
        banking_suggestions = {
            "Bank": [
                "Vietcombank",
                "BIDV",
                "VietinBank",
                "ACB",
                "Techcombank",
                "MB Bank",
                "VPBank",
                "TPBank",
                "SeABank",
            ],
            "Product": [
                "Thẻ tín dụng",
                "Tài khoản tiết kiệm",
                "Vay thế chấp",
                "Bảo hiểm nhân thọ",
                "Quỹ đầu tư",
            ],
            "Location": [
                "Chi nhánh Hà Nội",
                "Chi nhánh TP.HCM",
                "Phòng giao dịch",
                "ATM",
                "Trung tâm giao dịch",
            ],
        }

        # Suggest entities if we have related entities but missing common ones
        for entity_type, common_entities in banking_suggestions.items():
            if entity_type in entity_types:
                existing_entities_of_type = [
                    self._normalize_vietnamese_text(
                        e.get("text", e.get("entity_text", ""))
                    )
                    for e in entities
                    if e.get("entity_type") == entity_type
                ]

                for common_entity in common_entities:
                    normalized_common = self._normalize_vietnamese_text(common_entity)
                    if normalized_common not in existing_entities_of_type:
                        suggestions.append(
                            {
                                "suggested_text": common_entity,
                                "suggested_type": entity_type,
                                "reason": f"Common {entity_type} in Vietnamese banking domain",
                                "confidence": 0.6,
                                "priority": "low",
                                "source": "domain_knowledge",
                            }
                        )

        return suggestions

    async def _suggest_cooccurrence_relationships(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest relationships based on entity co-occurrence patterns"""
        suggestions = []

        # This would ideally analyze the source text to find entities that appear together
        # For now, we'll use a simplified heuristic based on Vietnamese banking logic

        persons = [e for e in entities if e.get("entity_type") == "Person"]
        banks = [e for e in entities if e.get("entity_type") == "Bank"]
        accounts = [e for e in entities if e.get("entity_type") == "Account"]

        # Suggest person-bank relationships if we have both
        if persons and banks and len(persons) <= 3 and len(banks) <= 2:
            for person in persons:
                for bank in banks:
                    suggestions.append(
                        {
                            "source_entity": person.get(
                                "text", person.get("entity_text", "")
                            ),
                            "target_entity": account.get(
                                "text", account.get("entity_text", "")
                            ),
                            "suggested_type": "owns_account",
                            "reason": "Person and account co-occurrence suggests ownership",
                            "confidence": 0.7,
                            "priority": "medium",
                            "source_entity_type": "Person",
                            "target_entity_type": "Account",
                        }
                    )

        return suggestions

    # =============================================
    # HELPER METHODS
    # =============================================

    def _infer_vietnamese_entity_type(self, entity_text: str) -> str:
        """Infer entity type from Vietnamese text"""
        text_lower = entity_text.lower()

        # Vietnamese banking entity type inference
        if any(word in text_lower for word in ["ngân hàng", "nh", "bank"]):
            return "Bank"
        elif any(word in text_lower for word in ["tài khoản", "tk", "account"]):
            return "Account"
        elif any(word in text_lower for word in ["thẻ", "card", "visa", "master"]):
            return "Product"
        elif any(word in text_lower for word in ["giao dịch", "transaction"]):
            return "Transaction"
        elif any(
            word in text_lower for word in ["chi nhánh", "phòng giao dịch", "atm"]
        ):
            return "Location"
        elif any(
            word in text_lower for word in ["triệu", "tỷ", "nghìn", "đồng", "vnd"]
        ):
            return "Money"
        # Vietnamese name pattern
        elif len(entity_text.split()) >= 2 and entity_text[0].isupper():
            return "Person"
        else:
            return "Unknown"

    def _is_valid_vietnamese_banking_relationship(
        self,
        source_entity: Dict[str, Any],
        target_entity: Dict[str, Any],
        relationship_type: str,
    ) -> bool:
        """Check if a relationship is valid in Vietnamese banking context"""
        source_text = source_entity.get(
            "text", source_entity.get("entity_text", "")
        ).lower()
        target_text = target_entity.get(
            "text", target_entity.get("entity_text", "")
        ).lower()

        # Avoid suggesting relationships between the same entity
        if self._normalize_vietnamese_text(
            source_text
        ) == self._normalize_vietnamese_text(target_text):
            return False

        # Vietnamese banking relationship validation rules
        if relationship_type == "is_customer_of":
            # Person should have a Vietnamese name pattern
            return (
                source_entity.get("entity_type") == "Person"
                and target_entity.get("entity_type") == "Bank"
            )

        elif relationship_type == "owns_account":
            # Account should have account-like text
            return (
                source_entity.get("entity_type") == "Person"
                and target_entity.get("entity_type") == "Account"
            )

        elif relationship_type == "belongs_to_bank":
            # Account should belong to a bank
            return (
                source_entity.get("entity_type") == "Account"
                and target_entity.get("entity_type") == "Bank"
            )

        return True

    def _normalize_vietnamese_text(self, text: str) -> str:
        """Normalize Vietnamese text for comparison"""
        import re

        text = text.lower().strip()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common Vietnamese prefixes/suffixes
        text = re.sub(r"^(ông|bà|anh|chị|em|cô|chú|bác)\s+", "", text)
        text = re.sub(r"\s+(ạ|à|ơi|nhé)$", "", text)

        # Normalize banking terms
        text = text.replace("tk", "tài khoản")
        text = text.replace("nh", "ngân hàng")

        return text

    def _deduplicate_entity_suggestions(
        self, suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate entity suggestions"""
        unique_suggestions = []
        seen = set()

        for suggestion in suggestions:
            key = (
                self._normalize_vietnamese_text(suggestion.get("suggested_text", "")),
                suggestion.get("suggested_type", ""),
            )

            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)

        # Sort by confidence and priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        unique_suggestions.sort(
            key=lambda x: (
                priority_order.get(x.get("priority", "low"), 1),
                x.get("confidence", 0),
            ),
            reverse=True,
        )

        return unique_suggestions

    def _deduplicate_relationship_suggestions(
        self, suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate relationship suggestions"""
        unique_suggestions = []
        seen = set()

        for suggestion in suggestions:
            key = (
                self._normalize_vietnamese_text(suggestion.get("source_entity", "")),
                self._normalize_vietnamese_text(suggestion.get("target_entity", "")),
                suggestion.get("suggested_type", ""),
            )

            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)

        # Sort by confidence and priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        unique_suggestions.sort(
            key=lambda x: (
                priority_order.get(x.get("priority", "low"), 1),
                x.get("confidence", 0),
            ),
            reverse=True,
        )

        return unique_suggestions

    async def _apply_suggestions(
        self,
        suggestions: Dict[str, Any],
        confidence_threshold: float,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply high-confidence suggestions automatically"""
        try:
            supabase = await get_supabase()
            applied_count = {"entities": 0, "relationships": 0, "errors": []}

            # Apply entity suggestions
            for entity_suggestion in suggestions.get("missing_entities", []):
                if entity_suggestion.get("confidence", 0) >= confidence_threshold:
                    try:
                        entity_data = {
                            "entity_text": entity_suggestion["suggested_text"],
                            "entity_type": entity_suggestion["suggested_type"],
                            "confidence": entity_suggestion.get("confidence"),
                            "extraction_confidence": entity_suggestion.get(
                                "confidence"
                            ),
                            "is_verified": False,
                            "validation_status": "auto_suggested",
                            "created_by": user_id,
                            "properties": {
                                "auto_suggested": True,
                                "reason": entity_suggestion.get("reason"),
                                "source": entity_suggestion.get("source"),
                                "priority": entity_suggestion.get("priority"),
                            },
                        }

                        await supabase.from_("kg_entities").insert(
                            entity_data
                        ).execute()
                        applied_count["entities"] += 1

                    except Exception as e:
                        applied_count["errors"].append(
                            f"Error applying entity suggestion: {str(e)}"
                        )

            # Apply relationship suggestions
            for rel_suggestion in suggestions.get("missing_relationships", []):
                if rel_suggestion.get("confidence", 0) >= confidence_threshold:
                    try:
                        # Find source and target entity IDs
                        source_entity_id = await self._find_entity_by_text(
                            rel_suggestion.get("source_entity", "")
                        )
                        target_entity_id = await self._find_entity_by_text(
                            rel_suggestion.get("target_entity", "")
                        )

                        if source_entity_id and target_entity_id:
                            relationship_data = {
                                "source_entity_id": source_entity_id,
                                "target_entity_id": target_entity_id,
                                "confidence": rel_suggestion.get("confidence"),
                                "extraction_confidence": rel_suggestion.get(
                                    "confidence"
                                ),
                                "is_verified": False,
                                "validation_status": "auto_suggested",
                                "properties": {
                                    "auto_suggested": True,
                                    "reason": rel_suggestion.get("reason"),
                                    "relationship_type": rel_suggestion.get(
                                        "suggested_type"
                                    ),
                                    "source_entity_text": rel_suggestion.get(
                                        "source_entity"
                                    ),
                                    "target_entity_text": rel_suggestion.get(
                                        "target_entity"
                                    ),
                                },
                            }

                            await supabase.from_("kg_relationships").insert(
                                relationship_data
                            ).execute()
                            applied_count["relationships"] += 1

                    except Exception as e:
                        applied_count["errors"].append(
                            f"Error applying relationship suggestion: {str(e)}"
                        )

            return applied_count

        except Exception as e:
            await self.logger.error(f"Error applying suggestions: {e}")
            return {"entities": 0, "relationships": 0, "errors": [str(e)]}

    async def _find_entity_by_text(self, entity_text: str) -> Optional[str]:
        """Find entity ID by text with Vietnamese-aware matching"""
        try:
            supabase = await get_supabase()

            # First try exact match
            response = (
                await supabase.from_("kg_entities")
                .select("id")
                .eq("entity_text", entity_text)
                .limit(1)
                .execute()
            )

            if response.data:
                return response.data[0]["id"]

            # Try normalized matching
            normalized_text = self._normalize_vietnamese_text(entity_text)
            response = (
                await supabase.from_("kg_entities").select("id, entity_text").execute()
            )

            for entity in response.data:
                entity_normalized = self._normalize_vietnamese_text(
                    entity["entity_text"]
                )
                if entity_normalized == normalized_text:
                    return entity["id"]

            return None

        except Exception as e:
            await self.logger.warning(f"Error finding entity by text {entity_text}: {e}")
            return None
