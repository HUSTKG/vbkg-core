import {
  ApiResponse,
  PaginatedResponse,
  Pipeline,
  PipelineCreate,
  PipelineRun,
  PipelineRunStatus,
  PipelineRunWithSteps,
  PipelineStep,
  PipelineStepRun,
  PipelineUpdate,
  PipelineWithSteps,
  StartPipelineRequest,
  PipelineRunResult,
} from "../models";

// Basic Pipeline Operations
export interface IReadPipelinesRequest {
  skip?: number;
  limit?: number;
  pipeline_type?: string;
  is_active?: boolean;
}

export interface IReadPipelinesResponse extends PaginatedResponse<Pipeline> {}

export interface ICreatePipelineRequest extends PipelineCreate {}
export interface ICreatePipelineResponse extends ApiResponse<Pipeline> {}

export interface IReadPipelineRequest {
  id: string;
}

export interface IReadPipelineResponse extends ApiResponse<PipelineWithSteps> {}

export interface IUpdatePipelineRequest extends PipelineUpdate {
  id: string;
}
export interface IUpdatePipelineResponse extends ApiResponse<Pipeline> {}

export interface IDeletePipelineRequest {
  id: string;
}
export interface IDeletePipelineResponse extends ApiResponse<unknown> {}

// Pipeline Execution
export interface IRunPipelineRequest extends StartPipelineRequest {
  id: string;
}
export interface IRunPipelineResponse extends ApiResponse<PipelineRunResult> {}

// Pipeline Runs
export interface IReadPipelineRunsRequest {
  skip?: number;
  limit: number;
  pipeline_id: string;
  status?: PipelineRunStatus;
}
export interface IReadPipelineRunsResponse
  extends PaginatedResponse<PipelineRun> {}

export interface IReadPipelineRunRequest {
  id: string;
}
export interface IReadPipelineRunResponse extends ApiResponse<PipelineRunWithSteps> {}

export interface IGetPipelineRunStatusRequest {
  id: string;
}
export interface IGetPipelineRunStatusResponse
  extends ApiResponse<{ status: PipelineRunStatus; start_time?: string; end_time?: string; duration?: number }> {}

export interface ICancelPipelineRunRequest {
  id: string;
}
export interface ICancelPipelineRunResponse extends ApiResponse<null> {}

// Pipeline Steps
export interface IReadPipelineStepsRequest {
  pipeline_id: string;
}

export interface IReadPipelineStepsResponse
  extends PaginatedResponse<PipelineStep> {}

export interface IReadPipelineStepRequest {
  pipeline_id: string;
  step_id: string;
}

export interface IReadPipelineStepResponse extends ApiResponse<PipelineStep> {}

// Pipeline Step Runs
export interface IReadPipelineStepRunsRequest {
  pipeline_run_id: string;
  skip?: number;
  limit?: number;
  status?: PipelineRunStatus;
}

export interface IReadPipelineStepRunsResponse
  extends PaginatedResponse<PipelineStepRun> {}

export interface IReadPipelineStepRunRequest {
  pipeline_run_id: string;
  step_run_id: string;
}

export interface IReadPipelineStepRunResponse
  extends ApiResponse<PipelineStepRun> {}

export interface IRetryPipelineStepRunRequest {
  pipeline_run_id: string;
  step_run_id: string;
}

export interface IRetryPipelineStepRunResponse
  extends ApiResponse<PipelineStepRun> {}

// Template-based Pipeline Creation
export interface ICreatePipelineFromTemplateRequest {
  datasource_id: string;
  template_name: string;
  custom_options?: Record<string, any>;
  name_override?: string;
  description_override?: string;
  schedule?: string;
}

export interface ICreatePipelineFromTemplateResponse
  extends ApiResponse<Pipeline> {}

// Pipeline Analytics and Monitoring
export interface IGetPipelineStatsRequest {
  pipeline_id: string;
  start_date?: string;
  end_date?: string;
}

export interface IPipelineStats {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  average_duration: number;
  success_rate: number;
  last_run?: PipelineRun;
  step_failure_rates: Array<{
    step_id: string;
    step_name: string;
    failure_rate: number;
    average_duration: number;
  }>;
}

export interface IGetPipelineStatsResponse extends ApiResponse<IPipelineStats> {}

// Bulk Operations
export interface IBulkUpdatePipelinesRequest {
  pipeline_ids: string[];
  updates: PipelineUpdate;
}

export interface IBulkUpdatePipelinesResponse
  extends ApiResponse<{ updated_count: number; errors: Array<{ pipeline_id: string; error: string }> }> {}

export interface IBulkDeletePipelinesRequest {
  pipeline_ids: string[];
}

export interface IBulkDeletePipelinesResponse
  extends ApiResponse<{ deleted_count: number; errors: Array<{ pipeline_id: string; error: string }> }> {}

// Pipeline Validation
export interface IValidatePipelineRequest {
  pipeline: PipelineCreate;
}

export interface IPipelineValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  step_validations: Array<{
    step_name: string;
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  }>;
}

export interface IValidatePipelineResponse
  extends ApiResponse<IPipelineValidationResult> {}

// Pipeline Logs
export interface IGetPipelineRunLogsRequest {
  pipeline_run_id: string;
  step_id?: string;
  level?: "DEBUG" | "INFO" | "WARNING" | "ERROR";
  start_time?: string;
  end_time?: string;
}

export interface IPipelineLogEntry {
  timestamp: string;
  level: string;
  message: string;
  step_id?: string;
  step_name?: string;
  metadata?: Record<string, any>;
}

export interface IGetPipelineRunLogsResponse
  extends ApiResponse<IPipelineLogEntry[]> {}

// Pipeline Schedule Management
export interface IUpdatePipelineScheduleRequest {
  pipeline_id: string;
  schedule?: string; // CRON expression or null to disable
  timezone?: string;
}

export interface IUpdatePipelineScheduleResponse
  extends ApiResponse<{ pipeline_id: string; schedule?: string; timezone?: string; next_run?: string }> {}

export interface IGetScheduledPipelinesRequest {
  skip?: number;
  limit?: number;
  next_run_before?: string;
  next_run_after?: string;
}

export interface IScheduledPipeline extends Pipeline {
  next_run?: string;
  last_scheduled_run?: string;
}

export interface IGetScheduledPipelinesResponse
  extends PaginatedResponse<IScheduledPipeline> {}
