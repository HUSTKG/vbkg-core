import { ApiResponse } from "../models";
import {
  EmbeddingRequest,
  EmbeddingResponse,
  GraphSearchQuery,
  GraphSearchResult,
  SearchRequest,
  SearchResponse,
  SimilarEntityRequest,
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
