from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import PermissionChecker, get_current_user
from app.schemas.api import ApiResponse, PaginatedResponse
from app.schemas.entity import Entity
from app.schemas.knowledge import (CypherQuery, EntityCreate, EntityUpdate,
                                   RelationshipCreate)
from app.schemas.relationship import Relationship
from app.services.knowledge_graph import KnowledgeGraphService

router = APIRouter()

check_read_permission = PermissionChecker("kg:read")
check_write_permission = PermissionChecker("kg:write")


@router.post("/entities", response_model=ApiResponse[Entity], status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_in: EntityCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[Entity]:
    """
    Create a new entity in the knowledge graph.
    """
    kg_service = KnowledgeGraphService()
    response = await kg_service.create_entity(
        entity_text=entity_in.text,
        entity_type=entity_in.type,
        properties=entity_in.properties,
        fibo_class=entity_in.fibo_class,
        source_document_id=entity_in.source_document_id
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_201_CREATED,
        message="Entity created successfully"
    )

@router.get("/entities/search", response_model=ApiResponse[List[Dict[str, Any]]])
async def search_entities(
    query: str = Query(..., min_length=1),
    entity_type: Optional[str] = None,
    fibo_class: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    Search for entities by text.
    """
    kg_service = KnowledgeGraphService()
    response = await kg_service.search_entities(
        query=query,
        entity_type=entity_type,
        fibo_class=fibo_class,
        limit=limit
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entities retrieved successfully"
    )

@router.get("/entities/{entity_id}", response_model=ApiResponse[Entity])
async def read_entity(
    entity_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[Entity]:
    """
    Get a specific entity by ID.
    """
    kg_service = KnowledgeGraphService()
    response = await kg_service.get_entity(entity_id=entity_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entity retrieved successfully"
    )


@router.get("/entities/{entity_id}/relationships", response_model=ApiResponse[List[Relationship]])
async def read_entity_relationships(
    entity_id: str = Path(...),
    direction: Optional[str] = Query(None, enum=["incoming", "outgoing"]),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[List[Relationship]]:
    """
    Get all relationships for an entity.
    """
    kg_service = KnowledgeGraphService()
    response = await kg_service.get_entity_relationships(
        entity_id=entity_id,
        direction=direction
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entity relationships retrieved successfully"
    )


@router.patch("/entities/{entity_id}", response_model=ApiResponse[Entity])
async def update_entity(
    entity_in: EntityUpdate,
    entity_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[Entity]:
    """
    Update an entity's properties.
    """
    kg_service = KnowledgeGraphService()
    response = await kg_service.update_entity(
        entity_id=entity_id,
        properties=entity_in.properties,
        fibo_class=entity_in.fibo_class
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entity updated successfully"
    )


@router.delete("/entities/{entity_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_entity(
    entity_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete an entity and all its relationships.
    """
    kg_service = KnowledgeGraphService()
    response = await kg_service.delete_entity(entity_id=entity_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entity deleted successfully"
    )



@router.post("/relationships", response_model=ApiResponse[Relationship], status_code=status.HTTP_201_CREATED)
async def create_relationship(
    relationship_in: RelationshipCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[Relationship]:
    """
    Create a relationship between two entities.
    """
    kg_service = KnowledgeGraphService()
    response = await kg_service.create_relationship(
        source_id=relationship_in.source_id,
        target_id=relationship_in.target_id,
        relationship_type=relationship_in.type,
        properties=relationship_in.properties,
        fibo_property=relationship_in.fibo_property,
        source_document_id=relationship_in.source_document_id
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_201_CREATED,
        message="Relationship created successfully"
    )


@router.post("/query", response_model=ApiResponse[List[Dict[str, Any]]])
async def execute_query(
    query_in: CypherQuery,
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    Execute a Cypher query against the knowledge graph.
    """
    kg_service = KnowledgeGraphService()
    response = await kg_service.execute_query(
        query=query_in.query,
        parameters=query_in.parameters
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Query executed successfully"
    )


@router.get("/stats", response_model=ApiResponse[Dict[str, Any]])
async def get_knowledge_graph_stats(
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[Dict[str, Any]]:
    """
    Get statistics about the knowledge graph entities.
    """
    kg_service = KnowledgeGraphService()
    response = await kg_service.get_entity_stats()
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Knowledge graph statistics retrieved successfully"
    )


@router.post("/entities/merge", response_model=ApiResponse[Entity])
async def create_or_merge_entity(
    entity_in: EntityCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[Entity]:
    """
    Create a new entity or merge with existing one if found.
    """
    kg_service = KnowledgeGraphService()
    response = await kg_service.create_or_merge_entity(
        entity_text=entity_in.text,
        entity_type=entity_in.type,
        properties=entity_in.properties,
        fibo_class=entity_in.fibo_class,
        source_document_id=entity_in.source_document_id
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_201_CREATED,
        message="Entity created or merged successfully"
    )
