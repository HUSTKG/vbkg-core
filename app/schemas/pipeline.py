from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import UUID4, BaseModel, Field, validator, AnyHttpUrl


class PipelineType(str, Enum):
    EXTRACTION = "extraction"
    TRANSFORMATION = "transformation"
    LOADING = "loading"
    COMPLETE = "complete"


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStepType(str, Enum):
    FILE_READER = "file_reader"
    API_FETCHER = "api_fetcher"
    DATABASE_EXTRACTOR = "database_extractor"
    TEXT_EXTRACTOR = "text_extractor"
    LLM_ENTITY_EXTRACTOR = "llm_entity_extractor"
    FIBO_MAPPER = "fibo_mapper"
    ENTITY_RESOLUTION = "entity_resolution"
    KNOWLEDGE_GRAPH_WRITER = "knowledge_graph_writer"
    CUSTOM_PYTHON = "custom_python"


class StepConfig(BaseModel):
    """Base model for step configurations"""
    pass


class FileReaderConfig(StepConfig):
    """Configuration for reading files from storage"""
    file_id: UUID4 
    encoding: str = "utf-8"
    chunk_size: Optional[int] = None


class ApiFetcherConfig(StepConfig):
    """Configuration for fetching data from APIs"""
    url: AnyHttpUrl
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    pagination: Optional[Dict[str, Any]] = None


class DatabaseExtractorConfig(StepConfig):
    """Configuration for extracting data from databases"""
    connection_string: str
    query: str
    params: Optional[Dict[str, Any]] = None
    batch_size: int = 1000


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
    handle_conflicts: str = "keep_both"  # keep_both, keep_newest, keep_highest_confidence
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


class PipelineStep(BaseModel):
    id: UUID4 = Field(..., description="Unique ID for this step")
    name: str = Field(..., description="Human-readable name for this step")
    type: PipelineStepType
    config: Union[
        FileReaderConfig,
        ApiFetcherConfig,
        DatabaseExtractorConfig,
        TextExtractorConfig,
        LlmEntityExtractorConfig,
        FiboMapperConfig,
        EntityResolutionConfig,
        KnowledgeGraphWriterConfig,
        CustomPythonConfig,
        Dict[str, Any]
    ] = Field(default_factory=dict)
    inputs: Optional[List[str]] = None  # IDs of steps that feed into this step
    enabled: bool = True
    
    @validator('config', pre=True)
    def validate_config(cls, v, values):
        step_type = values.get('type')
        
        if not step_type:
            return v
        
        if isinstance(v, dict):
            if step_type == PipelineStepType.FILE_READER:
                return FileReaderConfig(**v)
            elif step_type == PipelineStepType.API_FETCHER:
                return ApiFetcherConfig(**v)
            elif step_type == PipelineStepType.DATABASE_EXTRACTOR:
                return DatabaseExtractorConfig(**v)
            elif step_type == PipelineStepType.TEXT_EXTRACTOR:
                return TextExtractorConfig(**v)
            elif step_type == PipelineStepType.LLM_ENTITY_EXTRACTOR:
                return LlmEntityExtractorConfig(**v)
            elif step_type == PipelineStepType.FIBO_MAPPER:
                return FiboMapperConfig(**v)
            elif step_type == PipelineStepType.ENTITY_RESOLUTION:
                return EntityResolutionConfig(**v)
            elif step_type == PipelineStepType.KNOWLEDGE_GRAPH_WRITER:
                return KnowledgeGraphWriterConfig(**v)
            elif step_type == PipelineStepType.CUSTOM_PYTHON:
                return CustomPythonConfig(**v)
        
        return v


class PipelineBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    pipeline_type: PipelineType
    steps: List[PipelineStep]
    schedule: Optional[str] = None  # CRON expression


class PipelineCreate(PipelineBase):
    pass


class PipelineUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    pipeline_type: Optional[PipelineType] = None
    steps: Optional[List[PipelineStep]] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None


class Pipeline(PipelineBase):
    id: UUID4 
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PipelineRunBase(BaseModel):
    pipeline_id: UUID4 
    status: PipelineStatus = PipelineStatus.PENDING
    triggered_by: Optional[str] = None


class PipelineRunCreate(PipelineRunBase):
    pass


class PipelineRun(PipelineRunBase):
    id: UUID4 
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # in seconds
    log: Optional[str] = None
    error_message: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PipelineStepResult(BaseModel):
    step_id: UUID4 
    status: PipelineStatus
    output: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # in seconds


class PipelineRunUpdate(BaseModel):
    status: Optional[PipelineStatus] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    log: Optional[str] = None
    error_message: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None


class PipelineRunLog(BaseModel):
    pipeline_id: UUID4 
    run_id: str
    logs: List[Dict[str, Any]]
    step_results: Dict[str, PipelineStepResult]

class PipelineRunStatus(BaseModel):
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # in seconds
    stats: Optional[Dict[str, Any]] = None
