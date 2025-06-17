import { ApiResponse } from "../models";
import {
  AISearchRequest,
  AISearchResponse,
  EmbeddingRequest,
  EmbeddingResponse,
  EntityRankResult,
  GraphSearchQuery,
  GraphSearchResult,
  SearchRequest,
  SearchResponse,
  SearchSuggestionRequest,
  SearchSuggestionResponse,
  SimilarEntityRequest,
  SubgraphContext,
} from "../models/search";

export interface ISearchEntitiesRequest extends SearchRequest {}
export interface ISearchEntitiesResponse extends ApiResponse<SearchResponse> {}

export interface IFindSimilarEntitiesRequest extends SimilarEntityRequest {}
export interface IFindSimilarEntitiesResponse extends ApiResponse<unknown[]> {}

export interface IGraphSearchRequest extends GraphSearchQuery {}
export interface IGraphSearchResponse extends ApiResponse<GraphSearchResult> {}

export interface IGenerateEmbeddingsRequest extends EmbeddingRequest {}
export interface IGenerateEmbeddingsResponse
  extends ApiResponse<EmbeddingResponse> {}

export interface ICreateEntityEmbeddingRequest {
  entity_id: string;
  model?: string;
}
export interface ICreateEntityEmbeddingResponse extends ApiResponse<unknown> {}

export interface IUpdateEntityEmbeddingsBatchRequest {
  entity_type?: string;
  limit?: number;
  model?: string;
}
export interface IUpdateEntityEmbeddingsBatchResponse
  extends ApiResponse<unknown> {}

export interface IAISearchRequest extends AISearchRequest {}
export interface IAISearchResponse extends ApiResponse<AISearchResponse> {}

export interface ISearchSuggestionsRequest extends SearchSuggestionRequest {}
export interface ISearchSuggestionsResponse extends ApiResponse<SearchSuggestionResponse> {}

export interface IQuickAISearchRequest {
  q: string;
  entity_types?: string[];
  max_results?: number;
  generate_answer?: boolean;
}

export interface IPersonRankRequest extends AISearchRequest {}
export interface IPersonRankResponse extends ApiResponse<{
  query: string;
  entities: EntityRankResult[];
  total_candidates: number;
  execution_time_ms: number;
}> {}

export interface ISearchSubgraphRequest extends AISearchRequest {}
export interface ISearchSubgraphResponse extends ApiResponse<{
  query: string;
  entities: EntityRankResult[];
  subgraph_context: SubgraphContext;
  execution_time_ms: number;
}> {}

export interface IExplainAISearchRequest extends AISearchRequest {}
export interface IExplainAISearchResponse extends ApiResponse<{
  query: string;
  algorithm_steps: string[];
  scoring_explanation: {
    similarity_score: string;
    personrank_score: string;
    final_score: string;
  };
  entities_with_scores: Array<{
    entity: string;
    type: string;
    similarity_score: number;
    personrank_score: number;
    final_score: number;
    explanation: string;
  }>;
  subgraph_stats: {
    nodes: number;
    edges: number;
    context_richness: string;
  };
  answer: string;
  confidence_explanation: string;
}> {}

// Search Analytics Types
export interface SearchTypeInfo {
  search_types: Array<{
    type: string;
    name: string;
    description: string;
    best_for: string;
  }>;
  recommendations: {
    simple_lookup: string;
    typo_tolerance: string;
    concept_search: string;
    general_search: string;
    complex_questions: string;
  };
}

export interface AISearchStats {
  ai_search_available: boolean;
  features: {
    semantic_search: boolean;
    personrank: boolean;
    subgraph_extraction: boolean;
    llm_generation: boolean;
    search_suggestions: boolean;
  };
  models: {
    embedding_model: string;
    llm_models: string[];
  };
  limits: {
    max_candidates: number;
    max_subgraph_nodes: number;
    max_results: number;
  };
}

export interface ISearchTypeInfoResponse extends ApiResponse<SearchTypeInfo> {}
export interface IAISearchStatsResponse extends ApiResponse<AISearchStats> {}
