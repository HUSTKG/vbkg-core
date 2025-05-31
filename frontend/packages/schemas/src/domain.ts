import { z } from "zod";

// =============================================
// DOMAIN SCHEMAS
// =============================================

// Schema for creating a domain
export const CreateDomainSchema = z.object({
  name: z.string().min(1).max(50),
  display_name: z.string().min(1).max(100),
  description: z.string().optional(),
  color: z.string().default("#6366F1"),
  icon: z.string().optional(),
  ontology_namespace: z.string().optional(),
  is_active: z.boolean().default(true),
  config: z.record(z.any()).default({}),
});

// Schema for updating a domain
export const UpdateDomainSchema = z.object({
  domain_id: z.number().int(),
  display_name: z.string().min(1).max(100).optional(),
  description: z.string().optional(),
  color: z.string().optional(),
  icon: z.string().optional(),
  ontology_namespace: z.string().optional(),
  is_active: z.boolean().optional(),
  config: z.record(z.any()).optional(),
});

// Schema for searching domains
export const SearchDomainsSchema = z.object({
  query: z.string().optional(),
  is_active: z.boolean().optional(),
  limit: z.number().min(1).max(200).default(50),
  offset: z.number().min(0).default(0),
});

// Schema for retrieving a domain by ID
export const ReadDomainByIdSchema = z.object({
  domain_id: z.number().int(),
  include_types: z.boolean().default(false),
});

// Schema for deleting a domain
export const DeleteDomainSchema = z.object({
  domain_id: z.number().int(),
});

// =============================================
// ENTITY TYPE SCHEMAS
// =============================================

// Schema for creating an entity type
export const CreateEntityTypeSchema = z.object({
  name: z.string().min(1).max(50),
  display_name: z.string().min(1).max(100),
  description: z.string().optional(),
  color: z.string().default("#3B82F6"),
  icon: z.string().optional(),
  extraction_pattern: z.string().optional(),
  validation_rules: z.record(z.any()).default({}),
  examples: z.array(z.string()).default([]),
  is_active: z.boolean().default(true),
  domain_ids: z.array(z.number().int()).default([]),
  primary_domain_id: z.number().int().optional(),
});

// Schema for updating an entity type
export const UpdateEntityTypeSchema = z.object({
  type_id: z.number().int(),
  display_name: z.string().min(1).max(100).optional(),
  description: z.string().optional(),
  color: z.string().optional(),
  icon: z.string().optional(),
  extraction_pattern: z.string().optional(),
  validation_rules: z.record(z.any()).optional(),
  examples: z.array(z.string()).optional(),
  is_active: z.boolean().optional(),
});

// Schema for searching entity types
export const SearchEntityTypesSchema = z.object({
  query: z.string().optional(),
  domain_ids: z.array(z.number().int()).optional(),
  is_active: z.boolean().optional(),
  include_usage: z.boolean().default(false),
  limit: z.number().min(1).max(200).default(50),
  offset: z.number().min(0).default(0),
});

// Schema for retrieving an entity type by ID
export const ReadEntityTypeByIdSchema = z.object({
  type_id: z.number().int(),
  include_domains: z.boolean().default(false),
  include_usage: z.boolean().default(false),
});

// Schema for deleting an entity type
export const DeleteEntityTypeSchema = z.object({
  type_id: z.number().int(),
});

// =============================================
// RELATIONSHIP TYPE SCHEMAS
// =============================================

// Schema for creating a relationship type
export const CreateRelationshipTypeSchema = z.object({
  name: z.string().min(1).max(50),
  display_name: z.string().min(1).max(100),
  description: z.string().optional(),
  source_entity_types: z.array(z.number().int()).default([]),
  target_entity_types: z.array(z.number().int()).default([]),
  is_bidirectional: z.boolean().default(false),
  color: z.string().default("#10B981"),
  extraction_pattern: z.string().optional(),
  validation_rules: z.record(z.any()).default({}),
  examples: z.array(z.string()).default([]),
  is_active: z.boolean().default(true),
  domain_ids: z.array(z.number().int()).default([]),
  primary_domain_id: z.number().int().optional(),
});

// Schema for updating a relationship type
export const UpdateRelationshipTypeSchema = z.object({
  type_id: z.number().int(),
  display_name: z.string().min(1).max(100).optional(),
  description: z.string().optional(),
  source_entity_types: z.array(z.number().int()).optional(),
  target_entity_types: z.array(z.number().int()).optional(),
  is_bidirectional: z.boolean().optional(),
  color: z.string().optional(),
  extraction_pattern: z.string().optional(),
  validation_rules: z.record(z.any()).optional(),
  examples: z.array(z.string()).optional(),
  is_active: z.boolean().optional(),
});

// Schema for searching relationship types
export const SearchRelationshipTypesSchema = z.object({
  query: z.string().optional(),
  domain_ids: z.array(z.number().int()).optional(),
  source_entity_type_id: z.number().int().optional(),
  target_entity_type_id: z.number().int().optional(),
  is_bidirectional: z.boolean().optional(),
  is_active: z.boolean().optional(),
  include_usage: z.boolean().default(false),
  limit: z.number().min(1).max(200).default(50),
  offset: z.number().min(0).default(0),
});

// Schema for retrieving a relationship type by ID
export const ReadRelationshipTypeByIdSchema = z.object({
  type_id: z.number().int(),
  include_domains: z.boolean().default(false),
  include_usage: z.boolean().default(false),
});

// Schema for deleting a relationship type
export const DeleteRelationshipTypeSchema = z.object({
  type_id: z.number().int(),
});

// =============================================
// DOMAIN MAPPING SCHEMAS
// =============================================

// Schema for adding entity type to domain
export const AddEntityTypeToDomainSchema = z.object({
  type_id: z.number().int(),
  domain_id: z.number().int(),
  is_primary: z.boolean().default(false),
  domain_specific_config: z.record(z.any()).default({}),
});

// Schema for removing entity type from domain
export const RemoveEntityTypeFromDomainSchema = z.object({
  type_id: z.number().int(),
  domain_id: z.number().int(),
});

// Schema for adding relationship type to domain
export const AddRelationshipTypeToDomainSchema = z.object({
  type_id: z.number().int(),
  domain_id: z.number().int(),
  is_primary: z.boolean().default(false),
  domain_specific_config: z.record(z.any()).default({}),
});

// Schema for removing relationship type from domain
export const RemoveRelationshipTypeFromDomainSchema = z.object({
  type_id: z.number().int(),
  domain_id: z.number().int(),
});

// =============================================
// VALIDATION SCHEMAS
// =============================================

// Schema for validating type constraints
export const ValidateTypeConstraintsSchema = z.object({
  entity_type_id: z.number().int().optional(),
  relationship_type_id: z.number().int().optional(),
  source_entity_type_id: z.number().int().optional(),
  target_entity_type_id: z.number().int().optional(),
});

// =============================================
// UTILITY SCHEMAS
// =============================================

// Schema for getting entity types by domain
export const GetEntityTypesByDomainSchema = z.object({
  domain_name: z.string().min(1),
  primary_only: z.boolean().default(false),
});

// Schema for getting relationship types by domain
export const GetRelationshipTypesByDomainSchema = z.object({
  domain_name: z.string().min(1),
  primary_only: z.boolean().default(false),
});

// Schema for getting compatible relationships
export const GetCompatibleRelationshipsSchema = z.object({
  source_entity_type_id: z.number().int(),
  target_entity_type_id: z.number().int().optional(),
  domain_ids: z.array(z.number().int()).optional(),
});

// =============================================
// BULK OPERATION SCHEMAS
// =============================================

// Schema for bulk creating entity types
export const BulkCreateEntityTypesSchema = z.object({
  entity_types: z.array(CreateEntityTypeSchema),
});

// Schema for bulk creating relationship types
export const BulkCreateRelationshipTypesSchema = z.object({
  relationship_types: z.array(CreateRelationshipTypeSchema),
});

// =============================================
// ANALYTICS SCHEMAS
// =============================================

// Schema for domain analytics overview (no parameters needed)
export const GetDomainAnalyticsOverviewSchema = z.object({});

// Schema for domain stats
export const GetDomainStatsSchema = z.object({
  domain_id: z.number().int(),
});
