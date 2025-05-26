import hashlib
import math
import re
from collections import Counter
from difflib import SequenceMatcher
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import Levenshtein
import numpy as np


class SimilarityMethod(str, Enum):
    """Available similarity calculation methods"""
    
    # Text similarity methods
    EXACT = "exact"
    FUZZY = "fuzzy"
    LEVENSHTEIN = "levenshtein"
    JARO_WINKLER = "jaro_winkler"
    SOUNDEX = "soundex"
    METAPHONE = "metaphone"
    
    # Vector similarity methods
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    MANHATTAN = "manhattan"
    DOT_PRODUCT = "dot_product"
    
    # Set similarity methods
    JACCARD = "jaccard"
    SORENSEN_DICE = "sorensen_dice"
    OVERLAP = "overlap"
    
    # Semantic similarity methods
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class SimilarityConfig:
    """Configuration for similarity calculations"""
    
    def __init__(
        self,
        fuzzy_threshold: float = 0.6,
        soundex_length: int = 4,
        jaro_winkler_prefix_scale: float = 0.1,
        cosine_epsilon: float = 1e-8,
        semantic_weight: float = 0.7,
        text_weight: float = 0.3,
        case_sensitive: bool = False,
        normalize_text: bool = True,
        remove_stopwords: bool = False,
        enable_caching: bool = True
    ):
        self.fuzzy_threshold = fuzzy_threshold
        self.soundex_length = soundex_length
        self.jaro_winkler_prefix_scale = jaro_winkler_prefix_scale
        self.cosine_epsilon = cosine_epsilon
        self.semantic_weight = semantic_weight
        self.text_weight = text_weight
        self.case_sensitive = case_sensitive
        self.normalize_text = normalize_text
        self.remove_stopwords = remove_stopwords
        self.enable_caching = enable_caching


# Global config instance
_similarity_config = SimilarityConfig()


def get_similarity_config() -> SimilarityConfig:
    """Get global similarity configuration"""
    return _similarity_config


def set_similarity_config(config: SimilarityConfig):
    """Set global similarity configuration"""
    global _similarity_config
    _similarity_config = config


def calculate_similarity(
    item1: Any,
    item2: Any,
    method: Union[str, SimilarityMethod] = SimilarityMethod.FUZZY,
    config: Optional[SimilarityConfig] = None,
    **kwargs
) -> float:
    """
    Calculate similarity between two items using specified method.
    
    Args:
        item1: First item to compare
        item2: Second item to compare  
        method: Similarity calculation method
        config: Optional custom configuration
        **kwargs: Additional method-specific parameters
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if config is None:
        config = get_similarity_config()
    
    method = SimilarityMethod(method) if isinstance(method, str) else method
    
    # Handle None values
    if item1 is None and item2 is None:
        return 1.0
    if item1 is None or item2 is None:
        return 0.0
    
    # Route to appropriate similarity function
    if method in [SimilarityMethod.EXACT, SimilarityMethod.FUZZY, SimilarityMethod.LEVENSHTEIN, 
                  SimilarityMethod.JARO_WINKLER, SimilarityMethod.SOUNDEX, SimilarityMethod.METAPHONE]:
        return _calculate_text_similarity(str(item1), str(item2), method, config, **kwargs)
    
    elif method in [SimilarityMethod.COSINE, SimilarityMethod.EUCLIDEAN, 
                    SimilarityMethod.MANHATTAN, SimilarityMethod.DOT_PRODUCT]:
        return _calculate_vector_similarity(item1, item2, method, config, **kwargs)
    
    elif method in [SimilarityMethod.JACCARD, SimilarityMethod.SORENSEN_DICE, SimilarityMethod.OVERLAP]:
        return _calculate_set_similarity(item1, item2, method, config, **kwargs)
    
    elif method == SimilarityMethod.SEMANTIC:
        return _calculate_semantic_similarity(item1, item2, config, **kwargs)
    
    elif method == SimilarityMethod.HYBRID:
        return _calculate_hybrid_similarity(item1, item2, config, **kwargs)
    
    else:
        raise ValueError(f"Unknown similarity method: {method}")


# =============================================
# TEXT SIMILARITY METHODS
# =============================================

def _calculate_text_similarity(
    text1: str, 
    text2: str, 
    method: SimilarityMethod, 
    config: SimilarityConfig,
    **kwargs
) -> float:
    """Calculate text similarity using specified method"""
    
    # Normalize text if enabled
    if config.normalize_text:
        text1 = _normalize_text(text1, config)
        text2 = _normalize_text(text2, config)
    
    # Use caching for expensive operations
    if config.enable_caching and method in [SimilarityMethod.SOUNDEX, SimilarityMethod.METAPHONE]:
        cache_key = _generate_cache_key(text1, text2, method)
        cached_result = _get_cached_similarity(cache_key)
        if cached_result is not None:
            return cached_result
    
    if method == SimilarityMethod.EXACT:
        result = _exact_match(text1, text2, config.case_sensitive)
    
    elif method == SimilarityMethod.FUZZY:
        result = _fuzzy_similarity(text1, text2)
    
    elif method == SimilarityMethod.LEVENSHTEIN:
        result = _levenshtein_similarity(text1, text2)
    
    elif method == SimilarityMethod.JARO_WINKLER:
        result = _jaro_winkler_similarity(text1, text2, config.jaro_winkler_prefix_scale)
    
    elif method == SimilarityMethod.SOUNDEX:
        result = _soundex_similarity(text1, text2, config.soundex_length)
    
    elif method == SimilarityMethod.METAPHONE:
        result = _metaphone_similarity(text1, text2)
    
    else:
        raise ValueError(f"Unknown text similarity method: {method}")
    
    # Cache result if enabled
    if config.enable_caching and method in [SimilarityMethod.SOUNDEX, SimilarityMethod.METAPHONE]:
        _cache_similarity(cache_key, result)
    
    return result


def _normalize_text(text: str, config: SimilarityConfig) -> str:
    """Normalize text for comparison"""
    
    # Convert to lowercase if not case sensitive
    if not config.case_sensitive:
        text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters (keep alphanumeric and spaces)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    
    # Remove stopwords if enabled
    if config.remove_stopwords:
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = text.split()
        text = ' '.join([word for word in words if word.lower() not in stopwords])
    
    return text


def _exact_match(text1: str, text2: str, case_sensitive: bool) -> float:
    """Exact string match"""
    if not case_sensitive:
        return 1.0 if text1.lower() == text2.lower() else 0.0
    return 1.0 if text1 == text2 else 0.0


def _fuzzy_similarity(text1: str, text2: str) -> float:
    """Fuzzy string similarity using difflib"""
    return SequenceMatcher(None, text1, text2).ratio()


def _levenshtein_similarity(text1: str, text2: str) -> float:
    """Levenshtein distance similarity"""
    max_len = max(len(text1), len(text2))
    if max_len == 0:
        return 1.0
    
    distance = Levenshtein.distance(text1, text2)
    return 1.0 - (distance / max_len)


def _jaro_winkler_similarity(text1: str, text2: str, prefix_scale: float) -> float:
    """Jaro-Winkler similarity"""
    return Levenshtein.jaro_winkler(text1, text2, prefix_scale)


@lru_cache(maxsize=1000)
def _soundex(text: str, length: int = 4) -> str:
    """Generate Soundex code for text"""
    if not text:
        return "0" * length
    
    text = re.sub(r'[^A-Za-z]', '', text.upper())
    if not text:
        return "0" * length
    
    # Soundex mapping
    mapping = {
        'BFPV': '1', 'CGJKQSXZ': '2', 'DT': '3',
        'L': '4', 'MN': '5', 'R': '6'
    }
    
    # Keep first letter
    soundex = text[0]
    
    # Convert remaining letters
    for char in text[1:]:
        for chars, digit in mapping.items():
            if char in chars:
                if soundex[-1] != digit:  # Avoid consecutive duplicates
                    soundex += digit
                break
    
    # Pad or truncate to specified length
    soundex = (soundex + "0" * length)[:length]
    return soundex


def _soundex_similarity(text1: str, text2: str, length: int) -> float:
    """Soundex-based similarity"""
    soundex1 = _soundex(text1, length)
    soundex2 = _soundex(text2, length)
    return 1.0 if soundex1 == soundex2 else 0.0


@lru_cache(maxsize=1000)
def _metaphone(text: str) -> str:
    """Simple Metaphone algorithm implementation"""
    if not text:
        return ""
    
    text = re.sub(r'[^A-Za-z]', '', text.upper())
    if not text:
        return ""
    
    # Simplified metaphone rules
    metaphone = ""
    i = 0
    
    while i < len(text):
        char = text[i]
        
        if char in 'AEIOU':
            if i == 0:
                metaphone += char
        elif char == 'B':
            metaphone += 'B'
        elif char == 'C':
            if i + 1 < len(text) and text[i + 1] in 'EIY':
                metaphone += 'S'
            else:
                metaphone += 'K'
        elif char == 'D':
            metaphone += 'T'
        elif char == 'F':
            metaphone += 'F'
        elif char == 'G':
            metaphone += 'K'
        elif char == 'H':
            if i == 0 or text[i-1] in 'AEIOU':
                metaphone += 'H'
        elif char == 'J':
            metaphone += 'J'
        elif char == 'K':
            metaphone += 'K'
        elif char == 'L':
            metaphone += 'L'
        elif char == 'M':
            metaphone += 'M'
        elif char == 'N':
            metaphone += 'N'
        elif char == 'P':
            if i + 1 < len(text) and text[i + 1] == 'H':
                metaphone += 'F'
                i += 1
            else:
                metaphone += 'P'
        elif char == 'Q':
            metaphone += 'K'
        elif char == 'R':
            metaphone += 'R'
        elif char == 'S':
            if i + 1 < len(text) and text[i + 1] == 'H':
                metaphone += 'X'
                i += 1
            else:
                metaphone += 'S'
        elif char == 'T':
            if i + 1 < len(text) and text[i + 1] == 'H':
                metaphone += '0'
                i += 1
            else:
                metaphone += 'T'
        elif char == 'V':
            metaphone += 'F'
        elif char == 'W':
            metaphone += 'W'
        elif char == 'X':
            metaphone += 'KS'
        elif char == 'Y':
            metaphone += 'Y'
        elif char == 'Z':
            metaphone += 'S'
        
        i += 1
    
    return metaphone


def _metaphone_similarity(text1: str, text2: str) -> float:
    """Metaphone-based similarity"""
    metaphone1 = _metaphone(text1)
    metaphone2 = _metaphone(text2)
    return 1.0 if metaphone1 == metaphone2 else 0.0


# =============================================
# VECTOR SIMILARITY METHODS
# =============================================

def _calculate_vector_similarity(
    vector1: Union[List[float], np.ndarray],
    vector2: Union[List[float], np.ndarray],
    method: SimilarityMethod,
    config: SimilarityConfig,
    **kwargs
) -> float:
    """Calculate vector similarity"""
    
    # Convert to numpy arrays
    if not isinstance(vector1, np.ndarray):
        vector1 = np.array(vector1, dtype=np.float32)
    if not isinstance(vector2, np.ndarray):
        vector2 = np.array(vector2, dtype=np.float32)
    
    # Ensure same dimensions
    if vector1.shape != vector2.shape:
        raise ValueError(f"Vector dimensions don't match: {vector1.shape} vs {vector2.shape}")
    
    if method == SimilarityMethod.COSINE:
        return _cosine_similarity(vector1, vector2, config.cosine_epsilon)
    
    elif method == SimilarityMethod.EUCLIDEAN:
        return _euclidean_similarity(vector1, vector2)
    
    elif method == SimilarityMethod.MANHATTAN:
        return _manhattan_similarity(vector1, vector2)
    
    elif method == SimilarityMethod.DOT_PRODUCT:
        return _dot_product_similarity(vector1, vector2)
    
    else:
        raise ValueError(f"Unknown vector similarity method: {method}")


def _cosine_similarity(vector1: np.ndarray, vector2: np.ndarray, epsilon: float) -> float:
    """Cosine similarity between two vectors"""
    
    # Calculate norms
    norm1 = np.linalg.norm(vector1)
    norm2 = np.linalg.norm(vector2)
    
    # Handle zero vectors
    if norm1 < epsilon or norm2 < epsilon:
        return 0.0
    
    # Calculate cosine similarity
    dot_product = np.dot(vector1, vector2)
    return dot_product / (norm1 * norm2)


def _euclidean_similarity(vector1: np.ndarray, vector2: np.ndarray) -> float:
    """Euclidean distance converted to similarity score"""
    
    distance = np.linalg.norm(vector1 - vector2)
    max_distance = np.linalg.norm(vector1) + np.linalg.norm(vector2)
    
    if max_distance == 0:
        return 1.0
    
    return 1.0 - (distance / max_distance)


def _manhattan_similarity(vector1: np.ndarray, vector2: np.ndarray) -> float:
    """Manhattan distance converted to similarity score"""
    
    distance = np.sum(np.abs(vector1 - vector2))
    max_distance = np.sum(np.abs(vector1)) + np.sum(np.abs(vector2))
    
    if max_distance == 0:
        return 1.0
    
    return 1.0 - (distance / max_distance)


def _dot_product_similarity(vector1: np.ndarray, vector2: np.ndarray) -> float:
    """Normalized dot product similarity"""
    
    dot_product = np.dot(vector1, vector2)
    
    # Normalize by vector magnitudes
    magnitude1 = np.sqrt(np.sum(vector1 ** 2))
    magnitude2 = np.sqrt(np.sum(vector2 ** 2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    # Return normalized dot product (same as cosine similarity)
    return dot_product / (magnitude1 * magnitude2)


# =============================================
# SET SIMILARITY METHODS
# =============================================

def _calculate_set_similarity(
    set1: Union[Set, List, str],
    set2: Union[Set, List, str],
    method: SimilarityMethod,
    config: SimilarityConfig,
    **kwargs
) -> float:
    """Calculate set similarity"""
    
    # Convert to sets
    if isinstance(set1, str):
        set1 = set(_tokenize_string(set1, config))
    elif isinstance(set1, list):
        set1 = set(set1)
    
    if isinstance(set2, str):
        set2 = set(_tokenize_string(set2, config))
    elif isinstance(set2, list):
        set2 = set(set2)
    
    if method == SimilarityMethod.JACCARD:
        return _jaccard_similarity(set1, set2)
    
    elif method == SimilarityMethod.SORENSEN_DICE:
        return _sorensen_dice_similarity(set1, set2)
    
    elif method == SimilarityMethod.OVERLAP:
        return _overlap_similarity(set1, set2)
    
    else:
        raise ValueError(f"Unknown set similarity method: {method}")


def _tokenize_string(text: str, config: SimilarityConfig) -> List[str]:
    """Tokenize string into words"""
    
    if config.normalize_text:
        text = _normalize_text(text, config)
    
    return text.split()


def _jaccard_similarity(set1: Set, set2: Set) -> float:
    """Jaccard similarity coefficient"""
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0


def _sorensen_dice_similarity(set1: Set, set2: Set) -> float:
    """Sørensen-Dice similarity coefficient"""
    
    intersection = len(set1.intersection(set2))
    total = len(set1) + len(set2)
    
    return (2 * intersection) / total if total > 0 else 0.0


def _overlap_similarity(set1: Set, set2: Set) -> float:
    """Overlap coefficient"""
    
    intersection = len(set1.intersection(set2))
    min_size = min(len(set1), len(set2))
    
    return intersection / min_size if min_size > 0 else 0.0


# =============================================
# SEMANTIC & HYBRID METHODS
# =============================================

def _calculate_semantic_similarity(
    item1: Any,
    item2: Any,
    config: SimilarityConfig,
    **kwargs
) -> float:
    """Calculate semantic similarity using embeddings"""
    
    # This would typically require loading a pre-trained model
    # For now, fall back to fuzzy matching
    # In production, you'd use sentence transformers or similar
    
    if hasattr(item1, '__iter__') and hasattr(item2, '__iter__'):
        # Assume these are embeddings
        return _cosine_similarity(np.array(item1), np.array(item2), config.cosine_epsilon)
    else:
        # Assume these are text strings
        # In production, you'd generate embeddings first
        return _fuzzy_similarity(str(item1), str(item2))


def _calculate_hybrid_similarity(
    item1: Any,
    item2: Any,
    config: SimilarityConfig,
    **kwargs
) -> float:
    """Calculate hybrid similarity combining multiple methods"""
    
    text1, text2 = str(item1), str(item2)
    
    # Calculate different similarity scores
    fuzzy_score = _fuzzy_similarity(text1, text2)
    jaro_score = _jaro_winkler_similarity(text1, text2, config.jaro_winkler_prefix_scale)
    jaccard_score = _jaccard_similarity(
        set(_tokenize_string(text1, config)),
        set(_tokenize_string(text2, config))
    )
    
    # Weighted combination
    return (0.4 * fuzzy_score + 0.3 * jaro_score + 0.3 * jaccard_score)


# =============================================
# CACHING UTILITIES
# =============================================

_similarity_cache = {}


def _generate_cache_key(item1: str, item2: str, method: SimilarityMethod) -> str:
    """Generate cache key for similarity calculation"""
    
    # Sort items to ensure consistent key regardless of order
    items = sorted([item1, item2])
    key_string = f"{items[0]}||{items[1]}||{method.value}"
    return hashlib.md5(key_string.encode()).hexdigest()


def _get_cached_similarity(cache_key: str) -> Optional[float]:
    """Get cached similarity result"""
    return _similarity_cache.get(cache_key)


def _cache_similarity(cache_key: str, result: float):
    """Cache similarity result"""
    
    # Limit cache size
    if len(_similarity_cache) >= 10000:
        # Remove oldest entries
        keys_to_remove = list(_similarity_cache.keys())[:5000]
        for key in keys_to_remove:
            del _similarity_cache[key]
    
    _similarity_cache[cache_key] = result


def clear_similarity_cache():
    """Clear the similarity cache"""
    global _similarity_cache
    _similarity_cache = {}


# =============================================
# UTILITY FUNCTIONS
# =============================================

def batch_similarity(
    items1: List[Any],
    items2: List[Any],
    method: Union[str, SimilarityMethod] = SimilarityMethod.FUZZY,
    config: Optional[SimilarityConfig] = None
) -> List[List[float]]:
    """Calculate similarity matrix for two lists of items"""
    
    if config is None:
        config = get_similarity_config()
    
    similarity_matrix = []
    
    for item1 in items1:
        row = []
        for item2 in items2:
            similarity = calculate_similarity(item1, item2, method, config)
            row.append(similarity)
        similarity_matrix.append(row)
    
    return similarity_matrix


def find_most_similar(
    target: Any,
    candidates: List[Any],
    method: Union[str, SimilarityMethod] = SimilarityMethod.FUZZY,
    threshold: float = 0.0,
    top_k: Optional[int] = None,
    config: Optional[SimilarityConfig] = None
) -> List[Tuple[Any, float]]:
    """Find most similar items from candidates"""
    
    if config is None:
        config = get_similarity_config()
    
    similarities = []
    
    for candidate in candidates:
        similarity = calculate_similarity(target, candidate, method, config)
        if similarity >= threshold:
            similarities.append((candidate, similarity))
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return top k results
    if top_k is not None:
        similarities = similarities[:top_k]
    
    return similarities


def similarity_clustering(
    items: List[Any],
    threshold: float = 0.8,
    method: Union[str, SimilarityMethod] = SimilarityMethod.FUZZY,
    config: Optional[SimilarityConfig] = None
) -> List[List[Any]]:
    """Cluster items based on similarity threshold"""
    
    if config is None:
        config = get_similarity_config()
    
    clusters = []
    processed = set()
    
    for i, item1 in enumerate(items):
        if i in processed:
            continue
        
        cluster = [item1]
        processed.add(i)
        
        for j, item2 in enumerate(items[i+1:], i+1):
            if j in processed:
                continue
            
            similarity = calculate_similarity(item1, item2, method, config)
            if similarity >= threshold:
                cluster.append(item2)
                processed.add(j)
        
        clusters.append(cluster)
    
    return clusters


# =============================================
# SPECIALIZED ENTITY SIMILARITY
# =============================================

def calculate_entity_similarity(
    entity1: Dict[str, Any],
    entity2: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
    config: Optional[SimilarityConfig] = None
) -> Dict[str, float]:
    """Calculate comprehensive similarity between two entities"""
    
    if config is None:
        config = get_similarity_config()
    
    if weights is None:
        weights = {
            "text": 0.4,
            "type": 0.2,
            "properties": 0.3,
            "semantic": 0.1
        }
    
    similarities = {}
    
    # Text similarity
    text1 = entity1.get("entity_text", "")
    text2 = entity2.get("entity_text", "")
    similarities["text"] = calculate_similarity(text1, text2, SimilarityMethod.HYBRID, config)
    
    # Type similarity
    type1 = entity1.get("entity_type", "")
    type2 = entity2.get("entity_type", "")
    similarities["type"] = 1.0 if type1 == type2 else 0.0
    
    # Property similarity
    props1 = entity1.get("properties", {})
    props2 = entity2.get("properties", {})
    similarities["properties"] = _calculate_property_similarity(props1, props2, config)
    
    # Semantic similarity (if embeddings available)
    if "embedding" in entity1 and "embedding" in entity2:
        similarities["semantic"] = calculate_similarity(
            entity1["embedding"], entity2["embedding"], SimilarityMethod.COSINE, config
        )
    else:
        similarities["semantic"] = similarities["text"]  # Fallback
    
    # Calculate weighted overall similarity
    overall_similarity = sum(
        similarities[key] * weights.get(key, 0.0)
        for key in similarities.keys()
    )
    
    similarities["overall"] = overall_similarity
    
    return similarities


def _calculate_property_similarity(
    props1: Dict[str, Any],
    props2: Dict[str, Any],
    config: SimilarityConfig
) -> float:
    """Calculate similarity between entity properties"""
    
    if not props1 and not props2:
        return 1.0
    
    if not props1 or not props2:
        return 0.0
    
    # Get common keys
    keys1 = set(props1.keys())
    keys2 = set(props2.keys())
    common_keys = keys1.intersection(keys2)
    all_keys = keys1.union(keys2)
    
    if not all_keys:
        return 1.0
    
    # Calculate similarity for each property
    similarities = []
    
    for key in common_keys:
        val1, val2 = props1[key], props2[key]
        
        if isinstance(val1, str) and isinstance(val2, str):
            sim = calculate_similarity(val1, val2, SimilarityMethod.FUZZY, config)
        elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            # Numeric similarity
            max_val = max(abs(val1), abs(val2), 1)  # Avoid division by zero
            sim = 1.0 - abs(val1 - val2) / max_val
        elif val1 == val2:
            sim = 1.0
        else:
            sim = 0.0
        
        similarities.append(sim)
    
    # Penalize for missing keys
    key_overlap = len(common_keys) / len(all_keys)
    
    if similarities:
        avg_similarity = sum(similarities) / len(similarities)
        return avg_similarity * key_overlap
    else:
        return key_overlap
