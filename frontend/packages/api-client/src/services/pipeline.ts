import {
	ICancelPipelineRunRequest,
	ICancelPipelineRunResponse,
	ICreatePipelineRequest,
	ICreatePipelineResponse,
	IDeletePipelineRequest,
	IDeletePipelineResponse,
	IGetPipelineRunStatusRequest,
	IGetPipelineRunStatusResponse,
	IGetPipelineStepLogsRequest,
	IGetPipelineStepLogsResponse,
	IReadPipelineRequest,
	IReadPipelineResponse,
	IReadPipelineRunRequest,
	IReadPipelineRunResponse,
	IReadPipelineRunsRequest,
	IReadPipelineRunsResponse,
	IReadPipelinesRequest,
	IReadPipelinesResponse,
	IReadPipelineStepRequest,
	IReadPipelineStepResponse,
	IReadPipelineStepRunRequest,
	IReadPipelineStepRunResponse,
	IReadPipelineStepRunsRequest,
	IReadPipelineStepRunsResponse,
	IReadPipelineStepsRequest,
	IReadPipelineStepsResponse,
	IRunPipelineRequest,
	IRunPipelineResponse,
	IUpdatePipelineRequest,
	IUpdatePipelineResponse,
} from "@vbkg/types";
import { api } from "../config/axios";
import { API_ENDPOINTS } from "@vbkg/utils";

const readPipelines = async (input: IReadPipelinesRequest) => {
	return await api().get<IReadPipelinesResponse>(API_ENDPOINTS.READ_PIPELINES, {
		params: input,
	});
};

const createPipeline = async (input: ICreatePipelineRequest) => {
	return await api().post<ICreatePipelineResponse>(
		API_ENDPOINTS.CREATE_PIPELINE,
		input,
	);
};

const readPipeline = async (input: IReadPipelineRequest) => {
	return await api().get<IReadPipelineResponse>(
		API_ENDPOINTS.READ_PIPELINE(input.id),
		{
			params: input,
		},
	);
};

const updatePipeline = async (input: IUpdatePipelineRequest) => {
	return await api().put<IUpdatePipelineResponse>(
		API_ENDPOINTS.UPDATE_PIPELINE(input.id),
		input,
	);
};

const deletePipeline = async (input: IDeletePipelineRequest) => {
	return await api().delete<IDeletePipelineResponse>(
		API_ENDPOINTS.DELETE_PIPELINE(input.id),
	);
};

const runPipeline = async (input: IRunPipelineRequest) => {
	return await api().post<IRunPipelineResponse>(
		API_ENDPOINTS.RUN_PIPELINE(input.id),
		input,
	);
};

const readPipelineRuns = async ({
	pipeline_id,
	...input
}: IReadPipelineRunsRequest) => {
	return await api().get<IReadPipelineRunsResponse>(
		API_ENDPOINTS.READ_PIPELINE_RUNS(pipeline_id),
		{
			params: input,
		},
	);
};

const readPipelineRun = async (input: IReadPipelineRunRequest) => {
	return await api().get<IReadPipelineRunResponse>(
		API_ENDPOINTS.READ_PIPELINE_RUN(input.id),
		{
			params: input,
		},
	);
};

const getPipelineRunStatus = async (input: IGetPipelineRunStatusRequest) => {
	return await api().get<IGetPipelineRunStatusResponse>(
		API_ENDPOINTS.GET_PIPELINE_RUN_STATUS(input.id),
		{
			params: input,
		},
	);
};

const cancelPipelineRun = async (input: ICancelPipelineRunRequest) => {
	return await api().post<ICancelPipelineRunResponse>(
		API_ENDPOINTS.CANCEL_PIPELINE_RUN(input.pipeline_id, input.id),
	);
};

const readPipelineSteps = async ({
	pipeline_id,
	...input
}: IReadPipelineStepsRequest) => {
	return await api().get<IReadPipelineStepsResponse>(
		API_ENDPOINTS.READ_PIPELINE_STEPS(pipeline_id),
		{
			params: input,
		},
	);
};

const readPipelineStep = async (input: IReadPipelineStepRequest) => {
	return await api().get<IReadPipelineStepResponse>(
		API_ENDPOINTS.READ_PIPELINE_STEP(input.step_id, input.pipeline_id),
	);
};

const readPipelineStepRuns = async (input: IReadPipelineStepRunsRequest) => {
	return await api().get<IReadPipelineStepRunsResponse>(
		API_ENDPOINTS.READ_PIPELINE_STEP_RUNS(input.pipeline_run_id),
	);
};

const readPipelineStepRun = async (input: IReadPipelineStepRunRequest) => {
	return await api().get<IReadPipelineStepRunResponse>(
		API_ENDPOINTS.READ_PIPELINE_STEP_RUN(
			input.step_run_id,
			input.pipeline_run_id,
		),
	);
};

const readPipelineStepLogs = async (input: IGetPipelineStepLogsRequest) => {
	return await api().get<IGetPipelineStepLogsResponse>(
		API_ENDPOINTS.READ_PIPELINE_STEP_LOGS,
		{
			params: input,
		},
	);
};

export const PipelineService = {
	readPipelines,
	createPipeline,
	readPipeline,
	updatePipeline,
	deletePipeline,
	runPipeline,
	readPipelineRuns,
	readPipelineRun,
	getPipelineRunStatus,
	cancelPipelineRun,
	readPipelineSteps,
	readPipelineStep,
	readPipelineStepRuns,
	readPipelineStepRun,
	readPipelineStepLogs,
};
