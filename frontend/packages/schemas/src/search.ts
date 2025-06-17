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

// AI Search Request Schema
export const AISearchRequestSchema = z.object({
  query: z.string().min(1, "Query is required").max(500, "Query too long"),
  entity_types: z.array(z.string()).optional(),
  max_candidates: z.number().min(1).max(200).default(50),
  similarity_threshold: z.number().min(0).max(1).default(0.3),
  top_k_entities: z.number().min(1).max(50).default(10),
  subgraph_radius: z.number().min(1).max(4).default(2),
  max_subgraph_nodes: z.number().min(10).max(500).default(100),
  damping_factor: z.number().min(0.1).max(0.99).default(0.85),
  max_iterations: z.number().min(5).max(100).default(20),
  generate_answer: z.boolean().default(true),
  llm_model: z.string().default("gpt-4o-mini")
});

// Quick AI Search Schema
export const QuickAISearchSchema = z.object({
  q: z.string().min(1, "Query is required").max(500, "Query too long"),
  entity_types: z.array(z.string()).optional(),
  max_results: z.number().min(1).max(50).default(10),
  generate_answer: z.boolean().default(true)
});

// Search Suggestions Schema
export const SearchSuggestionsSchema = z.object({
  q: z.string().min(1, "Query is required").max(100, "Query too long"),
  limit: z.number().min(1).max(20).default(5)
});

// PersonRank Request Schema
export const PersonRankRequestSchema = z.object({
  query: z.string().min(1, "Query is required"),
  entity_types: z.array(z.string()).optional(),
  max_candidates: z.number().min(1).max(200).default(50),
  similarity_threshold: z.number().min(0).max(1).default(0.3),
  damping_factor: z.number().min(0.1).max(0.99).default(0.85),
  max_iterations: z.number().min(5).max(100).default(20)
});

// Subgraph Request Schema
export const SubgraphRequestSchema = z.object({
  query: z.string().min(1, "Query is required"),
  entity_types: z.array(z.string()).optional(),
  max_candidates: z.number().min(1).max(200).default(50),
  similarity_threshold: z.number().min(0).max(1).default(0.3),
  top_k_entities: z.number().min(1).max(50).default(10),
  subgraph_radius: z.number().min(1).max(4).default(2),
  max_subgraph_nodes: z.number().min(10).max(500).default(100)
});

// Advanced Search Form Schema (for UI forms)
export const AdvancedSearchFormSchema = z.object({
  query: z.string().min(1, "Query is required").max(500, "Query too long"),
  search_type: z.enum(["exact", "fuzzy", "semantic", "hybrid", "ai_powered"]).default("ai_powered"),
  entity_types: z.array(z.string()).optional(),
  max_results: z.number().min(1).max(50).default(10),
  similarity_threshold: z.number().min(0).max(1).default(0.3),
  include_answer: z.boolean().default(true),
  include_subgraph: z.boolean().default(true),
  llm_model: z.string().default("gpt-4o-mini")
});

// Search Filter Schema (for complex filtering)
export const SearchFilterSchema = z.object({
  query: z.string().min(1),
  filters: z.record(z.any()).optional(),
  date_range: z.object({
    start: z.date().optional(),
    end: z.date().optional()
  }).optional(),
  score_range: z.object({
    min: z.number().min(0).max(1).optional(),
    max: z.number().min(0).max(1).optional()
  }).optional(),
  sort_by: z.enum(["relevance", "score", "date", "name"]).default("relevance"),
  sort_order: z.enum(["asc", "desc"]).default("desc")
});

// Export Schema Types
export type AISearchRequestType = z.infer<typeof AISearchRequestSchema>;
export type QuickAISearchType = z.infer<typeof QuickAISearchSchema>;
export type SearchSuggestionsType = z.infer<typeof SearchSuggestionsSchema>;
export type PersonRankRequestType = z.infer<typeof PersonRankRequestSchema>;
export type SubgraphRequestType = z.infer<typeof SubgraphRequestSchema>;
export type AdvancedSearchFormType = z.infer<typeof AdvancedSearchFormSchema>;
export type SearchFilterType = z.infer<typeof SearchFilterSchema>;
