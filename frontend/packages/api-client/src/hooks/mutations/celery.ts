// ===== 6. Mutation Hooks - mutations/celery.ts =====
import {
  useMutation,
  UseMutationOptions,
  useQueryClient,
} from "@tanstack/react-query";
import {
  IRevokeTaskRequest,
  IRevokeTaskResponse,
  IShutdownWorkerRequest,
  IShutdownWorkerResponse,
} from "@vbkg/types";
import { CeleryService } from "../../services/celery";
import { QueryKeys } from "../../config/queryKeys";

// Revoke/terminate a task
export const useRevokeTask = (
  options?: UseMutationOptions<IRevokeTaskResponse, Error, IRevokeTaskRequest>,
) => {
  const queryClient = useQueryClient();
  return useMutation<IRevokeTaskResponse, Error, IRevokeTaskRequest>({
    mutationFn: CeleryService.revokeTask,
    ...options,
    onSuccess: (...params) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: QueryKeys.celery.tasks.all() });
      queryClient.invalidateQueries({ queryKey: QueryKeys.celery.dashboard() });
      queryClient.invalidateQueries({ queryKey: QueryKeys.celery.stats() });
      options?.onSuccess?.(...params);
    },
  });
};

// Shutdown a worker
export const useShutdownWorker = (
  options?: UseMutationOptions<
    IShutdownWorkerResponse,
    Error,
    IShutdownWorkerRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<IShutdownWorkerResponse, Error, IShutdownWorkerRequest>({
    mutationFn: CeleryService.shutdownWorker,
    ...options,
    onSuccess: (...params) => {
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: QueryKeys.celery.workers.all(),
      });
      queryClient.invalidateQueries({ queryKey: QueryKeys.celery.dashboard() });
      options?.onSuccess?.(...params);
    },
  });
};
