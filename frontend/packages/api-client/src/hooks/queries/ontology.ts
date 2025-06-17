import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  IReadOntologyClassesRequest,
  IReadOntologyClassesResponse,
  IReadOntologyClassRequest,
  IReadOntologyClassResponse,
  IReadOntologyPropertiesRequest,
  IReadOntologyPropertiesResponse,
  IReadOntologyPropertyRequest,
  IReadOntologyPropertyResponse,
  IReadEntityMappingsRequest,
  IReadEntityMappingsResponse,
  IReadRelationshipMappingsRequest,
  IReadRelationshipMappingsResponse,
  ISuggestOntologyClassesRequest,
  ISuggestOntologyClassesResponse,
  ISuggestOntologyPropertiesRequest,
  ISuggestOntologyPropertiesResponse,
} from "@vbkg/types";
import { OntologyService } from "../../services/ontology";

export const useOntologyClasses = (
  input: IReadOntologyClassesRequest,
  options?: UseQueryOptions<IReadOntologyClassesResponse, Error>,
) => {
  return useQuery<IReadOntologyClassesResponse, Error>({
    queryKey: ["ontologyClasses", input],
    queryFn: () => OntologyService.readOntologyClasses(input),
    ...options,
  });
};

export const useOntologyClass = (
  input: IReadOntologyClassRequest,
  options?: UseQueryOptions<IReadOntologyClassResponse, Error>,
) => {
  return useQuery<IReadOntologyClassResponse, Error>({
    queryKey: ["ontologyClass", input.id],
    queryFn: () => OntologyService.readOntologyClass(input),
    enabled: !!input.id,
    ...options,
  });
};

// FIBO Properties (keeping existing)
export const useOntologyProperties = (
  input: IReadOntologyPropertiesRequest,
  options?: UseQueryOptions<IReadOntologyPropertiesResponse, Error>,
) => {
  return useQuery<IReadOntologyPropertiesResponse, Error>({
    queryKey: ["ontologyProperties", input],
    queryFn: () => OntologyService.readOntologyProperties(input),
    ...options,
  });
};

export const useOntologyProperty = (
  input: IReadOntologyPropertyRequest,
  options?: UseQueryOptions<IReadOntologyPropertyResponse, Error>,
) => {
  return useQuery<IReadOntologyPropertyResponse, Error>({
    queryKey: ["ontologyProperty", input.id],
    queryFn: () => OntologyService.readOntologyProperty(input),
    enabled: !!input.id,
    ...options,
  });
};

// Entity Mappings (updated)
export const useEntityMappings = (
  input: IReadEntityMappingsRequest,
  options?: UseQueryOptions<IReadEntityMappingsResponse, Error>,
) => {
  return useQuery<IReadEntityMappingsResponse, Error>({
    queryKey: ["entityMappings", input],
    queryFn: () => OntologyService.readEntityMappings(input),
    ...options,
  });
};

// Relationship Mappings (updated)
export const useRelationshipMappings = (
  input: IReadRelationshipMappingsRequest,
  options?: UseQueryOptions<IReadRelationshipMappingsResponse, Error>,
) => {
  return useQuery<IReadRelationshipMappingsResponse, Error>({
    queryKey: ["relationshipMappings", input],
    queryFn: () => OntologyService.readRelationshipMappings(input),
    ...options,
  });
};

// // Suggestion Hooks
// export const useSuggestEntityTypes = (
//   input: ISuggestEntityTypesRequest,
//   options?: UseQueryOptions<ISuggestEntityTypesResponse, Error>,
// ) => {
//   return useQuery<ISuggestEntityTypesResponse, Error>({
//     queryKey: ["suggestEntityTypes", input],
//     queryFn: () => OntologyService.suggestEntityTypes(input),
//     enabled: !!input.text,
//     ...options,
//   });
// };
//
// export const useSuggestRelationshipTypes = (
//   input: ISuggestRelationshipTypesRequest,
//   options?: UseQueryOptions<ISuggestRelationshipTypesResponse, Error>,
// ) => {
//   return useQuery<ISuggestRelationshipTypesResponse, Error>({
//     queryKey: ["suggestRelationshipTypes", input],
//     queryFn: () => OntologyService.suggestRelationshipTypes(input),
//     enabled: !!input.text,
//     ...options,
//   });
// };

export const useSuggestOntologyClasses = (
  input: ISuggestOntologyClassesRequest,
  options?: Partial<UseQueryOptions<ISuggestOntologyClassesResponse, Error>>,
) => {
  return useQuery<ISuggestOntologyClassesResponse, Error>({
    queryKey: ["suggestOntologyClasses", input],
    queryFn: () => OntologyService.suggestOntologyClasses(input),
    enabled: !!(input.entity_type || input.entity_text || input.entity_type_id),
    ...options,
  });
};

export const useSuggestOntologyProperties = (
  input: ISuggestOntologyPropertiesRequest,
  options?: Partial<UseQueryOptions<ISuggestOntologyPropertiesResponse, Error>>,
) => {
  return useQuery<ISuggestOntologyPropertiesResponse, Error>({
    queryKey: ["suggestOntologyProperties", input],
    queryFn: () => OntologyService.suggestOntologyProperties(input),
    ...options,
  });
};

// Stats Hook
// export const useMappingStats = (
//   input: IGetMappingStatsRequest,
//   options?: UseQueryOptions<IGetMappingStatsResponse, Error>,
// ) => {
//   return useQuery<IGetMappingStatsResponse, Error>({
//     queryKey: ["mappingStats", input],
//     queryFn: () => OntologyService.getMappingStats(input),
//     ...options,
//   });
// };
