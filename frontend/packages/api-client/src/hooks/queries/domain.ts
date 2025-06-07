import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  IReadDomainsRequest,
  IReadDomainsResponse,
  IReadDomainRequest,
  IReadDomainResponse,
  IGetDomainStatsRequest,
  IGetDomainStatsResponse,
  IReadEntityTypesRequest,
  IReadEntityTypesResponse,
  IReadEntityTypeRequest,
  IReadEntityTypeResponse,
  IReadRelationshipTypesRequest,
  IReadRelationshipTypesResponse,
  IReadRelationshipTypeRequest,
  IReadRelationshipTypeResponse,
  IGetEntityTypesByDomainRequest,
  IGetEntityTypesByDomainResponse,
  IGetRelationshipTypesByDomainRequest,
  IGetRelationshipTypesByDomainResponse,
  IGetCompatibleRelationshipsRequest,
  IGetCompatibleRelationshipsResponse,
} from "@vbkg/types";
import { DomainService } from "../../services/domain";

// =============================================
// DOMAIN HOOKS
// =============================================

export const useDomains = (
  input: IReadDomainsRequest,
  options?: UseQueryOptions<IReadDomainsResponse, Error>,
) => {
  return useQuery<IReadDomainsResponse, Error>({
    queryKey: ["domains", input],
    queryFn: () => DomainService.readDomains(input),
    ...options,
  });
};

export const useDomain = (
  input: IReadDomainRequest,
  options?: UseQueryOptions<IReadDomainResponse, Error>,
) => {
  return useQuery<IReadDomainResponse, Error>({
    queryKey: ["domain", input.id, { include_types: input.include_types }],
    queryFn: () => DomainService.readDomain(input),
    enabled: !!input.id,
    ...options,
  });
};

export const useDomainStats = (
  input: IGetDomainStatsRequest,
  options?: UseQueryOptions<IGetDomainStatsResponse, Error>,
) => {
  return useQuery<IGetDomainStatsResponse, Error>({
    queryKey: ["domainStats", input.id],
    queryFn: () => DomainService.getDomainStats(input),
    enabled: !!input.id,
    ...options,
  });
};

// =============================================
// ENTITY TYPE HOOKS
// =============================================

export const useEntityTypes = (
  input: IReadEntityTypesRequest,
  options?: UseQueryOptions<IReadEntityTypesResponse, Error>,
) => {
  return useQuery<IReadEntityTypesResponse, Error>({
    queryKey: ["entityTypes", input],
    queryFn: () => DomainService.readEntityTypes(input),
    ...options,
  });
};

export const useEntityType = (
  input: IReadEntityTypeRequest,
  options?: UseQueryOptions<IReadEntityTypeResponse, Error>,
) => {
  return useQuery<IReadEntityTypeResponse, Error>({
    queryKey: [
      "entityType",
      input.id,
      {
        include_domains: input.include_domains,
        include_usage: input.include_usage,
      },
    ],
    queryFn: () => DomainService.readEntityType(input),
    enabled: !!input.id,
    ...options,
  });
};

// =============================================
// RELATIONSHIP TYPE HOOKS
// =============================================

export const useRelationshipTypes = (
  input: IReadRelationshipTypesRequest,
  options?: UseQueryOptions<IReadRelationshipTypesResponse, Error>,
) => {
  return useQuery<IReadRelationshipTypesResponse, Error>({
    queryKey: ["relationshipTypes", input],
    queryFn: () => DomainService.readRelationshipTypes(input),
    ...options,
  });
};

export const useRelationshipType = (
  input: IReadRelationshipTypeRequest,
  options?: UseQueryOptions<IReadRelationshipTypeResponse, Error>,
) => {
  return useQuery<IReadRelationshipTypeResponse, Error>({
    queryKey: [
      "relationshipType",
      input.id,
      {
        include_domains: input.include_domains,
        include_usage: input.include_usage,
      },
    ],
    queryFn: () => DomainService.readRelationshipType(input),
    enabled: !!input.id,
    ...options,
  });
};

// =============================================
// UTILITY HOOKS
// =============================================

export const useEntityTypesByDomain = (
  input: IGetEntityTypesByDomainRequest,
  options?: UseQueryOptions<IGetEntityTypesByDomainResponse, Error>,
) => {
  return useQuery<IGetEntityTypesByDomainResponse, Error>({
    queryKey: [
      "entityTypesByDomain",
      input.domain_name,
      { primary_only: input.primary_only },
    ],
    queryFn: () => DomainService.getEntityTypesByDomain(input),
    enabled: !!input.domain_name,
    ...options,
  });
};

export const useRelationshipTypesByDomain = (
  input: IGetRelationshipTypesByDomainRequest,
  options?: UseQueryOptions<IGetRelationshipTypesByDomainResponse, Error>,
) => {
  return useQuery<IGetRelationshipTypesByDomainResponse, Error>({
    queryKey: [
      "relationshipTypesByDomain",
      input.domain_name,
      { primary_only: input.primary_only },
    ],
    queryFn: () => DomainService.getRelationshipTypesByDomain(input),
    enabled: !!input.domain_name,
    ...options,
  });
};

export const useCompatibleRelationships = (
  input: IGetCompatibleRelationshipsRequest,
  options?: UseQueryOptions<IGetCompatibleRelationshipsResponse, Error>,
) => {
  return useQuery<IGetCompatibleRelationshipsResponse, Error>({
    queryKey: ["compatibleRelationships", input],
    queryFn: () => DomainService.getCompatibleRelationships(input),
    enabled: !!input.source_entity_type_id,
    ...options,
  });
};

// =============================================
// VALIDATION HOOKS
// =============================================

// Note: Validation is typically used on-demand, so it might be better suited for useMutation
// But including it here for completeness as a query hook
export const useValidationTypeConstraints = (
  input: {
    entity_type_id?: number;
    relationship_type_id?: number;
    source_entity_type_id?: number;
    target_entity_type_id?: number;
  },
  options?: UseQueryOptions<any, Error>,
) => {
  return useQuery({
    queryKey: ["validateTypeConstraints", input],
    queryFn: () => DomainService.validateTypeConstraints(input),
    enabled: !!(
      input.relationship_type_id &&
      input.source_entity_type_id &&
      input.target_entity_type_id
    ),
    ...options,
  });
};
