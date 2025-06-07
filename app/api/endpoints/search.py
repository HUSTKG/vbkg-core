from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import PermissionChecker
from app.schemas.api import ApiResponse
from app.schemas.search import (
    EmbeddingRequest,
    EmbeddingResponse,
    GraphSearchQuery,
    GraphSearchResult,
    SearchRequest,
    SearchResponse,
    SimilarEntityRequest,
)
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
    Search for entities in the knowledge graph.
    """
    search_service = SearchService()
    response = await search_service.search_entities(search_request=search_request)
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
    """
    Find entities similar to the specified entity.
    """
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
    """
    Perform a graph search following a relationship path.
    """
    search_service = SearchService()
    response = await search_service.graph_search(
        query=query,
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Graph search completed successfully",
    )


@router.post("/embedding", response_model=ApiResponse[EmbeddingResponse])
async def generate_embedding(
    request: EmbeddingRequest,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[EmbeddingResponse]:
    """
    Generate embedding for arbitrary text.
    """
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
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Create or update embedding for an entity.
    """
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
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Update embeddings for a batch of entities without embeddings.
    """
    search_service = SearchService()
    response = await search_service.update_entity_embeddings_batch(
        entity_type=entity_type, limit=limit, model=model
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Batch entity embeddings updated successfully",
    )
