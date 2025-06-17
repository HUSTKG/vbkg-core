import {
	UseMutationOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";
import {
	ICreateEntityRequest,
	ICreateEntityResponse,
	ICreateOrMergeEntityRequest,
	ICreateOrMergeEntityResponse,
	ICreateRelationshipRequest,
	ICreateRelationshipResponse,
	IDeleteEntityRequest,
	IDeleteEntityResponse,
	IUpdateEntityRequest,
	IUpdateEntityResponse,
	IExecuteQueryRequest,
	IExecuteQueryResponse,
	IFindPathsRequest,
	IPathResponse,
	IKGCompletionRequest,
	IKGCompletionRequestResponse,
	IKGCompletionActionResponse,
	ISuggestionActionRequest,
} from "@vbkg/types";
import { QueryKeys } from "../../config/queryKeys";
import { KnowledgeGraphService } from "../../services/knowledge-graph";

// Graph traversal mutations
export const useKGFindPaths = (
	options?: UseMutationOptions<IPathResponse[], Error, IFindPathsRequest>,
) => {
	const queryClient = useQueryClient();
	return useMutation<IPathResponse[], Error, IFindPathsRequest>({
		mutationFn: KnowledgeGraphService.findPaths,
		...options,
		onSuccess: (data, variables, context) => {
			// Optionally invalidate related queries
			queryClient.invalidateQueries({
				queryKey: QueryKeys.knowledgeGraph.entity(variables.source_entity_id),
			});
			queryClient.invalidateQueries({
				queryKey: QueryKeys.knowledgeGraph.entity(variables.target_entity_id),
			});
			options?.onSuccess?.(data, variables, context);
		},
	});
};

export const useKGExecuteQuery = (
	options?: UseMutationOptions<
		IExecuteQueryResponse,
		Error,
		IExecuteQueryRequest
	>,
) => {
	const queryClient = useQueryClient();
	return useMutation<IExecuteQueryResponse, Error, IExecuteQueryRequest>({
		mutationFn: KnowledgeGraphService.executeQuery,
		...options,
		onSuccess: (data, variables, context) => {
			// Custom queries might affect various parts of the graph
			// Invalidate stats and related queries based on query type
			if (variables.cypher_query.toUpperCase().includes("MATCH")) {
				// For read queries, we might want to refresh stats
				queryClient.invalidateQueries({
					queryKey: QueryKeys.knowledgeGraph.stats(),
				});
			}
			options?.onSuccess?.(data, variables, context);
		},
	});
};

// Create entity
export const useCreateEntity = (
	options: UseMutationOptions<
		ICreateEntityResponse,
		Error,
		ICreateEntityRequest
	>,
) => {
	const queryClient = useQueryClient();
	return useMutation<ICreateEntityResponse, Error, ICreateEntityRequest>({
		mutationFn: KnowledgeGraphService.createEntityRequest,
		...options,
		onSuccess: (data, vars, ...params) => {
			queryClient.invalidateQueries({
				queryKey: QueryKeys.knowledgeGraph.entitiesSearch({}),
			});
			if (options.onSuccess) {
				options.onSuccess(data, vars, ...params);
			}
		},
	});
};

// Update entity
export const useUpdateEntity = (
	options: UseMutationOptions<
		IUpdateEntityResponse,
		Error,
		IUpdateEntityRequest
	>,
) => {
	const queryClient = useQueryClient();
	return useMutation<IUpdateEntityResponse, Error, IUpdateEntityRequest>({
		mutationFn: KnowledgeGraphService.updateEntity,
		...options,
		onSuccess: (data, vars, ...params) => {
			queryClient.invalidateQueries({
				queryKey: QueryKeys.knowledgeGraph.entitiesSearch({}),
			});
			queryClient.invalidateQueries({
				queryKey: QueryKeys.knowledgeGraph.entity(vars.id),
			});
			if (options.onSuccess) {
				options.onSuccess(data, vars, ...params);
			}
		},
	});
};

// Delete entity
export const useDeleteEntity = (
	options: UseMutationOptions<
		IDeleteEntityResponse,
		Error,
		IDeleteEntityRequest
	>,
) => {
	const queryClient = useQueryClient();
	return useMutation<IDeleteEntityResponse, Error, IDeleteEntityRequest>({
		mutationFn: KnowledgeGraphService.deleteEntity,
		...options,
		onSuccess: (data, vars, ...params) => {
			queryClient.invalidateQueries({
				queryKey: QueryKeys.knowledgeGraph.entitiesSearch({}),
			});
			queryClient.invalidateQueries({
				queryKey: QueryKeys.knowledgeGraph.entity(vars.id),
			});
			if (options.onSuccess) {
				options.onSuccess(data, vars, ...params);
			}
		},
	});
};

// Create relationship
export const useCreateRelationship = (
	options: UseMutationOptions<
		ICreateRelationshipResponse,
		Error,
		ICreateRelationshipRequest
	>,
) => {
	return useMutation<
		ICreateRelationshipResponse,
		Error,
		ICreateRelationshipRequest
	>({
		mutationFn: KnowledgeGraphService.createRelationship,
		...options,
	});
};

// Create or merge entity
export const useCreateOrMergeEntity = (
	options: UseMutationOptions<
		ICreateOrMergeEntityResponse,
		Error,
		ICreateOrMergeEntityRequest
	>,
) => {
	return useMutation<
		ICreateOrMergeEntityResponse,
		Error,
		ICreateOrMergeEntityRequest
	>({
		mutationFn: KnowledgeGraphService.createOrMergeEntity,
		...options,
	});
};

// =============================================
// MUTATION HOOKS
// =============================================

// Generate KG Completion
export const useGenerateKGCompletion = (
  options?: UseMutationOptions<
    IKGCompletionRequestResponse,
    Error,
    IKGCompletionRequest
  >,
) => {
  const queryClient = useQueryClient();
  
  return useMutation<IKGCompletionRequestResponse, Error, IKGCompletionRequest>({
    mutationFn: KnowledgeGraphService.generateKGCompletion,
    onSuccess: (data, variables, context) => {
      // Invalidate suggestions and stats queries
      queryClient.invalidateQueries({
        queryKey: QueryKeys.knowledgeGraph.completionSuggestions({}),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.knowledgeGraph.completionStats(),
      });
      
      // If auto-apply was enabled, also invalidate entity/relationship queries
      if (variables.auto_apply_suggestions) {
        queryClient.invalidateQueries({
          queryKey: QueryKeys.knowledgeGraph.entitiesSearch({}),
        });
        queryClient.invalidateQueries({
          queryKey: QueryKeys.knowledgeGraph.relationshipsSearch({}),
        });
        queryClient.invalidateQueries({
          queryKey: QueryKeys.knowledgeGraph.stats(),
        });
      }
      
      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

// Handle suggestion actions (accept, reject, apply)
export const useHandleSuggestionAction = (
  options?: UseMutationOptions<
    IKGCompletionActionResponse,
    Error,
    ISuggestionActionRequest
  >,
) => {
  const queryClient = useQueryClient();
  
  return useMutation<IKGCompletionActionResponse, Error, ISuggestionActionRequest>({
    mutationFn: KnowledgeGraphService.handleSuggestionAction,
    onSuccess: (data, variables, context) => {
      // Invalidate suggestions and stats
      queryClient.invalidateQueries({
        queryKey: QueryKeys.knowledgeGraph.completionSuggestions({}),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.knowledgeGraph.completionStats(),
      });
      
      // If action was 'apply', also invalidate entity/relationship queries
      if (variables.action === 'apply') {
        queryClient.invalidateQueries({
          queryKey: QueryKeys.knowledgeGraph.entitiesSearch({}),
        });
        queryClient.invalidateQueries({
          queryKey: QueryKeys.knowledgeGraph.relationshipsSearch({}),
        });
        queryClient.invalidateQueries({
          queryKey: QueryKeys.knowledgeGraph.stats(),
        });
      }
      
      // Invalidate individual suggestion queries for the affected suggestions
      variables.suggestion_ids.forEach(id => {
        queryClient.invalidateQueries({
          queryKey: QueryKeys.knowledgeGraph.completionSuggestion(id),
        });
      });
      
      options?.onSuccess?.(data, variables, context);
    },
    ...options,
  });
};

// Delete suggestion
export const useDeleteSuggestion = (
  options?: UseMutationOptions<IKGCompletionActionResponse, Error, string>,
) => {
  const queryClient = useQueryClient();
  
  return useMutation<IKGCompletionActionResponse, Error, string>({
    mutationFn: KnowledgeGraphService.deleteSuggestion,
    onSuccess: (data, suggestionId, context) => {
      // Remove the suggestion from cache
      queryClient.removeQueries({
        queryKey: QueryKeys.knowledgeGraph.completionSuggestion(suggestionId),
      });
      
      // Invalidate suggestions list and stats
      queryClient.invalidateQueries({
        queryKey: QueryKeys.knowledgeGraph.completionSuggestions({}),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.knowledgeGraph.completionStats(),
      });
      
      options?.onSuccess?.(data, suggestionId, context);
    },
    ...options,
  });
};

export const useBulkDeleteSuggestions = (
  options?: UseMutationOptions<void, Error, string[]>,
) => {
  const queryClient = useQueryClient();
  
  return useMutation<void, Error, string[]>({
    mutationFn: async (suggestionIds: string[]) => {
      // Delete all suggestions in parallel
      await Promise.all(
        suggestionIds.map(id => KnowledgeGraphService.deleteSuggestion(id))
      );
    },
    onSuccess: (data, suggestionIds, context) => {
      // Remove suggestions from cache
      suggestionIds.forEach(id => {
        queryClient.removeQueries({
          queryKey: QueryKeys.knowledgeGraph.completionSuggestion(id),
        });
      });
      
      // Invalidate suggestions list and stats
      queryClient.invalidateQueries({
        queryKey: QueryKeys.knowledgeGraph.completionSuggestions({}),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.knowledgeGraph.completionStats(),
      });
      
      options?.onSuccess?.(data, suggestionIds, context);
    },
    ...options,
  });
};
