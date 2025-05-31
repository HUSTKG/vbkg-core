import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  IGetDatasourceRequest,
  IGetDatasourceResponse,
  IGetDatasourcesRequest,
  IGetDatasourcesResponse,
  IGetPipelineTemplatesRequest,
  IGetPipelineTemplatesResponse,
} from "@vbkg/types";
import { QueryKeys } from "../../config/queryKeys";
import { DatasourceService } from "../../services/datasource";

// Fetch all datasources
export const useDatasources = (
  input: IGetDatasourcesRequest,
  options?: UseQueryOptions<IGetDatasourcesResponse, Error>,
) => {
  return useQuery<IGetDatasourcesResponse, Error>({
    queryKey: QueryKeys.datasources.list(input),
    queryFn: () => DatasourceService.readDatasources(input),
    ...options,
  });
};

// Fetch a specific datasource
export const useDatasource = (
  input: IGetDatasourceRequest,
  options?: Partial<UseQueryOptions<IGetDatasourceResponse, Error>>,
) => {
  return useQuery<IGetDatasourceResponse, Error>({
    queryKey: QueryKeys.datasources.details(input.id),
    queryFn: () => DatasourceService.readDatasource(input),
    ...options,
  });
};

export const usePipelineTemplates = (
  input: IGetPipelineTemplatesRequest,
  options?: UseQueryOptions<IGetPipelineTemplatesResponse, Error>,
) => {
  return useQuery<IGetPipelineTemplatesResponse, Error>({
    queryKey: QueryKeys.datasources.pipeline_templates(input.datasource_id),
    queryFn: () => DatasourceService.getPipelineTemplates(input),
    ...options,
  });
};
