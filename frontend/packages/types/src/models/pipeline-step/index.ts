import { PipelineRunStatus } from "../pipeline";

export enum PipelineStepType {
  // Data Acquisition Steps
  FILE_INGESTION = "file_ingestion",
  API_INGESTION = "api_ingestion",
  DATABASE_INGESTION = "database_ingestion",
  
  // Data Preprocessing Steps
  TEXT_CHUNKING = "text_chunking",
  DATA_CLEANER = "data_cleaner",
  DATA_VALIDATOR = "data_validator",
  
  // Knowledge Extraction Steps
  KNOWLEDGE_EXTRACTOR = "knowledge_extractor",
  KNOWLEDGE_MAPPING = "knowledge_mapping",
  
  // Ontology Management Steps
  ONTOLOGY_ENRICHMENT = "ontology_enrichment",
  
  // Entity Processing Steps
  ENTITY_RESOLUTION = "entity_resolution",
  ENTITY_FUSION = "entity_fusion",
  ENTITY_ENRICHMENT = "entity_enrichment",
  
  // Knowledge Graph Operations
  KG_WRITER = "kg_writer",
  KG_COMPLETION = "kg_completion",
  
  // Quality Assurance Steps
  QUALITY_MONITORING = "quality_monitoring",
  
  // Custom and Utility Steps
  CUSTOM_PYTHON = "custom_python",
}

export interface StepConfig extends Record<string, any> {
  // Common configuration
  datasource_id?: string;
  trust_score?: number;
  metadata_tracking?: boolean;
  error_handling?: string; // stop, skip, retry
  max_retries?: number;
  timeout?: number; // seconds
  
  // Incremental processing
  is_incremental?: boolean;
  incremental_field?: string;
  last_processed_value?: string;
}

export interface FileIngestionConfig extends StepConfig {
  file_paths?: string[];
  file_pattern?: string;
  encoding?: string;
  chunk_size?: number;
  supported_formats?: string[];
  extract_metadata?: boolean;
  recursive?: boolean;
}

export interface ApiIngestionConfig extends StepConfig {
  url?: string;
  method?: string;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  body?: Record<string, any>;
  auth_type?: string;
  auth_config?: Record<string, any>;
  pagination?: Record<string, any>;
  rate_limit?: Record<string, any>;
  response_format?: string;
}

export interface DatabaseIngestionConfig extends StepConfig {
  connection_string?: string;
  query: string;
  params?: Record<string, any>;
  batch_size?: number;
  parallel_connections?: number;
  streaming?: boolean;
  incremental_column?: string;
}

export interface TextChunkingConfig extends StepConfig {
  chunk_size?: number;
  chunk_overlap?: number;
  chunking_strategy?: string; // recursive, semantic, sentence
  preserve_structure?: boolean;
  min_chunk_size?: number;
  max_chunk_size?: number;
}

export interface DataCleanerConfig extends StepConfig {
  remove_duplicates?: boolean;
  normalize_text?: boolean;
  remove_empty_values?: boolean;
  standardize_formats?: boolean;
  custom_cleaning_rules?: Record<string, any>[];
  preserve_original?: boolean;
}

export interface DataValidatorConfig extends StepConfig {
  validation_rules?: Record<string, any>[];
  schema_validation?: boolean;
  quality_thresholds?: Record<string, number>;
  report_violations?: boolean;
  auto_fix?: boolean;
}

export interface KnowledgeExtractorConfig extends StepConfig {
  extraction_method?: string; // rule_based, ml, hybrid
  entity_types?: string[];
  relation_types?: string[];
  extraction_rules?: Record<string, any>[];
  confidence_threshold?: number;
}

export interface KnowledgeMappingConfig extends StepConfig {
  model?: string;
  temperature?: number;
  entity_types?: string[];
  relation_types?: string[];
  prompt_template?: string;
  max_tokens?: number;
  context_window?: number;
  batch_size?: number;
  confidence_threshold?: number;
}

export interface OntologyEnrichmentConfig extends StepConfig {
  ontology_source?: string; // custom, dbpedia, wikidata, fibo
  enrichment_strategy?: string; // mapping, alignment, merging
  similarity_threshold?: number;
  auto_enrichment?: boolean;
  manual_mappings?: Record<string, string>;
  preserve_existing?: boolean;
}

export interface EntityResolutionConfig extends StepConfig {
  resolution_strategy?: string; // exact_match, fuzzy_match, embedding, ml
  similarity_threshold?: number;
  blocking_strategy?: string; // standard, sorted_neighborhood, canopy
  blocking_keys?: string[];
  match_attributes?: string[];
  fuzzy_algorithm?: string;
  embedding_model?: string;
  batch_size?: number;
}

export interface EntityFusionConfig extends StepConfig {
  fusion_strategy?: string; // most_recent, most_frequent, weighted, custom
  conflict_resolution?: string; // keep_all, prioritize_source, vote
  source_weights?: Record<string, number>;
  preserve_provenance?: boolean;
  quality_threshold?: number;
}

export interface EntityEnrichmentConfig extends StepConfig {
  enrichment_sources?: string[];
  enrichment_types?: string[];
  enrichment_strategy?: string; // append, merge, replace
  confidence_threshold?: number;
  rate_limit?: Record<string, any>;
}

export interface KgWriterConfig extends StepConfig {
  graph_format?: string; // rdf, property_graph
  serialization?: string; // turtle, n3, json-ld
  batch_size?: number;
  create_if_not_exists?: boolean;
  update_if_exists?: string; // merge, replace, skip
  validate_before_write?: boolean;
  namespace_config?: Record<string, string>;
  compression?: boolean;
}

export interface KgCompletionConfig extends StepConfig {
  completion_method?: string; // embedding, rule_based, ml
  link_prediction?: boolean;
  entity_prediction?: boolean;
  confidence_threshold?: number;
  max_predictions?: number;
  validation_rules?: Record<string, any>[];
}

export interface QualityMonitoringConfig extends StepConfig {
  metrics?: string[];
  quality_threshold?: number;
  monitoring_frequency?: string; // batch, real_time, scheduled
  alert_thresholds?: Record<string, number>;
  report_format?: string;
}

export interface CustomPythonConfig extends StepConfig {
  code: string;
  requirements?: string[];
  input_mapping?: Record<string, string>;
  output_mapping?: Record<string, string>;
  environment?: string; // sandbox, container, native
  resource_limits?: Record<string, any>;
}

export interface IncrementalConfig {
  enabled?: boolean;
  strategy?: string; // timestamp, sequence, custom
  checkpoint_field: string;
  checkpoint_value?: string | number | Date;
  full_refresh_interval?: string;
  change_detection?: string; // polling, event, log_based
}

export interface StepDependency {
  step_id: string;
  condition?: string; // completed, any_output, custom
  custom_condition?: string;
}

export interface PipelineStepBase {
  name: string;
  step_type: PipelineStepType;
  config: StepConfig;
  run_order: number;
  description?: string;
  enabled?: boolean;
  
  // Dependencies and flow control
  depends_on?: string[];
  inputs?: string[];
  parallel_execution?: boolean;
  
  // Incremental processing
  is_incremental_capable?: boolean;
  incremental_config?: IncrementalConfig;
  
  // Error handling
  on_failure?: string; // stop, skip, retry
  max_retries?: number;
  retry_delay?: number;
  
  // Resource management
  resource_requirements?: Record<string, any>;
  timeout?: number;
}

export interface PipelineStepRunBase {
  pipeline_run_id: string;
  step_id: string;
  status: PipelineRunStatus;
  run_order: number;
  start_time?: string;
  end_time?: string;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  retry_count?: number;
  celery_task_id?: string;
}

export interface PipelineStepCreate extends PipelineStepBase {
  id?: string;
}

export interface PipelineStepRunCreate extends PipelineStepRunBase {
  // No additional fields
}

export interface PipelineStepUpdate {
  name?: string;
  step_type?: PipelineStepType;
  config?: Record<string, any>;
  run_order?: number;
  description?: string;
  enabled?: boolean;
  depends_on?: string[];
  incremental_config?: IncrementalConfig;
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
  metadata?: Record<string, any>;
}
