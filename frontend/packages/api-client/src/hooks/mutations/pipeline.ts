import { useMutation, UseMutationOptions } from "@tanstack/react-query";
import {
	ICreatePipelineRequest,
	ICreatePipelineResponse,
	IUpdatePipelineRequest,
	IUpdatePipelineResponse,
	IDeletePipelineRequest,
	IDeletePipelineResponse,
	IRunPipelineRequest,
	IRunPipelineResponse,
	ICancelPipelineRunRequest,
	ICancelPipelineRunResponse,
} from "@vbkg/types";
import { PipelineService } from "../../services/pipeline";

// Create a new pipeline
export const useCreatePipeline = (
	options: UseMutationOptions<
		ICreatePipelineResponse,
		Error,
		ICreatePipelineRequest
	>,
) => {
	return useMutation<ICreatePipelineResponse, Error, ICreatePipelineRequest>({
		mutationFn: PipelineService.createPipeline,
		...options,
	});
};

// Update an existing pipeline
export const useUpdatePipeline = (
	options: UseMutationOptions<
		IUpdatePipelineResponse,
		Error,
		IUpdatePipelineRequest
	>,
) => {
	return useMutation<IUpdatePipelineResponse, Error, IUpdatePipelineRequest>({
		mutationFn: PipelineService.updatePipeline,
		...options,
	});
};

// Delete a pipeline
export const useDeletePipeline = (
	options: UseMutationOptions<
		IDeletePipelineResponse,
		Error,
		IDeletePipelineRequest
	>,
) => {
	return useMutation<IDeletePipelineResponse, Error, IDeletePipelineRequest>({
		mutationFn: PipelineService.deletePipeline,
		...options,
	});
};

// Run a pipeline
export const useRunPipeline = (
	options: UseMutationOptions<IRunPipelineResponse, Error, IRunPipelineRequest>,
) => {
	return useMutation<IRunPipelineResponse, Error, IRunPipelineRequest>({
		mutationFn: PipelineService.runPipeline,
		...options,
	});
};

// Cancel a pipeline run
export const useCancelPipelineRun = (
	options: UseMutationOptions<
		ICancelPipelineRunResponse,
		Error,
		ICancelPipelineRunRequest
	>,
) => {
	return useMutation<
		ICancelPipelineRunResponse,
		Error,
		ICancelPipelineRunRequest
	>({
		mutationFn: PipelineService.cancelPipelineRun,
		...options,
	});
};
