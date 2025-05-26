from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# =============================================
# BASE MODELS
# =============================================

class DomainBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Domain name")
    display_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, description="Domain description")
    color: str = Field(default="#6366F1", description="UI color")
    icon: Optional[str] = Field(None, description="Icon identifier")
    ontology_namespace: Optional[str] = Field(None, description="Ontology namespace")
    is_active: bool = Field(default=True, description="Is domain active")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Domain configuration")


class EntityTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Entity type name")
    display_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, description="Entity type description") 
    color: str = Field(default="#3B82F6", description="UI color")
    icon: Optional[str] = Field(None, description="Icon identifier")
    extraction_pattern: Optional[str] = Field(None, description="Extraction pattern")
    validation_rules: Optional[Dict[str, Any]] = Field(default={}, description="Validation rules")
    examples: Optional[List[str]] = Field(default=[], description="Example entities")
    is_active: bool = Field(default=True, description="Is type active")


class RelationshipTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Relationship type name")
    display_name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: Optional[str] = Field(None, description="Relationship type description")
    source_entity_types: Optional[List[int]] = Field(default=[], description="Allowed source entity type IDs")
    target_entity_types: Optional[List[int]] = Field(default=[], description="Allowed target entity type IDs")
    is_bidirectional: bool = Field(default=False, description="Is relationship bidirectional")
    color: str = Field(default="#10B981", description="UI color")
    extraction_pattern: Optional[str] = Field(None, description="Extraction pattern")
    validation_rules: Optional[Dict[str, Any]] = Field(default={}, description="Validation rules")
    examples: Optional[List[str]] = Field(default=[], description="Example relationships")
    is_active: bool = Field(default=True, description="Is type active")


# =============================================
# RESPONSE MODELS
# =============================================

class DomainResponse(DomainBase):
    id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EntityTypeResponse(EntityTypeBase):
    id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    domains: Optional[List[Dict[str, Any]]] = Field(default=[], description="Associated domains")
    usage_count: Optional[int] = Field(default=0, description="Usage count in KG")
    
    class Config:
        from_attributes = True


class RelationshipTypeResponse(RelationshipTypeBase):
    id: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    domains: Optional[List[Dict[str, Any]]] = Field(default=[], description="Associated domains")
    usage_count: Optional[int] = Field(default=0, description="Usage count in KG")
    
    class Config:
        from_attributes = True


class DomainDetailResponse(DomainResponse):
    entity_types: List[EntityTypeResponse] = Field(default=[], description="Entity types in domain")
    relationship_types: List[RelationshipTypeResponse] = Field(default=[], description="Relationship types in domain")
    stats: Optional[Dict[str, Any]] = Field(default={}, description="Domain statistics")


# =============================================
# REQUEST MODELS
# =============================================

class CreateDomainRequest(DomainBase):
    pass


class UpdateDomainRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    ontology_namespace: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class CreateEntityTypeRequest(EntityTypeBase):
    domain_ids: Optional[List[int]] = Field(default=[], description="Domain IDs to associate with")
    primary_domain_id: Optional[int] = Field(None, description="Primary domain ID")


class UpdateEntityTypeRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    extraction_pattern: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    examples: Optional[List[str]] = None
    is_active: Optional[bool] = None


class CreateRelationshipTypeRequest(RelationshipTypeBase):
    domain_ids: Optional[List[int]] = Field(default=[], description="Domain IDs to associate with")
    primary_domain_id: Optional[int] = Field(None, description="Primary domain ID")


class UpdateRelationshipTypeRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    source_entity_types: Optional[List[int]] = None
    target_entity_types: Optional[List[int]] = None
    is_bidirectional: Optional[bool] = None
    color: Optional[str] = None
    extraction_pattern: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    examples: Optional[List[str]] = None
    is_active: Optional[bool] = None


class TypeDomainMappingRequest(BaseModel):
    type_id: int = Field(..., description="Entity/Relationship type ID")
    domain_id: int = Field(..., description="Domain ID")
    is_primary: bool = Field(default=False, description="Is primary domain for this type")
    domain_specific_config: Optional[Dict[str, Any]] = Field(default={}, description="Domain-specific config")


class BulkTypeMappingRequest(BaseModel):
    type_id: int = Field(..., description="Type ID")
    domain_mappings: List[Dict[str, Any]] = Field(..., description="Domain mappings")


# =============================================
# SEARCH & FILTER MODELS
# =============================================

class DomainSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    limit: int = Field(default=50, le=200, description="Results per page")
    offset: int = Field(default=0, ge=0, description="Results offset")


class EntityTypeSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    domain_ids: Optional[List[int]] = Field(None, description="Filter by domain IDs")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    include_usage: bool = Field(default=False, description="Include usage statistics")
    limit: int = Field(default=50, le=200, description="Results per page")
    offset: int = Field(default=0, ge=0, description="Results offset")


class RelationshipTypeSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    domain_ids: Optional[List[int]] = Field(None, description="Filter by domain IDs")
    source_entity_type_id: Optional[int] = Field(None, description="Filter by source entity type")
    target_entity_type_id: Optional[int] = Field(None, description="Filter by target entity type")
    is_bidirectional: Optional[bool] = Field(None, description="Filter by bidirectional")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    include_usage: bool = Field(default=False, description="Include usage statistics")
    limit: int = Field(default=50, le=200, description="Results per page")
    offset: int = Field(default=0, ge=0, description="Results offset")


# =============================================
# SEARCH RESPONSE MODELS
# =============================================

class DomainSearchResponse(BaseModel):
    domains: List[DomainResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class EntityTypeSearchResponse(BaseModel):
    entity_types: List[EntityTypeResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class RelationshipTypeSearchResponse(BaseModel):
    relationship_types: List[RelationshipTypeResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


# =============================================
# VALIDATION & MAPPING MODELS
# =============================================

class TypeValidationRequest(BaseModel):
    entity_type_id: Optional[int] = None
    relationship_type_id: Optional[int] = None
    source_entity_type_id: Optional[int] = None
    target_entity_type_id: Optional[int] = None


class TypeValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default=[])
    warnings: List[str] = Field(default=[])


class DomainStatsResponse(BaseModel):
    domain_id: int
    domain_name: str
    entity_types_count: int
    relationship_types_count: int
    entities_count: int
    relationships_count: int
    last_updated: datetime


# =============================================
# FIBO MAPPING MODELS
# =============================================

class FiboMappingRequest(BaseModel):
    entity_type_id: Optional[int] = None
    relationship_type_id: Optional[int] = None
    fibo_class_id: Optional[int] = None
    fibo_property_id: Optional[int] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Mapping confidence")
    mapping_notes: Optional[str] = Field(None, description="Mapping notes")
    is_verified: bool = Field(default=False, description="Is mapping verified")


class FiboMappingResponse(BaseModel):
    id: int
    entity_type_id: Optional[int] = None
    relationship_type_id: Optional[int] = None
    fibo_class_id: Optional[int] = None
    fibo_property_id: Optional[int] = None
    fibo_class: Optional[Dict[str, Any]] = None
    fibo_property: Optional[Dict[str, Any]] = None
    confidence: float
    mapping_status: str
    mapping_notes: Optional[str] = None
    is_verified: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# =============================================
# EXTRACTION TEMPLATE MODELS
# =============================================

class ExtractionTemplateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    domain: str = Field(..., description="Target domain")
    entity_types: List[int] = Field(..., description="Entity type IDs to extract")
    relationship_types: List[int] = Field(..., description="Relationship type IDs to extract")
    prompt_template: str = Field(..., description="AI prompt template")
    extraction_config: Optional[Dict[str, Any]] = Field(default={}, description="Extraction configuration")
    is_active: bool = Field(default=True, description="Is template active")


class ExtractionTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    domain: str
    entity_types: List[Dict[str, Any]] = Field(default=[])
    relationship_types: List[Dict[str, Any]] = Field(default=[])
    prompt_template: str
    extraction_config: Dict[str, Any]
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
