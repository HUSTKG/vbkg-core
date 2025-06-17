import { z } from "zod";

// Mapping Status Schema
export const MappingStatusSchema = z.enum([
	"pending",
	"mapped",
	"rejected",
	"needs_review",
]);

export const ReadOntologyClassesSchema = z.object({
	domain: z.string().optional(),
	search: z.string().optional(),
	is_custom: z.boolean().optional(),
	limit: z.number().min(1).max(1000).default(100),
	skip: z.number().min(0).default(0),
});

export const ReadOntologyClassByIdSchema = z.object({
	class_id: z.number().int(),
});

export const CreateOntologyClassSchema = z.object({
	uri: z.string().url(),
	label: z.string().optional(),
	description: z.string().optional(),
	domain: z.string().optional(),
	properties: z.record(z.any()).optional(),
	parent_class_uri: z.string().optional(),
	is_custom: z.boolean().default(false),
});

export const UpdateOntologyClassSchema = z.object({
	label: z.string().optional(),
	description: z.string().optional(),
	properties: z.record(z.any()).optional(),
	parent_class_uri: z.string().optional(),
});

export const DeleteOntologyClassSchema = z.object({
	class_id: z.number().int(),
});

// Ontology Property Schemas (keeping existing with minor updates)
export const ReadOntologyPropertiesSchema = z.object({
	domain_class_id: z.number().int().optional(),
	property_type: z.enum(["object", "datatype"]).optional(),
	search: z.string().optional(),
	is_custom: z.boolean().optional(),
	limit: z.number().min(1).max(1000).default(100),
	skip: z.number().min(0).default(0),
});

export const ReadOntologyPropertyByIdSchema = z.object({
	property_id: z.number().int(),
});

export const CreateOntologyPropertySchema = z.object({
	uri: z.string().url(),
	label: z.string().optional(),
	description: z.string().optional(),
	property_type: z.enum(["object", "datatype"]),
	domain_class_uri: z.string().optional(),
	range_class_uri: z.string().optional(),
	is_custom: z.boolean().default(false),
});

export const UpdateOntologyPropertySchema = z.object({
	property_id: z.number().int(),
	label: z.string().optional(),
	description: z.string().optional(),
	property_type: z.enum(["object", "datatype"]).optional(),
	domain_class_uri: z.string().optional(),
	range_class_uri: z.string().optional(),
});

export const DeleteOntologyPropertySchema = z.object({
	property_id: z.number().int(),
});

// Updated Mapping Schemas
export const EntityMappingCreateSchema = z
	.object({
		entity_type: z.string().optional(), // Legacy field
		entity_type_id: z.number().int().optional(),
		ontology_class_uri: z.string().url(),
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
	ontology_class_uri: z.string().url().optional(),
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
		ontology_property_uri: z.string().url(),
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
	ontology_property_uri: z.string().url().optional(),
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
export const ImportOntologySchema = z.object({
	file_id: z.string().optional(),
	format: z.enum(["rdf", "owl", "ttl"]).default("rdf"),
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

export const SuggestOntologyClassesSchema = z
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

export const SuggestOntologyPropertiesSchema = z.object({
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
