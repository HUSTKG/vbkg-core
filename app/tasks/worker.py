import os
import logging
from celery import Celery
from celery.signals import worker_process_init
import asyncio
from functools import wraps

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "knowledge_graph_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
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
        logger.info(f"Enriching entities with embeddings: {len(entity_ids) if entity_ids else 'all'}")
        
        # Convert string IDs to UUID
        if entity_ids:
            entity_ids = [UUID(id) for id in entity_ids]
        
        result = await enrich_entities_with_embeddings(
            entity_ids=entity_ids,
            batch_size=batch_size,
            force_update=force_update
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
    from app.tasks.transformation import sync_entities_to_neo4j, sync_relationships_to_neo4j
    from uuid import UUID
    
    try:
        logger.info(f"Syncing to Neo4j: {len(entity_ids) if entity_ids else 'all'} entities, {len(relationship_ids) if relationship_ids else 'all'} relationships")
        
        # Convert string IDs to UUID
        if entity_ids:
            entity_ids = [UUID(id) for id in entity_ids]
        
        if relationship_ids:
            relationship_ids = [UUID(id) for id in relationship_ids]
        
        # Sync entities first
        entity_result = await sync_entities_to_neo4j(
            entity_ids=entity_ids,
            batch_size=batch_size
        )
        
        # Sync relationships
        relationship_result = await sync_relationships_to_neo4j(
            relationship_ids=relationship_ids,
            batch_size=batch_size
        )
        
        return {
            "entities": entity_result,
            "relationships": relationship_result
        }
    
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
        logger.info(f"Detecting entity conflicts: threshold={threshold}, entity_types={entity_types or 'all'}")
        
        result = await detect_entity_conflicts(
            threshold=threshold,
            batch_size=batch_size,
            entity_types=entity_types
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error detecting conflicts: {str(e)}")
        return {"status": "failed", "error": str(e)}

@celery_app.task(name="run_pipeline")
@async_task
async def run_pipeline_task(pipeline_id, pipeline_run_id=None, params=None):
    """
    Run a data pipeline.
    
    Args:
        pipeline_id: ID of the pipeline to run
        pipeline_run_id: ID of the pipeline run record, or None to create a new one
        params: Pipeline parameters
    """
    from app.services.data_extraction import run_pipeline
    from uuid import UUID
    
    try:
        logger.info(f"Running pipeline {pipeline_id}")
        
        result = await run_pipeline(
            pipeline_id=UUID(pipeline_id),
            pipeline_run_id=UUID(pipeline_run_id) if pipeline_run_id else None,
            params=params
        )
        
        return {"success": result}
    
    except Exception as e:
        logger.error(f"Error running pipeline {pipeline_id}: {str(e)}")
        return {"success": False, "error": str(e)}

@celery_app.task(name="ingest_api_data")
@async_task
async def ingest_api_data_task(api_url, data_format, datasource_id, user_id=None, auth_params=None, query_params=None, headers=None):
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
            headers=headers
        )
        
        return {"success": bool(result), "file_id": result["id"] if result else None}
    
    except Exception as e:
        logger.error(f"Error ingesting API data from {api_url}: {str(e)}")
        return {"success": False, "error": str(e)}

@celery_app.task(name="ingest_database_data")
@async_task
async def ingest_database_data_task(connection_string, query, datasource_id, user_id=None, output_format="csv"):
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
            output_format=output_format
        )
        
        return {"success": bool(result), "file_id": result["id"] if result else None}
    
    except Exception as e:
        logger.error(f"Error ingesting database data: {str(e)}")
        return {"success": False, "error": str(e)}
