from datetime import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from fastapi import HTTPException, status

from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.core.supabase import get_supabase
from app.nlp.entity_extraction import extract_entities
from app.nlp.relation_extraction import extract_relationships
from app.nlp.text_chunking import chunk_text
from app.schemas.pipeline import PipelineCreate, PipelineRunCreate, PipelineStep, PipelineStepType, PipelineUpdate, StepConfig
from app.utils.file_handler import get_file_type, parse_file_content
from app.utils.s3 import download_file_from_s3

logger = logging.getLogger(__name__)

class DataExtractionService:
    """
    Service class for data extraction and pipeline management.
    """

    async def get_datasources(
        self,
        skip: int = 0,
        limit: int = 100,
        source_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of data sources with optional filtering.
        """
        try:
            supabase = await get_supabase() 
            query = supabase.table("data_sources").select("*")
            
            if source_type:
                query = query.eq("source_type", source_type)
            
            if is_active is not None:
                query = query.eq("is_active", is_active)
            
            response = await query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
            return response.data
        
        except Exception as e:
            logger.error(f"Error getting data sources: {e}")
            return []

    async def get_datasource(self, datasource_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a specific data source by ID.
        """
        try:
            supabase = await get_supabase() 
            response = await supabase.table("data_sources").select("*").eq("id", str(datasource_id)).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error getting data source {datasource_id}: {e}")
            return None

    async def create_datasource(
        self,
        datasource_in: Dict[str, Any],
        created_by: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new data source.
        """
        try:
            supabase = await get_supabase()
            
            data = {
                "name": datasource_in["name"],
                "description": datasource_in.get("description"),
                "source_type": datasource_in["source_type"],
                "connection_details": datasource_in["connection_details"],
                "credentials": datasource_in.get("credentials"),
                "is_active": datasource_in.get("is_active", True),
                "created_by": str(created_by) if created_by else None
            }
            
            response = await supabase.table("data_sources").insert(data).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error creating data source: {e}")
            return None

    async def update_datasource(
        self,
        datasource_id: UUID,
        datasource_in: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing data source.
        """
        try:
            supabase = await get_supabase()
            
            # Prepare update data
            data = {}
            
            if "name" in datasource_in:
                data["name"] = datasource_in["name"]
            
            if "description" in datasource_in:
                data["description"] = datasource_in["description"]
            
            if "connection_details" in datasource_in:
                data["connection_details"] = datasource_in["connection_details"]
            
            if "credentials" in datasource_in:
                data["credentials"] = datasource_in["credentials"]
            
            if "is_active" in datasource_in:
                data["is_active"] = datasource_in["is_active"]
            
            if not data:
                # Nothing to update
                return await self.get_datasource(datasource_id)
            
            response = await supabase.table("data_sources").update(data).eq("id", str(datasource_id)).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error updating data source {datasource_id}: {e}")
            return None

    async def delete_datasource(self, datasource_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Delete a data source.
        """
        try:
            supabase = await get_supabase()
            
            # Get the data source first
            datasource = await self.get_datasource(datasource_id)
            if not datasource:
                return None
            
            # Delete the data source
            response = await supabase.table("data_sources").delete().eq("id", str(datasource_id)).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error deleting data source {datasource_id}: {e}")
            return None

    # File Upload Management

    async def create_file_upload(
        self,
        file_upload_in: Dict[str, Any],
        uploaded_by: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new file upload record.
        """
        try:
            supabase = await get_supabase()
            
            data = {
                "data_source_id": str(file_upload_in["data_source_id"]),
                "file_name": file_upload_in["file_name"],
                "file_type": file_upload_in["file_type"],
                "file_size": file_upload_in["file_size"],
                "storage_path": file_upload_in["storage_path"],
                "upload_status": file_upload_in.get("upload_status", "pending"),
                "processed": file_upload_in.get("processed", False),
                "metadata": file_upload_in.get("metadata", {}),
                "uploaded_by": str(uploaded_by) if uploaded_by else None
            }
            
            response = await supabase.table("file_uploads").insert(data).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error creating file upload: {e}")
            return None

    async def get_file_uploads(
        self,
        skip: int = 0,
        limit: int = 100,
        datasource_id: Optional[UUID] = None,
        status: Optional[str] = None,
        processed: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of file uploads with optional filtering.
        """
        try:
            supabase = await get_supabase()
            query = supabase.table("file_uploads").select("*")
            
            if datasource_id:
                query = query.eq("data_source_id", str(datasource_id))
            
            if status:
                query = query.eq("upload_status", status)
            
            if processed is not None:
                query = query.eq("processed", processed)
            
            response = await query.range(skip, skip + limit - 1).order("uploaded_at", desc=True).execute()
            return response.data
        
        except Exception as e:
            logger.error(f"Error getting file uploads: {e}")
            return []

    async def get_file_upload(self, file_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a specific file upload by ID.
        """
        try:
            supabase = await get_supabase()
            response = await supabase.table("file_uploads").select("*").eq("id", str(file_id)).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error getting file upload {file_id}: {e}")
            return None

    async def update_file_upload_status(
        self,
        file_id: UUID,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update the status of a file upload.
        """
        try:
            supabase = await get_supabase()
            
            data: dict[str, Any] = {"upload_status": status}
            
            if metadata:
                data["metadata"] = metadata
            
            if status == "completed":
                data["processed"] = True
            
            response = await supabase.table("file_uploads").update(data).eq("id", str(file_id)).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error updating file upload status {file_id}: {e}")
            return None



    async def create_pipeline_run(
        self,
        pipeline_run_in: PipelineRunCreate 
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new pipeline run record.
        """
        try:
            supabase = await get_supabase()
            
            now = datetime.utcnow().isoformat()
            
            data = {
                "pipeline_id": str(pipeline_run_in.pipeline_id),
                "status": pipeline_run_in.status,
                "start_time": now,
                "triggered_by": pipeline_run_in.triggered_by if pipeline_run_in.triggered_by else None,
            }
            
            response = await supabase.table("pipeline_runs").insert(data).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error creating pipeline run: {e}")
            return None

    async def get_pipeline_runs(
        self,
        skip: int = 0,
        limit: int = 100,
        pipeline_id: Optional[UUID] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of pipeline runs with optional filtering.
        """
        try:
            supabase = await get_supabase()
            query = supabase.table("pipeline_runs").select("*")
            
            if pipeline_id:
                query = query.eq("pipeline_id", str(pipeline_id))
            
            if status:
                query = query.eq("status", status)
            
            response = await query.range(skip, skip + limit - 1).order("start_time", desc=True).execute()
            return response.data
        
        except Exception as e:
            logger.error(f"Error getting pipeline runs: {e}")
            return []

    async def get_pipeline_run(self, run_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a specific pipeline run by ID.
        """
        try:
            supabase = await get_supabase()
            response = await supabase.table("pipeline_runs").select("*").eq("id", str(run_id)).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error getting pipeline run {run_id}: {e}")
            return None

    async def update_pipeline_run_status(
        self,
        run_id: UUID,
        status: str,
        end_time: Optional[str] = None,
        duration: Optional[int] = None,
        log: Optional[str] = None,
        error_message: Optional[str] = None,
        stats: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update the status of a pipeline run.
        """
        try:
            supabase = await get_supabase()
            
            data: dict[str, Any] = {"status": status}
            
            if end_time:
                data["end_time"] = end_time
            
            if duration is not None:
                data["duration"] = duration
            
            if log:
                data["log"] = log
            
            if error_message:
                data["error_message"] = error_message
            
            if stats:
                data["stats"] = stats
            
            response = await supabase.table("pipeline_runs").update(data).eq("id", str(run_id)).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error updating pipeline run status {run_id}: {e}")
            return None

    async def run_pipeline(
        self,
        pipeline_id: UUID,
        pipeline_run_id: UUID,
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Execute a pipeline.
        """
        try:
            pipeline = await self.get_pipeline(pipeline_id)
            if not pipeline:
                logger.error(f"Pipeline {pipeline_id} not found")
                return False
            
            # Update status to running
            await self.update_pipeline_run_status(
                run_id=pipeline_run_id,
                status="running"
            )
            
            # Get pipeline steps
            steps = pipeline["steps"]
            
            # Execute each step in sequence
            log_entries = []
            stats = {}
            start_time = datetime.utcnow()
            
            try:
                for i, step in enumerate(steps):
                    step_start = datetime.utcnow()
                    step_type = step["type"]
                    step_config = json.loads(step["config"])

                    print(type(step_config))
                    
                    log_entries.append(f"[{step_start.isoformat()}] Starting step {i+1}/{len(steps)}: {step_type}")
                    
                    # Execute the step based on type
                    if step_type == PipelineStepType.DATABASE_EXTRACTOR.value:
                        datasource_id = step_config["datasource_id"]
                        result = await self.extract_from_datasource(datasource_id, step_config)
                        stats[f"step_{i+1}_entities"] = result["entity_count"]
                        stats[f"step_{i+1}_relationships"] = result["relationship_count"]
                    
                    elif step_type == PipelineStepType.FILE_READER.value:
                        file_id = step_config["file_id"]
                        result = await self.extract_from_file(UUID(file_id), step_config)
                        stats[f"step_{i+1}_entities"] = result["entity_count"]
                        stats[f"step_{i+1}_relationships"] = result["relationship_count"]
                    
                    elif step_type == PipelineStepType.ENTITY_RESOLUTION.value:
                        threshold = step_config.get("threshold", 0.8)
                        entity_types = step_config.get("entity_types", [])
                        result = await self.run_entity_resolution(threshold, entity_types)
                        stats[f"step_{i+1}_conflicts"] = result["conflict_count"]
                    
                    elif step_type == PipelineStepType.KNOWLEDGE_GRAPH_WRITER.value:
                        result = await self.update_knowledge_graph()
                        stats[f"step_{i+1}_updated_entities"] = result["updated_entities"]
                        stats[f"step_{i+1}_updated_relationships"] = result["updated_relationships"]
                    
                    else:
                        log_entries.append(f"[{datetime.utcnow().isoformat()}] Unsupported step type: {step_type}")
                        continue
                    
                    step_end = datetime.utcnow()
                    step_duration = (step_end - step_start).total_seconds()
                    log_entries.append(f"[{step_end.isoformat()}] Completed step {i+1}/{len(steps)} in {step_duration:.2f}s")
                
                # All steps completed successfully
                end_time = datetime.utcnow()
                duration = int((end_time - start_time).total_seconds())
                
                stats["total_duration"] = duration
                stats["parameters"] = params or {}
                
                await self.update_pipeline_run_status(
                    run_id=pipeline_run_id,
                    status="completed",
                    end_time=end_time.isoformat(),
                    duration=duration,
                    log="\n".join(log_entries),
                    stats=stats
                )
                
                return True
                
            except Exception as e:
                error_message = f"Pipeline execution error: {str(e)}"
                log_entries.append(f"[{datetime.utcnow().isoformat()}] {error_message}")
                
                end_time = datetime.utcnow()
                duration = int((end_time - start_time).total_seconds())
                
                await self.update_pipeline_run_status(
                    run_id=pipeline_run_id,
                    status="failed",
                    end_time=end_time.isoformat(),
                    duration=duration,
                    log="\n".join(log_entries),
                    error_message=error_message,
                    stats=stats
                )
                
                logger.error(f"Pipeline execution error {pipeline_id}: {e}")
                return False
        
        except Exception as e:
            logger.error(f"Error setting up pipeline execution {pipeline_id}: {e}")
            
            # Update status to failed
            await self.update_pipeline_run_status(
                run_id=pipeline_run_id,
                status="failed",
                end_time=datetime.utcnow().isoformat(),
                error_message=f"Pipeline setup error: {str(e)}"
            )
            
            return False

    async def cancel_pipeline_run(self, run_id: UUID) -> bool:
        """
        Cancel a running pipeline.
        """
        try:
            # This is a simple implementation. In a real system, you would need
            # to implement a mechanism to actually interrupt the running tasks.
            
            pipeline_run = await self.get_pipeline_run(run_id)
            if not pipeline_run:
                return False
            
            if pipeline_run["status"] not in ["pending", "running"]:
                return False
            
            await self.update_pipeline_run_status(
                run_id=run_id,
                status="failed",
                end_time=datetime.utcnow().isoformat(),
                error_message="Pipeline cancelled by user"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error cancelling pipeline run {run_id}: {e}")
            return False

    # Extraction Results

    async def create_extraction_result(
        self,
        extraction_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new extraction result record.
        """
        try:
            supabase = await get_supabase() 
            
            data = {
                "pipeline_run_id": str(extraction_result["pipeline_run_id"]) if extraction_result.get("pipeline_run_id") else None,
                "source_id": str(extraction_result["source_id"]) if extraction_result.get("source_id") else None,
                "entity_count": extraction_result["entity_count"],
                "relationship_count": extraction_result["relationship_count"],
                "processed_text_length": extraction_result["processed_text_length"],
                "extracted_entities": extraction_result["extracted_entities"],
                "extracted_relationships": extraction_result["extracted_relationships"],
                "status": extraction_result["status"],
                "error_message": extraction_result.get("error_message")
            }
            
            response = await supabase.table("extraction_results").insert(data).execute()
            
            if response.data:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error creating extraction result: {e}")
            return None

    async def get_extraction_results(
        self,
        pipeline_run_id: Optional[UUID] = None,
        file_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get extraction results with optional filtering.
        """
        try:
            supabase = await get_supabase() 
            query = supabase.table("extraction_results").select("*")
            
            if pipeline_run_id:
                query = query.eq("pipeline_run_id", str(pipeline_run_id))
            
            if file_id:
                query = query.eq("source_id", str(file_id))
            
            response = await query.order("created_at", desc=True).execute()
            return response.data
        
        except Exception as e:
            logger.error(f"Error getting extraction results: {e}")
            return []

    # Implementation of pipeline step functions

    async def extract_from_datasource(
        self,
        datasource_id: UUID,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract entities and relationships from a data source.
        """
        # This is a placeholder implementation. In a real system, this would
        # depend on the type of data source.
        
        # Get all files from this data source
        file_uploads = await self.get_file_uploads(
            datasource_id=datasource_id,
            processed=False
        )
        
        total_entities = 0
        total_relationships = 0
        
        for file_upload in file_uploads:
            # Process each file
            await self.process_file_upload(UUID(file_upload["id"]))
            
            # Get extraction results for this file
            results = await self.get_extraction_results(file_id=UUID(file_upload["id"]))
            
            for result in results:
                total_entities += result["entity_count"]
                total_relationships += result["relationship_count"]
        
        return {
            "entity_count": total_entities,
            "relationship_count": total_relationships,
            "files_processed": len(file_uploads)
        }

    async def extract_from_file(
        self,
        file_id: UUID,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract entities and relationships from a specific file.
        """
        print(file_id)
        # Process the file
        await self.process_file_upload(file_id)
        
        # Get extraction results
        results = await self.get_extraction_results(file_id=file_id)
        
        total_entities = sum(result["entity_count"] for result in results)
        total_relationships = sum(result["relationship_count"] for result in results)
        
        return {
            "entity_count": total_entities,
            "relationship_count": total_relationships
        }

    async def run_entity_resolution(
        self,
        text_threshold: float = 0.8,
        embedding_threshold: float = 0.8,
        max_conflicts: int = 10,
        entity_types: List[str] = []
    ) -> Dict[str, Any]:
        """
        Run entity resolution to find and resolve conflicts.
        """
        from app.services.entity_resolution import EntityResolutionService   
        # Get entities to check
        supabase = await get_supabase() 
        entity_resolution_service = EntityResolutionService()

        query = supabase.table("kg_entities").select("id, entity_type")
        
        if entity_types:
            query = query.in_("entity_type", entity_types)
        
        response = await query.execute()
        entities = response.data
        
        conflict_count = 0
        
        for entity in entities:
            # Find conflicts for this entity
            # TODO: Implement the logic to find conflicts
            conflicts = await entity_resolution_service.find_entity_conflicts(
                entity_id=UUID(entity["id"]),
                text_threshold = text_threshold, 
                embedding_threshold = embedding_threshold,
                max_conflicts = max_conflicts 
            )
            
            # Create conflict records
            for conflict in conflicts:
                await entity_resolution_service.create_entity_conflict(
                    entity_id_1=UUID(conflict["entity_id_1"]),
                    entity_id_2=UUID(conflict["entity_id_2"]),
                    similarity_score=conflict["similarity_score"],
                    conflict_type=conflict["conflict_type"]
                )
                
                conflict_count += 1
        
        return {
            "conflict_count": conflict_count,
            "entities_checked": len(entities)
        }

    async def update_knowledge_graph(self) -> Dict[str, Any]:
        """
        Update the knowledge graph based on extracted entities and relationships.
        """
        from app.services.knowledge_graph import KnowledgeGraphService 

        # Synchronize entities to Neo4j
        kg_service = KnowledgeGraphService()

        # TODO: Implement the logic to update the knowledge graph

        return {
            "updated_entities": None,
            "updated_relationships":None 
        }
