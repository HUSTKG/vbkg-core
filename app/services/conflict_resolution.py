import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.core.config import settings
from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import (ConflictResolution,
                                             ConflictStatus, ConflictType,
                                             ResolutionMethod)
from app.services.knowledge_graph import KnowledgeGraphService

logger = logging.getLogger(__name__)


class ConflictResolutionService:
    """Service for resolving conflicts using AI assistance and expert input"""

    def __init__(self):
        self.kg_editor = KnowledgeGraphService()
        self.llm_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def resolve_conflict_automatically(
        self, conflict_id: str, use_ai: bool = True, confidence_threshold: float = 0.85
    ) -> Dict[str, Any]:
        """Attempt to resolve conflict automatically using AI"""

        supabase = await get_supabase()

        # Get conflict details
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .single()
            .execute()
        )
        conflict = conflict_response.data

        if not conflict:
            raise ValueError(f"Conflict {conflict_id} not found")

        # Generate AI resolution suggestions
        if use_ai:
            ai_suggestions = await self._generate_ai_resolution(conflict)

            await supabase.table("conflicts").update(
                {"auto_resolution_suggestions": ai_suggestions}
            ).eq("id", conflict_id).execute()

            # Filter by confidence threshold
            viable_suggestions = [
                s
                for s in ai_suggestions
                if s.get("confidence", 0) >= confidence_threshold
            ]

            if viable_suggestions:
                # Apply the highest confidence suggestion
                best_suggestion = max(
                    viable_suggestions, key=lambda x: x.get("confidence", 0)
                )
                return await self._apply_resolution(conflict_id, best_suggestion)

        # Fallback to rule-based resolution
        rule_based_resolution = await self._apply_rule_based_resolution(conflict)
        if rule_based_resolution:
            return await self._apply_resolution(conflict_id, rule_based_resolution)

        # Mark for manual review
        await self._assign_for_manual_review(conflict_id)
        return {
            "success": False,
            "message": "Conflict requires manual review",
            "assigned_for_review": True,
        }

    async def _generate_ai_resolution(self, conflict: Dict) -> List[Dict[str, Any]]:
        """Generate AI-powered resolution suggestions"""

        # Get detailed context for the conflict
        context = await self._get_conflict_context(conflict)

        # Create prompt for LLM
        prompt = self._create_resolution_prompt(conflict, context)

        try:
            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in knowledge graph conflict resolution.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            # Extract response text
            response_text = response.choices[0].message.content.strip()


            # Parse LLM response
            suggestions = self._parse_ai_response(response_text)
            return suggestions

        except Exception as e:
            logger.error(f"AI resolution generation failed: {e}")
            return []

    def _create_resolution_prompt(self, conflict: Dict, context: Dict) -> str:
        """Create structured prompt for AI conflict resolution"""

        conflict_type = conflict["conflict_type"]

        base_prompt = f"""
        Bạn là chuyên gia trong quản lý chất lượng đồ thị tri thức. Hãy phân tích xung đột sau đây và đưa ra khuyến nghị giải quyết.

        CHI TIẾT XUNG ĐỘT:
        Loại: {conflict_type}
        Mức độ nghiêm trọng: {conflict["severity"]}
        Mô tả: {conflict["description"]}
        Độ tin cậy: {conflict["confidence_score"]}

        DỮ LIỆU BỐI CẢNH:
        {json.dumps(context, indent=2)}

        NHIỆM VỤ: Đưa ra 1-3 gợi ý giải quyết, mỗi gợi ý bao gồm:
        1. Phương pháp giải quyết (merge_entities, keep_both, keep_source, keep_target, create_new, v.v.)
        2. Lý do chi tiết
        3. Điểm tin cậy (0-1)
        4. Các hành động cụ thể cần thực hiện
        5. Rủi ro tiềm ẩn hoặc những điều cần cân nhắc

        Định dạng phản hồi của bạn dưới dạng mảng JSON của các đối tượng giải quyết.
            """

        # Add type-specific guidance
        if conflict_type == "duplicate_entity":
            base_prompt += """
            
        Đối với các thực thể trùng lặp, hãy xem xét:
        - Mức độ tương đồng ngữ nghĩa và bối cảnh
        - Độ tin cậy và tính cập nhật của nguồn
        - Tính đầy đủ của thông tin
        - Việc bảo toàn các mối quan hệ
        """
        elif conflict_type == "contradictory_relationship":
            base_prompt += """
            
        Đối với các mối quan hệ mâu thuẫn, hãy xem xét:
        - Khía cạnh thời gian (cái nào gần đây hơn?)
        - Độ tin cậy của nguồn
        - Bối cảnh và hoàn cảnh
        - Khả năng cả hai đều đúng trong các bối cảnh khác nhau
        """

        return base_prompt

    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured suggestions"""

        try:
            # Try to extract JSON from response
            import re

            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                return suggestions
            else:
                # Fallback parsing
                return self._fallback_parse_response(response)

        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return []

    async def _get_conflict_context(self, conflict: Dict) -> Dict[str, Any]:
        """Get comprehensive context for conflict resolution"""

        supabase = await get_supabase()
        context = {}

        # Get entity details if involved
        if conflict.get("source_entity_id"):
            entity_response = (
                await supabase.table("kg_entities")
                .select("*")
                .eq("id", conflict["source_entity_id"])
                .single()
                .execute()
            )
            context["source_entity"] = entity_response.data

        if conflict.get("target_entity_id"):
            entity_response = (
                await supabase.table("kg_entities")
                .select("*")
                .eq("id", conflict["target_entity_id"])
                .single()
                .execute()
            )
            context["target_entity"] = entity_response.data

        # Get relationship details if involved
        if conflict.get("source_relationship_id"):
            rel_response = (
                await supabase.table("kg_relationships")
                .select("*")
                .eq("id", conflict["source_relationship_id"])
                .single()
                .execute()
            )
            context["source_relationship"] = rel_response.data

        # Get source document information
        if context.get("source_entity"):
            source_doc_id = context["source_entity"].get("source_document_id")
            if source_doc_id:
                doc_response = (
                    await supabase.table("file_uploads")
                    .select("*")
                    .eq("id", source_doc_id)
                    .single()
                    .execute()
                )
                context["source_document"] = doc_response.data

        return context

    async def _apply_rule_based_resolution(
        self, conflict: Dict
    ) -> Optional[Dict[str, Any]]:
        """Apply rule-based resolution for common conflict patterns"""

        conflict_type = conflict["conflict_type"]
        confidence = conflict["confidence_score"]

        # High confidence duplicate entities
        if conflict_type == "duplicate_entity" and confidence >= 0.95:
            return {
                "resolution_method": ResolutionMethod.MERGE_ENTITIES,
                "reasoning": f"High confidence duplicate detected ({confidence:.2f})",
                "confidence": 0.9,
                "actions": {
                    "merge_strategy": "prefer_more_complete",
                    "preserve_all_relationships": True,
                },
            }

        # Source reliability rules
        if conflict.get("context_data", {}).get("source_reliability"):
            reliability = conflict["context_data"]["source_reliability"]
            if reliability["source"] > reliability["target"] + 0.2:
                return {
                    "resolution_method": ResolutionMethod.KEEP_SOURCE,
                    "reasoning": f"Source has higher reliability score",
                    "confidence": 0.8,
                    "actions": {"delete_target": True},
                }

        return None

    async def resolve_conflict_manually(
        self, conflict_id: str, resolution: ConflictResolution, expert_id: str
    ) -> Dict[str, Any]:
        """Apply manual resolution by expert"""

        # Validate expert permissions
        if not await self._validate_expert_permissions(expert_id):
            raise PermissionError("User does not have expert permissions")

        # Apply the resolution
        result = await self._apply_resolution(
            conflict_id, resolution.model_dump(), expert_id
        )

        # Update conflict status
        await self._update_conflict_status(
            conflict_id, ConflictStatus.RESOLVED_MANUAL, resolution=resolution
        )

        return result

    async def _apply_resolution(
        self,
        conflict_id: str,
        resolution_data: Dict[str, Any],
        resolved_by: str = "ai_system",
    ) -> Dict[str, Any]:
        """Apply the specified resolution to the conflict"""

        method = resolution_data.get("resolution_method")
        actions = resolution_data.get("actions", {})

        try:
            if method == ResolutionMethod.MERGE_ENTITIES:
                result = await self._merge_entities(conflict_id, actions)
            elif method == ResolutionMethod.KEEP_SOURCE:
                result = await self._keep_source_entity(conflict_id, actions)
            elif method == ResolutionMethod.KEEP_TARGET:
                result = await self._keep_target_entity(conflict_id, actions)
            elif method == ResolutionMethod.KEEP_BOTH:
                result = await self._keep_both_entities(conflict_id, actions)
            elif method == ResolutionMethod.CREATE_NEW:
                result = await self._create_new_entity(conflict_id, actions)
            else:
                raise ValueError(f"Unknown resolution method: {method}")

            # Update conflict status
            resolution = ConflictResolution(
                resolution_method=method,
                resolution_data=actions,
                reasoning=resolution_data.get("reasoning", ""),
                confidence_score=resolution_data.get("confidence"),
                resolved_by=resolved_by,
                resolution_timestamp=datetime.now(),
            )

            await self._update_conflict_status(
                conflict_id,
                (
                    ConflictStatus.RESOLVED_AUTO
                    if resolved_by == "ai_system"
                    else ConflictStatus.RESOLVED_MANUAL
                ),
                resolution=resolution,
            )

            return {"success": True, "method": method, "details": result}

        except Exception as e:
            logger.error(f"Failed to apply resolution: {e}")
            return {"success": False, "error": str(e)}

    async def _merge_entities(self, conflict_id: str, actions: Dict) -> Dict[str, Any]:
        """Merge two conflicting entities"""

        # Get conflict details
        supabase = await get_supabase()
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .single()
            .execute()
        )
        conflict = conflict_response.data

        source_entity_id = conflict["source_entity_id"]
        target_entity_id = conflict["target_entity_id"]

        # Get entity details
        source_entity = (
            await supabase.table("kg_entities")
            .select("*")
            .eq("id", source_entity_id)
            .single()
            .execute()
        )
        target_entity = (
            await supabase.table("kg_entities")
            .select("*")
            .eq("id", target_entity_id)
            .single()
            .execute()
        )

        # Determine merge strategy
        merge_strategy = actions.get("merge_strategy", "prefer_more_complete")

        if merge_strategy == "prefer_more_complete":
            primary_entity, secondary_entity = self._choose_more_complete_entity(
                source_entity.data, target_entity.data
            )
        else:
            primary_entity, secondary_entity = source_entity.data, target_entity.data

        # Merge properties
        merged_properties = self._merge_entity_properties(
            primary_entity.get("properties", {}), secondary_entity.get("properties", {})
        )

        # Update primary entity
        await supabase.table("kg_entities").update(
            {
                "properties": merged_properties,
                "confidence": max(
                    primary_entity.get("confidence", 0.5),
                    secondary_entity.get("confidence", 0.5),
                ),
            }
        ).eq("id", primary_entity["id"]).execute()

        # Transfer relationships from secondary to primary
        if actions.get("preserve_all_relationships", True):
            await self._transfer_relationships(
                secondary_entity["id"], primary_entity["id"]
            )

        # Archive secondary entity
        await supabase.table("kg_entities").update(
            {"is_active": False, "merged_into": primary_entity["id"]}
        ).eq("id", secondary_entity["id"]).execute()

        return {
            "primary_entity_id": primary_entity["id"],
            "archived_entity_id": secondary_entity["id"],
            "merged_properties": merged_properties,
        }

    async def get_conflicts_for_review(
        self,
        expert_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[ConflictStatus] = None,
        conflict_type: Optional[ConflictType] = None,
        limit: int = 50,
    ) -> APIResponse[Dict[str, Any]]:
        """Get conflicts assigned for expert review"""

        supabase = await get_supabase()

        query = supabase.table("conflicts").select("*")

        if status:
            query = query.eq("status", status.value)
        else:
            query = query.in_(
                "status",
                [ConflictStatus.DETECTED.value, ConflictStatus.UNDER_REVIEW.value],
            )

        if severity:
            query = query.eq("severity", severity)

        if expert_id:
            query = query.eq("assigned_to", expert_id)

        if conflict_type:
            query = query.eq("conflict_type", conflict_type.value)

        # Prioritize by severity and assignment
        query = query.order("detected_at", desc=False).limit(limit)

        response = await query.execute()
        conflicts = response.data

        # Enrich with context data
        enriched_conflicts = []
        for conflict in conflicts:
            enriched_conflict = await self._enrich_conflict_with_context(conflict)
            enriched_conflicts.append(enriched_conflict)

        count = (
            await supabase.table("conflicts")
            .select("id", count=CountMethod.estimated, head=True)
            .execute()
        )

        return APIResponse(
            data=enriched_conflicts, count=count.count if count.count else 0
        )

    async def _enrich_conflict_with_context(self, conflict: Dict) -> Dict[str, Any]:
        """Enrich conflict with additional context for expert review"""

        context = await self._get_conflict_context(conflict)
        conflict["context"] = context

        return conflict

    # Helper methods
    def _choose_more_complete_entity(
        self, entity1: Dict, entity2: Dict
    ) -> Tuple[Dict, Dict]:
        """Choose the more complete entity based on various factors"""

        def calculate_completeness_score(entity: Dict) -> float:
            """Calculate completeness score for an entity"""
            score = 0.0

            # Basic properties weight
            props = entity.get("properties", {})
            score += len(props) * 0.1

            # Required fields weight
            required_fields = ["name", "full_name", "title"]
            for field in required_fields:
                if field in props and props[field]:
                    score += 0.3

            # Confidence score weight
            confidence = entity.get("confidence", 0.0)
            score += confidence * 0.4

            # Verification status weight
            if entity.get("is_verified", False):
                score += 0.5

            # Source reliability weight
            source_reliability = entity.get("source_reliability", 0.5)
            score += source_reliability * 0.2

            # Recency weight (more recent is better)
            created_at = entity.get("created_at")
            if created_at:
                try:
                    from datetime import datetime, timedelta

                    created_date = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                    days_old = (datetime.now() - created_date.replace(tzinfo=None)).days
                    recency_score = max(0, 1 - (days_old / 365))  # Decay over a year
                    score += recency_score * 0.3
                except:
                    pass

            return score

        score1 = calculate_completeness_score(entity1)
        score2 = calculate_completeness_score(entity2)

        logger.info(
            f"Entity completeness scores: {entity1.get('id')}={score1:.2f}, {entity2.get('id')}={score2:.2f}"
        )

        if score1 >= score2:
            return entity1, entity2
        else:
            return entity2, entity1

    def _merge_entity_properties(self, props1: Dict, props2: Dict) -> Dict:
        """Merge properties from two entities intelligently"""

        merged = {}
        all_keys = set(props1.keys()) | set(props2.keys())

        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            # If only one has the property, use it
            if val1 is None and val2 is not None:
                merged[key] = val2
            elif val2 is None and val1 is not None:
                merged[key] = val1
            # If both have the property
            elif val1 is not None and val2 is not None:
                # Handle different data types
                if isinstance(val1, str) and isinstance(val2, str):
                    # Choose longer string if significantly different
                    if len(val2) > len(val1) * 1.5:
                        merged[key] = val2
                    elif len(val1) > len(val2) * 1.5:
                        merged[key] = val1
                    else:
                        # Keep the first one if similar length
                        merged[key] = val1

                elif isinstance(val1, list) and isinstance(val2, list):
                    # Merge lists and remove duplicates
                    merged[key] = list(set(val1 + val2))

                elif isinstance(val1, dict) and isinstance(val2, dict):
                    # Recursively merge dictionaries
                    merged[key] = self._merge_entity_properties(val1, val2)

                else:
                    # For other types, prefer non-null values
                    merged[key] = val1 if val1 != "" else val2

        return merged

    async def _transfer_relationships(self, from_entity_id: str, to_entity_id: str):
        """Transfer all relationships from one entity to another"""

        supabase = await get_supabase()

        try:
            # Find all relationships where the entity is source
            source_rels = (
                await supabase.table("kg_relationships")
                .select("*")
                .eq("source_entity_id", from_entity_id)
                .execute()
            )

            # Find all relationships where the entity is target
            target_rels = (
                await supabase.table("kg_relationships")
                .select("*")
                .eq("target_entity_id", from_entity_id)
                .execute()
            )

            # Update source relationships
            for rel in source_rels.data:
                # Check if similar relationship already exists
                similar_rel = (
                    await supabase.table("kg_relationships")
                    .select("*")
                    .eq("source_entity_id", to_entity_id)
                    .eq("target_entity_id", rel["target_entity_id"])
                    .eq("relationship_type", rel["relationship_type"])
                    .execute()
                )

                if not similar_rel.data:
                    # Update the relationship
                    await supabase.table("kg_relationships").update(
                        {"source_entity_id": to_entity_id}
                    ).eq("id", rel["id"]).execute()
                else:
                    # Mark as duplicate and deactivate
                    await supabase.table("kg_relationships").update(
                        {"is_active": False, "merged_into": similar_rel.data[0]["id"]}
                    ).eq("id", rel["id"]).execute()

            # Update target relationships
            for rel in target_rels.data:
                # Check if similar relationship already exists
                similar_rel = (
                    await supabase.table("kg_relationships")
                    .select("*")
                    .eq("source_entity_id", rel["source_entity_id"])
                    .eq("target_entity_id", to_entity_id)
                    .eq("relationship_type", rel["relationship_type"])
                    .execute()
                )

                if not similar_rel.data:
                    # Update the relationship
                    await supabase.table("kg_relationships").update(
                        {"target_entity_id": to_entity_id}
                    ).eq("id", rel["id"]).execute()
                else:
                    # Mark as duplicate and deactivate
                    await supabase.table("kg_relationships").update(
                        {"is_active": False, "merged_into": similar_rel.data[0]["id"]}
                    ).eq("id", rel["id"]).execute()

            logger.info(
                f"Transferred {len(source_rels.data)} source and {len(target_rels.data)} target relationships"
            )

        except Exception as e:
            logger.error(f"Failed to transfer relationships: {e}")
            raise

    async def _keep_source_entity(
        self, conflict_id: str, actions: Dict
    ) -> Dict[str, Any]:
        """Keep source entity and remove/archive target entity"""

        supabase = await get_supabase()

        # Get conflict details
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .single()
            .execute()
        )
        conflict = conflict_response.data

        source_entity_id = conflict["source_entity_id"]
        target_entity_id = conflict["target_entity_id"]

        # Transfer relationships if requested
        if actions.get("preserve_relationships", True):
            await self._transfer_relationships(target_entity_id, source_entity_id)

        # Archive target entity
        await supabase.table("kg_entities").update(
            {
                "is_active": False,
                "superseded_by": source_entity_id,
                "archived_reason": "Conflict resolution - kept source",
            }
        ).eq("id", target_entity_id).execute()

        return {
            "kept_entity_id": source_entity_id,
            "archived_entity_id": target_entity_id,
            "action": "kept_source",
        }

    async def _keep_target_entity(
        self, conflict_id: str, actions: Dict
    ) -> Dict[str, Any]:
        """Keep target entity and remove/archive source entity"""

        supabase = await get_supabase()

        # Get conflict details
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .single()
            .execute()
        )
        conflict = conflict_response.data

        source_entity_id = conflict["source_entity_id"]
        target_entity_id = conflict["target_entity_id"]

        # Transfer relationships if requested
        if actions.get("preserve_relationships", True):
            await self._transfer_relationships(source_entity_id, target_entity_id)

        # Archive source entity
        await supabase.table("kg_entities").update(
            {
                "is_active": False,
                "superseded_by": target_entity_id,
                "archived_reason": "Conflict resolution - kept target",
            }
        ).eq("id", source_entity_id).execute()

        return {
            "kept_entity_id": target_entity_id,
            "archived_entity_id": source_entity_id,
            "action": "kept_target",
        }

    async def _keep_both_entities(
        self, conflict_id: str, actions: Dict
    ) -> Dict[str, Any]:
        """Keep both entities and mark conflict as acceptable"""

        supabase = await get_supabase()

        # Get conflict details
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .single()
            .execute()
        )
        conflict = conflict_response.data

        # Add disambiguation info to both entities if provided
        disambiguation = actions.get("disambiguation", {})

        if disambiguation:
            # Update source entity
            if disambiguation.get("source_context"):
                await supabase.table("kg_entities").update(
                    {"disambiguation_context": disambiguation["source_context"]}
                ).eq("id", conflict["source_entity_id"]).execute()

            # Update target entity
            if disambiguation.get("target_context"):
                await supabase.table("kg_entities").update(
                    {"disambiguation_context": disambiguation["target_context"]}
                ).eq("id", conflict["target_entity_id"]).execute()

        return {
            "source_entity_id": conflict["source_entity_id"],
            "target_entity_id": conflict["target_entity_id"],
            "action": "kept_both",
            "disambiguation_applied": bool(disambiguation),
        }

    async def _create_new_entity(
        self, conflict_id: str, actions: Dict
    ) -> Dict[str, Any]:
        """Create a new entity combining information from conflicting entities"""

        supabase = await get_supabase()

        # Get conflict details
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .single()
            .execute()
        )
        conflict = conflict_response.data

        # Get source and target entities
        source_entity = (
            await supabase.table("kg_entities")
            .select("*")
            .eq("id", conflict["source_entity_id"])
            .single()
            .execute()
        )
        target_entity = (
            await supabase.table("kg_entities")
            .select("*")
            .eq("id", conflict["target_entity_id"])
            .single()
            .execute()
        )

        # Merge properties
        merged_properties = self._merge_entity_properties(
            source_entity.data.get("properties", {}),
            target_entity.data.get("properties", {}),
        )

        # Create new entity
        new_entity_data = {
            "entity_type": source_entity.data["entity_type"],
            "properties": merged_properties,
            "confidence": max(
                source_entity.data.get("confidence", 0.5),
                target_entity.data.get("confidence", 0.5),
            ),
            "is_active": True,
            "created_from_merge": True,
            "source_entities": [
                conflict["source_entity_id"],
                conflict["target_entity_id"],
            ],
        }

        new_entity_response = (
            await supabase.table("kg_entities").insert(new_entity_data).execute()
        )
        new_entity_id = new_entity_response.data[0]["id"]

        # Transfer relationships to new entity
        await self._transfer_relationships(conflict["source_entity_id"], new_entity_id)
        await self._transfer_relationships(conflict["target_entity_id"], new_entity_id)

        # Archive old entities
        await supabase.table("kg_entities").update(
            {
                "is_active": False,
                "superseded_by": new_entity_id,
                "archived_reason": "Conflict resolution - merged into new entity",
            }
        ).eq("id", conflict["source_entity_id"]).execute()

        await supabase.table("kg_entities").update(
            {
                "is_active": False,
                "superseded_by": new_entity_id,
                "archived_reason": "Conflict resolution - merged into new entity",
            }
        ).eq("id", conflict["target_entity_id"]).execute()

        return {
            "new_entity_id": new_entity_id,
            "archived_entities": [
                conflict["source_entity_id"],
                conflict["target_entity_id"],
            ],
            "action": "created_new",
        }

    async def _assign_for_manual_review(self, conflict_id: str):
        """Assign conflict for manual expert review"""

        supabase = await get_supabase()

        # Find available expert (simple round-robin or by workload)
        experts_response = (
            await supabase.table("users")
            .select("id")
            .eq("role", "expert")
            .eq("is_active", True)
            .execute()
        )

        if experts_response.data:
            # Simple assignment to first available expert
            # In production, you'd want more sophisticated load balancing
            expert_id = experts_response.data[0]["id"]

            await supabase.table("conflicts").update(
                {
                    "status": ConflictStatus.UNDER_REVIEW.value,
                    "assigned_expert_id": expert_id,
                    "assigned_at": datetime.now().isoformat(),
                }
            ).eq("id", str(conflict_id)).execute()

            logger.info(f"Assigned conflict {conflict_id} to expert {expert_id}")

    async def _update_conflict_status(
        self,
        conflict_id: str,
        status: ConflictStatus,
        resolution: Optional[ConflictResolution] = None,
    ):
        """Update conflict status and resolution data"""

        supabase = await get_supabase()

        update_data: Dict[str, Any] = {
            "status": status.value,
            "updated_at": datetime.now().isoformat(),
        }

        if resolution:
            update_data["resolution_data"] = resolution.model_dump()
            update_data["resolved_at"] = datetime.now().isoformat()

        await supabase.table("conflicts").update(update_data).eq(
            "id", str(conflict_id)
        ).execute()

        logger.info(f"Updated conflict {conflict_id} status to {status.value}")

    async def _validate_expert_permissions(self, expert_id: str) -> bool:
        """Validate that user has expert permissions"""

        supabase = await get_supabase()

        try:
            user_response = (
                await supabase.table("users")
                .select("role, permissions")
                .eq("id", expert_id)
                .single()
                .execute()
            )

            user = user_response.data
            if not user:
                return False

            # Check role
            if user.get("role") in ["expert", "admin"]:
                return True

            # Check specific permissions
            permissions = user.get("permissions", [])
            return "quality:expert" in permissions

        except Exception as e:
            logger.error(f"Failed to validate expert permissions: {e}")
            return False

    def _fallback_parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Fallback parsing when JSON extraction fails"""

        suggestions = []

        # Try to extract structured information using regex patterns
        method_pattern = r"(?:method|resolution)[:\s]+(\w+)"
        confidence_pattern = r"(?:confidence)[:\s]+([\d.]+)"
        reasoning_pattern = r"(?:reasoning|reason)[:\s]+([^\n]+)"

        methods = re.findall(method_pattern, response, re.IGNORECASE)
        confidences = re.findall(confidence_pattern, response)
        reasonings = re.findall(reasoning_pattern, response, re.IGNORECASE)

        # Create basic suggestions from extracted patterns
        for i, method in enumerate(methods):
            suggestion = {
                "resolution_method": method.lower(),
                "confidence": float(confidences[i]) if i < len(confidences) else 0.5,
                "reasoning": (
                    reasonings[i].strip()
                    if i < len(reasonings)
                    else f"Apply {method} resolution"
                ),
                "actions": {},
            }
            suggestions.append(suggestion)

        # If no patterns found, create a generic suggestion
        if not suggestions:
            suggestions.append(
                {
                    "resolution_method": "manual_review",
                    "confidence": 0.3,
                    "reasoning": "Unable to parse AI response, requires manual review",
                    "actions": {},
                }
            )

        return suggestions
