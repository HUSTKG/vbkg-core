import {
  IGetEntityRequest,
  ISearchKGEntitiesRequest,
  IEntitySearchResponse,
  IGetEntityTypesResponse,
  IGetEntityNeighborsRequest,
  IGetEntityNeighborsResponse,
  IGetRelationshipRequest,
  IGetEntityRelationshipsRequest,
  IRelationshipSearchResponse,
  IGetSubgraphRequest,
  ISubgraphResponse,
  IFindPathsRequest,
  IPathResponse,
  IExecuteQueryRequest,
  IExecuteQueryResponse,
  IGetStatsResponse,
  IGetInvestmentInsightsRequest,
  IGetInvestmentInsightsResponse,
  IGlobalSearchRequest,
  IGlobalSearchResponse,
  Entity,
  Relationship,
  ISearchRelationshipsRequest,
} from "@vbkg/types";

import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

// Entity endpoints
const getEntity = async (input: IGetEntityRequest): Promise<Entity> => {
  return await api()
    .get<Entity>(API_ENDPOINTS.GET_KG_ENTITY(input.entity_id), {
      params: {
        include_relationships: input.include_relationships,
      },
    })
    .then((res) => res.data);
};

const searchEntities = async (
  input: ISearchKGEntitiesRequest,
): Promise<IEntitySearchResponse> => {
  return await api()
    .get<IEntitySearchResponse>(API_ENDPOINTS.SEARCH_KG_ENTITIES, {
      params: {
        query: input.query,
        entity_types: input.entity_types,
        limit: input.limit,
        offset: input.offset,
        min_confidence: input.min_confidence,
        verified_only: input.verified_only,
        semantic_search: input.semantic_search,
      },
    })
    .then((res) => res.data);
};

const searchRelationships = async (
  input: ISearchRelationshipsRequest,
): Promise<IRelationshipSearchResponse> => {
  return await api()
    .get<IRelationshipSearchResponse>(API_ENDPOINTS.SEARCH_KG_RELATIONSHIPS, {
      params: {
        query: input.query,
        relationship_types: input.relationship_types,
        limit: input.limit,
        offset: input.offset,
        min_confidence: input.min_confidence,
        verified_only: input.verified_only,
        semantic_search: input.semantic_search,
      },
    })
    .then((res) => res.data);
};

const getEntityTypes = async (): Promise<IGetEntityTypesResponse> => {
  return await api()
    .get<IGetEntityTypesResponse>(API_ENDPOINTS.GET_KG_ENTITY_TYPES)
    .then((res) => res.data);
};

const getEntityNeighbors = async (
  input: IGetEntityNeighborsRequest,
): Promise<IGetEntityNeighborsResponse> => {
  return await api()
    .get<IGetEntityNeighborsResponse>(
      API_ENDPOINTS.GET_KG_ENTITY_NEIGHBORS(input.entity_id),
      {
        params: {
          max_depth: input.max_depth,
          relationship_types: input.relationship_types,
          limit_per_level: input.limit_per_level,
        },
      },
    )
    .then((res) => res.data);
};

// Relationship endpoints
const getRelationship = async (
  input: IGetRelationshipRequest,
): Promise<Relationship> => {
  return await api()
    .get<Relationship>(API_ENDPOINTS.GET_KG_RELATIONSHIP(input.relationship_id))
    .then((res) => res.data);
};

const getEntityRelationships = async (
  input: IGetEntityRelationshipsRequest,
): Promise<IRelationshipSearchResponse> => {
  return await api()
    .get<IRelationshipSearchResponse>(
      API_ENDPOINTS.GET_KG_ENTITY_RELATIONSHIPS(input.entity_id),
      {
        params: {
          relationship_types: input.relationship_types,
          direction: input.direction,
          limit: input.limit,
          offset: input.offset,
        },
      },
    )
    .then((res) => res.data);
};

// Graph traversal endpoints
const getSubgraph = async (
  input: IGetSubgraphRequest,
): Promise<ISubgraphResponse> => {
  return await api()
    .get<ISubgraphResponse>(API_ENDPOINTS.GET_KG_SUBGRAPH(input.entity_id), {
      params: {
        radius: input.radius,
        max_nodes: input.max_nodes,
        relationship_types: input.relationship_types,
      },
    })
    .then((res) => res.data);
};

const findPaths = async (
  input: IFindPathsRequest,
): Promise<IPathResponse[]> => {
  return await api()
    .post<IPathResponse[]>(API_ENDPOINTS.FIND_KG_PATHS, input)
    .then((res) => res.data);
};

const executeQuery = async (
  input: IExecuteQueryRequest,
): Promise<IExecuteQueryResponse> => {
  return await api()
    .post<IExecuteQueryResponse>(API_ENDPOINTS.EXECUTE_KG_QUERY, input)
    .then((res) => res.data);
};

// Analytics & Statistics
const getStats = async (): Promise<IGetStatsResponse> => {
  return await api()
    .get<IGetStatsResponse>(API_ENDPOINTS.GET_KG_STATS)
    .then((res) => res.data);
};

const getInvestmentInsights = async (
  input: IGetInvestmentInsightsRequest,
): Promise<IGetInvestmentInsightsResponse> => {
  return await api()
    .get<IGetInvestmentInsightsResponse>(
      API_ENDPOINTS.GET_KG_INVESTMENT_INSIGHTS,
      {
        params: {
          entity_type: input.entity_type,
          limit: input.limit,
        },
      },
    )
    .then((res) => res.data);
};

// Search & Discovery
const globalSearch = async (
  input: IGlobalSearchRequest,
): Promise<IGlobalSearchResponse> => {
  return await api()
    .get<IGlobalSearchResponse>(API_ENDPOINTS.KG_GLOBAL_SEARCH, {
      params: {
        query: input.query,
        search_type: input.search_type,
        semantic: input.semantic,
        limit: input.limit,
      },
    })
    .then((res) => res.data);
};

export const KnowledgeGraphService = {
  // Entities
  getEntity,
  searchEntities,
  getEntityTypes,
  getEntityNeighbors,

  // Relationships
  searchRelationships,
  getRelationship,
  getEntityRelationships,

  // Graph Traversal
  getSubgraph,
  findPaths,
  executeQuery,

  // Analytics
  getStats,
  getInvestmentInsights,

  // Search
  globalSearch,
};
