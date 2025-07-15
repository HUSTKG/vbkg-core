import logging
import re
from typing import Any, Dict, List, Optional

from app.core.llm_client import get_llm_client
from app.core.supabase import get_supabase
from app.services.ontology.main import OntologyService

logger = logging.getLogger(__name__)


class RelationshipExtractionService:
    """
    Enhanced relationship extraction service with ontology context and direct Supabase saving
    """

    def __init__(self):
        # Initialize OpenAI client
        self.llm_client = get_llm_client()
        # Initialize Ontology service for context
        self.ontology_service = OntologyService()

    async def extract_relationships(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        domain: Optional[str] = None,
        user_id: Optional[str] = None,
        auto_save: bool = True,
    ) -> Dict[str, Any]:
        """
        Extract relationships between entities using LLM with ontology context

        Args:
            text: Input text (Vietnamese)
            entities: List of extracted entities (should have database IDs if saved)
            domain: Domain to focus on
            user_id: User ID for tracking changes
            auto_save: Whether to automatically save results to database

        Returns:
            Dictionary containing extracted relationships with saved IDs
        """
        try:
            # Get ontology context for better relationship extraction
            ontology_context = await self._get_ontology_context(domain)

            # Use LLM for extraction with ontology context
            relationships = await self._extract_relationships_with_llm(
                text, entities, domain, ontology_context
            )

            logger.info(
                f"Extracted {len(relationships)} relationships using LLM with ontology context"
            )

            # Basic deduplication
            deduplicated_relationships = self._deduplicate_relationships(relationships)

            logger.info(
                f"Deduplicated relationships: {len(deduplicated_relationships)}"
            )

            # Auto-save results if requested
            saved_relationships = []
            if auto_save and deduplicated_relationships:
                saved_relationships = await self._save_relationships_to_kg_table(
                    relationships=deduplicated_relationships,
                    entities=entities,
                    user_id=user_id,
                )

            return {
                "relationships": (
                    saved_relationships
                    if saved_relationships
                    else deduplicated_relationships
                ),
                "extraction_method": "llm_ontology_enhanced",
                "relationship_count": len(
                    saved_relationships
                    if saved_relationships
                    else deduplicated_relationships
                ),
                "ontology_context_used": bool(ontology_context),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in relationship extraction: {e}")
            raise Exception(
                "An error occurred during relationship extraction. Please try again later."
            )

    async def _get_ontology_context(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ontology context including object properties for relationship extraction
        """
        try:
            context = {
                "object_properties": [],
                "ontology_classes": [],
                "domain_info": domain,
            }

            # Get object properties for relationships
            object_properties = await self.ontology_service.get_properties_by_type(
                property_type="object", domain=domain, limit=100
            )
            context["object_properties"] = object_properties

            # Get ontology classes for context
            classes_response = await self.ontology_service.get_ontology_classes(
                domain=domain, limit=100
            )

            if hasattr(classes_response, "data") and classes_response.data:
                context["ontology_classes"] = classes_response.data
            elif isinstance(classes_response, dict) and "data" in classes_response:
                context["ontology_classes"] = classes_response["data"]

            logger.info(
                f"Retrieved ontology context for relationships: {len(context['object_properties'])} object properties, "
                f"{len(context['ontology_classes'])} classes"
            )

            return context

        except Exception as e:
            logger.warning(
                f"Could not retrieve ontology context for relationships: {e}"
            )
            return {}

    def _format_ontology_context_for_prompt(
        self, ontology_context: Dict[str, Any]
    ) -> str:
        """
        Format ontology context for inclusion in LLM prompt
        """
        if not ontology_context:
            return "Không có thông tin ontology có sẵn."

        context_text = []

        # Format object properties for relationships
        object_props = ontology_context.get("object_properties", [])
        if object_props:
            context_text.append("**CÁC THUỘC TÍNH ĐỐI TƯỢNG (OBJECT PROPERTIES):**")
            context_text.append(
                "*Sử dụng để trích xuất mối quan hệ giữa các thực thể:*"
            )
            for prop in object_props[:30]:  # Limit to avoid too long prompt
                prop_info = f"- {prop.get('label', prop.get('uri', 'Unknown'))}"
                if prop.get("description"):
                    prop_info += f": {prop['description']}"
                if prop.get("domain_class_uri") and prop.get("range_class_uri"):
                    prop_info += f" (Domain: {prop['domain_class_uri']} → Range: {prop['range_class_uri']})"
                context_text.append(prop_info)

        # Format ontology classes for reference
        classes = ontology_context.get("ontology_classes", [])
        if classes:
            context_text.append(
                "\n**CÁC LỚP THỰC THỂ (ONTOLOGY CLASSES) - để tham khảo:**"
            )
            class_labels = [
                cls.get("label", cls.get("uri", "Unknown")) for cls in classes[:15]
            ]
            context_text.append(", ".join(class_labels))

        return "\n".join(context_text)

    async def _extract_relationships_with_llm(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        domain: Optional[str] = None,
        ontology_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract ALL possible relationships using LLM with ontology context
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

                # Include abbreviations if available
                abbreviation = ""
                if isinstance(entity.get("properties"), dict):
                    abbreviation = entity["properties"].get("abbreviation", "")
                elif isinstance(entity.get("properties"), list):
                    for prop in entity["properties"]:
                        if prop.get("property_name") == "abbreviation":
                            abbreviation = prop.get("property_value", "")
                            break

                entity_info_str = f'Entity_{i+1} [ID: {entity_id}]: "{entity_text}" (Type: {entity_type})'
                if abbreviation:
                    entity_info_str += f" (Viết tắt: {abbreviation})"

                entity_info.append(entity_info_str)

            entity_list = "\n".join(entity_info)

            # Format ontology context for prompt
            ontology_context_text = self._format_ontology_context_for_prompt(
                ontology_context or {}
            )

            system_prompt = f"""
            Bạn là một hệ thống trích xuất MỐI QUAN HỆ chuyên nghiệp cho tiếng Việt.
            
            MỤC TIÊU: Trích xuất TẤT CẢ mối quan hệ giữa các thực thể với thông tin ontology.
            
            {ontology_context_text}
            
            HƯỚNG DẪN TRÍCH XUẤT:
            1. **Ưu tiên sử dụng ontology**: Sử dụng các object properties từ ontology đã cho
            2. **Extract mọi mối quan hệ**: Tìm tất cả kết nối giữa các thực thể
            3. **Tự đặt tên relationship type mới**: Nếu không có trong ontology, tự đặt tên phù hợp
            4. **Only entity-to-entity**: CHỈ quan hệ giữa 2 thực thể, không phải thuộc tính của 1 thực thể
            5. **Clear evidence**: Phải có bằng chứng rõ ràng trong văn bản
            6. **⭐ CHÚ Ý VỀ TỪ VIẾT TẮT**: 
               - Có thể sử dụng từ viết tắt để nhận diện thực thể
               - VD: "VCB cung cấp dịch vụ cho khách hàng" → hiểu VCB là "Ngân hàng Thương mại Cổ phần Việt Nam"
            
            Các loại mối quan hệ thường gặp (có thể mở rộng):
            **Ngân hàng:**
            - hasAccount (có tài khoản), isCustomerOf (là khách hàng của)
            - transfersTo (chuyển tiền cho), borrowsFrom (vay từ)
            - providesServiceTo (cung cấp dịch vụ), manages (quản lý)
            - ownsCard (sở hữu thẻ), appliesFor (đăng ký)
            - issuesCard (phát hành thẻ), offersProduct (cung cấp sản phẩm)
            
            **Tổ chức:**
            - worksFor (làm việc cho), employs (tuyển dụng)
            - partnersWith (hợp tác với), competesWith (cạnh tranh với)
            - subsidiaryOf (là công ty con), owns (sở hữu)
            - collaboratesWith (hợp tác với), acquires (mua lại)
            
            **Địa lý:**
            - locatedIn (nằm trong), adjacentTo (liền kề)
            - serves (phục vụ khu vực), operatesIn (hoạt động tại)
            - hasAddress (có địa chỉ), situatedAt (tọa lạc tại)
            
            **Thời gian:**
            - happensBefore/After (xảy ra trước/sau)
            - validDuring (có hiệu lực trong), occursDuring (xảy ra trong)
            
            **Tài chính:**
            - guarantees (bảo lãnh), secures (thế chấp)
            - inheritsFrom (thừa kế từ), donatesTo (quyên góp cho)
            - investsIn (đầu tư vào), fundsTo (tài trợ cho)
            
            ⭐ QUAN TRỌNG: Hãy tự tạo relationship type mới nếu cần thiết!
            
            VÍ DỤ SAI (datatype properties):
            - "Nguyễn Văn A có tên là Nguyễn Văn A" ← SAI
            - "Tài khoản có số 123456" ← SAI
            
            VÍ DỤ ĐÚNG (object properties):
            - "Nguyễn Văn A có tài khoản tại VietinBank" ← ĐÚNG
            - "Chi nhánh Hà Nội thuộc về VietinBank" ← ĐÚNG
            - "VCB phát hành thẻ tín dụng cho khách hàng" ← ĐÚNG
            
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
                        "relationship_type": "loại mối quan hệ (ưu tiên từ ontology object properties)",
                        "ontology_property_uri": "URI của object property nếu có",
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
            
            ĐẶC BIỆT CHÚ Ý:
            - Ưu tiên sử dụng các object properties từ ontology đã cho
            - CHỈ trích xuất mối quan hệ GIỮA các thực thể, KHÔNG trích xuất thuộc tính của từng thực thể
            - Có thể sử dụng từ viết tắt để nhận diện thực thể trong văn bản
            - Nếu không có object property phù hợp trong ontology, tự tạo relationship type mới
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
                relationship["extraction_method"] = "llm_ontology_enhanced"
                relationship["id"] = f"relationship_{len(processed_relationships)}"

                # Map ontology property URI to ID if available
                if relationship.get("ontology_property_uri") and ontology_context:
                    relationship["ontology_property_id"] = (
                        await self._map_ontology_property_uri_to_id(
                            relationship["ontology_property_uri"], ontology_context
                        )
                    )

                # Basic validation
                if self._validate_relationship_basic(relationship, entities):
                    processed_relationships.append(relationship)

            return processed_relationships

        except Exception as e:
            logger.error(f"Error in LLM relationship extraction: {e}")
            return []

    async def _map_ontology_property_uri_to_id(
        self, property_uri: str, ontology_context: Dict[str, Any]
    ) -> Optional[int]:
        """
        Map ontology property URI to database ID
        """
        try:
            properties = ontology_context.get("object_properties", [])
            for prop in properties:
                if prop.get("uri") == property_uri:
                    return prop.get("id")
            return None
        except Exception as e:
            logger.warning(f"Error mapping ontology property URI to ID: {e}")
            return None

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
        Find the entity that best matches the given text with Vietnamese-specific matching and abbreviation support
        """
        text = text.lower().strip()

        # Remove common Vietnamese prefixes/suffixes
        text = re.sub(r"^(ông|bà|anh|chị|em|cô|chú|bác)\s+", "", text)
        text = re.sub(r"\s+(ạ|à|ơi|nhé)$", "", text)

        best_match = None
        best_score = 0

        for entity in entities:
            entity_text = entity.get("text", entity.get("entity_text", "")).lower()

            # Check for abbreviation match
            abbreviation = ""
            if isinstance(entity.get("properties"), dict):
                abbreviation = entity["properties"].get("abbreviation", "").lower()
            elif isinstance(entity.get("properties"), list):
                for prop in entity["properties"]:
                    if prop.get("property_name") == "abbreviation":
                        abbreviation = prop.get("property_value", "").lower()
                        break

            # Direct match with full name
            if entity_text == text:
                return entity

            # Direct match with abbreviation
            if abbreviation and abbreviation == text:
                return entity

            # Partial match with scoring
            score = 0
            if text in entity_text or entity_text in text:
                score = 0.8
            elif abbreviation and (text in abbreviation or abbreviation in text):
                score = 0.9  # Higher score for abbreviation match
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

            # Find entities in this sentence (including abbreviations)
            for entity in entities:
                entity_text = entity.get("text", entity.get("entity_text", ""))

                # Check for abbreviation
                abbreviation = ""
                if isinstance(entity.get("properties"), dict):
                    abbreviation = entity["properties"].get("abbreviation", "")
                elif isinstance(entity.get("properties"), list):
                    for prop in entity["properties"]:
                        if prop.get("property_name") == "abbreviation":
                            abbreviation = prop.get("property_value", "")
                            break

                # Check if entity or its abbreviation appears in sentence
                if entity_text.lower() in sentence.lower() or (
                    abbreviation and abbreviation.lower() in sentence.lower()
                ):
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
            "issues": ["phát hành", "cấp phát", "ban hành"],
            "offers": ["cung cấp", "đề xuất", "chào bán"],
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
            ("Organization", "Person"): "employs",
            ("Person", "Organization"): "works_for",
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
            "issues": [
                ("Bank", "Card"),
                ("Bank", "Product"),
                ("Organization", "Document"),
            ],
            "offers": [("Bank", "Product"), ("Organization", "Product")],
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

    async def _save_relationships_to_kg_table(
        self,
        relationships: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Save relationships to kg_relationships table and return saved relationships with IDs

        Args:
            relationships: List of relationships to save
            entities: List of entities for ID mapping
            user_id: User ID for tracking

        Returns:
            List of saved relationships with database IDs
        """
        try:
            supabase = await get_supabase()
            saved_relationships = []

            for relationship in relationships:
                # Find corresponding entity IDs from saved entities
                source_entity_id = await self._find_kg_entity_id(
                    relationship.get("source_entity", ""), entities
                )
                target_entity_id = await self._find_kg_entity_id(
                    relationship.get("target_entity", ""), entities
                )

                if not source_entity_id or not target_entity_id:
                    logger.warning(
                        f"Could not find entity IDs for relationship: {relationship}"
                    )
                    continue

                relationship_data = {
                    "source_entity_id": source_entity_id,
                    "target_entity_id": target_entity_id,
                    "relationship_type": relationship.get("relationship_type"),
                    "ontology_property_id": relationship.get("ontology_property_id"),
                    "properties": {
                        "source_entity_id": source_entity_id,
                        "target_entity_id": target_entity_id,
                        "extraction_method": relationship.get("extraction_method"),
                        "pattern_matched": relationship.get("pattern_matched"),
                        "is_mapped": relationship.get("is_mapped", False),
                        "evidence_text": relationship.get("evidence_text", ""),
                        "relationship_phrase": relationship.get(
                            "relationship_phrase", ""
                        ),
                        "relationship_direction": relationship.get(
                            "relationship_direction", "forward"
                        ),
                        "ontology_property_uri": relationship.get(
                            "ontology_property_uri"
                        ),
                    },
                    "confidence": relationship.get("confidence", 0.0),
                    "extraction_confidence": relationship.get("confidence", 0.0),
                    "is_verified": False,
                    "validation_status": "pending",
                    "created_by": user_id,
                }

                logger.info(f"Saving relationship: {relationship_data}")

                relationship_response = (
                    await supabase.from_("kg_relationships")
                    .insert(relationship_data)
                    .execute()
                )

                if relationship_response.data:
                    saved_relationship = relationship_response.data[0]
                    # Merge original relationship data with saved relationship data
                    merged_relationship = {**relationship, **saved_relationship}
                    saved_relationships.append(merged_relationship)
                    logger.info(
                        f"Successfully saved relationship with ID: {saved_relationship['id']}"
                    )
                else:
                    logger.warning(f"Failed to save relationship: {relationship}")

            logger.info(
                f"Successfully saved {len(saved_relationships)} relationships to kg_relationships table"
            )
            return saved_relationships

        except Exception as e:
            logger.error(f"Error saving relationships to kg_relationships table: {e}")
            # Return original relationships if saving fails
            return relationships

    async def _find_kg_entity_id(
        self, entity_text: str, entities: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Find the corresponding kg_entities ID for an entity text from saved entities
        Support both full name and abbreviation matching

        Args:
            entity_text: Text of the entity to find
            entities: List of saved entities with database IDs

        Returns:
            Database ID of the entity or None if not found
        """
        try:
            # First try to find entity in the provided entities list (should have DB IDs)
            for entity in entities:
                entity_actual_text = entity.get("text", entity.get("entity_text", ""))

                # Check for abbreviation
                abbreviation = ""
                if isinstance(entity.get("properties"), dict):
                    abbreviation = entity["properties"].get("abbreviation", "")
                elif isinstance(entity.get("properties"), list):
                    for prop in entity["properties"]:
                        if prop.get("property_name") == "abbreviation":
                            abbreviation = prop.get("property_value", "")
                            break

                # Check similarity with full name
                if (
                    entity_actual_text
                    and self._vietnamese_similarity(
                        entity_text.lower(), entity_actual_text.lower()
                    )
                    > 0.8
                ):
                    return entity.get("id")

                # Check exact match with abbreviation
                if abbreviation and abbreviation.lower() == entity_text.lower():
                    return entity.get("id")

            # Fallback: query database directly
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

            # Try abbreviation match in properties
            response = (
                await supabase.from_("kg_entities")
                .select("id, entity_text, properties")
                .limit(50)
                .execute()
            )

            for entity in response.data:
                # Check abbreviation in properties
                properties = entity.get("properties", {})
                if isinstance(properties, dict) and properties.get("abbreviation"):
                    if properties["abbreviation"].lower() == entity_text.lower():
                        return entity["id"]

                # Check fuzzy match with entity text
                entity_db_text = entity.get("entity_text", "")
                if (
                    entity_db_text
                    and self._vietnamese_similarity(
                        entity_text.lower(), entity_db_text.lower()
                    )
                    > 0.8
                ):
                    return entity["id"]

            return None

        except Exception as e:
            logger.warning(f"Error finding kg_entity_id for {entity_text}: {e}")
            return None

    async def save_extraction_results(
        self, relationships: List[Dict[str, Any]], extraction_result_id: int
    ) -> List[int]:
        """
        Save relationship extraction results to database (legacy method for compatibility)

        This method is kept for backward compatibility but relationships should now be
        saved directly using _save_relationships_to_kg_table
        """
        logger.info(
            "Using legacy save_extraction_results method - consider using direct saving"
        )
        return []

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

            total_relationships = sum(
                result.get("relationship_count", 0) for result in response.data
            )
            total_extractions = len(response.data)

            return {
                "total_relationships": total_relationships,
                "total_extractions": total_extractions,
                "average_relationships_per_extraction": (
                    total_relationships / total_extractions
                    if total_extractions > 0
                    else 0
                ),
                "domain": domain,
            }

        except Exception as e:
            logger.error(f"Error getting relationship statistics: {e}")
            return {}
