import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import {
  IReadPipelinesRequest,
  IReadPipelinesResponse,
  IReadPipelineRequest,
  IReadPipelineResponse,
  IReadPipelineRunsRequest,
  IReadPipelineRunsResponse,
  IReadPipelineRunRequest,
  IReadPipelineRunResponse,
  IGetPipelineRunStatusRequest,
  IGetPipelineRunStatusResponse,
  IReadPipelineStepsRequest,
  IReadPipelineStepsResponse,
  IReadPipelineStepRequest,
  IReadPipelineStepResponse,
  IReadPipelineStepRunsRequest,
  IReadPipelineStepRunsResponse,
  IReadPipelineStepRunRequest,
  IReadPipelineStepRunResponse,
} from "@vbkg/types";
import { PipelineService } from "../../services/pipeline";

// Fetch all pipelines
export const usePipelines = (
  input: IReadPipelinesRequest,
  options?: Partial<UseQueryOptions<IReadPipelinesResponse, Error>>,
) => {
  return useQuery<IReadPipelinesResponse, Error>({
    queryKey: ["pipelines", input],
    queryFn: () => PipelineService.readPipelines(input),
    ...options,
  });
};

// Fetch a specific pipeline
export const usePipeline = (
  input: IReadPipelineRequest,
  options?: Partial<UseQueryOptions<IReadPipelineResponse, Error>>,
) => {
  return useQuery<IReadPipelineResponse, Error>({
    queryKey: ["pipeline", input.id],
    queryFn: () => PipelineService.readPipeline(input),
    ...options,
  });
};

// Fetch all pipeline runs
export const usePipelineRuns = (
  input: IReadPipelineRunsRequest,
  options?: UseQueryOptions<IReadPipelineRunsResponse, Error>,
) => {
  return useQuery<IReadPipelineRunsResponse, Error>({
    queryKey: ["pipelineRuns", input],
    queryFn: () => PipelineService.readPipelineRuns(input),
    ...options,
  });
};

// Fetch a specific pipeline run
export const usePipelineRun = (
  input: IReadPipelineRunRequest,
  options?: UseQueryOptions<IReadPipelineRunResponse, Error>,
) => {
  return useQuery<IReadPipelineRunResponse, Error>({
    queryKey: ["pipelineRun", input.id],
    queryFn: () => PipelineService.readPipelineRun(input),
    ...options,
  });
};

// Get pipeline run status
export const usePipelineRunStatus = (
  input: IGetPipelineRunStatusRequest,
  options?: UseQueryOptions<IGetPipelineRunStatusResponse, Error>,
) => {
  return useQuery<IGetPipelineRunStatusResponse, Error>({
    queryKey: ["pipelineRunStatus", input.id],
    queryFn: () => PipelineService.getPipelineRunStatus(input),
    ...options,
  });
};

export const usePipelineSteps = (
  input: IReadPipelineStepsRequest,
  options?: Partial<UseQueryOptions<IReadPipelineStepsResponse, Error>>,
) => {
  return useQuery<IReadPipelineStepsResponse, Error>({
    queryKey: ["pipelineSteps", input],
    queryFn: () => PipelineService.readPipelineSteps(input),
    ...options,
  });
};

// Fetch a specific pipeline
export const usePipelineStep = (
  input: IReadPipelineStepRequest,
  options?: Partial<UseQueryOptions<IReadPipelineStepResponse, Error>>,
) => {
  return useQuery<IReadPipelineStepResponse, Error>({
    queryKey: ["pipelineStep", input.step_id],
    queryFn: () => PipelineService.readPipelineStep(input),
    ...options,
  });
};

// Fetch all pipeline runs
export const usePipelineStepRuns = (
  input: IReadPipelineStepRunsRequest,
  options?: UseQueryOptions<IReadPipelineStepRunsResponse, Error>,
) => {
  return useQuery<IReadPipelineStepRunsResponse, Error>({
    queryKey: ["pipelineRuns", input],
    queryFn: () => PipelineService.readPipelineStepRuns(input),
    ...options,
  });
};

// Fetch a specific pipeline run
export const usePipelineStepRun = (
  input: IReadPipelineStepRunRequest,
  options?: UseQueryOptions<IReadPipelineStepRunResponse, Error>,
) => {
  return useQuery<IReadPipelineStepRunResponse, Error>({
    queryKey: ["pipelineRun", input.step_run_id],
    queryFn: () => PipelineService.readPipelineStepRun(input),
    ...options,
  });
};
