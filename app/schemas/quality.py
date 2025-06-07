from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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


class QualityReport(BaseModel):
    report_date: str
    overall_score: float
    dimension_scores: Dict[QualityDimension, float]
    total_entities: int
    total_relationships: int
    issues_detected: int
    conflicts_pending: int
    improvement_recommendations: List[str]
