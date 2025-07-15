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
) => {
	return await api()
		.post<ISearchEntitiesResponse>(API_ENDPOINTS.SEARCH_ENTITIES, input)
};

const findSimilarEntities = async (
	input: IFindSimilarEntitiesRequest,
) => {
	return await api()
		.post<IFindSimilarEntitiesResponse>(
			API_ENDPOINTS.FIND_SIMILAR_ENTITIES,
			input,
		)
};

const graphSearch = async (
	input: IGraphSearchRequest,
) => {
	return await api()
		.post<IGraphSearchResponse>(API_ENDPOINTS.GRAPH_SEARCH, input)
};

const generateEmbedding = async (
	input: IGenerateEmbeddingsRequest,
) => {
	return await api()
		.post<IGenerateEmbeddingsResponse>(API_ENDPOINTS.GENERATE_EMBEDDINGS, input)
};

const createEntityEmbedding = async (
	input: ICreateEntityEmbeddingRequest,
) => {
	return await api()
		.post<ICreateEntityEmbeddingResponse>(
			API_ENDPOINTS.CREATE_ENTITY_EMBEDDING(input.entity_id),
			input,
		)
};

const updateEntityEmbeddingBatch = async (
	input: IUpdateEntityEmbeddingsBatchRequest,
) => {
	return await api()
		.post<IUpdateEntityEmbeddingsBatchResponse>(
			API_ENDPOINTS.UPDATE_ENTITY_EMBEDDINGS_BATCH,
			input,
		)
};

const aiSearch = async (
	input: IAISearchRequest,
) => {
	return await api()
		.post<IAISearchResponse>(API_ENDPOINTS.AI_SEARCH, input)
};

// Quick AI Search
const quickAISearch = async (
	params: IQuickAISearchRequest,
) => {
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
};

// Search Suggestions
const getSearchSuggestions = async (
	params: ISearchSuggestionsRequest,
) => {
	const searchParams = new URLSearchParams();
	searchParams.append("q", params.partial_query);

	if (params.limit) {
		searchParams.append("limit", params.limit.toString());
	}

	return await api()
		.get<ISearchSuggestionsResponse>(
			`${API_ENDPOINTS.SEARCH_SUGGESTIONS}?${searchParams.toString()}`,
		)
};

// PersonRank Scores
const calculatePersonRankScores = async (
	input: IPersonRankRequest,
) => {
	return await api()
		.post<IPersonRankResponse>(API_ENDPOINTS.PERSONRANK_SCORES, input)
};

// AI Subgraph
const getAISubgraph = async (
	input: ISearchSubgraphRequest,
) => {
	return await api()
		.post<ISearchSubgraphResponse>(API_ENDPOINTS.AI_SUBGRAPH, input)
};

// Explain AI Search
const explainAISearch = async (
	input: IExplainAISearchRequest,
) => {
	return await api()
		.post<IExplainAISearchResponse>(
			API_ENDPOINTS.EXPLAIN_AI_SEARCH,
			input,
		)
};

// Get Search Type Info
const getSearchTypeInfo = async () => {
	return await api()
		.get<ISearchTypeInfoResponse>(API_ENDPOINTS.SEARCH_TYPE_INFO)
};

// Get AI Search Stats
const getAISearchStats = async () => {
	return await api()
		.get<IAISearchStatsResponse>(API_ENDPOINTS.AI_SEARCH_STATS)
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
