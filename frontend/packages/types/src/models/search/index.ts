export enum SearchType {
  EXACT = "exact",
  FUZZY = "fuzzy",
  SEMANTIC = "semantic",
  HYBRID = "hybrid",
}

export interface SearchFilter {
  field: string;
  operator: string; // eq, gt, lt, gte, lte, contains, in
}

export interface RelationshipFilter {
  relationship_type?: string;
  target_type?: string;
  target_property?: string;
  target_value?: any;
  direction: "outgoing" | "incoming" | "both";
}

export enum SortOrder {
  ASC = "asc",
  DESC = "desc",
}

export interface SearchSort {
  field: string;
  order?: SortOrder;
}

export interface SearchRequest {
  query: string;
  entity_types?: string[];
  search_type?: SearchType;
  filters?: SearchFilter[];
  relationship_filters?: RelationshipFilter[];
  sort?: SearchSort[];
  limit?: number; // default: 10, min: 1, max: 100
  offset?: number; // default: 0, min: 0
  include_relationships?: boolean;
  include_similar_entities?: boolean;
  similarity_threshold?: number;
  embedding_model?: string;
  return_fields?: string[]; // If None, return all fields
}

export interface EntitySearchResult {
  id: string;
  text: string;
  type: string;
  properties: Record<string, any>;
  fibo_class?: string;
  score: number;
  relationships?: Record<string, any>[];
  similar_entities?: Record<string, any>[];
}

export interface SearchResponse {
  results: EntitySearchResult[];
  total: number;
  query: string;
  search_type: SearchType;
  execution_time_ms: number;
}

export interface EmbeddingRequest {
  text: string;
  model?: string;
}

export interface EmbeddingResponse {
  embedding: number[];
  model: string;
  text: string;
  vector_size: number;
}

export interface SimilarEntityRequest {
  entity_id: string;
  limit?: number; // default: 10, min: 1, max: 100
  similarity_threshold?: number; // default: 0.7, min: 0, max: 1
  entity_types?: string[];
}

export interface GraphSearchQuery {
  start_entity_id?: string;
  start_entity_type?: string;
  start_entity_text?: string;
  relationship_path: string[]; // e.g. ["HAS_ACCOUNT", "BELONGS_TO"]
  end_entity_type?: string;
  max_depth?: number; // default: 3, min: 1, max: 5
  limit?: number; // default: 20, min: 1, max: 100
}

export interface GraphSearchResult {
  paths: Record<string, any>[];
  total: number;
  execution_time_ms: number;
}

