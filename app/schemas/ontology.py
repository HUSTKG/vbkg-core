from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.domain import EntityTypeResponse, RelationshipTypeResponse


class OntologyClassBase(BaseModel):
    uri: str = Field(..., description="URI of the Ontology class")
    label: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class OntologyClassCreate(OntologyClassBase):
    parent_class_uri: Optional[str] = None
    is_custom: bool = False


class OntologyClassUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    parent_class_uri: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class OntologyClass(OntologyClassBase):
    id: int
    parent_class_id: Optional[int] = None
    is_custom: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OntologyPropertyBase(BaseModel):
    uri: str = Field(..., description="URI of the Ontology property")
    label: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    property_type: str = Field(
        ..., description="Type of property: 'object' or 'datatype'"
    )


class OntologyPropertyCreate(OntologyPropertyBase):
    domain_class_uri: Optional[str] = None
    range_class_uri: Optional[str] = None
    is_custom: bool = False


class OntologyPropertyUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    domain_class_uri: Optional[str] = None
    range_class_uri: Optional[str] = None
    property_type: Optional[str] = None


class OntologyProperty(OntologyPropertyBase):
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
    fibo_class_uri: str = Field(..., description="Ontology class URI")
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
    fibo_property_uri: str = Field(..., description="Ontology property URI")
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
    fibo_property: Optional[OntologyProperty] = None  # Joined Ontology property

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


class OntologyClassSuggestion(BaseModel):
    fibo_class: OntologyClass
    confidence: float
    reason: str


class OntologyPropertySuggestion(BaseModel):
    fibo_property: OntologyProperty
    confidence: float
    reason: str
