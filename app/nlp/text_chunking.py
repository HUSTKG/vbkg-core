from typing import List, Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

# Try to import spaCy for better sentence segmentation
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy is not installed. Text chunking will use simple methods.")

# Default parameters for chunking
DEFAULT_CHUNK_SIZE = 1000  # characters
DEFAULT_CHUNK_OVERLAP = 200  # characters
DEFAULT_CHUNK_MIN_SIZE = 100  # minimum characters for a valid chunk

# Load spaCy model for sentence splitting if available
nlp_sentences = None
if SPACY_AVAILABLE:
    try:
        # Use a small model just for sentence segmentation
        nlp_sentences = spacy.load("xx_ent_wiki_sm")
        logger.info("Loaded spaCy model for sentence segmentation")
    except OSError:
        logger.warning("spaCy model not found for sentence segmentation")

def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    min_chunk_size: int = DEFAULT_CHUNK_MIN_SIZE
) -> List[str]:
    """
    Split text into overlapping chunks, trying to respect sentence boundaries.
    
    Args:
        text: Input text
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of overlapping characters between chunks
        min_chunk_size: Minimum size of a chunk to be included
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # Use spaCy for better sentence splitting if available
    if SPACY_AVAILABLE and nlp_sentences:
        return chunk_text_with_spacy(text, chunk_size, chunk_overlap, min_chunk_size)
    else:
        return chunk_text_simple(text, chunk_size, chunk_overlap, min_chunk_size)

def chunk_text_with_spacy(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int
) -> List[str]:
    """
    Split text into chunks using spaCy for sentence segmentation.
    
    Args:
        text: Input text
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of overlapping characters between chunks
        min_chunk_size: Minimum size of a chunk to be included
        
    Returns:
        List of text chunks
    """
    try:
        # Process the text to get sentence boundaries
        doc = nlp_sentences(text)
        sentences = list(doc.sents)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence_text = sentence.text
            
            # If adding this sentence would exceed the chunk size
            if len(current_chunk) + len(sentence_text) > chunk_size and current_chunk:
                # Add the current chunk if it's large enough
                if len(current_chunk) >= min_chunk_size:
                    chunks.append(current_chunk.strip())
                
                # Start a new chunk with overlap
                overlap_start = max(0, len(current_chunk) - chunk_overlap)
                current_chunk = current_chunk[overlap_start:] + sentence_text
            else:
                # Add the sentence to the current chunk
                current_chunk += sentence_text
        
        # Add the last chunk if it's not empty and large enough
        if current_chunk and len(current_chunk) >= min_chunk_size:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    except Exception as e:
        logger.error(f"Error in spaCy text chunking: {e}")
        # Fall back to simple chunking
        return chunk_text_simple(text, chunk_size, chunk_overlap, min_chunk_size)

def chunk_text_simple(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int
) -> List[str]:
    """
    Split text into chunks using simple regex-based sentence splitting.
    
    Args:
        text: Input text
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of overlapping characters between chunks
        min_chunk_size: Minimum size of a chunk to be included
        
    Returns:
        List of text chunks
    """
    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # If adding this sentence would exceed the chunk size
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            # Add the current chunk if it's large enough
            if len(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk.strip())
            
            # Start a new chunk with overlap
            overlap_start = max(0, len(current_chunk) - chunk_overlap)
            current_chunk = current_chunk[overlap_start:] + sentence
        else:
            # Add the sentence to the current chunk
            current_chunk += " " + sentence if current_chunk else sentence
    
    # Add the last chunk if it's not empty and large enough
    if current_chunk and len(current_chunk) >= min_chunk_size:
        chunks.append(current_chunk.strip())
    
    # If the text is too short to generate any chunks, just return the whole text
    if not chunks and len(text) >= min_chunk_size:
        chunks.append(text.strip())
    
    return chunks

def chunk_by_paragraphs(
    text: str,
    max_paragraphs_per_chunk: int = 5,
    min_paragraphs_per_chunk: int = 1
) -> List[str]:
    """
    Split text into chunks by paragraphs.
    
    Args:
        text: Input text
        max_paragraphs_per_chunk: Maximum number of paragraphs per chunk
        min_paragraphs_per_chunk: Minimum number of paragraphs per chunk
        
    Returns:
        List of text chunks
    """
    # Split text into paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    
    # Filter out empty paragraphs
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if not paragraphs:
        return []
    
    # If there are fewer paragraphs than the minimum, return the whole text
    if len(paragraphs) <= min_paragraphs_per_chunk:
        return [text.strip()]
    
    chunks = []
    current_paragraphs = []
    
    for paragraph in paragraphs:
        current_paragraphs.append(paragraph)
        
        if len(current_paragraphs) >= max_paragraphs_per_chunk:
            chunks.append("\n\n".join(current_paragraphs))
            current_paragraphs = []
    
    # Add the last chunk if not empty
    if current_paragraphs:
        chunks.append("\n\n".join(current_paragraphs))
    
    return chunks

def chunk_structured_data(data: Dict[str, Any], chunk_size: int = 50) -> List[Dict[str, Any]]:
    """
    Split structured data into chunks.
    
    Args:
        data: Structured data (e.g., from JSON or CSV)
        chunk_size: Maximum number of items per chunk
        
    Returns:
        List of data chunks
    """
    # Handle list of records (e.g., CSV rows or JSON array)
    if isinstance(data, list):
        chunks = []
        for i in range(0, len(data), chunk_size):
            chunks.append(data[i:i+chunk_size])
        return chunks
    
    # Handle nested dictionaries
    if isinstance(data, dict):
        # For simple key-value dictionaries, just return as is
        if all(not isinstance(v, (dict, list)) for v in data.values()):
            return [data]
        
        # For complex nested structures, split into chunks based on keys
        chunks = []
        current_chunk = {}
        current_size = 0
        
        for key, value in data.items():
            if isinstance(value, list) and len(value) > chunk_size:
                # Split large lists into chunks
                for i in range(0, len(value), chunk_size):
                    chunks.append({key: value[i:i+chunk_size]})
            elif current_size >= chunk_size:
                chunks.append(current_chunk)
                current_chunk = {key: value}
                current_size = 1
            else:
                current_chunk[key] = value
                current_size += 1
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    # Default: return as a single chunk
    return [data]
