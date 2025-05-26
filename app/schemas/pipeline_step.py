from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator


class PipelineRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStepType(str, Enum):
    FILE_READER = "file_reader"
    API_FETCHER = "api_fetcher"
    DATABASE_EXTRACTOR = "database_extractor"
    TEXT_EXTRACTOR = "text_extractor"
    LLM_ENTITY_EXTRACTOR = "llm_entity_extractor"
    FIBO_MAPPER = "fibo_mapper"
    ENTITY_RESOLUTION = "entity_resolution"
    KNOWLEDGE_GRAPH_WRITER = "knowledge_graph_writer"
    DATA_VALIDATION = "data_validation"
    DATA_TRANSFORMATION = "data_transformation"
    CUSTOM_PYTHON = "custom_python"


class StepConfig(BaseModel):
    """Base model for step configurations"""

    pass


class FileReaderConfig(StepConfig):
    """Configuration for reading files from storage"""

    datasource_id: Optional[str] = None  # Reference to data source
    file_id: Optional[str] = None  # Direct file ID (alternative to datasource)
    encoding: str = "utf-8"
    chunk_size: Optional[int] = None
    file_filter: Optional[str] = None  # Pattern to filter files


class ApiFetcherConfig(StepConfig):
    """Configuration for fetching data from APIs"""

    datasource_id: Optional[str] = None  # Reference to data source
    url: Optional[AnyHttpUrl] = None  # Direct URL (alternative to datasource)
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    pagination: Optional[Dict[str, Any]] = None
    use_datasource_auth: bool = True  # Use auth from data source


class DatabaseExtractorConfig(StepConfig):
    """Configuration for extracting data from databases"""

    datasource_id: Optional[str] = None  # Reference to data source
    connection_string: Optional[str] = None  # Direct connection (alternative)
    query: str
    params: Optional[Dict[str, Any]] = None
    batch_size: int = 1000
    use_datasource_connection: bool = True  # Use connection from data source


class TextExtractorConfig(StepConfig):
    """Configuration for extracting text from documents"""

    input_format: str  # pdf, docx, html, etc.
    extract_tables: bool = False
    extract_metadata: bool = True
    language: Optional[str] = None
    chunk_size: int = 1000
    chunk_overlap: int = 200


class LlmEntityExtractorConfig(StepConfig):
    """Configuration for extracting entities using LLM"""

    model: str = "gpt-3.5-turbo-0125"
    temperature: float = 0.2
    entity_types: List[str] = []
    prompt_template: Optional[str] = None
    max_tokens: int = 1000
    extract_relationships: bool = False
    context_window: int = 4000


class FiboMapperConfig(StepConfig):
    """Configuration for mapping to FIBO ontology"""

    mapping_confidence_threshold: float = 0.7
    save_mappings: bool = True
    suggest_mappings: bool = True
    domains: List[str] = []
    verify_mappings: bool = False


class EntityResolutionConfig(StepConfig):
    """Configuration for resolving duplicate entities"""

    resolution_strategy: str = "exact_match"  # exact_match, fuzzy_match, embedding
    similarity_threshold: float = 0.8
    match_on: List[str] = ["text"]
    fuzzy_algorithm: Optional[str] = None
    handle_conflicts: str = (
        "keep_both"  # keep_both, keep_newest, keep_highest_confidence
    )
    embedding_model: Optional[str] = None


class KnowledgeGraphWriterConfig(StepConfig):
    """Configuration for writing to knowledge graph"""

    batch_size: int = 100
    create_if_not_exists: bool = True
    update_if_exists: bool = False
    store_metadata: bool = True
    track_provenance: bool = True
    commit_strategy: str = "batch"  # batch, single, transaction


class CustomPythonConfig(StepConfig):
    """Configuration for custom Python code execution"""

    code: str
    requirements: List[str] = []
    input_mapping: Dict[str, str] = {}
    output_mapping: Dict[str, str] = {}
    timeout: int = 60  # seconds


class PipelineStepBase(BaseModel):
    name: str = Field(..., description="Human-readable name for this step")
    step_type: PipelineStepType
    config: Dict[str, Any] = Field(..., description="Configuration for this step")
    run_order: int = Field(..., description="Execution run_order of this step")
    inputs: Optional[List[str]] = None
    enabled: bool = True
    datasource_id: Optional[str] = None  # Direct reference to data source

    @field_validator("config")
    def validate_config_with_datasource(cls, v, values):
        step_type = values.data.get("step_type")
        datasource_id = values.data.get("datasource_id")

        if not step_type:
            return v

        # If datasource_id is provided, some config fields become optional
        if isinstance(v, dict):
            if step_type == PipelineStepType.FILE_READER:
                config = FileReaderConfig(**v)
                if datasource_id and not config.datasource_id:
                    config.datasource_id = datasource_id
                return config
            elif step_type == PipelineStepType.API_FETCHER:
                config = ApiFetcherConfig(**v)
                if datasource_id and not config.datasource_id:
                    config.datasource_id = datasource_id
                return config
            elif step_type == PipelineStepType.DATABASE_EXTRACTOR:
                config = DatabaseExtractorConfig(**v)
                if datasource_id and not config.datasource_id:
                    config.datasource_id = datasource_id
                return config

        return v

class PipelineStepRunBase(BaseModel):
    status: PipelineRunStatus = PipelineRunStatus.PENDING
    run_order: int
    input_data: Optional[Dict[str, Any]] = None


# Create Models
class PipelineStepCreate(PipelineStepBase):
    id: Optional[str] = None


class PipelineStepRunCreate(PipelineStepRunBase):
    pipeline_run_id: str
    step_id: str
    celery_task_id: Optional[str] = None


# Update Models
class PipelineStepUpdate(BaseModel):
    name: Optional[str] = None
    step_type: Optional[PipelineStepType] = None
    config: Optional[Dict[str, Any]] = None
    run_order: Optional[int] = None
    enabled: Optional[bool] = None
    inputs: Optional[List[str]] = None


class PipelineStepRunUpdate(BaseModel):
    status: Optional[PipelineRunStatus] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = None
    celery_task_id: Optional[str] = None


# Response Models
class PipelineStep(PipelineStepBase):
    id: Optional[str] = None
    pipeline_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PipelineStepRun(PipelineStepRunBase):
    id: str
    pipeline_run_id: str
    step_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    celery_task_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Operational Models
class PipelineStepResult(BaseModel):
    step_id: str
    status: PipelineRunStatus
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
