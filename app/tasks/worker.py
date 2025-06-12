import asyncio
import json
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
from app.tasks.executors import STEP_EXECUTORS

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

        logger.info(f"Found {len(steps)} steps in pipeline")

        # Sort steps by run_order and organize by dependency levels
        dependency_levels = organize_steps_by_dependency_levels(steps)

        logger.info(f"Pipeline will execute in {len(dependency_levels)} levels")
        for i, level in enumerate(dependency_levels):
            level_names = [step['name'] for step in level]
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
                    dependencies.update([dep.strip() for dep in step["depends_on"].split(",") if dep.strip()])
            
            # Check "inputs" field for backwards compatibility
            if step.get("inputs"):
                if isinstance(step["inputs"], list):
                    dependencies.update(step["inputs"])
                elif isinstance(step["inputs"], str):
                    dependencies.update([dep.strip() for dep in step["inputs"].split(",") if dep.strip()])

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
            f"Step type: {step_type}, config keys: {list(config.keys()) if config else []}"
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
        step_run_data = PipelineStepRunCreate(
            pipeline_run_id=pipeline_run_id,
            step_id=step_id,
            status=StepStatus.RUNNING,
            run_order=step["run_order"],
            input_data=resolved_input_data,
            celery_task_id=self.request.id,
            start_time=datetime.now(timezone.utc),
        )

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
            step_run_update=PipelineStepRunUpdate(
                status=StepStatus.COMPLETED,
                end_time=datetime.now(timezone.utc),
                output_data=output_data,
            ),
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
        logger.error(traceback.format_exc())

        # Update step run as failed
        if step_run_id:
            await step_service.update_pipeline_step_run(
                step_run_id=step_run_id,
                pipeline_run_id=pipeline_run_id,
                step_run_update=PipelineStepRunUpdate(
                    status=StepStatus.FAILED,
                    end_time=datetime.now(timezone.utc),
                    error_message=error_message,
                ),
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
            step_inputs.update([s.strip() for s in step["depends_on"].split(",") if s.strip()])
    
    # Check "inputs" field for backwards compatibility
    if step.get("inputs"):
        if isinstance(step["inputs"], list):
            step_inputs.update(step["inputs"])
        elif isinstance(step["inputs"], str) and step["inputs"]:
            step_inputs.update([s.strip() for s in step["inputs"].split(",") if s.strip()])

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
    
    # Get dependencies from both "depends_on" and "inputs" fields
    step_inputs = set()
    
    # Check "depends_on" field
    if step.get("depends_on"):
        if isinstance(step["depends_on"], list):
            step_inputs.update(step["depends_on"])
        elif isinstance(step["depends_on"], str) and step["depends_on"]:
            step_inputs.update([s.strip() for s in step["depends_on"].split(",") if s.strip()])
    
    # Check "inputs" field for backwards compatibility
    if step.get("depends_on"):
        if isinstance(step["depends_on"], list):
            step_inputs.update(step["depends_on"])
        elif isinstance(step["depends_on"], str) and step["depends_on"]:
            step_inputs.update([s.strip() for s in step["depends_on"].split(",") if s.strip()])

    step_inputs = list(step_inputs)  # Convert to list

    logger.info(
            f"Resolving input data for step {step['id']} - inputs: {step_inputs}"
            )

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
    step_type: str, config: Dict[str, Any], input_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute a step based on its type using the executor classes.

    Args:
        step_type: Type of the step
        config: Step configuration
        input_data: Input data from previous steps

    Returns:
        Output data from step execution
    """
    try:
        # Get step executor from the STEP_EXECUTORS mapping
        step_type_enum = PipelineStepType(step_type)
        executor_class = STEP_EXECUTORS.get(step_type_enum)

        if not executor_class:
            raise ValueError(f"No executor found for step type: {step_type}")

        # Create executor instance
        step_metadata = {
            "step_type": step_type,
        }
        executor = executor_class(config, step_metadata)

        # Execute step
        output_data = await executor.execute(input_data or {})

        return output_data

    except Exception as e:
        logger.error(f"Error executing step type {step_type}: {str(e)}")
        raise


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
            if step_run.get("celery_task_id") and step_run["status"] == StepStatus.RUNNING:
                try:
                    celery_app.control.revoke(step_run["celery_task_id"], terminate=True)
                    
                    # Update step run status
                    await step_service.update_pipeline_step_run(
                        step_run["id"],
                        run_id,
                        PipelineStepRunUpdate(
                            status=StepStatus.CANCELLED,
                            end_time=datetime.now(timezone.utc),
                            error_message="Cancelled by user",
                        ),
                    )
                except Exception as e:
                    logger.error(f"Failed to cancel step task {step_run['celery_task_id']}: {e}")

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
