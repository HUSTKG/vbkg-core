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
	IGetDomainAnalyticsOverviewResponse,
	IGetDomainAnalyticsOverviewRequest,
} from "@vbkg/types";
import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

// =============================================
// DOMAIN SERVICES
// =============================================

const createDomain = async (input: ICreateDomainRequest) => {
	return await api().post<ICreateDomainResponse>(
		API_ENDPOINTS.CREATE_DOMAIN,
		input,
	);
};

const readDomains = async (input: IReadDomainsRequest) => {
	return await api().get<IReadDomainsResponse>(API_ENDPOINTS.READ_DOMAINS, {
		params: input,
	});
};

const readDomain = async (input: IReadDomainRequest) => {
	return await api().get<IReadDomainResponse>(
		API_ENDPOINTS.READ_DOMAIN(input.id),
		{
			params: { include_types: input.include_types },
		},
	);
};

const updateDomain = async (input: IUpdateDomainRequest) => {
	const { id, ...updateData } = input;
	return await api().put<IUpdateDomainResponse>(
		API_ENDPOINTS.UPDATE_DOMAIN(id),
		updateData,
	);
};

const deleteDomain = async (input: IDeleteDomainRequest) => {
	return await api().delete<IDeleteDomainResponse>(
		API_ENDPOINTS.DELETE_DOMAIN(input.id),
	);
};

const getDomainStats = async (input: IGetDomainStatsRequest) => {
	return await api().get<IGetDomainStatsResponse>(
		API_ENDPOINTS.GET_DOMAIN_STATS(input.id),
	);
};

// =============================================
// ENTITY TYPE SERVICES
// =============================================

const createEntityType = async (input: ICreateEntityTypeRequest) => {
	return await api().post<ICreateEntityTypeResponse>(
		API_ENDPOINTS.CREATE_ENTITY_TYPE,
		input,
	);
};

const readEntityTypes = async (input: IReadEntityTypesRequest) => {
	return await api().get<IReadEntityTypesResponse>(
		API_ENDPOINTS.READ_ENTITY_TYPES,
		{
			params: input,
		},
	);
};

const readEntityType = async (input: IReadEntityTypeRequest) => {
	return await api().get<IReadEntityTypeResponse>(
		API_ENDPOINTS.READ_ENTITY_TYPE(input.id),
		{
			params: {
				include_domains: input.include_domains,
				include_usage: input.include_usage,
			},
		},
	);
};

const updateEntityType = async (input: IUpdateEntityTypeRequest) => {
	const { id, ...updateData } = input;
	return await api().put<IUpdateEntityTypeResponse>(
		API_ENDPOINTS.UPDATE_ENTITY_TYPE(id),
		updateData,
	);
};

const deleteEntityType = async (input: IDeleteEntityTypeRequest) => {
	return await api().delete<IDeleteEntityTypeResponse>(
		API_ENDPOINTS.DELETE_ENTITY_TYPE(input.id),
	);
};

// =============================================
// RELATIONSHIP TYPE SERVICES
// =============================================

const createRelationshipType = async (
	input: ICreateRelationshipTypeRequest,
) => {
	return await api().post<ICreateRelationshipTypeResponse>(
		API_ENDPOINTS.CREATE_RELATIONSHIP_TYPE,
		input,
	);
};

const readRelationshipTypes = async (input: IReadRelationshipTypesRequest) => {
	return await api().get<IReadRelationshipTypesResponse>(
		API_ENDPOINTS.READ_RELATIONSHIP_TYPES,
		{
			params: input,
		},
	);
};

const readRelationshipType = async (input: IReadRelationshipTypeRequest) => {
	return await api().get<IReadRelationshipTypeResponse>(
		API_ENDPOINTS.READ_RELATIONSHIP_TYPE(input.id),
		{
			params: {
				include_domains: input.include_domains,
				include_usage: input.include_usage,
			},
		},
	);
};

const updateRelationshipType = async (
	input: IUpdateRelationshipTypeRequest,
) => {
	const { id, ...updateData } = input;
	return await api().put<IUpdateRelationshipTypeResponse>(
		API_ENDPOINTS.UPDATE_RELATIONSHIP_TYPE(id),
		updateData,
	);
};

const deleteRelationshipType = async (
	input: IDeleteRelationshipTypeRequest,
) => {
	return await api().delete<IDeleteRelationshipTypeResponse>(
		API_ENDPOINTS.DELETE_RELATIONSHIP_TYPE(input.id),
	);
};

// =============================================
// DOMAIN MAPPING SERVICES
// =============================================

const addEntityTypeToDomain = async (input: IAddEntityTypeToDomainRequest) => {
	const { type_id, ...mappingData } = input;
	return await api().post<IAddEntityTypeToDomainResponse>(
		API_ENDPOINTS.ADD_ENTITY_TYPE_TO_DOMAIN(type_id),
		mappingData,
	);
};

const removeEntityTypeFromDomain = async (
	input: IRemoveEntityTypeFromDomainRequest,
) => {
	return await api().delete<IRemoveEntityTypeFromDomainResponse>(
		API_ENDPOINTS.REMOVE_ENTITY_TYPE_FROM_DOMAIN(
			input.type_id,
			input.domain_id,
		),
	);
};

const addRelationshipTypeToDomain = async (
	input: IAddRelationshipTypeToDomainRequest,
) => {
	const { type_id, ...mappingData } = input;
	return await api().post<IAddRelationshipTypeToDomainResponse>(
		API_ENDPOINTS.ADD_RELATIONSHIP_TYPE_TO_DOMAIN(type_id),
		mappingData,
	);
};

const removeRelationshipTypeFromDomain = async (
	input: IRemoveRelationshipTypeFromDomainRequest,
) => {
	return await api().delete<IRemoveRelationshipTypeFromDomainResponse>(
		API_ENDPOINTS.REMOVE_RELATIONSHIP_TYPE_FROM_DOMAIN(
			input.type_id,
			input.domain_id,
		),
	);
};

// =============================================
// VALIDATION SERVICES
// =============================================

const validateTypeConstraints = async (
	input: IValidateTypeConstraintsRequest,
) => {
	return await api().post<IValidateTypeConstraintsResponse>(
		API_ENDPOINTS.VALIDATE_TYPE_CONSTRAINTS,
		input,
	);
};

// =============================================
// UTILITY SERVICES
// =============================================

const getEntityTypesByDomain = async (
	input: IGetEntityTypesByDomainRequest,
) => {
	return await api().get<IGetEntityTypesByDomainResponse>(
		API_ENDPOINTS.GET_ENTITY_TYPES_BY_DOMAIN(input.domain_name),
		{
			params: { primary_only: input.primary_only },
		},
	);
};

const getRelationshipTypesByDomain = async (
	input: IGetRelationshipTypesByDomainRequest,
) => {
	return await api().get<IGetRelationshipTypesByDomainResponse>(
		API_ENDPOINTS.GET_RELATIONSHIP_TYPES_BY_DOMAIN(input.domain_name),
		{
			params: { primary_only: input.primary_only },
		},
	);
};

const getCompatibleRelationships = async (
	input: IGetCompatibleRelationshipsRequest,
) => {
	return await api().get<IGetCompatibleRelationshipsResponse>(
		API_ENDPOINTS.GET_COMPATIBLE_RELATIONSHIPS,
		{
			params: input,
		},
	);
};

const getDomainOverview = async (input: IGetDomainAnalyticsOverviewRequest) => {
	return await api().get<IGetDomainAnalyticsOverviewResponse>(
		API_ENDPOINTS.GET_DOMAIN_OVERVIEW,
		{
			params: input,
		},
	);
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
	getDomainOverview,
};
