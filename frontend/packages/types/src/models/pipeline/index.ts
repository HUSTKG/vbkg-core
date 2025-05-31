import {
  PipelineStep,
  PipelineStepCreate,
  PipelineStepResult,
  PipelineStepRun,
} from "../pipeline-step";

export enum PipelineType {
  EXTRACTION = "extraction",
  TRANSFORMATION = "transformation",
  LOADING = "loading",
  COMPLETE = "complete",
}

export enum PipelineStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
}

export interface PipelineBase {
  name: string;
  description?: string;
  pipeline_type: PipelineType;
  steps: PipelineStep[];
  schedule?: string;
}

export interface PipelineCreate extends Omit<PipelineBase, "steps"> {
  steps: PipelineStepCreate[];
}

export interface PipelineUpdate {
  name?: string;
  description?: string;
  pipeline_type?: PipelineType;
  steps?: PipelineStep[];
  schedule?: string;
  is_active?: boolean;
}

export interface Pipeline extends PipelineBase {
  id: string; // UUID
  is_active: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface PipelineRunBase {
  pipeline_id: string; // UUID
  status: PipelineStatus;
  triggered_by?: string;
}

export interface PipelineRunCreate extends PipelineRunBase {
  // No additional fields
}

export interface PipelineRunLog {
  pipeline_id: string; // UUID
  run_id: string;
  logs: Record<string, any>[];
  step_results: Record<string, PipelineStepResult>;
}

export interface PipelineRunStatus {
  status: PipelineStatus;
  start_time: string;
  end_time?: string;
  duration?: number; // in seconds
  stats?: Record<string, any>;
}

export interface PipelineRunCreate extends PipelineRunBase {
  celery_task_id?: string;
}

export interface PipelineUpdate {
  name?: string;
  description?: string;
  pipeline_type?: PipelineType;
  schedule?: string;
  is_active?: boolean;
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
  start_time?: string;
  end_time?: string;
  duration?: number;
  result?: Record<string, any>;
  log?: string;
  error_message?: string;
  stats?: Record<string, any>;
  celery_task_id?: string;
  created_at: string;
}

export interface PipelineWithSteps {
  steps: PipelineStep[];
}

export interface PipelineRunWithSteps extends PipelineRun {
  step_runs: Array<PipelineStepRun>;
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
