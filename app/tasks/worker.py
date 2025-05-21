import asyncio
import json
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Dict, Optional
from uuid import UUID

from celery import Celery
from celery.signals import worker_process_init

from app.core.config import settings
from app.core.logger import get_logger
from app.schemas.pipeline import PipelineRunStatus, PipelineRunUpdate
from app.schemas.pipeline_step import PipelineRunStatus as StepStatus
from app.schemas.pipeline_step import PipelineStepType
from app.utils.stats_manager import track_stats

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
    task_routes={
        "app.tasks.worker.run_pipeline_task": {"queue": "pipeline"},
        "app.tasks.worker.run_pipeline_step_task": {"queue": "steps"},
    },
)

# Initialize logger
logger = get_logger(__name__)

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
    run_id: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """
    Run a complete pipeline by orchestrating its steps.

    Args:
        pipeline_id: ID of the pipeline to run
        run_id: ID of the pipeline run record (if already created)
        user_id: ID of the user triggering the pipeline
    """
    print("oke")
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
                    start_time=datetime.now(timezone.utc),
                ),
            )

        # Get pipeline steps ordered by run_order
        steps_response = await step_service.get_pipeline_steps(pipeline_id)
        steps = steps_response.data

        if not steps:
            raise Exception("No steps found for pipeline")

        # Sort steps by run_order
        steps.sort(key=lambda x: x["run_order"])

        # Track step outputs and dependencies
        step_outputs = {}
        completed_steps = set()
        step_runs = {}  # Map step_id to step_run_id

        # Execute steps in dependency order
        for step in steps:
            step_id = step["id"]
            step_inputs = step.get("inputs", [])

            # Check dependencies
            if step_inputs:
                missing_deps = set(step_inputs) - completed_steps
                if missing_deps:
                    raise Exception(
                        f"Step {step_id} has unmet dependencies: {missing_deps}"
                    )

                # Gather input data from dependent steps
                input_data = {}
                for dep_step_id in step_inputs:
                    if dep_step_id in step_outputs:
                        input_data[f"step_{dep_step_id}"] = step_outputs[dep_step_id]
            else:
                input_data = {}

            # Execute the step
            logger.info(f"Executing step {step_id} ({step['name']})")

            # Run step and wait for completion
            step_result = await run_pipeline_step_task.apply_async(
                args=[pipeline_id, step_id, run_id, input_data], queue="steps"
            ).get()

            if step_result["status"] == StepStatus.COMPLETED:
                step_outputs[step_id] = step_result.get("output_data", {})
                completed_steps.add(step_id)
                step_runs[step_id] = step_result["step_run_id"]
                logger.info(f"Step {step_id} completed successfully")
            else:
                error_msg = step_result.get("error_message", "Unknown error")
                raise Exception(f"Step {step_id} failed: {error_msg}")

        # Update pipeline run as completed
        if run_id:
            end_time = datetime.now(timezone.utc)
            await pipeline_service.update_pipeline_run(
                run_id,
                pipeline_id=pipeline_id,
                run_update=PipelineRunUpdate(
                    status=PipelineRunStatus.COMPLETED,
                    end_time=end_time,
                    result=step_outputs,
                    stats={
                        "total_steps": len(steps),
                        "completed_steps": len(completed_steps),
                        "step_runs": step_runs,
                    },
                ),
            )

        logger.info(f"Pipeline {pipeline_id} completed successfully")
        return {
            "success": True,
            "pipeline_id": pipeline_id,
            "run_id": run_id,
            "status": PipelineRunStatus.COMPLETED,
            "steps_completed": len(completed_steps),
            "result": step_outputs,
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
                    end_time=datetime.now(timezone.utc),
                    error_message=error_message,
                ),
            )

        return {
            "success": False,
            "error": error_message,
            "pipeline_id": pipeline_id,
            "run_id": run_id,
        }


@celery_app.task(name="run_pipeline_step", bind=True)
@async_task
@track_stats
async def run_pipeline_step_task(
    self,
    pipeline_id: str,
    step_id: str,
    pipeline_run_id: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None,
):
    """
    Execute a single pipeline step.

    Args:
        pipeline_id: ID of the pipeline
        step_id: ID of the step to run
        pipeline_run_id: ID of the pipeline run
        input_data: Input data from previous steps
    """
    step_service = PipelineStepService()
    step_run_id = None

    try:
        logger.info(f"Starting step {step_id} in pipeline {pipeline_id}")

        # Get step details
        step = await step_service.get_pipeline_step(step_id)
        step_type = step["step_type"]
        config = (
            json.loads(step["config"])
            if isinstance(step["config"], str)
            else step["config"]
        )

        # Create step run record
        step_run_data = {
            "pipeline_run_id": pipeline_run_id,
            "step_id": step_id,
            "status": StepStatus.RUNNING,
            "run_order": step["run_order"],
            "input_data": input_data,
            "celery_task_id": self.request.id,
            "start_time": datetime.now(timezone.utc).isoformat(),
        }

        step_run = await step_service.create_step_run(step_run_data)
        step_run_id = step_run["id"]

        # Execute step based on type
        output_data = await execute_step_by_type(step_type, config, input_data)

        # Update step run as completed
        await step_service.update_pipeline_step_run(
            step_run_id,
            {
                "status": StepStatus.COMPLETED,
                "end_time": datetime.now(timezone.utc).isoformat(),
                "output_data": output_data,
            },
        )

        logger.info(f"Step {step_id} completed successfully")
        return {
            "status": StepStatus.COMPLETED,
            "step_run_id": step_run_id,
            "step_id": step_id,
            "output_data": output_data,
        }

    except Exception as e:
        error_message = f"Step execution failed: {str(e)}"
        logger.error(f"Step {step_id} failed: {error_message}")

        # Update step run as failed
        if step_run_id:
            await step_service.update_pipeline_step_run(
                step_run_id,
                {
                    "status": StepStatus.FAILED,
                    "end_time": datetime.now(timezone.utc).isoformat(),
                    "error_message": error_message,
                },
            )

        return {
            "status": StepStatus.FAILED,
            "step_run_id": step_run_id,
            "step_id": step_id,
            "error_message": error_message,
        }


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


# Step execution implementations
async def execute_file_reader_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute file reader step"""
    from app.tasks.extraction import process_file

    file_id = config.get("file_id")
    if not file_id:
        raise ValueError("file_id is required for file reader step")

    result = await process_file(UUID(file_id))

    return {
        "file_processed": result,
        "file_id": file_id,
        "processing_status": "completed" if result else "failed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def execute_api_fetcher_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute API fetcher step"""
    from app.tasks.ingestion import ingest_api_data

    required_fields = ["url", "data_format", "datasource_id"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"{field} is required for API fetcher step")

    result = await ingest_api_data(
        api_url=config["url"],
        data_format=config["data_format"],
        datasource_id=UUID(config["datasource_id"]),
        user_id=UUID(config["user_id"]) if config.get("user_id") else None,
        auth_params=config.get("auth_params"),
        query_params=config.get("query_params"),
        headers=config.get("headers"),
    )

    return {
        "api_data_ingested": bool(result),
        "file_id": result.get("id") if result else None,
        "api_url": config["url"],
        "data_format": config["data_format"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def execute_database_extractor_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute database extractor step"""
    from app.tasks.ingestion import ingest_database_data

    required_fields = ["connection_string", "query", "datasource_id"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"{field} is required for database extractor step")

    result = await ingest_database_data(
        connection_string=config["connection_string"],
        query=config["query"],
        datasource_id=UUID(config["datasource_id"]),
        user_id=UUID(config["user_id"]) if config.get("user_id") else None,
        output_format=config.get("output_format", "csv"),
    )

    return {
        "database_data_extracted": bool(result),
        "file_id": result.get("id") if result else None,
        "query": config["query"],
        "output_format": config.get("output_format", "csv"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def execute_text_extractor_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute text extractor step"""
    # Implement text extraction logic based on your existing text processing
    input_format = config.get("input_format", "pdf")
    extract_tables = config.get("extract_tables", False)
    extract_metadata = config.get("extract_metadata", True)

    # Get file from input data or config
    file_id = None
    if input_data:
        file_id = input_data.get("file_id")
    if not file_id:
        file_id = config.get("file_id")

    if not file_id:
        raise ValueError("file_id is required for text extractor step")

    # Use your existing text extraction logic
    # This is a placeholder - integrate with your actual text extraction
    return {
        "text_extracted": True,
        "input_format": input_format,
        "extracted_metadata": {"format": input_format} if extract_metadata else {},
        "tables_extracted": [] if extract_tables else None,
        "file_id": file_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def execute_llm_entity_extractor_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute LLM entity extractor step"""
    # Integrate with your existing entity extraction
    model = config.get("model", "gpt-3.5-turbo")
    entity_types = config.get("entity_types", [])

    # Get extracted text from previous step or file
    text_content = None
    if input_data:
        text_content = input_data.get("extracted_text")

    if not text_content:
        raise ValueError("No text content available for entity extraction")

    # Use your existing entity extraction logic
    # This is a placeholder - integrate with your actual entity extraction
    return {
        "entities_extracted": True,
        "entity_count": 0,  # Replace with actual count
        "model_used": model,
        "entity_types": entity_types,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def execute_entity_resolution_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute entity resolution step"""
    from app.tasks.transformation import detect_entity_conflicts

    resolution_strategy = config.get("resolution_strategy", "exact_match")
    similarity_threshold = config.get("similarity_threshold", 0.8)

    result = await detect_entity_conflicts(
        threshold=similarity_threshold,
        batch_size=config.get("batch_size", 100),
        entity_types=config.get("entity_types"),
    )

    return {
        "entity_resolution_completed": True,
        "resolution_strategy": resolution_strategy,
        "similarity_threshold": similarity_threshold,
        "conflicts_detected": result.get("conflicts_detected", 0),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def execute_fibo_mapper_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute FIBO mapper step"""
    mapping_confidence_threshold = config.get("mapping_confidence_threshold", 0.7)
    domains = config.get("domains", [])

    # Implement FIBO mapping logic
    # This is a placeholder for your FIBO mapping implementation
    return {
        "fibo_mapping_completed": True,
        "mapping_confidence_threshold": mapping_confidence_threshold,
        "domains_processed": domains,
        "mappings_created": 0,  # Replace with actual count
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def execute_knowledge_graph_writer_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute knowledge graph writer step"""
    from app.tasks.transformation import (sync_entities_to_neo4j,
                                          sync_relationships_to_neo4j)

    batch_size = config.get("batch_size", 100)

    # Sync entities and relationships to Neo4j
    entity_result = await sync_entities_to_neo4j(batch_size=batch_size)
    relationship_result = await sync_relationships_to_neo4j(batch_size=batch_size)

    return {
        "knowledge_graph_updated": True,
        "entities_synced": entity_result.get("entities_created", 0),
        "relationships_synced": relationship_result.get("relationships_created", 0),
        "batch_size": batch_size,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def execute_custom_python_step(
    config: Dict[str, Any], input_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute custom Python code step"""
    import os
    import subprocess
    import tempfile

    code = config.get("code")
    if not code:
        raise ValueError("code is required for custom Python step")

    requirements = config.get("requirements", [])
    input_mapping = config.get("input_mapping", {})
    output_mapping = config.get("output_mapping", {})
    timeout = config.get("timeout", 60)

    # Prepare input data based on mapping
    mapped_inputs = {}
    if input_data and input_mapping:
        for key, source_key in input_mapping.items():
            if source_key in input_data:
                mapped_inputs[key] = input_data[source_key]

    # Create temporary script file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(f"import json\n")
        f.write(f"import sys\n")
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

        # Apply output mapping
        if output_mapping:
            mapped_output = {}
            for target_key, source_key in output_mapping.items():
                if source_key in output:
                    mapped_output[target_key] = output[source_key]
            output = mapped_output

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
                end_time=datetime.now(timezone.utc),
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


@celery_app.task(name="enrich_entities")
@async_task
async def enrich_entities_task(entity_ids=None, batch_size=100, force_update=False):
    """Enrich entities with embeddings."""
    from app.tasks.transformation import enrich_entities_with_embeddings

    try:
        if entity_ids:
            entity_ids = [UUID(id) for id in entity_ids]

        result = await enrich_entities_with_embeddings(
            entity_ids=entity_ids, batch_size=batch_size, force_update=force_update
        )
        return result
    except Exception as e:
        logger.error(f"Error enriching entities: {str(e)}")
        return {"status": "failed", "error": str(e)}


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
@celery_app.task(name='test_pipeline_task')
def test_pipeline_task(message="Test"):
    """Simple test task"""
    logger.info(f"Test task executed with message: {message}")
    return {"status": "success", "message": message}
