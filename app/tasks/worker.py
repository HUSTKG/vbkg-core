import asyncio
import traceback
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Optional

from celery import Celery
from celery.signals import worker_process_init
from celery.utils.log import get_task_logger

from app.core.config import settings
from app.schemas.pipeline import PipelineRunStatus, PipelineRunUpdate
from app.schemas.pipeline_step import PipelineRunStatus as StepStatus
from app.schemas.pipeline_step import (PipelineStepRunCreate,
                                       PipelineStepRunUpdate, PipelineStepType)
from app.services.pipeline_step import PipelineStepService
from app.tasks.executors import GraphState, get_step_executor

# Create Celery app
celery_app = Celery(
    "pipeline_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=4,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=7200,  # 1 hour
    task_soft_time_limit=6400,  # 50 minutes
    # Task routing
    task_routes={
        # Main pipeline tasks
        "run_pipeline": {"queue": "pipeline"},
        "run_pipeline_step": {"queue": "steps"},
        # Pipeline management tasks
        "cancel_pipeline_run": {"queue": "pipeline"},
        # Coordination tasks
        "level_completion_callback": {"queue": "pipeline"},
        "complete_pipeline": {"queue": "pipeline"},
    },
    # Set default queue for any unrouted tasks
    task_default_queue="celery",
    task_default_exchange="celery",
    task_default_routing_key="celery",
)


logger = get_task_logger(__name__)
# Create an event loop for asyncio
loop = None


@worker_process_init.connect
def setup_worker_process(*args, **kwargs):
    """Initialize the worker process."""
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)


def async_task(func):
    """Decorator to run async tasks in Celery."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        global loop
        if loop is None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(func(*args, **kwargs))

    return wrapper


@celery_app.task(name="run_pipeline", bind=True)
@async_task
async def run_pipeline_task(
    self,
    pipeline_id: str,
    run_id: str,
    user_id: Optional[str] = None,
):
    """
    Run a complete pipeline by orchestrating its steps with dependency management.

    Args:
        pipeline_id: ID of the pipeline to run
        run_id: ID of the pipeline run record (if already created)
        user_id: ID of the user triggering the pipeline
    """
    from celery import chord, group

    from app.services.pipeline import PipelineService
    from app.services.pipeline_step import PipelineStepService

    pipeline_service = PipelineService()
    step_service = PipelineStepService()

    try:
        logger.info(f"Starting pipeline {pipeline_id} execution")

        # Update pipeline run status to running
        if run_id:
            await pipeline_service.update_pipeline_run(
                run_id,
                pipeline_id=pipeline_id,
                run_update=PipelineRunUpdate(
                    status=PipelineRunStatus.RUNNING,
                    celery_task_id=self.request.id,
                ),
            )

        # Get pipeline steps ordered by run_order
        steps_response = await step_service.get_pipeline_steps(pipeline_id)
        steps = steps_response.data

        if not steps:
            raise Exception("No steps found for pipeline")

        logger.info(f"Found {len(steps)} steps in pipeline")

        # Sort steps by run_order and organize by dependency levels
        dependency_levels = organize_steps_by_dependency_levels(steps)

        logger.info(f"Pipeline will execute in {len(dependency_levels)} levels")
        for i, level in enumerate(dependency_levels):
            level_names = [step["name"] for step in level]
            logger.info(f"  Level {i+1}: {level_names}")

        # Create task chains for each dependency level
        pipeline_workflow = create_pipeline_workflow(
            dependency_levels, pipeline_id, run_id
        )

        # Execute the workflow
        result = pipeline_workflow.apply_async()

        # Store the workflow result ID for tracking
        await pipeline_service.update_pipeline_run(
            run_id,
            pipeline_id=pipeline_id,
            run_update=PipelineRunUpdate(
                celery_task_id=result.id,
            ),
        )

        return {
            "workflow_started": True,
            "workflow_id": result.id,
            "dependency_levels": len(dependency_levels),
            "total_steps": sum(len(level) for level in dependency_levels),
        }

    except Exception as e:
        error_message = f"Pipeline execution failed: {str(e)}"
        logger.error(f"Pipeline {pipeline_id} failed: {error_message}")
        logger.error(traceback.format_exc())

        # Update pipeline run as failed
        if run_id:
            await pipeline_service.update_pipeline_run(
                run_id,
                pipeline_id=pipeline_id,
                run_update=PipelineRunUpdate(
                    status=PipelineRunStatus.FAILED,
                    end_time=datetime.now(timezone.utc).isoformat(),
                    error_message=error_message,
                ),
            )

        raise Exception(error_message)


def organize_steps_by_dependency_levels(
    steps: List[Dict[str, Any]],
) -> List[List[Dict[str, Any]]]:
    """
    Organize steps into dependency levels for sequential execution.

    Args:
        steps: List of pipeline steps

    Returns:
        List of levels, each level contains steps that can run in parallel
    """
    # Create step lookup
    step_map = {step["id"]: step for step in steps}

    # Track processed steps
    processed = set()
    levels = []

    while len(processed) < len(steps):
        current_level = []

        for step in steps:
            step_id = step["id"]

            # Skip if already processed
            if step_id in processed:
                continue

            # Get dependencies - handle both "depends_on" and "inputs" fields
            dependencies = set()

            # Check "depends_on" field
            if step.get("depends_on"):
                if isinstance(step["depends_on"], list):
                    dependencies.update(step["depends_on"])
                elif isinstance(step["depends_on"], str):
                    dependencies.update(
                        [
                            dep.strip()
                            for dep in step["depends_on"].split(",")
                            if dep.strip()
                        ]
                    )

            # Check "inputs" field for backwards compatibility
            if step.get("inputs"):
                if isinstance(step["inputs"], list):
                    dependencies.update(step["inputs"])
                elif isinstance(step["inputs"], str):
                    dependencies.update(
                        [
                            dep.strip()
                            for dep in step["inputs"].split(",")
                            if dep.strip()
                        ]
                    )

            # Check if all dependencies are satisfied
            if dependencies.issubset(processed):
                current_level.append(step)

        if not current_level:
            # No progress made - circular dependency
            remaining = [s["id"] for s in steps if s["id"] not in processed]
            raise Exception(f"Circular dependency detected among steps: {remaining}")

        # Sort current level by run_order
        current_level.sort(key=lambda x: x.get("run_order", 0))
        levels.append(current_level)

        # Mark as processed
        for step in current_level:
            processed.add(step["id"])

    return levels


def create_pipeline_workflow(
    dependency_levels: List[List[Dict[str, Any]]], pipeline_id: str, run_id: str
):
    """
    Create Celery workflow for pipeline execution.
    No data is passed between tasks - everything is retrieved from database.

    Args:
        dependency_levels: Steps organized by dependency levels
        pipeline_id: Pipeline ID
        run_id: Pipeline run ID

    Returns:
        Celery workflow (chain/group/chord)
    """
    from celery import chain, chord, group

    workflow_tasks = []

    for level_idx, level_steps in enumerate(dependency_levels):
        if len(level_steps) == 1:
            # Single step - add to chain directly
            step = level_steps[0]
            task_sig = run_pipeline_step_task.si(
                pipeline_id=pipeline_id,
                step_id=step["id"],
                pipeline_run_id=run_id,
                level_index=level_idx,
            )
            workflow_tasks.append(task_sig)

        else:
            # Multiple steps in parallel - use group
            parallel_tasks = []
            for step in level_steps:
                task_sig = run_pipeline_step_task.si(
                    pipeline_id=pipeline_id,
                    step_id=step["id"],
                    pipeline_run_id=run_id,
                    level_index=level_idx,
                )
                parallel_tasks.append(task_sig)

            # Use chord to wait for all parallel tasks to complete
            level_group = group(*parallel_tasks)
            level_callback = level_completion_callback.si(
                pipeline_id=pipeline_id, pipeline_run_id=run_id, level_index=level_idx
            )
            workflow_tasks.append(chord(level_group)(level_callback))

    # Add final completion task
    workflow_tasks.append(
        complete_pipeline.si(pipeline_id=pipeline_id, pipeline_run_id=run_id)
    )

    # Create the main chain
    return chain(*workflow_tasks)


@celery_app.task(name="run_pipeline_step", bind=True)
@async_task
async def run_pipeline_step_task(
    self,
    pipeline_id: str,
    step_id: str,
    pipeline_run_id: str,
    level_index: int = 0,
):
    """
    Execute a single pipeline step with detailed logging
    """
    from app.services.pipeline_step import PipelineStepService

    step_service = PipelineStepService()
    step_run_id = None

    try:
        # === LOG: Step starting ===
        logger.info(f"Starting step {step_id} in pipeline {pipeline_id}")

        # Get step details
        step = await step_service.get_pipeline_step(step_id, pipeline_id)
        step_type = step["step_type"]
        config = step["config"] if isinstance(step["config"], str) else step["config"]

        # Create step run record
        step_run_data = PipelineStepRunCreate(
            pipeline_run_id=pipeline_run_id,
            step_id=step_id,
            status=StepStatus.RUNNING,
            run_order=step["run_order"],
            input_data={},  # Will be updated later
            celery_task_id=self.request.id,
            start_time=datetime.now(timezone.utc),
        )

        step_run = await step_service.create_step_run(step_run_data)
        step_run_id = step_run["id"]

        # === LOG: Step run created ===
        await step_service.create_step_execution_log(
            step_run_id=step_run_id,
            pipeline_run_id=pipeline_run_id,
            log_data={
                "log_level": "INFO",
                "message": f"Step run created for {step['name']} ({step_type})",
                "details": {
                    "step_id": step_id,
                    "step_name": step["name"],
                    "step_type": step_type,
                    "run_order": step["run_order"],
                    "config_keys": list(config.keys()) if config else [],
                },
            },
        )

        # === LOG: Waiting for dependencies ===
        await step_service.create_step_execution_log(
            step_run_id=step_run_id,
            pipeline_run_id=pipeline_run_id,
            log_data={
                "log_level": "INFO",
                "message": "Checking step dependencies",
                "details": {
                    "depends_on": step.get("depends_on", []),
                    "inputs": step.get("inputs", []),
                },
            },
        )

        # Wait for dependencies
        await wait_for_dependencies(step, pipeline_run_id)

        # === LOG: Dependencies ready ===
        await step_service.create_step_execution_log(
            step_run_id=step_run_id,
            pipeline_run_id=pipeline_run_id,
            log_data={
                "log_level": "INFO",
                "message": "All dependencies are ready, proceeding with execution",
            },
        )

        # Resolve input data
        resolved_input_data = await resolve_step_input_data_from_db(
            step, pipeline_run_id
        )

        # === LOG: Input data resolved ===
        await step_service.create_step_execution_log(
            step_run_id=step_run_id,
            pipeline_run_id=pipeline_run_id,
            log_data={
                "log_level": "INFO",
                "message": f"Input data resolved",
                "details": {
                    "input_data_keys": list(resolved_input_data.keys()),
                    "graph_state_available": "graph_state" in resolved_input_data,
                    "entities_count": len(
                        resolved_input_data.get("graph_state", {}).get("entities", [])
                    ),
                    "relationships_count": len(
                        resolved_input_data.get("graph_state", {}).get(
                            "relationships", []
                        )
                    ),
                },
            },
        )

        # Update step run with input data
        await step_service.update_pipeline_step_run(
            step_run_id=step_run_id,
            step_run_update=PipelineStepRunUpdate(input_data=resolved_input_data),
        )

        # === LOG: Starting step execution ===
        await step_service.create_step_execution_log(
            step_run_id=step_run_id,
            pipeline_run_id=pipeline_run_id,
            log_data={
                "log_level": "INFO",
                "message": f"Starting execution of {step_type}",
                "details": {"execution_config": config},
            },
        )

        # Execute step
        step_metadata = {
            "step_id": step_id,
            "step_name": step["name"],
            "step_run_id": step_run_id,
            "step_type": step_type,
            "pipeline_run_id": pipeline_run_id,
            "pipeline_id": pipeline_id,
        }

        output_data = await execute_step_by_type(
            step_type, config, resolved_input_data, step_metadata, step_service
        )

        start_time = datetime.fromisoformat(
            step_run["start_time"].replace("Z", "+00:00")
        )

        # === LOG: Step execution completed ===
        await step_service.create_step_execution_log(
            step_run_id=step_run_id,
            pipeline_run_id=pipeline_run_id,
            log_data={
                "log_level": "INFO",
                "message": f"Step execution completed successfully",
                "details": {
                    "output_data_size": len(str(output_data)),
                    "output_keys": (
                        list(output_data.keys())
                        if isinstance(output_data, dict)
                        else []
                    ),
                    "execution_duration": (
                        datetime.now(timezone.utc) - start_time
                    ).total_seconds(),
                },
            },
        )

        # Update step run as completed
        await step_service.update_pipeline_step_run(
            step_run_id=step_run_id,
            step_run_update=PipelineStepRunUpdate(
                status=StepStatus.COMPLETED,
                end_time=datetime.now(timezone.utc).isoformat(),
                output_data=output_data,
            ),
        )

        # === LOG: Final success ===
        await step_service.create_step_execution_log(
            step_run_id=step_run_id,
            pipeline_run_id=pipeline_run_id,
            log_data={
                "log_level": "INFO",
                "message": f"Step {step['name']} completed successfully",
                "details": {
                    "final_status": "COMPLETED",
                    "total_execution_time": (
                        datetime.now(timezone.utc) - start_time
                    ).total_seconds(),
                },
            },
        )

        return {
            "status": StepStatus.COMPLETED,
            "step_run_id": step_run_id,
            "step_id": step_id,
            "level_index": level_index,
            "pipeline_id": pipeline_id,
            "pipeline_run_id": pipeline_run_id,
            "output_size": len(str(output_data)) if output_data else 0,
        }

    except Exception as e:
        error_message = f"Step execution failed: {str(e)}"
        logger.error(f"Step {step_id} failed: {error_message}")

        # === LOG: Error occurred ===
        if step_run_id:
            await step_service.create_step_execution_log(
                step_run_id=step_run_id,
                pipeline_run_id=pipeline_run_id,
                log_data={
                    "log_level": "ERROR",
                    "message": error_message,
                    "details": {
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc(),
                    },
                },
            )

            # Update step run as failed
            await step_service.update_pipeline_step_run(
                step_run_id=step_run_id,
                step_run_update=PipelineStepRunUpdate(
                    status=StepStatus.FAILED,
                    end_time=datetime.now(timezone.utc).isoformat(),
                    error_message=error_message,
                ),
            )

        raise Exception(f"Step {step_id} execution failed: {error_message}")


async def wait_for_dependencies(
    step: Dict[str, Any],
    pipeline_run_id: str,
    timeout: int = 3600,  # 1 hour timeout
    check_interval: int = 5,  # Check every 5 seconds
) -> bool:
    """
    Wait for step dependencies to complete before executing current step.

    Args:
        step: Step configuration
        pipeline_run_id: Pipeline run ID
        timeout: Maximum wait time in seconds
        check_interval: Check interval in seconds

    Returns:
        True if dependencies are ready, raises exception if timeout or failure
    """
    # Get dependencies from both "depends_on" and "inputs" fields
    step_inputs = set()

    # Check "depends_on" field
    if step.get("depends_on"):
        if isinstance(step["depends_on"], list):
            step_inputs.update(step["depends_on"])
        elif isinstance(step["depends_on"], str) and step["depends_on"]:
            step_inputs.update(
                [s.strip() for s in step["depends_on"].split(",") if s.strip()]
            )

    # Check "inputs" field for backwards compatibility
    if step.get("inputs"):
        if isinstance(step["inputs"], list):
            step_inputs.update(step["inputs"])
        elif isinstance(step["inputs"], str) and step["inputs"]:
            step_inputs.update(
                [s.strip() for s in step["inputs"].split(",") if s.strip()]
            )

    step_inputs = list(step_inputs)  # Convert to list

    logger.info(
        f"Waiting for dependencies for step {step['id']} - inputs: {step_inputs}"
    )

    if not step_inputs:
        return True  # No dependencies

    from app.services.pipeline_step import PipelineStepService

    step_service = PipelineStepService()

    start_time = datetime.now(timezone.utc)

    while True:
        try:
            # Get all step runs for this pipeline run
            logger.debug(
                f"Checking dependencies for step {step['id']} - pipeline run ID: {pipeline_run_id}"
            )
            step_runs_response = await step_service.get_pipeline_step_runs(
                pipeline_run_id
            )
            step_runs = step_runs_response.data if step_runs_response else []

            # Create lookup map: step_id -> step_run
            step_run_map = {}
            for run in step_runs:
                step_run_map[run["step_id"]] = run

            logger.debug(
                f"Checking dependencies for step {step['id']} - found {len(step_run_map)} step runs"
            )

            # Check dependency status
            all_ready = True
            failed_deps = []

            for dep_step_id in step_inputs:
                if dep_step_id not in step_run_map:
                    all_ready = False
                    logger.debug(f"Dependency {dep_step_id} not started yet")
                    break

                dep_status = step_run_map[dep_step_id]["status"]

                if dep_status == StepStatus.FAILED:
                    failed_deps.append(dep_step_id)
                elif dep_status != StepStatus.COMPLETED:
                    all_ready = False
                    logger.debug(f"Dependency {dep_step_id} status: {dep_status}")
                    break

            if failed_deps:
                raise Exception(f"Dependencies failed: {failed_deps}")

            if all_ready:
                logger.info(f"All dependencies ready for step {step['id']}")
                return True

            # Check timeout
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            if elapsed > timeout:
                raise Exception(f"Timeout waiting for dependencies: {step_inputs}")

            # Wait before next check
            await asyncio.sleep(check_interval)

        except Exception as e:
            if "Dependencies failed" in str(e) or "Timeout waiting" in str(e):
                raise
            logger.warning(f"Error checking dependencies: {str(e)}")
            await asyncio.sleep(check_interval)


async def build_graph_state_from_dependencies(
    step: Dict[str, Any], pipeline_run_id: str
) -> GraphState:
    """
    Build GraphState từ dependency step outputs stored trong database
    """
    graph_state = GraphState()

    try:
        from app.services.pipeline_step import PipelineStepService

        step_service = PipelineStepService()

        # Get step dependencies
        step_inputs = set()

        if step.get("depends_on"):
            if isinstance(step["depends_on"], list):
                step_inputs.update(step["depends_on"])
            elif isinstance(step["depends_on"], str) and step["depends_on"]:
                step_inputs.update(
                    [s.strip() for s in step["depends_on"].split(",") if s.strip()]
                )

        if step.get("inputs"):
            if isinstance(step["inputs"], list):
                step_inputs.update(step["inputs"])
            elif isinstance(step["inputs"], str) and step["inputs"]:
                step_inputs.update(
                    [s.strip() for s in step["inputs"].split(",") if s.strip()]
                )

        step_inputs = list(step_inputs)

        if not step_inputs:
            logger.info("No dependencies found, returning empty GraphState")
            return graph_state

        # Get all completed step runs for this pipeline run
        step_runs_response = await step_service.get_pipeline_step_runs(pipeline_run_id)
        step_runs = step_runs_response.data if step_runs_response else []

        # Create lookup map: step_id -> step_run for completed steps only
        step_run_map = {}
        for run in step_runs:
            if run["status"] == StepStatus.COMPLETED and run.get("output_data"):
                step_run_map[run["step_id"]] = run

        # Build GraphState từ dependency outputs in order
        dependency_outputs = []
        for dep_step_id in step_inputs:
            if dep_step_id in step_run_map:
                step_run = step_run_map[dep_step_id]
                output_data = step_run.get("output_data", {})

                # Add step info for ordering
                dependency_outputs.append(
                    {
                        "step_id": dep_step_id,
                        "step_name": step_run.get("step_name", dep_step_id),
                        "end_time": step_run.get("end_time"),
                        "output_data": output_data,
                    }
                )

        # Sort by end_time để maintain execution order
        dependency_outputs.sort(key=lambda x: x.get("end_time", ""))

        # Build GraphState từ each dependency output
        for dep_output in dependency_outputs:
            step_name = dep_output["step_name"]
            output_data = dep_output["output_data"]

            # Extract graph_state if available
            if "graph_state" in output_data:
                dep_graph_state = GraphState.from_dict(output_data["graph_state"])

                # Merge into our graph state
                if dep_graph_state.entities:
                    graph_state.add_entities(dep_graph_state.entities, step_name)
                if dep_graph_state.relationships:
                    graph_state.add_relationships(
                        dep_graph_state.relationships, step_name
                    )
                if dep_graph_state.raw_text_data:
                    graph_state.raw_text_data = dep_graph_state.raw_text_data
                if dep_graph_state.processed_chunks:
                    graph_state.processed_chunks = dep_graph_state.processed_chunks
                if dep_graph_state.cleaned_data:
                    graph_state.cleaned_data = dep_graph_state.cleaned_data
                if dep_graph_state.validation_results:
                    graph_state.validation_results = dep_graph_state.validation_results
                if dep_graph_state.conflicts:
                    graph_state.conflicts = dep_graph_state.conflicts

                # Merge metadata và step history
                graph_state.metadata.update(dep_graph_state.metadata)
                for completed_step in dep_graph_state.step_history:
                    if completed_step not in graph_state.step_history:
                        graph_state.step_history.append(completed_step)

            # Extract data directly from step output nếu không có graph_state
            else:
                _extract_data_from_step_output(graph_state, step_name, output_data)

        logger.info(
            f"Built GraphState cho step {step['id']} - "
            f"Entities: {len(graph_state.entities)}, "
            f"Relationships: {len(graph_state.relationships)}, "
            f"Text items: {len(graph_state.get_best_text_data())}, "
            f"Completed steps: {graph_state.step_history}"
        )

        return graph_state

    except Exception as e:
        logger.error(f"Failed to build GraphState từ dependencies: {e}")
        return graph_state


def _extract_data_from_step_output(
    graph_state: GraphState, step_name: str, output_data: Dict[str, Any]
):
    """Extract data từ step output để build GraphState"""

    # Extract entities
    entities = _extract_entities_from_output(output_data)
    if entities:
        graph_state.add_entities(entities, step_name)

    # Extract relationships
    relationships = _extract_relationships_from_output(output_data)
    if relationships:
        graph_state.add_relationships(relationships, step_name)

    # Extract text data
    text_data = _extract_text_data_from_output(output_data)
    if text_data:
        if "chunks" in output_data:
            graph_state.processed_chunks = text_data
        elif "cleaned_data" in output_data:
            graph_state.cleaned_data = text_data
        elif "files" in output_data:
            graph_state.raw_text_data = text_data


def _extract_entities_from_output(output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract entities từ step output với multiple paths"""
    entities = []

    # Common paths cho entities
    paths = [
        ["extraction_result", "data", "entities"],
        ["ontology_result", "data", "enriched_entities"],
        ["resolution_result", "data", "resolved_entities"],
        ["fusion_result", "data", "fused_entities"],
        ["enrichment_result", "data", "enriched_entities"],
    ]

    for path in paths:
        value = output
        for key in path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                value = None
                break

        if value and isinstance(value, list):
            entities.extend(value)
            break  # Take first found path

    return entities


def _extract_relationships_from_output(output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract relationships từ step output"""
    relationships = []

    paths = [
        ["extraction_result", "data", "relationships"],
        ["ontology_result", "data", "enriched_relationships"],
        ["completion_result", "data", "suggested_relationships"],
    ]

    for path in paths:
        value = output
        for key in path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                value = None
                break

        if value and isinstance(value, list):
            relationships.extend(value)
            break

    return relationships


def _extract_text_data_from_output(output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract text data từ step output"""
    text_data = []

    # Check for chunks
    if "chunks" in output and isinstance(output["chunks"], list):
        for chunk in output["chunks"]:
            if isinstance(chunk, dict) and "data" in chunk:
                text_data.append(chunk["data"])

    # Check for cleaned data
    elif "cleaned_data" in output:
        cleaned = output["cleaned_data"]
        if isinstance(cleaned, dict) and "data" in cleaned:
            text_data = (
                cleaned["data"]
                if isinstance(cleaned["data"], list)
                else [cleaned["data"]]
            )

    # Check for files
    elif "files" in output and isinstance(output["files"], list):
        for file_item in output["files"]:
            if isinstance(file_item, dict) and "data" in file_item:
                file_info = file_item["data"]
                text_data.append(
                    {
                        "text": str(file_info.get("text_content", "")),
                        "source": file_info.get("file_name", "unknown"),
                        "metadata": file_info,
                    }
                )

    return text_data


async def resolve_step_input_data_from_db(
    step: Dict[str, Any], pipeline_run_id: str
) -> Dict[str, Any]:
    """
    Enhanced version với GraphState support sử dụng step output_data
    """

    # 2. Build GraphState từ dependency step outputs
    try:
        graph_state = await build_graph_state_from_dependencies(step, pipeline_run_id)

        logger.info(
            f"Enhanced input cho step {step['id']} - "
            f"GraphState entities: {len(graph_state.entities)}, "
            f"relationships: {len(graph_state.relationships)}"
        )

        # 3. Return enhanced input với both formats
        enhanced_input = {
            "graph_state": graph_state.to_dict(),
            "step_metadata": {
                "step_id": step.get("id"),
                "step_name": step.get("name"),
                "step_type": step.get("step_type"),
                "pipeline_run_id": pipeline_run_id,
            },
        }

        return enhanced_input

    except Exception as e:
        logger.error(f"Failed to build enhanced input, falling back to legacy: {e}")
        raise Exception(
            f"Failed to resolve step input data for step {step['id']}: {str(e)}"
        )


@celery_app.task(name="level_completion_callback")
@async_task
async def level_completion_callback(
    level_results: List[Dict[str, Any]],
    pipeline_id: str,
    pipeline_run_id: str,
    level_index: int,
):
    """
    Callback task executed after completing a dependency level.

    Args:
        level_results: Results from all steps in the level (minimal data)
        pipeline_id: Pipeline ID
        pipeline_run_id: Pipeline run ID
        level_index: Level index that was completed
    """
    try:
        logger.info(
            f"Completed dependency level {level_index} for pipeline {pipeline_id}"
        )

        completed_steps = []
        failed_steps = []

        for result in level_results:
            if result and isinstance(result, dict):
                if result.get("status") == StepStatus.COMPLETED:
                    completed_steps.append(result["step_id"])
                else:
                    failed_steps.append(result.get("step_id", "unknown"))

        if failed_steps:
            error_message = f"Level {level_index} failed - steps: {failed_steps}"
            logger.error(error_message)

            # Update pipeline as failed
            from app.services.pipeline import PipelineService

            pipeline_service = PipelineService()
            await pipeline_service.update_pipeline_run(
                pipeline_run_id,
                pipeline_id=pipeline_id,
                run_update=PipelineRunUpdate(
                    status=PipelineRunStatus.FAILED,
                    end_time=datetime.now(timezone.utc).isoformat(),
                    error_message=error_message,
                ),
            )

            raise Exception(error_message)

        logger.info(f"Level {level_index} completed successfully: {completed_steps}")

        # Return minimal status data
        return {
            "level_completed": True,
            "level_index": level_index,
            "completed_count": len(completed_steps),
            "pipeline_id": pipeline_id,
            "pipeline_run_id": pipeline_run_id,
        }

    except Exception as e:
        logger.error(f"Level completion callback failed: {str(e)}")
        raise


@celery_app.task(name="complete_pipeline")
@async_task
async def complete_pipeline(
    pipeline_id: str,
    pipeline_run_id: str,
):
    """
    Complete the pipeline execution.

    Args:
        pipeline_id: Pipeline ID
        pipeline_run_id: Pipeline run ID
    """
    try:
        logger.info(f"Completing pipeline {pipeline_id}")

        from app.services.pipeline import PipelineService

        pipeline_service = PipelineService()

        # Update pipeline run status to completed
        await pipeline_service.update_pipeline_run(
            pipeline_run_id,
            pipeline_id=pipeline_id,
            run_update=PipelineRunUpdate(
                status=PipelineRunStatus.COMPLETED,
                end_time=datetime.now(timezone.utc).isoformat(),
            ),
        )

        logger.info(f"Pipeline {pipeline_id} completed successfully")

        return {
            "pipeline_completed": True,
            "pipeline_id": pipeline_id,
            "pipeline_run_id": pipeline_run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        error_message = f"Pipeline completion failed: {str(e)}"
        logger.error(error_message)

        # Update as failed
        from app.services.pipeline import PipelineService

        pipeline_service = PipelineService()
        await pipeline_service.update_pipeline_run(
            pipeline_run_id,
            pipeline_id=pipeline_id,
            run_update=PipelineRunUpdate(
                status=PipelineRunStatus.FAILED,
                end_time=datetime.now(timezone.utc).isoformat(),
                error_message=error_message,
            ),
        )

        raise Exception(error_message)


async def execute_step_by_type(
    step_type: str,
    config: Dict[str, Any],
    input_data: Optional[Dict[str, Any]] = None,
    step_metadata: Optional[Dict[str, Any]] = None,
    step_service: Optional[PipelineStepService] = None,
) -> Dict[str, Any]:
    """
    Enhanced step execution với detailed logging
    """
    pipeline_run_id = step_metadata.get("pipeline_run_id") if step_metadata else None
    step_run_id = step_metadata.get("step_run_id") if step_metadata else None

    try:
        # === LOG: Pre-execution ===
        if step_service and step_run_id:
            await step_service.create_step_execution_log(
                step_run_id=step_run_id,
                pipeline_run_id=pipeline_run_id,
                log_data={
                    "log_level": "DEBUG",
                    "message": f"Initializing {step_type} executor",
                    "details": {
                        "step_type": step_type,
                        "config_provided": config is not None,
                        "input_data_provided": input_data is not None,
                    },
                },
            )

        # Extract GraphState
        graph_state_dict = input_data.get("graph_state", {}) if input_data else {}
        graph_state = GraphState.from_dict(graph_state_dict)

        # === LOG: Graph state loaded ===
        if step_service and step_run_id:
            await step_service.create_step_execution_log(
                step_run_id=step_run_id,
                pipeline_run_id=pipeline_run_id,
                log_data={
                    "log_level": "DEBUG",
                    "message": "Graph state loaded",
                    "details": {
                        "entities_count": len(graph_state.entities),
                        "relationships_count": len(graph_state.relationships),
                        "text_data_count": len(graph_state.raw_text_data),
                        "chunks_count": len(graph_state.processed_chunks),
                        "completed_steps": graph_state.step_history,
                    },
                },
            )

        # Get executor
        executor = get_step_executor(
            step_type=PipelineStepType(step_type),
            step_config=config,
            step_metadata=step_metadata or {},
            graph_state=graph_state,
        )

        # === LOG: Executor created ===
        if step_service and step_run_id:
            await step_service.create_step_execution_log(
                step_run_id=step_run_id,
                pipeline_run_id=pipeline_run_id,
                log_data={
                    "log_level": "DEBUG",
                    "message": f"Executor created for {step_type}",
                    "details": {
                        "executor_class": executor.__class__.__name__,
                        "prerequisites_met": executor._check_prerequisites(),
                    },
                },
            )

        # Execute với GraphState context
        output_data = await executor.execute(input_data, step_service)

        # === LOG: Execution successful ===
        if step_service and step_run_id:
            final_graph_state = output_data.get("graph_state", {})
            await step_service.create_step_execution_log(
                step_run_id=step_run_id,
                pipeline_run_id=pipeline_run_id,
                log_data={
                    "log_level": "INFO",
                    "message": f"Executor completed successfully",
                    "details": {
                        "output_contains_graph_state": "graph_state" in output_data,
                        "final_entities_count": len(
                            final_graph_state.get("entities", [])
                        ),
                        "final_relationships_count": len(
                            final_graph_state.get("relationships", [])
                        ),
                        "output_data_keys": list(output_data.keys()),
                    },
                },
            )

        return output_data

    except Exception as e:
        # === LOG: Execution failed ===
        if step_service and step_run_id:
            await step_service.create_step_execution_log(
                step_run_id=step_run_id,
                pipeline_run_id=pipeline_run_id,
                log_data={
                    "log_level": "ERROR",
                    "message": f"Executor failed: {str(e)}",
                    "details": {
                        "error_type": type(e).__name__,
                        "traceback": traceback.format_exc(),
                    },
                },
            )

        raise Exception(f"Failed to execute step {step_type}: {str(e)}")


@celery_app.task(name="cancel_pipeline_run")
@async_task
async def cancel_pipeline_run_task(run_id: str, pipeline_id: str = None):
    """Cancel a pipeline run and all its step tasks"""

    try:
        logger.info(f"Cancelling pipeline run {run_id}")

        # Get pipeline run details
        from app.services.pipeline import PipelineService
        from app.services.pipeline_step import PipelineStepService

        pipeline_service = PipelineService()
        step_service = PipelineStepService()

        # Get all step runs for this pipeline run
        step_runs_response = await step_service.get_pipeline_step_runs(run_id)
        step_runs = step_runs_response.data if step_runs_response else []

        # Cancel running step tasks
        for step_run in step_runs:
            if (
                step_run.get("celery_task_id")
                and step_run["status"] == StepStatus.RUNNING
            ):
                try:
                    celery_app.control.revoke(
                        step_run["celery_task_id"], terminate=True
                    )

                    # Update step run status
                    await step_service.update_pipeline_step_run(
                        run_id,
                        PipelineStepRunUpdate(
                            status=StepStatus.CANCELLED,
                            end_time=datetime.now(timezone.utc).isoformat(),
                            error_message="Cancelled by user",
                        ),
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to cancel step task {step_run['celery_task_id']}: {e}"
                    )

        # Update pipeline run status to cancelled
        await pipeline_service.update_pipeline_run(
            run_id,
            pipeline_id,
            PipelineRunUpdate(
                status=PipelineRunStatus.CANCELLED,
                end_time=datetime.now(timezone.utc).isoformat(),
                error_message="Cancelled by user",
            ),
        )

        return {"status": "cancelled", "run_id": run_id}

    except Exception as e:
        logger.error(f"Failed to cancel pipeline run {run_id}: {e}")
        raise


# Health check task
@celery_app.task(name="health_check")
def health_check():
    """Health check task for monitoring"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Test task for debugging
@celery_app.task(name="test_pipeline_task")
def test_task(message: str = "Hello from Celery"):
    """Test task for debugging"""
    logger.info(f"Test task executed: {message}")
    return {"message": message, "timestamp": datetime.now().isoformat()}
