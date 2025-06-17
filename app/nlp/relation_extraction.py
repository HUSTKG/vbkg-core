import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.llm_client import get_llm_client
from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)

class RelationshipExtractionService:
    """
    Simplified relationship extraction service focusing on extraction with basic processing
    """

    def __init__(self):
        # Initialize OpenAI client
        self.llm_client = get_llm_client()

    async def extract_relationships(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        domain: Optional[str] = None,
        user_id: Optional[str] = None,
        auto_save: bool = True,
    ) -> Dict[str, Any]:
        """
        Extract relationships between entities using LLM with basic processing

        Args:
            text: Input text (Vietnamese)
            entities: List of extracted entities
            domain: Domain to focus on
            user_id: User ID for tracking changes
            auto_save: Whether to automatically save results to database

        Returns:
            Dictionary containing extracted relationships
        """
        try:
            # Use LLM for extraction
            relationships = await self._extract_relationships_with_llm(
                text, entities, domain
            )

            logger.info(f"Extracted {len(relationships)} relationships using LLM")

            # Basic deduplication
            deduplicated_relationships = self._deduplicate_relationships(relationships)

            logger.info(f"Deduplicated relationships: {len(deduplicated_relationships)}")

            # Auto-save results if requested
            saved_relationship_ids = []
            if auto_save and deduplicated_relationships:
                logger.info(
                    "Auto-saving relationships - requires extraction_result_id from entity extraction"
                )

            return {
                "relationships": deduplicated_relationships,
                "extraction_method": "llm_basic",
                "relationship_count": len(deduplicated_relationships),
                "saved_relationship_ids": saved_relationship_ids,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in relationship extraction: {e}")
            raise Exception(
                    "An error occurred during relationship extraction. Please try again later."
                                )

    async def _extract_relationships_with_llm(
        self, text: str, entities: List[Dict[str, Any]], domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract ALL possible relationships using LLM
        """
        if not self.llm_client:
            return []

        try:
            # Prepare entity information
            entity_info = []
            for i, entity in enumerate(entities):
                entity_text = entity.get("text", entity.get("entity_text", ""))
                entity_type = entity.get("entity_type", "Unknown")
                entity_id = entity.get("id", f"entity_{i}")

                entity_info.append(
                    f'Entity_{i+1} [ID: {entity_id}]: "{entity_text}" (Type: {entity_type})'
                )

            entity_list = "\n".join(entity_info)

            system_prompt = f"""
            Bạn là một hệ thống trích xuất MỐI QUAN HỆ chuyên nghiệp cho tiếng Việt.
            
            MỤC TIÊU: Trích xuất TẤT CẢ mối quan hệ giữa các thực thể.
            
            HƯỚNG DẪN TRÍCH XUẤT:
            1. **Extract mọi mối quan hệ**: Tìm tất cả kết nối giữa các thực thể
            2. **Tự đặt tên relationship type**: Tự đặt tên relationship type phù hợp
            3. **Only entity-to-entity**: CHỈ quan hệ giữa 2 thực thể, không phải thuộc tính của 1 thực thể
            4. **Clear evidence**: Phải có bằng chứng rõ ràng trong văn bản
            
            Các loại mối quan hệ thường gặp (có thể mở rộng):
            **Ngân hàng:**
            - hasAccount (có tài khoản), isCustomerOf (là khách hàng của)
            - transfersTo (chuyển tiền cho), borrowsFrom (vay từ)
            - providesServiceTo (cung cấp dịch vụ), manages (quản lý)
            - ownsCard (sở hữu thẻ), appliesFor (đăng ký)
            
            **Tổ chức:**
            - worksFor (làm việc cho), employs (tuyển dụng)
            - partnersWith (hợp tác với), competesWith (cạnh tranh với)
            - subsidiaryOf (là công ty con), owns (sở hữu)
            
            **Địa lý:**
            - locatedIn (nằm trong), adjacentTo (liền kề)
            - serves (phục vụ khu vực), operatesIn (hoạt động tại)
            
            **Thời gian:**
            - happensBefore/After (xảy ra trước/sau)
            - validDuring (có hiệu lực trong)
            
            **Tài chính:**
            - guarantees (bảo lãnh), secures (thế chấp)
            - inheritsFrom (thừa kế từ), donatesTo (quyên góp cho)
            
            ⭐ QUAN TRỌNG: Hãy tự tạo relationship type mới nếu cần thiết!
            
            VÍ DỤ SAI (datatype properties):
            - "Nguyễn Văn A có tên là Nguyễn Văn A" ← SAI
            - "Tài khoản có số 123456" ← SAI
            
            VÍ DỤ ĐÚNG (object properties):
            - "Nguyễn Văn A có tài khoản tại VietinBank" ← ĐÚNG
            - "Chi nhánh Hà Nội thuộc về VietinBank" ← ĐÚNG
            
            OUTPUT FORMAT (JSON):
            {{
                "relationships": [
                    {{
                        "source_entity_id": "ID_thực_thể_nguồn",
                        "target_entity_id": "ID_thực_thể_đích",
                        "source_entity": "text thực thể nguồn",
                        "target_entity": "text thực thể đích", 
                        "source_entity_type": "loại thực thể nguồn",
                        "target_entity_type": "loại thực thể đích",
                        "relationship_type": "loại mối quan hệ",
                        "relationship_phrase": "cụm từ thể hiện mối quan hệ",
                        "evidence_text": "đoạn văn chứng minh cụ thể",
                        "confidence": điểm_tin_cậy,
                        "relationship_direction": "forward|backward|bidirectional"
                    }}
                ]
            }}
            """

            user_prompt = f"""Văn bản phân tích:
            {text}
            
            Danh sách thực thể:
            {entity_list}
            
            Hãy trích xuất TẤT CẢ mối quan hệ giữa các thực thể có thể tìm thấy.
            Chú ý: CHỈ trích xuất mối quan hệ GIỮA các thực thể, KHÔNG trích xuất thuộc tính của từng thực thể.
            """

            content = await self.llm_client.extract_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            relationships = content.get("relationships", [])

            # Basic post-processing
            processed_relationships = []
            for relationship in relationships:
                # Add basic metadata
                relationship["extraction_method"] = "llm_basic"
                relationship["id"] = f"relationship_{len(processed_relationships)}"
                
                # Basic validation
                if self._validate_relationship_basic(relationship, entities):
                    processed_relationships.append(relationship)

            return processed_relationships

        except Exception as e:
            logger.error(f"Error in LLM relationship extraction: {e}")
            return []

    def _validate_relationship_basic(
        self, relationship: Dict[str, Any], entities: List[Dict[str, Any]]
    ) -> bool:
        """Basic validation for relationships"""
        try:
            source_entity_id = relationship.get("source_entity_id")
            target_entity_id = relationship.get("target_entity_id")

            # Check entities exist
            source_exists = any(e.get("id") == source_entity_id for e in entities)
            target_exists = any(e.get("id") == target_entity_id for e in entities)

            if not source_exists or not target_exists:
                logger.warning(f"Relationship references non-existent entities")
                return False

            # Check for self-reference
            if source_entity_id == target_entity_id:
                logger.warning(f"Self-referencing relationship filtered out")
                return False

            # Check evidence exists
            evidence_text = relationship.get("evidence_text", "")
            if not evidence_text or len(evidence_text.strip()) < 5:
                logger.warning(f"Insufficient evidence for relationship")
                return False

            return True

        except Exception as e:
            logger.error(f"Error in basic relationship validation: {e}")
            return False

    def _find_best_matching_entity(
        self, text: str, entities: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the entity that best matches the given text with Vietnamese-specific matching
        """
        text = text.lower().strip()

        # Remove common Vietnamese prefixes/suffixes
        text = re.sub(r"^(ông|bà|anh|chị|em|cô|chú|bác)\s+", "", text)
        text = re.sub(r"\s+(ạ|à|ơi|nhé)$", "", text)

        best_match = None
        best_score = 0

        for entity in entities:
            entity_text = entity.get("text", entity.get("entity_text", "")).lower()

            # Direct match
            if entity_text == text:
                return entity

            # Partial match with scoring
            score = 0
            if text in entity_text or entity_text in text:
                score = 0.8
            elif self._vietnamese_similarity(text, entity_text) > 0.7:
                score = 0.7

            if score > best_score:
                best_score = score
                best_match = entity

        return best_match if best_score > 0.5 else None

    def _vietnamese_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two Vietnamese texts
        """
        # Simple word-based similarity for Vietnamese
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _extract_vietnamese_co_occurrence_relationships(
        self, text: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships based on entity co-occurrence within Vietnamese sentences
        """
        relationships = []

        # Split text into Vietnamese sentences
        sentences = re.split(r"[.!?]+|(?<=[。！？])", text)

        for sentence in sentences:
            sentence_entities = []

            # Find entities in this sentence
            for entity in entities:
                entity_text = entity.get("text", entity.get("entity_text", ""))
                if entity_text.lower() in sentence.lower():
                    sentence_entities.append(entity)

            # Create relationships between co-occurring entities
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i + 1 :]:
                    entity1_type = entity1.get("entity_type", "")
                    entity2_type = entity2.get("entity_type", "")

                    # Skip entities of the same type
                    if entity1_type == entity2_type:
                        continue

                    relationship_type = (
                        self._determine_vietnamese_co_occurrence_relationship_type(
                            entity1, entity2, sentence
                        )
                    )

                    if relationship_type:
                        relationships.append(
                            {
                                "id": f"relationship_{len(relationships)}",
                                "source_entity_id": entity1.get("id"),
                                "target_entity_id": entity2.get("id"),
                                "source_entity": entity1.get(
                                    "text", entity1.get("entity_text", "")
                                ),
                                "target_entity": entity2.get(
                                    "text", entity2.get("entity_text", "")
                                ),
                                "source_entity_type": entity1.get("entity_type"),
                                "target_entity_type": entity2.get("entity_type"),
                                "relationship_type": relationship_type,
                                "confidence": 0.5,  # Lower confidence for co-occurrence relationships
                                "extraction_method": "vietnamese_cooccurrence",
                                "evidence_text": sentence,
                                "relationship_phrase": sentence.strip(),
                                "relationship_direction": "bidirectional",
                            }
                        )

        return relationships

    def _determine_vietnamese_co_occurrence_relationship_type(
        self, entity1: Dict[str, Any], entity2: Dict[str, Any], sentence: str
    ) -> Optional[str]:
        """
        Determine the relationship type between co-occurring entities based on Vietnamese context
        """
        type1 = entity1.get("entity_type", "")
        type2 = entity2.get("entity_type", "")
        sentence_lower = sentence.lower()

        # Define Vietnamese relationship indicators
        vietnamese_indicators = {
            "has_account": ["có tài khoản", "mở tài khoản", "sở hữu tài khoản"],
            "is_customer_of": ["khách hàng của", "giao dịch tại", "sử dụng dịch vụ"],
            "provides_service_to": ["cung cấp", "phục vụ", "phát hành"],
            "works_at": ["làm việc tại", "nhân viên", "cán bộ"],
            "located_at": ["tại", "ở", "địa chỉ"],
            "manages": ["quản lý", "điều hành", "phụ trách"],
            "transfers_to": ["chuyển", "gửi", "thanh toán"],
        }

        # Check for specific Vietnamese relationship indicators
        for relationship, indicators in vietnamese_indicators.items():
            if any(indicator in sentence_lower for indicator in indicators):
                # Check if entity types match the relationship
                if self._entity_types_match_relationship(type1, type2, relationship):
                    return relationship

        # Fallback to type-based relationships
        relationship_map = {
            ("Person", "Bank"): "associated_with",
            ("Bank", "Person"): "serves",
            ("Person", "Account"): "has_account",
            ("Account", "Person"): "belongs_to",
            ("Bank", "Product"): "offers",
            ("Product", "Bank"): "offered_by",
            ("Person", "Product"): "uses",
            ("Product", "Person"): "used_by",
            ("Location", "Bank"): "hosts",
            ("Bank", "Location"): "located_at",
        }

        return relationship_map.get((type1, type2), "related_to")

    def _entity_types_match_relationship(
        self, type1: str, type2: str, relationship: str
    ) -> bool:
        """
        Check if entity types are appropriate for the relationship
        """
        type_constraints = {
            "has_account": [("Person", "Account"), ("Person", "Bank")],
            "is_customer_of": [("Person", "Bank")],
            "provides_service_to": [("Bank", "Person"), ("Bank", "Organization")],
            "works_at": [("Person", "Bank"), ("Person", "Organization")],
            "located_at": [("Bank", "Location"), ("Person", "Location")],
            "manages": [("Person", "Account"), ("Person", "Bank")],
            "transfers_to": [("Person", "Person"), ("Account", "Account")],
        }

        allowed_types = type_constraints.get(relationship, [])
        return (type1, type2) in allowed_types or (type2, type1) in allowed_types

    def _deduplicate_relationships(
        self, relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate relationships using Vietnamese-aware comparison
        """
        unique_relationships = []
        seen_relationships = set()

        for rel in relationships:
            source_entity = rel.get("source_entity", "").lower().strip()
            target_entity = rel.get("target_entity", "").lower().strip()
            relationship_type = rel.get("relationship_type", "")

            # Create a key for deduplication (normalize order for symmetric relationships)
            if source_entity < target_entity:
                rel_key = (source_entity, target_entity, relationship_type)
            else:
                rel_key = (target_entity, source_entity, relationship_type)

            if rel_key not in seen_relationships:
                seen_relationships.add(rel_key)
                unique_relationships.append(rel)
            else:
                # If we've seen this relationship before, keep the one with higher confidence
                for i, existing_rel in enumerate(unique_relationships):
                    existing_source = (
                        existing_rel.get("source_entity", "").lower().strip()
                    )
                    existing_target = (
                        existing_rel.get("target_entity", "").lower().strip()
                    )
                    existing_type = existing_rel.get("relationship_type", "")

                    # Check if this is the same relationship
                    if (
                        (
                            existing_source == source_entity
                            and existing_target == target_entity
                        )
                        or (
                            existing_source == target_entity
                            and existing_target == source_entity
                        )
                    ) and existing_type == relationship_type:

                        existing_confidence = existing_rel.get("confidence", 0)
                        new_confidence = rel.get("confidence", 0)

                        if new_confidence > existing_confidence:
                            unique_relationships[i] = rel
                        break

        return unique_relationships

    async def save_extraction_results(
        self, relationships: List[Dict[str, Any]], extraction_result_id: int
    ) -> List[int]:
        """
        Save relationship extraction results to database

        Args:
            relationships: Extracted relationships
            extraction_result_id: ID of the parent extraction result

        Returns:
            List of saved relationship IDs
        """
        try:
            supabase = await get_supabase()

            logger.info(
                f"Saving {len(relationships)} relationships to database for extraction result {extraction_result_id}"
            )

            relationship_ids = []

            for relationship in relationships:
                # Find corresponding entity IDs from kg_entities table
                source_entity_id = await self._find_kg_entity_id(
                    relationship.get("source_entity", ""), extraction_result_id
                )
                target_entity_id = await self._find_kg_entity_id(
                    relationship.get("target_entity", ""), extraction_result_id
                )

                logger.info(
                    f"Source entity ID: {source_entity_id}, "
                    f"Target entity ID: {target_entity_id}"
                )

                relationship_data = {
                    "source_entity_id": source_entity_id,
                    "target_entity_id": target_entity_id,
                    "relationship_type": relationship.get("relationship_type"),
                    "properties": {
                        "relationship_type": relationship.get("relationship_type"),
                        "extraction_method": relationship.get("extraction_method"),
                        "pattern_matched": relationship.get("pattern_matched"),
                        "source_entity_text": relationship.get("source_entity"),
                        "target_entity_text": relationship.get("target_entity"),
                        "confidence": relationship.get("confidence"),
                        "evidence_text": relationship.get("evidence_text"),
                        "relationship_phrase": relationship.get("relationship_phrase"),
                    },
                    "confidence": relationship.get("confidence"),
                    "extraction_confidence": relationship.get("confidence"),
                    "is_verified": False,
                    "validation_status": "pending",
                }

                logger.info(f"Saving relationship: {relationship_data}")

                response = (
                    await supabase.from_("kg_relationships")
                    .insert(relationship_data)
                    .execute()
                )

                if response.data:
                    relationship_ids.append(response.data[0]["id"])

            logger.info(f"Saved {len(relationship_ids)} relationships to database")
            return relationship_ids

        except Exception as e:
            logger.error(f"Error saving relationship extraction results: {e}")
            raise

    async def _find_kg_entity_id(
        self, entity_text: str, extraction_result_id: int
    ) -> Optional[str]:
        """
        Find the corresponding kg_entities ID for an entity text
        """
        try:
            supabase = await get_supabase()

            # First try to find entity from the same extraction
            response = (
                await supabase.from_("kg_entities")
                .select("id")
                .eq("entity_text", entity_text)
                .limit(1)
                .execute()
            )

            if response.data:
                return response.data[0]["id"]

            # If not found, try fuzzy matching
            response = (
                await supabase.from_("kg_entities")
                .select("id, entity_text")
                .ilike("entity_text", f"%{entity_text}%")
                .limit(5)
                .execute()
            )

            for entity in response.data:
                if (
                    self._vietnamese_similarity(
                        entity_text.lower(), entity["entity_text"].lower()
                    )
                    > 0.8
                ):
                    return entity["id"]

            return None

        except Exception as e:
            logger.warning(f"Error finding kg_entity_id for {entity_text}: {e}")
            return None

    async def get_relationship_statistics(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about extracted relationships
        """
        try:
            supabase = await get_supabase()

            # Get basic relationship counts
            query = supabase.from_("extraction_results").select("relationship_count")
            response = await query.execute()

            total_relationships = sum(result.get("relationship_count", 0) for result in response.data)
            total_extractions = len(response.data)

            return {
                "total_relationships": total_relationships,
                "total_extractions": total_extractions,
                "average_relationships_per_extraction": (
                    total_relationships / total_extractions if total_extractions > 0 else 0
                ),
                "domain": domain,
            }

        except Exception as e:
            logger.error(f"Error getting relationship statistics: {e}")
            return {}
