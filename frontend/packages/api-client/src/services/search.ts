import {
	ICreateEntityEmbeddingRequest,
	ICreateEntityEmbeddingResponse,
	IFindSimilarEntitiesRequest,
	IFindSimilarEntitiesResponse,
	IGenerateEmbeddingsRequest,
	IGenerateEmbeddingsResponse,
	IGraphSearchRequest,
	IGraphSearchResponse,
	ISearchEntitiesRequest,
	ISearchEntitiesResponse,
	IUpdateEntityEmbeddingsBatchRequest,
	IUpdateEntityEmbeddingsBatchResponse,
} from "@vbkg/types";
import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

const searchEntities = async (
	input: ISearchEntitiesRequest,
): Promise<ISearchEntitiesResponse> => {
	return await api()
		.post<ISearchEntitiesResponse>(API_ENDPOINTS.SEARCH_ENTITIES, input)
		.then((res) => res.data);
};

const findSimilarEntities = async (
	input: IFindSimilarEntitiesRequest,
): Promise<IFindSimilarEntitiesResponse> => {
	return await api()
		.post<IFindSimilarEntitiesResponse>(
			API_ENDPOINTS.FIND_SIMILAR_ENTITIES,
			input,
		)
		.then((res) => res.data);
};

const graphSearch = async (
	input: IGraphSearchRequest,
): Promise<IGraphSearchResponse> => {
	return await api()
		.post<IGraphSearchResponse>(API_ENDPOINTS.GRAPH_SEARCH, input)
		.then((res) => res.data);
};

const generateEmbedding = async (
	input: IGenerateEmbeddingsRequest,
): Promise<IGenerateEmbeddingsResponse> => {
	return await api()
		.post<IGenerateEmbeddingsResponse>(API_ENDPOINTS.GENERATE_EMBEDDINGS, input)
		.then((res) => res.data);
};

const createEntityEmbedding = async (
	input: ICreateEntityEmbeddingRequest,
): Promise<ICreateEntityEmbeddingResponse> => {
	return await api()
		.post<ICreateEntityEmbeddingResponse>(
			API_ENDPOINTS.CREATE_ENTITY_EMBEDDING(input.entity_id),
			input,
		)
		.then((res) => res.data);
};

const updateEntityEmbeddingBatch = async (
	input: IUpdateEntityEmbeddingsBatchRequest,
): Promise<IUpdateEntityEmbeddingsBatchResponse> => {
	return await api()
		.post<IUpdateEntityEmbeddingsBatchResponse>(
			API_ENDPOINTS.UPDATE_ENTITY_EMBEDDINGS_BATCH,
			input,
		)
		.then((res) => res.data);
};

export const SearchService = {
	searchEntities,
	findSimilarEntities,
	graphSearch,
	generateEmbedding,
	createEntityEmbedding,
	updateEntityEmbeddingBatch,
};
