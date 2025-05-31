import {
  ICreateEntityRequest,
  ICreateEntityResponse,
  ISearchKGEntitiesRequest,
  IReadEntityRequest,
  IReadEntityResponse,
  ISearchKGEntitiesResponse,
  IUpdateEntityRequest,
  IUpdateEntityResponse,
  IDeleteEntityRequest,
  IDeleteEntityResponse,
  IReadEntityRelationshipsRequest,
  IReadEntityRelationshipsResponse,
  ICreateRelationshipRequest,
  ICreateRelationshipResponse,
  IExcuteQueryRequest,
  IExcuteQueryResponse,
  IGetKnowledgeGraphStatsRequest,
  IGetKnowledgeGraphStatsResponse,
  ICreateOrMergeEntityRequest,
  ICreateOrMergeEntityResponse,
} from "@vbkg/types";
import { api } from "../config/axios";
import { API_ENDPOINTS } from "@vbkg/utils";

const createEntityRequest = async (
  input: ICreateEntityRequest,
): Promise<ICreateEntityResponse> => {
  return await api()
    .post<ICreateEntityResponse>(API_ENDPOINTS.CREATE_ENTITY, input)
    .then((res) => res.data);
};

const searchEntities = async (
  input: ISearchKGEntitiesRequest,
): Promise<ISearchKGEntitiesResponse> => {
  return await api()
    .get<ISearchKGEntitiesResponse>(API_ENDPOINTS.SEARCH_KG_ENTITIES, {
      params: input,
    })
    .then((res) => res.data);
};

const readEntity = async (
  input: IReadEntityRequest,
): Promise<IReadEntityResponse> => {
  return await api()
    .get<IReadEntityResponse>(API_ENDPOINTS.READ_ENTITY(input.id), {
      params: input,
    })
    .then((res) => res.data);
};

const updateEntity = async (
  input: IUpdateEntityRequest,
): Promise<IUpdateEntityResponse> => {
  return await api()
    .put<IUpdateEntityResponse>(API_ENDPOINTS.UPDATE_ENTITY(input.id), input)
    .then((res) => res.data);
};

const deleteEntity = async (
  input: IDeleteEntityRequest,
): Promise<IDeleteEntityResponse> => {
  return await api()
    .delete<IDeleteEntityResponse>(API_ENDPOINTS.DELETE_ENTITY(input.id))
    .then((res) => res.data);
};

const readEntityRelationships = async (
  input: IReadEntityRelationshipsRequest,
): Promise<IReadEntityRelationshipsResponse> => {
  return await api()
    .get<IReadEntityRelationshipsResponse>(
      API_ENDPOINTS.READ_ENTITY_RELATIONSHIPS(input.id),
      {
        params: input,
      },
    )
    .then((res) => res.data);
};

const createRelationship = async (
  input: ICreateRelationshipRequest,
): Promise<ICreateRelationshipResponse> => {
  return await api()
    .post<ICreateRelationshipResponse>(API_ENDPOINTS.CREATE_RELATIONSHIP, input)
    .then((res) => res.data);
};

const executeQuery = async (
  input: IExcuteQueryRequest,
): Promise<IExcuteQueryResponse> => {
  return await api()
    .post<IExcuteQueryResponse>(API_ENDPOINTS.EXCUTE_QUERY, input)
    .then((res) => res.data);
};

const getKnowledgeGraphStats = async (
  input: IGetKnowledgeGraphStatsRequest,
): Promise<IGetKnowledgeGraphStatsResponse> => {
  return await api()
    .get<IGetKnowledgeGraphStatsResponse>(
      API_ENDPOINTS.GET_KNOWLEDGE_GRAPH_STATS,
      {
        params: input,
      },
    )
    .then((res) => res.data);
};

const createOrMergeEntity = async (
  input: ICreateOrMergeEntityRequest,
): Promise<ICreateOrMergeEntityResponse> => {
  return await api()
    .post<ICreateOrMergeEntityResponse>(
      API_ENDPOINTS.CREATE_OR_MERGE_ENTITY,
      input,
    )
    .then((res) => res.data);
};

export const KnowledgeService = {
  createEntityRequest,
  searchEntities,
  readEntity,
  updateEntity,
  deleteEntity,
  readEntityRelationships,
  createRelationship,
  executeQuery,
  getKnowledgeGraphStats,
  createOrMergeEntity,
};
