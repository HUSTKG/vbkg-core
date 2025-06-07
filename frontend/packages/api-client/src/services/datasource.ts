import {
  ICreateDatasourceRequest,
  ICreateDatasourceResponse,
  ICreatePipelineFromTemplateRequest,
  ICreatePipelineFromTemplateResponse,
  IDeleteDatasourceRequest,
  IDeleteDatasourceResponse,
  IGetDatasourceRequest,
  IGetDatasourceResponse,
  IGetDatasourcesRequest,
  IGetDatasourcesResponse,
  IGetPipelineTemplatesRequest,
  IGetPipelineTemplatesResponse,
  IUpdateDatasourceRequest,
  IUpdateDatasourceResponse,
} from "@vbkg/types";

import { API_ENDPOINTS } from "@vbkg/utils";
import { api } from "../config/axios";

const createDatasource = async (
  input: ICreateDatasourceRequest,
): Promise<ICreateDatasourceResponse> => {
  return await api()
    .post<ICreateDatasourceResponse>(API_ENDPOINTS.CREATE_DATASOURCE, input)
    .then((res) => res.data);
};

const readDatasources = async (
  input: IGetDatasourcesRequest,
): Promise<IGetDatasourcesResponse> => {
  return await api()
    .get(API_ENDPOINTS.READ_DATASOURCES, {
      params: {
        ...input,
      },
    })
    .then((res) => res.data);
};

const readDatasource = async (
  input: IGetDatasourceRequest,
): Promise<IGetDatasourceResponse> => {
  return await api()
    .get<IGetDatasourceResponse>(API_ENDPOINTS.READ_DATASOURCE(input.id), {
      params: {
        ...input,
      },
    })
    .then((res) => res.data);
};

const updateDatasource = async (
  input: IUpdateDatasourceRequest,
): Promise<IUpdateDatasourceResponse> => {
  return await api()
    .patch<IUpdateDatasourceResponse>(
      API_ENDPOINTS.UPDATE_DATASOURCE(input.id),
      input,
    )
    .then((res) => res.data);
};

const deleteDatasource = async (
  input: IDeleteDatasourceRequest,
): Promise<IDeleteDatasourceResponse> => {
  return await api()
    .delete<IDeleteDatasourceResponse>(
      API_ENDPOINTS.DELETE_DATASOURCE(input.id),
    )
    .then((res) => res.data);
};

const getPipelineTemplates = async (
  input: IGetPipelineTemplatesRequest,
): Promise<IGetPipelineTemplatesResponse> => {
  return await api()
    .get<IGetPipelineTemplatesResponse>(
      API_ENDPOINTS.GET_PIPELINE_TEMPLATES(input.datasource_id),
      {
        params: {
          ...input,
        },
      },
    )
    .then((res) => res.data);
};

const createPipelineFromTemplate = async ({
  datasource_id,
  ...input
}: ICreatePipelineFromTemplateRequest): Promise<ICreatePipelineFromTemplateResponse> => {
  return await api()
    .post<ICreatePipelineFromTemplateResponse>(
      API_ENDPOINTS.CREATE_PIPELINE_FROM_TEMPLATE(datasource_id),
      input,
    )
    .then((res) => res.data);
};

export const DatasourceService = {
  createDatasource,
  readDatasources,
  readDatasource,
  updateDatasource,
  deleteDatasource,
  getPipelineTemplates,
  createPipelineFromTemplate,
};
