import {
  PipelineStep,
  PipelineStepCreate,
  PipelineStepRun,
} from "../pipeline-step";

export enum PipelineType {
  EXTRACTION = "extraction",
  TRANSFORMATION = "transformation",
  LOADING = "loading",
  COMPLETE = "complete",
}

export enum PipelineRunStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export interface PipelineBase {
  name: string;
  description?: string;
  pipeline_type: PipelineType;
  schedule?: string; // CRON expression
  is_active?: boolean;
}

export interface PipelineCreate extends PipelineBase {
  steps: PipelineStepCreate[];
}

export interface PipelineUpdate {
  name?: string;
  description?: string;
  pipeline_type?: PipelineType;
  schedule?: string;
  is_active?: boolean;
}

export interface Pipeline extends PipelineBase {
  id: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
  steps?: PipelineStep[];
}

export interface PipelineRunBase {
  pipeline_id: string;
  status: PipelineRunStatus;
  start_time?: string;
  input_parameters?: Record<string, any>;
  triggered_by?: string;
}

export interface PipelineRunCreate extends PipelineRunBase {
  celery_task_id?: string;
}

export interface PipelineRunUpdate {
  status?: PipelineRunStatus;
  end_time?: string;
  duration?: number;
  result?: Record<string, any>;
  log?: string;
  error_message?: string;
  stats?: Record<string, any>;
  celery_task_id?: string;
}

export interface PipelineRun extends PipelineRunBase {
  id: string;
  end_time?: string;
  duration?: number;
  result?: Record<string, any>;
  log?: string;
  error_message?: string;
  stats?: Record<string, any>;
  celery_task_id?: string;
  created_at: string;
}

// Extended Response Models (with relationships)
export interface PipelineWithSteps extends Pipeline {
  steps: PipelineStep[];
}

export interface PipelineRunWithSteps extends PipelineRun {
  step_runs: PipelineStepRun[];
}

export interface StartPipelineRequest {
  input_parameters?: Record<string, any>;
}

export interface PipelineRunResult {
  pipeline_run_id: string;
  celery_task_id?: string;
  status: PipelineRunStatus;
  message: string;
}

export interface PipelineCreateFromTemplate {
  datasource_id: string;
  template_name: string;
  custom_options?: Record<string, any>;
  name_override?: string;
  description_override?: string;
  schedule?: string;
}

export interface PipelineStepWithDataSource extends PipelineStep {
  datasource_id?: string;
  datasource_name?: string;
  datasource_type?: string;
}
