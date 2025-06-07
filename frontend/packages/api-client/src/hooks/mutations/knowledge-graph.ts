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
