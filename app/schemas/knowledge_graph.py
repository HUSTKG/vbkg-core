from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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


class CypherQuery(BaseModel):
    query: str
    parameters: Optional[Dict[str, Any]] = None
