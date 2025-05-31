import {
  ICreateEntityMappingRequest,
  ICreateEntityMappingResponse,
  ICreateFiboClassRequest,
  ICreateFiboClassResponse,
  ICreateFiboPropertyRequest,
  ICreateFiboPropertyResponse,
  ICreateRelationshipMappingRequest,
  ICreateRelationshipMappingResponse,
  IDeleteEntityMappingRequest,
  IDeleteEntityMappingResponse,
  IDeleteFiboClassRequest,
  IDeleteFiboClassResponse,
  IDeleteFiboPropertyRequest,
  IDeleteFiboPropertyResponse,
  IDeleteRelationshipMappingRequest,
  IDeleteRelationshipMappingResponse,
  IImportOntologyRequest,
  IImportOntologyResponse,
  IReadEntityMappingsRequest,
  IReadEntityMappingsResponse,
  IReadFiboClassesRequest,
  IReadFiboClassRequest,
  IReadFiboClassResponse,
  IReadFiboPropertiesRequest,
  IReadFiboPropertiesResponse,
  IReadFiboPropertyRequest,
  IReadFiboPropertyResponse,
  IReadRelationshipMappingsRequest,
  IReadRelationshipMappingsResponse,
  ISuggestFiboClassesRequest,
  ISuggestFiboClassesResponse,
  ISuggestFiboPropertiesRequest,
  ISuggestFiboPropertiesResponse,
  IUpdateFiboClassRequest,
  IUpdateFiboClassResponse,
  IUpdateFiboPropertyRequest,
  IUpdateFiboPropertyResponse,
  IVerifyEntityMappingRequest,
  IVerifyEntityMappingResponse,
  IVerifyRelationshipMappingRequest,
  IVerifyRelationshipMappingResponse,
  IReadFiboClassesResponse,
  // ISuggestEntityTypesRequest,
  // ISuggestEntityTypesResponse,
  // ISuggestRelationshipTypesRequest,
  // ISuggestRelationshipTypesResponse,
  // IBulkCreateEntityMappingsRequest,
  // IBulkCreateEntityMappingsResponse,
} from "@vbkg/types";
import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

const readFiboClasses = async (
  input: IReadFiboClassesRequest,
): Promise<IReadFiboClassesResponse> => {
  return await api()
    .get<IReadFiboClassesResponse>(API_ENDPOINTS.READ_FIBO_CLASSES, {
      params: input,
    })
    .then((res) => res.data);
};

const createFiboClass = async (
  input: ICreateFiboClassRequest,
): Promise<ICreateFiboClassResponse> => {
  return await api()
    .post<ICreateFiboClassResponse>(API_ENDPOINTS.CREATE_FIBO_CLASS, input)
    .then((res) => res.data);
};

const readFiboClass = async (
  input: IReadFiboClassRequest,
): Promise<IReadFiboClassResponse> => {
  return await api()
    .get<IReadFiboClassResponse>(API_ENDPOINTS.READ_FIBO_CLASS(input.id))
    .then((res) => res.data);
};

const updateFiboClass = async (
  input: IUpdateFiboClassRequest,
): Promise<IUpdateFiboClassResponse> => {
  return await api()
    .put<IUpdateFiboClassResponse>(
      API_ENDPOINTS.UPDATE_FIBO_CLASS(input.id),
      input,
    )
    .then((res) => res.data);
};

const deleteFiboClass = async (
  input: IDeleteFiboClassRequest,
): Promise<IDeleteFiboClassResponse> => {
  return await api()
    .delete<IDeleteFiboClassResponse>(API_ENDPOINTS.DELETE_FIBO_CLASS(input.id))
    .then((res) => res.data);
};

const readFiboProperties = async (
  input: IReadFiboPropertiesRequest,
): Promise<IReadFiboPropertiesResponse> => {
  return await api()
    .get<IReadFiboPropertiesResponse>(API_ENDPOINTS.READ_FIBO_PROPERTIES, {
      params: input,
    })
    .then((res) => res.data);
};

const createFiboProperty = async (
  input: ICreateFiboPropertyRequest,
): Promise<ICreateFiboPropertyResponse> => {
  return await api()
    .post<ICreateFiboPropertyResponse>(
      API_ENDPOINTS.CREATE_FIBO_PROPERTY,
      input,
    )
    .then((res) => res.data);
};

const readFiboProperty = async (
  input: IReadFiboPropertyRequest,
): Promise<IReadFiboPropertyResponse> => {
  return await api()
    .get<IReadFiboPropertyResponse>(API_ENDPOINTS.READ_FIBO_PROPERTY(input.id))
    .then((res) => res.data);
};

const updateFiboProperty = async (
  input: IUpdateFiboPropertyRequest,
): Promise<IUpdateFiboPropertyResponse> => {
  return await api()
    .put<IUpdateFiboPropertyResponse>(
      API_ENDPOINTS.UPDATE_FIBO_PROPERTY(input.id),
      input,
    )
    .then((res) => res.data);
};

const deleteFiboProperty = async (
  input: IDeleteFiboPropertyRequest,
): Promise<IDeleteFiboPropertyResponse> => {
  return await api()
    .delete<IDeleteFiboPropertyResponse>(
      API_ENDPOINTS.DELETE_FIBO_PROPERTY(input.id),
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

const suggestFiboClasses = async (
  input: ISuggestFiboClassesRequest,
): Promise<ISuggestFiboClassesResponse> => {
  return await api()
    .post<ISuggestFiboClassesResponse>(
      API_ENDPOINTS.SUGGEST_FIBO_CLASSES,
      input,
    )
    .then((res) => res.data);
};

const suggestFiboProperties = async (
  input: ISuggestFiboPropertiesRequest,
): Promise<ISuggestFiboPropertiesResponse> => {
  return await api()
    .post<ISuggestFiboPropertiesResponse>(
      API_ENDPOINTS.SUGGEST_FIBO_PROPERTIES,
      input,
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

export const FiboService = {
  readFiboProperties,
  createFiboProperty,
  readFiboProperty,
  updateFiboProperty,
  deleteFiboProperty,

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
  suggestFiboClasses,
  suggestFiboProperties,

  // Bulk Operations
  // bulkCreateEntityMappings,
  // bulkCreateRelationshipMappings,

  // Stats
  // getMappingStats,

  readFiboClasses,
  createFiboClass,
  readFiboClass,
  updateFiboClass,
  deleteFiboClass,
};
