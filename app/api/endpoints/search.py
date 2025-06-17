from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import PermissionChecker
from app.schemas.api import ApiResponse
from app.schemas.search import (  # Existing schemas; New AI search schemas
    AISearchRequest, AISearchResponse, EmbeddingRequest, EmbeddingResponse,
    GraphSearchQuery, GraphSearchResult, SearchRequest, SearchResponse,
    SearchSuggestionResponse, SimilarEntityRequest)
from app.services.search import SearchService

router = APIRouter()

check_read_permission = PermissionChecker("kg:read")
check_write_permission = PermissionChecker("kg:edit")


@router.post("/entities", response_model=ApiResponse[SearchResponse])
async def search_entities(
    search_request: SearchRequest,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)],
) -> Any:
    """
    Search for entities using various search strategies.

    Supports:
    - EXACT: Exact text matching
    - FUZZY: Fuzzy text matching
    - SEMANTIC: Semantic similarity using embeddings
    - HYBRID: Combination of exact and semantic
    - AI_POWERED: AI-powered search with PersonRank
    """
    search_service = SearchService()
    response = await search_service.search_entities(search_request)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entities retrieved successfully",
    )


@router.post("/similar", response_model=ApiResponse[List[Dict[str, Any]]])
async def find_similar_entities(
    request: SimilarEntityRequest,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)],
) -> ApiResponse[List[Dict[str, Any]]]:
    """Find entities similar to the specified entity."""
    search_service = SearchService()
    response = await search_service.find_similar_entities(request=request)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Similar entities retrieved successfully",
    )


@router.post("/graph", response_model=ApiResponse[GraphSearchResult])
async def graph_search(
    query: GraphSearchQuery,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)],
) -> ApiResponse[GraphSearchResult]:
    """Perform a graph search following a relationship path."""
    search_service = SearchService()
    response = await search_service.graph_search(query=query)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Graph search completed successfully",
    )


@router.post("/embedding", response_model=ApiResponse[EmbeddingResponse])
async def generate_embedding(
    request: EmbeddingRequest,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)],
) -> ApiResponse[EmbeddingResponse]:
    """Generate embedding for arbitrary text."""
    search_service = SearchService()
    response = await search_service.generate_embedding(request=request)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Embedding generated successfully",
    )


@router.post(
    "/entities/{entity_id}/embedding", response_model=ApiResponse[Dict[str, Any]]
)
async def create_entity_embedding(
    entity_id: str = Path(...),
    model: Optional[str] = None,
    current_user: Annotated[Dict[str, Any], Depends(check_write_permission)] = None,
) -> ApiResponse[Dict[str, Any]]:
    """Create or update embedding for an entity."""
    search_service = SearchService()
    response = await search_service.create_entity_embedding(
        entity_id=entity_id, model=model
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entity embedding created successfully",
    )


@router.post("/entities/embeddings/batch", response_model=ApiResponse[Dict[str, Any]])
async def update_entity_embeddings_batch(
    entity_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    model: Optional[str] = None,
    current_user: Annotated[Dict[str, Any], Depends(check_write_permission)] = None,
) -> ApiResponse[Dict[str, Any]]:
    """Update embeddings for a batch of entities without embeddings."""
    search_service = SearchService()
    response = await search_service.update_entity_embeddings_batch(
        entity_type=entity_type, limit=limit, model=model
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Batch entity embeddings updated successfully",
    )


# ===== NEW AI SEARCH ENDPOINTS =====


@router.post("/ai", response_model=ApiResponse[AISearchResponse])
async def ai_search(
    request: AISearchRequest,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)],
) -> ApiResponse[AISearchResponse]:
    """
    AI-powered search using semantic similarity + PersonRank + LLM generation.

    This endpoint:
    1. Performs semantic search to find relevant entities
    2. Ranks entities using PersonRank algorithm based on graph structure
    3. Extracts subgraph context around top entities
    4. Generates natural language answer using LLM
    """
    search_service = SearchService()
    response = await search_service.ai_search(request)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="AI search completed successfully",
    )


@router.get("/ai/quick", response_model=ApiResponse[AISearchResponse])
async def quick_ai_search(
    q: str = Query(..., description="Search query"),
    entity_types: Optional[List[str]] = Query(
        None, description="Filter by entity types"
    ),
    max_results: int = Query(10, ge=1, le=50, description="Maximum results"),
    generate_answer: bool = Query(True, description="Generate LLM answer"),
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)] = None,
) -> ApiResponse[AISearchResponse]:
    """
    Quick AI search with simplified parameters.
    Convenient endpoint for simple AI searches.
    """
    search_service = SearchService()
    request = AISearchRequest(
        query=q,
        entity_types=entity_types,
        top_k_entities=max_results,
        generate_answer=generate_answer,
    )
    response = await search_service.ai_search(request)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Quick AI search completed successfully",
    )


@router.get("/suggestions", response_model=ApiResponse[SearchSuggestionResponse])
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial query"),
    limit: int = Query(5, ge=1, le=20, description="Maximum suggestions"),
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)] = None,
) -> ApiResponse[SearchSuggestionResponse]:
    """Get search suggestions based on partial query"""
    search_service = SearchService()
    suggestions = await search_service.get_search_suggestions(q, limit)
    response = SearchSuggestionResponse(suggestions=suggestions, query=q)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Search suggestions retrieved successfully",
    )


# ===== ADVANCED AI SEARCH ENDPOINTS =====


@router.post("/ai/personrank", response_model=ApiResponse[Dict[str, Any]])
async def calculate_personrank_scores(
    request: AISearchRequest,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)],
) -> ApiResponse[Dict[str, Any]]:
    """
    Calculate PersonRank scores for entities without LLM generation.
    Useful for understanding entity importance in graph context.
    """
    search_service = SearchService()
    # Disable LLM generation for this endpoint
    request.generate_answer = False

    result = await search_service.ai_search(request)

    # Return only the ranking information
    response_data = {
        "query": result.query,
        "entities": result.entities,
        "total_candidates": result.total_candidates,
        "execution_time_ms": result.execution_time_ms,
    }
    return ApiResponse(
        data=response_data,
        status=status.HTTP_200_OK,
        message="PersonRank scores calculated successfully",
    )


@router.post("/ai/subgraph", response_model=ApiResponse[Dict[str, Any]])
async def get_ai_subgraph(
    request: AISearchRequest,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)],
) -> ApiResponse[Dict[str, Any]]:
    """
    Get subgraph context around entities relevant to query.
    Returns graph structure without LLM generation.
    """
    search_service = SearchService()
    # Disable LLM generation for this endpoint
    request.generate_answer = False

    result = await search_service.ai_search(request)

    # Return subgraph and entities
    response_data = {
        "query": result.query,
        "entities": result.entities,
        "subgraph_context": result.subgraph_context,
        "execution_time_ms": result.execution_time_ms,
    }
    return ApiResponse(
        data=response_data,
        status=status.HTTP_200_OK,
        message="AI subgraph extracted successfully",
    )


@router.post("/ai/explain", response_model=ApiResponse[Dict[str, Any]])
async def explain_ai_search(
    request: AISearchRequest,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)],
) -> ApiResponse[Dict[str, Any]]:
    """
    Explain AI search results with detailed scoring breakdown.
    Useful for understanding how the AI search algorithm works.
    """
    search_service = SearchService()
    result = await search_service.ai_search(request)

    # Add explanation of scores
    explanation = {
        "query": result.query,
        "algorithm_steps": [
            "1. Semantic Search: Found relevant entities using text embeddings",
            "2. PersonRank: Ranked entities based on graph structure and query relevance",
            "3. Subgraph Extraction: Retrieved connected entities and relationships",
            "4. LLM Generation: Created natural language answer from context",
        ],
        "scoring_explanation": {
            "similarity_score": "Cosine similarity between query and entity embeddings (0-1)",
            "personrank_score": "Graph-based importance score considering query relevance (0-1)",
            "final_score": "Weighted combination: 0.4 * similarity + 0.6 * personrank",
        },
        "entities_with_scores": [
            {
                "entity": entity.entity_text,
                "type": entity.entity_type,
                "similarity_score": round(entity.similarity_score, 4),
                "personrank_score": round(entity.personrank_score, 4),
                "final_score": round(entity.final_score, 4),
                "explanation": f"High {'similarity' if entity.similarity_score > entity.personrank_score else 'graph importance'} score",
            }
            for entity in result.entities
        ],
        "subgraph_stats": {
            "nodes": (
                result.subgraph_context.node_count if result.subgraph_context else 0
            ),
            "edges": (
                result.subgraph_context.edge_count if result.subgraph_context else 0
            ),
            "context_richness": (
                "Rich"
                if (result.subgraph_context and result.subgraph_context.node_count > 20)
                else "Moderate"
            ),
        },
        "answer": result.answer,
        "confidence_explanation": f"Confidence {result.confidence_score:.2f} based on entity relevance and context richness",
    }

    return ApiResponse(
        data=explanation,
        status=status.HTTP_200_OK,
        message="AI search explanation generated successfully",
    )


# ===== SEARCH ANALYTICS ENDPOINTS =====


@router.get("/analytics/search-types", response_model=ApiResponse[Dict[str, Any]])
async def get_search_type_info(
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)] = None,
) -> ApiResponse[Dict[str, Any]]:
    """Get information about available search types"""
    response_data = {
        "search_types": [
            {
                "type": "exact",
                "name": "Exact Search",
                "description": "Direct text matching for precise results",
                "best_for": "Finding specific entities by name",
            },
            {
                "type": "fuzzy",
                "name": "Fuzzy Search",
                "description": "Approximate text matching with typo tolerance",
                "best_for": "Finding entities with similar spelling",
            },
            {
                "type": "semantic",
                "name": "Semantic Search",
                "description": "Meaning-based search using embeddings",
                "best_for": "Finding conceptually related entities",
            },
            {
                "type": "hybrid",
                "name": "Hybrid Search",
                "description": "Combines exact and semantic search",
                "best_for": "Balanced relevance and precision",
            },
            {
                "type": "ai_powered",
                "name": "AI-Powered Search",
                "description": "Advanced search with PersonRank and LLM answers",
                "best_for": "Complex questions requiring graph reasoning",
            },
        ],
        "recommendations": {
            "simple_lookup": "exact",
            "typo_tolerance": "fuzzy",
            "concept_search": "semantic",
            "general_search": "hybrid",
            "complex_questions": "ai_powered",
        },
    }
    return ApiResponse(
        data=response_data,
        status=status.HTTP_200_OK,
        message="Search type information retrieved successfully",
    )


@router.get("/analytics/ai-search-stats", response_model=ApiResponse[Dict[str, Any]])
async def get_ai_search_stats(
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)] = None,
) -> ApiResponse[Dict[str, Any]]:
    """Get statistics about AI search capability"""
    try:
        search_service = SearchService()
        # Check if AI search is properly configured
        ai_available = search_service.openai_available

        response_data = {
            "ai_search_available": ai_available,
            "features": {
                "semantic_search": True,
                "personrank": True,
                "subgraph_extraction": True,
                "llm_generation": ai_available,
                "search_suggestions": True,
            },
            "models": {
                "embedding_model": "text-embedding-ada-002",
                "llm_models": (
                    ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"] if ai_available else []
                ),
            },
            "limits": {
                "max_candidates": 200,
                "max_subgraph_nodes": 500,
                "max_results": 50,
            },
        }
        return ApiResponse(
            data=response_data,
            status=status.HTTP_200_OK,
            message="AI search statistics retrieved successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI search stats failed: {str(e)}",
        )
