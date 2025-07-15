import json
import logging
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import HTTPException, status

from app.schemas.search import EmbeddingRequest

from .base import BaseSearchService

logger = logging.getLogger(__name__)


class EmbeddingService(BaseSearchService):
    """Service for embedding generation and management"""

    async def generate_embedding(self, request: EmbeddingRequest) -> Dict[str, Any]:
        """Generate embedding for a text"""
        if not self.openai_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API is not configured",
            )

        try:
            embedding = await self._generate_embedding(
                text=request.text, model=request.model
            )

            return {
                "embedding": embedding,
                "model": request.model or "text-embedding-ada-002",
                "text": request.text,
                "vector_size": len(embedding),
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating embedding: {str(e)}",
            )

    async def create_entity_embedding(
        self, entity_id: str, model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create embedding for a new entity"""
        if not self.openai_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API is not configured",
            )

        try:
            # Get entity from PostgreSQL
            supabase = await self.get_supabase_client()

            entity_response = await (
                supabase.table("kg_entities")
                .select("id, entity_text, entity_type")
                .eq("id", entity_id)
                .eq("is_active", True)
                .single()
                .execute()
            )

            if not entity_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found"
                )

            entity = entity_response.data
            entity_text = entity.get("entity_text", "")

            if not entity_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Entity has no text to embed",
                )

            # Generate embedding
            embedding = await self._generate_embedding(entity_text, model)

            # Update entity with embedding
            await (
                supabase.table("kg_entities")
                .update({"embedding": json.dumps(embedding)})
                .eq("id", entity_id)
                .execute()
            )

            return {
                "id": entity["id"],
                "text": entity["entity_text"],
                "type": entity["entity_type"],
                "embedding_created": True,
                "vector_size": len(embedding),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating entity embedding: {str(e)}",
            )

    async def update_entity_embedding(self, entity_id: str) -> Dict[str, Any]:
        """Update embedding for an entity"""
        return await self.create_entity_embedding(entity_id)

    async def update_entity_embeddings_batch(
        self,
        entity_type: Optional[str] = None,
        limit: int = 100,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update embeddings for a batch of entities"""
        if not self.openai_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API is not configured",
            )

        try:
            supabase = await self.get_supabase_client()

            # Build query for entities without embeddings
            db_query = (
                supabase.table("kg_entities")
                .select("id, entity_text, entity_type")
                .eq("is_active", True)
                .is_("embedding", "null")
                .limit(limit)
            )

            if entity_type:
                db_query = db_query.eq("entity_type", entity_type)

            response = await db_query.execute()
            entities = response.data

            if not entities:
                return {
                    "updated_entities": [],
                    "total_updated": 0,
                    "message": "No entities found without embeddings",
                }

            updated_entities = []

            for entity in entities:
                entity_id = entity["id"]
                entity_text = entity.get("entity_text", "")

                if not entity_text:
                    continue

                try:
                    # Generate embedding
                    embedding = await self._generate_embedding(entity_text, model)

                    # Update entity with embedding
                    await (
                        supabase.table("kg_entities")
                        .update({"embedding": json.dumps(embedding)})
                        .eq("id", entity_id)
                        .execute()
                    )

                    updated_entities.append(
                        {
                            "id": entity_id,
                            "text": entity_text,
                            "type": entity["entity_type"],
                            "embedding_updated": True,
                            "vector_size": len(embedding),
                        }
                    )

                except Exception as e:
                    logger.error(
                        f"Error updating embedding for entity {entity_id}: {e}"
                    )
                    continue

            return {
                "updated_entities": updated_entities,
                "total_updated": len(updated_entities),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating entity embeddings: {str(e)}",
            )

    async def _generate_embedding(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding for a text using OpenAI API"""
        if not self.openai_available:
            raise ValueError("OpenAI API is not available")

        try:
            # Use specified model or default
            embedding_model = model or "text-embedding-ada-002"

            # Call OpenAI API
            response = await self.aclient.embeddings.create(
                model=embedding_model, input=text, encoding_format="float"
            )

            # Extract embedding
            embedding = response.data[0].embedding

            return embedding
        except Exception as e:
            raise ValueError(f"Error generating embedding: {e}")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same dimension")

        # Convert to numpy arrays for efficient computation
        a = np.array(vec1)
        b = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)
