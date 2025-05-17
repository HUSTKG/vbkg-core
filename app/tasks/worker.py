import logging
from celery import Celery, chain, shared_task, signature
from celery.signals import worker_process_init
import asyncio
from functools import wraps

from typing import Dict, Optional
from kombu import Any

from app.core.config import settings
from app.schemas.pipeline import PipelineStepType
from app.utils.stats_manager import track_stats

# Create Celery app
celery_app = Celery(
    "knowledge_graph_worker",
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
)

# Initialize logger
logger = logging.getLogger(__name__)

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


@celery_app.task(name="process_file")
@async_task
async def process_file_task(file_id: str):
    """
    Process a file to extract entities and relationships.

    Args:
        file_id: ID of the file to process
    """
    from app.tasks.extraction import process_file
    from uuid import UUID

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
    """
    Enrich entities with embeddings.

    Args:
        entity_ids: List of entity IDs to enrich, or None to process all entities without embeddings
        batch_size: Number of entities to process in each batch
        force_update: Whether to update embeddings even if they already exist
    """
    from app.tasks.transformation import enrich_entities_with_embeddings
    from uuid import UUID

    try:
        logger.info(
            f"Enriching entities with embeddings: {len(entity_ids) if entity_ids else 'all'}"
        )

        # Convert string IDs to UUID
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
    """
    Synchronize entities and relationships to Neo4j.

    Args:
        entity_ids: List of entity IDs to synchronize, or None to process all entities without Neo4j ID
        relationship_ids: List of relationship IDs to synchronize, or None to process all relationships without Neo4j ID
        batch_size: Number of items to process in each batch
    """
    from app.tasks.transformation import (
        sync_entities_to_neo4j,
        sync_relationships_to_neo4j,
    )
    from uuid import UUID

    try:
        logger.info(
            f"Syncing to Neo4j: {len(entity_ids) if entity_ids else 'all'} entities, {len(relationship_ids) if relationship_ids else 'all'} relationships"
        )

        # Convert string IDs to UUID
        if entity_ids:
            entity_ids = [UUID(id) for id in entity_ids]

        if relationship_ids:
            relationship_ids = [UUID(id) for id in relationship_ids]

        # Sync entities first
        entity_result = await sync_entities_to_neo4j(
            entity_ids=entity_ids, batch_size=batch_size
        )

        # Sync relationships
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
    """
    Detect conflicts between entities.

    Args:
        threshold: Similarity threshold for conflict detection
        batch_size: Number of entities to process in each batch
        entity_types: Types of entities to process, or None to process all types
    """
    from app.tasks.transformation import detect_entity_conflicts

    try:
        logger.info(
            f"Detecting entity conflicts: threshold={threshold}, entity_types={entity_types or 'all'}"
        )

        result = await detect_entity_conflicts(
            threshold=threshold, batch_size=batch_size, entity_types=entity_types
        )

        return result

    except Exception as e:
        logger.error(f"Error detecting conflicts: {str(e)}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="ingest_api_data")
@async_task
async def ingest_api_data_task(
    api_url,
    data_format,
    datasource_id,
    user_id=None,
    auth_params=None,
    query_params=None,
    headers=None,
):
    """
    Ingest data from an API.

    Args:
        api_url: URL of the API
        data_format: Format of the data (json, xml, etc.)
        datasource_id: ID of the data source
        user_id: ID of the user initiating the ingestion
        auth_params: Authentication parameters
        query_params: Query parameters
        headers: Request headers
    """
    from app.tasks.ingestion import ingest_api_data
    from uuid import UUID

    try:
        logger.info(f"Ingesting API data from {api_url}")

        result = await ingest_api_data(
            api_url=api_url,
            data_format=data_format,
            datasource_id=UUID(datasource_id),
            user_id=UUID(user_id) if user_id else None,
            auth_params=auth_params,
            query_params=query_params,
            headers=headers,
        )

        return {"success": bool(result), "file_id": result["id"] if result else None}

    except Exception as e:
        logger.error(f"Error ingesting API data from {api_url}: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="ingest_database_data")
@async_task
async def ingest_database_data_task(
    connection_string, query, datasource_id, user_id=None, output_format="csv"
):
    """
    Ingest data from a database.

    Args:
        connection_string: Database connection string
        query: SQL query to execute
        datasource_id: ID of the data source
        user_id: ID of the user initiating the ingestion
        output_format: Format to save the data (csv, json)
    """
    from app.tasks.ingestion import ingest_database_data
    from uuid import UUID

    try:
        logger.info(f"Ingesting database data with query: {query}")

        result = await ingest_database_data(
            connection_string=connection_string,
            query=query,
            datasource_id=UUID(datasource_id),
            user_id=UUID(user_id) if user_id else None,
            output_format=output_format,
        )

        return {"success": bool(result), "file_id": result["id"] if result else None}

    except Exception as e:
        logger.error(f"Error ingesting database data: {str(e)}")
        return {"success": False, "error": str(e)}


@shared_task(name="run_pipeline", bind=True)
@async_task
async def run_pipeline_task(
    pipeline_id: str,
    pipeline_run_id: Optional[str] = None,
):
    """
    Run a data pipeline.

    Args:
        pipeline_id: ID of the pipeline to run
        pipeline_run_id: ID of the pipeline run record, or None to create a new one
    """
    from app.core.supabase import get_supabase

    try:
        supabase = await get_supabase()
        logger.info(f"Running pipeline {pipeline_id}")

        # Create celery chain

        steps = (
            await supabase.table("pipeline_steps")
            .select("*")
            .eq("pipeline_id", pipeline_id)
            .order("order", desc=False)
            .execute()
        )

        # Create a chain of tasks based on pipeline steps

        tasks = []

        for step in steps.data:
            step_id = step["id"]
            task_name = "run_pipeline_step_task"
            task = run_pipeline_step_task.s(
                pipeline_id=pipeline_id,
                step_id=step_id,
                pipeline_run_id=pipeline_run_id,
                params=step["config"],
            )

            tasks.append(task)

        result = chain(*tasks).apply_async()

        return {
            "success": True,
            "pipeline_run_id": pipeline_run_id,
            "task_id": result,
        }

    except Exception as e:
        logger.error(f"Error running pipeline {pipeline_id}: {str(e)}")
        return {"success": False, "error": str(e)}


@celery_app.task(name="run_pipeline_step", bind=True)
@async_task
@track_stats
async def run_pipeline_step_task(
    pipeline_id: str,
    step_id: str,
    pipeline_run_id: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
):
    """
    Run a specific step of a data pipeline.
    Args:
        pipeline_id: ID of the pipeline
        step_id: ID of the step to run
        pipeline_run_id: ID of the pipeline run record, or None to create a new one
        params: Step parameters
    """
    from app.services.pipeline import PipelineService

    try:
        pipeline_service = PipelineService()
        logger.info(f"Running pipeline step {step_id} in pipeline {pipeline_id}")
        # Fetch the pipeline and step details
        steps = await pipeline_service.get_pipeline_steps(pipeline_id=pipeline_id)
        # Find the specific step to run
        step = next((s for s in steps.data if s.id == step_id), None)
        if not step:
            logger.error(f"Step {step_id} not found in pipeline {pipeline_id}")
            return {"success": False, "error": f"Step {step_id} not found"}
        # Execute the task based on the step type
        if step.step_type == PipelineStepType.API_FETCHER:
            from app.tasks.ingestion import ingest_api_data

            result = await ingest_api_data(
                api_url=step.config["api_url"],
                data_format=step.config["data_format"],
                datasource_id=step.config["datasource_id"],
                user_id=step.config.get("user_id"),
                auth_params=step.config.get("auth_params"),
                query_params=step.config.get("query_params"),
                headers=step.config.get("headers"),
            )
            return result

        elif step.step_type == PipelineStepType.FILE_READER:
            from app.tasks.ingestion import process_file

            result = await process_file(step.config["file_id"])
            return result
        elif step.step_type == PipelineStepType.DATABASE_EXTRACTOR:
            from app.tasks.ingestion import ingest_database_data

            result = await ingest_database_data(
                connection_string=step.config["connection_string"],
                query=step.config["query"],
                datasource_id=step.config["datasource_id"],
                user_id=step.config.get("user_id"),
                output_format=step.config.get("output_format") or "csv",
            )
            return result
        elif step.step_type == PipelineStepType.TEXT_EXTRACTOR:
            return
        elif step.step_type == PipelineStepType.LLM_ENTITY_EXTRACTOR:

            return
        elif step.step_type == PipelineStepType.ENTITY_RESOLUTION:
            return
        elif step.step_type == PipelineStepType.FIBO_MAPPER:
            return
        elif step.step_type == PipelineStepType.KNOWLEDGE_GRAPH_WRITER:
            return
        else:
            logger.error(f"Unknown pipeline step type: {step.step_type}")
            return {
                "success": False,
                "error": f"Unknown pipeline step type: {step.step_type}",
            }
    except Exception as e:
        logger.error(f"Error running pipeline step {step_id}: {str(e)}")
        return {"success": False, "error": str(e)}
