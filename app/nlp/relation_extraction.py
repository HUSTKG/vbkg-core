import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.supabase import get_supabase
from app.nlp.ontogpt import OntoGPTService
from app.services.ontology import OntologyService

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI is not installed. Install with: pip install openai")

# Enhanced Vietnamese banking relation patterns
VIETNAMESE_BANKING_RELATION_PATTERNS = [
    {
        "pattern": r"(.+?)\s+(mở|có|sở hữu|đăng ký)\s+(tài khoản|TK)\s*(?:số\s*)?(\d+)?\s*(?:tại|ở)\s+(.+)",
        "source_type": "Person",
        "target_type": "Account", 
        "relation_type": "has_account",
        "confidence": 0.8
    },
    {
        "pattern": r"(.+?)\s+(chuyển|gửi|chuyển khoản)\s+(.*?)\s+(?:cho|đến|tới)\s+(.+)",
        "source_type": "Person",
        "target_type": "Person",
        "relation_type": "transfers_money_to",
        "confidence": 0.7
    },
    {
        "pattern": r"(.+?)\s+(là khách hàng của|sử dụng dịch vụ của|giao dịch tại)\s+(.+)",
        "source_type": "Person",
        "target_type": "Bank",
        "relation_type": "is_customer_of",
        "confidence": 0.9
    },
    {
        "pattern": r"(.+?)\s+(cung cấp|phát hành|cho vay|bán)\s+(.*?)\s+(?:cho|đến)\s+(.+)",
        "source_type": "Bank",
        "target_type": "Person",
        "relation_type": "provides_service_to",
        "confidence": 0.8
    },
    {
        "pattern": r"(.+?)\s+(thuộc|của|do)\s+(.+?)\s+(quản lý|sở hữu|điều hành)",
        "source_type": "Account",
        "target_type": "Person",
        "relation_type": "belongs_to",
        "confidence": 0.8
    },
    {
        "pattern": r"(.+?)\s+(thực hiện|tạo)\s+giao dịch\s+(.*?)\s+(?:tại|với)\s+(.+)",
        "source_type": "Person",
        "target_type": "Bank",
        "relation_type": "performs_transaction_at",
        "confidence": 0.7
    },
    {
        "pattern": r"chi nhánh\s+(.+?)\s+(?:của|thuộc)\s+(.+)",
        "source_type": "Location",
        "target_type": "Bank",
        "relation_type": "is_branch_of",
        "confidence": 0.9
    },
    {
        "pattern": r"(.+?)\s+(vay|đi vay)\s+(.*?)\s+(?:từ|tại)\s+(.+)",
        "source_type": "Person",
        "target_type": "Bank",
        "relation_type": "borrows_from",
        "confidence": 0.8
    },
    {
        "pattern": r"(.+?)\s+(gửi tiết kiệm|gửi|đầu tư)\s+(.*?)\s+(?:vào|tại)\s+(.+)",
        "source_type": "Person",
        "target_type": "Product",
        "relation_type": "invests_in",
        "confidence": 0.8
    },
    {
        "pattern": r"thẻ\s+(.+?)\s+(?:của|thuộc)\s+(.+)",
        "source_type": "Product",
        "target_type": "Person",
        "relation_type": "issued_to",
        "confidence": 0.8
    }
]

class RelationshipExtractionService:
    """
    Enhanced relationship extraction service using OntoGPT and existing ontology with Vietnamese support
    """
    
    def __init__(self):
        self.ontogpt_service = OntoGPTService()
        self.ontology_service = OntologyService()
        
        # Initialize OpenAI client for fallback
        self.openai_client = None
        if OPENAI_AVAILABLE:
            try:
                import os
                openai_api_key = os.environ.get("OPENAI_API_KEY")
                if openai_api_key:
                    self.openai_client = OpenAI(api_key=openai_api_key)
                    logger.info("OpenAI client initialized for relationship extraction")
                else:
                    logger.warning("OPENAI_API_KEY not found in environment variables")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}")

    async def extract_relationships(
        self, 
        text: str, 
        entities: List[Dict[str, Any]],
        domain: Optional[str] = None,
        use_ontogpt: bool = False,
        enrich_ontology: bool = False,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract relationships between entities using OntoGPT library with Vietnamese ontology guidance
        
        Args:
            text: Input text (Vietnamese)
            entities: List of extracted entities
            domain: Domain to focus on
            use_ontogpt: Whether to use OntoGPT library
            enrich_ontology: Whether to automatically enrich ontology
            user_id: User ID for tracking changes
            
        Returns:
            Dictionary containing extracted relationships and enrichment results
        """
        try:
            if use_ontogpt:
                # Use OntoGPT library for extraction
                extraction_result = await self.ontogpt_service.extract_knowledge_with_ontogpt(
                    text=text,
                    domain=domain,
                    extract_new_concepts=enrich_ontology,
                )
                
                relationships = extraction_result.get("relationships", [])
                
                # Enrich ontology if requested and new concepts found
                enrichment_result = None
                if enrich_ontology and "new_concepts" in extraction_result:
                    new_concepts = extraction_result["new_concepts"]
                    if new_concepts and new_concepts.get("properties"):
                        enrichment_result = await self.ontogpt_service.enrich_ontology_with_new_concepts(
                            new_concepts, user_id
                        )
                
                # Enhance relationships with ontology mapping from database
                enhanced_relationships = await self._enhance_relationships_with_ontology_mapping(
                    relationships, entities
                )
                
                return {
                    "relationships": enhanced_relationships,
                    "extraction_method": "ontogpt_library",
                    "ontology_enrichment": enrichment_result,
                    "new_concepts": extraction_result.get("new_concepts"),
                    "extraction_metadata": extraction_result.get("extraction_metadata"),
                    "success": True
                }
            else:
                # Fallback to traditional extraction
                relationships = await self._extract_relationships_traditional(text, entities, domain)
                return {
                    "relationships": relationships,
                    "extraction_method": "traditional",
                    "success": True
                }
                
        except Exception as e:
            logger.error(f"Error in relationship extraction: {e}")
            # Fallback to rule-based extraction
            relationships = self._extract_relationships_with_vietnamese_rules(text, entities)
            return {
                "relationships": relationships,
                "extraction_method": "rules_fallback",
                "error": str(e),
                "success": False
            }

    async def _enhance_relationships_with_ontology_mapping(
        self, 
        relationships: List[Dict[str, Any]],
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance extracted relationships with ontology mapping information from database
        """
        enhanced_relationships = []
        
        # Create entity lookup for matching
        entity_lookup = {}
        for entity in entities:
            entity_text = entity.get("text", entity.get("entity_text", ""))
            entity_lookup[entity_text.lower()] = entity
        
        for relationship in relationships:
            enhanced_relationship = relationship.copy()
            
            # Find source and target entities
            source_text = relationship.get("source_entity", "")
            target_text = relationship.get("target_entity", "")
            
            source_entity = entity_lookup.get(source_text.lower())
            target_entity = entity_lookup.get(target_text.lower())
            
            if source_entity:
                enhanced_relationship["source_entity_info"] = source_entity
                enhanced_relationship["source_entity_id"] = source_entity.get("id")
                enhanced_relationship["source_ontology_class_id"] = source_entity.get("ontology_class_id")
            
            if target_entity:
                enhanced_relationship["target_entity_info"] = target_entity
                enhanced_relationship["target_entity_id"] = target_entity.get("id")
                enhanced_relationship["target_ontology_class_id"] = target_entity.get("ontology_class_id")
            
            # Get ontology property information from database if mapped
            ontology_property_id = relationship.get("ontology_property_id")
            if ontology_property_id:
                try:
                    supabase = await get_supabase()
                    response = await supabase.from_("ontology_properties").select("*").eq("id", ontology_property_id).single().execute()
                    
                    if response.data:
                        ontology_property = response.data
                        enhanced_relationship["ontology_property_info"] = ontology_property
                        enhanced_relationship["is_mapped"] = True
                        enhanced_relationship["ontology_property_uri"] = ontology_property.get("uri")
                    else:
                        enhanced_relationship["is_mapped"] = False
                        
                except Exception as e:
                    logger.warning(f"Could not find ontology property {ontology_property_id}: {e}")
                    enhanced_relationship["is_mapped"] = False
            else:
                enhanced_relationship["is_mapped"] = False
                
                # Try to suggest mapping if not mapped
                relationship_type = relationship.get("relationship_type", "")
                if relationship_type and source_entity and target_entity:
                    source_type = source_entity.get("entity_type", "")
                    target_type = target_entity.get("entity_type", "")
                    
                    suggestions = await self._suggest_ontology_property_mapping(
                        relationship_type=relationship_type,
                        source_entity_type=source_type,
                        target_entity_type=target_type,
                        max_suggestions=3
                    )
                    enhanced_relationship["mapping_suggestions"] = suggestions
            
            enhanced_relationships.append(enhanced_relationship)
        
        return enhanced_relationships

    async def _suggest_ontology_property_mapping(
        self,
        relationship_type: str,
        source_entity_type: str,
        target_entity_type: str,
        max_suggestions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest ontology property mappings for a relationship using database
        """
        try:
            supabase = await get_supabase()
            
            suggestions = []
            
            # First try exact label match
            response = await supabase.from_("ontology_properties").select("*").ilike("label", f"%{relationship_type}%").limit(max_suggestions).execute()
            
            for prop in response.data:
                suggestions.append({
                    "ontology_property_id": prop["id"],
                    "label": prop["label"],
                    "uri": prop["uri"],
                    "description": prop.get("description"),
                    "similarity_score": 0.9,
                    "match_type": "label_match"
                })
            
            # If not enough suggestions, try description search
            if len(suggestions) < max_suggestions:
                remaining = max_suggestions - len(suggestions)
                response = await supabase.from_("ontology_properties").select("*").ilike("description", f"%{relationship_type}%").limit(remaining).execute()
                
                for prop in response.data:
                    # Avoid duplicates
                    if not any(s["ontology_property_id"] == prop["id"] for s in suggestions):
                        suggestions.append({
                            "ontology_property_id": prop["id"],
                            "label": prop["label"],
                            "uri": prop["uri"],
                            "description": prop.get("description"),
                            "similarity_score": 0.7,
                            "match_type": "description_match"
                        })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting ontology property mapping: {e}")
            return []

    async def _extract_relationships_traditional(
        self, 
        text: str, 
        entities: List[Dict[str, Any]],
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Traditional relationship extraction using existing ontology for guidance with Vietnamese support
        """
        if not self.openai_client:
            return self._extract_relationships_with_vietnamese_rules(text, entities)
        
        try:
            # Get ontology context from database
            ontology_context = await self.ontogpt_service.get_ontology_context(domain)
            
            # Prepare property information for prompt with Vietnamese labels
            properties_info = []
            for prop_id, info in list(ontology_context["properties"].items())[:30]:  # Limit to avoid token overflow
                label = info.get("label", f"Property_{prop_id}")
                desc = info.get("description", "")
                prop_type = info.get("property_type", "")
                
                prop_desc = f"- {label} ({prop_type})"
                if desc:
                    prop_desc += f": {desc}"
                
                properties_info.append(prop_desc)
            
            # Prepare entity information for prompt
            entity_info = []
            for i, entity in enumerate(entities):
                entity_text = entity.get("text", entity.get("entity_text", ""))
                entity_type = entity.get("entity_type", "")
                entity_info.append(f"Thực thể {i+1}: {entity_text} (Loại: {entity_type})")
            
            entity_text = "\n".join(entity_info)
            
            system_prompt = f"""
            Bạn là một hệ thống trích xuất mối quan hệ chuyên nghiệp cho tiếng Việt trong lĩnh vực ngân hàng.
            
            Sử dụng các loại mối quan hệ sau từ ontology hiện có:
            {chr(10).join(properties_info)}
            
            Hướng dẫn trích xuất mối quan hệ:
            1. Xác định mối quan hệ giữa các thực thể đã được trích xuất
            2. Chọn loại mối quan hệ phù hợp nhất từ danh sách ontology
            3. Đảm bảo mối quan hệ có cơ sở trong văn bản
            4. Đánh giá độ tin cậy từ 0.0 đến 1.0
            5. Nếu có thể, xác định ID của ontology property tương ứng
            
            Chú ý đặc biệt với các mối quan hệ tiếng Việt:
            - "có tài khoản tại" → has_account_at
            - "là khách hàng của" → is_customer_of
            - "chuyển tiền cho" → transfers_money_to
            - "cung cấp dịch vụ cho" → provides_service_to
            - "thuộc về" → belongs_to
            - "quản lý" → manages
            - "thực hiện giao dịch tại" → performs_transaction_at
            
            Chỉ trả về các mối quan hệ có cơ sở rõ ràng trong văn bản.
            
            OUTPUT FORMAT (JSON):
            {{
                "relationships": [
                    {{
                        "source_entity": "văn bản thực thể nguồn",
                        "target_entity": "văn bản thực thể đích",
                        "relationship_type": "loại từ ontology",
                        "ontology_property_id": ID_hoặc_null,
                        "ontology_property_uri": "URI hoặc null",
                        "confidence": điểm_tin_cậy
                    }}
                ]
            }}
            """
            
            user_prompt = f"""Văn bản để phân tích:
            {text}
            
            Các thực thể đã trích xuất:
            {entity_text}
            
            Hãy trích xuất tất cả các mối quan hệ giữa các thực thể từ văn bản tiếng Việt này.
            Đặc biệt chú ý đến các cụm từ chỉ mối quan hệ trong tiếng Việt.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            relationships = result.get("relationships", [])
            
            # Try to match ontology property ID if not provided
            for relationship in relationships:
                relationship["extraction_method"] = "traditional_llm"
                
                if not relationship.get("ontology_property_id") and relationship.get("relationship_type"):
                    ontology_property_id = await self._find_ontology_property_id(
                        relationship["relationship_type"], ontology_context
                    )
                    if ontology_property_id:
                        relationship["ontology_property_id"] = ontology_property_id
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error in traditional relationship extraction: {e}")
            return self._extract_relationships_with_vietnamese_rules(text, entities)

    async def _find_ontology_property_id(
        self, 
        relationship_type: str, 
        ontology_context: Dict[str, Any]
    ) -> Optional[int]:
        """Find ontology property ID by label"""
        for prop_id, info in ontology_context["properties"].items():
            if info.get("label", "").lower() == relationship_type.lower():
                return prop_id
        return None

    def _extract_relationships_with_vietnamese_rules(
        self, 
        text: str, 
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships using Vietnamese rule-based patterns (fallback method)
        """
        relationships = []
        
        # Group entities by type for easier access
        entities_by_type = {}
        entity_positions = {}  # Track entity positions in text
        
        for entity in entities:
            entity_text = entity.get("text", entity.get("entity_text", ""))
            entity_type = entity.get("entity_type", "")
            
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)
            
            # Store position information
            entity_positions[entity_text.lower()] = {
                "entity": entity,
                "start": entity.get("start_position", 0),
                "end": entity.get("end_position", len(entity_text))
            }
        
        # Apply each relation pattern to extract relationships
        for pattern_info in VIETNAMESE_BANKING_RELATION_PATTERNS:
            matches = re.finditer(pattern_info["pattern"], text, re.IGNORECASE | re.UNICODE)
            
            for match in matches:
                try:
                    # Extract groups based on pattern
                    groups = match.groups()
                    if len(groups) >= 2:
                        source_text = groups[0].strip()
                        target_text = groups[-1].strip()  # Last group is usually target
                        
                        # Handle specific patterns
                        if len(groups) >= 4 and "tài khoản" in pattern_info["pattern"]:
                            # Pattern with account: person + action + account + location
                            source_text = groups[0].strip()
                            if groups[3]:  # Account number
                                target_text = f"tài khoản {groups[3]}"
                            else:
                                target_text = "tài khoản"
                        elif len(groups) >= 3:
                            # Pattern with middle element: source + action + object + target
                            source_text = groups[0].strip()
                            target_text = groups[-1].strip()
                        
                        # Find the corresponding entities
                        source_entity = self._find_best_matching_entity(
                            source_text, entities_by_type.get(pattern_info["source_type"], [])
                        )
                        target_entity = self._find_best_matching_entity(
                            target_text, entities_by_type.get(pattern_info["target_type"], [])
                        )
                        
                        if source_entity and target_entity:
                            relationships.append({
                                "source_entity_id": source_entity.get("id"),
                                "target_entity_id": target_entity.get("id"),
                                "source_entity": source_entity.get("text", source_entity.get("entity_text", "")),
                                "target_entity": target_entity.get("text", target_entity.get("entity_text", "")),
                                "relationship_type": pattern_info["relation_type"],
                                "ontology_property_id": None,
                                "ontology_property_uri": None,
                                "confidence": pattern_info["confidence"],
                                "is_mapped": False,
                                "extraction_method": "vietnamese_rules",
                                "pattern_matched": pattern_info["pattern"]
                            })
                            
                except Exception as e:
                    logger.warning(f"Error processing relationship pattern match: {e}")
                    continue
        
        # Extract co-occurrence relationships with Vietnamese context
        co_occurrence_relationships = self._extract_vietnamese_co_occurrence_relationships(text, entities)
        relationships.extend(co_occurrence_relationships)
        
        # Remove duplicates
        relationships = self._remove_duplicate_relationships(relationships)
        
        return relationships

    def _find_best_matching_entity(
        self, 
        text: str, 
        entities: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the entity that best matches the given text with Vietnamese-specific matching
        """
        text = text.lower().strip()
        
        # Remove common Vietnamese prefixes/suffixes
        text = re.sub(r'^(ông|bà|anh|chị|em|cô|chú|bác)\s+', '', text)
        text = re.sub(r'\s+(ạ|à|ơi|nhé)$', '', text)
        
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
        self, 
        text: str, 
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships based on entity co-occurrence within Vietnamese sentences
        """
        relationships = []
        
        # Split text into Vietnamese sentences
        sentences = re.split(r'[.!?]+|(?<=[。！？])', text)
        
        for sentence in sentences:
            sentence_entities = []
            
            # Find entities in this sentence
            for entity in entities:
                entity_text = entity.get("text", entity.get("entity_text", ""))
                if entity_text.lower() in sentence.lower():
                    sentence_entities.append(entity)
            
            # Create relationships between co-occurring entities
            for i, entity1 in enumerate(sentence_entities):
                for entity2 in sentence_entities[i+1:]:
                    entity1_type = entity1.get("entity_type", "")
                    entity2_type = entity2.get("entity_type", "")
                    
                    # Skip entities of the same type
                    if entity1_type == entity2_type:
                        continue
                    
                    relationship_type = self._determine_vietnamese_co_occurrence_relationship_type(
                        entity1, entity2, sentence
                    )
                    
                    if relationship_type:
                        relationships.append({
                            "source_entity_id": entity1.get("id"),
                            "target_entity_id": entity2.get("id"),
                            "source_entity": entity1.get("text", entity1.get("entity_text", "")),
                            "target_entity": entity2.get("text", entity2.get("entity_text", "")),
                            "relationship_type": relationship_type,
                            "ontology_property_id": None,
                            "ontology_property_uri": None,
                            "confidence": 0.5,  # Lower confidence for co-occurrence relationships
                            "is_mapped": False,
                            "extraction_method": "vietnamese_cooccurrence"
                        })
        
        return relationships

    def _determine_vietnamese_co_occurrence_relationship_type(
        self, 
        entity1: Dict[str, Any], 
        entity2: Dict[str, Any],
        sentence: str
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
            "transfers_to": ["chuyển", "gửi", "thanh toán"]
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
            ("Bank", "Location"): "located_at"
        }
        
        return relationship_map.get((type1, type2), "related_to")

    def _entity_types_match_relationship(
        self, 
        type1: str, 
        type2: str, 
        relationship: str
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
            "transfers_to": [("Person", "Person"), ("Account", "Account")]
        }
        
        allowed_types = type_constraints.get(relationship, [])
        return (type1, type2) in allowed_types or (type2, type1) in allowed_types

    def _remove_duplicate_relationships(
        self, 
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate relationships, keeping the one with higher confidence
        """
        seen_relationships = {}
        unique_relationships = []
        
        for rel in relationships:
            # Create a key based on source, target, and relationship type
            key = (
                rel.get("source_entity", "").lower(),
                rel.get("target_entity", "").lower(),
                rel.get("relationship_type", "")
            )
            
            if key not in seen_relationships:
                seen_relationships[key] = rel
                unique_relationships.append(rel)
            else:
                # Keep the one with higher confidence
                existing_confidence = seen_relationships[key].get("confidence", 0)
                new_confidence = rel.get("confidence", 0)
                
                if new_confidence > existing_confidence:
                    # Replace the existing one
                    unique_relationships = [r for r in unique_relationships if r != seen_relationships[key]]
                    seen_relationships[key] = rel
                    unique_relationships.append(rel)
        
        return unique_relationships

    async def validate_relationships_against_ontology(
        self, 
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate extracted relationships against current ontology from database
        """
        try:
            validation_result = await self.ontogpt_service.validate_extraction_against_ontology(
                entities=[],  # Only validating relationships here
                relationships=relationships
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating relationships: {e}")
            return {"relationship_validations": [], "overall_score": 0.0}

    async def get_relationship_mapping_suggestions(
        self, 
        relationship_type: str,
        source_entity_type: Optional[str] = None,
        target_entity_type: Optional[str] = None,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get suggestions for mapping a relationship to ontology properties from database
        """
        try:
            suggestions = await self._suggest_ontology_property_mapping(
                relationship_type=relationship_type,
                source_entity_type=source_entity_type or "",
                target_entity_type=target_entity_type or "",
                max_suggestions=max_suggestions
            )
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting relationship mapping suggestions: {e}")
            return []

    async def save_extraction_results(
        self, 
        relationships: List[Dict[str, Any]],
        extraction_result_id: int
    ) -> List[int]:
        """
        Save relationship extraction results to database with proper ontology mapping
        
        Args:
            relationships: Extracted relationships
            extraction_result_id: ID of the parent extraction result
            
        Returns:
            List of saved relationship IDs
        """
        try:
            supabase = await get_supabase()

            logger.info(f"Saving {relationships} relationships to database for extraction result {extraction_result_id}")
            
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
                    f"Target entity ID: {target_entity_id}, "
                                        )
                
                relationship_data = {
                    "source_entity_id": source_entity_id,
                    "target_entity_id": target_entity_id,
                    "ontology_property_id": relationship.get("ontology_property_id"),
                    "properties": {
                        "relationship_type": relationship.get("relationship_type"),
                        "extraction_method": relationship.get("extraction_method"),
                        "pattern_matched": relationship.get("pattern_matched"),
                        "source_entity_text": relationship.get("source_entity"),
                        "target_entity_text": relationship.get("target_entity")
                    },
                    "confidence": relationship.get("confidence"),
                    "extraction_confidence": relationship.get("confidence"),
                    "is_verified": False,
                    "validation_status": "pending"
                }

                logger.info(f"Saving relationship: {relationship_data}")
                
                response = await supabase.from_("kg_relationships").insert(
                    relationship_data
                ).execute()
                
                if response.data:
                    relationship_ids.append(response.data[0]["id"])
            
            logger.info(f"Saved {len(relationship_ids)} relationships to database")
            return relationship_ids
            
        except Exception as e:
            logger.error(f"Error saving relationship extraction results: {e}")
            raise

    async def _find_kg_entity_id(
        self, 
        entity_text: str, 
        extraction_result_id: int
    ) -> Optional[str]:
        """
        Find the corresponding kg_entities ID for an entity text
        """
        try:
            supabase = await get_supabase()
            
            # First try to find entity from the same extraction
            response = await supabase.from_("kg_entities").select("id").eq("entity_text", entity_text).limit(1).execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # If not found, try fuzzy matching
            response = await supabase.from_("kg_entities").select("id, entity_text").ilike("entity_text", f"%{entity_text}%").limit(5).execute()
            
            for entity in response.data:
                if self._vietnamese_similarity(entity_text.lower(), entity["entity_text"].lower()) > 0.8:
                    return entity["id"]
            
            return None
            
        except Exception as e:
            logger.warning(f"Error finding kg_entity_id for {entity_text}: {e}")
            return None

    async def suggest_missing_relationships(
        self, 
        extraction_result_id: int
    ) -> List[Dict[str, Any]]:
        """
        Suggest missing relationships for a knowledge graph using Vietnamese domain knowledge
        """
        try:
            suggestions = await self.ontogpt_service.suggest_knowledge_graph_completion(
                extraction_result_id=extraction_result_id
            )
            
            return suggestions.get("missing_relationships", [])
            
        except Exception as e:
            logger.error(f"Error suggesting missing relationships: {e}")
            return []

    def merge_relationship_lists(
        self, 
        list1: List[Dict[str, Any]], 
        list2: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge two relationship lists, avoiding duplicates with Vietnamese-aware comparison
        """
        merged = list(list1)  # Start with a copy of the first list
        
        # Function to check if two relationships are duplicates
        def relationships_match(r1, r2):
            return (
                self._vietnamese_similarity(
                    r1.get("source_entity", "").lower(), 
                    r2.get("source_entity", "").lower()
                ) > 0.9 and
                self._vietnamese_similarity(
                    r1.get("target_entity", "").lower(), 
                    r2.get("target_entity", "").lower()
                ) > 0.9 and
                r1.get("relationship_type") == r2.get("relationship_type")
            )
        
        # Add relationships from list2 that don't duplicate any in list1
        for rel2 in list2:
            if not any(relationships_match(rel1, rel2) for rel1 in list1):
                merged.append(rel2)
        
        return merged

    async def get_relationship_statistics(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about extracted relationships
        """
        try:
            supabase = await get_supabase()
            
            # Get relationship counts by type
            query = supabase.from_("kg_relationships").select("ontology_property_id, ontology_properties(label, domain)")
            if domain:
                query = query.eq("ontology_properties.domain", domain)
            
            response = await query.execute()
            
            # Count relationships by type
            relationship_counts = {}
            total_relationships = len(response.data)
            mapped_relationships = 0
            
            for rel in response.data:
                if rel.get("ontology_property_id"):
                    mapped_relationships += 1
                    prop_info = rel.get("ontology_properties")
                    if prop_info:
                        label = prop_info.get("label", "Unknown")
                        relationship_counts[label] = relationship_counts.get(label, 0) + 1
            
            return {
                "total_relationships": total_relationships,
                "mapped_relationships": mapped_relationships,
                "mapping_percentage": (mapped_relationships / total_relationships * 100) if total_relationships > 0 else 0,
                "relationship_type_counts": relationship_counts,
                "domain": domain
            }
            
        except Exception as e:
            logger.error(f"Error getting relationship statistics: {e}")
            return {}
