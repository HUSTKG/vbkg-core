import {
	ICreateDefaultVisualizationRequest,
	ICreateDefaultVisualizationResponse,
	ICreateVisualizationRequest,
	IDeleteVisualizationRequest,
	IDeleteVisualizationResponse,
	IGetVisualizationDataRequest,
	IGetVisualizationDataResponse,
	IGetVisualizationTemplatesRequest,
	IGetVisualizationTemplatesResponse,
	IReadPublicVisualizationsRequest,
	IReadPublicVisualizationsResponse,
	IReadVisualizationRequest,
	IReadVisualizationResponse,
	IReadVisualizationsRequest,
	IUpdateVisualizationRequest,
	IUpdateVisualizationResponse,
} from "@vbkg/types";
import { api } from "../config/axios";
import { API_ENDPOINTS } from "@vbkg/utils";

const createVisualization = async (input: ICreateVisualizationRequest) => {
	return await api().post<ICreateVisualizationRequest>(
		API_ENDPOINTS.CREATE_VISUALIZATION,
		input,
	);
};

const readVisualizations = async (input: IReadVisualizationsRequest) => {
	return await api().get(API_ENDPOINTS.READ_VISUALIZATIONS, {
		params: {
			...input,
		},
	});
};

const readPublicVisualizations = async (
	input: IReadPublicVisualizationsRequest,
) => {
	return await api().get<IReadPublicVisualizationsResponse>(
		API_ENDPOINTS.READ_PUBLIC_VISUALIZATIONS,
		{
			params: {
				...input,
			},
		},
	);
};

const readVisualization = async (input: IReadVisualizationRequest) => {
	return await api().get<IReadVisualizationResponse>(
		API_ENDPOINTS.READ_VISUALIZATION(input.id),
	);
};

const updateVisualization = async (input: IUpdateVisualizationRequest) => {
	return await api().put<IUpdateVisualizationResponse>(
		API_ENDPOINTS.UPDATE_VISUALIZATION(input.id),
		input,
	);
};

const deleteVisualization = async (input: IDeleteVisualizationRequest) => {
	return await api().delete<IDeleteVisualizationResponse>(
		API_ENDPOINTS.DELETE_VISUALIZATION(input.id),
	);
};

const getVisualizationData = async (input: IGetVisualizationDataRequest) => {
	return await api().get<IGetVisualizationDataResponse>(
		API_ENDPOINTS.GET_VISUALIZATION_DATA(input.id),
	);
};

const createDefaultVisualization = async (
	input: ICreateDefaultVisualizationRequest,
) => {
	return await api().post<ICreateDefaultVisualizationResponse>(
		API_ENDPOINTS.CREATE_DEFAULT_VISUALIZATION,
		input,
	);
};

const getVisualizationTemplates = async (
	input: IGetVisualizationTemplatesRequest,
) => {
	return await api().get<IGetVisualizationTemplatesResponse>(
		API_ENDPOINTS.GET_VISUALIZATION_TEMPLATES,
		{
			params: {
				...input,
			},
		},
	);
};

export const VisualizationService = {
	createVisualization,
	readVisualizations,
	readPublicVisualizations,
	readVisualization,
	updateVisualization,
	deleteVisualization,
	getVisualizationData,
	createDefaultVisualization,
	getVisualizationTemplates,
};
