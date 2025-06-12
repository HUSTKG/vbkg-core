import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.supabase import get_supabase
from app.nlp.ontogpt import OntoGPTService
from app.services.ontology import OntologyService

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI is not installed. Install with: pip install openai")

# Enhanced Vietnamese banking entity patterns
VIETNAMESE_BANKING_ENTITY_PATTERNS = {
    "Bank": [
        r"\b(VietinBank|BIDV|Vietcombank|ACB|MB Bank|Techcombank|VPBank|HD Bank|TPBank|SeABank|VIB|OCB|SHB|Eximbank|Sacombank|DongA Bank|VietBank|TMCP|Ngân hàng)\b",
        r"\b(ngân hàng|NH)\s+([A-Z][a-zA-Z0-9\s]+)\b",
    ],
    "Person": [
        r"\b([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+)?)\b",
        r"\b(khách hàng|KH)\s+([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]+)\b",
    ],
    "Account": [
        r"\b(tài khoản|TK)\s+(?:số\s+)?(\d{10,16})\b",
        r"\b(\d{10,16})\b(?=.*(?:tài khoản|TK))",
        r"\b(STK|số tài khoản)\s*:?\s*(\d{10,16})\b",
    ],
    "Money": [
        r"\b(\d+(?:[.,]\d+)*)\s*(VND|VNĐ|đồng|triệu|tỷ|nghìn|ngàn)\b",
        r"\b(\d+(?:[.,]\d+)*)\s*(USD|dollar|Dollar)\b",
        r"\b(triệu|tỷ)\s+(\d+(?:[.,]\d+)*)\s*(?:VND|VNĐ|đồng)?\b",
    ],
    "Date": [
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        r"\b(ngày|tháng)\s+(\d{1,2})\s*(tháng)?\s*(\d{1,2})?\s*(năm)?\s*(\d{2,4})?\b",
        r"\b(\d{1,2})\s*(tháng)\s*(\d{1,2})\s*(năm)?\s*(\d{2,4})\b",
    ],
    "Product": [
        r"\b(thẻ tín dụng|thẻ ghi nợ|thẻ ATM|thẻ visa|thẻ master)\b",
        r"\b(tiết kiệm|gửi tiết kiệm|sổ tiết kiệm)\b",
        r"\b(vay thế chấp|vay tín chấp|khoản vay|cho vay)\b",
        r"\b(bảo hiểm nhân thọ|bảo hiểm|quỹ đầu tư)\b",
    ],
    "Transaction": [
        r"\b(giao dịch|chuyển khoản|nạp tiền|rút tiền|thanh toán)\b",
        r"\b(chuyển tiền|chuyển|gửi tiền)\b",
        r"\b(mã giao dịch|mã GD)\s*:?\s*([A-Z0-9]{6,20})\b",
    ],
    "Location": [
        r"\b(chi nhánh|CN)\s+([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]+)\b",
        r"\b(phòng giao dịch|PGD)\s+([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]+)\b",
        r"\b(tại|ở)\s+([A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]+)\b",
    ],
}

class EntityExtractionService:
    """
    Enhanced entity extraction service using OntoGPT and existing ontology with Vietnamese support
    """
    
    def __init__(self):
        self.ontogpt_service = OntoGPTService()
        self.ontology_service = OntologyService()
        
        # Initialize OpenAI client for fallback
        self.openai_client = None
        if OPENAI_AVAILABLE:
            try:
                openai_api_key = os.environ.get("OPENAI_API_KEY")
                if openai_api_key:
                    self.openai_client = OpenAI(api_key=openai_api_key)
                    logger.info("OpenAI client initialized for entity extraction")
                else:
                    logger.warning("OPENAI_API_KEY not found in environment variables")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}")

    async def extract_entities(
        self, 
        text: str, 
        domain: Optional[str] = None,
        use_ontogpt: bool = True,
        enrich_ontology: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract entities from Vietnamese text using OntoGPT library with ontology guidance
        
        Args:
            text: Input text (Vietnamese)
            domain: Domain to focus on (e.g., 'banking' for banking)
            use_ontogpt: Whether to use OntoGPT library (fallback to traditional if False)
            enrich_ontology: Whether to automatically enrich ontology with new concepts
            user_id: User ID for tracking ontology changes
            
        Returns:
            Dictionary containing extracted entities and enrichment results
        """
        try:
            if use_ontogpt:
                # Use OntoGPT library for extraction
                extraction_result = await self.ontogpt_service.extract_knowledge_with_ontogpt(
                    text=text,
                    domain=domain,
                    extract_new_concepts=enrich_ontology,
                )

                logger.info(f"Extraction result: {extraction_result}")
                
                entities = extraction_result.get("entities", [])
                
                # Enrich ontology if requested and new concepts found
                enrichment_result = None
                if enrich_ontology and "new_concepts" in extraction_result:
                    new_concepts = extraction_result["new_concepts"]
                    if new_concepts and (new_concepts.get("classes") or new_concepts.get("properties")):
                        enrichment_result = await self.ontogpt_service.enrich_ontology_with_new_concepts(
                            new_concepts, user_id
                        )
                
                # Validate and enhance entities with database mapping
                enhanced_entities = await self._enhance_entities_with_ontology_mapping(entities)
                
                return {
                    "entities": enhanced_entities,
                    "extraction_method": "ontogpt_library",
                    "ontology_enrichment": enrichment_result,
                    "new_concepts": extraction_result.get("new_concepts"),
                    "extraction_metadata": extraction_result.get("extraction_metadata"),
                    "success": True
                }
            else:
                # Fallback to traditional extraction
                entities = await self._extract_entities_traditional(text, domain)
                return {
                    "entities": entities,
                    "extraction_method": "traditional",
                    "success": True
                }
                
        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
            # Fallback to regex extraction
            entities = self._extract_entities_with_vietnamese_regex(text)
            return {
                "entities": entities,
                "extraction_method": "regex_fallback", 
                "error": str(e),
                "success": False
            }

    async def _enhance_entities_with_ontology_mapping(
        self, 
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance extracted entities with ontology mapping information from database
        """
        enhanced_entities = []
        
        for entity in entities:
            enhanced_entity = entity.copy()
            
            # Get ontology class information from database if mapped
            ontology_class_id = entity.get("ontology_class_id")
            if ontology_class_id:
                try:
                    supabase = await get_supabase()
                    response = await supabase.from_("ontology_classes").select("*").eq("id", ontology_class_id).single().execute()
                    
                    if response.data:
                        ontology_class = response.data
                        enhanced_entity["ontology_class_info"] = ontology_class
                        enhanced_entity["is_mapped"] = True
                        enhanced_entity["ontology_class_uri"] = ontology_class.get("uri")
                        enhanced_entity["entity_type"] = ontology_class.get("label", enhanced_entity.get("entity_type"))
                    else:
                        enhanced_entity["is_mapped"] = False
                        
                except Exception as e:
                    logger.warning(f"Could not find ontology class {ontology_class_id}: {e}")
                    enhanced_entity["is_mapped"] = False
            else:
                enhanced_entity["is_mapped"] = False
                
                # Try to suggest mapping if not mapped
                entity_text = entity.get("text", "")
                entity_type = entity.get("entity_type", "")
                if entity_text:
                    suggestions = await self._suggest_ontology_class_mapping(
                        entity_text=entity_text,
                        entity_type=entity_type,
                        max_suggestions=3
                    )
                    enhanced_entity["mapping_suggestions"] = suggestions
            
            enhanced_entities.append(enhanced_entity)
        
        return enhanced_entities

    async def _suggest_ontology_class_mapping(
        self,
        entity_text: str,
        entity_type: str,
        max_suggestions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest ontology class mappings for an entity using database
        """
        try:
            supabase = await get_supabase()
            
            # Search for similar classes by label or description
            suggestions = []
            
            # First try exact label match
            response = await supabase.from_("ontology_classes").select("*").ilike("label", f"%{entity_type}%").limit(max_suggestions).execute()
            
            for cls in response.data:
                suggestions.append({
                    "ontology_class_id": cls["id"],
                    "label": cls["label"],
                    "uri": cls["uri"],
                    "description": cls.get("description"),
                    "similarity_score": 0.9,
                    "match_type": "label_match"
                })
            
            # If not enough suggestions, try description search
            if len(suggestions) < max_suggestions:
                remaining = max_suggestions - len(suggestions)
                response = await supabase.from_("ontology_classes").select("*").ilike("description", f"%{entity_text}%").limit(remaining).execute()
                
                for cls in response.data:
                    # Avoid duplicates
                    if not any(s["ontology_class_id"] == cls["id"] for s in suggestions):
                        suggestions.append({
                            "ontology_class_id": cls["id"],
                            "label": cls["label"],
                            "uri": cls["uri"],
                            "description": cls.get("description"),
                            "similarity_score": 0.7,
                            "match_type": "description_match"
                        })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting ontology class mapping: {e}")
            return []

    async def _extract_entities_traditional(
        self, 
        text: str, 
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Traditional entity extraction using existing ontology for guidance with Vietnamese support
        """
        if not self.openai_client:
            return self._extract_entities_with_vietnamese_regex(text)
        
        try:
            # Get ontology context from database
            ontology_context = await self.ontogpt_service.get_ontology_context(domain)
            
            # Prepare class information for prompt with Vietnamese labels
            classes_info = []
            for class_id, info in list(ontology_context["classes"].items())[:30]:  # Limit to avoid token overflow
                label = info.get("label", f"Class_{class_id}")
                desc = info.get("description", "")
                vietnamese_labels = self._extract_vietnamese_labels(info.get("properties", {}))
                
                class_desc = f"- {label}"
                if desc:
                    class_desc += f": {desc}"
                if vietnamese_labels:
                    class_desc += f" (Các từ tiếng Việt: {', '.join(vietnamese_labels)})"
                
                classes_info.append(class_desc)
            
            system_prompt = f"""
            Bạn là một hệ thống trích xuất thực thể ngân hàng chuyên nghiệp cho tiếng Việt.
            
            Sử dụng các loại thực thể sau từ ontology hiện có:
            {chr(10).join(classes_info)}
            
            Hướng dẫn trích xuất:
            1. Tìm tất cả các thực thể liên quan đến ngân hàng và tài chính trong văn bản
            2. Xác định chính xác vị trí của thực thể trong văn bản (số ký tự bắt đầu)
            3. Chọn loại thực thể phù hợp nhất từ danh sách trên
            4. Đánh giá độ tin cậy từ 0.0 đến 1.0
            5. Nếu có thể, xác định ID của ontology class tương ứng
            
            Chú ý đặc biệt với:
            - Tên người Việt (họ và tên)
            - Tên ngân hàng Việt Nam
            - Số tài khoản và thẻ
            - Số tiền bằng tiếng Việt (triệu, tỷ, nghìn)
            - Địa danh Việt Nam
            
            OUTPUT FORMAT (JSON):
            {{
                "entities": [
                    {{
                        "text": "văn bản thực thể chính xác",
                        "entity_type": "loại từ ontology",
                        "start_position": vị_trí_bắt_đầu,
                        "confidence": điểm_tin_cậy,
                        "ontology_class_id": ID_hoặc_null,
                        "ontology_class_uri": "URI hoặc null"
                    }}
                ]
            }}
            """

            user_prompt = f"""Văn bản để phân tích:
            {text}
            
            Hãy trích xuất tất cả các thực thể liên quan đến ngân hàng và tài chính từ văn bản tiếng Việt trên.
            Đặc biệt chú ý đến các thuật ngữ tiếng Việt và cách viết số tiền theo phong cách Việt Nam.
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)
            entities = result.get("entities", [])

            # Calculate end positions and add Vietnamese-specific processing
            for entity in entities:
                if "start_position" in entity and "text" in entity:
                    entity["end_position"] = entity["start_position"] + len(entity["text"])
                
                # Add extraction method
                entity["extraction_method"] = "traditional_llm"
                
                # Try to match ontology class ID if not provided
                if not entity.get("ontology_class_id") and entity.get("entity_type"):
                    ontology_class_id = await self._find_ontology_class_id(
                        entity["entity_type"], ontology_context
                    )
                    if ontology_class_id:
                        entity["ontology_class_id"] = ontology_class_id

            return entities

        except Exception as e:
            logger.error(f"Error in traditional entity extraction: {e}")
            return self._extract_entities_with_vietnamese_regex(text)

    def _extract_vietnamese_labels(self, properties: Dict[str, Any]) -> List[str]:
        """Extract Vietnamese labels from ontology properties"""
        labels = []
        if isinstance(properties, dict):
            vietnamese_labels = properties.get("vietnamese_labels", [])
            if isinstance(vietnamese_labels, list):
                labels.extend(vietnamese_labels)
            elif isinstance(vietnamese_labels, str):
                labels.append(vietnamese_labels)
        return labels

    async def _find_ontology_class_id(
        self, 
        entity_type: str, 
        ontology_context: Dict[str, Any]
    ) -> Optional[int]:
        """Find ontology class ID by label"""
        for class_id, info in ontology_context["classes"].items():
            if info.get("label", "").lower() == entity_type.lower():
                return class_id
        return None

    def _extract_entities_with_vietnamese_regex(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities using Vietnamese-enhanced regex patterns (fallback method)
        """
        entities = []

        for entity_type, patterns in VIETNAMESE_BANKING_ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.UNICODE)

                for match in matches:
                    # Handle different capture groups
                    entity_text = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group()
                    
                    # For patterns with multiple groups, get the most relevant one
                    if match.lastindex and match.lastindex > 1:
                        # For patterns like "khách hàng Nguyễn Văn A"
                        if entity_type == "Person" and match.group(2):
                            entity_text = match.group(2)
                        # For patterns with account numbers
                        elif entity_type == "Account" and match.group(2):
                            entity_text = match.group(2)
                        # For money amounts
                        elif entity_type == "Money":
                            amount = match.group(1) if match.group(1) else ""
                            unit = match.group(2) if match.lastindex >= 2 and match.group(2) else ""
                            entity_text = f"{amount} {unit}".strip()

                    entities.append({
                        "text": entity_text.strip(),
                        "entity_type": entity_type,
                        "start_position": match.start(),
                        "end_position": match.end(),
                        "confidence": 0.6,  # Lower confidence for regex-based entities
                        "ontology_class_id": None,
                        "ontology_class_uri": None,
                        "is_mapped": False,
                        "extraction_method": "regex_vietnamese"
                    })

        # Remove duplicates and overlapping entities
        entities = self._remove_overlapping_entities(entities)
        
        return entities

    def _remove_overlapping_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                if (entity["start_position"] < existing["end_position"] and 
                    entity["end_position"] > existing["start_position"]):
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

    async def validate_entities_against_ontology(
        self, 
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate extracted entities against current ontology from database
        """
        try:
            validation_result = await self.ontogpt_service.validate_extraction_against_ontology(
                entities=entities,
                relationships=[]  # Only validating entities here
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating entities: {e}")
            return {"entity_validations": [], "overall_score": 0.0}

    async def get_entity_mapping_suggestions(
        self, 
        entity_text: str, 
        entity_type: Optional[str] = None,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get suggestions for mapping an entity to ontology classes from database
        """
        try:
            suggestions = await self._suggest_ontology_class_mapping(
                entity_text=entity_text,
                entity_type=entity_type or "",
                max_suggestions=max_suggestions
            )
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting mapping suggestions: {e}")
            return []

    async def save_extraction_results(
        self, 
        text: str,
        entities: List[Dict[str, Any]], 
        extraction_metadata: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> int:
        """
        Save extraction results to database with proper entity-ontology mapping
        
        Args:
            text: Original text
            entities: Extracted entities
            extraction_metadata: Metadata about the extraction process
            user_id: User who performed the extraction
            
        Returns:
            ID of the saved extraction result
        """
        try:
            supabase = await get_supabase()
            
            # Save extraction result
            extraction_data = {
                "extracted_entities": {
                    "entities": entities,
                    "source_text": text
                },
                "extracted_relationships": {"relationships": []},
                "status": "completed",
                "entity_count": len(entities),
                "relationship_count": 0,
                "processed_text_length": len(text)
            }

            extraction_response = await supabase.from_("extraction_results").insert(
                extraction_data
            ).execute()
            
            extraction_id = extraction_response.data[0]["id"]

            # Save entities to kg_entities table
            for entity in entities:
                entity_data = {
                    "entity_text": entity.get("text"),
                    "ontology_class_id": entity.get("ontology_class_id"),
                    "properties": {
                        "start_position": entity.get("start_position"),
                        "end_position": entity.get("end_position"),
                        "entity_type": entity.get("entity_type"),
                        "extraction_method": entity.get("extraction_method"),
                        "extraction_metadata": extraction_metadata
                    },
                    "confidence": entity.get("confidence"),
                    "extraction_confidence": entity.get("confidence"),
                    "is_verified": False,
                    "validation_status": "pending",
                    "created_by": user_id,
                    "source_document_id": None  # Could link to file upload if applicable
                }
                
                await supabase.from_("kg_entities").insert(entity_data).execute()
            
            logger.info(f"Saved extraction results with ID: {extraction_id}, {len(entities)} entities")
            return extraction_id
            
        except Exception as e:
            logger.error(f"Error saving extraction results: {e}")
            raise

    async def load_custom_entity_types(self, domain: Optional[str] = None) -> Dict[str, str]:
        """
        Load custom entity types from ontology database
        """
        try:
            supabase = await get_supabase()
            
            # Get ontology classes from database
            query = supabase.from_("ontology_classes").select("*").eq("is_custom", True)
            if domain:
                query = query.eq("domain", domain)
                
            response = await query.execute()
            
            custom_types = {}
            for cls in response.data:
                label = cls.get("label", cls.get("uri", "").split("/")[-1])
                description = cls.get("description", "")
                custom_types[label] = description
            
            logger.info(f"Loaded {len(custom_types)} custom entity types from database")
            return custom_types

        except Exception as e:
            logger.error(f"Error loading custom entity types: {e}")
            return {}

    async def export_entities_for_training(
        self, 
        extraction_result_ids: List[int],
        format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export extracted entities for training or analysis
        
        Args:
            extraction_result_ids: List of extraction result IDs to export
            format: Export format ('json', 'csv', 'spacy')
            
        Returns:
            Exported data
        """
        try:
            supabase = await get_supabase()
            
            # Get extraction results with entities
            results = []
            for result_id in extraction_result_ids:
                # Get extraction result
                extraction_response = await supabase.from_("extraction_results").select("*").eq("id", result_id).single().execute()
                
                if extraction_response.data:
                    extraction_data = extraction_response.data
                    
                    # Get associated entities
                    entities_response = await supabase.from_("kg_entities").select("*, ontology_classes(label, uri)").eq("source_document_id", result_id).execute()
                    
                    extraction_data["entities"] = entities_response.data
                    results.append(extraction_data)
            
            if format == "json":
                return {"extraction_results": results}
            elif format == "spacy":
                # Convert to spaCy training format
                training_data = []
                for result in results:
                    extracted_entities = result.get("extracted_entities", {})
                    text = extracted_entities.get("source_text", "")
                    entities = []
                    
                    for entity_info in result.get("entities", []):
                        start_pos = entity_info.get("properties", {}).get("start_position", 0)
                        end_pos = entity_info.get("properties", {}).get("end_position", 0)
                        entity_type = entity_info.get("properties", {}).get("entity_type", "ENTITY")
                        
                        entities.append((start_pos, end_pos, entity_type))
                    
                    training_data.append((text, {"entities": entities}))
                
                return {"spacy_training_data": training_data}
            else:
                return {"error": f"Unsupported export format: {format}"}
                
        except Exception as e:
            logger.error(f"Error exporting entities: {e}")
            raise

    async def get_entity_statistics(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about extracted entities
        """
        try:
            supabase = await get_supabase()
            
            # Get entity counts by type
            query = supabase.from_("kg_entities").select("ontology_class_id, ontology_classes(label, domain)")
            if domain:
                query = query.eq("ontology_classes.domain", domain)
            
            response = await query.execute()
            
            # Count entities by type
            entity_counts = {}
            total_entities = len(response.data)
            mapped_entities = 0
            
            for entity in response.data:
                if entity.get("ontology_class_id"):
                    mapped_entities += 1
                    class_info = entity.get("ontology_classes")
                    if class_info:
                        label = class_info.get("label", "Unknown")
                        entity_counts[label] = entity_counts.get(label, 0) + 1
            
            # Get validation statistics
            validation_query = supabase.from_("kg_entities").select("validation_status")
            if domain:
                validation_query = validation_query.eq("ontology_classes.domain", domain)
            
            validation_response = await validation_query.execute()
            
            validation_counts = {}
            for entity in validation_response.data:
                status = entity.get("validation_status", "unknown")
                validation_counts[status] = validation_counts.get(status, 0) + 1
            
            return {
                "total_entities": total_entities,
                "mapped_entities": mapped_entities,
                "mapping_percentage": (mapped_entities / total_entities * 100) if total_entities > 0 else 0,
                "entity_type_counts": entity_counts,
                "validation_status_counts": validation_counts,
                "domain": domain
            }
            
        except Exception as e:
            logger.error(f"Error getting entity statistics: {e}")
            return {}
