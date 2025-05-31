import { z } from "zod";

// Mapping Status Schema
export const MappingStatusSchema = z.enum([
  "pending",
  "mapped",
  "rejected",
  "needs_review",
]);

export const ReadFiboClassesSchema = z.object({
  domain: z.string().optional(),
  search: z.string().optional(),
  is_custom: z.boolean().optional(),
  limit: z.number().min(1).max(1000).default(100),
  skip: z.number().min(0).default(0),
});

export const ReadFiboClassByIdSchema = z.object({
  class_id: z.number().int(),
});

export const CreateFiboClassSchema = z.object({
  uri: z.string().url(),
  label: z.string().optional(),
  description: z.string().optional(),
  domain: z.string().optional(),
  properties: z.record(z.any()).optional(),
  parent_class_uri: z.string().optional(),
  is_custom: z.boolean().default(false),
});

export const UpdateFiboClassSchema = z.object({
  class_id: z.number().int(),
  label: z.string().optional(),
  description: z.string().optional(),
  properties: z.record(z.any()).optional(),
  parent_class_uri: z.string().optional(),
});

export const DeleteFiboClassSchema = z.object({
  class_id: z.number().int(),
});

// FIBO Property Schemas (keeping existing with minor updates)
export const ReadFiboPropertiesSchema = z.object({
  domain_class_id: z.number().int().optional(),
  property_type: z.enum(["object", "datatype"]).optional(),
  search: z.string().optional(),
  is_custom: z.boolean().optional(),
  limit: z.number().min(1).max(1000).default(100),
  skip: z.number().min(0).default(0),
});

export const ReadFiboPropertyByIdSchema = z.object({
  property_id: z.number().int(),
});

export const CreateFiboPropertySchema = z.object({
  uri: z.string().url(),
  label: z.string().optional(),
  description: z.string().optional(),
  property_type: z.enum(["object", "datatype"]),
  domain_class_uri: z.string().optional(),
  range_class_uri: z.string().optional(),
  is_custom: z.boolean().default(false),
});

export const UpdateFiboPropertySchema = z.object({
  property_id: z.number().int(),
  label: z.string().optional(),
  description: z.string().optional(),
  property_type: z.enum(["object", "datatype"]).optional(),
  domain_class_uri: z.string().optional(),
  range_class_uri: z.string().optional(),
});

export const DeleteFiboPropertySchema = z.object({
  property_id: z.number().int(),
});

// Updated Mapping Schemas
export const EntityMappingCreateSchema = z
  .object({
    entity_type: z.string().optional(), // Legacy field
    entity_type_id: z.number().int().optional(),
    fibo_class_uri: z.string().url(),
    confidence: z.number().min(0).max(1).optional(),
    is_verified: z.boolean().default(false),
    mapping_status: MappingStatusSchema.default("pending"),
    mapping_notes: z.string().optional(),
    auto_mapped: z.boolean().default(false),
  })
  .refine((data) => data.entity_type || data.entity_type_id, {
    message: "Either entity_type or entity_type_id must be provided",
  });

export const EntityMappingUpdateSchema = z.object({
  entity_type: z.string().optional(),
  entity_type_id: z.number().int().optional(),
  fibo_class_uri: z.string().url().optional(),
  confidence: z.number().min(0).max(1).optional(),
  is_verified: z.boolean().optional(),
  mapping_status: MappingStatusSchema.optional(),
  mapping_notes: z.string().optional(),
  auto_mapped: z.boolean().optional(),
});

export const ReadEntityMappingsSchema = z.object({
  entity_type_id: z.number().int().optional(),
  mapping_status: MappingStatusSchema.optional(),
  is_verified: z.boolean().optional(),
  auto_mapped: z.boolean().optional(),
  search: z.string().optional(),
  limit: z.number().min(1).max(1000).default(100),
  skip: z.number().min(0).default(0),
});

export const RelationshipMappingCreateSchema = z
  .object({
    relationship_type: z.string().optional(), // Legacy field
    relationship_type_id: z.number().int().optional(),
    fibo_property_uri: z.string().url(),
    confidence: z.number().min(0).max(1).optional(),
    is_verified: z.boolean().default(false),
    mapping_status: MappingStatusSchema.default("pending"),
    mapping_notes: z.string().optional(),
    auto_mapped: z.boolean().default(false),
  })
  .refine((data) => data.relationship_type || data.relationship_type_id, {
    message:
      "Either relationship_type or relationship_type_id must be provided",
  });

export const RelationshipMappingUpdateSchema = z.object({
  relationship_type: z.string().optional(),
  relationship_type_id: z.number().int().optional(),
  fibo_property_uri: z.string().url().optional(),
  confidence: z.number().min(0).max(1).optional(),
  is_verified: z.boolean().optional(),
  mapping_status: MappingStatusSchema.optional(),
  mapping_notes: z.string().optional(),
  auto_mapped: z.boolean().optional(),
});

export const ReadRelationshipMappingsSchema = z.object({
  relationship_type_id: z.number().int().optional(),
  mapping_status: MappingStatusSchema.optional(),
  is_verified: z.boolean().optional(),
  auto_mapped: z.boolean().optional(),
  search: z.string().optional(),
  limit: z.number().min(1).max(1000).default(100),
  skip: z.number().min(0).default(0),
});

// Ontology Import Schema (keeping existing with updates)
export const ImportOntologySchema = z
  .object({
    file_id: z.string().optional(),
    url: z.string().url().optional(),
    format: z.enum(["rdf", "owl", "ttl"]).default("rdf"),
  })
  .refine((data) => data.file_id || data.url, {
    message: "Either file_id or url must be provided",
  });

// Suggestion Schemas
export const SuggestEntityTypesSchema = z.object({
  text: z.string().min(1),
  context: z.string().optional(),
  domain_id: z.number().int().optional(),
  max_suggestions: z.number().min(1).max(20).default(5),
});

export const SuggestRelationshipTypesSchema = z.object({
  text: z.string().min(1),
  source_entity_type_id: z.number().int().optional(),
  target_entity_type_id: z.number().int().optional(),
  context: z.string().optional(),
  domain_id: z.number().int().optional(),
  max_suggestions: z.number().min(1).max(20).default(5),
});

export const SuggestFiboClassesSchema = z
  .object({
    entity_text: z.string().optional(),
    entity_type: z.string().optional(),
    entity_type_id: z.number().int().optional(),
    context: z.string().optional(),
    max_suggestions: z.number().min(1).max(20).default(5),
  })
  .refine(
    (data) => data.entity_text || data.entity_type || data.entity_type_id,
    {
      message:
        "At least one of entity_text, entity_type, or entity_type_id must be provided",
    },
  );

export const SuggestFiboPropertiesSchema = z.object({
  relationship_type: z.string().optional(),
  relationship_type_id: z.number().int().optional(),
  source_entity_type: z.string().optional(),
  source_entity_type_id: z.number().int().optional(),
  target_entity_type: z.string().optional(),
  target_entity_type_id: z.number().int().optional(),
  context: z.string().optional(),
  max_suggestions: z.number().min(1).max(20).default(5),
});

// Bulk Operations Schemas
export const BulkEntityMappingCreateSchema = z.object({
  mappings: z.array(EntityMappingCreateSchema),
});

export const BulkRelationshipMappingCreateSchema = z.object({
  mappings: z.array(RelationshipMappingCreateSchema),
});

// Verification Schemas
export const VerifyEntityMappingSchema = z.object({
  entity_mapping_id: z.number().int(),
  verified: z.boolean(),
  notes: z.string().optional(),
});

export const VerifyRelationshipMappingSchema = z.object({
  relationship_mapping_id: z.number().int(),
  verified: z.boolean(),
  notes: z.string().optional(),
});
