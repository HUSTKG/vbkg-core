import { z } from "zod";
import { stringToJSONSchema } from "./common";

// Schema for creating an entity
export const CreateEntitySchema = z.object({
	entity_text: z.string().min(1), // Entity text is required
	entity_type: z.string().min(1), // Entity type is required
	properties: stringToJSONSchema, // Optional properties
	source_document_id: z.string().uuid().optional(), // Optional source document ID as UUID
	confidence: z.number().min(0).max(1).optional(), // Optional confidence score between 0 and 1
	is_verified: z.boolean().default(false), // Optional verification status, default is false
});

// Schema for retrieving an entity by ID
export const ReadEntityByIdSchema = z.object({
	entity_id: z.string().uuid(), // Entity ID must be a valid UUID
});

// Schema for retrieving relationships of an entity
export const ReadEntityRelationshipsSchema = z.object({
	entity_id: z.string().uuid(), // Entity ID must be a valid UUID
	direction: z.enum(["incoming", "outgoing"]).optional(), // Optional direction filter
});

// Schema for updating an entity
export const UpdateEntitySchema = z.object({
	entity_id: z.string().uuid(), // Entity ID must be a valid UUID
	properties: z.record(z.string(), z.any()).optional(), // Optional properties update
	fibo_class: z.string().optional(), // Optional FIBO class update
});

// Schema for deleting an entity
export const DeleteEntitySchema = z.object({
	entity_id: z.string().uuid(), // Entity ID must be a valid UUID
});

// Schema for searching entities
export const SearchKGEntitiesSchema = z.object({
	query: z.string().min(1), // Search query is required
	entity_type: z.string().optional(), // Optional entity type filter
	fibo_class: z.string().optional(), // Optional FIBO class filter
	limit: z.number().min(1).max(100).default(20), // Pagination limit
});

// Schema for creating a relationship
export const CreateRelationshipSchema = z.object({
	source_entity_id: z.string(), // Source entity ID must be a valid UUID
	target_entity_id: z.string(), // Target entity ID must be a valid UUID
	source_document_id: z.string().uuid().optional(), // Optional source document ID as UUID
	is_verified: z.boolean().default(false), // Optional verification status, default is false
	verification_notes: z.string().optional(), // Optional verification notes
	relationship_type: z.string().min(1), // Relationship type is required
	properties: stringToJSONSchema, 
	confidence: z.string().optional(), // Optional confidence score between 0 and 1
});

// Schema for executing a Cypher query
export const ExecuteQuerySchema = z.object({
	query: z.string().min(1), // Cypher query is required
	parameters: z.record(z.string(), z.any()).optional(), // Optional query parameters
});

// Schema for retrieving knowledge graph statistics
export const GetKnowledgeGraphStatsSchema = z.object({});

// Schema for creating or merging an entity
export const CreateOrMergeEntitySchema = z.object({
	text: z.string().min(1), // Entity text is required
	type: z.string().min(1), // Entity type is required
	properties: z.record(z.string(), z.any()).optional(), // Optional properties
	fibo_class: z.string().optional(), // Optional FIBO class
	source_document_id: z.string().uuid().optional(), // Optional source document ID as UUID
});
