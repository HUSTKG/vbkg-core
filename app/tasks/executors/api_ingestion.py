from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from app.tasks.executors.graph_state import GraphDataType

from .base import BaseStepExecutor, PipelineExecutionError


class ApiIngestionExecutor(BaseStepExecutor):
    """Enhanced API data ingestion với graph state support"""

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.tasks.data_ingestion import DataIngestionTask

            # Initialize DataIngestionTask
            ingestion_task = DataIngestionTask(logger=self.logger)

            api_url = self.config.get("url")
            auth_params = self.config.get("auth_config", {})
            query_params = self.config.get("params", {})
            headers = self.config.get("headers", {})
            response_format = self.config.get("response_format", "json")
            datasource_id = self.config.get("datasource_id")
            user_id = self.config.get("user_id")

            if not api_url or not datasource_id:
                raise PipelineExecutionError(
                    "api_url and datasource_id are required for API ingestion"
                )

            # Use DataIngestionTask to handle API ingestion
            api_record = await ingestion_task.ingest_api_data(
                api_url=api_url,
                data_format=response_format,
                datasource_id=UUID(datasource_id),
                user_id=UUID(user_id) if user_id else None,
                auth_params=auth_params,
                query_params=query_params,
                headers=headers,
            )

            if not api_record:
                raise PipelineExecutionError("API ingestion failed")

            result = self._track_provenance(api_record, api_url)

            # Handle incremental processing
            api_data = {"api_response": result}
            filtered_data, incremental_info = await self._handle_incremental_processing(
                api_data
            )

            return {
                **filtered_data,
                "record_count": 1,
                "incremental_info": incremental_info,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "api_ingestion",
                    "api_url": api_url,
                    "response_format": response_format,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"API ingestion execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với API data"""
        if "api_response" in step_result:
            api_data = step_result["api_response"]
            if isinstance(api_data, dict) and "data" in api_data:
                api_content = api_data["data"]
                text_data = [
                    {
                        "text": str(api_content),
                        "source": "api",
                        "metadata": api_content,
                        "provenance": api_data.get("provenance", {}),
                    }
                ]

                self.graph_state.set_text_data(
                    text_data, GraphDataType.RAW_TEXT, self.step_name
                )
