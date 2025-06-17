from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# =============================================
# DOMAIN SCHEMAS
# =============================================

class DomainBase(BaseModel):
    name: str = Field(..., description="Domain unique name")
    display_name: str = Field(..., description="Display name for the domain")
    description: Optional[str] = Field(None, description="Domain description")
    ontology_namespace: Optional[str] = Field(None, description="Ontology namespace URI")
    ontology_prefix: Optional[str] = Field(None, description="Ontology prefix")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Domain configuration")
    is_active: bool = True


class CreateDomainRequest(DomainBase):
    ontology_class_ids: Optional[List[int]] = Field(default_factory=list, description="Ontology classes to associate")
    ontology_property_ids: Optional[List[int]] = Field(default_factory=list, description="Ontology properties to associate")
    primary_ontology_class_id: Optional[int] = Field(None, description="Primary ontology class")
    primary_ontology_property_id: Optional[int] = Field(None, description="Primary ontology property")


class UpdateDomainRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    ontology_namespace: Optional[str] = None
    ontology_prefix: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DomainResponse(DomainBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DomainDetailResponse(DomainResponse):
    ontology_classes: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    ontology_properties: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    stats: Optional[Dict[str, Any]] = None


class DomainStatsResponse(BaseModel):
    domain_id: int
    ontology_classes_count: int
    ontology_properties_count: int
    entities_count: int = 0
    relationships_count: int = 0
    last_updated: datetime


# =============================================
# ONTOLOGY CLASS ASSOCIATION SCHEMAS
# =============================================

class OntologyClassDomainMappingRequest(BaseModel):
    domain_id: int
    is_primary: bool = False
    domain_specific_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OntologyClassResponse(BaseModel):
    id: int
    uri: str
    label: Optional[str]
    description: Optional[str]
    domain: Optional[str]
    parent_class_id: Optional[int]
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_custom: bool = False
    created_at: datetime
    updated_at: datetime
    domains: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    usage_count: Optional[int] = 0

    class Config:
        from_attributes = True


# =============================================
# ONTOLOGY PROPERTY ASSOCIATION SCHEMAS
# =============================================

class OntologyPropertyDomainMappingRequest(BaseModel):
    domain_id: int
    is_primary: bool = False
    domain_specific_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OntologyPropertyResponse(BaseModel):
    id: int
    uri: str
    label: Optional[str]
    description: Optional[str]
    domain_class_id: Optional[int]
    range_class_id: Optional[int]
    property_type: Optional[str]
    domain: Optional[str]
    is_custom: bool = False
    created_at: datetime
    updated_at: datetime
    domains: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    usage_count: Optional[int] = 0

    class Config:
        from_attributes = True


# =============================================
# VALIDATION SCHEMAS
# =============================================

class OntologyValidationRequest(BaseModel):
    ontology_property_id: int
    source_ontology_class_id: int
    target_ontology_class_id: int


class OntologyValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# =============================================
# SUGGESTION SCHEMAS
# =============================================

class OntologyClassSuggestion(BaseModel):
    ontology_class: Dict[str, Any]
    confidence: float = Field(..., ge=0, le=1)
    reason: str


class OntologyPropertySuggestion(BaseModel):
    ontology_property: Dict[str, Any]
    confidence: float = Field(..., ge=0, le=1)
    reason: str


# =============================================
# MAPPING SCHEMAS (Updated to work with ontology)
# =============================================

class EntityMappingBase(BaseModel):
    entity_type: Optional[str] = Field(None, description="Legacy entity type string")
    entity_type_id: Optional[int] = Field(None, description="Entity type ID reference")
    ontology_class_id: int = Field(..., description="Ontology class ID")
    confidence: Optional[float] = Field(0.8, ge=0, le=1)
    is_verified: bool = False
    mapping_status: str = Field(
        default="pending", description="Status: pending, mapped, rejected, needs_review"
    )
    mapping_notes: Optional[str] = None
    auto_mapped: bool = False


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


class EntityMappingResponse(EntityMappingBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    ontology_class: Optional[OntologyClassResponse] = None

    class Config:
        from_attributes = True


class RelationshipMappingBase(BaseModel):
    relationship_type: Optional[str] = Field(None, description="Legacy relationship type string")
    relationship_type_id: Optional[int] = Field(None, description="Relationship type ID reference")
    ontology_property_id: int = Field(..., description="Ontology property ID")
    confidence: Optional[float] = Field(0.8, ge=0, le=1)
    is_verified: bool = False
    mapping_status: str = Field(
        default="pending", description="Status: pending, mapped, rejected, needs_review"
    )
    mapping_notes: Optional[str] = None
    auto_mapped: bool = False


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


class RelationshipMappingResponse(RelationshipMappingBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    ontology_property: Optional[OntologyPropertyResponse] = None

    class Config:
        from_attributes = True


# =============================================
# BULK OPERATION SCHEMAS
# =============================================

class BulkOntologyClassAssociationRequest(BaseModel):
    ontology_classes: List[int]
    domain_id: int
    is_primary: bool = False
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BulkOntologyPropertyAssociationRequest(BaseModel):
    ontology_properties: List[int]
    domain_id: int
    is_primary: bool = False
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BulkOperationResponse(BaseModel):
    created: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    total_attempted: int
    successful: int
    failed: int


# =============================================
# MAPPING SUGGESTIONS SCHEMAS
# =============================================

class OntologyMappingSuggestionsRequest(BaseModel):
    domain: Optional[str] = None
    confidence_threshold: float = Field(0.8, ge=0, le=1)
    auto_apply: bool = False


class OntologyMappingSuggestionsResponse(BaseModel):
    id: str
    domain: Optional[str]
    entity_suggestions: List[Dict[str, Any]]
    relationship_suggestions: List[Dict[str, Any]]
    saved_entity_mappings: int
    saved_relationship_mappings: int
    confidence_threshold: float
    status: str
    created_at: datetime
    processed_at: Optional[datetime]


# =============================================
# SEARCH AND FILTER SCHEMAS
# =============================================

class DomainSearchFilters(BaseModel):
    query: Optional[str] = None
    is_active: Optional[bool] = None
    has_ontology_classes: Optional[bool] = None
    has_ontology_properties: Optional[bool] = None
    ontology_namespace: Optional[str] = None


class OntologyClassSearchFilters(BaseModel):
    query: Optional[str] = None
    domain_ids: Optional[List[int]] = None
    is_mapped: Optional[bool] = None
    is_custom: Optional[bool] = None
    include_usage: bool = False
    parent_class_id: Optional[int] = None


class OntologyPropertySearchFilters(BaseModel):
    query: Optional[str] = None
    domain_ids: Optional[List[int]] = None
    is_mapped: Optional[bool] = None
    is_custom: Optional[bool] = None
    property_type: Optional[str] = None
    domain_class_id: Optional[int] = None
    range_class_id: Optional[int] = None
    include_usage: bool = False


class EntityMappingSearchFilters(BaseModel):
    query: Optional[str] = None
    ontology_class_id: Optional[int] = None
    mapping_status: Optional[str] = None
    is_verified: Optional[bool] = None
    auto_mapped: Optional[bool] = None
    domain_id: Optional[int] = None


class RelationshipMappingSearchFilters(BaseModel):
    query: Optional[str] = None
    ontology_property_id: Optional[int] = None
    mapping_status: Optional[str] = None
    is_verified: Optional[bool] = None
    auto_mapped: Optional[bool] = None
    domain_id: Optional[int] = None


# =============================================
# ANALYTICS SCHEMAS
# =============================================

class DomainAnalyticsOverview(BaseModel):
    overview: Dict[str, Any]
    domain_stats: List[Dict[str, Any]]
    ontology_coverage: Dict[str, Any]
    mapping_statistics: Dict[str, Any]
    generated_at: datetime


class OntologyMappingAnalytics(BaseModel):
    total_mappings: int
    verified_mappings: int
    pending_mappings: int
    auto_mapped_count: int
    mapping_coverage: float
    confidence_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
