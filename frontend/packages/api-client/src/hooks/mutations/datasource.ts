import {
  useMutation,
  UseMutationOptions,
  useQueryClient,
} from "@tanstack/react-query";
import {
  ICreateDatasourceRequest,
  ICreateDatasourceResponse,
  ICreatePipelineFromTemplateRequest,
  ICreatePipelineFromTemplateResponse,
  IDeleteDatasourceRequest,
  IDeleteDatasourceResponse,
  IUpdateDatasourceRequest,
  IUpdateDatasourceResponse,
} from "@vbkg/types";
import { DatasourceService } from "../../services/datasource";
import { QueryKeys } from "../../config/queryKeys";

// Datasource CRUD operations
export const useCreateDatasource = (
  options: UseMutationOptions<
    ICreateDatasourceResponse,
    Error,
    ICreateDatasourceRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<
    ICreateDatasourceResponse,
    Error,
    ICreateDatasourceRequest
  >({
    mutationFn: DatasourceService.createDatasource,
    ...options,
    onSuccess: (...params) => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.datasources.list() });
      options?.onSuccess?.(...params);
    },
  });
};

export const useUpdateDatasource = (
  options: UseMutationOptions<
    IUpdateDatasourceResponse,
    Error,
    IUpdateDatasourceRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<
    IUpdateDatasourceResponse,
    Error,
    IUpdateDatasourceRequest
  >({
    mutationFn: DatasourceService.updateDatasource,
    ...options,
    onSuccess: (...params) => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.datasources.list() });
      options.onSuccess?.(...params);
    },
  });
};

export const useDeleteDatasource = (
  options: UseMutationOptions<
    IDeleteDatasourceResponse,
    Error,
    IDeleteDatasourceRequest
  >,
) => {
  const queryClient = useQueryClient();
  return useMutation<
    IDeleteDatasourceResponse,
    Error,
    IDeleteDatasourceRequest
  >({
    mutationFn: DatasourceService.deleteDatasource,
    ...options,
    onSuccess: (...params) => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.datasources.list() });
      options.onSuccess?.(...params);
    },
  });
};

export const useCreatePipelineFromTemplate = (
  options: UseMutationOptions<
    ICreatePipelineFromTemplateResponse,
    Error,
    ICreatePipelineFromTemplateRequest
  >,
) => {
  return useMutation<
    ICreatePipelineFromTemplateResponse,
    Error,
    ICreatePipelineFromTemplateRequest
  >({
    mutationFn: DatasourceService.createPipelineFromTemplate,
    ...options,
    onSuccess: (...params) => {
      options?.onSuccess?.(...params);
    },
  });
};
