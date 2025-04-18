from typing import List, Dict, Any, Optional, Union
import logging
import numpy as np
import os
import json
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

# Try to import sentence-transformers as fallback
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers is not installed. Will use OpenAI only.")

# Default embedding models
OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"  # or text-embedding-3-small, text-embedding-3-large
SENTENCE_TRANSFORMER_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Embedding model instances
openai_client = None
st_model = None

# Initialize OpenAI client
if OPENAI_AVAILABLE:
    try:
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if openai_api_key:
            openai_client = OpenAI(api_key=openai_api_key)
            logger.info("OpenAI client initialized for embeddings")
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables")
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")

# Initialize sentence-transformers model as fallback
if SENTENCE_TRANSFORMERS_AVAILABLE and not OPENAI_AVAILABLE:
    try:
        st_model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        logger.info(f"Loaded sentence-transformers model: {SENTENCE_TRANSFORMER_MODEL}")
    except Exception as e:
        logger.error(f"Error loading sentence-transformers model: {e}")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def get_openai_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding vector using OpenAI API.
    
    Args:
        text: Input text
        
    Returns:
        Embedding vector as a list of floats, or None if embedding fails
    """
    if not openai_client:
        raise ValueError("OpenAI client not initialized")
    
    try:
        model = os.environ.get("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
        
        # Make API call
        response = openai_client.embeddings.create(
            model=model,
            input=text
        )
        
        # Extract embedding vector
        embedding = response.data[0].embedding
        return embedding
    
    except Exception as e:
        logger.error(f"Error generating OpenAI embedding: {e}")
        raise

async def get_sentence_transformer_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding vector using sentence-transformers.
    
    Args:
        text: Input text
        
    Returns:
        Embedding vector as a list of floats, or None if embedding fails
    """
    global st_model
    
    if st_model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            st_model = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
        except Exception as e:
            logger.error(f"Error loading sentence-transformers model: {e}")
            return None
    
    if st_model is None:
        return None
    
    try:
        embedding = st_model.encode(text)
        return embedding.tolist()
    
    except Exception as e:
        logger.error(f"Error generating sentence-transformers embedding: {e}")
        return None

async def get_text_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding vector for a text string, using OpenAI if available.
    
    Args:
        text: Input text
        
    Returns:
        Embedding vector as a list of floats, or None if embedding fails
    """
    if OPENAI_AVAILABLE and openai_client:
        try:
            return await get_openai_embedding(text)
        except Exception as e:
            logger.error(f"OpenAI embedding failed, trying fallback: {e}")
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                return await get_sentence_transformer_embedding(text)
            return None
    elif SENTENCE_TRANSFORMERS_AVAILABLE:
        return await get_sentence_transformer_embedding(text)
    else:
        logger.error("No embedding models available")
        return None

async def batch_get_embeddings(texts: List[str]) -> List[Optional[List[float]]]:
    """
    Generate embedding vectors for a batch of texts.
    
    Args:
        texts: List of input texts
        
    Returns:
        List of embedding vectors, or None for texts that failed
    """
    if OPENAI_AVAILABLE and openai_client:
        try:
            model = os.environ.get("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
            
            # Make batch API call
            response = openai_client.embeddings.create(
                model=model,
                input=texts
            )
            
            # Extract embedding vectors in the correct order
            embeddings = [None] * len(texts)
            for item in response.data:
                embeddings[item.index] = item.embedding
                
            return embeddings
        
        except Exception as e:
            logger.error(f"Batch OpenAI embedding failed: {e}")
            
            # Fall back to sentence-transformers if available
            if SENTENCE_TRANSFORMERS_AVAILABLE and st_model:
                try:
                    embeddings = st_model.encode(texts)
                    return embeddings.tolist()
                except Exception as e2:
                    logger.error(f"Fallback batch embedding failed: {e2}")
    
    # Process each text individually
    results = []
    for text in texts:
        results.append(await get_text_embedding(text))
    
    return results

async def get_entity_embedding(entity: Dict[str, Any]) -> Optional[List[float]]:
    """
    Generate embedding vector for an entity.
    
    Args:
        entity: Entity dictionary with at least 'entity_text' field
        
    Returns:
        Embedding vector as a list of floats, or None if embedding fails
    """
    if "entity_text" not in entity:
        logger.error("Entity does not contain 'entity_text' field")
        return None
    
    # Include entity type in embedding text for better similarity matching
    if "entity_type" in entity:
        text = f"{entity['entity_type']}: {entity['entity_text']}"
    else:
        text = entity["entity_text"]
    
    return await get_text_embedding(text)

async def get_relationship_embedding(relationship: Dict[str, Any]) -> Optional[List[float]]:
    """
    Generate embedding vector for a relationship.
    
    Args:
        relationship: Relationship dictionary
        
    Returns:
        Embedding vector as a list of floats, or None if embedding fails
    """
    if not all(k in relationship for k in ["source_entity", "target_entity", "relationship_type"]):
        logger.error("Relationship missing required fields")
        return None
    
    # Create a text representation of the relationship
    text = f"{relationship['source_entity']} {relationship['relationship_type']} {relationship['target_entity']}"
    
    return await get_text_embedding(text)

async def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embedding vectors.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    try:
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return 0.0

# The rest of the functions remain the same as in the original embeddings.py
