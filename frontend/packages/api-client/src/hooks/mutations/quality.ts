import {
  useMutation,
  UseMutationOptions,
  useQueryClient,
} from "@tanstack/react-query";
import { QueryKeys } from "../../config/queryKeys";
import { QualityService } from "../../services/quality";
import {
  IRunQualityMonitoringRequest,
  IRunQualityMonitoringResponse,
  IDetectConflictsRequest,
  IDetectConflictsResponse,
  IResolveConflictRequest,
  IResolveConflictResponse,
  IAutoResolveConflictRequest,
  IAutoResolveConflictResponse,
  IApplyKGEditRequest,
  IApplyKGEditResponse,
  IRollbackKGChangesRequest,
  IRollbackKGChangesResponse,
  IAddQualityStepsToPipelineRequest,
  IAddQualityStepsToPipelineResponse,
} from "@vbkg/types";

// Quality Monitoring
export const useRunQualityMonitoring = (
  options?: UseMutationOptions<
    IRunQualityMonitoringResponse,
    Error,
    IRunQualityMonitoringRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<
    IRunQualityMonitoringResponse,
    Error,
    IRunQualityMonitoringRequest
  >({
    mutationFn: QualityService.runQualityMonitoring,
    ...options,
    onSuccess: (...params) => {
      queryClient.invalidateQueries({
        queryKey: QueryKeys.quality.dashboard(),
      });
      options?.onSuccess?.(...params);
    },
  });
};

// Conflicts
export const useDetectConflicts = (
  options?: UseMutationOptions<
    IDetectConflictsResponse,
    Error,
    IDetectConflictsRequest | undefined
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<
    IDetectConflictsResponse,
    Error,
    IDetectConflictsRequest | undefined
  >({
    mutationFn: QualityService.detectConflicts,
    ...options,
    onSuccess: (...params) => {
      queryClient.invalidateQueries({
        queryKey: QueryKeys.quality.conflicts.list(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.quality.dashboard(),
      });
      options?.onSuccess?.(...params);
    },
  });
};

export const useResolveConflict = (
  options?: UseMutationOptions<
    IResolveConflictResponse,
    Error,
    IResolveConflictRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<IResolveConflictResponse, Error, IResolveConflictRequest>({
    mutationFn: QualityService.resolveConflict,
    ...options,
    onSuccess: (data, variables, ...params) => {
      queryClient.invalidateQueries({
        queryKey: QueryKeys.quality.conflicts.list(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.quality.dashboard(),
      });
      options?.onSuccess?.(data, variables, ...params);
    },
  });
};

export const useAutoResolveConflict = (
  options?: UseMutationOptions<
    IAutoResolveConflictResponse,
    Error,
    IAutoResolveConflictRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<
    IAutoResolveConflictResponse,
    Error,
    IAutoResolveConflictRequest
  >({
    mutationFn: QualityService.autoResolveConflict,
    ...options,
    onSuccess: (data, variables, ...params) => {
      queryClient.invalidateQueries({
        queryKey: QueryKeys.quality.conflicts.list(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.quality.dashboard(),
      });
      options?.onSuccess?.(data, variables, ...params);
    },
  });
};

// KG Editing
export const useApplyKGEdit = (
  options?: UseMutationOptions<
    IApplyKGEditResponse,
    Error,
    IApplyKGEditRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<IApplyKGEditResponse, Error, IApplyKGEditRequest>({
    mutationFn: QualityService.applyKGEdit,
    ...options,
    onSuccess: (...params) => {
      queryClient.invalidateQueries({
        queryKey: QueryKeys.knowledgeGraph.all(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.quality.dashboard(),
      });
      options?.onSuccess?.(...params);
    },
  });
};

export const useRollbackKGChanges = (
  options?: UseMutationOptions<
    IRollbackKGChangesResponse,
    Error,
    IRollbackKGChangesRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<
    IRollbackKGChangesResponse,
    Error,
    IRollbackKGChangesRequest
  >({
    mutationFn: QualityService.rollbackKGChanges,
    ...options,
    onSuccess: (...params) => {
      queryClient.invalidateQueries({
        queryKey: QueryKeys.knowledgeGraph.all(),
      });
      queryClient.invalidateQueries({
        queryKey: QueryKeys.quality.dashboard(),
      });
      options?.onSuccess?.(...params);
    },
  });
};

export const useAddQualityStepsToPipeline = (
  options?: UseMutationOptions<
    IAddQualityStepsToPipelineResponse,
    Error,
    IAddQualityStepsToPipelineRequest
  >,
) => {
  return useMutation<
    IAddQualityStepsToPipelineResponse,
    Error,
    IAddQualityStepsToPipelineRequest
  >({
    mutationFn: QualityService.addQualityStepsToPipeline,
    ...options,
  });
};
