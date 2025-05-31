import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  IReadEntityRequest,
  IReadEntityResponse,
  IReadEntityRelationshipsRequest,
  IReadEntityRelationshipsResponse,
  IExcuteQueryRequest,
  IExcuteQueryResponse,
  IGetKnowledgeGraphStatsRequest,
  IGetKnowledgeGraphStatsResponse,
} from "@vbkg/types";
import { KnowledgeService } from "../../services/knowledge";

// Read single entity
export const useEntity = (
  input: IReadEntityRequest,
  options?: UseQueryOptions<IReadEntityResponse, Error>,
) => {
  return useQuery<IReadEntityResponse, Error>({
    queryKey: ["entity", input.id],
    queryFn: () => KnowledgeService.readEntity(input),
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
    queryFn: () => KnowledgeService.readEntityRelationships(input),
    ...options,
  });
};

// Execute query
export const useExecuteQuery = (
  input: IExcuteQueryRequest,
  options?: UseQueryOptions<IExcuteQueryResponse, Error>,
) => {
  return useQuery<IExcuteQueryResponse, Error>({
    queryKey: ["executeQuery", input],
    queryFn: () => KnowledgeService.executeQuery(input),
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
    queryFn: () => KnowledgeService.getKnowledgeGraphStats(input),
    ...options,
  });
};
