import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
	ISearchEntitiesRequest,
	ISearchEntitiesResponse,
	IFindSimilarEntitiesRequest,
	IFindSimilarEntitiesResponse,
	IGraphSearchRequest,
	IGraphSearchResponse,
	IAISearchRequest,
	IAISearchResponse,
	IQuickAISearchRequest,
	IPersonRankRequest,
	ISearchSubgraphRequest,
	IExplainAISearchRequest,
	IAISearchStatsResponse,
	ISearchTypeInfoResponse,
	IExplainAISearchResponse,
	ISearchSubgraphResponse,
	IPersonRankResponse,
	ISearchSuggestionsRequest,
	ISearchSuggestionsResponse,
} from "@vbkg/types";
import { SearchService } from "../../services/search";

// Search entities
export const useSearchEntities = (
	input: ISearchEntitiesRequest,
	options?: Partial<UseQueryOptions<ISearchEntitiesResponse, Error>>,
) => {
	return useQuery<ISearchEntitiesResponse, Error>({
		queryKey: ["searchEntities", input],
		queryFn: () => SearchService.searchEntities(input),
		...options,
	});
};

// Find similar entities
export const useFindSimilarEntities = (
	input: IFindSimilarEntitiesRequest,
	options?: Partial<UseQueryOptions<IFindSimilarEntitiesResponse, Error>>,
) => {
	return useQuery<IFindSimilarEntitiesResponse, Error>({
		queryKey: ["findSimilarEntities", input],
		queryFn: () => SearchService.findSimilarEntities(input),
		...options,
	});
};

// Graph search
export const useGraphSearch = (
	input: IGraphSearchRequest,
	options?: Partial<UseQueryOptions<IGraphSearchResponse, Error>>,
) => {
	return useQuery<IGraphSearchResponse, Error>({
		queryKey: ["graphSearch", input],
		queryFn: () => SearchService.graphSearch(input),
		...options,
	});
};

// Query Keys
export const aiSearchKeys = {
	all: ["ai-search"] as const,
	searches: () => [...aiSearchKeys.all, "searches"] as const,
	search: (params: IAISearchRequest) =>
		[...aiSearchKeys.searches(), params] as const,
	quickSearch: (params: IQuickAISearchRequest) =>
		[...aiSearchKeys.searches(), "quick", params] as const,
	suggestions: (query: string) =>
		[...aiSearchKeys.all, "suggestions", query] as const,
	personrank: (params: IPersonRankRequest) =>
		[...aiSearchKeys.all, "personrank", params] as const,
	subgraph: (params: ISearchSubgraphRequest) =>
		[...aiSearchKeys.all, "subgraph", params] as const,
	explain: (params: IExplainAISearchRequest) =>
		[...aiSearchKeys.all, "explain", params] as const,
	typeInfo: () => [...aiSearchKeys.all, "type-info"] as const,
	stats: () => [...aiSearchKeys.all, "stats"] as const,
};

export const useAISearch = (
	input: IAISearchRequest,
	options?: Partial<UseQueryOptions<IAISearchResponse, Error>>,
) => {
	return useQuery<IAISearchResponse, Error>({
		queryKey: aiSearchKeys.search(input),
		queryFn: () => SearchService.aiSearch(input),
		enabled: !!input.query && input.query.length > 0,
		staleTime: 5 * 60 * 1000, // 5 minutes
		...options,
	});
};

// Quick AI Search Hook
export const useQuickAISearch = (
	params: IQuickAISearchRequest,
	options?: Partial<UseQueryOptions<IAISearchResponse, Error>>,
) => {
	return useQuery<IAISearchResponse, Error>({
		queryKey: aiSearchKeys.quickSearch(params),
		queryFn: () => SearchService.quickAISearch(params),
		enabled: !!params.q && params.q.length > 0,
		staleTime: 5 * 60 * 1000, // 5 minutes
		...options,
	});
};

// Search Suggestions Hook
export const useSearchSuggestions = (
	params: ISearchSuggestionsRequest,
	options?: Partial<UseQueryOptions<ISearchSuggestionsResponse, Error>>,
) => {
	return useQuery<ISearchSuggestionsResponse, Error>({
		queryKey: aiSearchKeys.suggestions(params.partial_query),
		queryFn: () => SearchService.getSearchSuggestions(params),
		enabled: !!params.partial_query && params.partial_query.length >= 2,
		staleTime: 2 * 60 * 1000, // 2 minutes
		...options,
	});
};

// PersonRank Scores Hook
export const usePersonRankScores = (
	input: IPersonRankRequest,
	options?: Partial<UseQueryOptions<IPersonRankResponse, Error>>,
) => {
	return useQuery<IPersonRankResponse, Error>({
		queryKey: aiSearchKeys.personrank(input),
		queryFn: () => SearchService.calculatePersonRankScores(input),
		enabled: !!input.query && input.query.length > 0,
		staleTime: 10 * 60 * 1000, // 10 minutes
		...options,
	});
};

// AI Subgraph Hook
export const useAISubgraph = (
	input: ISearchSubgraphRequest,
	options?: Partial<UseQueryOptions<ISearchSubgraphResponse, Error>>,
) => {
	return useQuery<ISearchSubgraphResponse, Error>({
		queryKey: aiSearchKeys.subgraph(input),
		queryFn: () => SearchService.getAISubgraph(input),
		enabled: !!input.query && input.query.length > 0,
		staleTime: 10 * 60 * 1000, // 10 minutes
		...options,
	});
};

// Explain AI Search Hook
export const useExplainAISearch = (
	input: IExplainAISearchRequest,
	options?: Partial<UseQueryOptions<IExplainAISearchResponse, Error>>,
) => {
	return useQuery<IExplainAISearchResponse, Error>({
		queryKey: aiSearchKeys.explain(input),
		queryFn: () => SearchService.explainAISearch(input),
		enabled: !!input.query && input.query.length > 0,
		staleTime: 10 * 60 * 1000, // 10 minutes
		...options,
	});
};

// Search Type Info Hook
export const useSearchTypeInfo = (
	options?: Partial<UseQueryOptions<ISearchTypeInfoResponse, Error>>,
) => {
	return useQuery<ISearchTypeInfoResponse, Error>({
		queryKey: aiSearchKeys.typeInfo(),
		queryFn: SearchService.getSearchTypeInfo,
		staleTime: 60 * 60 * 1000, // 1 hour
		...options,
	});
};

// AI Search Stats Hook
export const useAISearchStats = (
	options?: Partial<UseQueryOptions<IAISearchStatsResponse, Error>>,
) => {
	return useQuery<IAISearchStatsResponse, Error>({
		queryKey: aiSearchKeys.stats(),
		queryFn: SearchService.getAISearchStats,
		staleTime: 30 * 60 * 1000, // 30 minutes
		...options,
	});
};
