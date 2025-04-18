from typing import Optional, List, Dict, Any
from pydantic import BaseModel, UUID4, Field, validator
from datetime import datetime

class EntityBase(BaseModel):
    """Base model for entity data."""
    entity_text: str
    entity_type: str
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)
    confidence: Optional[float] = 1.0
    
    @validator('confidence')
    def check_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v

class EntityCreate(EntityBase):
    """Model for creating a new entity."""
    source_document_id: Optional[UUID4] = None
    is_verified: Optional[bool] = False
    verification_notes: Optional[str] = None

class EntityUpdate(BaseModel):
    """Model for updating an existing entity."""
    entity_text: Optional[str] = None
    entity_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    is_verified: Optional[bool] = None
    verification_notes: Optional[str] = None
    
    @validator('confidence')
    def check_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v

class Entity(EntityBase):
    """Complete entity model returned from API."""
    id: UUID4
    source_document_id: Optional[UUID4] = None
    neo4j_id: Optional[str] = None
    fibo_class_id: Optional[int] = None
    is_verified: bool = False
    verification_notes: Optional[str] = None
    verified_by: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime
    
    # Optional embedding vector (not always returned)
    embedding: Optional[List[float]] = None
    
    class Config:
        orm_mode = True

class EntityInDB(Entity):
    """Model for entity stored in database."""
    pass

class EntitySearchResult(BaseModel):
    """Model for entity search result with similarity score."""
    entity: Entity
    similarity: Optional[float] = None

class EntitySearchParams(BaseModel):
    """Parameters for entity search."""
    query_text: Optional[str] = None
    entity_type: Optional[str] = None
    source_document_id: Optional[UUID4] = None
    is_verified: Optional[bool] = None
    confidence_min: Optional[float] = None
    semantic_search: bool = False
    skip: int = 0
    limit: int = 100

class EntityConflict(BaseModel):
    """Model for entity conflict."""
    id: UUID4
    entity_id_1: UUID4
    entity_id_2: UUID4
    similarity_score: float
    conflict_type: str
    status: str = "pending"
    resolution_notes: Optional[str] = None
    resolved_by: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime
    
    # Expanded entity data (will be populated in the response)
    entity1: Optional[Entity] = None
    entity2: Optional[Entity] = None
    
    class Config:
        orm_mode = True

class EntityResolution(BaseModel):
    """Model for resolving entity conflicts."""
    resolution_type: str = Field(..., description="Type of resolution: 'merge', 'keep_separate', or 'delete'")
    keep_entity_id: Optional[UUID4] = Field(None, description="ID of the entity to keep (for 'merge' or 'delete')")
    merged_properties: Optional[Dict[str, Any]] = Field(None, description="Properties for the merged entity")
    notes: Optional[str] = Field(None, description="Notes about the resolution")
    
    @validator('resolution_type')
    def check_resolution_type(cls, v):
        if v not in ['merge', 'keep_separate', 'delete']:
            raise ValueError("resolution_type must be one of: 'merge', 'keep_separate', 'delete'")
        return v
