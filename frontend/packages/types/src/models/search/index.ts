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


export enum SearchType {
  EXACT = "exact",
  FUZZY = "fuzzy",
  SEMANTIC = "semantic",
  HYBRID = "hybrid",
  AI_POWERED = "ai_powered"
}

// AI Search Request/Response Types
export interface AISearchRequest {
  query: string;
  entity_types?: string[];
  max_candidates?: number;
  similarity_threshold?: number;
  top_k_entities?: number;
  subgraph_radius?: number;
  max_subgraph_nodes?: number;
  damping_factor?: number;
  max_iterations?: number;
  generate_answer?: boolean;
  llm_model?: string;
}

export interface EntityRankResult {
  entity_id: string;
  entity_text: string;
  entity_type: string;
  similarity_score: number;
  personrank_score: number;
  final_score: number;
  properties: Record<string, any>;
}

export interface SubgraphContext {
  nodes: Array<{
    id: string;
    text: string;
    type: string;
    properties: Record<string, any>;
    is_top_entity: boolean;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    type: string;
    properties: Record<string, any>;
  }>;
  node_count: number;
  edge_count: number;
}

export interface AISearchResponse {
  query: string;
  answer: string;
  entities: EntityRankResult[];
  subgraph_context?: SubgraphContext;
  execution_time_ms: number;
  confidence_score: number;
  total_candidates: number;
}

export interface SearchSuggestionRequest {
  partial_query: string;
  limit?: number;
}

export interface SearchSuggestionResponse {
  suggestions: string[];
  query: string;
}
