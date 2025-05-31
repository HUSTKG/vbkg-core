// =============================================
// BASE TYPES
// =============================================

export type DomainBase = {
  name: string;
  display_name: string;
  description?: string;
  color?: string;
  icon?: string;
  ontology_namespace?: string;
  is_active?: boolean;
  config?: Record<string, any>;
};

export type EntityTypeBase = {
  name: string;
  display_name: string;
  description?: string;
  color?: string;
  icon?: string;
  extraction_pattern?: string;
  validation_rules?: Record<string, any>;
  examples?: string[];
  is_active?: boolean;
};

export type RelationshipTypeBase = {
  name: string;
  display_name: string;
  description?: string;
  source_entity_types?: number[];
  target_entity_types?: number[];
  is_bidirectional?: boolean;
  color?: string;
  extraction_pattern?: string;
  validation_rules?: Record<string, any>;
  examples?: string[];
  is_active?: boolean;
};

// =============================================
// RESPONSE TYPES
// =============================================

export type Domain = DomainBase & {
  id: number;
  created_by?: string;
  created_at: Date;
  updated_at: Date;
};

export type EntityType = EntityTypeBase & {
  id: number;
  created_by?: string;
  created_at: Date;
  updated_at: Date;
  domains?: Record<string, any>[];
  usage_count?: number;
};

export type RelationshipType = RelationshipTypeBase & {
  id: number;
  created_by?: string;
  created_at: Date;
  updated_at: Date;
  domains?: Record<string, any>[];
  usage_count?: number;
};

export type DomainDetail = Domain & {
  entity_types: EntityType[];
  relationship_types: RelationshipType[];
  stats?: Record<string, any>;
};

// =============================================
// REQUEST TYPES
// =============================================

export type CreateDomainRequest = DomainBase;

export type UpdateDomainRequest = {
  display_name?: string;
  description?: string;
  color?: string;
  icon?: string;
  ontology_namespace?: string;
  is_active?: boolean;
  config?: Record<string, any>;
};

export type CreateEntityTypeRequest = EntityTypeBase & {
  domain_ids?: number[];
  primary_domain_id?: number;
};

export type UpdateEntityTypeRequest = {
  display_name?: string;
  description?: string;
  color?: string;
  icon?: string;
  extraction_pattern?: string;
  validation_rules?: Record<string, any>;
  examples?: string[];
  is_active?: boolean;
};

export type CreateRelationshipTypeRequest = RelationshipTypeBase & {
  domain_ids?: number[];
  primary_domain_id?: number;
};

export type UpdateRelationshipTypeRequest = {
  display_name?: string;
  description?: string;
  source_entity_types?: number[];
  target_entity_types?: number[];
  is_bidirectional?: boolean;
  color?: string;
  extraction_pattern?: string;
  validation_rules?: Record<string, any>;
  examples?: string[];
  is_active?: boolean;
};

export type TypeDomainMappingRequest = {
  type_id: number;
  domain_id: number;
  is_primary?: boolean;
  domain_specific_config?: Record<string, any>;
};

export type BulkTypeMappingRequest = {
  type_id: number;
  domain_mappings: Record<string, any>[];
};

// =============================================
// SEARCH & FILTER TYPES
// =============================================

export type DomainSearchRequest = {
  query?: string;
  is_active?: boolean;
  limit?: number;
  offset?: number;
};

export type DomainSearchResponse = {
  domains: Domain[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
};

export type EntityTypeSearchRequest = {
  query?: string;
  domain_ids?: number[];
  is_active?: boolean;
  include_usage?: boolean;
  limit?: number;
  offset?: number;
};

export type EntityTypeSearchResponse = {
  entity_types: EntityType[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
};

export type RelationshipTypeSearchRequest = {
  query?: string;
  domain_ids?: number[];
  source_entity_type_id?: number;
  target_entity_type_id?: number;
  is_bidirectional?: boolean;
  is_active?: boolean;
  include_usage?: boolean;
  limit?: number;
  offset?: number;
};

export type RelationshipTypeSearchResponse = {
  relationship_types: RelationshipType[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
};

// =============================================
// VALIDATION & MAPPING TYPES
// =============================================

export type TypeValidationRequest = {
  entity_type_id?: number;
  relationship_type_id?: number;
  source_entity_type_id?: number;
  target_entity_type_id?: number;
};

export type TypeValidationResponse = {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
};

export type DomainStats = {
  domain_id: number;
  domain_name: string;
  entity_types_count: number;
  relationship_types_count: number;
  entities_count: number;
  relationships_count: number;
  last_updated: Date;
};

// =============================================
// FIBO MAPPING TYPES
// =============================================

export type FiboMappingRequest = {
  entity_type_id?: number;
  relationship_type_id?: number;
  fibo_class_id?: number;
  fibo_property_id?: number;
  confidence?: number;
  mapping_notes?: string;
  is_verified?: boolean;
};

export type FiboMapping = {
  id: number;
  entity_type_id?: number;
  relationship_type_id?: number;
  fibo_class_id?: number;
  fibo_property_id?: number;
  fibo_class?: Record<string, any>;
  fibo_property?: Record<string, any>;
  confidence: number;
  mapping_status: string;
  mapping_notes?: string;
  is_verified: boolean;
  created_by?: string;
  created_at: Date;
  updated_at: Date;
};

// =============================================
// EXTRACTION TEMPLATE TYPES
// =============================================

export type ExtractionTemplateRequest = {
  name: string;
  description?: string;
  domain: string;
  entity_types: number[];
  relationship_types: number[];
  prompt_template: string;
  extraction_config?: Record<string, any>;
  is_active?: boolean;
};

export type ExtractionTemplate = {
  id: string;
  name: string;
  description?: string;
  domain: string;
  entity_types: Record<string, any>[];
  relationship_types: Record<string, any>[];
  prompt_template: string;
  extraction_config: Record<string, any>;
  is_active: boolean;
  created_by?: string;
  created_at: Date;
  updated_at: Date;
};

// =============================================
// UTILITY TYPES
// =============================================

export type CompatibleRelationshipsResponse = {
  source_entity_type_id: number;
  target_entity_type_id?: number;
  compatible_relationships: RelationshipType[];
};

export type DomainAnalyticsOverview = {
  overview: {
    total_domains: number;
    total_entity_types: number;
    total_relationship_types: number;
    active_domains: number;
  };
  domain_stats: (DomainStats & {
    domain_name: string;
    display_name: string;
  })[];
  generated_at: string;
};

// =============================================
// BULK OPERATION TYPES
// =============================================

export type BulkCreateEntityTypesRequest = CreateEntityTypeRequest[];

export type BulkCreateEntityTypesResponse = {
  created: EntityType[];
  errors: Array<{
    index: number;
    name: string;
    error: string;
  }>;
  total_attempted: number;
  successful: number;
  failed: number;
};

export type BulkCreateRelationshipTypesRequest =
  CreateRelationshipTypeRequest[];

export type BulkCreateRelationshipTypesResponse = {
  created: RelationshipType[];
  errors: Array<{
    index: number;
    name: string;
    error: string;
  }>;
  total_attempted: number;
  successful: number;
  failed: number;
};
