from typing import Optional, List, Dict, Any
from pydantic import BaseModel, UUID4, Field, validator
from datetime import datetime

class RelationshipBase(BaseModel):
    """Base model for relationship data."""
    relationship_type: str
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)
    confidence: Optional[float] = 1.0
    
    @validator('confidence')
    def check_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v

class RelationshipCreate(RelationshipBase):
    """Model for creating a new relationship."""
    source_entity_id: UUID4
    target_entity_id: UUID4
    source_document_id: Optional[UUID4] = None
    is_verified: Optional[bool] = False
    verification_notes: Optional[str] = None

class RelationshipUpdate(BaseModel):
    """Model for updating an existing relationship."""
    relationship_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    is_verified: Optional[bool] = None
    verification_notes: Optional[str] = None
    
    @validator('confidence')
    def check_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v

class Relationship(RelationshipBase):
    """Complete relationship model returned from API."""
    id: UUID4
    source_entity_id: UUID4
    target_entity_id: UUID4
    source_document_id: Optional[UUID4] = None
    neo4j_id: Optional[str] = None
    fibo_property_id: Optional[int] = None
    is_verified: bool = False
    verification_notes: Optional[str] = None
    verified_by: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime
    
    # Expanded entity data (will be populated in the response)
    source_entity: Optional[Dict[str, Any]] = None
    target_entity: Optional[Dict[str, Any]] = None
    
    class Config:
        orm_mode = True

class RelationshipInDB(Relationship):
    """Model for relationship stored in database."""
    pass

class RelationshipSearchParams(BaseModel):
    """Parameters for relationship search."""
    relationship_type: Optional[str] = None
    source_entity_id: Optional[UUID4] = None
    target_entity_id: Optional[UUID4] = None
    source_document_id: Optional[UUID4] = None
    is_verified: Optional[bool] = None
    confidence_min: Optional[float] = None
    skip: int = 0
    limit: int = 100
