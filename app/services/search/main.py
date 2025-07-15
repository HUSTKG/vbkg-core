# app/services/search/main.py

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.schemas.search import (AISearchRequest, AISearchResponse,
                                EmbeddingRequest, EntitySearchResult,
                                GraphSearchQuery, SearchRequest,
                                SearchResponse, SearchType,
                                SimilarEntityRequest)

from .ai_search import AISearchService
from .embedding import EmbeddingService
from .graph import GraphService
from .traditional_search import TraditionalSearchService

logger = logging.getLogger(__name__)


class SearchService:
    """
    Main search service facade that combines all search functionality.
    Maintains backward compatibility with the original SearchService interface.
    """

    def __init__(self):
        # Initialize all sub-services
        self.ai_search_service = AISearchService()
        self.traditional_search_service = TraditionalSearchService()
        self.embedding_service = EmbeddingService()
        self.graph_service = GraphService()

    # ===== MAIN SEARCH METHODS =====

    async def search_entities(self, search_request: SearchRequest) -> SearchResponse:
        """Search for entities based on the search request"""
        if search_request.search_type == SearchType.AI_POWERED:
            return await self._ai_powered_search(search_request)
        else:
            return await self.traditional_search_service.search_entities(search_request)

    async def ai_search(self, request: AISearchRequest) -> AISearchResponse:
        """
        AI-powered search pipeline for banking knowledge graph
        """
        return await self.ai_search_service.ai_search(request)

    # ===== AI-POWERED SEARCH COMPATIBILITY =====

    async def _ai_powered_search(self, search_request: SearchRequest) -> SearchResponse:
        """Convert regular search request to AI search for backward compatibility"""

        # Convert SearchRequest to AISearchRequest
        ai_request = AISearchRequest(
            query=search_request.query,
            entity_types=search_request.entity_types,
            max_candidates=min(search_request.limit * 3, 100),
            top_k_entities=search_request.limit,
            generate_answer=False,  # Don't generate answer for regular search
        )

        # Perform AI search
        ai_response = await self.ai_search_service.ai_search(ai_request)

        # Convert back to SearchResponse format
        results = []
        for entity in ai_response.entities:
            result = EntitySearchResult(
                id=entity.entity_id,
                text=entity.entity_text,
                type=entity.entity_type,
                properties=entity.properties,
                ontology_class=None,
                score=entity.final_score,
                relationships=None,
                similar_entities=None,
            )
            results.append(result)

        return SearchResponse(
            results=results,
            total=ai_response.total_candidates,
            query=search_request.query,
            search_type=SearchType.AI_POWERED,
            execution_time_ms=ai_response.execution_time_ms,
        )

    # ===== RELATIONSHIP AND ENTITY METHODS =====

    async def get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get relationships for an entity"""
        return await self.graph_service.get_entity_relationships(entity_id)

    async def get_similar_entities(
        self,
        entity_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        entity_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get similar entities based on embedding similarity"""
        return await self.graph_service.get_similar_entities(
            entity_id=entity_id,
            limit=limit,
            similarity_threshold=similarity_threshold,
            entity_types=entity_types,
        )

    async def find_similar_entities(
        self, request: SimilarEntityRequest
    ) -> List[Dict[str, Any]]:
        """Find entities similar to a given entity"""
        return await self.graph_service.find_similar_entities(request)

    async def get_search_suggestions(
        self, partial_query: str, limit: int = 5
    ) -> List[str]:
        """Get search suggestions based on partial query"""
        return await self.graph_service.get_search_suggestions(
            partial_query=partial_query, limit=limit
        )

    # ===== GRAPH SEARCH METHODS =====

    async def graph_search(self, query: GraphSearchQuery) -> Dict[str, Any]:
        """Perform graph traversal search"""
        return await self.graph_service.graph_search(query)

    # ===== EMBEDDING METHODS =====

    async def generate_embedding(self, request: EmbeddingRequest) -> Dict[str, Any]:
        """Generate embedding for a text"""
        return await self.embedding_service.generate_embedding(request)

    async def create_entity_embedding(
        self, entity_id: str, model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create embedding for a new entity"""
        return await self.embedding_service.create_entity_embedding(
            entity_id=entity_id, model=model
        )

    async def update_entity_embedding(self, entity_id: str) -> Dict[str, Any]:
        """Update embedding for an entity"""
        return await self.embedding_service.update_entity_embedding(entity_id)

    async def update_entity_embeddings_batch(
        self,
        entity_type: Optional[str] = None,
        limit: int = 100,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update embeddings for a batch of entities"""
        return await self.embedding_service.update_entity_embeddings_batch(
            entity_type=entity_type, limit=limit, model=model
        )

    # ===== ENHANCED SEARCH WITH RELATIONSHIPS AND SIMILAR ENTITIES =====

    async def search_entities_with_enhancements(
        self, search_request: SearchRequest
    ) -> SearchResponse:
        """
        Enhanced search that includes relationships and similar entities if requested
        """
        # Perform base search
        response = await self.search_entities(search_request)

        # Include relationships if requested
        if search_request.include_relationships:
            for entity in response.results:
                entity.relationships = await self.get_entity_relationships(entity.id)

        # Include similar entities if requested
        if search_request.include_similar_entities:
            for entity in response.results:
                entity.similar_entities = await self.get_similar_entities(
                    entity_id=entity.id,
                    limit=5,
                    similarity_threshold=search_request.similarity_threshold or 0.7,
                    entity_types=search_request.entity_types,
                )

        return response

    # ===== PROPERTIES ACCESS FOR BACKWARD COMPATIBILITY =====

    @property
    def graph(self):
        """Access to Neo4j graph for backward compatibility"""
        return self.traditional_search_service.graph

    @property
    def node_matcher(self):
        """Access to node matcher for backward compatibility"""
        return self.traditional_search_service.node_matcher

    @property
    def rel_matcher(self):
        """Access to relationship matcher for backward compatibility"""
        return self.traditional_search_service.rel_matcher

    @property
    def openai_available(self):
        """Check if OpenAI is available"""
        return self.embedding_service.openai_available

    @property
    def aclient(self):
        """Access to OpenAI async client for backward compatibility"""
        return self.embedding_service.aclient if self.openai_available else None

    @property
    def personrank_calculator(self):
        """Access to PersonRank calculator for backward compatibility"""
        return self.ai_search_service.personrank_calculator

    # ===== UTILITY METHODS FOR BACKWARD COMPATIBILITY =====

    def _validate_entity_types(self, entity_types: Optional[List[str]]) -> List[str]:
        """Validate and clean entity types list"""
        return self.traditional_search_service._validate_entity_types(entity_types)

    def _convert_neo4j_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Neo4j properties, handling DateTime objects"""
        return self.traditional_search_service._convert_neo4j_properties(properties)

    async def get_supabase_client(self):
        """Get Supabase client instance"""
        return await self.traditional_search_service.get_supabase_client()
