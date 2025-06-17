import {
	ICreateEntityEmbeddingRequest,
	ICreateEntityEmbeddingResponse,
	IFindSimilarEntitiesRequest,
	IAISearchRequest,
	IAISearchResponse,
	ISearchSuggestionsRequest,
	ISearchSuggestionsResponse,
	IQuickAISearchRequest,
	IPersonRankRequest,
	IPersonRankResponse,
	ISearchSubgraphRequest,
	ISearchSubgraphResponse,
	IExplainAISearchRequest,
	IExplainAISearchResponse,
	ISearchTypeInfoResponse,
	IAISearchStatsResponse,
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

const aiSearch = async (
	input: IAISearchRequest,
): Promise<IAISearchResponse> => {
	return await api()
		.post<IAISearchResponse>(API_ENDPOINTS.AI_SEARCH, input)
		.then((res) => res.data);
};

// Quick AI Search
const quickAISearch = async (
	params: IQuickAISearchRequest,
): Promise<IAISearchResponse> => {
	const searchParams = new URLSearchParams();
	searchParams.append("q", params.q);

	if (params.entity_types) {
		params.entity_types.forEach((type) =>
			searchParams.append("entity_types", type),
		);
	}

	if (params.max_results) {
		searchParams.append("max_results", params.max_results.toString());
	}

	if (params.generate_answer !== undefined) {
		searchParams.append("generate_answer", params.generate_answer.toString());
	}

	return await api()
		.get<IAISearchResponse>(
			`${API_ENDPOINTS.QUICK_AI_SEARCH}?${searchParams.toString()}`,
		)
		.then((res) => res.data);
};

// Search Suggestions
const getSearchSuggestions = async (
	params: ISearchSuggestionsRequest,
): Promise<ISearchSuggestionsResponse> => {
	const searchParams = new URLSearchParams();
	searchParams.append("q", params.partial_query);

	if (params.limit) {
		searchParams.append("limit", params.limit.toString());
	}

	return await api()
		.get<ISearchSuggestionsResponse>(
			`${API_ENDPOINTS.SEARCH_SUGGESTIONS}?${searchParams.toString()}`,
		)
		.then((res) => res.data);
};

// PersonRank Scores
const calculatePersonRankScores = async (
	input: IPersonRankRequest,
): Promise<IPersonRankResponse> => {
	return await api()
		.post<IPersonRankResponse>(API_ENDPOINTS.PERSONRANK_SCORES, input)
		.then((res) => res.data);
};

// AI Subgraph
const getAISubgraph = async (
	input: ISearchSubgraphRequest,
): Promise<ISearchSubgraphResponse> => {
	return await api()
		.post<ISearchSubgraphResponse>(API_ENDPOINTS.AI_SUBGRAPH, input)
		.then((res) => res.data);
};

// Explain AI Search
const explainAISearch = async (
	input: IExplainAISearchRequest,
): Promise<IExplainAISearchResponse> => {
	return await api()
		.post<IExplainAISearchResponse>(
			API_ENDPOINTS.EXPLAIN_AI_SEARCH,
			input,
		)
		.then((res) => res.data);
};

// Get Search Type Info
const getSearchTypeInfo = async (): Promise<ISearchTypeInfoResponse> => {
	return await api()
		.get<ISearchTypeInfoResponse>(API_ENDPOINTS.SEARCH_TYPE_INFO)
		.then((res) => res.data);
};

// Get AI Search Stats
const getAISearchStats = async (): Promise<IAISearchStatsResponse> => {
	return await api()
		.get<IAISearchStatsResponse>(API_ENDPOINTS.AI_SEARCH_STATS)
		.then((res) => res.data);
};

export const SearchService = {
	searchEntities,
	findSimilarEntities,
	graphSearch,
	generateEmbedding,
	createEntityEmbedding,
	updateEntityEmbeddingBatch,
	aiSearch,
	quickAISearch,
	getSearchSuggestions,
	calculatePersonRankScores,
	getAISubgraph,
	explainAISearch,
	getSearchTypeInfo,
	getAISearchStats,
};
