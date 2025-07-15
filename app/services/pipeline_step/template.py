from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.schemas.pipeline_step import PipelineStepCreate, PipelineStepType

from .base import BasePipelineStepService
from .configuration import PipelineStepConfigurationService


class PipelineStepTemplateService(BasePipelineStepService):
    """Service for generating steps from templates"""

    def __init__(self):
        super().__init__()
        self.config_service = PipelineStepConfigurationService()

    async def generate_steps_from_template(
        self,
        datasource: Dict[str, Any],
        template: Dict[str, Any],
        custom_options: Dict[str, Any],
    ) -> List[PipelineStepCreate]:
        """Generate pipeline steps from template based on best practices"""

        steps = []
        trust_score = datasource.get("trust_score", 0.5)

        # Get step configurations from custom options
        step_configs = custom_options.get("steps", {})

        for i, step_type in enumerate(template["steps"]):
            step_key = f"{step_type}_{i}"
            step_custom_config = step_configs.get(step_key, {})

            step_config = await self.config_service.get_step_config_for_datasource(
                step_type=step_type,
                datasource=datasource,
                custom_options=custom_options,
                step_custom_config=step_custom_config,
                trust_score=trust_score,
            )

            # Determine dependencies
            inputs = []
            depends_on = []
            if i > 0:
                inputs = [f"{steps[i-1].id}"]
                depends_on = [steps[i - 1].id]

            step = PipelineStepCreate(
                id=str(uuid4()),
                name=self._get_step_display_name(step_type),
                step_type=PipelineStepType(step_type),
                config=step_config,
                run_order=i + 1,
                inputs=inputs,
                depends_on=depends_on,
                enabled=True,
                is_incremental_capable=self._is_step_incremental_capable(step_type),
                incremental_config=(
                    self._get_incremental_config(step_type, datasource)
                    if self._is_step_incremental_capable(step_type)
                    else None
                ),
            )
            steps.append(step)

        return steps

    def _get_step_display_name(self, step_type: str) -> str:
        """Get display name for step type"""
        names = {
            "file_ingestion": "File Ingestion",
            "api_ingestion": "API Data Ingestion",
            "database_ingestion": "Database Ingestion",
            "text_chunking": "Text Chunking",
            "data_cleaner": "Data Cleaner",
            "data_validator": "Data Validator",
            "knowledge_extractor": "Knowledge Extractor",
            "conflict_detection": "Conflict Detection",
            "conflict_resolution": "Conflict Resolution",
            "knowledge_mapping": "Knowledge Mapping",
            "ontology_enrichment": "Ontology Enrichment",
            "entity_resolution": "Entity Resolution",
            "entity_fusion": "Entity Fusion",
            "entity_enrichment": "Entity Enrichment",
            "kg_writer": "Knowledge Graph Writer",
            "kg_completion": "Knowledge Graph Completion",
            "quality_monitoring": "Quality Monitoring",
            "custom_python": "Custom Python Script",
        }
        return names.get(step_type, step_type.replace("_", " ").title())

    def _is_step_incremental_capable(self, step_type: str) -> bool:
        """Check if step type supports incremental processing"""
        incremental_capable_types = {
            "file_ingestion",
            "api_ingestion",
            "database_ingestion",
            "knowledge_extractor",
            "knowledge_mapping",
            "entity_resolution",
            "kg_writer",
            "quality_monitoring",
        }
        return step_type in incremental_capable_types

    def _get_incremental_config(
        self, step_type: str, datasource: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get incremental configuration for step type"""
        connection_details = datasource.get("connection_details", {})

        if step_type in ["database_ingestion", "api_ingestion"]:
            return {
                "enabled": True,
                "strategy": "timestamp",
                "checkpoint_field": connection_details.get(
                    "incremental_column", "updated_at"
                ),
                "change_detection": "polling",
            }
        elif step_type == "file_ingestion":
            return {
                "enabled": True,
                "strategy": "file_modification",
                "checkpoint_field": "file_mtime",
                "change_detection": "polling",
            }

        return None
