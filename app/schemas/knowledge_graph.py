from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Response Models
class EntityResponse(BaseModel):
    id: str
    entity_text: str
    entity_type: str
    properties: Dict[str, Any]
    confidence: float
    is_verified: bool
    relationship_count: int
    created_at: str
    updated_at: Optional[str] = None


class EntitySearchResponse(BaseModel):
    entities: List[EntityResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class RelationshipResponse(BaseModel):
    id: str
    relationship_type: str
    properties: Dict[str, Any]
    confidence: float
    is_verified: bool
    source_entity: Dict[str, Any]
    target_entity: Dict[str, Any]
    created_at: str


class RelationshipSearchResponse(BaseModel):
    relationships: List[RelationshipResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class SubgraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    center_entity_id: str
    radius: int
    node_count: int
    edge_count: int


class PathResponse(BaseModel):
    length: int
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]


class StatsResponse(BaseModel):
    total_entities: int
    total_relationships: int
    entity_types: List[Dict[str, Any]]
    relationship_types: List[Dict[str, Any]]
    recent_entities_count: int
    avg_relationships_per_entity: float
    last_updated: str


# Request Models
class GraphQueryRequest(BaseModel):
    cypher_query: str = Field(..., description="Cypher query to execute")
    parameters: Optional[Dict[str, Any]] = Field(
        default={}, description="Query parameters"
    )
    limit: Optional[int] = Field(default=100, le=1000, description="Maximum results")


class PathSearchRequest(BaseModel):
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    max_depth: Optional[int] = Field(default=5, le=10, description="Maximum path depth")
    relationship_types: Optional[List[str]] = Field(
        default=None, description="Allowed relationship types"
    )
