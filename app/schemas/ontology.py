from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# =============================================
# ONTOLOGY CLASS SCHEMAS
# =============================================

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


# =============================================
# ONTOLOGY PROPERTY SCHEMAS
# =============================================

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


# =============================================
# MAPPING SCHEMAS (Updated to match database)
# =============================================

class EntityMappingBase(BaseModel):
    entity_type: Optional[str] = Field(None, description="Legacy entity type string")
    ontology_class_id: Optional[int] = Field(None, description="Ontology class ID")
    confidence: Optional[float] = Field(0.8, ge=0, le=1)
    is_verified: bool = False
    mapping_status: str = Field(
        default="pending", description="Status: pending, mapped, rejected, needs_review"
    )
    mapping_notes: Optional[str] = None
    auto_mapped: bool = False
    suggestions: Optional[List[Dict[str, Any]]] = None

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
    ontology_class_id: Optional[int] = None
    confidence: Optional[float] = None
    is_verified: Optional[bool] = None
    mapping_status: Optional[str] = None
    mapping_notes: Optional[str] = None
    auto_mapped: Optional[bool] = None


class EntityMapping(EntityMappingBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    ontology_class: Optional[OntologyClass] = None  # Joined data

    class Config:
        from_attributes = True


class RelationshipMappingBase(BaseModel):
    relationship_type: Optional[str] = Field(
        None, description="Legacy relationship type string"
    )
    ontology_property_id: Optional[int] = Field(None, description="Ontology property ID")
    confidence: Optional[float] = Field(0.8, ge=0, le=1)
    is_verified: bool = False
    mapping_status: str = Field(
        default="pending", description="Status: pending, mapped, rejected, needs_review"
    )
    mapping_notes: Optional[str] = None
    suggestions: Optional[List[Dict[str, Any]]] = None
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
    ontology_property_id: Optional[int] = None
    confidence: Optional[float] = None
    is_verified: Optional[bool] = None
    mapping_status: Optional[str] = None
    mapping_notes: Optional[str] = None
    auto_mapped: Optional[bool] = None


class RelationshipMapping(RelationshipMappingBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    ontology_property: Optional[OntologyProperty] = None  # Joined Ontology property

    class Config:
        from_attributes = True


# =============================================
# IMPORT AND ENRICHMENT SCHEMAS
# =============================================

class OntologyImportRequest(BaseModel):
    file_id: Optional[str] = None
    url: Optional[str] = None
    format: str = "rdf"  # rdf, owl, ttl
    target_domain_id: Optional[int] = None

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
    classes_imported: Optional[int] = None
    properties_imported: Optional[int] = None
    classes_updated: Optional[int] = None
    properties_updated: Optional[int] = None
    domain_associations_created: Optional[int] = None
    errors: Optional[List[str]] = None


class OntologyEnrichmentRequest(BaseModel):
    domain: Optional[str] = None
    enrichment_type: str = Field(..., description="Type of enrichment to perform")
    confidence_threshold: float = Field(0.8, ge=0, le=1)
    auto_apply: bool = False
    input_data: Optional[Dict[str, Any]] = None

    @field_validator("enrichment_type")
    def validate_enrichment_type(cls, v):
        valid_types = ["entity_mapping", "relationship_mapping", "ontology_extension", "full_enrichment"]
        if v not in valid_types:
            raise ValueError(f"Enrichment type must be one of {valid_types}")
        return v


class OntologyEnrichmentResponse(BaseModel):
    id: str
    enrichment_type: str
    domain: Optional[str]
    status: str
    statistics: Optional[Dict[str, Any]] = None
    auto_applied: bool
    confidence_threshold: float
    execution_time_ms: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# =============================================
# SUGGESTION SCHEMAS
# =============================================

class OntologyClassSuggestion(BaseModel):
    ontology_class: OntologyClass
    confidence: float = Field(..., ge=0, le=1)
    reason: str


class OntologyPropertySuggestion(BaseModel):
    ontology_property: OntologyProperty
    confidence: float = Field(..., ge=0, le=1)
    reason: str


class EntityMappingSuggestion(BaseModel):
    entity_type: str
    ontology_class: OntologyClass
    confidence: float = Field(..., ge=0, le=1)
    reason: str
    auto_mappable: bool = False


class RelationshipMappingSuggestion(BaseModel):
    relationship_type: str
    ontology_property: OntologyProperty
    confidence: float = Field(..., ge=0, le=1)
    reason: str
    auto_mappable: bool = False


class OntologyMappingSuggestionsRequest(BaseModel):
    domain: Optional[str] = None
    confidence_threshold: float = Field(0.8, ge=0, le=1)
    auto_apply: bool = False


class OntologyMappingSuggestionsResponse(BaseModel):
    id: str
    domain: Optional[str]
    entity_suggestions: List[EntityMappingSuggestion]
    relationship_suggestions: List[RelationshipMappingSuggestion]
    saved_entity_mappings: int
    saved_relationship_mappings: int
    auto_applied: bool
    confidence_threshold: float
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# =============================================
# VALIDATION SCHEMAS
# =============================================

class OntologyValidationRequest(BaseModel):
    ontology_property_id: int
    source_ontology_class_id: int
    target_ontology_class_id: int
    domain_id: Optional[int] = None


class OntologyValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


# =============================================
# BULK OPERATIONS SCHEMAS
# =============================================

class BulkEntityMappingRequest(BaseModel):
    mappings: List[EntityMappingCreate]
    domain_id: Optional[int] = None
    auto_apply: bool = False


class BulkRelationshipMappingRequest(BaseModel):
    mappings: List[RelationshipMappingCreate]
    domain_id: Optional[int] = None
    auto_apply: bool = False


class BulkMappingResponse(BaseModel):
    created: List[Dict[str, Any]] = Field(default_factory=list)
    updated: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    total_attempted: int
    successful: int
    failed: int


# =============================================
# ANALYTICS AND STATISTICS SCHEMAS
# =============================================

class OntologyStatistics(BaseModel):
    total_classes: int
    total_properties: int
    custom_classes: int
    custom_properties: int
    classes_by_domain: Dict[str, int]
    properties_by_domain: Dict[str, int]
    domains: List[str]


class MappingStatistics(BaseModel):
    entity_mappings: Dict[str, int]
    relationship_mappings: Dict[str, int]
    coverage_percentage: float
    verification_rate: float
    auto_mapping_rate: float


class OntologyAnalyticsResponse(BaseModel):
    ontology_stats: OntologyStatistics
    mapping_stats: MappingStatistics
    domain_coverage: Dict[str, Any]
    quality_metrics: Dict[str, float]
    generated_at: datetime


# =============================================
# SEARCH AND FILTER SCHEMAS
# =============================================

class OntologySearchFilters(BaseModel):
    query: Optional[str] = None
    domain_ids: Optional[List[int]] = None
    is_custom: Optional[bool] = None
    include_usage: bool = False


class MappingSearchFilters(BaseModel):
    query: Optional[str] = None
    mapping_status: Optional[str] = None
    is_verified: Optional[bool] = None
    auto_mapped: Optional[bool] = None
    confidence_range: Optional[tuple[float, float]] = None
    created_by: Optional[str] = None
