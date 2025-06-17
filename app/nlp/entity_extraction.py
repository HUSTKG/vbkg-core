import logging
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.llm_client import get_llm_client
from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)


class EntityExtractionService:
    """
    Simplified entity extraction service focusing on extraction with basic processing
    """

    def __init__(self):
        # Initialize OpenAI client
        self.llm_client = get_llm_client()

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
        Extract entities from Vietnamese text using LLM with basic processing

        Args:
            text: Input text (Vietnamese)
            domain: Domain to focus on (e.g., 'banking' for banking)
            user_id: User ID for tracking
            auto_save: Whether to automatically save results to database

        Returns:
            Dictionary containing extracted entities
        """
        try:
            # Use LLM for extraction
            entities = await self._extract_entities_with_llm(text, domain)

            logger.info(f"Extracted {len(entities)} entities using LLM")

            # Basic deduplication
            deduplicated_entities = self._deduplicate_entities(entities)

            # Auto-save results if requested
            extraction_id = None
            if auto_save:
                extraction_id = await self.save_extraction_results(
                    text=text, entities=deduplicated_entities, user_id=user_id
                )

            return {
                "entities": deduplicated_entities,
                "extraction_method": "llm_basic",
                "entity_count": len(deduplicated_entities),
                "extraction_id": extraction_id,
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
            raise Exception(
                "Entity extraction failed. Please check the logs for details."
            )

    async def _extract_entities_with_llm(
        self, text: str, domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract entities using LLM with discovery-first approach
        """
        if not self.llm_client:
            return []

        try:
            system_prompt = f"""
            Bạn là một hệ thống trích xuất thực thể ngân hàng chuyên nghiệp cho tiếng Việt.
            
            MỤC TIÊU: Trích xuất TẤT CẢ thực thể có thể có trong văn bản.
            
            HƯỚNG DẪN TRÍCH XUẤT:
            1. **Extract mọi thứ có thể**: Tên người, ngân hàng, tài khoản, số tiền, ngày tháng, địa điểm, sản phẩm, giao dịch, v.v.
            2. **Tự đề xuất entity type**: Tự đề xuất loại thực thể phù hợp
            3. **Trích xuất thuộc tính**: Cho mỗi thực thể, tìm các thuộc tính dữ liệu liên quan
            
            Các loại thực thể thường gặp (có thể mở rộng):
            - Person (Người): tên, tuổi, nghề nghiệp, địa chỉ, sdt, email
            - Bank (Ngân hàng): tên, mã, địa chỉ, hotline
            - Account (Tài khoản): số tk, loại tk, số dư, ngày mở
            - Transaction (Giao dịch): mã gd, số tiền, ngày, loại
            - Product (Sản phẩm): tên sp, loại, lãi suất, phí
            - Location (Địa điểm): tên, địa chỉ, loại (chi nhánh/atm)
            - Document (Tài liệu): loại, số, ngày cấp
            - Card (Thẻ): loại thẻ, số thẻ, hạn sử dụng
            - Contract (Hợp đồng): số hợp đồng, loại, ngày ký
            - Money (Tiền): số tiền, đơn vị
            - Date (Ngày tháng): ngày, tháng, năm
            
            ⭐ QUAN TRỌNG: Hãy tự tạo entity type mới phù hợp nếu cần thiết!
            
            OUTPUT FORMAT (JSON):
            {{
                "entities": [
                    {{
                        "text": "văn bản thực thể chính xác",
                        "entity_type": "loại thực thể",
                        "start_position": vị_trí_bắt_đầu_trong_văn_bản,
                        "end_position": vị_trí_kết_thúc_trong_văn_bản,
                        "confidence": điểm_tin_cậy_thực_thể,
                        "properties": [
                            {{
                                "property_name": "tên thuộc tính bằng tiếng Anh, snake case",
                                "vietnamese_property_name": "tên thuộc tính bằng tiếng Việt",
                                "property_value": "giá trị cụ thể", 
                                "property_type": "string|number|date|boolean",
                                "confidence": điểm_tin_cậy_thuộc_tính
                            }}
                        ]
                    }}
                ]
            }}
            """

            user_prompt = f"""Văn bản để phân tích:
            {text}
            
            Hãy trích xuất TẤT CẢ thực thể và thuộc tính có thể tìm thấy từ văn bản tiếng Việt này.
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
                entity["extraction_method"] = "llm_basic"
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

                processed_entities.append(entity)

            return processed_entities

        except Exception as e:
            logger.error(f"Error in LLM entity extraction: {e}")
            return []

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
