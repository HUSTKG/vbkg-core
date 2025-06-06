import asyncio
import json
import os
import re
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from celery import Celery
from celery.signals import worker_process_init
from celery.utils.log import get_task_logger
from six import u

from app.core.config import settings
from app.schemas.pipeline import PipelineRunStatus, PipelineRunUpdate
from app.schemas.pipeline_step import PipelineRunStatus as StepStatus
from app.schemas.pipeline_step import PipelineStepType
from app.services.fibo import FIBOService

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
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    # FIXED ROUTING - Use the actual task names from @celery_app.task(name="...")
    task_routes={
        # Main pipeline tasks
        "run_pipeline": {"queue": "pipeline"},
        "run_pipeline_step": {"queue": "steps"},
        # Pipeline management tasks
        "cancel_pipeline_run": {"queue": "pipeline"},
        # Data processing tasks
        "process_file": {"queue": "steps"},
        "sync_to_neo4j": {"queue": "steps"},
        "detect_conflicts": {"queue": "steps"},
        # Test tasks (optional - you can remove if not needed)
        "test_pipeline_task": {"queue": "pipeline"},
    },
    # Set default queue for any unrouted tasks (optional)
    task_default_queue="celery",
    task_default_exchange="celery",
    task_default_routing_key="celery",
)

# Initialize logger
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

        # Sort steps by run_order and organize by dependency levels
        dependency_levels = organize_steps_by_dependency_levels(steps)

        # Create task chains for each dependency level (simplified - no data passing)
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

        return False


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

            # Check if all dependencies are satisfied
            dependencies = set(step.get("inputs", []))
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
    Execute a single pipeline step with dependency resolution from database.
    All input data is retrieved from database, not passed via Celery.

    Args:
        pipeline_id: ID of the pipeline
        step_id: ID of the step to run
        pipeline_run_id: ID of the pipeline run
        level_index: Dependency level index
    """
    from app.services.pipeline import PipelineService
    from app.services.pipeline_step import PipelineStepService

    step_service = PipelineStepService()
    pipeline_service = PipelineService()
    step_run_id = None

    try:
        logger.info(
            f"Starting step {step_id} in pipeline {pipeline_id} (level {level_index})"
        )

        # Get step details
        step = await step_service.get_pipeline_step(step_id, pipeline_id)
        step_type = step["step_type"]
        config = (
            json.loads(step["config"])
            if isinstance(step["config"], str)
            else step["config"]
        )

        logger.info(
            f"Step type: {step_type}, config: {config}, inputs: {step['inputs']}"
        )

        # Wait for dependencies to complete (if any)
        await wait_for_dependencies(step, pipeline_run_id)

        logger.info(f"Dependencies ready for step {step_id}")

        # Resolve input data from dependencies (retrieved from database)
        resolved_input_data = await resolve_step_input_data_from_db(
            step, pipeline_run_id
        )

        logger.info(
            f"Resolved input data for step {step_id}: {len(resolved_input_data)} keys"
        )

        # Create step run record
        step_run_data = {
            "pipeline_run_id": pipeline_run_id,
            "step_id": step_id,
            "status": StepStatus.RUNNING,
            "run_order": step["run_order"],
            "input_data": resolved_input_data,
            "celery_task_id": self.request.id,
            "start_time": datetime.now(timezone.utc).isoformat(),
        }

        step_run = await step_service.create_step_run(step_run_data)
        step_run_id = step_run["id"]

        logger.info(f"Step run created with ID {step_run_id}")

        # Execute step based on type
        output_data = await execute_step_by_type(step_type, config, resolved_input_data)

        logger.info(
            f"Step {step_id} executed successfully, output size: {len(str(output_data))} characters"
        )

        # Update step run as completed
        await step_service.update_pipeline_step_run(
            step_run_id=step_run_id,
            pipeline_run_id=pipeline_run_id,
            step_run_in={
                "status": StepStatus.COMPLETED,
                "end_time": datetime.now(timezone.utc).isoformat(),
                "output_data": output_data,
            },
        )

        logger.info(f"Step {step_id} completed successfully")

        # Return minimal data - just status info, no large output data
        return {
            "status": StepStatus.COMPLETED,
            "step_run_id": step_run_id,
            "step_id": step_id,
            "level_index": level_index,
            "pipeline_id": pipeline_id,
            "pipeline_run_id": pipeline_run_id,
            "output_size": (
                len(str(output_data)) if output_data else 0
            ),  # Just for logging
        }

    except Exception as e:
        error_message = f"Step execution failed: {str(e)}"
        logger.error(f"Step {step_id} failed: {error_message}")

        # Update step run as failed
        if step_run_id:
            await step_service.update_pipeline_step_run(
                step_run_id=step_run_id,
                pipeline_run_id=pipeline_run_id,
                step_run_in={
                    "status": StepStatus.FAILED,
                    "end_time": datetime.now(timezone.utc).isoformat(),
                    "error_message": error_message,
                },
            )

        # Update pipeline as failed
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

        raise Exception(f"Step {step_id} execution failed: {error_message}")


async def wait_for_dependencies(
    step: Dict[str, Any],
    pipeline_run_id: str,
    timeout: int = 90,  # 1 hour timeout
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
    # split by comma and strip whitespace
    step_inputs = step.get("inputs", [])
    if isinstance(step_inputs, str) and step_inputs:
        step_inputs = [s.strip() for s in step_inputs.split(",")]

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
            logger.info(
                f"Checking dependencies for step {step['id']} - pipeline run ID: {pipeline_run_id}"
            )
            step_runs_response = await step_service.get_pipeline_step_runs(
                pipeline_run_id
            )
            logger.info(
                f"Step runs response: {step_runs_response.data if step_runs_response else 'No data'}"
            )
            step_runs = step_runs_response.data if step_runs_response else []
            logger.info(f"Step runs: {step_runs}")

            # Create lookup map: step_id -> step_run
            step_run_map = {}
            for run in step_runs:
                step_run_map[run["step_id"]] = run

            logger.info(
                f"Checking dependencies for step {step['id']} - found {len(step_run_map)} step runs"
            )

            # Check dependency status
            all_ready = True
            failed_deps = []

            for dep_step_id in step_inputs:
                if dep_step_id not in step_run_map:
                    all_ready = False
                    logger.info(f"Dependency {dep_step_id} not started yet")
                    break

                dep_status = step_run_map[dep_step_id]["status"]

                if dep_status == StepStatus.FAILED:
                    failed_deps.append(dep_step_id)
                elif dep_status != StepStatus.COMPLETED:
                    all_ready = False
                    logger.info(f"Dependency {dep_step_id} status: {dep_status}")
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


async def resolve_step_input_data_from_db(
    step: Dict[str, Any], pipeline_run_id: str
) -> Dict[str, Any]:
    """
    Resolve input data for a step by fetching from database.

    Args:
        step: Step configuration
        pipeline_run_id: Pipeline run ID

    Returns:
        Resolved input data with dependency outputs
    """
    input_data = {}
    step_inputs = step.get("inputs", [])

    if isinstance(step_inputs, str) and step_inputs:
        # Split by comma and strip whitespace
        step_inputs = [s.strip() for s in step_inputs.split(",")]

    if not step_inputs:
        return input_data

    from app.services.pipeline_step import PipelineStepService

    step_service = PipelineStepService()

    try:
        # Get all completed step runs for this pipeline run
        step_runs_response = await step_service.get_pipeline_step_runs(pipeline_run_id)
        step_runs = step_runs_response.data if step_runs_response else []

        # Create lookup map: step_id -> step_run for completed steps only
        step_run_map = {}
        for run in step_runs:
            if run["status"] == StepStatus.COMPLETED:
                step_run_map[run["step_id"]] = run

        # Gather input data from dependencies
        for dep_step_id in step_inputs:
            if dep_step_id in step_run_map:
                dep_output = step_run_map[dep_step_id].get("output_data", {})
                if dep_output:
                    # Add with step prefix for clear identification
                    for key in dep_output:
                        input_data[key] = dep_output[key]

                    logger.info(
                        f"Added dependency data from step {dep_step_id} (size: {len(str(dep_output))} chars)"
                    )
            else:
                logger.warning(
                    f"Dependency step {dep_step_id} not found or not completed"
                )

        return input_data

    except Exception as e:
        logger.error(f"Failed to resolve input data for step {step['id']}: {str(e)}")
        return input_data


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
            if result.get("status") == StepStatus.COMPLETED:
                completed_steps.append(result["step_id"])
            else:
                failed_steps.append(result["step_id"])

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
    step_type: str, config: Dict[str, Any], input_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute a step based on its type.

    Args:
        step_type: Type of the step
        config: Step configuration
        input_data: Input data from previous steps

    Returns:
        Output data from step execution
    """
    try:
        if step_type == PipelineStepType.FILE_READER:
            return await execute_file_reader_step(config, input_data)

        elif step_type == PipelineStepType.API_FETCHER:
            return await execute_api_fetcher_step(config, input_data)

        elif step_type == PipelineStepType.DATABASE_EXTRACTOR:
            return await execute_database_extractor_step(config, input_data)

        elif step_type == PipelineStepType.TEXT_EXTRACTOR:
            return await execute_text_extractor_step(config, input_data)

        elif step_type == PipelineStepType.LLM_ENTITY_EXTRACTOR:
            return await execute_llm_entity_extractor_step(config, input_data)

        elif step_type == PipelineStepType.ENTITY_RESOLUTION:
            return await execute_entity_resolution_step(config, input_data)

        elif step_type == PipelineStepType.FIBO_MAPPER:
            return await execute_fibo_mapper_step(config, input_data)

        elif step_type == PipelineStepType.KNOWLEDGE_GRAPH_WRITER:
            return await execute_knowledge_graph_writer_step(config, input_data)

        elif step_type == PipelineStepType.CUSTOM_PYTHON:
            return await execute_custom_python_step(config, input_data)

        else:
            raise ValueError(f"Unknown step type: {step_type}")

    except Exception as e:
        logger.error(f"Error executing step type {step_type}: {str(e)}")
        raise


# =============================================
# SIMPLIFIED STEP IMPLEMENTATIONS
# =============================================


async def execute_text_extractor_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    SIMPLIFIED: Execute text extractor step - Only chunk text from file reader output
    No more PDF extraction, no saving to text_extractions table (doesn't exist)
    """

    logger.info("Executing text extractor step")

    chunk_size = config.get("chunk_size", 1000)
    chunk_overlap = config.get("chunk_overlap", 200)

    if not input_data:
        raise ValueError("Require input data from file reader step")

    if "file_content" in input_data and "error" in input_data["file_content"]:
        raise ValueError(
            f"File reader step failed: {input_data['file_content']['error']}"
        )

    if "file_content" not in input_data or "content" not in input_data["file_content"]:
        raise ValueError("Input data must contain 'file_content' with 'content' key")

    file_content = input_data["file_content"]["content"]["text"]

    if not file_content:
        raise ValueError("No text content available from file reader step")

    # Get file content from previous step (file reader)

    logger.info(
        f"Chunking text content of size {len(input_data['file_content']['content']['text'])} characters"
    )

    file_id = input_data.get("file_id")

    logger.info(f"Chunking text content of size {len(file_content)} characters")

    try:
        # Simply chunk the text content
        text_chunks = chunk_text(file_content, chunk_size, chunk_overlap)

        # Create simple metadata
        metadata = {
            "total_chunks": len(text_chunks),
            "total_characters": len(file_content),
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "extraction_date": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "text_chunks": text_chunks,
            "full_text": file_content,
            "chunk_count": len(text_chunks),
            "character_count": len(file_content),
            "metadata": metadata,
            "file_id": file_id,
            "text_processing_completed": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Text chunking failed: {str(e)}")
        raise Exception(f"Text chunking failed: {str(e)}")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            sentence_ends = [".", "!", "?", "\n"]
            best_break = end

            for i in range(end - 100, end + 100):
                if i < len(text) and text[i] in sentence_ends:
                    best_break = i + 1
                    break

            end = best_break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

        if start >= len(text):
            break

    return chunks


async def execute_llm_entity_extractor_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    UPDATED: Execute LLM entity extractor step
    Save to extraction_results table instead of entity_extractions
    """
    model = config.get("model", "gpt-4o-mini")
    entity_types = config.get("entity_types", [])
    extract_relationships = config.get("extract_relationships", True)
    relationship_types = config.get("relationship_types", [])
    max_tokens = config.get("max_tokens", 2000)
    temperature = config.get("temperature", 0.2)
    prompt_template = config.get("prompt_template", "")

    # Get text chunks from previous step
    if not input_data or "text_chunks" not in input_data:
        raise ValueError("No text chunks available from previous step")

    text_chunks = input_data["text_chunks"]
    file_id = input_data.get("file_id")

    all_entities: List[Dict[str, Any]] = []
    all_relationships: List[Dict[str, Any]] = []

    try:
        # Process each text chunk
        for i, chunk in enumerate(text_chunks):
            logger.info(f"Processing chunk {i+1}/{len(text_chunks)}")

            # Prepare prompt
            prompt = (
                prompt_template.format(text=chunk)
                if prompt_template
                else f"""
                        Extract entities and relationships from the following text.

                        Entity types: {', '.join(entity_types)}
                        Relationship types: {', '.join(relationship_types)}

                        Text: {chunk}

                        Return a JSON object with:
                        1. entities: list of {{text, type, confidence}}
                        2. relationships: list of {{source, target, type, confidence}}
                    """
            )

            # Call OpenAI API
            try:
                response = await call_openai_api(prompt, model, max_tokens, temperature)
                result = parse_llm_response(response)

                if result.get("entities"):
                    all_entities.append(
                        {"chunk_index": i, "entities": result["entities"]}
                    )

                if result.get("relationships") and extract_relationships:
                    all_relationships.append(
                        {"chunk_index": i, "relationships": result["relationships"]}
                    )

            except Exception as e:
                logger.warning(f"Failed to process chunk {i+1}: {str(e)}")
                continue

        # Deduplicate entities
        unique_entities = deduplicate_entities(all_entities)
        unique_relationships = deduplicate_relationships(all_relationships)

        # Save results to extraction_results table (matches schema)
        from app.core.supabase import get_supabase

        supabase = await get_supabase()

        extraction_record = {
            "source_id": file_id,
            "entity_count": len(unique_entities),
            "relationship_count": len(unique_relationships),
            "processed_text_length": sum(len(chunk) for chunk in text_chunks),
            "extracted_entities": unique_entities,
            "extracted_relationships": unique_relationships,
            "status": "completed",
        }

        result = (
            await supabase.table("extraction_results")
            .insert(extraction_record)
            .execute()
        )
        extraction_id = result.data[0]["id"]

        return {
            "entities_extracted": True,
            "extraction_id": extraction_id,
            "entities": unique_entities,
            "relationships": unique_relationships,
            "entity_count": len(unique_entities),
            "relationship_count": len(unique_relationships),
            "chunks_processed": len(text_chunks),
            "model_used": model,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Entity extraction failed: {str(e)}")
        raise Exception(f"Entity extraction failed: {str(e)}")


async def call_openai_api(
    prompt: str, model: str, max_tokens: int, temperature: float
) -> str:
    """Call OpenAI API for entity extraction"""
    try:
        # You'll need to set up OpenAI client
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at extracting entities and relationships from text. Always return valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        logger.info(
            f"OpenAI API response: {response.choices[0].message.content[:100]}..."
        )

        return response.choices[0].message.content

    except Exception as e:
        raise Exception(f"OpenAI API call failed: {str(e)}")


def parse_llm_response(response: str) -> Dict[str, Any]:
    """Parse LLM response to extract entities and relationships"""
    try:
        # Try to parse as JSON
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass

        # Ultimate fallback: return empty result
        return {"entities": [], "relationships": []}


def deduplicate_entities(
    extraction_entities: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Remove duplicate entities"""
    seen = set()
    unique_entities = []

    for extraction_item in extraction_entities:
        entities = extraction_item.get("entities", [])
        for entity in entities:
            key = (entity.get("text", "").lower(), entity.get("type", ""))
            if key not in seen:
                seen.add(key)
                # Add unique ID
                entity["id"] = str(uuid4())
                entity["chunk_index"] = extraction_item.get("chunk_index", 0)
                unique_entities.append(entity)

    return unique_entities


def deduplicate_relationships(
    extraction_relationships: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Remove duplicate relationships"""
    seen = set()
    unique_relationships = []

    for extraction_item in extraction_relationships:
        relationships = extraction_item.get("relationships", [])
        for rel in relationships:
            key = (
                rel.get("source", "").lower(),
                rel.get("target", "").lower(),
                rel.get("type", ""),
            )
            if key not in seen:
                seen.add(key)
                # Add unique ID
                rel["id"] = str(uuid4())
                rel["chunk_index"] = extraction_item.get("chunk_index", 0)
                unique_relationships.append(rel)

    return unique_relationships


async def execute_entity_resolution_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    SIMPLIFIED: Execute entity resolution step
    Update existing extraction_results record instead of creating entity_resolutions
    """
    resolution_strategy = config.get("resolution_strategy", "fuzzy_match")
    similarity_threshold = config.get("similarity_threshold", 0.85)

    if not input_data or "entities" not in input_data:
        raise ValueError("No entities available from previous step")

    entities = input_data["entities"]
    relationships = input_data.get("relationships", [])
    extraction_id = input_data.get("extraction_id")

    try:
        # Perform entity resolution
        resolved_entities = await resolve_entities(
            entities, resolution_strategy, similarity_threshold
        )

        # Update existing extraction_results record
        from app.core.supabase import get_supabase

        supabase = await get_supabase()

        # Update the extraction record with resolved data
        await supabase.table("extraction_results").update(
            {
                "extracted_entities": resolved_entities,
                "entity_count": len(resolved_entities),
                "status": "completed",
            }
        ).eq("id", extraction_id).execute()

        return {
            "entity_resolution_completed": True,
            "extraction_id": extraction_id,
            "resolved_entities": resolved_entities,
            "relationships": relationships,  # Pass through for next step
            "original_entity_count": len(entities),
            "resolved_entity_count": len(resolved_entities),
            "duplicates_merged": len(entities) - len(resolved_entities),
            "resolution_strategy": resolution_strategy,
            "similarity_threshold": similarity_threshold,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Entity resolution failed: {str(e)}")
        raise Exception(f"Entity resolution failed: {str(e)}")


async def resolve_entities(
    entities: List[Dict[str, Any]], strategy: str, threshold: float
) -> List[Dict[str, Any]]:
    """Resolve duplicate entities using specified strategy"""
    if strategy == "exact_match":
        return resolve_exact_match(entities)
    elif strategy == "fuzzy_match":
        return resolve_fuzzy_match(entities, threshold)
    else:
        return entities  # No resolution


def resolve_exact_match(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Resolve entities using exact text match"""
    entity_map = {}

    for entity in entities:
        key = (entity.get("text", "").lower(), entity.get("type", ""))

        if key in entity_map:
            # Merge with higher confidence
            existing = entity_map[key]
            if entity.get("confidence", 0) > existing.get("confidence", 0):
                entity_map[key] = entity
        else:
            entity_map[key] = entity

    return list(entity_map.values())


def resolve_fuzzy_match(
    entities: List[Dict[str, Any]], threshold: float
) -> List[Dict[str, Any]]:
    """Resolve entities using fuzzy string matching"""
    from difflib import SequenceMatcher

    resolved = []
    processed = set()

    for i, entity in enumerate(entities):
        if i in processed:
            continue

        merged_entity = entity.copy()
        similar_indices = [i]

        for j, other in enumerate(entities[i + 1 :], i + 1):
            if j in processed:
                continue

            # Only compare entities of same type
            if entity.get("type") != other.get("type"):
                continue

            # Calculate similarity
            similarity = SequenceMatcher(
                None, entity.get("text", "").lower(), other.get("text", "").lower()
            ).ratio()

            if similarity >= threshold:
                similar_indices.append(j)
                # Keep entity with higher confidence
                if other.get("confidence", 0) > merged_entity.get("confidence", 0):
                    merged_entity = other.copy()

        # Mark all similar entities as processed
        processed.update(similar_indices)
        resolved.append(merged_entity)

    return resolved


async def execute_knowledge_graph_writer_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    UPDATED: Execute knowledge graph writer step
    Save to kg_entities and kg_relationships tables (matches schema)
    """
    from app.tasks.transformation import enrich_entities_with_embeddings

    batch_size = config.get("batch_size", 100)

    if not input_data:
        raise ValueError("No data available from previous steps")

    mapped_entities = input_data.get("mapped_entities", [])
    mapped_relationships = input_data.get("mapped_relationships", [])
    unmapped_entities = input_data.get("unmapped_entities", [])
    unmapped_relationships = input_data.get("unmapped_relationships", [])
    create_unmapped = config.get("create_unmapped", True)

    resolved_entities = mapped_entities + unmapped_entities

    for entity in mapped_entities:
        entity["mapped"] = True
    for entity in unmapped_entities:
        entity["mapped"] = False
    for rel in mapped_relationships:
        rel["mapped"] = True
    for rel in unmapped_relationships:
        rel["mapped"] = False

    resolved_entities = mapped_entities + unmapped_entities

    resolved_relationships = mapped_relationships + unmapped_relationships

    extraction_id = input_data.get("extraction_id")

    try:
        from app.core.supabase import get_supabase

        supabase = await get_supabase()

        entities_created = 0
        relationships_created = 0
        created_relationships = []
        created_entities = []
        entity_id_map = {}  # Map entity text to UUID for relationships
        entity_text_map = {}
        entities = []

        # Create entities in batches
        for i in range(0, len(resolved_entities), batch_size):
            batch = resolved_entities[i : i + batch_size]
            entity_records = []

            for entity in batch:
                entity_record = {
                    "entity_text": entity.get("text", ""),
                    "entity_type": entity.get("type", ""),
                    "confidence": entity.get("confidence", 0.5),
                    "fibo_class_id": (
                        entity["fibo_mapping"]["fibo_class_id"]
                        if entity["mapped"]
                        else None
                    ),
                    "properties": {
                        "source_extraction_id": extraction_id,
                        "mapped": entity["mapped"] if "mapped" in entity else True,
                        "chunk_index": entity.get("chunk_index", 0),
                        "unmapped_reason": entity.get("unmapped_reason", ""),
                    },
                    "is_verified": False,
                }
                entity_records.append(entity_record)

            # Insert batch
            result = (
                await supabase.table("kg_entities").insert(entity_records).execute()
            )

            # Map entity text to UUID for relationships
            for i, record in enumerate(result.data):
                entity_text = batch[i].get("text", "")
                entity_id_map[entity_text] = record["id"]
                entity_text_map[record["id"]] = entity_text
                entities_created += 1
                entities.append(record["id"])

            created_entities.extend(result.data)

        await enrich_entities_with_embeddings(
            entity_ids=entities, batch_size=batch_size
        )

        # Create relationships in batches
        for i in range(0, len(resolved_relationships), batch_size):
            batch = resolved_relationships[i : i + batch_size]
            relationship_records = []

            for rel in batch:
                source_text = rel.get("source", "")
                target_text = rel.get("target", "")

                # Find entity IDs
                source_id = entity_id_map.get(source_text)
                target_id = entity_id_map.get(target_text)

                if source_id and target_id:
                    relationship_record = {
                        "source_entity_id": source_id,
                        "target_entity_id": target_id,
                        "relationship_type": rel.get("type", "RELATED_TO"),
                        "confidence": rel.get("confidence", 0.5),
                        "fibo_property_id": (
                            rel["fibo_mapping"]["fibo_property_id"]
                            if rel["mapped"]
                            else None
                        ),
                        "properties": {
                            "source_extraction_id": extraction_id,
                            "mapped": rel["mapped"] if "mapped" in rel else True,
                            "chunk_index": rel.get("chunk_index", 0),
                            "unmapped_reason": rel.get("unmapped_reason", ""),
                        },
                        "is_verified": False,
                    }
                    relationship_records.append(relationship_record)

            if relationship_records:
                response = (
                    await supabase.table("kg_relationships")
                    .insert(relationship_records)
                    .execute()
                )
                relationships_created += len(relationship_records)

                for record in response.data:
                    source_text = entity_text_map.get(record["source_entity_id"], "")
                    target_text = entity_text_map.get(record["target_entity_id"], "")
                    created_relationships.append(
                        {
                            "source": source_text,
                            "target": target_text,
                            "type": record["relationship_type"],
                            "confidence": record["confidence"],
                            "id": record["id"],
                            "properties": record["properties"],
                        }
                    )

        # Optionally sync to Neo4j (if configured)
        neo4j_status = "skipped"
        neo4j_results: Dict[str, Any] | None = None
        if config.get("sync_to_neo4j", True):
            try:
                # Store in Neo4j with FIBO metadata
                neo4j_results = await sync_to_neo4j(
                    entities=created_entities, relationships=created_relationships
                )
                neo4j_status = "completed"
            except Exception as e:
                logger.warning(f"Neo4j sync failed: {str(e)}")
                neo4j_status = "failed"

        return {
            "knowledge_graph_updated": True,
            "entities_created": entities_created,
            "relationships_created": relationships_created,
            "batch_size": batch_size,
            "neo4j_results": neo4j_results,
            "neo4j_status": neo4j_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Knowledge graph writing failed: {str(e)}")
        raise Exception(f"Knowledge graph writing failed: {str(e)}")


async def sync_to_neo4j(
    entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
):
    """Optional Neo4j sync - simplified implementation"""
    try:
        from app.utils.neo4j import get_neo4j_driver

        driver = get_neo4j_driver()

        logger.info(
            f"Syncing {entities} entities and {relationships} relationships to Neo4j"
        )

        async with driver.session() as session:
            # Create entities
            for entity in entities:
                entity_type = entity.get("entity_type", "Entity").replace(" ", "_")
                entity_text = entity.get("entity_text", "")
                confidence = entity.get("confidence", 0.5)
                entity_id = entity.get("id", str(uuid4()))

                query = f"""
                MERGE (e:`{entity_type}` {{text: $text}})
                SET e.confidence = $confidence,
                    e.entity_id = $entity_id,
                    e.entity_type = $entity_type,
                    e.updated_at = datetime()
                RETURN e
                """
                await session.run(
                    query,
                    {
                        "text": entity_text,
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "confidence": confidence,
                    },
                )

            # Create relationships
            for rel in relationships:
                source_text = rel.get("source", "")
                target_text = rel.get("target", "")
                rel_type = rel.get("type", "RELATED_TO").replace(" ", "_")
                rel_id = rel.get("id", str(uuid4()))
                confidence = rel.get("confidence", 0.5)

                query = f"""
                MATCH (source {{text: $source_text}})
                MATCH (target {{text: $target_text}})
                MERGE (source)-[r:`{rel_type}`]->(target)
                SET r.confidence = $confidence,
                    r.relationship_id = $rel_id,
                    r.relationship_type = $rel_type,
                    r.updated_at = datetime()
                RETURN r
                """
                await session.run(
                    query,
                    {
                        "source_text": source_text,
                        "target_text": target_text,
                        "rel_type": rel_type,
                        "rel_id": rel_id,
                        "confidence": confidence,
                    },
                )

    except Exception as e:
        logger.error(f"Neo4j sync failed: {str(e)}")
        raise


async def execute_custom_python_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute custom Python code step - Simplified"""
    import subprocess
    import tempfile

    code = config.get("code")
    if not code:
        raise ValueError("code is required for custom Python step")

    timeout = config.get("timeout", 60)
    input_mapping = config.get("input_mapping", {})

    # Prepare input data based on mapping
    mapped_inputs = {}
    if input_data and input_mapping:
        for key, source_key in input_mapping.items():
            if source_key in input_data:
                mapped_inputs[key] = input_data[source_key]

    # Create temporary script file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(f"import json\n")
        f.write(f"input_data = {json.dumps(mapped_inputs)}\n\n")
        f.write(code)
        f.write(f"\n\n# Output result as JSON\n")
        f.write(f"if 'result' in locals():\n")
        f.write(f"    print(json.dumps(result))\n")
        f.write(f"else:\n")
        f.write(f"    print(json.dumps({{}}))\n")
        script_path = f.name

    try:
        # Execute the script
        result = subprocess.run(
            ["python", script_path], capture_output=True, text=True, timeout=timeout
        )

        if result.returncode != 0:
            raise Exception(f"Script execution failed: {result.stderr}")

        # Parse output
        try:
            output = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            output = {"raw_output": result.stdout}

        return {
            "custom_python_executed": True,
            "result": output,
            "execution_time": timeout,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    finally:
        # Clean up temporary file
        if os.path.exists(script_path):
            os.unlink(script_path)


# =============================================
# DATA SOURCE RESOLUTION & FILE HANDLING
# =============================================


async def execute_file_reader_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute file reader step with data source resolution"""
    from app.services.file_upload import UploadService
    from app.utils.file_handler import process_file

    file_upload_service = UploadService()

    # Resolve data source configuration
    resolved_config = await resolve_datasource_config(config)

    # Get file ID from config or input data or data source
    file_id = None

    # Priority: explicit file_id > input data > data source latest file
    if "file_id" in resolved_config:
        file_id = resolved_config["file_id"]
    elif input_data and "file_id" in input_data:
        file_id = input_data["file_id"]

    if not file_id and "datasource_id" in resolved_config:
        # Get latest file from data source
        file_id = await get_latest_file_from_datasource(
            resolved_config["datasource_id"]
        )

    if not file_id:
        raise ValueError("No file available to read")

    file_info = await file_upload_service.get_file_upload(file_id)
    file_response = await file_upload_service.get_file_content(file_id)

    if not file_response:
        raise ValueError(f"File {file_id} not found or inaccessible")

    # Save to local to process
    local_file_path = f"/tmp/{file_id}-{file_info['file_name']}"

    with open(local_file_path, "wb") as f:
        f.write(file_response)

    # Process file content based on format
    file_content = await process_file(local_file_path, file_info["file_type"])

    # Clean up
    if os.path.exists(local_file_path):
        os.unlink(local_file_path)

    return {
        "file_processed": True,
        "file_id": file_id,
        "file_content": file_content,  # Pass content to next step
        "datasource_info": resolved_config.get("_datasource_info"),
        "processing_status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def execute_api_fetcher_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute API fetcher step with data source resolution"""
    # Resolve data source configuration
    resolved_config = await resolve_datasource_config(config)

    # Required fields after resolution
    if "url" not in resolved_config:
        raise ValueError("URL is required for API fetcher step")

    # Use resolved config for API call
    from app.tasks.ingestion import ingest_api_data

    result = await ingest_api_data(
        api_url=resolved_config["url"],
        data_format=resolved_config.get("data_format", "json"),
        datasource_id=(
            UUID(resolved_config["datasource_id"])
            if resolved_config.get("datasource_id")
            else None
        ),
        auth_params=resolved_config.get("auth_config"),
        headers=resolved_config.get("headers"),
        query_params=resolved_config.get("params"),
    )

    return {
        "api_data_ingested": bool(result),
        "file_id": result.get("id") if result else None,
        "api_url": resolved_config["url"],
        "datasource_info": resolved_config.get("_datasource_info"),
        "data_format": resolved_config.get("data_format", "json"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def execute_database_extractor_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute database extractor step with data source resolution"""
    # Resolve data source configuration
    resolved_config = await resolve_datasource_config(config)

    # Required fields after resolution
    required_fields = ["connection_string", "query"]
    for field in required_fields:
        if field not in resolved_config:
            raise ValueError(f"{field} is required for database extractor step")

    from app.tasks.ingestion import ingest_database_data

    result = await ingest_database_data(
        connection_string=resolved_config["connection_string"],
        query=resolved_config["query"],
        datasource_id=(
            UUID(resolved_config["datasource_id"])
            if resolved_config.get("datasource_id")
            else None
        ),
        output_format=resolved_config.get("output_format", "csv"),
    )

    return {
        "database_data_extracted": bool(result),
        "file_id": result.get("id") if result else None,
        "query": resolved_config["query"],
        "datasource_info": resolved_config.get("_datasource_info"),
        "output_format": resolved_config.get("output_format", "csv"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def resolve_datasource_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve data source configuration for step execution"""
    datasource_id = config.get("datasource_id")
    if not datasource_id:
        return config

    from app.services.datasource import DataSourceService

    datasource_service = DataSourceService()

    try:
        datasource = await datasource_service.get_datasource(datasource_id)
        connection_details = datasource["connection_details"]

        # Get credentials if needed
        credentials = await datasource_service.get_data_source_credentials(
            datasource_id
        )

        # Merge datasource config into step config
        resolved_config = config.copy()

        # For API fetcher
        if "url" not in config and "url" in connection_details:
            resolved_config["url"] = connection_details["url"]
        if "headers" not in config and "headers" in connection_details:
            resolved_config["headers"] = connection_details["headers"]
        if credentials and "auth_config" not in config:
            resolved_config["auth_config"] = credentials

        # For database extractor
        if (
            "connection_string" not in config
            and datasource["source_type"] == "database"
        ):
            resolved_config["connection_string"] = build_connection_string(
                connection_details, credentials
            )

        # For file reader
        if "file_format" not in config and "file_format" in connection_details:
            resolved_config["file_format"] = connection_details["file_format"]

        resolved_config["_datasource_info"] = {
            "name": datasource["name"],
            "source_type": datasource["source_type"],
        }

        return resolved_config

    except Exception as e:
        logger.error(f"Failed to resolve datasource {datasource_id}: {str(e)}")
        return config


async def get_latest_file_from_datasource(datasource_id: str) -> Optional[str]:
    """Get the latest file uploaded to a data source"""
    from app.core.supabase import get_supabase

    supabase = await get_supabase()

    response = (
        await supabase.table("file_uploads")
        .select("id")
        .eq("data_source_id", datasource_id)
        .eq("upload_status", "completed")
        .order("uploaded_at", desc=True)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]["id"]

    return None


def build_connection_string(
    connection_details: Dict, credentials: Optional[Dict]
) -> str:
    """Build database connection string from details and credentials"""
    db_type = connection_details.get("db_type", "postgresql")
    host = connection_details["host"]
    port = connection_details["port"]
    database = connection_details["database"]

    username = ""
    password = ""

    if credentials:
        username = credentials.get("username", "")
        password = credentials.get("password", "")

    if db_type == "postgresql":
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    elif db_type == "mysql":
        return f"mysql://{username}:{password}@{host}:{port}/{database}"
    elif db_type == "mssql":
        return f"mssql://{username}:{password}@{host}:{port}/{database}"
    else:
        return f"{db_type}://{username}:{password}@{host}:{port}/{database}"


async def execute_fibo_mapper_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Execute FIBO mapper step - Map extracted entities and relationships to FIBO ontology
    and store in Neo4j with FIBO metadata.

    This step:
    1. Loads verified entity and relationship mappings from the database
    2. Maps extracted entities to FIBO classes based on entity_type mappings
    3. Maps extracted relationships to FIBO properties based on relationship_type mappings
    4. Uses fuzzy matching for entities/relationships without exact mappings
    5. Stores mapped data in Neo4j with FIBO metadata
    6. Generates comprehensive mapping statistics

    Args:
        config: Configuration containing:
            - mapping_confidence_threshold: Minimum confidence for mappings (default: 0.7)
            - domains: List of FIBO domains to filter mappings (optional)
            - create_unmapped: Whether to create unmapped entities/relationships (default: True)
            - batch_size: Batch size for Neo4j operations (default: 100)
        input_data: Data from previous pipeline steps containing:
            - entities: List of extracted entities with type and text
            - relationships: List of extracted relationships with type, source, target
            - extraction_id: ID of the extraction run

    Returns:
        Dictionary with mapping results, statistics, and Neo4j storage status
    """
    from app.services.fibo import FIBOService
    from app.utils.neo4j import get_neo4j_driver

    # Validate input data
    validate_fibo_mapper_input(input_data or {})

    # Configuration
    mapping_confidence_threshold = config.get("mapping_confidence_threshold", 0.7)
    domains = config.get("domains", [])
    create_unmapped = config.get(
        "create_unmapped", True
    )  # Create entities/rels even if no FIBO mapping
    batch_size = config.get("batch_size", 100)

    if not input_data:
        raise ValueError("No data available from previous steps")

    # Get extracted entities and relationships
    entities = input_data.get("resolved_entities", [])
    relationships = input_data.get("relationships", [])
    extraction_id = input_data.get("extraction_id")

    if not entities and not relationships:
        raise ValueError("No entities or relationships found in input data")

    try:
        fibo_service = FIBOService()

        # Get all entity mappings and relationship mappings
        entity_mappings = await get_entity_mappings(fibo_service, domains)
        relationship_mappings = await get_relationship_mappings(fibo_service, domains)

        logger.info(
            f"Loaded {len(entity_mappings)} entity mappings and {len(relationship_mappings)} relationship mappings"
        )

        logger.info(entities)

        # Map entities to FIBO classes
        mapped_entities, unmapped_entities = await map_entities_to_fibo(
            entities, entity_mappings, fibo_service, mapping_confidence_threshold
        )

        # Map relationships to FIBO properties
        mapped_relationships, unmapped_relationships = await map_relationships_to_fibo(
            relationships,
            relationship_mappings,
            fibo_service,
            mapping_confidence_threshold,
        )

        logger.info(
            f"Mapped {len(mapped_entities)}/{len(entities)} entities and {len(mapped_relationships)}/{len(relationships)} relationships"
        )

        # Log detailed mapping results
        await log_mapping_results(
            mapped_entities,
            mapped_relationships,
            unmapped_entities,
            unmapped_relationships,
        )

        # Generate mapping statistics
        mapping_stats = generate_mapping_statistics(
            entities,
            relationships,
            mapped_entities,
            mapped_relationships,
            unmapped_entities,
            unmapped_relationships,
        )

        return {
            "fibo_mapping_completed": True,
            "extraction_id": extraction_id,
            "mapping_confidence_threshold": mapping_confidence_threshold,
            "mapped_entities": mapped_entities,
            "unmapped_entities": unmapped_entities,
            "mapped_relationships": mapped_relationships,
            "unmapped_relationships": unmapped_relationships,
            "domains_processed": domains,
            "entities": {
                "total": len(entities),
                "mapped": len(mapped_entities),
                "unmapped": len(unmapped_entities),
                "mapping_rate": len(mapped_entities) / len(entities) if entities else 0,
            },
            "relationships": {
                "total": len(relationships),
                "mapped": len(mapped_relationships),
                "unmapped": len(unmapped_relationships),
                "mapping_rate": (
                    len(mapped_relationships) / len(relationships)
                    if relationships
                    else 0
                ),
            },
            "mapping_statistics": mapping_stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"FIBO mapping failed: {str(e)}")
        raise Exception(f"FIBO mapping failed: {str(e)}")


async def get_entity_mappings(
    fibo_service: FIBOService, domains: List[str]
) -> Dict[str, Dict[str, Any]]:
    """Get all entity mappings as a lookup dictionary"""
    try:
        # Get all verified entity mappings
        mappings_response = await fibo_service.get_entity_mappings(
            is_verified=True, mapping_status="mapped", limit=1000  # Get all mappings
        )

        mappings = mappings_response.data if mappings_response else []

        # Create lookup dictionary: entity_type -> mapping_info
        entity_mapping_dict = {}

        for mapping in mappings:
            # Support both legacy entity_type and new entity_type_id
            entity_key = None
            if mapping.get("entity_type"):
                entity_key = mapping["entity_type"]
            elif mapping.get("entity_type_id") and mapping.get("entity_type_info"):
                entity_key = mapping["entity_type_info"]["name"]

            if entity_key:
                entity_mapping_dict[entity_key.lower()] = {
                    "fibo_class_uri": mapping["fibo_class_uri"],
                    "confidence": mapping.get("confidence", 1.0),
                    "mapping_id": mapping["id"],
                    "mapping_notes": mapping.get("mapping_notes"),
                    "auto_mapped": mapping.get("auto_mapped", False),
                }

        return entity_mapping_dict

    except Exception as e:
        logger.error(f"Error loading entity mappings: {str(e)}")
        return {}


async def get_relationship_mappings(
    fibo_service: FIBOService, domains: List[str]
) -> Dict[str, Dict[str, Any]]:
    """Get all relationship mappings as a lookup dictionary"""
    try:
        # Get all verified relationship mappings
        mappings_response = await fibo_service.get_relationship_mappings(
            is_verified=True, mapping_status="mapped", limit=1000  # Get all mappings
        )

        mappings = mappings_response.data if mappings_response else []

        # Create lookup dictionary: relationship_type -> mapping_info
        relationship_mapping_dict = {}

        for mapping in mappings:
            # Support both legacy relationship_type and new relationship_type_id
            rel_key = None
            if mapping.get("relationship_type"):
                rel_key = mapping["relationship_type"]
            elif mapping.get("relationship_type_id") and mapping.get(
                "relationship_type_info"
            ):
                rel_key = mapping["relationship_type_info"]["name"]

            if rel_key:
                relationship_mapping_dict[rel_key.lower()] = {
                    "fibo_property_uri": mapping["fibo_property_uri"],
                    "confidence": mapping.get("confidence", 1.0),
                    "mapping_id": mapping["id"],
                    "mapping_notes": mapping.get("mapping_notes"),
                    "auto_mapped": mapping.get("auto_mapped", False),
                }

        return relationship_mapping_dict

    except Exception as e:
        logger.error(f"Error loading relationship mappings: {str(e)}")
        return {}


async def map_entities_to_fibo(
    entities: List[Dict[str, Any]],
    entity_mappings: Dict[str, Dict[str, Any]],
    fibo_service: FIBOService,
    confidence_threshold: float,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Map entities to FIBO classes"""
    mapped_entities = []
    unmapped_entities = []

    for entity in entities:
        entity_type = entity.get("type", "").lower()
        entity_text = entity.get("text", "")
        entity_id = entity.get("id", str(uuid4()))

        # Check if we have a mapping for this entity type
        if entity_type in entity_mappings:
            mapping = entity_mappings[entity_type]

            # Check confidence threshold
            if mapping["confidence"] >= confidence_threshold:
                # Get FIBO class details
                try:
                    fibo_class = await fibo_service.get_fibo_class_by_uri(
                        mapping["fibo_class_uri"]
                    )

                    mapped_entity = {
                        **entity,  # Original entity data
                        "fibo_mapping": {
                            "fibo_class_id": fibo_class.get("id"),
                            "fibo_class_uri": mapping["fibo_class_uri"],
                            "fibo_class_label": fibo_class.get("label"),
                            "fibo_class_domain": fibo_class.get("domain"),
                            "mapping_confidence": mapping["confidence"],
                            "mapping_id": mapping["mapping_id"],
                            "mapping_notes": mapping.get("mapping_notes"),
                            "auto_mapped": mapping.get("auto_mapped", False),
                        },
                    }
                    mapped_entities.append(mapped_entity)
                    continue

                except Exception as e:
                    logger.warning(
                        f"Could not get FIBO class {mapping['fibo_class_uri']}: {str(e)}"
                    )

        # Try to find similar mappings if no exact match
        similar_mapping = await find_similar_entity_mapping(
            entity_type, entity_text, entity_mappings, fibo_service
        )

        if similar_mapping and similar_mapping["confidence"] >= confidence_threshold:
            mapped_entity = {**entity, "fibo_mapping": similar_mapping}
            mapped_entities.append(mapped_entity)
        else:
            # No mapping found
            unmapped_entity = {
                **entity,
                "unmapped_reason": (
                    "No FIBO mapping found"
                    if not similar_mapping
                    else f"Confidence {similar_mapping['confidence']} below threshold {confidence_threshold}"
                ),
            }
            unmapped_entities.append(unmapped_entity)

    return mapped_entities, unmapped_entities


async def map_relationships_to_fibo(
    relationships: List[Dict[str, Any]],
    relationship_mappings: Dict[str, Dict[str, Any]],
    fibo_service: FIBOService,
    confidence_threshold: float,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Map relationships to FIBO properties"""
    mapped_relationships = []
    unmapped_relationships = []

    for relationship in relationships:
        rel_type = relationship.get("type", "").lower()
        source = relationship.get("source", "")
        target = relationship.get("target", "")
        rel_id = relationship.get("id", str(uuid4()))

        # Check if we have a mapping for this relationship type
        if rel_type in relationship_mappings:
            mapping = relationship_mappings[rel_type]

            # Check confidence threshold
            if mapping["confidence"] >= confidence_threshold:
                # Get FIBO property details
                try:
                    fibo_property = await fibo_service.get_fibo_property_by_uri(
                        mapping["fibo_property_uri"]
                    )

                    mapped_relationship = {
                        **relationship,  # Original relationship data
                        "fibo_mapping": {
                            "fibo_property_id": fibo_property.get("id"),
                            "fibo_property_uri": mapping["fibo_property_uri"],
                            "fibo_property_label": fibo_property.get("label"),
                            "fibo_property_type": fibo_property.get("property_type"),
                            "mapping_confidence": mapping["confidence"],
                            "mapping_id": mapping["mapping_id"],
                            "mapping_notes": mapping.get("mapping_notes"),
                            "auto_mapped": mapping.get("auto_mapped", False),
                        },
                    }
                    mapped_relationships.append(mapped_relationship)
                    continue

                except Exception as e:
                    logger.warning(
                        f"Could not get FIBO property {mapping['fibo_property_uri']}: {str(e)}"
                    )

        # Try to find similar mappings if no exact match
        similar_mapping = await find_similar_relationship_mapping(
            rel_type, source, target, relationship_mappings, fibo_service
        )

        if similar_mapping and similar_mapping["confidence"] >= confidence_threshold:
            mapped_relationship = {**relationship, "fibo_mapping": similar_mapping}
            mapped_relationships.append(mapped_relationship)
        else:
            # No mapping found
            unmapped_relationship = {
                **relationship,
                "unmapped_reason": (
                    "No FIBO mapping found"
                    if not similar_mapping
                    else f"Confidence {similar_mapping['confidence']:.2f} below threshold {confidence_threshold}"
                ),
            }
            unmapped_relationships.append(unmapped_relationship)

    return mapped_relationships, unmapped_relationships


async def find_similar_entity_mapping(
    entity_type: str,
    entity_text: str,
    entity_mappings: Dict[str, Dict[str, Any]],
    fibo_service: FIBOService,
) -> Optional[Dict[str, Any]]:
    """Find similar entity mapping using fuzzy matching"""
    from difflib import SequenceMatcher

    best_match = None
    best_similarity = 0.0

    # Try fuzzy matching on entity types
    for mapped_type, mapping in entity_mappings.items():
        similarity = SequenceMatcher(
            None, entity_type.lower(), mapped_type.lower()
        ).ratio()

        if (
            similarity > best_similarity and similarity > 0.6
        ):  # Minimum similarity threshold
            best_similarity = similarity
            best_match = {
                **mapping,
                "confidence": mapping["confidence"]
                * similarity,  # Reduce confidence based on similarity
                "similarity_score": similarity,
                "matched_via": "fuzzy_entity_type",
            }

    # Also try matching on entity text keywords if no good type match
    if best_similarity < 0.8 and entity_text:
        entity_keywords = entity_text.lower().split()

        for mapped_type, mapping in entity_mappings.items():
            type_keywords = mapped_type.lower().split()

            # Check if any keywords match
            matching_keywords = set(entity_keywords) & set(type_keywords)
            if matching_keywords:
                keyword_similarity = len(matching_keywords) / max(
                    len(entity_keywords), len(type_keywords)
                )

                if keyword_similarity > best_similarity and keyword_similarity > 0.3:
                    best_similarity = keyword_similarity
                    best_match = {
                        **mapping,
                        "confidence": mapping["confidence"] * keyword_similarity,
                        "similarity_score": keyword_similarity,
                        "matched_via": "keyword_matching",
                        "matching_keywords": list(matching_keywords),
                    }

    return best_match


async def find_similar_relationship_mapping(
    rel_type: str,
    source: str,
    target: str,
    relationship_mappings: Dict[str, Dict[str, Any]],
    fibo_service: FIBOService,
) -> Optional[Dict[str, Any]]:
    """Find similar relationship mapping using fuzzy matching"""
    from difflib import SequenceMatcher

    best_match = None
    best_similarity = 0.0

    # Try fuzzy matching on relationship types
    for mapped_type, mapping in relationship_mappings.items():
        similarity = SequenceMatcher(
            None, rel_type.lower(), mapped_type.lower()
        ).ratio()

        if (
            similarity > best_similarity and similarity > 0.6
        ):  # Minimum similarity threshold
            best_similarity = similarity
            best_match = {
                **mapping,
                "confidence": mapping["confidence"] * similarity,
                "similarity_score": similarity,
                "matched_via": "fuzzy_relationship_type",
            }

    return best_match


def generate_mapping_statistics(
    entities: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]],
    mapped_entities: List[Dict[str, Any]],
    mapped_relationships: List[Dict[str, Any]],
    unmapped_entities: List[Dict[str, Any]],
    unmapped_relationships: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Generate comprehensive mapping statistics"""

    # Entity type distribution
    entity_type_stats = {}
    for entity in entities:
        entity_type = entity.get("type", "unknown")
        if entity_type not in entity_type_stats:
            entity_type_stats[entity_type] = {"total": 0, "mapped": 0, "unmapped": 0}
        entity_type_stats[entity_type]["total"] += 1

    for entity in mapped_entities:
        entity_type = entity.get("type", "unknown")
        if entity_type in entity_type_stats:
            entity_type_stats[entity_type]["mapped"] += 1

    for entity in unmapped_entities:
        entity_type = entity.get("type", "unknown")
        if entity_type in entity_type_stats:
            entity_type_stats[entity_type]["unmapped"] += 1

    # Relationship type distribution
    relationship_type_stats = {}
    for rel in relationships:
        rel_type = rel.get("type", "unknown")
        if rel_type not in relationship_type_stats:
            relationship_type_stats[rel_type] = {"total": 0, "mapped": 0, "unmapped": 0}
        relationship_type_stats[rel_type]["total"] += 1

    for rel in mapped_relationships:
        rel_type = rel.get("type", "unknown")
        if rel_type in relationship_type_stats:
            relationship_type_stats[rel_type]["mapped"] += 1

    for rel in unmapped_relationships:
        rel_type = rel.get("type", "unknown")
        if rel_type in relationship_type_stats:
            relationship_type_stats[rel_type]["unmapped"] += 1

    # FIBO class distribution for mapped entities
    fibo_class_distribution = {}
    for entity in mapped_entities:
        fibo_class = entity["fibo_mapping"].get("fibo_class_label", "Unknown")
        fibo_class_distribution[fibo_class] = (
            fibo_class_distribution.get(fibo_class, 0) + 1
        )

    # FIBO property distribution for mapped relationships
    fibo_property_distribution = {}
    for rel in mapped_relationships:
        fibo_property = rel["fibo_mapping"].get("fibo_property_label", "Unknown")
        fibo_property_distribution[fibo_property] = (
            fibo_property_distribution.get(fibo_property, 0) + 1
        )

    return {
        "entity_type_distribution": entity_type_stats,
        "relationship_type_distribution": relationship_type_stats,
        "fibo_class_distribution": fibo_class_distribution,
        "fibo_property_distribution": fibo_property_distribution,
        "coverage": {
            "entity_mapping_coverage": (
                len(mapped_entities) / len(entities) if entities else 0
            ),
            "relationship_mapping_coverage": (
                len(mapped_relationships) / len(relationships) if relationships else 0
            ),
        },
        "quality_metrics": {
            "avg_entity_mapping_confidence": (
                sum(e["fibo_mapping"]["mapping_confidence"] for e in mapped_entities)
                / len(mapped_entities)
                if mapped_entities
                else 0
            ),
            "avg_relationship_mapping_confidence": (
                sum(
                    r["fibo_mapping"]["mapping_confidence"]
                    for r in mapped_relationships
                )
                / len(mapped_relationships)
                if mapped_relationships
                else 0
            ),
            "auto_mapped_entities": len(
                [
                    e
                    for e in mapped_entities
                    if e["fibo_mapping"].get("auto_mapped", False)
                ]
            ),
            "auto_mapped_relationships": len(
                [
                    r
                    for r in mapped_relationships
                    if r["fibo_mapping"].get("auto_mapped", False)
                ]
            ),
        },
    }


def validate_fibo_mapper_input(input_data: Dict[str, Any]) -> None:
    """Validate input data for FIBO mapper step"""
    required_fields = ["entities", "relationships"]

    if not input_data:
        raise ValueError("Input data is required for FIBO mapper step")

    # Check if we have at least entities or relationships
    entities = input_data.get("entities", [])
    relationships = input_data.get("relationships", [])

    if not entities and not relationships:
        raise ValueError("Input data must contain either entities or relationships")

    # Validate entity structure
    for i, entity in enumerate(entities):
        if not isinstance(entity, dict):
            raise ValueError(f"Entity {i} must be a dictionary")

        if "text" not in entity or "type" not in entity:
            raise ValueError(f"Entity {i} must have 'text' and 'type' fields")

    # Validate relationship structure
    for i, relationship in enumerate(relationships):
        if not isinstance(relationship, dict):
            raise ValueError(f"Relationship {i} must be a dictionary")

        required_rel_fields = ["source", "target", "type"]
        for field in required_rel_fields:
            if field not in relationship:
                raise ValueError(f"Relationship {i} must have '{field}' field")


def sanitize_neo4j_label(label: str) -> str:
    """Sanitize a string to be used as a Neo4j label"""
    if not label:
        return "Unknown"

    # Replace spaces and special characters with underscores
    import re

    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", label)

    # Ensure it starts with a letter or underscore
    if sanitized and not sanitized[0].isalpha() and sanitized[0] != "_":
        sanitized = "_" + sanitized

    # Remove multiple consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove trailing underscores
    sanitized = sanitized.rstrip("_")

    return sanitized or "Unknown"


async def log_mapping_results(
    mapped_entities: List[Dict[str, Any]],
    mapped_relationships: List[Dict[str, Any]],
    unmapped_entities: List[Dict[str, Any]],
    unmapped_relationships: List[Dict[str, Any]],
) -> None:
    """Log detailed mapping results for debugging and monitoring"""

    logger.info("=== FIBO Mapping Results ===")
    logger.info(
        f"Entities: {len(mapped_entities)} mapped, {len(unmapped_entities)} unmapped"
    )
    logger.info(
        f"Relationships: {len(mapped_relationships)} mapped, {len(unmapped_relationships)} unmapped"
    )

    # Log unmapped entity types for potential mapping improvements
    if unmapped_entities:
        unmapped_entity_types = {}
        for entity in unmapped_entities:
            entity_type = entity.get("type", "unknown")
            unmapped_entity_types[entity_type] = (
                unmapped_entity_types.get(entity_type, 0) + 1
            )

        logger.warning(f"Unmapped entity types: {unmapped_entity_types}")

    # Log unmapped relationship types
    if unmapped_relationships:
        unmapped_rel_types = {}
        for rel in unmapped_relationships:
            rel_type = rel.get("type", "unknown")
            unmapped_rel_types[rel_type] = unmapped_rel_types.get(rel_type, 0) + 1

        logger.warning(f"Unmapped relationship types: {unmapped_rel_types}")

    # Log successful FIBO mappings
    if mapped_entities:
        fibo_classes_used = {}
        for entity in mapped_entities:
            fibo_class = entity["fibo_mapping"].get("fibo_class_label", "Unknown")
            fibo_classes_used[fibo_class] = fibo_classes_used.get(fibo_class, 0) + 1

        logger.info(f"FIBO classes used: {fibo_classes_used}")

    if mapped_relationships:
        fibo_properties_used = {}
        for rel in mapped_relationships:
            fibo_property = rel["fibo_mapping"].get("fibo_property_label", "Unknown")
            fibo_properties_used[fibo_property] = (
                fibo_properties_used.get(fibo_property, 0) + 1
            )

        logger.info(f"FIBO properties used: {fibo_properties_used}")


# =============================================
# EXISTING TASK IMPLEMENTATIONS
# =============================================


# Task cleanup and cancellation
@celery_app.task(name="cancel_pipeline_run")
@async_task
async def cancel_pipeline_run_task(
    pipeline_run_id: str, pipeline_id: str
) -> Dict[str, Any]:
    """Cancel a running pipeline"""
    from app.services.pipeline import PipelineService

    pipeline_service = PipelineService()

    try:
        # Update pipeline run status to cancelled
        await pipeline_service.update_pipeline_run(
            pipeline_run_id,
            pipeline_id=pipeline_id,
            run_update=PipelineRunUpdate(
                status=PipelineRunStatus.CANCELLED,
                end_time=datetime.now(timezone.utc).isoformat(),
            ),
        )

        # TODO: Cancel any running step tasks
        # This would require tracking and revoking celery task IDs

        return {"success": True, "message": f"Pipeline run {pipeline_run_id} cancelled"}

    except Exception as e:
        logger.error(f"Failed to cancel pipeline run {pipeline_run_id}: {e}")
        return {"success": False, "error": str(e)}


# Existing tasks from your code
@celery_app.task(name="process_file")
@async_task
async def process_file_task(file_id: str):
    """Process a file to extract entities and relationships."""
    from app.tasks.extraction import process_file

    try:
        logger.info(f"Processing file {file_id}")
        result = await process_file(UUID(file_id))
        return {"success": result}
    except Exception as e:
        logger.error(f"Error processing file {file_id}: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="sync_to_neo4j")
@async_task
async def sync_to_neo4j_task(entity_ids=None, relationship_ids=None, batch_size=100):
    """Synchronize entities and relationships to Neo4j."""
    from app.tasks.transformation import (sync_entities_to_neo4j,
                                          sync_relationships_to_neo4j)

    try:
        if entity_ids:
            entity_ids = [UUID(id) for id in entity_ids]
        if relationship_ids:
            relationship_ids = [UUID(id) for id in relationship_ids]

        entity_result = await sync_entities_to_neo4j(
            entity_ids=entity_ids, batch_size=batch_size
        )
        relationship_result = await sync_relationships_to_neo4j(
            relationship_ids=relationship_ids, batch_size=batch_size
        )

        return {"entities": entity_result, "relationships": relationship_result}
    except Exception as e:
        logger.error(f"Error syncing to Neo4j: {str(e)}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="detect_conflicts")
@async_task
async def detect_conflicts_task(threshold=0.75, batch_size=100, entity_types=None):
    """Detect conflicts between entities."""
    from app.tasks.transformation import detect_entity_conflicts

    try:
        result = await detect_entity_conflicts(
            threshold=threshold, batch_size=batch_size, entity_types=entity_types
        )
        return result
    except Exception as e:
        logger.error(f"Error detecting conflicts: {str(e)}")
        return {"status": "failed", "error": str(e)}


# Simple test task
@celery_app.task(name="test_pipeline_task")
def test_pipeline_task(message="Test"):
    """Simple test task"""
    logger.info(f"Test task executed with message: {message}")
    return {"status": "success", "message": message}
