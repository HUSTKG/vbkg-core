from typing import Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, PermissionChecker 
from app.services.knowledge_graph import KnowledgeGraphService

router = APIRouter()

check_read_permission = PermissionChecker("knowledge:read")
check_write_permission = PermissionChecker("knowledge:write")


class EntityCreate(BaseModel):
    text: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    properties: Dict[str, Any] = Field(default_factory=dict)
    fibo_class: Optional[str] = None
    source_document_id: Optional[str] = None


class RelationshipCreate(BaseModel):
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    fibo_property: Optional[str] = None
    source_document_id: Optional[str] = None


class EntityUpdate(BaseModel):
    properties: Dict[str, Any] = Field(default_factory=dict)
    fibo_class: Optional[str] = None


class CypherQuery(BaseModel):
    query: str
    parameters: Optional[Dict[str, Any]] = None


@router.post("/entities", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_in: EntityCreate,
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Create a new entity in the knowledge graph.
    """
    kg_service = KnowledgeGraphService()
    return await kg_service.create_entity(
        entity_text=entity_in.text,
        entity_type=entity_in.type,
        properties=entity_in.properties,
        fibo_class=entity_in.fibo_class,
        source_document_id=entity_in.source_document_id
    )


@router.get("/entities/{entity_id}", response_model=Dict[str, Any])
async def read_entity(
    entity_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Get a specific entity by ID.
    """
    kg_service = KnowledgeGraphService()
    return await kg_service.get_entity(entity_id=entity_id)


@router.get("/entities/{entity_id}/relationships", response_model=List[Dict[str, Any]])
async def read_entity_relationships(
    entity_id: str = Path(...),
    direction: Optional[str] = Query(None, enum=["incoming", "outgoing"]),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Get all relationships for an entity.
    """
    kg_service = KnowledgeGraphService()
    return await kg_service.get_entity_relationships(
        entity_id=entity_id,
        direction=direction
    )


@router.patch("/entities/{entity_id}", response_model=Dict[str, Any])
async def update_entity(
    entity_in: EntityUpdate,
    entity_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Update an entity's properties.
    """
    kg_service = KnowledgeGraphService()
    return await kg_service.update_entity(
        entity_id=entity_id,
        properties=entity_in.properties,
        fibo_class=entity_in.fibo_class
    )


@router.delete("/entities/{entity_id}", response_model=Dict[str, Any])
async def delete_entity(
    entity_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Delete an entity and all its relationships.
    """
    kg_service = KnowledgeGraphService()
    return await kg_service.delete_entity(entity_id=entity_id)


@router.get("/entities", response_model=List[Dict[str, Any]])
async def search_entities(
    query: str = Query(..., min_length=1),
    entity_type: Optional[str] = None,
    fibo_class: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Search for entities by text.
    """
    kg_service = KnowledgeGraphService()
    return await kg_service.search_entities(
        query=query,
        entity_type=entity_type,
        fibo_class=fibo_class,
        limit=limit
    )


@router.post("/relationships", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_relationship(
    relationship_in: RelationshipCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Create a relationship between two entities.
    """
    kg_service = KnowledgeGraphService()
    return await kg_service.create_relationship(
        source_id=relationship_in.source_id,
        target_id=relationship_in.target_id,
        relationship_type=relationship_in.type,
        properties=relationship_in.properties,
        fibo_property=relationship_in.fibo_property,
        source_document_id=relationship_in.source_document_id
    )


@router.post("/query", response_model=List[Dict[str, Any]])
async def execute_query(
    query_in: CypherQuery,
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Execute a Cypher query against the knowledge graph.
    """
    kg_service = KnowledgeGraphService()
    return await kg_service.execute_query(
        query=query_in.query,
        parameters=query_in.parameters
    )


@router.get("/stats", response_model=Dict[str, Any])
async def get_knowledge_graph_stats(
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> Any:
    """
    Get statistics about the knowledge graph entities.
    """
    kg_service = KnowledgeGraphService()
    return await kg_service.get_entity_stats()


@router.post("/entities/merge", response_model=str)
async def create_or_merge_entity(
    entity_in: EntityCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Create a new entity or merge with existing one if found.
    """
    kg_service = KnowledgeGraphService()
    return await kg_service.create_or_merge_entity(
        entity_text=entity_in.text,
        entity_type=entity_in.type,
        properties=entity_in.properties,
        fibo_class=entity_in.fibo_class,
        source_document_id=entity_in.source_document_id
    )
