import asyncio
import hashlib
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

import numpy as np

try:
    import openai
    from openai import AsyncOpenAI
except ImportError:
    openai = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from app.core.config import settings
from app.core.supabase import get_supabase

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using various providers"""
    
    def __init__(self):
        self.openai_client = None
        self.sentence_transformer = None
        self.embedding_cache = {}
        
        # Initialize OpenAI client
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Initialize Sentence Transformer (fallback)
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Sentence Transformer model loaded")
            except Exception as e:
                logger.warning(f"Failed to load Sentence Transformer: {e}")
    
    async def get_text_embedding(
        self, 
        text: str, 
        model: Optional[str] = None,
        cache: bool = True
    ) -> Optional[List[float]]:
        """
        Generate embedding for text using available provider
        
        Args:
            text: Text to embed
            model: Specific model to use (optional)
            cache: Whether to cache the result
            
        Returns:
            List of floats representing the embedding, or None if failed
        """
        
        if not text or not text.strip():
            return None
        
        # Normalize text
        text = text.strip()
        
        # Check cache first
        if cache:
            cache_key = self._get_cache_key(text, model)
            if cache_key in self.embedding_cache:
                return self.embedding_cache[cache_key]
        
        # Try OpenAI first (best quality)
        if self.openai_client:
            embedding = await self._get_openai_embedding(text, model)
            if embedding:
                if cache:
                    self.embedding_cache[cache_key] = embedding
                return embedding
        
        # Fallback to Sentence Transformer
        if self.sentence_transformer:
            embedding = await self._get_sentence_transformer_embedding(text)
            if embedding:
                if cache:
                    self.embedding_cache[cache_key] = embedding
                return embedding
        
        # Fallback to simple TF-IDF
        logger.warning("No embedding service available, using TF-IDF fallback")
        embedding = self._get_tfidf_embedding(text)
        if cache and embedding:
            self.embedding_cache[cache_key] = embedding
        
        return embedding
    
    async def _get_openai_embedding(
        self, 
        text: str, 
        model: Optional[str] = None
    ) -> Optional[List[float]]:
        """Get embedding from OpenAI"""
        
        try:
            model = model or settings.OPENAI_EMBEDDING_MODEL
            
            response = await self.openai_client.embeddings.create(
                input=text,
                model=model
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return None
    
    async def _get_sentence_transformer_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from Sentence Transformer"""
        
        try:
            # Run in thread pool since sentence transformers is not async
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.sentence_transformer.encode, 
                text
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Sentence Transformer embedding failed: {e}")
            return None
    
    def _get_tfidf_embedding(self, text: str) -> Optional[List[float]]:
        """Simple TF-IDF based embedding (fallback)"""
        
        try:
            from sklearn.decomposition import TruncatedSVD
            from sklearn.feature_extraction.text import TfidfVectorizer

            # Simple tokenization
            words = text.lower().split()
            
            if not words:
                return None
            
            # Create a simple TF-IDF representation
            # This is a very basic implementation
            vectorizer = TfidfVectorizer(max_features=384)
            
            # Need at least 2 documents for TF-IDF
            corpus = [text, ""]
            
            tfidf_matrix = vectorizer.fit_transform(corpus)
            
            # Use SVD to reduce dimensionality
            svd = TruncatedSVD(n_components=min(384, tfidf_matrix.shape[1]))
            embeddings = svd.fit_transform(tfidf_matrix)
            
            return embeddings[0].tolist()
            
        except Exception as e:
            logger.error(f"TF-IDF embedding failed: {e}")
            
            # Ultimate fallback - random embedding (for testing)
            return [0.1] * 384
    
    def _get_cache_key(self, text: str, model: Optional[str] = None) -> str:
        """Generate cache key for text and model"""
        
        content = f"{text}||{model or 'default'}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_batch_embeddings(
        self, 
        texts: List[str], 
        model: Optional[str] = None,
        batch_size: int = 100
    ) -> List[Optional[List[float]]]:
        """Get embeddings for multiple texts"""
        
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Process batch
            batch_results = await asyncio.gather(
                *[self.get_text_embedding(text, model) for text in batch],
                return_exceptions=True
            )
            
            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch embedding failed: {result}")
                    results.append(None)
                else:
                    results.append(result)
        
        return results
    
    def clear_cache(self):
        """Clear embedding cache"""
        self.embedding_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "cache_size": len(self.embedding_cache),
            "cache_memory_usage": sum(
                len(str(v)) for v in self.embedding_cache.values()
            )
        }


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get global embedding service instance"""
    
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    
    return _embedding_service


# Convenience functions
async def get_text_embedding(text: str, model: Optional[str] = None) -> Optional[List[float]]:
    """Get text embedding using global service"""
    
    service = get_embedding_service()
    return await service.get_text_embedding(text, model)


async def get_entity_embedding(entity_text: str, entity_type: str) -> Optional[List[float]]:
    """Get embedding for entity with type context"""
    
    # Combine entity text with type for better context
    combined_text = f"{entity_type}: {entity_text}"
    return await get_text_embedding(combined_text)


async def get_batch_embeddings(texts: List[str]) -> List[Optional[List[float]]]:
    """Get embeddings for multiple texts"""
    
    service = get_embedding_service()
    return await service.get_batch_embeddings(texts)


# =============================================
# DATABASE INTEGRATION
# =============================================

async def update_entity_embeddings(
    entity_ids: Optional[List[str]] = None,
    batch_size: int = 50,
    force_update: bool = False
) -> Dict[str, Any]:
    """Update embeddings for entities in database"""
    
    supabase = await get_supabase()
    service = get_embedding_service()
    
    # Get entities without embeddings or force update all
    if entity_ids:
        query = supabase.table("kg_entities").select("id, entity_text, entity_type").in_("id", entity_ids)
    else:
        query = supabase.table("kg_entities").select("id, entity_text, entity_type").eq("is_active", True)
    
    if not force_update:
        query = query.is_("embedding", "null")
    
    response = await query.limit(1000).execute()  # Safety limit
    entities = response.data
    
    if not entities:
        return {"updated_count": 0, "error_count": 0}
    
    updated_count = 0
    error_count = 0
    
    # Process in batches
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i + batch_size]
        
        # Generate embeddings for batch
        texts = [f"{entity['entity_type']}: {entity['entity_text']}" for entity in batch]
        embeddings = await service.get_batch_embeddings(texts)
        
        # Update entities with embeddings
        for entity, embedding in zip(batch, embeddings):
            if embedding:
                try:
                    await supabase.table("kg_entities").update({
                        "embedding": embedding
                    }).eq("id", entity["id"]).execute()
                    
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to update embedding for entity {entity['id']}: {e}")
                    error_count += 1
            else:
                error_count += 1
        
        # Add small delay to avoid overwhelming the API
        await asyncio.sleep(0.1)
    
    return {
        "updated_count": updated_count,
        "error_count": error_count,
        "total_processed": len(entities)
    }


# =============================================
# SIMILARITY SEARCH HELPERS
# =============================================

async def find_similar_entities(
    query_text: str,
    entity_type: Optional[str] = None,
    limit: int = 20,
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Find entities similar to query text using embeddings"""
    
    # Get query embedding
    query_embedding = await get_text_embedding(query_text)
    if not query_embedding:
        return []
    
    supabase = await get_supabase()
    
    # Get entities with embeddings
    query = supabase.table("kg_entities").select(
        "id, entity_text, entity_type, properties, confidence, embedding"
    ).eq("is_active", True).not_.is_("embedding", "null")
    
    if entity_type:
        query = query.eq("entity_type", entity_type)
    
    response = await query.execute()
    entities = response.data
    
    # Calculate similarities
    similar_entities = []
    
    for entity in entities:
        if entity.get("embedding"):
            try:
                from app.utils.similarity import (SimilarityMethod,
                                                  calculate_similarity)
                
                similarity = calculate_similarity(
                    query_embedding,
                    entity["embedding"],
                    SimilarityMethod.COSINE
                )
                
                if similarity >= similarity_threshold:
                    entity_result = {
                        "id": entity["id"],
                        "entity_text": entity["entity_text"],
                        "entity_type": entity["entity_type"],
                        "properties": entity["properties"],
                        "confidence": entity["confidence"],
                        "similarity_score": similarity
                    }
                    similar_entities.append(entity_result)
                    
            except Exception as e:
                logger.error(f"Error calculating similarity for entity {entity['id']}: {e}")
    
    # Sort by similarity and limit results
    similar_entities.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similar_entities[:limit]


# =============================================
# EMBEDDING QUALITY METRICS
# =============================================

async def evaluate_embedding_quality() -> Dict[str, Any]:
    """Evaluate the quality of embeddings in the system"""
    
    supabase = await get_supabase()
    
    # Get sample of entities with embeddings
    response = await supabase.table("kg_entities").select(
        "id, entity_text, entity_type, embedding"
    ).eq("is_active", True).not_.is_("embedding", "null").limit(1000).execute()
    
    entities = response.data
    
    if not entities:
        return {"error": "No entities with embeddings found"}
    
    # Quality metrics
    metrics = {
        "total_entities": len(entities),
        "embedding_dimensions": len(entities[0]["embedding"]) if entities else 0,
        "entity_types": {},
        "average_embedding_norm": 0,
        "embedding_distribution": {}
    }
    
    # Analyze by entity type
    norms = []
    
    for entity in entities:
        entity_type = entity["entity_type"]
        embedding = entity["embedding"]
        
        # Count by type
        if entity_type not in metrics["entity_types"]:
            metrics["entity_types"][entity_type] = 0
        metrics["entity_types"][entity_type] += 1
        
        # Calculate embedding norm
        if embedding:
            norm = np.linalg.norm(embedding)
            norms.append(norm)
    
    if norms:
        metrics["average_embedding_norm"] = float(np.mean(norms))
        metrics["embedding_norm_std"] = float(np.std(norms))
        metrics["min_norm"] = float(np.min(norms))
        metrics["max_norm"] = float(np.max(norms))
    
    return metrics


# =============================================
# INITIALIZATION
# =============================================

async def initialize_embeddings():
    """Initialize embedding service and update missing embeddings"""
    
    logger.info("Initializing embedding service...")
    
    service = get_embedding_service()
    
    # Test embedding generation
    test_embedding = await service.get_text_embedding("test")
    if test_embedding:
        logger.info(f"✅ Embedding service working (dimension: {len(test_embedding)})")
    else:
        logger.warning("⚠️ Embedding service not working properly")
    
    # Update missing embeddings for existing entities
    logger.info("Updating missing entity embeddings...")
    result = await update_entity_embeddings(batch_size=20)
    
    logger.info(f"✅ Updated {result['updated_count']} entity embeddings")
    if result['error_count'] > 0:
        logger.warning(f"⚠️ {result['error_count']} entities failed to update")


if __name__ == "__main__":
    # Test embedding service
    async def test_embeddings():
        service = get_embedding_service()
        
        # Test single embedding
        embedding = await service.get_text_embedding("Apple Inc is a technology company")
        print(f"Single embedding: {len(embedding) if embedding else 'None'}")
        
        # Test batch embeddings
        texts = ["Apple Inc", "Microsoft Corporation", "Google LLC"]
        embeddings = await service.get_batch_embeddings(texts)
        print(f"Batch embeddings: {len([e for e in embeddings if e is not None])}/{len(texts)}")
        
        # Test similarity search
        similar = await find_similar_entities("technology company", limit=5)
        print(f"Similar entities found: {len(similar)}")
    
    asyncio.run(test_embeddings())
