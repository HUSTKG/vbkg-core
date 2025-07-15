import {
	ICreateEntityMappingRequest,
	ICreateEntityMappingResponse,
	ICreateOntologyClassRequest,
	ICreateOntologyClassResponse,
	ICreateOntologyPropertyRequest,
	ICreateOntologyPropertyResponse,
	ICreateRelationshipMappingRequest,
	IDeleteEntityMappingRequest,
	IDeleteEntityMappingResponse,
	IDeleteOntologyClassRequest,
	IDeleteOntologyClassResponse,
	IDeleteOntologyPropertyRequest,
	IDeleteOntologyPropertyResponse,
	IDeleteRelationshipMappingRequest,
	IDeleteRelationshipMappingResponse,
	IImportOntologyRequest,
	IImportOntologyResponse,
	IReadEntityMappingsRequest,
	IReadEntityMappingsResponse,
	IReadOntologyClassesRequest,
	IReadOntologyClassRequest,
	IReadOntologyClassResponse,
	IReadOntologyPropertiesRequest,
	IReadOntologyPropertiesResponse,
	IReadOntologyPropertyRequest,
	IReadOntologyPropertyResponse,
	IReadRelationshipMappingsRequest,
	IReadRelationshipMappingsResponse,
	ISuggestOntologyClassesRequest,
	ISuggestOntologyClassesResponse,
	ISuggestOntologyPropertiesRequest,
	ISuggestOntologyPropertiesResponse,
	IUpdateOntologyClassRequest,
	IUpdateOntologyClassResponse,
	IUpdateOntologyPropertyRequest,
	IUpdateOntologyPropertyResponse,
	IVerifyEntityMappingRequest,
	IVerifyEntityMappingResponse,
	IVerifyRelationshipMappingRequest,
	IVerifyRelationshipMappingResponse,
	IReadOntologyClassesResponse,
	IApplyEntityMappingSuggestionRequest,
	IApplyEntityMappingSuggestionResponse,
	IApplyRelationshipMappingSuggestionRequest,
	IApplyRelationshipMappingSuggestionResponse,
	// ISuggestEntityTypesRequest,
	// ISuggestEntityTypesResponse,
	// ISuggestRelationshipTypesRequest,
	// ISuggestRelationshipTypesResponse,
	// IBulkCreateEntityMappingsRequest,
	// IBulkCreateEntityMappingsResponse,
} from "@vbkg/types";
import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

const readOntologyClasses = async (input: IReadOntologyClassesRequest) => {
	return await api().get<IReadOntologyClassesResponse>(
		API_ENDPOINTS.READ_ONTOLOGY_CLASSES,
		{
			params: input,
		},
	);
};

const createOntologyClass = async (input: ICreateOntologyClassRequest) => {
	return await api().post<ICreateOntologyClassResponse>(
		API_ENDPOINTS.CREATE_ONTOLOGY_CLASS,
		input,
	);
};

const readOntologyClass = async (input: IReadOntologyClassRequest) => {
	return await api().get<IReadOntologyClassResponse>(
		API_ENDPOINTS.READ_ONTOLOGY_CLASS(input.id),
	);
};

const updateOntologyClass = async (input: IUpdateOntologyClassRequest) => {
	return await api().put<IUpdateOntologyClassResponse>(
		API_ENDPOINTS.UPDATE_ONTOLOGY_CLASS(input.id),
		input,
	);
};

const deleteOntologyClass = async (input: IDeleteOntologyClassRequest) => {
	return await api().delete<IDeleteOntologyClassResponse>(
		API_ENDPOINTS.DELETE_ONTOLOGY_CLASS(input.id),
	);
};

const readOntologyProperties = async (
	input: IReadOntologyPropertiesRequest,
) => {
	return await api().get<IReadOntologyPropertiesResponse>(
		API_ENDPOINTS.READ_ONTOLOGY_PROPERTIES,
		{
			params: input,
		},
	);
};

const createOntologyProperty = async (
	input: ICreateOntologyPropertyRequest,
) => {
	return await api().post<ICreateOntologyPropertyResponse>(
		API_ENDPOINTS.CREATE_ONTOLOGY_PROPERTY,
		input,
	);
};

const readOntologyProperty = async (input: IReadOntologyPropertyRequest) => {
	return await api().get<IReadOntologyPropertyResponse>(
		API_ENDPOINTS.READ_ONTOLOGY_PROPERTY(input.id),
	);
};

const updateOntologyProperty = async (
	input: IUpdateOntologyPropertyRequest,
) => {
	return await api().put<IUpdateOntologyPropertyResponse>(
		API_ENDPOINTS.UPDATE_ONTOLOGY_PROPERTY(input.id),
		input,
	);
};

const deleteOntologyProperty = async (
	input: IDeleteOntologyPropertyRequest,
) => {
	return await api().delete<IDeleteOntologyPropertyResponse>(
		API_ENDPOINTS.DELETE_ONTOLOGY_PROPERTY(input.id),
	);
};

// Ontology import (keeping existing)
const importOntology = async (input: IImportOntologyRequest) => {
	return await api().post<IImportOntologyResponse>(
		API_ENDPOINTS.IMPORT_ONTOLOGY,
		input,
	);
};

// Entity Mapping operations (updated)
const readEntityMappings = async (input: IReadEntityMappingsRequest) => {
	return await api().get<IReadEntityMappingsResponse>(
		API_ENDPOINTS.READ_ENTITY_MAPPINGS,
		{
			params: input,
		},
	);
};

const createEntityMapping = async (input: ICreateEntityMappingRequest) => {
	return await api().post<ICreateEntityMappingResponse>(
		API_ENDPOINTS.CREATE_ENTITY_MAPPING,
		input,
	);
};

const deleteEntityMapping = async (input: IDeleteEntityMappingRequest) => {
	return await api().delete<IDeleteEntityMappingResponse>(
		API_ENDPOINTS.DELETE_ENTITY_MAPPING(input.id),
	);
};

const verifyEntityMapping = async (input: IVerifyEntityMappingRequest) => {
	return await api().put<IVerifyEntityMappingResponse>(
		API_ENDPOINTS.VERIFY_ENTITY_MAPPING(input.id),
		input,
	);
};

// Relationship Mapping operations (updated)
const readRelationshipMappings = async (
	input: IReadRelationshipMappingsRequest,
) => {
	return await api().get<IReadRelationshipMappingsResponse>(
		API_ENDPOINTS.READ_RELATIONSHIP_MAPPINGS,
		{
			params: input,
		},
	);
};

const createRelationshipMapping = async (
	input: ICreateRelationshipMappingRequest,
) => {
	return await api().post<any>(
		API_ENDPOINTS.CREATE_RELATIONSHIP_MAPPING,
		input,
	);
};

const deleteRelationshipMapping = async (
	input: IDeleteRelationshipMappingRequest,
) => {
	return await api().delete<IDeleteRelationshipMappingResponse>(
		API_ENDPOINTS.DELETE_RELATIONSHIP_MAPPING(input.id),
	);
};

const verifyRelationshipMapping = async (
	input: IVerifyRelationshipMappingRequest,
) => {
	return await api().put<IVerifyRelationshipMappingResponse>(
		API_ENDPOINTS.VERIFY_RELATIONSHIP_MAPPING(input.id),
		input,
	);
};

// // New suggestion operations
// const suggestEntityTypes = async (
//   input: ISuggestEntityTypesRequest,
// ): Promise<ISuggestEntityTypesResponse> => {
//   return await api()
//     .post<ISuggestEntityTypesResponse>(
//       API_ENDPOINTS.SUGGEST_ENTITY_TYPES,
//       input,
//     )
// };
//
// const suggestRelationshipTypes = async (
//   input: ISuggestRelationshipTypesRequest,
// ): Promise<ISuggestRelationshipTypesResponse> => {
//   return await api()
//     .post<ISuggestRelationshipTypesResponse>(
//       API_ENDPOINTS.su,
//       input,
//     )
// };

const suggestOntologyClasses = async (
	input: ISuggestOntologyClassesRequest,
) => {
	return await api().get<ISuggestOntologyClassesResponse>(
		API_ENDPOINTS.SUGGEST_ONTOLOGY_CLASSES,
		{
			params: input,
		},
	);
};

const suggestOntologyProperties = async (
	input: ISuggestOntologyPropertiesRequest,
) => {
	return await api().get<ISuggestOntologyPropertiesResponse>(
		API_ENDPOINTS.SUGGEST_ONTOLOGY_PROPERTIES,
		{ params: input },
	);
};

// // Bulk operations
// const bulkCreateEntityMappings = async (
//   input: IBulkCreateEntityMappingsRequest,
// ): Promise<IBulkCreateEntityMappingsResponse> => {
//   return await api()
//     .post<IBulkCreateEntityMappingsResponse>(
//       API_ENDPOINTS.BULK_CREATE_ENTITY_MAPPINGS,
//       input,
//     )
// };
//
// const bulkCreateRelationshipMappings = async (
//   input: IBulkCreateRelationshipMappingsRequest,
// ): Promise<IBulkCreateRelationshipMappingsResponse> => {
//   return await api()
//     .post<IBulkCreateRelationshipMappingsResponse>(
//       API_ENDPOINTS.BULK_CREATE_RELATIONSHIP_MAPPINGS,
//       input,
//     )
// };

// // Stats
// const getMappingStats = async (
//   input: IGetMappingStatsRequest,
// ): Promise<IGetMappingStatsResponse> => {
//   return await api()
//     .get<IGetMappingStatsResponse>(API_ENDPOINTS.GET_MAPPING_STATS, {
//       params: input,
//     })
// };

const applyEntityMappingSuggestion = async (
	input: IApplyEntityMappingSuggestionRequest,
) => {
	return await api().post<IApplyEntityMappingSuggestionResponse>(
		API_ENDPOINTS.APPLY_ENTITY_MAPPING_SUGGESTION(input.id),
		{
		},
		{
			params: {
				suggestion_index: input.suggestion_index,
			},
		},
	);
};

const applyRelationshipMappingSuggestion = async (
	input: IApplyRelationshipMappingSuggestionRequest,
) => {
	return await api().post<IApplyRelationshipMappingSuggestionResponse>(
		API_ENDPOINTS.APPLY_RELATIONSHIP_MAPPING_SUGGESTION(input.id),
		{},
		{
			params: {
				suggestion_index: input.suggestion_index,
			},
		},
	);
};

export const OntologyService = {
	readOntologyProperties,
	createOntologyProperty,
	readOntologyProperty,
	updateOntologyProperty,
	deleteOntologyProperty,

	// Ontology Import
	importOntology,

	// Entity Mappings (updated)
	readEntityMappings,
	createEntityMapping,
	deleteEntityMapping,
	verifyEntityMapping,

	// Relationship Mappings (updated)
	readRelationshipMappings,
	createRelationshipMapping,
	deleteRelationshipMapping,
	verifyRelationshipMapping,

	// // Suggestions
	// suggestEntityTypes,
	// suggestRelationshipTypes,
	suggestOntologyClasses,
	suggestOntologyProperties,

	// Bulk Operations
	// bulkCreateEntityMappings,
	// bulkCreateRelationshipMappings,

	// Stats
	// getMappingStats,

	readOntologyClasses,
	createOntologyClass,
	readOntologyClass,
	updateOntologyClass,
	deleteOntologyClass,

	applyEntityMappingSuggestion,
	applyRelationshipMappingSuggestion,
};
