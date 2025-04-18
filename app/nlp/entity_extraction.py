from typing import List, Dict, Any, Optional
import logging
import os
import json
import re
import time
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

# Fallback regex patterns for basic entity extraction (in case OpenAI is unavailable)
BANKING_ENTITY_PATTERNS = {
    "Bank": r"\b(VietinBank|BIDV|Vietcombank|ACB|MB Bank|Techcombank|VPBank|HD Bank|TPBank|SeABank|VIB|OCB)\b",
    "Person": r"\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b",
    "Account": r"\b(\d{10,14})\b",
    "Money": r"\b(\d+(?:,\d+)*(?:\.\d+)?(?:\s?(?:VND|USD|triệu đồng|tỷ đồng)))\b",
    "Date": r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
    "Product": r"\b(thẻ tín dụng|thẻ ghi nợ|tiết kiệm|vay thế chấp|vay tín chấp|bảo hiểm nhân thọ|quỹ đầu tư)\b"
}

# Initialize OpenAI client
openai_client = None
if OPENAI_AVAILABLE:
    try:
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if openai_api_key:
            openai_client = OpenAI(api_key=openai_api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables")
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")

# Define entity types for banking domain
BANKING_ENTITY_TYPES = [
    "Bank", "Person", "Account", "CreditCard", "DebitCard", "Loan", "Deposit", "Investment", 
    "Insurance", "Transaction", "Date", "Money", "InterestRate", "Fee", "Branch", "ATM",
    "IdentificationDocument", "PhoneNumber", "Email", "Address", "Organization"
]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def extract_entities_with_openai(text: str) -> List[Dict[str, Any]]:
    """
    Extract entities using OpenAI API.
    
    Args:
        text: Input text
        
    Returns:
        List of extracted entities
    """
    if not openai_client:
        raise ValueError("OpenAI client not initialized")
    
    try:
        # Prepare the system prompt for entity extraction
        system_prompt = f"""
        Bạn là một hệ thống trích xuất thực thể ngân hàng cho tiếng Việt.
        Nhiệm vụ của bạn là phân tích văn bản và xác định tất cả các thực thể theo các loại sau:
        {', '.join(BANKING_ENTITY_TYPES)}
        
        Đối với mỗi thực thể được tìm thấy, hãy cung cấp:
        1. Văn bản thực thể chính xác
        2. Loại thực thể
        3. Vị trí bắt đầu (ký tự) trong văn bản gốc
        4. Điểm tin cậy (0.0-1.0)
        
        Đáp ứng đầu ra ở định dạng JSON với dạng sau:
        [
            {{"entity_text": "text", "entity_type": "type", "start_position": position, "confidence": score}}
        ]
        """
        
        user_prompt = f"""Văn bản để phân tích:
        {text}
        
        Hãy trích xuất tất cả các thực thể liên quan đến ngân hàng và tài chính từ văn bản trên.
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
        
        # Extract the entities
        if "entities" in result:
            entities = result["entities"]
        else:
            # Try to extract the JSON array directly
            return json.loads(content)
        
        # Calculate end positions
        for entity in entities:
            if "start_position" in entity and "entity_text" in entity:
                entity["end_position"] = entity["start_position"] + len(entity["entity_text"])
        
        return entities
    
    except Exception as e:
        logger.error(f"Error in OpenAI entity extraction: {e}")
        raise

async def extract_entities(text: str) -> List[Dict[str, Any]]:
    """
    Extract entities from text using OpenAI if available, otherwise fall back to regex.
    
    Args:
        text: Input text
        
    Returns:
        List of extracted entities
    """
    if OPENAI_AVAILABLE and openai_client:
        try:
            return await extract_entities_with_openai(text)
        except Exception as e:
            logger.error(f"OpenAI extraction failed, falling back to regex: {e}")
            return extract_entities_with_regex(text)
    else:
        return extract_entities_with_regex(text)

def extract_entities_with_regex(text: str) -> List[Dict[str, Any]]:
    """
    Extract entities using regex patterns.
    
    Args:
        text: Input text
        
    Returns:
        List of extracted entities
    """
    entities = []
    
    # Apply each regex pattern to extract entities
    for entity_type, pattern in BANKING_ENTITY_PATTERNS.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            entities.append({
                "entity_text": match.group(),
                "entity_type": entity_type,
                "start_position": match.start(),
                "end_position": match.end(),
                "confidence": 0.6  # Lower confidence for regex-based entities
            })
    
    return entities

def load_custom_entity_types(path: str = None) -> Dict[str, str]:
    """
    Load custom entity types from a configuration file.
    
    Args:
        path: Path to the configuration file
        
    Returns:
        Dictionary of entity type patterns
    """
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "config", "entity_types.json")
    
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                custom_types = json.load(f)
            
            logger.info(f"Loaded {len(custom_types)} custom entity types")
            return custom_types
        else:
            logger.warning(f"Custom entity types file not found: {path}")
            return {}
    
    except Exception as e:
        logger.error(f"Error loading custom entity types: {e}")
        return {}
