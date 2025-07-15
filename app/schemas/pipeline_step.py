from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class PipelineRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStepType(str, Enum):
    # Data Acquisition Steps
    FILE_INGESTION = "file_ingestion"
    API_INGESTION = "api_ingestion"
    DATABASE_INGESTION = "database_ingestion"

    # Data Preprocessing Steps
    TEXT_CHUNKING = "text_chunking"
    DATA_CLEANER = "data_cleaner"
    DATA_VALIDATOR = "data_validator"

    # Knowledge Extraction Steps
    KNOWLEDGE_EXTRACTOR = "knowledge_extractor"  # for structured data
    KNOWLEDGE_MAPPING = "knowledge_mapping"  # for unstructured data

    # Ontology Management Steps
    ONTOLOGY_ENRICHMENT = "ontology_enrichment"

    # Entity Processing Steps
    ENTITY_RESOLUTION = "entity_resolution"
    ENTITY_FUSION = "entity_fusion"
    ENTITY_ENRICHMENT = "entity_enrichment"  # e.g., adding attributes

    # Knowledge Graph Operations
    KG_WRITER = "kg_writer"
    KG_COMPLETION = "kg_completion"

    # Quality Assurance Steps
    QUALITY_MONITORING = "quality_monitoring"

    # Custom and Utility Steps
    CUSTOM_PYTHON = "custom_python"

    CONFLICT_RESOLUTION = "conflict_resolution"  # for handling data conflicts
    CONFLICT_DETECTION = "conflict_detection"  # for detecting data conflicts


class StepConfig(BaseModel):
    """Base model for step configurations"""

    # Common configuration
    datasource_id: Optional[str] = None
    trust_score: Optional[float] = 0.5
    metadata_tracking: bool = True
    error_handling: str = "stop"  # stop, skip, retry
    max_retries: int = 3
    timeout: int = 300  # seconds

    # Incremental processing
    is_incremental: bool = False
    incremental_field: Optional[str] = None
    last_processed_value: Optional[str] = None


class FileIngestionConfig(StepConfig):
    """Configuration for file ingestion"""

    file_paths: List[str] = []
    file_pattern: Optional[str] = None
    encoding: str = "utf-8"
    chunk_size: Optional[int] = None
    supported_formats: List[str] = ["txt", "pdf", "docx", "json", "xml", "csv"]
    extract_metadata: bool = True
    recursive: bool = False


class ApiIngestionConfig(StepConfig):
    """Configuration for API data ingestion"""

    url: Optional[AnyHttpUrl] = None
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    auth_type: Optional[str] = None  # bearer, basic, api_key
    auth_config: Optional[Dict[str, Any]] = None
    pagination: Optional[Dict[str, Any]] = None
    rate_limit: Optional[Dict[str, Any]] = None
    response_format: str = "json"


class DatabaseIngestionConfig(StepConfig):
    """Configuration for database data ingestion"""

    connection_string: Optional[str] = None
    query: str
    params: Optional[Dict[str, Any]] = None
    batch_size: int = 1000
    parallel_connections: int = 1
    streaming: bool = False
    incremental_column: Optional[str] = None


class TextChunkingConfig(StepConfig):
    """Configuration for text chunking"""

    chunk_size: int = 1000
    chunk_overlap: int = 200
    chunking_strategy: str = "recursive"  # recursive, semantic, sentence
    preserve_structure: bool = True
    min_chunk_size: int = 100
    max_chunk_size: int = 2000


class DataCleanerConfig(StepConfig):
    """Configuration for data cleaning"""

    remove_duplicates: bool = True
    normalize_text: bool = True
    remove_empty_values: bool = True
    standardize_formats: bool = True
    custom_cleaning_rules: Optional[List[Dict]] = None
    preserve_original: bool = False


class DataValidatorConfig(StepConfig):
    """Configuration for data validation"""

    validation_rules: List[Dict[str, Any]] = []
    schema_validation: bool = True
    quality_thresholds: Dict[str, float] = {}
    report_violations: bool = True
    auto_fix: bool = False


class KnowledgeExtractorConfig(StepConfig):
    """Configuration for structured knowledge extraction"""

    extraction_method: str = "rule_based"  # rule_based, ml, hybrid
    entity_types: List[str] = []
    relation_types: List[str] = []
    extraction_rules: Optional[List[Dict]] = None
    confidence_threshold: float = 0.7


class KnowledgeMappingConfig(StepConfig):
    """Configuration for unstructured knowledge mapping"""

    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    entity_types: List[str] = []
    relation_types: List[str] = []
    prompt_template: Optional[str] = None
    max_tokens: int = 1000
    context_window: int = 4000
    batch_size: int = 10
    confidence_threshold: float = 0.7


class OntologyEnrichmentConfig(StepConfig):
    """Configuration for ontology enrichment"""

    ontology_source: str = "custom"  # custom, dbpedia, wikidata, fibo
    enrichment_strategy: str = "mapping"  # mapping, alignment, merging
    similarity_threshold: float = 0.8
    auto_enrichment: bool = True
    manual_mappings: Optional[Dict[str, str]] = None
    preserve_existing: bool = True


class EntityResolutionConfig(StepConfig):
    """Configuration for entity resolution"""

    resolution_strategy: str = "exact_match"  # exact_match, fuzzy_match, embedding, ml
    similarity_threshold: float = 0.8
    blocking_strategy: str = "standard"  # standard, sorted_neighborhood, canopy
    blocking_keys: List[str] = []
    match_attributes: List[str] = []
    fuzzy_algorithm: Optional[str] = "levenshtein"
    embedding_model: Optional[str] = None
    batch_size: int = 1000


class EntityFusionConfig(StepConfig):
    """Configuration for entity fusion"""

    fusion_strategy: str = "most_recent"  # most_recent, most_frequent, weighted, custom
    conflict_resolution: str = "keep_all"  # keep_all, prioritize_source, vote
    source_weights: Optional[Dict[str, float]] = None
    preserve_provenance: bool = True
    quality_threshold: float = 0.5


class EntityEnrichmentConfig(StepConfig):
    """Configuration for entity enrichment"""

    enrichment_sources: List[str] = []  # external APIs, knowledge bases
    enrichment_types: List[str] = []  # attributes, relationships, metadata
    enrichment_strategy: str = "append"  # append, merge, replace
    confidence_threshold: float = 0.7
    rate_limit: Optional[Dict[str, Any]] = None


class KgWriterConfig(StepConfig):
    """Configuration for knowledge graph writing"""

    graph_format: str = "rdf"  # rdf, property_graph
    serialization: str = "turtle"  # turtle, n3, json-ld, etc.
    batch_size: int = 1000
    create_if_not_exists: bool = True
    update_if_exists: str = "merge"  # merge, replace, skip
    validate_before_write: bool = True
    namespace_config: Optional[Dict[str, str]] = None
    compression: bool = False


class KgCompletionConfig(StepConfig):
    """Configuration for knowledge graph completion"""

    completion_method: str = "embedding"  # embedding, rule_based, ml
    link_prediction: bool = True
    entity_prediction: bool = False
    confidence_threshold: float = 0.8
    max_predictions: int = 1000
    validation_rules: Optional[List[Dict]] = None


class QualityMonitoringConfig(StepConfig):
    """Configuration for quality monitoring"""

    metrics: List[str] = ["completeness", "consistency", "accuracy"]
    quality_threshold: float = 0.8
    monitoring_frequency: str = "batch"  # batch, real_time, scheduled
    alert_thresholds: Dict[str, float] = {}
    report_format: str = "json"


class CustomPythonConfig(StepConfig):
    """Configuration for custom Python code execution"""

    code: str
    requirements: List[str] = []
    input_mapping: Dict[str, str] = {}
    output_mapping: Dict[str, str] = {}
    environment: str = "sandbox"  # sandbox, container, native
    resource_limits: Optional[Dict[str, Any]] = None


class IncrementalConfig(BaseModel):
    """Configuration for incremental processing"""

    enabled: bool = False
    strategy: str = "timestamp"  # timestamp, sequence, custom
    checkpoint_field: str
    checkpoint_value: Optional[Union[str, int, datetime]] = None
    full_refresh_interval: Optional[str] = None  # cron expression
    change_detection: str = "polling"  # polling, event, log_based


class StepDependency(BaseModel):
    """Step dependency configuration"""

    step_id: str
    condition: str = "completed"  # completed, any_output, custom
    custom_condition: Optional[str] = None


class PipelineStepBase(BaseModel):
    name: str = Field(..., description="Human-readable name for this step")
    step_type: PipelineStepType
    config: Dict[str, Any] = Field(..., description="Configuration for this step")
    run_order: int = Field(..., description="Execution order of this step")
    description: Optional[str] = None
    enabled: bool = True

    # Dependencies and flow control
    depends_on: List[str] = []  # List of step IDs this step depends on
    inputs: Optional[List[str]] = None
    parallel_execution: bool = False

    # Incremental processing
    is_incremental_capable: bool = False
    incremental_config: Optional[IncrementalConfig] = None

    # Error handling
    on_failure: str = "stop"  # stop, skip, retry
    max_retries: int = 3
    retry_delay: int = 60  # seconds

    # Resource management
    resource_requirements: Optional[Dict[str, Any]] = None
    timeout: int = 3600  # seconds

    @field_validator("config")
    def validate_step_config(cls, v, values):
        step_type = values.data.get("step_type")
        if not step_type:
            return v

        # Validate config based on step type
        config_classes = {
            PipelineStepType.FILE_INGESTION: FileIngestionConfig,
            PipelineStepType.API_INGESTION: ApiIngestionConfig,
            PipelineStepType.DATABASE_INGESTION: DatabaseIngestionConfig,
            PipelineStepType.TEXT_CHUNKING: TextChunkingConfig,
            PipelineStepType.DATA_CLEANER: DataCleanerConfig,
            PipelineStepType.DATA_VALIDATOR: DataValidatorConfig,
            PipelineStepType.KNOWLEDGE_EXTRACTOR: KnowledgeExtractorConfig,
            PipelineStepType.KNOWLEDGE_MAPPING: KnowledgeMappingConfig,
            PipelineStepType.ONTOLOGY_ENRICHMENT: OntologyEnrichmentConfig,
            PipelineStepType.ENTITY_RESOLUTION: EntityResolutionConfig,
            PipelineStepType.ENTITY_FUSION: EntityFusionConfig,
            PipelineStepType.ENTITY_ENRICHMENT: EntityEnrichmentConfig,
            PipelineStepType.KG_WRITER: KgWriterConfig,
            PipelineStepType.KG_COMPLETION: KgCompletionConfig,
            PipelineStepType.QUALITY_MONITORING: QualityMonitoringConfig,
            PipelineStepType.CUSTOM_PYTHON: CustomPythonConfig,
        }

        config_class = config_classes.get(step_type)
        if config_class and isinstance(v, dict):
            try:
                validated_config = config_class(**v)
                return validated_config.model_dump()
            except Exception as e:
                raise ValueError(f"Invalid config for {step_type}: {e}")

        return v


class PipelineStepRunBase(BaseModel):
    pipeline_run_id: str
    step_id: str
    status: PipelineRunStatus = PipelineRunStatus.PENDING
    run_order: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    celery_task_id: Optional[str] = None


class PipelineStepCreate(PipelineStepBase):
    id: Optional[str] = None


class PipelineStepRunCreate(PipelineStepRunBase):
    pass


# Update Models
class PipelineStepUpdate(BaseModel):
    name: Optional[str] = None
    step_type: Optional[PipelineStepType] = None
    config: Optional[Dict[str, Any]] = None
    run_order: Optional[int] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    depends_on: Optional[List[str]] = None
    incremental_config: Optional[IncrementalConfig] = None


class PipelineStepRunUpdate(BaseModel):
    status: Optional[PipelineRunStatus] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = None
    celery_task_id: Optional[str] = None


class PipelineStep(PipelineStepBase):
    id: str
    pipeline_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PipelineStepRun(PipelineStepRunBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class PipelineStepResult(BaseModel):
    step_id: str
    status: PipelineRunStatus
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
