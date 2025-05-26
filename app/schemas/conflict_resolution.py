from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


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


class ConflictCreate(ConflictBase):
    detected_by: str  # "system", "user", "expert"
    auto_resolution_attempted: bool = False


class ConflictResolution(BaseModel):
    resolution_method: ResolutionMethod
    resolution_data: Dict[str, Any]
    reasoning: str
    confidence_score: Optional[Union[str, float]] = None
    resolved_by: str  # user_id or "ai_system"
    resolution_timestamp: datetime
    validation_required: bool = False


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

    class Config:
        from_attributes = True


class ConflictUpdate(BaseModel):
    status: Optional[ConflictStatus] = None
    assigned_to: Optional[str] = None
    resolution: Optional[ConflictResolution] = None
    review_notes: Optional[str] = None
    escalation_reason: Optional[str] = None


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
    score: str = Field(..., ge=0.0, le=1.0)
    assessment_date: datetime
    assessment_method: str  # "automatic", "manual", "rule_based"
    details: Optional[Dict[str, Any]] = None
    improvement_suggestions: Optional[List[str]] = None


class QualityReport(BaseModel):
    report_date: datetime
    overall_score: str
    dimension_scores: Dict[QualityDimension, str]
    total_entities: int
    total_relationships: int
    issues_detected: int
    conflicts_pending: int
    improvement_recommendations: List[str]


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


class KGEditResult(BaseModel):
    success: bool
    applied_changes: List[Dict[str, Any]]
    validation_errors: Optional[List[str]] = None
    rollback_info: Optional[Dict[str, Any]] = None
