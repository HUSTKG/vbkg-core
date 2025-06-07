from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class SearchType(str, Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


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
    type: str
    properties: Dict[str, Any]
    fibo_class: Optional[str] = None
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
    relationship_path: List[str]  # e.g. ["HAS_ACCOUNT", "BELONGS_TO"]
    end_entity_type: Optional[str] = None
    max_depth: int = Field(3, ge=1, le=5)
    limit: int = Field(20, ge=1, le=100)

    @field_validator("relationship_path")
    def validate_relationship_path(cls, v):
        if not v:
            raise ValueError("Relationship path must not be empty")
        return v

    # @field_validator("start_entity_id", "start_entity_type", "start_entity_text")
    # def validate_start_entity(cls, v, values):
    #     # Ensure at least one of start_entity_id, start_entity_type+start_entity_text is provided
    #     if (
    #         "start_entity_id" not in values
    #         and "start_entity_type" not in values
    #         and "start_entity_text" not in values
    #     ):
    #         raise ValueError(
    #             "Either start_entity_id or both start_entity_type and start_entity_text must be provided"
    #         )
    #     return v


class GraphSearchResult(BaseModel):
    paths: List[Dict[str, Any]]
    total: int
    execution_time_ms: int
