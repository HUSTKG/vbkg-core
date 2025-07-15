import logging
from typing import Any, Dict, List, Optional

from app.core.llm_client import get_llm_client
from app.core.supabase import get_supabase
from app.services.ontology.main import OntologyService

logger = logging.getLogger(__name__)


class EntityExtractionService:
    """
    Enhanced entity extraction service with ontology context and direct Supabase saving
    """

    def __init__(self):
        # Initialize OpenAI client
        self.llm_client = get_llm_client()
        # Initialize Ontology service for context
        self.ontology_service = OntologyService()

    async def extract_entities(
        self,
        text: str,
        domain: Optional[str] = None,
        user_id: Optional[str] = None,
        auto_save: bool = True,
        step_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        incremental_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract entities from Vietnamese text using LLM with ontology context

        Args:
            text: Input text (Vietnamese)
            domain: Domain to focus on (e.g., 'banking' for banking)
            user_id: User ID for tracking
            auto_save: Whether to automatically save results to database
            step_id: Pipeline step ID
            pipeline_id: Pipeline ID
            incremental_config: Configuration for incremental processing

        Returns:
            Dictionary containing extracted entities with saved IDs
        """
        try:
            # Get ontology context for better extraction
            ontology_context = await self._get_ontology_context(domain)

            # Use LLM for extraction with ontology context
            entities = await self._extract_entities_with_llm(
                text, domain, ontology_context
            )

            logger.info(
                f"Extracted {len(entities)} entities using LLM with ontology context"
            )

            # Basic deduplication
            deduplicated_entities = self._deduplicate_entities(entities)

            # Auto-save results if requested
            extraction_id = None
            saved_entities = []
            if auto_save:
                extraction_id = await self.save_extraction_results(
                    text=text, entities=deduplicated_entities, user_id=user_id
                )

                # Save individual entities to kg_entities table
                saved_entities = await self._save_entities_to_kg_table(
                    entities=deduplicated_entities,
                    user_id=user_id,
                    extraction_id=extraction_id,
                )

            return {
                "entities": saved_entities if saved_entities else deduplicated_entities,
                "extraction_method": "llm_ontology_enhanced",
                "entity_count": len(
                    saved_entities if saved_entities else deduplicated_entities
                ),
                "extraction_id": extraction_id,
                "ontology_context_used": bool(ontology_context),
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
            raise Exception(
                "Entity extraction failed. Please check the logs for details."
            )

    async def _get_ontology_context(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ontology context including classes and datatype properties for entity extraction
        """
        try:
            context = {
                "ontology_classes": [],
                "datatype_properties": [],
                "domain_info": domain,
            }

            # Get ontology classes
            classes_response = await self.ontology_service.get_ontology_classes(
                domain=domain, limit=100
            )

            if hasattr(classes_response, "data") and classes_response.data:
                context["ontology_classes"] = classes_response.data
            elif isinstance(classes_response, dict) and "data" in classes_response:
                context["ontology_classes"] = classes_response["data"]

            # Get datatype properties for entity attributes
            datatype_properties = await self.ontology_service.get_properties_by_type(
                property_type="datatype", domain=domain, limit=100
            )
            context["datatype_properties"] = datatype_properties

            logger.info(
                f"Retrieved ontology context: {len(context['ontology_classes'])} classes, "
                f"{len(context['datatype_properties'])} datatype properties"
            )

            return context

        except Exception as e:
            logger.warning(f"Could not retrieve ontology context: {e}")
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

        # Format ontology classes
        classes = ontology_context.get("ontology_classes", [])
        if classes:
            context_text.append("**CÁC LỚP THỰC THỂ CÓ SẴN (ONTOLOGY CLASSES):**")
            for cls in classes[:20]:  # Limit to avoid too long prompt
                class_info = f"- {cls.get('label', cls.get('uri', 'Unknown'))}"
                if cls.get("description"):
                    class_info += f": {cls['description']}"
                context_text.append(class_info)

        # Format datatype properties for entity attributes
        datatype_props = ontology_context.get("datatype_properties", [])
        if datatype_props:
            context_text.append("\n**CÁC THUỘC TÍNH DỮ LIỆU (DATATYPE PROPERTIES):**")
            context_text.append("*Sử dụng để trích xuất thuộc tính của thực thể:*")
            for prop in datatype_props[:30]:  # Limit to avoid too long prompt
                prop_info = f"- {prop.get('label', prop.get('uri', 'Unknown'))}"
                if prop.get("description"):
                    prop_info += f": {prop['description']}"
                context_text.append(prop_info)

        return "\n".join(context_text)

    async def _extract_entities_with_llm(
        self,
        text: str,
        domain: Optional[str] = None,
        ontology_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extract entities using LLM with ontology context and discovery-first approach
        """
        if not self.llm_client:
            return []

        try:
            # Format ontology context for prompt
            ontology_context_text = self._format_ontology_context_for_prompt(
                ontology_context or {}
            )

            system_prompt = f"""
            Bạn là một hệ thống trích xuất thực thể ngân hàng chuyên nghiệp cho tiếng Việt.
            
            MỤC TIÊU: Trích xuất TẤT CẢ thực thể có thể có trong văn bản với thông tin ontology.
            
            {ontology_context_text}
            
            HƯỚNG DẪN TRÍCH XUẤT:
            1. **Ưu tiên sử dụng ontology**: Sử dụng các lớp thực thể và thuộc tính từ ontology đã cho
            2. **Extract mọi thứ có thể**: Tên người, ngân hàng, tài khoản, số tiền, ngày tháng, địa điểm, sản phẩm, giao dịch, v.v.
            3. **Tự đề xuất entity type mới**: Nếu không có trong ontology, tự đề xuất loại thực thể phù hợp
            4. **Trích xuất thuộc tính datatype**: Sử dụng datatype properties từ ontology để trích xuất thuộc tính
            5. **⭐ ĐẶC BIỆT CHÚ Ý VỀ TỪ VIẾT TẮT**: 
               - Trích xuất cả tên đầy đủ và từ viết tắt
               - Lưu từ viết tắt vào properties với key "abbreviation" hoặc "short_name"
               - VD: "Ngân hàng Thương mại Cổ phần Việt Nam (VCB)" → entity_text: "Ngân hàng Thương mại Cổ phần Việt Nam", properties: {{"abbreviation": "VCB"}}
               - VD: "Ông Nguyễn Văn A (Mr. A)" → entity_text: "Nguyễn Văn A", properties: {{"nickname": "Mr. A"}}
            
            Các loại thực thể thường gặp (có thể mở rộng):
            - Person (Người): tên, tuổi, nghề nghiệp, địa chỉ, sdt, email, biệt danh, từ viết tắt
            - Bank (Ngân hàng): tên, mã, địa chỉ, hotline, website, loại ngân hàng, từ viết tắt
            - Account (Tài khoản): số tk, loại tk, số dư, ngày mở, ngày đóng
            - Transaction (Giao dịch): mã gd, số tiền, ngày, loại
            - Product (Sản phẩm): tên sp, loại, lãi suất, phí, từ viết tắt
            - Location (Địa điểm): tên, địa chỉ, loại (chi nhánh/atm), từ viết tắt
            - Document (Tài liệu): loại, số, ngày cấp, ngày hết hạn, từ viết tắt
            - Card (Thẻ): loại thẻ, số thẻ, hạn sử dụng, ngày phát hành
            - Contract (Hợp đồng): số hợp đồng, loại, ngày ký
            - Money (Tiền): số tiền, đơn vị, mệnh giá, từ viết tắt đơn vị
            - Date (Ngày tháng): ngày, tháng, năm
            - Organization (Tổ chức): tên, loại, địa chỉ, từ viết tắt
            
            ⭐ QUAN TRỌNG: Hãy tự tạo entity type mới phù hợp nếu cần thiết!
            
            OUTPUT FORMAT (JSON):
            {{
                "entities": [
                    {{
                        "text": "văn bản thực thể chính xác (không bao gồm từ viết tắt trong ngoặc)",
                        "entity_type": "loại thực thể (ưu tiên từ ontology)",
                        "ontology_class_uri": "URI của ontology class nếu có",
                        "start_position": vị_trí_bắt_đầu_trong_văn_bản,
                        "end_position": vị_trí_kết_thúc_trong_văn_bản,
                        "confidence": điểm_tin_cậy_thực_thể,
                        "properties": [
                            {{
                                "property_name": "tên thuộc tính bằng tiếng Anh, snake case (ưu tiên từ datatype properties)",
                                "vietnamese_property_name": "tên thuộc tính bằng tiếng Việt",
                                "property_value": "giá trị cụ thể", 
                                "property_type": "string|number|date|boolean",
                                "confidence": điểm_tin_cậy_thuộc_tính,
                                "ontology_property_uri": "URI của datatype property nếu có"
                            }},
                            {{
                                "property_name": "abbreviation",
                                "vietnamese_property_name": "từ viết tắt",
                                "property_value": "từ viết tắt nếu có",
                                "property_type": "string",
                                "confidence": 0.9
                            }}
                        ]
                    }}
                ]
            }}
            """

            user_prompt = f"""Văn bản để phân tích:
            {text}
            
            Hãy trích xuất TẤT CẢ thực thể và thuộc tính có thể tìm thấy từ văn bản tiếng Việt này.
            
            ĐẶC BIỆT CHÚ Ý:
            - Ưu tiên sử dụng các ontology classes và datatype properties đã cho
            - Luôn trích xuất từ viết tắt trong ngoặc đơn () vào properties
            - Tách rời tên chính và từ viết tắt
            - Sử dụng thuộc tính datatype từ ontology cho việc mô tả chi tiết thực thể
            """

            content = await self.llm_client.extract_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            entities = content.get("entities", [])

            # Basic post-processing
            processed_entities = []
            for entity in entities:
                # Add basic metadata
                entity["extraction_method"] = "llm_ontology_enhanced"
                entity["id"] = f"entity_{len(processed_entities)}"

                # Ensure position information
                if "start_position" not in entity and "text" in entity:
                    # Try to find position in text
                    entity_text = entity["text"]
                    start_pos = text.find(entity_text)
                    if start_pos != -1:
                        entity["start_position"] = start_pos
                        entity["end_position"] = start_pos + len(entity_text)
                    else:
                        entity["start_position"] = 0
                        entity["end_position"] = len(entity_text)

                # Map ontology class URI to ID if available
                if entity.get("ontology_class_uri") and ontology_context:
                    entity["ontology_class_id"] = (
                        await self._map_ontology_class_uri_to_id(
                            entity["ontology_class_uri"], ontology_context
                        )
                    )

                processed_entities.append(entity)

            return processed_entities

        except Exception as e:
            logger.error(f"Error in LLM entity extraction: {e}")
            return []

    async def _map_ontology_class_uri_to_id(
        self, class_uri: str, ontology_context: Dict[str, Any]
    ) -> Optional[int]:
        """
        Map ontology class URI to database ID
        """
        try:
            classes = ontology_context.get("ontology_classes", [])
            for cls in classes:
                if cls.get("uri") == class_uri:
                    return cls.get("id")
            return None
        except Exception as e:
            logger.warning(f"Error mapping ontology class URI to ID: {e}")
            return None

    def _deduplicate_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate entities using Vietnamese-aware comparison
        """
        unique_entities = []
        seen_entities = set()

        for entity in entities:
            entity_text = entity.get("text", "").lower().strip()
            entity_type = entity.get("entity_type", "")

            # Create a key for deduplication
            entity_key = (entity_text, entity_type)

            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                unique_entities.append(entity)
            else:
                # If we've seen this entity before, keep the one with higher confidence
                for i, existing_entity in enumerate(unique_entities):
                    if (
                        existing_entity.get("text", "").lower().strip() == entity_text
                        and existing_entity.get("entity_type", "") == entity_type
                    ):

                        existing_confidence = existing_entity.get("confidence", 0)
                        new_confidence = entity.get("confidence", 0)

                        if new_confidence > existing_confidence:
                            unique_entities[i] = entity
                        break

        return unique_entities

    def _remove_overlapping_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove overlapping entities, keeping the one with higher confidence
        """
        # Sort by start position
        entities.sort(key=lambda x: x["start_position"])

        filtered_entities = []
        for entity in entities:
            # Check if this entity overlaps with any previously added entity
            overlaps = False
            for existing in filtered_entities:
                if (
                    entity["start_position"] < existing["end_position"]
                    and entity["end_position"] > existing["start_position"]
                ):
                    # There's an overlap
                    if entity["confidence"] <= existing["confidence"]:
                        overlaps = True
                        break
                    else:
                        # Remove the existing entity as this one has higher confidence
                        filtered_entities.remove(existing)
                        break

            if not overlaps:
                filtered_entities.append(entity)

        return filtered_entities

    async def _save_entities_to_kg_table(
        self,
        entities: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        extraction_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Save entities to kg_entities table and return saved entities with IDs

        Args:
            entities: List of entities to save
            user_id: User ID for tracking
            extraction_id: Associated extraction result ID

        Returns:
            List of saved entities with database IDs
        """
        try:
            supabase = await get_supabase()
            saved_entities = []

            for entity in entities:
                # Prepare entity properties (including abbreviations)
                entity_properties = {}
                for prop in entity.get("properties", []):
                    if (
                        prop.get("confidence", 0) >= 0.5
                    ):  # Lower threshold for abbreviations
                        entity_properties[prop["property_name"]] = prop[
                            "property_value"
                        ]

                entity_data = {
                    "entity_text": entity.get("text", ""),
                    "entity_type": entity.get("entity_type", "Unknown"),
                    "ontology_class_id": entity.get("ontology_class_id"),
                    "properties": {
                        "start_position": entity.get("start_position"),
                        "end_position": entity.get("end_position"),
                        "entity_type": entity.get("entity_type", "Entity"),
                        "extraction_method": entity.get(
                            "extraction_method", "llm_ontology_enhanced"
                        ),
                        "is_mapped": entity.get("is_mapped", False),
                        "confidence": entity.get("confidence", 0.0),
                        "ontology_class_uri": entity.get("ontology_class_uri"),
                        **entity_properties,
                    },
                    "confidence": entity.get("confidence", 0.0),
                    "extraction_confidence": entity.get("confidence", 0.0),
                    "is_verified": False,
                    "validation_status": "pending",
                    "created_by": user_id,
                    "source_document_id": None,
                    "extraction_result_id": extraction_id,
                }

                logger.info(
                    f"Saving entity: {entity_data.get('entity_text', 'unknown')}"
                )

                entity_response = (
                    await supabase.from_("kg_entities").insert(entity_data).execute()
                )

                if entity_response.data:
                    saved_entity = entity_response.data[0]
                    # Merge original entity data with saved entity data
                    merged_entity = {**entity, **saved_entity}
                    saved_entities.append(merged_entity)
                    logger.info(
                        f"Successfully saved entity with ID: {saved_entity['id']}"
                    )
                else:
                    logger.warning(
                        f"Failed to save entity: {entity_data.get('entity_text', 'unknown')}"
                    )

            logger.info(
                f"Successfully saved {len(saved_entities)} entities to kg_entities table"
            )
            return saved_entities

        except Exception as e:
            logger.error(f"Error saving entities to kg_entities table: {e}")
            # Return original entities if saving fails
            return entities

    async def save_extraction_results(
        self, text: str, entities: List[Dict[str, Any]], user_id: Optional[str] = None
    ) -> int:
        """
        Save extraction results to database

        Args:
            text: Original text
            entities: Extracted entities
            user_id: User who performed the extraction

        Returns:
            ID of the saved extraction result
        """
        try:
            supabase = await get_supabase()

            # Save extraction result
            extraction_data = {
                "extracted_entities": {"entities": entities, "source_text": text},
                "extracted_relationships": {"relationships": []},
                "status": "completed",
                "entity_count": len(entities),
                "relationship_count": 0,
                "processed_text_length": len(text),
            }

            extraction_response = (
                await supabase.from_("extraction_results")
                .insert(extraction_data)
                .execute()
            )

            extraction_id = extraction_response.data[0]["id"]

            logger.info(
                f"Saved extraction results with ID: {extraction_id}, {len(entities)} entities"
            )
            return extraction_id

        except Exception as e:
            logger.error(f"Error saving extraction results: {e}")
            raise

    async def get_entity_statistics(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about extracted entities
        """
        try:
            supabase = await get_supabase()

            # Get basic entity counts
            query = supabase.from_("extraction_results").select("entity_count")
            response = await query.execute()

            total_entities = sum(
                result.get("entity_count", 0) for result in response.data
            )
            total_extractions = len(response.data)

            return {
                "total_entities": total_entities,
                "total_extractions": total_extractions,
                "average_entities_per_extraction": (
                    total_entities / total_extractions if total_extractions > 0 else 0
                ),
                "domain": domain,
            }

        except Exception as e:
            logger.error(f"Error getting entity statistics: {e}")
            return {}
