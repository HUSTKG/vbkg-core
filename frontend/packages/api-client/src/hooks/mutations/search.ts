import { useMutation, UseMutationOptions } from "@tanstack/react-query";
import {
	IGenerateEmbeddingsRequest,
	IGenerateEmbeddingsResponse,
	ICreateEntityEmbeddingRequest,
	ICreateEntityEmbeddingResponse,
	IUpdateEntityEmbeddingsBatchRequest,
	IUpdateEntityEmbeddingsBatchResponse,
	IPersonRankRequest,
	IPersonRankResponse,
	ISearchSubgraphRequest,
	ISearchSubgraphResponse,
	IExplainAISearchRequest,
	IExplainAISearchResponse,
    IAISearchResponse,
    IAISearchRequest,
} from "@vbkg/types";
import { SearchService } from "../../services/search";

// Generate embeddings
export const useGenerateEmbeddings = (
	options: UseMutationOptions<
		IGenerateEmbeddingsResponse,
		Error,
		IGenerateEmbeddingsRequest
	>,
) => {
	return useMutation<
		IGenerateEmbeddingsResponse,
		Error,
		IGenerateEmbeddingsRequest
	>({
		mutationFn: SearchService.generateEmbedding,
		...options,
	});
};

// Create entity embedding
export const useCreateEntityEmbedding = (
	options: UseMutationOptions<
		ICreateEntityEmbeddingResponse,
		Error,
		ICreateEntityEmbeddingRequest
	>,
) => {
	return useMutation<
		ICreateEntityEmbeddingResponse,
		Error,
		ICreateEntityEmbeddingRequest
	>({
		mutationFn: SearchService.createEntityEmbedding,
		...options,
	});
};

// Update entity embeddings batch
export const useUpdateEntityEmbeddingsBatch = (
	options: UseMutationOptions<
		IUpdateEntityEmbeddingsBatchResponse,
		Error,
		IUpdateEntityEmbeddingsBatchRequest
	>,
) => {
	return useMutation<
		IUpdateEntityEmbeddingsBatchResponse,
		Error,
		IUpdateEntityEmbeddingsBatchRequest
	>({
		mutationFn: SearchService.updateEntityEmbeddingBatch,
		...options,
	});
};

// Mutation Hooks for Actions
export const usePersonRankMutation = (
	options?: UseMutationOptions<IPersonRankResponse, Error, IPersonRankRequest>,
) => {
	return useMutation<IPersonRankResponse, Error, IPersonRankRequest>({
		mutationFn: SearchService.calculatePersonRankScores,
		...options,
	});
};

export const useSearchSubgraphMutation = (
	options?: UseMutationOptions<
		ISearchSubgraphResponse,
		Error,
		ISearchSubgraphRequest
	>,
) => {
	return useMutation<ISearchSubgraphResponse, Error, ISearchSubgraphRequest>({
		mutationFn: SearchService.getAISubgraph,
		...options,
	});
};

export const useExplainSearchMutation = (
	options?: UseMutationOptions<
		IExplainAISearchResponse,
		Error,
		IExplainAISearchRequest
	>,
) => {
	return useMutation<IExplainAISearchResponse, Error, IExplainAISearchRequest>({
		mutationFn: SearchService.explainAISearch,
		...options,
	});
};

// AI Search Mutation (for manual triggering)
export const useAISearchMutation = (
	options?: UseMutationOptions<IAISearchResponse, Error, IAISearchRequest>,
) => {
	return useMutation<IAISearchResponse, Error, IAISearchRequest>({
		mutationFn: SearchService.aiSearch,
		...options,
	});
};

