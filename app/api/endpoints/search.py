# app/api/endpoints/search.py
from typing import Annotated, Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, PermissionChecker 
from app.services.search import SearchService
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SimilarEntityRequest,
    EmbeddingRequest,
    EmbeddingResponse,
    GraphSearchQuery,
    GraphSearchResult
)

router = APIRouter()

check_read_permission = PermissionChecker("knowledge:read")
check_write_permission = PermissionChecker("knowledge:write")

@router.post("/entities", response_model=SearchResponse)
async def search_entities(
    search_request: SearchRequest,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)]
) -> Any:
    """
    Search for entities in the knowledge graph.
    """
    search_service = SearchService()
    return await search_service.search_entities(search_request=search_request)


@router.post("/similar", response_model=List[Dict[str, Any]])
async def find_similar_entities(
    request: SimilarEntityRequest,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)]
) -> Any:
    """
    Find entities similar to the specified entity.
    """
    search_service = SearchService()
    return await search_service.find_similar_entities(request=request)


@router.post("/graph", response_model=GraphSearchResult)
async def graph_search(
    query: GraphSearchQuery,
    current_user: Annotated[Dict[str, Any], Depends(check_read_permission)]
) -> Any:
    """
    Perform a graph search following a relationship path.
    """
    search_service = SearchService()
    return await search_service.graph_search(
        start_entity_id=query.start_entity_id,
        start_entity_type=query.start_entity_type,
        start_entity_text=query.start_entity_text,
        relationship_path=query.relationship_path,
        end_entity_type=query.end_entity_type,
        max_depth=query.max_depth,
        limit=query.limit
    )


@router.post("/embedding", response_model=EmbeddingResponse)
async def generate_embedding(
    request: EmbeddingRequest,
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Generate embedding for arbitrary text.
    """
    search_service = SearchService()
    return await search_service.generate_text_embedding(request=request)


@router.post("/entities/{entity_id}/embedding", response_model=Dict[str, Any])
async def create_entity_embedding(
    entity_id: str = Path(...),
    model: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Create or update embedding for an entity.
    """
    search_service = SearchService()
    return await search_service.create_entity_embedding(
        entity_id=entity_id,
        model=model
    )


@router.post("/entities/embeddings/batch", response_model=Dict[str, Any])
async def update_entity_embeddings_batch(
    entity_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    model: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Update embeddings for a batch of entities without embeddings.
    """
    search_service = SearchService()
    return await search_service.update_entity_embeddings_batch(
        entity_type=entity_type,
        limit=limit,
        model=model
    )
