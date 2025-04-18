from typing import List, Dict, Any, Optional, Tuple
import logging
import os
import json
import re
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI is not installed. Install with: pip install openai")

# Try to import OpenRE
try:
    # This is just a placeholder - you'll need to implement the actual import for OpenRE
    # or whichever relation extraction library you decide to use for Vietnamese
    import openre  # or another suitable relation extraction library
    OPENRE_AVAILABLE = True
except ImportError:
    OPENRE_AVAILABLE = False
    logger.warning("OpenRE is not installed. Relation extraction will use fallback methods.")

# Initialize OpenAI client
openai_client = None
if OPENAI_AVAILABLE:
    try:
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if openai_api_key:
            openai_client = OpenAI(api_key=openai_api_key)
            logger.info("OpenAI client initialized for relation extraction")
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables")
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")

# Fallback patterns for basic relation extraction
BANKING_RELATION_PATTERNS = [
    {
        "pattern": r"(.*)\s(mở|có|sở hữu)\s(.*)\stại\s(.*)",
        "source_type": "Person",
        "target_type": "Account",
        "relation_type": "owns_account"
    },
    {
        "pattern": r"(.*)\s(chuyển|gửi)\s(.*)\scho\s(.*)",
        "source_type": "Person",
        "target_type": "Person",
        "relation_type": "transfers_money_to"
    },
    {
        "pattern": r"(.*)\s(là khách hàng của|sử dụng dịch vụ của)\s(.*)",
        "source_type": "Person",
        "target_type": "Bank",
        "relation_type": "is_customer_of"
    },
    {
        "pattern": r"(.*)\s(cung cấp|phát hành)\s(.*)\scho\s(.*)",
        "source_type": "Bank",
        "target_type": "Person",
        "relation_type": "provides_product_to"
    }
]

# Define common banking relationships for GPT prompt
BANKING_RELATIONSHIPS = [
    "owns_account", "is_customer_of", "has_loan_with", "deposits_money_at", 
    "withdraws_money_from", "transfers_money_to", "provides_service_to", 
    "works_for", "manages", "located_in", "has_branch_at", "offers_product",
    "uses_product", "pays_interest_to", "charges_fee_to", "guarantees",
    "insures"
]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def extract_relationships_with_openai(text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract relationships using OpenAI API.
    
    Args:
        text: Input text
        entities: List of extracted entities
        
    Returns:
        List of extracted relationships
    """
    if not openai_client:
        raise ValueError("OpenAI client not initialized")
    
    try:
        # Prepare entity information for the prompt
        entity_info = []
        for i, entity in enumerate(entities):
            entity_info.append(f"Entity {i+1}: {entity['entity_text']} (Type: {entity['entity_type']})")
        
        entity_text = "\n".join(entity_info)
        
        # Prepare the system prompt
        system_prompt = f"""
        Bạn là một hệ thống trích xuất mối quan hệ cho tiếng Việt trong lĩnh vực ngân hàng.
        Nhiệm vụ của bạn là phân tích văn bản và xác định các mối quan hệ giữa các thực thể.
        Các loại mối quan hệ phổ biến trong ngân hàng bao gồm:
        {', '.join(BANKING_RELATIONSHIPS)}
        
        Cho một danh sách các thực thể đã được trích xuất, hãy xác định mối quan hệ giữa chúng.
        Đối với mỗi mối quan hệ, hãy cung cấp:
        1. Thực thể nguồn (source_entity)
        2. Thực thể đích (target_entity)
        3. Loại mối quan hệ (relationship_type)
        4. Điểm tin cậy (confidence) từ 0.0 đến 1.0
        
        Chỉ trả về các mối quan hệ có cơ sở trong văn bản, đừng tạo ra mối quan hệ không tồn tại.
        
        Đáp ứng đầu ra ở định dạng JSON với dạng sau:
        {{
            "relationships": [
                {{
                    "source_entity": "text",
                    "target_entity": "text",
                    "relationship_type": "type",
                    "confidence": score
                }}
            ]
        }}
        """
        
        user_prompt = f"""Văn bản để phân tích:
        {text}
        
        Các thực thể đã trích xuất:
        {entity_text}
        
        Hãy trích xuất tất cả các mối quan hệ giữa các thực thể từ văn bản này.
        """
        
        # Make the API call
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",  # or use a more appropriate model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        # Process the response
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Extract the relationships
        relationships = result.get("relationships", [])
        
        # Add placeholder IDs for source and target entities
        for rel in relationships:
            rel["source_entity_id"] = None  # Will be filled when entities are stored
            rel["target_entity_id"] = None  # Will be filled when entities are stored
        
        return relationships
    
    except Exception as e:
        logger.error(f"Error in OpenAI relation extraction: {e}")
        raise

async def extract_relationships_with_openre(text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract relationships using OpenRE or a similar Vietnamese NLP model.
    
    Args:
        text: Input text
        entities: List of extracted entities
        
    Returns:
        List of extracted relationships
    """
    # This is a placeholder - you would need to implement the actual OpenRE integration
    # based on the specific library or model you select for Vietnamese relation extraction
    
    # Example implementation structure:
    try:
        # 1. Prepare the text and entities for OpenRE
        # 2. Call the OpenRE model
        # 3. Process the results into the expected format
        
        # Since this is a placeholder, we'll just return an empty list for now
        logger.warning("OpenRE extraction not yet implemented, using fallback methods")
        return []
    
    except Exception as e:
        logger.error(f"Error in OpenRE relation extraction: {e}")
        # Fall back to rule-based extraction
        return extract_relationships_with_rules(text, entities)

async def extract_relationships(text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract relationships between entities in text.
    
    Args:
        text: Input text
        entities: List of extracted entities
        
    Returns:
        List of extracted relationships
    """
    # First try OpenAI if available
    if OPENAI_AVAILABLE and openai_client:
        try:
            return await extract_relationships_with_openai(text, entities)
        except Exception as e:
            logger.error(f"OpenAI relation extraction failed, trying next method: {e}")
    
    # Then try OpenRE if available
    if OPENRE_AVAILABLE:
        try:
            return await extract_relationships_with_openre(text, entities)
        except Exception as e:
            logger.error(f"OpenRE extraction failed, falling back to rules: {e}")
    
    # Fall back to rule-based methods
    return extract_relationships_with_rules(text, entities)

# The extract_relationships_with_rules function and other helper functions remain the same
def extract_relationships_with_rules(text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract relationships using rule-based patterns.
    
    Args:
        text: Input text
        entities: List of extracted entities
        
    Returns:
        List of extracted relationships
    """
    relationships = []
    
    # Group entities by type for easier access
    entities_by_type = {}
    for entity in entities:
        entity_type = entity["entity_type"]
        if entity_type not in entities_by_type:
            entities_by_type[entity_type] = []
        entities_by_type[entity_type].append(entity)
    
    # Apply each relation pattern to extract relationships
    for pattern_info in BANKING_RELATION_PATTERNS:
        matches = re.finditer(pattern_info["pattern"], text, re.IGNORECASE)
        
        for match in matches:
            # Extract the matched groups
            if len(match.groups()) >= 4:
                source_text = match.group(1).strip()
                relation_verb = match.group(2).strip()
                target_text = match.group(3).strip()
                context = match.group(4).strip() if len(match.groups()) >= 4 else ""
                
                # Find the corresponding entities
                source_entity = find_matching_entity(source_text, entities_by_type.get(pattern_info["source_type"], []))
                target_entity = find_matching_entity(target_text, entities_by_type.get(pattern_info["target_type"], []))
                
                if source_entity and target_entity:
                    relationships.append({
                        "source_entity_id": None,  # Will be filled when entities are stored
                        "target_entity_id": None,  # Will be filled when entities are stored
                        "source_entity": source_entity["entity_text"],
                        "target_entity": target_entity["entity_text"],
                        "relationship_type": pattern_info["relation_type"],
                        "confidence": 0.6  # Lower confidence for rule-based relationships
                    })
    
    # Extract co-occurrence relationships
    co_occurrence_relationships = extract_co_occurrence_relationships(text, entities)
    relationships.extend(co_occurrence_relationships)
    
    return relationships

def find_matching_entity(text: str, entities: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Find the entity that best matches the given text.
    
    Args:
        text: Text to match
        entities: List of entities to search
        
    Returns:
        Matching entity or None if no match is found
    """
    text = text.lower().strip()
    
    # Direct match
    for entity in entities:
        if entity["entity_text"].lower() == text:
            return entity
    
    # Partial match
    for entity in entities:
        if text in entity["entity_text"].lower() or entity["entity_text"].lower() in text:
            return entity
    
    return None

def extract_co_occurrence_relationships(text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract relationships based on entity co-occurrence within the same sentence.
    
    Args:
        text: Input text
        entities: List of extracted entities
        
    Returns:
        List of co-occurrence relationships
    """
    relationships = []
    
    # Split text into sentences
    sentences = re.split(r'[.!?]+', text)
    
    for sentence in sentences:
        sentence_entities = []
        
        # Find entities in this sentence
        for entity in entities:
            start = entity["start_position"]
            end = entity["end_position"]
            
            # Check if the entity is within the current sentence
            sentence_start = text.find(sentence)
            sentence_end = sentence_start + len(sentence)
            
            if start >= sentence_start and end <= sentence_end:
                sentence_entities.append(entity)
        
        # Create relationships between co-occurring entities
        for i, entity1 in enumerate(sentence_entities):
            for entity2 in sentence_entities[i+1:]:
                # Skip entities of the same type
                if entity1["entity_type"] == entity2["entity_type"]:
                    continue
                
                relationship_type = determine_co_occurrence_relationship_type(entity1, entity2)
                
                relationships.append({
                    "source_entity_id": None,
                    "target_entity_id": None,
                    "source_entity": entity1["entity_text"],
                    "target_entity": entity2["entity_text"],
                    "relationship_type": relationship_type,
                    "confidence": 0.5  # Lower confidence for co-occurrence relationships
                })
    
    return relationships

def determine_co_occurrence_relationship_type(entity1: Dict[str, Any], entity2: Dict[str, Any]) -> str:
    """
    Determine the relationship type between co-occurring entities based on their types.
    
    Args:
        entity1: First entity
        entity2: Second entity
        
    Returns:
        Relationship type
    """
    type1 = entity1["entity_type"]
    type2 = entity2["entity_type"]
    
    # Define relationship types based on entity type pairs
    relationship_map = {
        ("Person", "Bank"): "associated_with",
        ("Bank", "Person"): "serves",
        ("Person", "Account"): "has_account",
        ("Account", "Person"): "belongs_to",
        ("Bank", "Product"): "offers",
        ("Product", "Bank"): "offered_by",
        ("Person", "Product"): "uses",
        ("Product", "Person"): "used_by"
    }
    
    return relationship_map.get((type1, type2), "related_to")

def merge_relationship_lists(list1: List[Dict[str, Any]], list2: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge two relationship lists, avoiding duplicates.
    
    Args:
        list1: First list of relationships
        list2: Second list of relationships
        
    Returns:
        Merged list of relationships
    """
    merged = list(list1)  # Start with a copy of the first list
    
    # Function to check if two relationships are duplicates
    def relationships_match(r1, r2):
        return (r1["source_entity"] == r2["source_entity"] and 
                r1["target_entity"] == r2["target_entity"] and 
                r1["relationship_type"] == r2["relationship_type"])
    
    # Add relationships from list2 that don't duplicate any in list1
    for rel2 in list2:
        if not any(relationships_match(rel1, rel2) for rel1 in list1):
            merged.append(rel2)
    
    return merged
