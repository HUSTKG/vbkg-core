import { z } from "zod";

// Schema for searching entities
export const SearchEntitiesSchema = z.object({
  query: z.string().min(1), // Search query is required
  filters: z.record(z.string(), z.any()).optional(), // Optional filters as key-value pairs
  limit: z.number().min(1).max(1000).default(100), // Pagination limit
  offset: z.number().min(0).default(0), // Pagination offset
});

// Schema for finding similar entities
export const FindSimilarEntitiesSchema = z.object({
  entity_id: z.string().uuid(), // Entity ID must be a valid UUID
  similarity_threshold: z.number().min(0).max(1).optional(), // Optional similarity threshold
  top_k: z.number().min(1).max(100).default(10), // Maximum number of similar entities
});

// Schema for graph search
export const GraphSearchSchema = z.object({
  start_entity_id: z.string().uuid(), // Start entity ID must be a valid UUID
  relationship_path: z.array(z.string()).min(1), // Relationship path is required
  depth_limit: z.number().min(1).max(10).default(3), // Maximum depth for graph traversal
});

// Schema for generating embeddings
export const GenerateEmbeddingSchema = z.object({
  text: z.string().min(1), // Text to embed is required
  model: z.string().optional(), // Optional model to use for embedding
});

// Schema for creating/updating an entity embedding
export const CreateEntityEmbeddingSchema = z.object({
  entity_id: z.string().uuid(), // Entity ID must be a valid UUID
  model: z.string().optional(), // Optional model to use for embedding
});

// Schema for batch updating entity embeddings
export const UpdateEntityEmbeddingsBatchSchema = z.object({
  entity_type: z.string().optional(), // Optional entity type filter
  limit: z.number().min(1).max(1000).default(100), // Maximum number of entities to update
  model: z.string().optional(), // Optional model to use for embeddings
});
