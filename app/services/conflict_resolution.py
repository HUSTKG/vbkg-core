import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.core.llm_client import get_llm_client
from app.core.supabase import get_supabase
from app.schemas.conflict_resolution import (ConflictResolution,
                                             ConflictStatus, ConflictType,
                                             ResolutionMethod)
from app.services.knowledge_graph import KnowledgeGraphService

logger = logging.getLogger(__name__)


class ConflictResolutionService:
    """Service for resolving conflicts using AI assistance and expert input"""

    def __init__(self):
        self.kg_service = KnowledgeGraphService()
        self.llm_client = get_llm_client()

    async def resolve_conflict_automatically(
        self, conflict_id: str, use_ai: bool = True, confidence_threshold: float = 0.95
    ) -> Dict[str, Any]:
        """Attempt to resolve conflict automatically using AI"""

        supabase = await get_supabase()

        # Get conflict details
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .maybe_single()
            .execute()
        )

        if not conflict_response or not conflict_response.data:
            raise ValueError(f"Conflict {conflict_id} not found")

        conflict = conflict_response.data

        # Skip one that has auto_resolution_suggestions
        if conflict.get("auto_resolution_suggestions"):
            logger.info(f"Conflict {conflict_id} already has AI suggestions")

        # Generate AI resolution suggestions
        if use_ai and not conflict.get("auto_resolution_suggestions"):
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
            response = await self.llm_client.chat_completion(
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
                response_format={"type": "json_object"},
            )

            return self._parse_ai_response(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"AI resolution generation failed: {e}")
            return []

    def _create_resolution_prompt(self, conflict: Dict, context: Dict) -> str:
        """Create structured prompt for AI conflict resolution"""

        conflict_type = conflict["conflict_type"]
        conflict_id = conflict["id"]

        base_prompt = f"""
    Bạn là chuyên gia AI trong quản lý chất lượng đồ thị tri thức. Nhiệm vụ của bạn là phân tích xung đột và đưa ra các gợi ý giải quyết cụ thể, có thể thực thi được.

    CHI TIẾT XUNG ĐỘT:
    - ID: {conflict_id}
    - Loại: {conflict_type}
    - Mức độ nghiêm trọng: {conflict["severity"]}
    - Mô tả: {conflict["description"]}
    - Độ tin cậy phát hiện: {conflict["confidence_score"]}
    - Entity nguồn: {conflict.get("source_entity_id", "N/A")}
    - Entity đích: {conflict.get("target_entity_id", "N/A")}

    DỮ LIỆU BỐI CẢNH:
    {json.dumps(context, indent=2, ensure_ascii=False)}

    PHƯƠNG PHÁP GIẢI QUYẾT KHẠC VỠI:
    - merge_entities: Gộp các entity trùng lặp
    - keep_source: Giữ entity nguồn, xóa entity đích  
    - keep_target: Giữ entity đích, xóa entity nguồn
    - keep_both: Giữ cả hai entity (có thể thêm disambiguation)
    - create_new: Tạo entity mới từ thông tin của cả hai
    - delete_conflicting: Xóa các phần tử gây xung đột
    - manual_edit: Chỉnh sửa thủ công theo hướng dẫn cụ thể
    - ai_resolution: Để AI tự động xử lý

    NHIỆM VỤ:
    Đưa ra 1-3 gợi ý giải quyết theo định dạng JSON chính xác sau đây. Mỗi gợi ý phải bao gồm:

    1. resolution_method: Một trong các phương pháp trên
    2. reasoning: Lý do chi tiết (ít nhất 50 ký tự)
    3. confidence: Điểm tin cậy từ 0.0 đến 1.0
    4. actions: Object chứa các hành động cụ thể cần thực hiện

    ĐỊNH DẠNG PHẢN HỒI BẮT BUỘC:
    ```json
    [
      {{
        "resolution_method": "merge_entities",
        "reasoning": "Lý do chi tiết tại sao chọn phương pháp này...",
        "confidence": 0.85,
        "actions": {{
          "merge_strategy": "prefer_more_complete",
          "preserve_all_relationships": true,
          "target_entity_id": "entity_id_to_keep",
          "additional_data": {{}}
        }}
      }}
    ]
    ```
    """

        # Add type-specific guidance
        if conflict_type == "duplicate_entity":
            base_prompt += """

    HƯỚNG DẪN CHO DUPLICATE_ENTITY:
    - Ưu tiên merge_entities nếu độ tương đồng cao (>0.8)
    - Sử dụng keep_source/keep_target nếu một entity rõ ràng tốt hơn
    - Actions cho merge_entities phải bao gồm:
      * merge_strategy: "prefer_more_complete", "prefer_source", "prefer_target"
      * preserve_all_relationships: true/false
      * target_entity_id: ID entity sẽ được giữ lại

    VÍ DỤ ACTIONS CHO MERGE_ENTITIES:
    ```json
    {
      "merge_strategy": "prefer_more_complete",
      "preserve_all_relationships": true,
      "target_entity_id": "uuid-of-target-entity",
      "merge_rules": {
        "name": "prefer_longer",
        "description": "combine",
        "properties": "merge_non_conflicting"
      }
    }
    ```

    VÍ DỤ ACTIONS CHO KEEP_SOURCE/KEEP_TARGET:
    ```json
    {
      "preserve_relationships": true,
      "archive_reason": "Lower quality data",
      "transfer_unique_properties": true
    }
    ```
    """

        elif conflict_type == "contradictory_relationship":
            base_prompt += """

    HƯỚNG DẪN CHO CONTRADICTORY_RELATIONSHIP:
    - Xem xét temporal context (thời gian nào gần đây hơn)
    - Đánh giá độ tin cậy nguồn dữ liệu
    - Có thể keep_both nếu cả hai đều đúng trong context khác nhau

    VÍ DỤ ACTIONS CHO DELETE_CONFLICTING:
    ```json
    {
      "delete_relationship_ids": ["rel_id_1", "rel_id_2"],
      "delete_reason": "Contradictory temporal information",
      "preserve_entities": true
    }
    ```

    VÍ DỤ ACTIONS CHO CREATE_NEW:
    ```json
    {
      "new_relationship_type": "works_at_period",
      "relationship_properties": {
        "start_date": "2020-01-01",
        "end_date": "2023-12-31",
        "position": "Software Engineer"
      },
      "replace_existing": ["old_rel_id_1"]
    }
    ```
    """

        elif conflict_type == "attribute_mismatch":
            base_prompt += """

    HƯỚNG DẪN CHO ATTRIBUTE_MISMATCH:
    - Ưu tiên nguồn dữ liệu đáng tin cậy hơn
    - Xem xét độ mới của thông tin
    - Có thể manual_edit nếu cần merge giá trị

    VÍ DỤ ACTIONS CHO MANUAL_EDIT:
    ```json
    {
      "attribute_updates": [
        {
          "entity_id": "entity_uuid",
          "attribute_name": "company_name", 
          "new_value": "Corrected Company Name",
          "update_reason": "Merged from reliable sources"
        }
      ]
    }
    ```
    """

        elif conflict_type == "temporal_conflict":
            base_prompt += """

    HƯỚNG DẪN CHO TEMPORAL_CONFLICT:
    - Sắp xếp lại timeline theo thứ tự logic
    - Ưu tiên thông tin gần đây và đáng tin cậy
    - Có thể tạo periods riêng biệt nếu cần

    VÍ DỤ ACTIONS CHO MANUAL_EDIT:
    ```json
    {
      "timeline_corrections": [
        {
          "event_id": "event_uuid",
          "corrected_date": "2023-06-15",
          "confidence": 0.9,
          "source_priority": "high"
        }
      ],
      "create_temporal_periods": true
    }
    ```
    """

        elif conflict_type == "missing_relationship":
            base_prompt += """

    HƯỚNG DẪN CHO MISSING_RELATIONSHIP:
    - Sử dụng create_new để tạo relationship bị thiếu
    - Xác định chính xác loại relationship cần tạo

    VÍ DỤ ACTIONS CHO CREATE_NEW:
    ```json
    {
      "create_relationships": [
        {
          "source_entity_id": "entity1_uuid",
          "target_entity_id": "entity2_uuid", 
          "relationship_type": "works_at",
          "properties": {
            "start_date": "2023-01-01",
            "position": "Engineer"
          },
          "confidence": 0.8
        }
      ]
    }
    ```
    """

        elif conflict_type == "source_conflict":
            base_prompt += """

    HƯỚNG DẪN CHO SOURCE_CONFLICT:
    - Ưu tiên nguồn có độ tin cậy cao hơn
    - Xem xét độ mới của dữ liệu
    - Có thể keep_both nếu từ nguồn khác nhau hợp lệ

    VÍ DỤ ACTIONS CHO KEEP_SOURCE:
    ```json
    {
      "source_priority_reason": "Higher reliability score",
      "preserve_source_metadata": true,
      "archive_conflicting_data": true
    }
    ```
    """

        elif conflict_type == "schema_mismatch":
            base_prompt += """

    HƯỚNG DẪN CHO SCHEMA_MISMATCH:
    - Sử dụng manual_edit để chuẩn hóa schema
    - Có thể ai_resolution cho auto-transformation

    VÍ DỤ ACTIONS CHO MANUAL_EDIT:
    ```json
    {
      "schema_transformations": [
        {
          "entity_id": "entity_uuid",
          "transform_type": "normalize_properties",
          "mapping_rules": {
            "old_field": "new_field",
            "company": "organization_name"
          }
        }
      ]
    }
    ```
    """

        base_prompt += """

    LƯU Ý QUAN TRỌNG:
    1. Phản hồi PHẢI là JSON array hợp lệ
    2. Mỗi resolution_method phải thuộc danh sách cho phép
    3. Confidence phải từ 0.0 đến 1.0
    4. Reasoning phải ít nhất 50 ký tự và giải thích cụ thể
    5. Actions phải chứa thông tin đủ để thực thi
    6. Không được thêm text nào ngoài JSON array

    BẮT ĐẦU PHẢN HỒI JSON:"""

        return base_prompt

    def _parse_ai_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured suggestions"""

        try:
            # Clean the response - remove any markdown formatting
            cleaned_response = response.strip()

            # Remove markdown code blocks if present
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            cleaned_response = cleaned_response.strip()

            # Try to find JSON array in the response
            import re

            json_match = re.search(r"\[.*?\]", cleaned_response, re.DOTALL)

            if json_match:
                json_str = json_match.group()
                suggestions = json.loads(json_str)

                # Validate and clean each suggestion
                validated_suggestions = []
                valid_methods = [
                    "merge_entities",
                    "keep_source",
                    "keep_target",
                    "keep_both",
                    "create_new",
                    "delete_conflicting",
                    "manual_edit",
                    "ai_resolution",
                ]

                for suggestion in suggestions:
                    if not isinstance(suggestion, dict):
                        continue

                    # Validate required fields
                    if "resolution_method" not in suggestion:
                        continue
                    if suggestion["resolution_method"] not in valid_methods:
                        continue
                    if (
                        "reasoning" not in suggestion
                        or len(suggestion["reasoning"]) < 10
                    ):
                        continue
                    if "confidence" not in suggestion:
                        suggestion["confidence"] = 0.5
                    if "actions" not in suggestion:
                        suggestion["actions"] = {}

                    # Ensure confidence is in valid range
                    confidence = float(suggestion["confidence"])
                    if confidence < 0.0:
                        confidence = 0.0
                    elif confidence > 1.0:
                        confidence = 1.0
                    suggestion["confidence"] = confidence

                    validated_suggestions.append(suggestion)

                if validated_suggestions:
                    logger.info(
                        f"Successfully parsed {len(validated_suggestions)} AI suggestions"
                    )
                    return validated_suggestions
                else:
                    logger.warning("No valid suggestions found in AI response")

            else:
                logger.warning("No JSON array found in AI response")

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")

        # Fallback to more robust parsing
        return self._fallback_parse_response(response)

    def _fallback_parse_response(self, response: str) -> List[Dict[str, Any]]:
        """Enhanced fallback parsing when JSON extraction fails"""

        suggestions = []

        try:
            # Try to extract method and reasoning patterns
            lines = response.split("\n")
            current_suggestion = {}

            for line in lines:
                line = line.strip()

                # Look for resolution method
                method_match = re.search(
                    r'(?:resolution_method|method)["\s]*[:=]["\s]*(\w+)',
                    line,
                    re.IGNORECASE,
                )
                if method_match:
                    method = method_match.group(1).lower()
                    valid_methods = [
                        "merge_entities",
                        "keep_source",
                        "keep_target",
                        "keep_both",
                        "create_new",
                        "delete_conflicting",
                        "manual_edit",
                        "ai_resolution",
                    ]
                    if method in valid_methods:
                        if current_suggestion:
                            suggestions.append(current_suggestion)
                        current_suggestion = {"resolution_method": method}

                # Look for confidence
                conf_match = re.search(
                    r'(?:confidence)["\s]*[:=]["\s]*([\d.]+)', line, re.IGNORECASE
                )
                if conf_match and current_suggestion:
                    try:
                        confidence = float(conf_match.group(1))
                        current_suggestion["confidence"] = max(
                            0.0, min(1.0, confidence)
                        )
                    except:
                        current_suggestion["confidence"] = 0.5

                # Look for reasoning
                reason_match = re.search(
                    r'(?:reasoning|reason)["\s]*[:=]["\s]*(.+)', line, re.IGNORECASE
                )
                if reason_match and current_suggestion:
                    reasoning = reason_match.group(1).strip('"').strip()
                    if len(reasoning) > 10:
                        current_suggestion["reasoning"] = reasoning

            # Add the last suggestion
            if current_suggestion:
                suggestions.append(current_suggestion)

            # Fill in missing required fields
            for suggestion in suggestions:
                if "reasoning" not in suggestion:
                    method = suggestion.get("resolution_method", "manual_edit")
                    suggestion["reasoning"] = (
                        f"Áp dụng phương pháp {method} để giải quyết xung đột này dựa trên phân tích dữ liệu"
                    )

                if "confidence" not in suggestion:
                    suggestion["confidence"] = 0.3  # Low confidence for fallback

                if "actions" not in suggestion:
                    suggestion["actions"] = {}

            if suggestions:
                logger.info(
                    f"Fallback parsing extracted {len(suggestions)} suggestions"
                )
                return suggestions

        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}")

        # Last resort - create a manual review suggestion
        logger.warning("Creating manual review suggestion as last resort")
        return [
            {
                "resolution_method": "manual_edit",
                "reasoning": "AI không thể phân tích xung đột này tự động, cần chuyên gia xem xét và đưa ra hướng dẫn cụ thể để giải quyết",
                "confidence": 0.2,
                "actions": {
                    "requires_expert_review": True,
                    "analysis_failed": True,
                    "suggested_action": "Manual review and resolution required",
                },
            }
        ]

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
                .maybe_single()
                .execute()
            )

            if entity_response and entity_response.data:
                context["source_entity"] = entity_response.data

        if conflict.get("target_entity_id"):
            entity_response = (
                await supabase.table("kg_entities")
                .select("*")
                .eq("id", conflict["target_entity_id"])
                .maybe_single()
                .execute()
            )
            if entity_response and entity_response.data:
                context["target_entity"] = entity_response.data

        # Get relationship details if involved
        if conflict.get("source_relationship_id"):
            rel_response = (
                await supabase.table("kg_relationships")
                .select("*")
                .eq("id", conflict["source_relationship_id"])
                .maybe_single()
                .execute()
            )
            if rel_response and rel_response.data:
                context["source_relationship"] = rel_response.data

        # Get source document information
        if context.get("source_entity"):
            source_doc_id = context["source_entity"].get("source_document_id")
            if source_doc_id:
                doc_response = (
                    await supabase.table("file_uploads")
                    .select("*")
                    .eq("id", source_doc_id)
                    .maybe_single()
                    .execute()
                )
                if doc_response and doc_response.data:
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
        """Apply the specified resolution to the conflict using KG service"""

        method = resolution_data.get("resolution_method")
        actions = resolution_data.get("actions", {})

        try:
            if method == ResolutionMethod.MERGE_ENTITIES:
                result = await self._merge_entities_via_kg_service(conflict_id, actions, resolved_by)
            elif method == ResolutionMethod.KEEP_SOURCE:
                result = await self._keep_source_entity_via_kg_service(conflict_id, actions, resolved_by)
            elif method == ResolutionMethod.KEEP_TARGET:
                result = await self._keep_target_entity_via_kg_service(conflict_id, actions, resolved_by)
            elif method == ResolutionMethod.KEEP_BOTH:
                result = await self._keep_both_entities(conflict_id, actions)
            elif method == ResolutionMethod.CREATE_NEW:
                result = await self._create_new_entity_via_kg_service(conflict_id, actions, resolved_by)
            elif method == ResolutionMethod.DELETE_CONFLICTING:
                result = await self._delete_conflicting_via_kg_service(conflict_id, actions, resolved_by)
            elif method == ResolutionMethod.MANUAL_EDIT:
                result = await self._manual_edit_via_kg_service(conflict_id, actions, resolved_by)
            else:
                raise ValueError(f"Unknown resolution method: {method}")

            # Update conflict status
            resolution = ConflictResolution(
                resolution_method=method,
                resolution_data=actions,
                reasoning=resolution_data.get("reasoning", ""),
                confidence_score=resolution_data.get("confidence"),
                resolved_by=resolved_by if resolved_by != "ai_system" else None,
                resolution_timestamp=datetime.now().isoformat(),
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

    async def _merge_entities_via_kg_service(
        self, conflict_id: str, actions: Dict, resolved_by: str
    ) -> Dict[str, Any]:
        """Merge two conflicting entities using KG service"""

        supabase = await get_supabase()
        
        # Get conflict details
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .maybe_single()
            .execute()
        )

        if not conflict_response or not conflict_response.data:
            raise ValueError(f"Conflict {conflict_id} not found")

        conflict = conflict_response.data
        source_entity_id = conflict["source_entity_id"]
        target_entity_id = conflict["target_entity_id"]

        # Get entity details
        source_entity = await self.kg_service.get_entity(source_entity_id, include_relationships=True)
        target_entity = await self.kg_service.get_entity(target_entity_id, include_relationships=True)

        if not source_entity or not target_entity:
            raise ValueError("One or both entities not found")

        # Determine merge strategy
        merge_strategy = actions.get("merge_strategy", "prefer_more_complete")

        if merge_strategy == "prefer_more_complete":
            primary_entity, secondary_entity = self._choose_more_complete_entity(
                source_entity, target_entity
            )
        elif merge_strategy == "prefer_source":
            primary_entity, secondary_entity = source_entity, target_entity
        elif merge_strategy == "prefer_target":
            primary_entity, secondary_entity = target_entity, source_entity
        else:
            primary_entity, secondary_entity = source_entity, target_entity

        # Merge properties
        merged_properties = self._merge_entity_properties(
            primary_entity.get("properties", {}), 
            secondary_entity.get("properties", {})
        )

        # Update primary entity through KG service
        update_data = {
            "id": primary_entity["id"],
            "properties": merged_properties,
            "confidence": max(
                primary_entity.get("confidence", 0.5),
                secondary_entity.get("confidence", 0.5),
            ),
        }

        updated_entity = await self.kg_service._update_entity(update_data, resolved_by)

        # Delete secondary entity through KG service (this will handle Neo4j too)
        await self.kg_service._delete_entity(secondary_entity["id"], resolved_by)

        return {
            "primary_entity_id": primary_entity["id"],
            "deleted_entity_id": secondary_entity["id"],
            "merged_properties": merged_properties,
            "updated_entity": updated_entity,
        }

    async def _keep_source_entity_via_kg_service(
        self, conflict_id: str, actions: Dict, resolved_by: str
    ) -> Dict[str, Any]:
        """Keep source entity and delete target using KG service"""

        supabase = await get_supabase()

        # Get conflict details
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .maybe_single()
            .execute()
        )
        
        if not conflict_response or not conflict_response.data:
            raise ValueError(f"Conflict {conflict_id} not found")
        
        conflict = conflict_response.data
        source_entity_id = conflict["source_entity_id"]
        target_entity_id = conflict["target_entity_id"]

        # Delete target entity using KG service (handles both PostgreSQL and Neo4j)
        await self.kg_service._delete_entity(target_entity_id, resolved_by)

        return {
            "kept_entity_id": source_entity_id,
            "deleted_entity_id": target_entity_id,
            "action": "kept_source",
        }

    async def _keep_target_entity_via_kg_service(
        self, conflict_id: str, actions: Dict, resolved_by: str
    ) -> Dict[str, Any]:
        """Keep target entity and delete source using KG service"""

        supabase = await get_supabase()

        # Get conflict details
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .maybe_single()
            .execute()
        )
        
        if not conflict_response or not conflict_response.data:
            raise ValueError(f"Conflict {conflict_id} not found")
        
        conflict = conflict_response.data
        source_entity_id = conflict["source_entity_id"]
        target_entity_id = conflict["target_entity_id"]

        # Delete source entity using KG service (handles both PostgreSQL and Neo4j)
        await self.kg_service._delete_entity(source_entity_id, resolved_by)

        return {
            "kept_entity_id": target_entity_id,
            "deleted_entity_id": source_entity_id,
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
            .maybe_single()
            .execute()
        )
        
        if not conflict_response or not conflict_response.data:
            raise ValueError(f"Conflict {conflict_id} not found")
        
        conflict = conflict_response.data

        # Add disambiguation info to both entities if provided
        disambiguation = actions.get("disambiguation", {})

        if disambiguation:
            # Update source entity
            if disambiguation.get("source_context"):
                source_update = {
                    "id": conflict["source_entity_id"],
                    "properties": {"disambiguation_context": disambiguation["source_context"]}
                }
                await self.kg_service._update_entity(source_update, "system")

            # Update target entity
            if disambiguation.get("target_context"):
                target_update = {
                    "id": conflict["target_entity_id"],
                    "properties": {"disambiguation_context": disambiguation["target_context"]}
                }
                await self.kg_service._update_entity(target_update, "system")

        return {
            "source_entity_id": conflict["source_entity_id"],
            "target_entity_id": conflict["target_entity_id"],
            "action": "kept_both",
            "disambiguation_applied": bool(disambiguation),
        }

    async def _create_new_entity_via_kg_service(
        self, conflict_id: str, actions: Dict, resolved_by: str
    ) -> Dict[str, Any]:
        """Create a new entity combining information from conflicting entities"""

        supabase = await get_supabase()

        # Get conflict details
        conflict_response = (
            await supabase.table("conflicts")
            .select("*")
            .eq("id", str(conflict_id))
            .maybe_single()
            .execute()
        )
        
        if not conflict_response or not conflict_response.data:
            raise ValueError(f"Conflict {conflict_id} not found")
        
        conflict = conflict_response.data

        # Get source and target entities
        source_entity = await self.kg_service.get_entity(conflict["source_entity_id"])
        target_entity = await self.kg_service.get_entity(conflict["target_entity_id"])

        if not source_entity or not target_entity:
            raise ValueError("One or both entities not found")

        # Merge properties
        merged_properties = self._merge_entity_properties(
            source_entity.get("properties", {}),
            target_entity.get("properties", {}),
        )

        # Create new entity data
        new_entity_data = {
            "entity_text": actions.get("entity_text", source_entity["entity_text"]),
            "entity_type": source_entity["entity_type"],
            "properties": merged_properties,
            "confidence": max(
                source_entity.get("confidence", 0.5),
                target_entity.get("confidence", 0.5),
            ),
            "source_document_id": source_entity.get("source_document_id"),
            "is_verified": False,
        }

        # Create new entity using KG service
        new_entity = await self.kg_service._create_entity(new_entity_data, resolved_by)
        new_entity_id = new_entity["id"]

        # Delete old entities using KG service
        await self.kg_service._delete_entity(conflict["source_entity_id"], resolved_by)
        await self.kg_service._delete_entity(conflict["target_entity_id"], resolved_by)

        return {
            "new_entity_id": new_entity_id,
            "new_entity": new_entity,
            "deleted_entities": [
                conflict["source_entity_id"],
                conflict["target_entity_id"],
            ],
            "action": "created_new",
        }

    async def _delete_conflicting_via_kg_service(
        self, conflict_id: str, actions: Dict, resolved_by: str
    ) -> Dict[str, Any]:
        """Delete conflicting relationships or entities"""

        supabase = await get_supabase()
        deleted_items = []

        # Delete relationships if specified
        if "delete_relationship_ids" in actions:
            for rel_id in actions["delete_relationship_ids"]:
                # Get relationship details first
                rel_response = (
                    await supabase.table("kg_relationships")
                    .select("*")
                    .eq("id", rel_id)
                    .maybe_single()
                    .execute()
                )
                
                if rel_response and rel_response.data:
                    # Soft delete relationship in PostgreSQL
                    await supabase.table("kg_relationships").update(
                        {
                            "is_active": False,
                            "deleted_at": datetime.now().isoformat(),
                            "deleted_by": resolved_by,
                            "deleted_reason": actions.get("delete_reason", "Conflict resolution")
                        }
                    ).eq("id", rel_id).execute()

                    # Delete from Neo4j if neo4j_id exists
                    relationship = rel_response.data
                    if relationship.get("neo4j_id"):
                        from app.utils.neo4j import get_neo4j_driver
                        neo4j_driver = get_neo4j_driver()
                        
                        async with neo4j_driver.session() as session:
                            await session.run(
                                "MATCH ()-[r]->() WHERE id(r) = $neo4j_id DELETE r",
                                {"neo4j_id": int(relationship["neo4j_id"])}
                            )

                    deleted_items.append({"type": "relationship", "id": rel_id})

        # Delete entities if specified
        if "delete_entity_ids" in actions:
            for entity_id in actions["delete_entity_ids"]:
                await self.kg_service._delete_entity(entity_id, resolved_by)
                deleted_items.append({"type": "entity", "id": entity_id})

        return {
            "deleted_items": deleted_items,
            "delete_reason": actions.get("delete_reason", "Conflict resolution"),
            "action": "deleted_conflicting"
        }

    async def _manual_edit_via_kg_service(
        self, conflict_id: str, actions: Dict, resolved_by: str
    ) -> Dict[str, Any]:
        """Apply manual edits to entities or relationships"""

        updated_items = []

        # Update entities if specified
        if "attribute_updates" in actions:
            for update in actions["attribute_updates"]:
                entity_id = update["entity_id"]
                
                # Get current entity
                entity = await self.kg_service.get_entity(entity_id)
                if not entity:
                    continue

                # Prepare update data
                current_props = entity.get("properties", {})
                current_props[update["attribute_name"]] = update["new_value"]

                update_data = {
                    "id": entity_id,
                    "properties": current_props
                }

                # Update using KG service
                updated_entity = await self.kg_service._update_entity(update_data, resolved_by)
                updated_items.append({
                    "type": "entity", 
                    "id": entity_id, 
                    "update": update,
                    "updated_entity": updated_entity
                })

        # Update relationships if specified
        if "relationship_updates" in actions:
            supabase = await get_supabase()
            
            for update in actions["relationship_updates"]:
                rel_id = update["relationship_id"]
                
                # Update relationship properties
                current_rel = (
                    await supabase.table("kg_relationships")
                    .select("*")
                    .eq("id", rel_id)
                    .maybe_single()
                    .execute()
                )
                
                if current_rel and current_rel.data:
                    current_props = current_rel.data.get("properties", {})
                    current_props.update(update.get("new_properties", {}))
                    
                    # Update in PostgreSQL
                    await supabase.table("kg_relationships").update(
                        {
                            "properties": current_props,
                            "updated_at": datetime.now().isoformat(),
                            "updated_by": resolved_by
                        }
                    ).eq("id", rel_id).execute()

                    # Update in Neo4j if exists
                    relationship = current_rel.data
                    if relationship.get("neo4j_id"):
                        from app.utils.neo4j import get_neo4j_driver
                        neo4j_driver = get_neo4j_driver()
                        
                        async with neo4j_driver.session() as session:
                            await session.run(
                                """
                                MATCH ()-[r]->() WHERE id(r) = $neo4j_id
                                SET r.properties = $properties
                                """,
                                {
                                    "neo4j_id": int(relationship["neo4j_id"]),
                                    "properties": json.dumps(current_props)
                                }
                            )

                    updated_items.append({
                        "type": "relationship",
                        "id": rel_id,
                        "update": update
                    })

        # Create new relationships if specified
        if "create_relationships" in actions:
            for rel_data in actions["create_relationships"]:
                new_relationship = await self.kg_service._create_relationship(rel_data, resolved_by)
                updated_items.append({
                    "type": "new_relationship",
                    "relationship": new_relationship
                })

        return {
            "updated_items": updated_items,
            "action": "manual_edit",
            "total_updates": len(updated_items)
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

    async def _assign_for_manual_review(self, conflict_id: str):
        """Assign conflict for manual expert review"""

        from app.services.user import UserService

        user_service = UserService()
        supabase = await get_supabase()

        # Find available expert (simple round-robin or by workload)
        experts_response = await user_service.get_users(role_filter="expert")

        if experts_response.data:
            # Simple assignment to first available expert
            # In production, you'd want more sophisticated load balancing
            expert_id = experts_response.data[0]["id"]

            await supabase.table("conflicts").update(
                {
                    "status": ConflictStatus.UNDER_REVIEW.value,
                    "assigned_to": expert_id,
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
