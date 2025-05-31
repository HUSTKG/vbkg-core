import { PipelineRunStatus } from "../pipeline";

export enum PipelineStepType {
  FILE_READER = "file_reader",
  API_FETCHER = "api_fetcher",
  DATABASE_EXTRACTOR = "database_extractor",
  TEXT_EXTRACTOR = "text_extractor",
  LLM_ENTITY_EXTRACTOR = "llm_entity_extractor",
  FIBO_MAPPER = "fibo_mapper",
  ENTITY_RESOLUTION = "entity_resolution",
  KNOWLEDGE_GRAPH_WRITER = "knowledge_graph_writer",
  CUSTOM_PYTHON = "custom_python",
}

export interface StepConfig extends Record<string, any> {
  // Base model for step configurations
}

export interface FileReaderConfig extends StepConfig {
  file_id: string; // UUID
  encoding?: string;
  chunk_size?: number;
}

export interface ApiFetcherConfig extends StepConfig {
  url: string; // AnyHttpUrl
  method?: string;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  body?: Record<string, any>;
  auth_type?: string;
  auth_config?: Record<string, any>;
  pagination?: Record<string, any>;
}

export interface DatabaseExtractorConfig extends StepConfig {
  connection_string: string;
  query: string;
  params?: Record<string, any>;
  batch_size?: number;
}

export interface TextExtractorConfig extends StepConfig {
  input_format: string; // pdf, docx, html, etc.
  extract_tables?: boolean;
  extract_metadata?: boolean;
  language?: string;
  chunk_size?: number;
  chunk_overlap?: number;
}

export interface LlmEntityExtractorConfig extends StepConfig {
  model?: string;
  temperature?: number;
  entity_types?: string[];
  prompt_template?: string;
  max_tokens?: number;
  extract_relationships?: boolean;
  context_window?: number;
}

export interface FiboMapperConfig extends StepConfig {
  mapping_confidence_threshold?: number;
  save_mappings?: boolean;
  suggest_mappings?: boolean;
  domains?: string[];
  verify_mappings?: boolean;
}

export interface EntityResolutionConfig extends StepConfig {
  resolution_strategy?: string; // exact_match, fuzzy_match, embedding
  similarity_threshold?: number;
  match_on?: string[];
  fuzzy_algorithm?: string;
  handle_conflicts?: string; // keep_both, keep_newest, keep_highest_confidence
  embedding_model?: string;
}

export interface KnowledgeGraphWriterConfig extends StepConfig {
  batch_size?: number;
  create_if_not_exists?: boolean;
  update_if_exists?: boolean;
  store_metadata?: boolean;
  track_provenance?: boolean;
  commit_strategy?: string; // batch, single, transaction
}

export interface CustomPythonConfig extends StepConfig {
  code: string;
  requirements?: string[];
  input_mapping?: Record<string, string>;
  output_mapping?: Record<string, string>;
  timeout?: number; // seconds
}

export interface PipelineStepBase {
  name: string;
  step_type: PipelineStepType;
  config: StepConfig;
  run_order: number;
  inputs: string[];
  enabled: boolean;
}

export interface PipelineStepRunBase {
  status: PipelineRunStatus;
  run_order: number;
  input_data?: Record<string, any>;
}

export interface PipelineStepCreate extends PipelineStepBase {
  id?: string;
}

export interface PipelineStepRunCreate extends PipelineStepRunBase {
  pipeline_run_id: string;
  step_id: string;
  celery_task_id?: string;
}

export interface PipelineStepUpdate {
  name?: string;
  step_type?: PipelineStepType;
  config?: Record<string, any>;
  run_order?: number;
  enabled?: boolean;
  inputs?: string[];
}

export interface PipelineStepRunUpdate {
  status?: PipelineRunStatus;
  start_time?: string;
  end_time?: string;
  output_data?: Record<string, any>;
  error_message?: string;
  retry_count?: number;
  celery_task_id?: string;
}

export interface PipelineStep extends PipelineStepBase {
  id: string;
  pipeline_id: string;
  created_at: string;
  updated_at: string;
}

export interface PipelineStepRun extends PipelineStepRunBase {
  id: string;
  pipeline_run_id: string;
  step_id: string;
  start_time?: string;
  end_time?: string;
  output_data?: Record<string, any>;
  error_message?: string;
  retry_count?: number;
  celery_task_id?: string;
  created_at: string;
}

export interface PipelineStepResult {
  step_id: string;
  status: PipelineRunStatus;
  output?: Record<string, any>;
  error_message?: string;
  start_time: string;
  end_time?: string;
  duration?: number;
}
