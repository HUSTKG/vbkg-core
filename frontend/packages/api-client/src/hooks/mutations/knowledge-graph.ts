import {
  useMutation,
  UseMutationOptions,
  useQueryClient,
} from "@tanstack/react-query";
import {
  IFindPathsRequest,
  IPathResponse,
  IExecuteQueryRequest,
  IExecuteQueryResponse,
} from "@vbkg/types";
import { KnowledgeGraphService } from "../../services/knowledge-graph";
import { QueryKeys } from "../../config/queryKeys";

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
