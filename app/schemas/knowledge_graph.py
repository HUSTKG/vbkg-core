from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


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

# Request Models
class KGCompletionRequest(BaseModel):
    """Request for knowledge graph completion"""
    entity_ids: Optional[List[str]] = Field(None, description="Specific entity IDs to complete around")
    completion_types: List[str] = Field(
        default=["missing_entities", "missing_relationships"],
        description="Types of completion to perform"
    )
    auto_apply_suggestions: bool = Field(
        default=False,
        description="Whether to automatically apply high-confidence suggestions"
    )
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for auto-application"
    )
    limit_entities: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000,
        description="Maximum number of entities to analyze"
    )
    limit_relationships: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000,
        description="Maximum number of relationships to analyze"
    )


class SuggestionActionRequest(BaseModel):
    """Request to accept, reject, or apply suggestions"""
    suggestion_ids: List[str] = Field(..., description="IDs of suggestions to act upon")
    action: str = Field(..., description="Action to take: accept, reject, apply")
    review_notes: Optional[str] = Field(None, description="Notes about the review decision")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")

    @field_validator('action')
    def validate_action(cls, v):
        if v not in ['accept', 'reject', 'apply']:
            raise ValueError('Action must be one of: accept, reject, apply')
        return v


class SuggestionFilter(BaseModel):
    """Filter for searching suggestions"""
    suggestion_type: Optional[str] = Field(None, pattern="^(entity|relationship)$")
    status: Optional[str] = Field(None, pattern="^(pending|accepted|rejected|applied)$")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    source: Optional[str] = None
    created_after: Optional[str] = None
    created_before: Optional[str] = None


# Response Models
class KGCompletionSuggestion(BaseModel):
    """Complete suggestion model"""
    id: str
    suggestion_type: str
    status: str
    priority: str
    confidence: float
    reason: str
    source: str
    
    # Entity-specific fields
    suggested_entity_text: Optional[str] = None
    suggested_entity_type: Optional[str] = None
    
    # Relationship-specific fields
    source_entity_id: Optional[str] = None
    target_entity_id: Optional[str] = None
    suggested_relationship_type: Optional[str] = None
    source_entity_text: Optional[str] = None
    target_entity_text: Optional[str] = None
    
    # Applied tracking
    applied_entity_id: Optional[str] = None
    applied_relationship_id: Optional[str] = None
    applied_at: Optional[str] = None
    applied_by: Optional[str] = None
    
    # Review tracking
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Metadata
    context_data: Optional[Dict[str, Any]] = None
    validation_errors: Optional[Dict[str, Any]] = None
    
    created_by: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class KGCompletionResponse(BaseModel):
    """Response from knowledge graph completion"""
    suggestions: List[KGCompletionSuggestion]
    stats: Dict[str, Any]
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class SuggestionActionResponse(BaseModel):
    """Response from suggestion actions"""
    processed_suggestions: List[str]
    applied_entities: List[str] = []
    applied_relationships: List[str] = []
    errors: List[str] = []
    success: bool
    message: str


class KGCompletionStats(BaseModel):
    """Knowledge graph completion statistics"""
    total_suggestions: int
    pending_suggestions: int
    accepted_suggestions: int
    rejected_suggestions: int
    applied_suggestions: int
    entity_suggestions: int
    relationship_suggestions: int
    avg_confidence: float
    high_priority_pending: int


# Internal suggestion models for generation
class EntitySuggestionInternal(BaseModel):
    """Internal entity suggestion for generation"""
    suggested_text: str
    suggested_type: str
    reason: str
    confidence: float
    priority: str
    source: str
    context_data: Optional[Dict[str, Any]] = None


class RelationshipSuggestionInternal(BaseModel):
    """Internal relationship suggestion for generation"""
    source_entity: str
    target_entity: str
    suggested_type: str
    reason: str
    confidence: float
    priority: str
    source_entity_type: Optional[str] = None
    target_entity_type: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
