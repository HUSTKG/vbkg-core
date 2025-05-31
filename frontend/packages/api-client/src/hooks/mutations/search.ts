import { useMutation, UseMutationOptions } from "@tanstack/react-query";
import {
  IGenerateEmbeddingsRequest,
  IGenerateEmbeddingsResponse,
  ICreateEntityEmbeddingRequest,
  ICreateEntityEmbeddingResponse,
  IUpdateEntityEmbeddingsBatchRequest,
  IUpdateEntityEmbeddingsBatchResponse,
} from "@vbkg/types";
import { SearchService } from "../../services/search";

// Generate embeddings
export const useGenerateEmbeddings = (
  options: UseMutationOptions<IGenerateEmbeddingsResponse, Error, IGenerateEmbeddingsRequest>,
) => {
  return useMutation<IGenerateEmbeddingsResponse, Error, IGenerateEmbeddingsRequest>({
    mutationFn: SearchService.generateEmbedding,
    ...options,
  });
};

// Create entity embedding
export const useCreateEntityEmbedding = (
  options: UseMutationOptions<ICreateEntityEmbeddingResponse, Error, ICreateEntityEmbeddingRequest>,
) => {
  return useMutation<ICreateEntityEmbeddingResponse, Error, ICreateEntityEmbeddingRequest>({
    mutationFn: SearchService.createEntityEmbedding,
    ...options,
  });
};

// Update entity embeddings batch
export const useUpdateEntityEmbeddingsBatch = (
  options: UseMutationOptions<IUpdateEntityEmbeddingsBatchResponse, Error, IUpdateEntityEmbeddingsBatchRequest>,
) => {
  return useMutation<IUpdateEntityEmbeddingsBatchResponse, Error, IUpdateEntityEmbeddingsBatchRequest>({
    mutationFn: SearchService.updateEntityEmbeddingBatch,
    ...options,
  });
};
