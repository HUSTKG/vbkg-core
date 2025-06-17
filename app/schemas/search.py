# app/schemas/search.py (Enhanced version)

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SearchType(str, Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    AI_POWERED = "ai_powered"  # New AI search type


class SearchFilter(BaseModel):
    field: str
    operator: str  # eq, gt, lt, gte, lte, contains, in
    value: Any


class RelationshipFilter(BaseModel):
    relationship_type: Optional[str] = None
    target_type: Optional[str] = None
    target_property: Optional[str] = None
    target_value: Optional[Any] = None
    direction: str = "outgoing"  # outgoing, incoming, both


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SearchSort(BaseModel):
    field: str
    order: SortOrder = SortOrder.ASC


class SearchRequest(BaseModel):
    query: str
    entity_types: Optional[List[str]] = None
    search_type: SearchType = SearchType.HYBRID
    filters: Optional[List[SearchFilter]] = None
    relationship_filters: Optional[List[RelationshipFilter]] = None
    sort: Optional[List[SearchSort]] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)
    include_relationships: bool = False
    include_similar_entities: bool = False
    similarity_threshold: Optional[float] = None
    embedding_model: Optional[str] = None
    return_fields: Optional[List[str]] = None  # If None, return all fields


class EntitySearchResult(BaseModel):
    id: str
    text: str
    type: Optional[str]
    properties: Dict[str, Any]
    ontology_class: Optional[str] = None
    score: float
    relationships: Optional[List[Dict[str, Any]]] = None
    similar_entities: Optional[List[Dict[str, Any]]] = None


class SearchResponse(BaseModel):
    results: List[EntitySearchResult]
    total: int
    query: str
    search_type: SearchType
    execution_time_ms: int


class EmbeddingRequest(BaseModel):
    text: str
    model: Optional[str] = None


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    model: str
    text: str
    vector_size: int


class SimilarEntityRequest(BaseModel):
    entity_id: str
    limit: int = Field(10, ge=1, le=100)
    similarity_threshold: float = Field(0.7, ge=0, le=1)
    entity_types: Optional[List[str]] = None


class GraphSearchQuery(BaseModel):
    start_entity_id: Optional[str] = None
    start_entity_type: Optional[str] = None
    start_entity_text: Optional[str] = None
    end_entity_type: Optional[str] = None
    max_depth: int = Field(3, ge=1, le=5)
    limit: int = Field(20, ge=1, le=100)
    relationship_path: Optional[List[str]] = None  # e.g. ["HAS_ACCOUNT", "BELONGS_TO"]


class GraphSearchResult(BaseModel):
    paths: List[Dict[str, Any]]
    total: int
    execution_time_ms: int


# ===== NEW AI SEARCH SCHEMAS =====

class AISearchRequest(BaseModel):
    """Request model for AI-powered search"""
    
    query: str = Field(..., description="Natural language query")
    entity_types: Optional[List[str]] = Field(
        None, description="Filter by specific entity types"
    )
    max_candidates: int = Field(
        50, ge=1, le=200, description="Maximum entities to consider for ranking"
    )
    similarity_threshold: float = Field(
        0.3, ge=0.0, le=1.0, description="Minimum similarity threshold for semantic search"
    )
    top_k_entities: int = Field(
        10, ge=1, le=50, description="Number of top entities to include in response"
    )
    subgraph_radius: int = Field(
        2, ge=1, le=4, description="Radius for subgraph extraction around top entities"
    )
    max_subgraph_nodes: int = Field(
        100, ge=10, le=500, description="Maximum nodes in subgraph context"
    )
    damping_factor: float = Field(
        0.85, ge=0.1, le=0.99, description="PersonRank damping factor"
    )
    max_iterations: int = Field(
        20, ge=5, le=100, description="Maximum iterations for PersonRank algorithm"
    )
    generate_answer: bool = Field(
        True, description="Whether to generate LLM answer"
    )
    llm_model: str = Field(
        "gpt-4o-mini", description="LLM model to use for answer generation"
    )


class EntityRankResult(BaseModel):
    """Entity with ranking scores"""
    
    entity_id: str
    entity_text: str
    entity_type: str
    similarity_score: float = Field(description="Semantic similarity to query")
    personrank_score: float = Field(description="PersonRank score in graph")
    final_score: float = Field(description="Combined ranking score")
    properties: Dict[str, Any] = Field(default_factory=dict)


class SubgraphContext(BaseModel):
    """Subgraph context around top entities"""
    
    nodes: List[Dict[str, Any]] = Field(description="Nodes in subgraph")
    edges: List[Dict[str, Any]] = Field(description="Edges in subgraph")
    node_count: int
    edge_count: int


class AISearchResponse(BaseModel):
    """Response from AI search"""
    
    query: str
    answer: str = Field(description="Generated answer from LLM")
    entities: List[EntityRankResult] = Field(description="Top ranked entities")
    subgraph_context: Optional[SubgraphContext] = Field(description="Graph context")
    execution_time_ms: int
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in answer")
    total_candidates: int = Field(description="Total entities considered")


class SearchSuggestionRequest(BaseModel):
    """Request for search suggestions"""
    
    partial_query: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(5, ge=1, le=20)


class SearchSuggestionResponse(BaseModel):
    """Response with search suggestions"""
    
    suggestions: List[str]
    query: str
