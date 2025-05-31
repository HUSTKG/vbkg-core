import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  IReadFiboClassesRequest,
  IReadFiboClassesResponse,
  IReadFiboClassRequest,
  IReadFiboClassResponse,
  IReadFiboPropertiesRequest,
  IReadFiboPropertiesResponse,
  IReadFiboPropertyRequest,
  IReadFiboPropertyResponse,
  IReadEntityMappingsRequest,
  IReadEntityMappingsResponse,
  IReadRelationshipMappingsRequest,
  IReadRelationshipMappingsResponse,
  ISuggestFiboClassesRequest,
  ISuggestFiboClassesResponse,
  ISuggestFiboPropertiesRequest,
  ISuggestFiboPropertiesResponse,
} from "@vbkg/types";
import { FiboService } from "../../services/fibo";

export const useFiboClasses = (
  input: IReadFiboClassesRequest,
  options?: UseQueryOptions<IReadFiboClassesResponse, Error>,
) => {
  return useQuery<IReadFiboClassesResponse, Error>({
    queryKey: ["fiboClasses", input],
    queryFn: () => FiboService.readFiboClasses(input),
    ...options,
  });
};

export const useFiboClass = (
  input: IReadFiboClassRequest,
  options?: UseQueryOptions<IReadFiboClassResponse, Error>,
) => {
  return useQuery<IReadFiboClassResponse, Error>({
    queryKey: ["fiboClass", input.id],
    queryFn: () => FiboService.readFiboClass(input),
    enabled: !!input.id,
    ...options,
  });
};

// FIBO Properties (keeping existing)
export const useFiboProperties = (
  input: IReadFiboPropertiesRequest,
  options?: UseQueryOptions<IReadFiboPropertiesResponse, Error>,
) => {
  return useQuery<IReadFiboPropertiesResponse, Error>({
    queryKey: ["fiboProperties", input],
    queryFn: () => FiboService.readFiboProperties(input),
    ...options,
  });
};

export const useFiboProperty = (
  input: IReadFiboPropertyRequest,
  options?: UseQueryOptions<IReadFiboPropertyResponse, Error>,
) => {
  return useQuery<IReadFiboPropertyResponse, Error>({
    queryKey: ["fiboProperty", input.id],
    queryFn: () => FiboService.readFiboProperty(input),
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
    queryFn: () => FiboService.readEntityMappings(input),
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
    queryFn: () => FiboService.readRelationshipMappings(input),
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
//     queryFn: () => FiboService.suggestEntityTypes(input),
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
//     queryFn: () => FiboService.suggestRelationshipTypes(input),
//     enabled: !!input.text,
//     ...options,
//   });
// };

export const useSuggestFiboClasses = (
  input: ISuggestFiboClassesRequest,
  options?: UseQueryOptions<ISuggestFiboClassesResponse, Error>,
) => {
  return useQuery<ISuggestFiboClassesResponse, Error>({
    queryKey: ["suggestFiboClasses", input],
    queryFn: () => FiboService.suggestFiboClasses(input),
    enabled: !!(input.entity_type || input.entity_text || input.entity_type_id),
    ...options,
  });
};

export const useSuggestFiboProperties = (
  input: ISuggestFiboPropertiesRequest,
  options?: UseQueryOptions<ISuggestFiboPropertiesResponse, Error>,
) => {
  return useQuery<ISuggestFiboPropertiesResponse, Error>({
    queryKey: ["suggestFiboProperties", input],
    queryFn: () => FiboService.suggestFiboProperties(input),
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
//     queryFn: () => FiboService.getMappingStats(input),
//     ...options,
//   });
// };
