import logging
from typing import Any, Dict, Optional

from app.schemas.pipeline_step import PipelineStepType
from app.tasks.executors.api_ingestion import ApiIngestionExecutor
from app.tasks.executors.conflict_detection import ConflictDetectionExecutor
from app.tasks.executors.conflict_resolution import ConflictResolutionExecutor
from app.tasks.executors.custom_python import CustomPythonExecutor
from app.tasks.executors.data_cleaner import DataCleanerExecutor
from app.tasks.executors.data_validator import DataValidatorExecutor
from app.tasks.executors.database_ingestion import DatabaseIngestionExecutor
from app.tasks.executors.entity_enrichment import EntityEnrichmentExecutor
from app.tasks.executors.entity_fusion import EntityFusionExecutor
from app.tasks.executors.entity_resolution import EntityResolutionExecutor
from app.tasks.executors.file_ingestion import FileIngestionExecutor
from app.tasks.executors.graph_state import GraphState
from app.tasks.executors.kg_completion import KgCompletionExecutor
from app.tasks.executors.kg_writer import KgWriterExecutor
from app.tasks.executors.knowledge_extractor import KnowledgeExtractorExecutor
from app.tasks.executors.ontology_enrichment import OntologyEnrichmentExecutor
from app.tasks.executors.quality_monitoring import QualityMonitoringExecutor
from app.tasks.executors.text_chunking import TextChunkingExecutor

# Initialize logging
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# Updated step executor registry
STEP_EXECUTORS = {
    PipelineStepType.FILE_INGESTION: FileIngestionExecutor,
    PipelineStepType.API_INGESTION: ApiIngestionExecutor,
    PipelineStepType.DATABASE_INGESTION: DatabaseIngestionExecutor,
    PipelineStepType.TEXT_CHUNKING: TextChunkingExecutor,
    PipelineStepType.DATA_CLEANER: DataCleanerExecutor,
    PipelineStepType.DATA_VALIDATOR: DataValidatorExecutor,
    PipelineStepType.KNOWLEDGE_EXTRACTOR: KnowledgeExtractorExecutor,
    PipelineStepType.ONTOLOGY_ENRICHMENT: OntologyEnrichmentExecutor,
    PipelineStepType.ENTITY_RESOLUTION: EntityResolutionExecutor,
    PipelineStepType.ENTITY_FUSION: EntityFusionExecutor,
    PipelineStepType.ENTITY_ENRICHMENT: EntityEnrichmentExecutor,
    PipelineStepType.KG_WRITER: KgWriterExecutor,
    PipelineStepType.KG_COMPLETION: KgCompletionExecutor,
    PipelineStepType.QUALITY_MONITORING: QualityMonitoringExecutor,
    PipelineStepType.CUSTOM_PYTHON: CustomPythonExecutor,
    PipelineStepType.CONFLICT_DETECTION: ConflictDetectionExecutor,  # For backward compatibility
    PipelineStepType.CONFLICT_RESOLUTION: ConflictResolutionExecutor,
}


def get_step_executor(
    step_type: PipelineStepType,
    step_config: Dict[str, Any],
    step_metadata: Dict[str, Any],
    graph_state: Optional[GraphState] = None,
):
    """Get enhanced executor instance với graph state support"""
    executor_class = STEP_EXECUTORS.get(step_type)
    if not executor_class:
        raise ValueError(f"No executor found for step type: {step_type}")

    # Return enhanced executor với graph state
    return executor_class(step_config, step_metadata, graph_state)
