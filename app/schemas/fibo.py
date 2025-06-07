from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.domain import EntityTypeResponse, RelationshipTypeResponse


class FIBOClassBase(BaseModel):
    uri: str = Field(..., description="URI of the FIBO class")
    label: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class FIBOClassCreate(FIBOClassBase):
    parent_class_uri: Optional[str] = None
    is_custom: bool = False


class FIBOClassUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    parent_class_uri: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class FIBOClass(FIBOClassBase):
    id: int
    parent_class_id: Optional[int] = None
    is_custom: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FIBOPropertyBase(BaseModel):
    uri: str = Field(..., description="URI of the FIBO property")
    label: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    property_type: str = Field(
        ..., description="Type of property: 'object' or 'datatype'"
    )


class FIBOPropertyCreate(FIBOPropertyBase):
    domain_class_uri: Optional[str] = None
    range_class_uri: Optional[str] = None
    is_custom: bool = False


class FIBOPropertyUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    domain_class_uri: Optional[str] = None
    range_class_uri: Optional[str] = None
    property_type: Optional[str] = None


class FIBOProperty(FIBOPropertyBase):
    id: int
    domain_class_id: Optional[int] = None
    range_class_id: Optional[int] = None
    is_custom: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Updated Mapping Models
class EntityMappingBase(BaseModel):
    entity_type: Optional[str] = Field(None, description="Legacy entity type string")
    entity_type_id: Optional[int] = Field(None, description="Entity type ID reference")
    fibo_class_uri: str = Field(..., description="FIBO class URI")
    confidence: Optional[float] = None
    is_verified: bool = False
    mapping_status: str = Field(
        default="pending", description="Status: pending, mapped, rejected, needs_review"
    )
    mapping_notes: Optional[str] = None
    auto_mapped: bool = False

    @field_validator("mapping_status")
    def validate_mapping_status(cls, v):
        valid_statuses = ["pending", "mapped", "rejected", "needs_review"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class EntityMappingCreate(EntityMappingBase):
    pass


class EntityMappingUpdate(BaseModel):
    entity_type: Optional[str] = None
    entity_type_id: Optional[int] = None
    fibo_class_uri: Optional[str] = None
    confidence: Optional[float] = None
    is_verified: Optional[bool] = None
    mapping_status: Optional[str] = None
    mapping_notes: Optional[str] = None
    auto_mapped: Optional[bool] = None


class EntityMapping(EntityMappingBase):
    id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    entity_type_info: Optional[EntityTypeResponse] = None  # Joined data

    class Config:
        from_attributes = True


class RelationshipMappingBase(BaseModel):
    relationship_type: Optional[str] = Field(
        None, description="Legacy relationship type string"
    )
    relationship_type_id: Optional[int] = Field(
        None, description="Relationship type ID reference"
    )
    fibo_property_uri: str = Field(..., description="FIBO property URI")
    confidence: Optional[float] = None
    is_verified: bool = False
    mapping_status: str = Field(
        default="pending", description="Status: pending, mapped, rejected, needs_review"
    )
    mapping_notes: Optional[str] = None
    auto_mapped: bool = False

    @field_validator("mapping_status")
    def validate_mapping_status(cls, v):
        valid_statuses = ["pending", "mapped", "rejected", "needs_review"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class RelationshipMappingCreate(RelationshipMappingBase):
    pass


class RelationshipMappingUpdate(BaseModel):
    relationship_type: Optional[str] = None
    relationship_type_id: Optional[int] = None
    fibo_property_uri: Optional[str] = None
    confidence: Optional[float] = None
    is_verified: Optional[bool] = None
    mapping_status: Optional[str] = None
    mapping_notes: Optional[str] = None
    auto_mapped: Optional[bool] = None


class RelationshipMapping(RelationshipMappingBase):
    id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    relationship_type_info: Optional[RelationshipTypeResponse] = None  # Joined data
    fibo_property: Optional[FIBOProperty] = None  # Joined FIBO property

    class Config:
        from_attributes = True


# Request/Response Models
class OntologyImportRequest(BaseModel):
    file_id: Optional[str] = None
    url: Optional[str] = None
    format: str = "rdf"  # rdf, owl, ttl

    @field_validator("format")
    def validate_format(cls, v):
        valid_formats = ["rdf", "owl", "ttl"]
        if v not in valid_formats:
            raise ValueError(f"Format must be one of {valid_formats}")
        return v

    @model_validator(mode="after")
    def validate_source(self):
        if not self.file_id and not self.url:
            raise ValueError("Either file_id or url must be provided")
        return self


class OntologyImportResponse(BaseModel):
    success: bool
    message: str
    classes_imported: Optional[int] = None
    properties_imported: Optional[int] = None
    errors: Optional[List[str]] = None


# Suggestion Models
class EntityTypeSuggestion(BaseModel):
    entity_type: EntityTypeResponse
    confidence: float
    reason: str


class RelationshipTypeSuggestion(BaseModel):
    relationship_type: RelationshipTypeResponse
    confidence: float
    reason: str


class FIBOClassSuggestion(BaseModel):
    fibo_class: FIBOClass
    confidence: float
    reason: str


class FIBOPropertySuggestion(BaseModel):
    fibo_property: FIBOProperty
    confidence: float
    reason: str
