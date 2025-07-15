import logging
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from app.tasks.executors.graph_state import GraphDataType

from .base import BaseStepExecutor, PipelineExecutionError

logger = logging.getLogger(__name__)


class DatabaseIngestionExecutor(BaseStepExecutor):
    """Enhanced Database data ingestion với graph state support"""

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.services.pipeline_step import PipelineStepService
            from app.tasks.data_ingestion import DataIngestionTask
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

            connection_string = self.config.get("connection_string")
            query = self.config.get("query")
            output_format = self.config.get("output_format", "json")
            datasource_id = self.config.get("datasource_id")
            user_id = self.config.get("user_id")

            if not connection_string or not query or not datasource_id:
                raise PipelineExecutionError(
                    "connection_string, query, and datasource_id are required for database ingestion"
                )

            # Use DataIngestionTask to handle database ingestion
            db_record = await ingestion_task.ingest_database_data(
                connection_string=connection_string,
                query=query,
                datasource_id=UUID(datasource_id),
                user_id=UUID(user_id) if user_id else None,
                output_format=output_format,
            )

            if not db_record:
                raise PipelineExecutionError("Database ingestion failed")

            result = self._track_provenance(db_record, connection_string)

            # Handle incremental processing
            db_data = {"database_result": result}
            filtered_data, incremental_info = await self._handle_incremental_processing(
                db_data
            )

            return {
                **filtered_data,
                "record_count": db_record.get("metadata", {}).get("row_count", 0),
                "incremental_info": incremental_info,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "database_ingestion",
                    "output_format": output_format,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Database ingestion execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với database data"""
        if "database_result" in step_result:
            db_data = step_result["database_result"]
            if isinstance(db_data, dict) and "data" in db_data:
                db_content = db_data["data"]
                text_data = [
                    {
                        "text": str(db_content),
                        "source": "database",
                        "metadata": db_content,
                        "provenance": db_data.get("provenance", {}),
                    }
                ]

                self.graph_state.set_text_data(
                    text_data, GraphDataType.RAW_TEXT, self.step_name
                )
