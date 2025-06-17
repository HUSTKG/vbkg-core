import {
	ICreateEntityMappingRequest,
	ICreateEntityMappingResponse,
	ICreateOntologyClassRequest,
	ICreateOntologyClassResponse,
	ICreateOntologyPropertyRequest,
	ICreateOntologyPropertyResponse,
	ICreateRelationshipMappingRequest,
	ICreateRelationshipMappingResponse,
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
	// ISuggestEntityTypesRequest,
	// ISuggestEntityTypesResponse,
	// ISuggestRelationshipTypesRequest,
	// ISuggestRelationshipTypesResponse,
	// IBulkCreateEntityMappingsRequest,
	// IBulkCreateEntityMappingsResponse,
} from "@vbkg/types";
import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

const readOntologyClasses = async (
	input: IReadOntologyClassesRequest,
): Promise<IReadOntologyClassesResponse> => {
	return await api()
		.get<IReadOntologyClassesResponse>(API_ENDPOINTS.READ_ONTOLOGY_CLASSES, {
			params: input,
		})
		.then((res) => res.data);
};

const createOntologyClass = async (
	input: ICreateOntologyClassRequest,
): Promise<ICreateOntologyClassResponse> => {
	return await api()
		.post<ICreateOntologyClassResponse>(API_ENDPOINTS.CREATE_ONTOLOGY_CLASS, input)
		.then((res) => res.data);
};

const readOntologyClass = async (
	input: IReadOntologyClassRequest,
): Promise<IReadOntologyClassResponse> => {
	return await api()
		.get<IReadOntologyClassResponse>(API_ENDPOINTS.READ_ONTOLOGY_CLASS(input.id))
		.then((res) => res.data);
};

const updateOntologyClass = async (
	input: IUpdateOntologyClassRequest,
): Promise<IUpdateOntologyClassResponse> => {
	return await api()
		.put<IUpdateOntologyClassResponse>(
			API_ENDPOINTS.UPDATE_ONTOLOGY_CLASS(input.id),
			input,
		)
		.then((res) => res.data);
};

const deleteOntologyClass = async (
	input: IDeleteOntologyClassRequest,
): Promise<IDeleteOntologyClassResponse> => {
	return await api()
		.delete<IDeleteOntologyClassResponse>(API_ENDPOINTS.DELETE_ONTOLOGY_CLASS(input.id))
		.then((res) => res.data);
};

const readOntologyProperties = async (
	input: IReadOntologyPropertiesRequest,
): Promise<IReadOntologyPropertiesResponse> => {
	return await api()
		.get<IReadOntologyPropertiesResponse>(API_ENDPOINTS.READ_ONTOLOGY_PROPERTIES, {
			params: input,
		})
		.then((res) => res.data);
};

const createOntologyProperty = async (
	input: ICreateOntologyPropertyRequest,
): Promise<ICreateOntologyPropertyResponse> => {
	return await api()
		.post<ICreateOntologyPropertyResponse>(
			API_ENDPOINTS.CREATE_ONTOLOGY_PROPERTY,
			input,
		)
		.then((res) => res.data);
};

const readOntologyProperty = async (
	input: IReadOntologyPropertyRequest,
): Promise<IReadOntologyPropertyResponse> => {
	return await api()
		.get<IReadOntologyPropertyResponse>(API_ENDPOINTS.READ_ONTOLOGY_PROPERTY(input.id))
		.then((res) => res.data);
};

const updateOntologyProperty = async (
	input: IUpdateOntologyPropertyRequest,
): Promise<IUpdateOntologyPropertyResponse> => {
	return await api()
		.put<IUpdateOntologyPropertyResponse>(
			API_ENDPOINTS.UPDATE_ONTOLOGY_PROPERTY(input.id),
			input,
		)
		.then((res) => res.data);
};

const deleteOntologyProperty = async (
	input: IDeleteOntologyPropertyRequest,
): Promise<IDeleteOntologyPropertyResponse> => {
	return await api()
		.delete<IDeleteOntologyPropertyResponse>(
			API_ENDPOINTS.DELETE_ONTOLOGY_PROPERTY(input.id),
		)
		.then((res) => res.data);
};

// Ontology import (keeping existing)
const importOntology = async (
	input: IImportOntologyRequest,
): Promise<IImportOntologyResponse> => {
	return await api()
		.post<IImportOntologyResponse>(API_ENDPOINTS.IMPORT_ONTOLOGY, input)
		.then((res) => res.data);
};

// Entity Mapping operations (updated)
const readEntityMappings = async (
	input: IReadEntityMappingsRequest,
): Promise<IReadEntityMappingsResponse> => {
	return await api()
		.get<IReadEntityMappingsResponse>(API_ENDPOINTS.READ_ENTITY_MAPPINGS, {
			params: input,
		})
		.then((res) => res.data);
};

const createEntityMapping = async (
	input: ICreateEntityMappingRequest,
): Promise<ICreateEntityMappingResponse> => {
	return await api()
		.post<ICreateEntityMappingResponse>(
			API_ENDPOINTS.CREATE_ENTITY_MAPPING,
			input,
		)
		.then((res) => res.data);
};

const deleteEntityMapping = async (
	input: IDeleteEntityMappingRequest,
): Promise<IDeleteEntityMappingResponse> => {
	return await api()
		.delete<IDeleteEntityMappingResponse>(
			API_ENDPOINTS.DELETE_ENTITY_MAPPING(input.id),
		)
		.then((res) => res.data);
};

const verifyEntityMapping = async (
	input: IVerifyEntityMappingRequest,
): Promise<IVerifyEntityMappingResponse> => {
	return await api()
		.put<IVerifyEntityMappingResponse>(
			API_ENDPOINTS.VERIFY_ENTITY_MAPPING(input.id),
			input,
		)
		.then((res) => res.data);
};

// Relationship Mapping operations (updated)
const readRelationshipMappings = async (
	input: IReadRelationshipMappingsRequest,
): Promise<IReadRelationshipMappingsResponse> => {
	return await api()
		.get<IReadRelationshipMappingsResponse>(
			API_ENDPOINTS.READ_RELATIONSHIP_MAPPINGS,
			{
				params: input,
			},
		)
		.then((res) => res.data);
};

const createRelationshipMapping = async (
	input: ICreateRelationshipMappingRequest,
): Promise<ICreateRelationshipMappingResponse> => {
	return await api()
		.post<ICreateRelationshipMappingResponse>(
			API_ENDPOINTS.CREATE_RELATIONSHIP_MAPPING,
			input,
		)
		.then((res) => res.data);
};

const deleteRelationshipMapping = async (
	input: IDeleteRelationshipMappingRequest,
): Promise<IDeleteRelationshipMappingResponse> => {
	return await api()
		.delete<IDeleteRelationshipMappingResponse>(
			API_ENDPOINTS.DELETE_RELATIONSHIP_MAPPING(input.id),
		)
		.then((res) => res.data);
};

const verifyRelationshipMapping = async (
	input: IVerifyRelationshipMappingRequest,
): Promise<IVerifyRelationshipMappingResponse> => {
	return await api()
		.put<IVerifyRelationshipMappingResponse>(
			API_ENDPOINTS.VERIFY_RELATIONSHIP_MAPPING(input.id),
			input,
		)
		.then((res) => res.data);
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
//     .then((res) => res.data);
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
//     .then((res) => res.data);
// };

const suggestOntologyClasses = async (
	input: ISuggestOntologyClassesRequest,
): Promise<ISuggestOntologyClassesResponse> => {
	return await api()
		.get<ISuggestOntologyClassesResponse>(API_ENDPOINTS.SUGGEST_ONTOLOGY_CLASSES, {
			params: input,
		})
		.then((res) => res.data);
};

const suggestOntologyProperties = async (
	input: ISuggestOntologyPropertiesRequest,
): Promise<ISuggestOntologyPropertiesResponse> => {
	return await api()
		.get<ISuggestOntologyPropertiesResponse>(
			API_ENDPOINTS.SUGGEST_ONTOLOGY_PROPERTIES,
			{params: input},
		)
		.then((res) => res.data);
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
//     .then((res) => res.data);
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
//     .then((res) => res.data);
// };

// // Stats
// const getMappingStats = async (
//   input: IGetMappingStatsRequest,
// ): Promise<IGetMappingStatsResponse> => {
//   return await api()
//     .get<IGetMappingStatsResponse>(API_ENDPOINTS.GET_MAPPING_STATS, {
//       params: input,
//     })
//     .then((res) => res.data);
// };

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
};
