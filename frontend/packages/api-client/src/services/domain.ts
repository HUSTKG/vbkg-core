import {
  ICreateDomainRequest,
  ICreateDomainResponse,
  IReadDomainsRequest,
  IReadDomainsResponse,
  IReadDomainRequest,
  IReadDomainResponse,
  IUpdateDomainRequest,
  IUpdateDomainResponse,
  IDeleteDomainRequest,
  IDeleteDomainResponse,
  IGetDomainStatsRequest,
  IGetDomainStatsResponse,
  ICreateEntityTypeRequest,
  ICreateEntityTypeResponse,
  IReadEntityTypesRequest,
  IReadEntityTypesResponse,
  IReadEntityTypeRequest,
  IReadEntityTypeResponse,
  IUpdateEntityTypeRequest,
  IUpdateEntityTypeResponse,
  IDeleteEntityTypeRequest,
  IDeleteEntityTypeResponse,
  ICreateRelationshipTypeRequest,
  ICreateRelationshipTypeResponse,
  IReadRelationshipTypesRequest,
  IReadRelationshipTypesResponse,
  IReadRelationshipTypeRequest,
  IReadRelationshipTypeResponse,
  IUpdateRelationshipTypeRequest,
  IUpdateRelationshipTypeResponse,
  IDeleteRelationshipTypeRequest,
  IDeleteRelationshipTypeResponse,
  IAddEntityTypeToDomainRequest,
  IAddEntityTypeToDomainResponse,
  IRemoveEntityTypeFromDomainRequest,
  IRemoveEntityTypeFromDomainResponse,
  IAddRelationshipTypeToDomainRequest,
  IAddRelationshipTypeToDomainResponse,
  IRemoveRelationshipTypeFromDomainRequest,
  IRemoveRelationshipTypeFromDomainResponse,
  IValidateTypeConstraintsRequest,
  IValidateTypeConstraintsResponse,
  IGetEntityTypesByDomainRequest,
  IGetEntityTypesByDomainResponse,
  IGetRelationshipTypesByDomainRequest,
  IGetRelationshipTypesByDomainResponse,
  IGetCompatibleRelationshipsRequest,
  IGetCompatibleRelationshipsResponse,
  IGetDomainAnalyticsOverviewRequest,
  IGetDomainAnalyticsOverviewResponse,
  IBulkCreateEntityTypesRequest,
  IBulkCreateEntityTypesResponse,
  IBulkCreateRelationshipTypesRequest,
  IBulkCreateRelationshipTypesResponse,
} from "@vbkg/types";
import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

// =============================================
// DOMAIN SERVICES
// =============================================

const createDomain = async (
  input: ICreateDomainRequest,
): Promise<ICreateDomainResponse> => {
  return await api()
    .post<ICreateDomainResponse>(API_ENDPOINTS.CREATE_DOMAIN, input)
    .then((res) => res.data);
};

const readDomains = async (
  input: IReadDomainsRequest,
): Promise<IReadDomainsResponse> => {
  return await api()
    .get<IReadDomainsResponse>(API_ENDPOINTS.READ_DOMAINS, {
      params: input,
    })
    .then((res) => res.data);
};

const readDomain = async (
  input: IReadDomainRequest,
): Promise<IReadDomainResponse> => {
  return await api()
    .get<IReadDomainResponse>(API_ENDPOINTS.READ_DOMAIN(input.id), {
      params: { include_types: input.include_types },
    })
    .then((res) => res.data);
};

const updateDomain = async (
  input: IUpdateDomainRequest,
): Promise<IUpdateDomainResponse> => {
  const { id, ...updateData } = input;
  return await api()
    .put<IUpdateDomainResponse>(API_ENDPOINTS.UPDATE_DOMAIN(id), updateData)
    .then((res) => res.data);
};

const deleteDomain = async (
  input: IDeleteDomainRequest,
): Promise<IDeleteDomainResponse> => {
  return await api()
    .delete<IDeleteDomainResponse>(API_ENDPOINTS.DELETE_DOMAIN(input.id))
    .then((res) => res.data);
};

const getDomainStats = async (
  input: IGetDomainStatsRequest,
): Promise<IGetDomainStatsResponse> => {
  return await api()
    .get<IGetDomainStatsResponse>(API_ENDPOINTS.GET_DOMAIN_STATS(input.id))
    .then((res) => res.data);
};

// =============================================
// ENTITY TYPE SERVICES
// =============================================

const createEntityType = async (
  input: ICreateEntityTypeRequest,
): Promise<ICreateEntityTypeResponse> => {
  return await api()
    .post<ICreateEntityTypeResponse>(API_ENDPOINTS.CREATE_ENTITY_TYPE, input)
    .then((res) => res.data);
};

const readEntityTypes = async (
  input: IReadEntityTypesRequest,
): Promise<IReadEntityTypesResponse> => {
  return await api()
    .get<IReadEntityTypesResponse>(API_ENDPOINTS.READ_ENTITY_TYPES, {
      params: input,
    })
    .then((res) => res.data);
};

const readEntityType = async (
  input: IReadEntityTypeRequest,
): Promise<IReadEntityTypeResponse> => {
  return await api()
    .get<IReadEntityTypeResponse>(API_ENDPOINTS.READ_ENTITY_TYPE(input.id), {
      params: {
        include_domains: input.include_domains,
        include_usage: input.include_usage,
      },
    })
    .then((res) => res.data);
};

const updateEntityType = async (
  input: IUpdateEntityTypeRequest,
): Promise<IUpdateEntityTypeResponse> => {
  const { id, ...updateData } = input;
  return await api()
    .put<IUpdateEntityTypeResponse>(
      API_ENDPOINTS.UPDATE_ENTITY_TYPE(id),
      updateData,
    )
    .then((res) => res.data);
};

const deleteEntityType = async (
  input: IDeleteEntityTypeRequest,
): Promise<IDeleteEntityTypeResponse> => {
  return await api()
    .delete<IDeleteEntityTypeResponse>(
      API_ENDPOINTS.DELETE_ENTITY_TYPE(input.id),
    )
    .then((res) => res.data);
};

// =============================================
// RELATIONSHIP TYPE SERVICES
// =============================================

const createRelationshipType = async (
  input: ICreateRelationshipTypeRequest,
): Promise<ICreateRelationshipTypeResponse> => {
  return await api()
    .post<ICreateRelationshipTypeResponse>(
      API_ENDPOINTS.CREATE_RELATIONSHIP_TYPE,
      input,
    )
    .then((res) => res.data);
};

const readRelationshipTypes = async (
  input: IReadRelationshipTypesRequest,
): Promise<IReadRelationshipTypesResponse> => {
  return await api()
    .get<IReadRelationshipTypesResponse>(
      API_ENDPOINTS.READ_RELATIONSHIP_TYPES,
      {
        params: input,
      },
    )
    .then((res) => res.data);
};

const readRelationshipType = async (
  input: IReadRelationshipTypeRequest,
): Promise<IReadRelationshipTypeResponse> => {
  return await api()
    .get<IReadRelationshipTypeResponse>(
      API_ENDPOINTS.READ_RELATIONSHIP_TYPE(input.id),
      {
        params: {
          include_domains: input.include_domains,
          include_usage: input.include_usage,
        },
      },
    )
    .then((res) => res.data);
};

const updateRelationshipType = async (
  input: IUpdateRelationshipTypeRequest,
): Promise<IUpdateRelationshipTypeResponse> => {
  const { id, ...updateData } = input;
  return await api()
    .put<IUpdateRelationshipTypeResponse>(
      API_ENDPOINTS.UPDATE_RELATIONSHIP_TYPE(id),
      updateData,
    )
    .then((res) => res.data);
};

const deleteRelationshipType = async (
  input: IDeleteRelationshipTypeRequest,
): Promise<IDeleteRelationshipTypeResponse> => {
  return await api()
    .delete<IDeleteRelationshipTypeResponse>(
      API_ENDPOINTS.DELETE_RELATIONSHIP_TYPE(input.id),
    )
    .then((res) => res.data);
};

// =============================================
// DOMAIN MAPPING SERVICES
// =============================================

const addEntityTypeToDomain = async (
  input: IAddEntityTypeToDomainRequest,
): Promise<IAddEntityTypeToDomainResponse> => {
  const { type_id, ...mappingData } = input;
  return await api()
    .post<IAddEntityTypeToDomainResponse>(
      API_ENDPOINTS.ADD_ENTITY_TYPE_TO_DOMAIN(type_id),
      mappingData,
    )
    .then((res) => res.data);
};

const removeEntityTypeFromDomain = async (
  input: IRemoveEntityTypeFromDomainRequest,
): Promise<IRemoveEntityTypeFromDomainResponse> => {
  return await api()
    .delete<IRemoveEntityTypeFromDomainResponse>(
      API_ENDPOINTS.REMOVE_ENTITY_TYPE_FROM_DOMAIN(
        input.type_id,
        input.domain_id,
      ),
    )
    .then((res) => res.data);
};

const addRelationshipTypeToDomain = async (
  input: IAddRelationshipTypeToDomainRequest,
): Promise<IAddRelationshipTypeToDomainResponse> => {
  const { type_id, ...mappingData } = input;
  return await api()
    .post<IAddRelationshipTypeToDomainResponse>(
      API_ENDPOINTS.ADD_RELATIONSHIP_TYPE_TO_DOMAIN(type_id),
      mappingData,
    )
    .then((res) => res.data);
};

const removeRelationshipTypeFromDomain = async (
  input: IRemoveRelationshipTypeFromDomainRequest,
): Promise<IRemoveRelationshipTypeFromDomainResponse> => {
  return await api()
    .delete<IRemoveRelationshipTypeFromDomainResponse>(
      API_ENDPOINTS.REMOVE_RELATIONSHIP_TYPE_FROM_DOMAIN(
        input.type_id,
        input.domain_id,
      ),
    )
    .then((res) => res.data);
};

// =============================================
// VALIDATION SERVICES
// =============================================

const validateTypeConstraints = async (
  input: IValidateTypeConstraintsRequest,
): Promise<IValidateTypeConstraintsResponse> => {
  return await api()
    .post<IValidateTypeConstraintsResponse>(
      API_ENDPOINTS.VALIDATE_TYPE_CONSTRAINTS,
      input,
    )
    .then((res) => res.data);
};

// =============================================
// UTILITY SERVICES
// =============================================

const getEntityTypesByDomain = async (
  input: IGetEntityTypesByDomainRequest,
): Promise<IGetEntityTypesByDomainResponse> => {
  return await api()
    .get<IGetEntityTypesByDomainResponse>(
      API_ENDPOINTS.GET_ENTITY_TYPES_BY_DOMAIN(input.domain_name),
      {
        params: { primary_only: input.primary_only },
      },
    )
    .then((res) => res.data);
};

const getRelationshipTypesByDomain = async (
  input: IGetRelationshipTypesByDomainRequest,
): Promise<IGetRelationshipTypesByDomainResponse> => {
  return await api()
    .get<IGetRelationshipTypesByDomainResponse>(
      API_ENDPOINTS.GET_RELATIONSHIP_TYPES_BY_DOMAIN(input.domain_name),
      {
        params: { primary_only: input.primary_only },
      },
    )
    .then((res) => res.data);
};

const getCompatibleRelationships = async (
  input: IGetCompatibleRelationshipsRequest,
): Promise<IGetCompatibleRelationshipsResponse> => {
  return await api()
    .get<IGetCompatibleRelationshipsResponse>(
      API_ENDPOINTS.GET_COMPATIBLE_RELATIONSHIPS,
      {
        params: input,
      },
    )
    .then((res) => res.data);
};

// =============================================
// ANALYTICS SERVICES
// =============================================

const getDomainAnalyticsOverview = async (
  input: IGetDomainAnalyticsOverviewRequest,
): Promise<IGetDomainAnalyticsOverviewResponse> => {
  return await api()
    .get<IGetDomainAnalyticsOverviewResponse>(
      API_ENDPOINTS.GET_DOMAIN_ANALYTICS_OVERVIEW,
    )
    .then((res) => res.data);
};

// =============================================
// BULK OPERATION SERVICES
// =============================================

const bulkCreateEntityTypes = async (
  input: IBulkCreateEntityTypesRequest,
): Promise<IBulkCreateEntityTypesResponse> => {
  return await api()
    .post<IBulkCreateEntityTypesResponse>(
      API_ENDPOINTS.BULK_CREATE_ENTITY_TYPES,
      input,
    )
    .then((res) => res.data);
};

const bulkCreateRelationshipTypes = async (
  input: IBulkCreateRelationshipTypesRequest,
): Promise<IBulkCreateRelationshipTypesResponse> => {
  return await api()
    .post<IBulkCreateRelationshipTypesResponse>(
      API_ENDPOINTS.BULK_CREATE_RELATIONSHIP_TYPES,
      input,
    )
    .then((res) => res.data);
};

// =============================================
// EXPORT SERVICE
// =============================================

export const DomainService = {
  // Domains
  createDomain,
  readDomains,
  readDomain,
  updateDomain,
  deleteDomain,
  getDomainStats,

  // Entity Types
  createEntityType,
  readEntityTypes,
  readEntityType,
  updateEntityType,
  deleteEntityType,

  // Relationship Types
  createRelationshipType,
  readRelationshipTypes,
  readRelationshipType,
  updateRelationshipType,
  deleteRelationshipType,

  // Domain Mappings
  addEntityTypeToDomain,
  removeEntityTypeFromDomain,
  addRelationshipTypeToDomain,
  removeRelationshipTypeFromDomain,

  // Validation
  validateTypeConstraints,

  // Utilities
  getEntityTypesByDomain,
  getRelationshipTypesByDomain,
  getCompatibleRelationships,

  // Analytics
  getDomainAnalyticsOverview,

  // Bulk Operations
  bulkCreateEntityTypes,
  bulkCreateRelationshipTypes,
};
