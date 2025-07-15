from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.services.pipeline_step import PipelineStepService
from app.tasks.executors.graph_state import GraphState
from app.tasks.executors.step_logger import StepLogger


class PipelineExecutionError(Exception):
    """Exception raised when pipeline step execution fails"""

    pass


class BaseStepExecutor:
    """Enhanced base class với graph state support"""

    def __init__(
        self,
        step_config: Dict[str, Any],
        step_metadata: Dict[str, Any],
        graph_state: Optional[GraphState] = None,
        step_service: Optional[PipelineStepService] = None,
    ):
        self.config = step_config
        self.metadata = step_metadata
        self.step_id = step_metadata.get("step_id")
        self.step_run_id = step_metadata.get("step_run_id")
        self.step_name = step_metadata.get("step_name", "Unknown")
        self.pipeline_id = step_metadata.get("pipeline_id")
        self.pipeline_run_id = step_metadata.get("pipeline_run_id")
        self.graph_state = graph_state or GraphState()
        self.step_service = None  # Will be injected
        self.logger = None

    async def execute(
        self, input_data: Dict[str, Any], step_service: Optional[PipelineStepService]
    ) -> Dict[str, Any]:
        """Execute với detailed logging"""
        self.logger = StepLogger(
            step_name=self.step_name,
            step_run_id=self.step_run_id,
            pipeline_run_id=self.pipeline_run_id,
            step_service=step_service,
        )

        try:
            # === LOG: Prerequisites check ===
            await self.logger.info("Checking prerequisites")
            prerequisites_met = self._check_prerequisites()

            if not prerequisites_met:
                await self.logger.warning(
                    "Prerequisites not fully met, but continuing..."
                )
            else:
                await self.logger.info("All prerequisites satisfied")

            # === LOG: Input processing ===
            await self.logger.debug("Processing input data")
            self._update_graph_state_from_input(input_data)

            # === LOG: Step execution start ===
            await self.logger.info(f"Starting {self.step_name} execution")
            step_result = await self._execute_step_logic(input_data)

            # === LOG: Graph state update ===
            await self.logger.debug("Updating graph state with results")
            self._update_graph_state_from_results(step_result)

            # === LOG: Completion ===
            self.graph_state.add_step_to_history(self.step_name)
            await self.logger.info(f"{self.step_name} completed successfully")

            return {"graph_state": self.graph_state.to_dict()}

        except Exception as e:
            await self.logger.error(f"Execution failed: {str(e)}")
            raise

    async def _handle_incremental_processing(
        self, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Handle incremental processing if enabled"""
        return input_data, None

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclasses - core step logic"""
        raise NotImplementedError

    def _check_prerequisites(self) -> bool:
        """Check if prerequisites are met - override in subclasses"""
        return True

    def _update_graph_state_from_input(self, input_data: Dict[str, Any]):
        """Update graph state với data từ previous steps"""

        # Extract graph state from input if available
        if "graph_state" in input_data:
            previous_state_dict = input_data["graph_state"]
            if previous_state_dict:
                previous_state = GraphState.from_dict(previous_state_dict)

                # Merge previous state vào current state
                self.graph_state.entities = previous_state.entities
                self.graph_state.relationships = previous_state.relationships
                self.graph_state.raw_text_data = previous_state.raw_text_data
                self.graph_state.processed_chunks = previous_state.processed_chunks
                self.graph_state.cleaned_data = previous_state.cleaned_data
                self.graph_state.validation_results = previous_state.validation_results
                self.graph_state.metadata = previous_state.metadata
                self.graph_state.step_history = previous_state.step_history

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với results from current step - override in subclasses"""
        pass

    def _get_best_entities(self) -> List[Dict[str, Any]]:
        """Get best available entities từ graph state"""
        return self.graph_state.get_latest_entities()

    def _get_best_relationships(self) -> List[Dict[str, Any]]:
        """Get best available relationships từ graph state"""
        return self.graph_state.get_latest_relationships()

    def _get_best_text_data(self) -> List[Dict[str, Any]]:
        """Get best available text data"""
        return self.graph_state.get_best_text_data()

    def _track_provenance(
        self, data: Any, source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track provenance information for data"""
        return {
            "data": data,
            "provenance": {
                "step_id": self.step_id,
                "step_name": self.step_name,
                "source": source or "pipeline_step",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trust_score": self.config.get("trust_score", 0.5),
            },
        }
