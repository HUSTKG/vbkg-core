import logging
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from app.tasks.executors.graph_state import GraphDataType

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class FileIngestionExecutor(BaseStepExecutor):
    """Executor for file ingestion với graph state support"""

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.data_ingestion import DataIngestionTask
            from app.tasks.entity_enrichment import EntityEnrichmentTask
            from app.tasks.executors.step_logger import StepLogger

            step_service = PipelineStepService()

            logger = StepLogger(
                step_name=self.step_name,
                pipeline_run_id=self.pipeline_run_id,
                step_run_id=self.step_run_id,
                step_service=step_service,
            )

            # Initialize DataIngestionTask
            ingestion_task = DataIngestionTask(logger=logger)

            datasource_id = self.config.get("datasource_id")
            encoding = self.config.get("encoding", "utf-8")
            extract_metadata = self.config.get("extract_metadata", True)

            if not datasource_id:
                raise PipelineExecutionError(
                    "datasource_id is required for file ingestion"
                )

            await self.logger.info(
                f"Starting file ingestion for data source {datasource_id}"
            )

            # Use DataIngestionTask to handle multiple file ingestion
            ingestion_result = await ingestion_task.ingest_multiple_files(
                datasource_id=UUID(datasource_id),
                encoding=encoding,
                extract_metadata=extract_metadata,
            )

            if "error" in ingestion_result:
                raise PipelineExecutionError(
                    f"File ingestion failed: {ingestion_result['error']}"
                )

            # Process each file with provenance tracking
            processed_files = []
            for file_record in ingestion_result["processed_files"]:
                processed_files.append(
                    self._track_provenance(file_record, file_record.get("file_name"))
                )

            return {
                "files": processed_files,
                "total_files": ingestion_result["total_files"],
                "successful_files": ingestion_result["successful_files"],
                "failed_files": ingestion_result["failed_files"],
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "file_ingestion",
                    "ingestion_stats": ingestion_result.get("metadata", {}),
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"File ingestion execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với ingested file data"""
        if "files" in step_result:
            text_data = []
            for file_item in step_result["files"]:
                if isinstance(file_item, dict) and "data" in file_item:
                    file_info = file_item["data"]
                    text_data.append(
                        {
                            "text": str(file_info.get("text_content", "")),
                            "source": file_info.get("file_name", "unknown"),
                            "metadata": file_info,
                            "provenance": file_item.get("provenance", {}),
                        }
                    )

            if text_data:
                self.graph_state.set_text_data(
                    text_data, GraphDataType.RAW_TEXT, self.step_name
                )
