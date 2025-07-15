import {
	UseMutationOptions,
	useMutation,
	useQueryClient,
} from "@tanstack/react-query";
import {
	ICancelPipelineRunRequest,
	ICancelPipelineRunResponse,
	ICreatePipelineRequest,
	ICreatePipelineResponse,
	IDeletePipelineRequest,
	IDeletePipelineResponse,
	IRunPipelineRequest,
	IRunPipelineResponse,
	IUpdatePipelineRequest,
	IUpdatePipelineResponse,
} from "@vbkg/types";
import { PipelineService } from "../../services/pipeline";
import { QueryKeys } from "../../config/queryKeys";

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
	const queryClient = useQueryClient();
	return useMutation<IDeletePipelineResponse, Error, IDeletePipelineRequest>({
		mutationFn: PipelineService.deletePipeline,
		...options,
		onSuccess: (data, variables, context) => {
			// Invalidate queries related to pipelines
			queryClient.invalidateQueries({
				queryKey: ["pipelines"],
			});
			options.onSuccess?.(data, variables, context);
		},
	});
};

// Run a pipeline
export const useRunPipeline = (
	options: UseMutationOptions<IRunPipelineResponse, Error, IRunPipelineRequest>,
) => {
	const queryClient = useQueryClient();
	return useMutation<IRunPipelineResponse, Error, IRunPipelineRequest>({
		mutationFn: PipelineService.runPipeline,
		...options,
		onSuccess: (data, variables, context) => {
			queryClient.invalidateQueries({
				queryKey: ["pipelineRuns", { pipeline_id: variables.id }],
			});
			options.onSuccess?.(data, variables, context);
		},
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
	const queryClient = useQueryClient();
	return useMutation<
		ICancelPipelineRunResponse,
		Error,
		ICancelPipelineRunRequest
	>({
		mutationFn: PipelineService.cancelPipelineRun,
		...options,
		onSuccess: (data, variables, context) => {
			queryClient.invalidateQueries({
				queryKey: ["pipelineRuns", { pipeline_id: variables.pipeline_id }],
			});
			options.onSuccess?.(data, variables, context);
		},
	});
};
