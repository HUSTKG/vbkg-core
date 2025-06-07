from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ConflictType(str, Enum):
    DUPLICATE_ENTITY = "duplicate_entity"
    CONTRADICTORY_RELATIONSHIP = "contradictory_relationship"
    MISSING_RELATIONSHIP = "missing_relationship"
    ATTRIBUTE_MISMATCH = "attribute_mismatch"
    TEMPORAL_CONFLICT = "temporal_conflict"
    SOURCE_CONFLICT = "source_conflict"
    SCHEMA_MISMATCH = "schema_mismatch"


class ConflictSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictStatus(str, Enum):
    DETECTED = "detected"
    UNDER_REVIEW = "under_review"
    RESOLVED_MANUAL = "resolved_manual"
    RESOLVED_AUTO = "resolved_auto"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ResolutionMethod(str, Enum):
    MERGE_ENTITIES = "merge_entities"
    KEEP_BOTH = "keep_both"
    KEEP_SOURCE = "keep_source"
    KEEP_TARGET = "keep_target"
    CREATE_NEW = "create_new"
    DELETE_CONFLICTING = "delete_conflicting"
    MANUAL_EDIT = "manual_edit"
    AI_RESOLUTION = "ai_resolution"
    TEMPORAL_ORDERING = "temporal_ordering"
    SOURCE_PRIORITIZATION = "source_prioritization"


# Base Conflict Model
class ConflictBase(BaseModel):
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    confidence_score: Union[str, float] = Field(..., ge=0.0, le=1.0)
    source_entity_id: Optional[str] = None
    target_entity_id: Optional[str] = None
    source_relationship_id: Optional[str] = None
    target_relationship_id: Optional[str] = None
    conflicting_attributes: Optional[Dict[str, Any]] = None
    context_data: Optional[Dict[str, Any]] = None

    @field_validator('confidence_score')
    def validate_confidence_score(cls, v):
        if isinstance(v, str):
            return float(v)
        return v


# Specific Conflict Models

class DuplicateEntityConflict(ConflictBase):
    """Model for duplicate entity conflicts with detailed similarity metrics"""
    
    conflict_type: ConflictType = ConflictType.DUPLICATE_ENTITY
    similarity_scores: Dict[str, float] = Field(
        ..., 
        description="Individual similarity scores for different metrics"
    )
    weighted_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Final weighted similarity score"
    )
    weight_configuration: Dict[str, float] = Field(
        ...,
        description="Weights used for calculation"
    )
    matching_attributes: List[str] = Field(
        default_factory=list,
        description="List of attributes that match between entities"
    )
    differing_attributes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of attributes that differ with their values"
    )
    source_documents: Dict[str, str] = Field(
        default_factory=dict,
        description="Source document IDs for both entities"
    )


class ContradictoryRelationshipConflict(ConflictBase):
    """Model for contradictory relationship conflicts"""
    
    conflict_type: ConflictType = ConflictType.CONTRADICTORY_RELATIONSHIP
    relationship_types: List[str] = Field(
        ...,
        description="The contradictory relationship types"
    )
    contradiction_pattern: str = Field(
        ...,
        description="Type of contradiction (direct, temporal, logical)"
    )
    temporal_overlap: Optional[Dict[str, Any]] = Field(
        None,
        description="Details about temporal overlap if applicable"
    )
    affected_entities: Dict[str, str] = Field(
        ...,
        description="IDs and names of entities involved"
    )


class AttributeMismatchConflict(ConflictBase):
    """Model for attribute mismatch conflicts"""
    
    conflict_type: ConflictType = ConflictType.ATTRIBUTE_MISMATCH
    mismatched_attribute: str = Field(
        ...,
        description="The specific attribute that doesn't match"
    )
    attribute_values: Dict[str, Any] = Field(
        ...,
        description="Values from each entity"
    )
    value_similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity between the mismatched values"
    )
    is_critical_attribute: bool = Field(
        ...,
        description="Whether this is a critical attribute"
    )
    suggested_value: Optional[Any] = Field(
        None,
        description="AI-suggested resolution value"
    )


class TemporalConflict(ConflictBase):
    """Model for temporal conflicts"""
    
    conflict_type: ConflictType = ConflictType.TEMPORAL_CONFLICT
    temporal_issue: str = Field(
        ...,
        description="Type of temporal issue (overlap, impossible_sequence, missing_dates)"
    )
    event_timeline: List[Dict[str, Any]] = Field(
        ...,
        description="Chronological list of conflicting events"
    )
    date_conflicts: List[Dict[str, Any]] = Field(
        ...,
        description="Specific date conflicts with details"
    )
    suggested_timeline: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="AI-suggested corrected timeline"
    )


class SourceConflict(ConflictBase):
    """Model for source-based conflicts"""
    
    conflict_type: ConflictType = ConflictType.SOURCE_CONFLICT
    source_info: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Information about each conflicting source"
    )
    conflicting_data: List[Dict[str, Any]] = Field(
        ...,
        description="List of specific data points that conflict"
    )
    source_reliability_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Reliability scores for each source"
    )
    recommended_source: Optional[str] = Field(
        None,
        description="Recommended source based on reliability"
    )


# Conflict Creation Models with validation

class ConflictCreate(ConflictBase):
    detected_by: str  # "system", "user", "expert"
    auto_resolution_attempted: bool = False


class DuplicateEntityConflictCreate(DuplicateEntityConflict):
    detected_by: str
    auto_resolution_attempted: bool = False


class ContradictoryRelationshipConflictCreate(ContradictoryRelationshipConflict):
    detected_by: str
    auto_resolution_attempted: bool = False


class AttributeMismatchConflictCreate(AttributeMismatchConflict):
    detected_by: str
    auto_resolution_attempted: bool = False


class TemporalConflictCreate(TemporalConflict):
    detected_by: str
    auto_resolution_attempted: bool = False


class SourceConflictCreate(SourceConflict):
    detected_by: str
    auto_resolution_attempted: bool = False


# Resolution Models

class ConflictResolution(BaseModel):
    resolution_method: ResolutionMethod
    resolution_data: Dict[str, Any]
    reasoning: str
    confidence_score: Optional[Union[str, float]] = None
    resolved_by: str  # user_id or "ai_system"
    resolution_timestamp: datetime
    validation_required: bool = False


class ConflictResolutionRequest(BaseModel):
    resolution_method: ResolutionMethod
    resolution_data: Dict[str, Any]
    reasoning: str
    confidence_score: Optional[Union[str, float]] = None


# Conflict Resolution Strategies

class ResolutionStrategy(BaseModel):
    """Base class for resolution strategies"""
    
    strategy_type: str
    applicable_conflict_types: List[ConflictType]
    confidence_threshold: float = Field(0.7, ge=0.0, le=1.0)
    requires_human_review: bool = True


class MergeStrategy(ResolutionStrategy):
    """Strategy for merging duplicate entities"""
    
    strategy_type: str = "merge"
    applicable_conflict_types: List[ConflictType] = [ConflictType.DUPLICATE_ENTITY]
    merge_rules: Dict[str, str] = Field(
        default_factory=dict,
        description="Rules for merging specific attributes"
    )
    preserve_relationships: bool = True
    create_alias: bool = True


class TemporalOrderingStrategy(ResolutionStrategy):
    """Strategy for resolving temporal conflicts"""
    
    strategy_type: str = "temporal_ordering"
    applicable_conflict_types: List[ConflictType] = [ConflictType.TEMPORAL_CONFLICT]
    prefer_recent_dates: bool = True
    validate_sequence: bool = True
    fill_missing_dates: bool = False


class SourcePrioritizationStrategy(ResolutionStrategy):
    """Strategy for resolving source conflicts"""
    
    strategy_type: str = "source_prioritization"
    applicable_conflict_types: List[ConflictType] = [ConflictType.SOURCE_CONFLICT]
    source_priority_order: List[str] = Field(
        default_factory=list,
        description="Ordered list of source IDs by priority"
    )
    consider_recency: bool = True
    consider_confidence: bool = True


# Conflict Management Models

class Conflict(ConflictBase):
    id: str
    status: ConflictStatus
    detected_at: datetime
    detected_by: str
    assigned_to: Optional[str] = None  # expert user_id
    resolution: Optional[ConflictResolution] = None
    review_notes: Optional[str] = None
    escalation_reason: Optional[str] = None
    auto_resolution_suggestions: Optional[List[Dict[str, Any]]] = None
    related_conflicts: Optional[List[str]] = Field(
        default_factory=list,
        description="IDs of related conflicts"
    )
    impact_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Estimated impact on knowledge graph quality"
    )

    class Config:
        from_attributes = True


class ConflictUpdate(BaseModel):
    status: Optional[ConflictStatus] = None
    assigned_to: Optional[str] = None
    resolution: Optional[ConflictResolution] = None
    review_notes: Optional[str] = None
    escalation_reason: Optional[str] = None


class ConflictBatch(BaseModel):
    """Model for batch conflict operations"""
    
    conflict_ids: List[str]
    action: str = Field(..., description="batch_resolve, batch_assign, batch_reject")
    action_data: Dict[str, Any]
    reason: str


# Quality Assessment Models

class QualityDimension(str, Enum):
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    TIMELINESS = "timeliness"
    RELEVANCE = "relevance"


class QualityAssessment(BaseModel):
    entity_id: Optional[str] = None
    relationship_id: Optional[str] = None
    dimension: QualityDimension
    score: float = Field(..., ge=0.0, le=1.0)
    assessment_date: datetime
    assessment_method: str  # "automatic", "manual", "rule_based"
    details: Optional[Dict[str, Any]] = None
    improvement_suggestions: Optional[List[str]] = None
    related_conflicts: Optional[List[str]] = Field(
        default_factory=list,
        description="IDs of conflicts affecting this quality dimension"
    )


class QualityReport(BaseModel):
    report_date: str 
    overall_score: float
    dimension_scores: Dict[QualityDimension, float]
    total_entities: int
    total_relationships: int
    issues_detected: int
    conflicts_pending: int
    conflicts_by_type: Dict[ConflictType, int]
    conflicts_by_severity: Dict[ConflictSeverity, int]
    improvement_recommendations: List[str]
    trend_analysis: Optional[Dict[str, Any]] = Field(
        None,
        description="Comparison with previous reports"
    )


# Knowledge Graph Edit Models

class KGEditAction(str, Enum):
    CREATE_ENTITY = "create_entity"
    UPDATE_ENTITY = "update_entity"
    DELETE_ENTITY = "delete_entity"
    MERGE_ENTITIES = "merge_entities"
    CREATE_RELATIONSHIP = "create_relationship"
    UPDATE_RELATIONSHIP = "update_relationship"
    DELETE_RELATIONSHIP = "delete_relationship"
    BULK_UPDATE = "bulk_update"


class KGEdit(BaseModel):
    action: KGEditAction
    entity_data: Optional[Dict[str, Any]] = None
    relationship_data: Optional[Dict[str, Any]] = None
    bulk_data: Optional[List[Dict[str, Any]]] = None
    reason: str
    validate_before_apply: bool = True
    conflict_id: Optional[str] = Field(
        None,
        description="ID of conflict this edit resolves"
    )


class KGEditResult(BaseModel):
    success: bool
    applied_changes: List[Dict[str, Any]]
    validation_errors: Optional[List[str]] = None
    rollback_info: Optional[Dict[str, Any]] = None
    resolved_conflicts: Optional[List[str]] = Field(
        default_factory=list,
        description="IDs of conflicts resolved by this edit"
    )


# Conflict Analysis Models

class ConflictAnalysis(BaseModel):
    """Analysis of conflicts in the knowledge graph"""
    
    analysis_date: datetime
    total_conflicts: int
    conflicts_by_type: Dict[ConflictType, int]
    conflicts_by_severity: Dict[ConflictSeverity, int]
    conflicts_by_status: Dict[ConflictStatus, int]
    resolution_rate: float
    auto_resolution_rate: float
    average_resolution_time: Optional[float] = None
    most_common_patterns: List[Dict[str, Any]]
    recommendations: List[str]
