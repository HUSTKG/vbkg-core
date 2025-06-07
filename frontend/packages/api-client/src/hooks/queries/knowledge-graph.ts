import {
  Entity,
  IEntitySearchResponse,
  IGetEntityNeighborsRequest,
  IGetEntityNeighborsResponse,
  IGetEntityRelationshipsRequest,
  IGetEntityRequest,
  IGetEntityTypesResponse,
  IGetInvestmentInsightsRequest,
  IGetInvestmentInsightsResponse,
  IGetRelationshipRequest,
  IGetStatsResponse,
  IGetSubgraphRequest,
  IGlobalSearchRequest,
  IGlobalSearchResponse,
  IRelationshipSearchResponse,
  ISearchKGEntitiesRequest,
  ISearchRelationshipsRequest,
  ISubgraphResponse,
  Relationship,
  IExecuteQueryRequest,
  IExecuteQueryResponse,
  IGetKnowledgeGraphStatsRequest,
  IGetKnowledgeGraphStatsResponse,
  IReadEntityRelationshipsRequest,
  IReadEntityRelationshipsResponse,
  IReadEntityRequest,
  IReadEntityResponse,
} from "@vbkg/types";

import { UseQueryOptions, useQuery } from "@tanstack/react-query";
import { QueryKeys } from "../../config/queryKeys";
import { KnowledgeGraphService } from "../../services/knowledge-graph";

// Entity queries
export const useKGEntity = (
  input: IGetEntityRequest,
  options?: UseQueryOptions<Entity, Error>,
) => {
  return useQuery<Entity, Error>({
    queryKey: QueryKeys.knowledgeGraph.entity(
      input.entity_id,
      input.include_relationships,
    ),
    queryFn: () => KnowledgeGraphService.getEntity(input),
    enabled: !!input.entity_id,
    ...options,
  });
};

export const useKGEntitiesSearch = (
  input: ISearchKGEntitiesRequest,
  options?: UseQueryOptions<IEntitySearchResponse, Error>,
) => {
  return useQuery<IEntitySearchResponse, Error>({
    queryKey: QueryKeys.knowledgeGraph.entitiesSearch(input),
    queryFn: () => KnowledgeGraphService.searchEntities(input),
    ...options,
  });
};

export const useKGRelationshipsSearch = (
  input: ISearchRelationshipsRequest,
  options?: UseQueryOptions<IRelationshipSearchResponse, Error>,
) => {
  return useQuery<IRelationshipSearchResponse, Error>({
    queryKey: QueryKeys.knowledgeGraph.relationshipsSearch(input),
    queryFn: () => KnowledgeGraphService.searchRelationships(input),
    ...options,
  });
};

export const useKGEntityTypes = (
  options?: UseQueryOptions<IGetEntityTypesResponse, Error>,
) => {
  return useQuery<IGetEntityTypesResponse, Error>({
    queryKey: QueryKeys.knowledgeGraph.entityTypes(),
    queryFn: () => KnowledgeGraphService.getEntityTypes(),
    ...options,
  });
};

export const useKGEntityNeighbors = (
  input: IGetEntityNeighborsRequest,
  options?: UseQueryOptions<IGetEntityNeighborsResponse, Error>,
) => {
  return useQuery<IGetEntityNeighborsResponse, Error>({
    queryKey: QueryKeys.knowledgeGraph.entityNeighbors(
      input.entity_id,
      input.max_depth,
      input.relationship_types,
      input.limit_per_level,
    ),
    queryFn: () => KnowledgeGraphService.getEntityNeighbors(input),
    enabled: !!input.entity_id,
    ...options,
  });
};

// Relationship queries
export const useKGRelationship = (
  input: IGetRelationshipRequest,
  options?: UseQueryOptions<Relationship, Error>,
) => {
  return useQuery<Relationship, Error>({
    queryKey: QueryKeys.knowledgeGraph.relationship(input.relationship_id),
    queryFn: () => KnowledgeGraphService.getRelationship(input),
    enabled: !!input.relationship_id,
    ...options,
  });
};

export const useKGEntityRelationships = (
  input: IGetEntityRelationshipsRequest,
  options?: UseQueryOptions<IRelationshipSearchResponse, Error>,
) => {
  return useQuery<IRelationshipSearchResponse, Error>({
    queryKey: QueryKeys.knowledgeGraph.entityRelationships(
      input.entity_id,
      input.relationship_types,
      input.direction,
      input.limit,
      input.offset,
    ),
    queryFn: () => KnowledgeGraphService.getEntityRelationships(input),
    enabled: !!input.entity_id,
    ...options,
  });
};

// Graph traversal queries
export const useKGSubgraph = (
  input: IGetSubgraphRequest,
  options?: UseQueryOptions<ISubgraphResponse, Error>,
) => {
  return useQuery<ISubgraphResponse, Error>({
    queryKey: QueryKeys.knowledgeGraph.subgraph(
      input.entity_id,
      input.radius,
      input.max_nodes,
      input.relationship_types,
    ),
    queryFn: () => KnowledgeGraphService.getSubgraph(input),
    enabled: !!input.entity_id,
    ...options,
  });
};

// Analytics queries
export const useKGStats = (
  options?: UseQueryOptions<IGetStatsResponse, Error>,
) => {
  return useQuery<IGetStatsResponse, Error>({
    queryKey: QueryKeys.knowledgeGraph.stats(),
    queryFn: () => KnowledgeGraphService.getStats(),
    ...options,
  });
};

export const useKGInvestmentInsights = (
  input: IGetInvestmentInsightsRequest,
  options?: UseQueryOptions<IGetInvestmentInsightsResponse, Error>,
) => {
  return useQuery<IGetInvestmentInsightsResponse, Error>({
    queryKey: QueryKeys.knowledgeGraph.investmentInsights(
      input.entity_type!,
      input.limit,
    ),
    queryFn: () => KnowledgeGraphService.getInvestmentInsights(input),
    ...options,
  });
};

// Search queries
export const useKGGlobalSearch = (
  input: IGlobalSearchRequest,
  options?: UseQueryOptions<IGlobalSearchResponse, Error>,
) => {
  return useQuery<IGlobalSearchResponse, Error>({
    queryKey: QueryKeys.knowledgeGraph.globalSearch(input),
    queryFn: () => KnowledgeGraphService.globalSearch(input),
    enabled: !!input.query && input.query.length >= 2,
    ...options,
  });
};


// Read single entity
export const useEntity = (
  input: IReadEntityRequest,
  options?: UseQueryOptions<IReadEntityResponse, Error>,
) => {
  return useQuery<IReadEntityResponse, Error>({
    queryKey: ["entity", input.id],
    queryFn: () => KnowledgeGraphService.readEntity(input),
    ...options,
  });
};

// Read entity relationships
export const useEntityRelationships = (
  input: IReadEntityRelationshipsRequest,
  options?: UseQueryOptions<IReadEntityRelationshipsResponse, Error>,
) => {
  return useQuery<IReadEntityRelationshipsResponse, Error>({
    queryKey: ["entityRelationships", input.id],
    queryFn: () => KnowledgeGraphService.readEntityRelationships(input),
    ...options,
  });
};

// Execute query
export const useExecuteQuery = (
  input: IExecuteQueryRequest,
  options?: UseQueryOptions<IExecuteQueryResponse, Error>,
) => {
  return useQuery<IExecuteQueryResponse, Error>({
    queryKey: ["executeQuery", input],
    queryFn: () => KnowledgeGraphService.executeQuery(input),
    ...options,
  });
};

// Get knowledge graph stats
export const useKnowledgeGraphStats = (
  input: IGetKnowledgeGraphStatsRequest,
  options?: UseQueryOptions<IGetKnowledgeGraphStatsResponse, Error>,
) => {
  return useQuery<IGetKnowledgeGraphStatsResponse, Error>({
    queryKey: ["knowledgeGraphStats", input],
    queryFn: () => KnowledgeGraphService.getKnowledgeGraphStats(input),
    ...options,
  });
};
