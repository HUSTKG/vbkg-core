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

const createDatasource = async (input: ICreateDatasourceRequest) => {
	return await api().post<ICreateDatasourceResponse>(
		API_ENDPOINTS.CREATE_DATASOURCE,
		input,
	);
};

const readDatasources = async (
	input: IGetDatasourcesRequest,
): Promise<IGetDatasourcesResponse> => {
	return await api().get(API_ENDPOINTS.READ_DATASOURCES, {
		params: {
			...input,
		},
	});
};

const readDatasource = async (input: IGetDatasourceRequest) => {
	return await api().get<IGetDatasourceResponse>(
		API_ENDPOINTS.READ_DATASOURCE(input.id),
		{
			params: {
				...input,
			},
		},
	);
};

const updateDatasource = async (input: IUpdateDatasourceRequest) => {
	return await api().patch<IUpdateDatasourceResponse>(
		API_ENDPOINTS.UPDATE_DATASOURCE(input.id),
		input,
	);
};

const deleteDatasource = async (input: IDeleteDatasourceRequest) => {
	return await api().delete<IDeleteDatasourceResponse>(
		API_ENDPOINTS.DELETE_DATASOURCE(input.id),
	);
};

const getPipelineTemplates = async (input: IGetPipelineTemplatesRequest) => {
	return await api().get<IGetPipelineTemplatesResponse>(
		API_ENDPOINTS.GET_PIPELINE_TEMPLATES(input.datasource_id),
	);
};

const createPipelineFromTemplate = async ({
	datasource_id,
	...input
}: ICreatePipelineFromTemplateRequest) => {
	return await api().post<ICreatePipelineFromTemplateResponse>(
		API_ENDPOINTS.CREATE_PIPELINE_FROM_TEMPLATE(datasource_id),
		input,
	);
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
