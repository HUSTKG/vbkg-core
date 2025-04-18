# app/services/pipeline.py
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
import uuid
from datetime import datetime
import asyncio
import json
import traceback

from app.core.supabase import get_supabase
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineUpdate,
    PipelineStatus,
    PipelineRunCreate,
    PipelineRunUpdate,
    PipelineStepResult,
    PipelineStepType
)


class PipelineService:
    def __init__(self):
        self.supabase = get_supabase()

    async def create_pipeline(
        self,
        pipeline_in: PipelineCreate,
        user_id: str
    ) -> Dict[str, Any]:
        """Create a new pipeline"""
        try:
            # Generate IDs for steps if not provided
            steps = pipeline_in.steps
            for step in steps:
                if not step.id or step.id == "":
                    step.id = str(uuid.uuid4())
            
            # Create pipeline data
            data = pipeline_in.dict()
            data["created_by"] = user_id
            
            response = await self.supabase.from_("pipelines").insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline"
                )
                
            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline: {str(e)}"
            )

    async def get_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Get a pipeline by ID"""
        try:
            response = await self.supabase.from_("pipelines").select("*").eq("id", pipeline_id).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline not found"
                )
                
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline: {str(e)}"
            )

    async def update_pipeline(
        self,
        pipeline_id: str,
        pipeline_in: PipelineUpdate
    ) -> Dict[str, Any]:
        """Update a pipeline"""
        try:
            # Check if pipeline exists
            await self.get_pipeline(pipeline_id)
            
            # Update pipeline
            data = pipeline_in.dict(exclude_unset=True)
            
            response = await self.supabase.from_("pipelines").update(data).eq("id", pipeline_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline: {str(e)}"
            )

    async def delete_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Delete a pipeline"""
        try:
            # Check if pipeline exists
            await self.get_pipeline(pipeline_id)
            
            # Delete pipeline
            await self.supabase.from_("pipelines").delete().eq("id", pipeline_id).execute()
            
            return {"success": True, "message": "Pipeline deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting pipeline: {str(e)}"
            )

    async def get_pipelines(
        self,
        pipeline_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_by: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get pipelines with filtering and pagination"""
        try:
            query = self.supabase.from_("pipelines").select("*")
            
            if pipeline_type:
                query = query.eq("pipeline_type", pipeline_type)
                
            if is_active is not None:
                query = query.eq("is_active", is_active)
                
            if created_by:
                query = query.eq("created_by", created_by)
                
            response = await query.order("created_at", options={"ascending": False}).range(offset, offset + limit - 1).execute()
            
            return response.data or []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipelines: {str(e)}"
            )

    async def execute_pipeline(
        self,
        pipeline_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a pipeline"""
        try:
            # Check if pipeline exists and is active
            pipeline = await self.get_pipeline(pipeline_id)
            
            if not pipeline["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pipeline is not active"
                )
            
            # Create pipeline run
            run_data = PipelineRunCreate(
                pipeline_id=pipeline_id,
                status=PipelineStatus.PENDING,
                triggered_by=user_id
            )
            
            run = await self.create_pipeline_run(run_data)
            
            # Trigger async execution
            asyncio.create_task(self._execute_pipeline_async(pipeline_id, run["id"]))
            
            return run
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing pipeline: {str(e)}"
            )

    async def _execute_pipeline_async(self, pipeline_id: str, run_id: str) -> None:
        """Execute pipeline steps asynchronously"""
        # Get pipeline and update run status to running
        try:
            pipeline = await self.get_pipeline(pipeline_id)
            await self.update_pipeline_run(
                run_id,
                PipelineRunUpdate(
                    status=PipelineStatus.RUNNING,
                    start_time=datetime.utcnow().isoformat()
                )
            )
            
            # Initialize logs and results
            logs = []
            step_results = {}
            
            # Execute steps in order based on dependencies
            steps = pipeline["steps"]
            executed_steps = set()
            
            # Basic function to check if all dependencies are satisfied
            def can_execute_step(step):
                if not step.get("inputs"):
                    return True
                
                return all(input_id in executed_steps for input_id in step["inputs"])
            
            # Create a mapping of step outputs
            step_outputs = {}
            
            # Progress until all steps are executed or no more steps can be executed
            while len(executed_steps) < len(steps):
                made_progress = False
                
                for step in steps:
                    step_id = step["id"]
                    
                    # Skip steps that are already executed or disabled
                    if step_id in executed_steps or not step.get("enabled", True):
                        continue
                    
                    # Check if dependencies are satisfied
                    if not can_execute_step(step):
                        continue
                    
                    # Execute step
                    step_start_time = datetime.utcnow()
                    step_result = await self._execute_step(step, step_outputs, pipeline_id, run_id)
                    step_end_time = datetime.utcnow()
                    
                    # Calculate duration
                    duration = int((step_end_time - step_start_time).total_seconds())
                    
                    # Update step result with timing
                    step_result.start_time = step_start_time
                    step_result.end_time = step_end_time
                    step_result.duration = duration
                    
                    # Store step output for subsequent steps
                    if step_result.output:
                        step_outputs[step_id] = step_result.output
                    
                    # Store step result
                    step_results[step_id] = step_result
                    
                    # Add to executed steps
                    executed_steps.add(step_id)
                    made_progress = True
                    
                    # Log step execution
                    logs.append({
                        "timestamp": step_end_time.isoformat(),
                        "step_id": step_id,
                        "step_name": step["name"],
                        "status": step_result.status,
                        "duration": duration,
                        "error": step_result.error_message
                    })
                
                # If no progress was made in this iteration, there's a circular dependency or other problem
                if not made_progress and len(executed_steps) < len(steps):
                    error_message = "Execution halted: circular dependency or invalid step configuration"
                    
                    # Update run with error
                    await self.update_pipeline_run(
                        run_id,
                        PipelineRunUpdate(
                            status=PipelineStatus.FAILED,
                            end_time=datetime.utcnow().isoformat(),
                            error_message=error_message,
                            log=json.dumps(logs)
                        )
                    )
                    
                    # Store run logs
                    await self._store_pipeline_run_logs(pipeline_id, run_id, logs, step_results)
                    return
            
            # Calculate final status
            failed_steps = [s for s in step_results.values() if s.status == PipelineStatus.FAILED]
            final_status = PipelineStatus.FAILED if failed_steps else PipelineStatus.COMPLETED
            
            # Calculate stats
            stats = {
                "total_steps": len(steps),
                "completed_steps": len([s for s in step_results.values() if s.status == PipelineStatus.COMPLETED]),
                "failed_steps": len(failed_steps),
                "disabled_steps": len([s for s in steps if not s.get("enabled", True)]),
                "total_duration": sum([s.duration or 0 for s in step_results.values()])
            }
            
            # Update run with results
            await self.update_pipeline_run(
                run_id,
                PipelineRunUpdate(
                    status=final_status,
                    end_time=datetime.utcnow().isoformat(),
                    stats=stats,
                    log=json.dumps(logs)
                )
            )
            
            # Store run logs
            await self._store_pipeline_run_logs(pipeline_id, run_id, logs, step_results)
            
        except Exception as e:
            # Update run with error
            error_detail = traceback.format_exc()
            await self.update_pipeline_run(
                run_id,
                PipelineRunUpdate(
                    status=PipelineStatus.FAILED,
                    end_time=datetime.utcnow().isoformat(),
                    error_message=f"Pipeline execution error: {str(e)}",
                    log=error_detail
                )
            )

    async def _execute_step(
        self,
        step: Dict[str, Any],
        step_outputs: Dict[str, Any],
        pipeline_id: str,
        run_id: str
    ) -> PipelineStepResult:
        """Execute a single pipeline step"""
        try:
            step_id = step["id"]
            step_type = step["type"]
            config = step.get("config", {})
            
            # Get inputs from previous steps
            inputs = {}
            if step.get("inputs"):
                for input_id in step["inputs"]:
                    if input_id in step_outputs:
                        inputs[input_id] = step_outputs[input_id]
            
            # Execute step based on type
            output = None
            if step_type == PipelineStepType.FILE_READER:
                output = await self._execute_file_reader_step(config, inputs)
            elif step_type == PipelineStepType.TEXT_EXTRACTOR:
                output = await self._execute_text_extractor_step(config, inputs)
            elif step_type == PipelineStepType.LLM_ENTITY_EXTRACTOR:
                output = await self._execute_llm_entity_extractor_step(config, inputs)
            elif step_type == PipelineStepType.FIBO_MAPPER:
                output = await self._execute_fibo_mapper_step(config, inputs)
            elif step_type == PipelineStepType.ENTITY_RESOLUTION:
                output = await self._execute_entity_resolution_step(config, inputs)
            elif step_type == PipelineStepType.KNOWLEDGE_GRAPH_WRITER:
                output = await self._execute_knowledge_graph_writer_step(config, inputs)
            elif step_type == PipelineStepType.CUSTOM_PYTHON:
                output = await self._execute_custom_python_step(config, inputs)
            elif step_type == PipelineStepType.API_FETCHER:
                output = await self._execute_api_fetcher_step(config, inputs)
            elif step_type == PipelineStepType.DATABASE_EXTRACTOR:
                output = await self._execute_database_extractor_step(config, inputs)
            else:
                raise ValueError(f"Unsupported step type: {step_type}")
            
            return PipelineStepResult(
                step_id=step_id,
                status=PipelineStatus.COMPLETED,
                output=output,
                error_message=None,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration=0
            )
        except Exception as e:
            # Create failed step result
            return PipelineStepResult(
                step_id=step["id"],
                status=PipelineStatus.FAILED,
                output=None,
                error_message=str(e),
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration=0
            )

    async def _store_pipeline_run_logs(
        self,
        pipeline_id: str,
        run_id: str,
        logs: List[Dict[str, Any]],
        step_results: Dict[str, PipelineStepResult]
    ) -> None:
        """Store detailed logs for a pipeline run"""
        try:
            # Convert step results to dictionaries
            step_results_dict = {
                step_id: result.dict() for step_id, result in step_results.items()
            }
            
            # Store in pipeline_run_logs table
            log_data = {
                "pipeline_id": pipeline_id,
                "run_id": run_id,
                "logs": logs,
                "step_results": step_results_dict
            }
            
            await self.supabase.from_("pipeline_run_logs").insert(log_data).execute()
        except Exception as e:
            print(f"Error storing pipeline run logs: {e}")

    async def create_pipeline_run(
        self,
        run_in: PipelineRunCreate
    ) -> Dict[str, Any]:
        """Create a new pipeline run"""
        try:
            data = run_in.dict()
            data["start_time"] = datetime.utcnow().isoformat()
            
            response = await self.supabase.from_("pipeline_runs").insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline run"
                )
                
            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline run: {str(e)}"
            )

    async def get_pipeline_run(self, run_id: str) -> Dict[str, Any]:
        """Get a pipeline run by ID"""
        try:
            response = await self.supabase.from_("pipeline_runs").select("*").eq("id", run_id).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline run not found"
                )
                
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline run: {str(e)}"
            )

    async def update_pipeline_run(
        self,
        run_id: str,
        run_update: PipelineRunUpdate
    ) -> Dict[str, Any]:
        """Update a pipeline run"""
        try:
            # Check if run exists
            await self.get_pipeline_run(run_id)
            
            # Update run
            data = run_update.dict(exclude_unset=True)
            
            # Calculate duration if not provided
            if run_update.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED] and run_update.end_time and not run_update.duration:
                run = await self.get_pipeline_run(run_id)
                start_time = datetime.fromisoformat(run["start_time"])
                end_time = datetime.fromisoformat(run_update.end_time)
                data["duration"] = int((end_time - start_time).total_seconds())
            
            response = await self.supabase.from_("pipeline_runs").update(data).eq("id", run_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline run"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline run: {str(e)}"
            )

    async def get_pipeline_runs(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
        triggered_by: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get pipeline runs with filtering and pagination"""
        try:
            query = self.supabase.from_("pipeline_runs").select("*")
            
            if pipeline_id:
                query = query.eq("pipeline_id", pipeline_id)
                
            if status:
                query = query.eq("status", status)
                
            if triggered_by:
                query = query.eq("triggered_by", triggered_by)
                
            response = await query.order("created_at", options={"ascending": False}).range(offset, offset + limit - 1).execute()
            
            return response.data or []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline runs: {str(e)}"
            )

    async def get_pipeline_run_logs(self, run_id: str) -> Dict[str, Any]:
        """Get detailed logs for a pipeline run"""
        try:
            response = await self.supabase.from_("pipeline_run_logs").select("*").eq("run_id", run_id).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline run logs not found"
                )
                
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline run logs: {str(e)}"
            )

    # Step Execution Methods
    
    async def _execute_file_reader_step(
        self,
        config: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute file reader step"""
        from app.services.datasource import DataSourceService
        
        try:
            file_id = config.get("file_id")
            if not file_id:
                raise ValueError("file_id is required for file reader step")
            
            # Get file content
            datasource_service = DataSourceService()
            file_info = await datasource_service.get_file_upload(file_upload_id=file_id)
            file_content = await datasource_service.get_file_content(file_upload_id=file_id)
            
            # Return file info and content
            return {
                "file_info": file_info,
                "content": file_content.decode(config.get("encoding", "utf-8")),
                "content_type": file_info.get("file_type"),
                "file_name": file_info.get("file_name")
            }
        except Exception as e:
            raise ValueError(f"Error executing file reader step: {str(e)}")

    # app/services/pipeline.py (continued)

    async def _execute_text_extractor_step(
        self,
        config: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute text extractor step"""
        try:
            # Get input content
            input_content = None
            input_type = None
            
            # Check for file reader input
            for input_id, input_data in inputs.items():
                if "content" in input_data:
                    input_content = input_data["content"]
                    input_type = input_data.get("content_type", "text/plain")
                    break
            
            if not input_content:
                raise ValueError("No input content found")
            
            # Extract text based on input type
            extracted_text = ""
            if config.get("input_format") == "pdf" or input_type in ["application/pdf", "pdf"]:
                extracted_text = await self._extract_text_from_pdf(input_content)
            elif config.get("input_format") == "docx" or input_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"]:
                extracted_text = await self._extract_text_from_docx(input_content)
            elif config.get("input_format") == "html" or input_type in ["text/html", "html"]:
                extracted_text = await self._extract_text_from_html(input_content)
            else:
                # Assume plain text
                extracted_text = input_content
            
            # Split into chunks if requested
            chunks = []
            if config.get("chunk_size", 0) > 0:
                chunk_size = config.get("chunk_size", 1000)
                chunk_overlap = config.get("chunk_overlap", 200)
                chunks = self._split_text_into_chunks(extracted_text, chunk_size, chunk_overlap)
            
            return {
                "text": extracted_text,
                "chunks": chunks,
                "language": config.get("language"),
                "metadata": {"chunk_count": len(chunks)} if chunks else {}
            }
        except Exception as e:
            raise ValueError(f"Error executing text extractor step: {str(e)}")

    async def _extract_text_from_pdf(self, content: str) -> str:
        """Extract text from PDF content"""
        try:
            # For demonstration, we'll just return the content as is
            # In a real implementation, you would use PyPDF2, pdfplumber, or similar
            # This would require actual binary content, not the string representation
            return f"[PDF text extraction placeholder]"
        except Exception as e:
            raise ValueError(f"Error extracting text from PDF: {str(e)}")

    async def _extract_text_from_docx(self, content: str) -> str:
        """Extract text from DOCX content"""
        try:
            # For demonstration, we'll just return the content as is
            # In a real implementation, you would use python-docx or similar
            return f"[DOCX text extraction placeholder]"
        except Exception as e:
            raise ValueError(f"Error extracting text from DOCX: {str(e)}")

    async def _extract_text_from_html(self, content: str) -> str:
        """Extract text from HTML content"""
        try:
            # For demonstration, we'll use a simple regex-based approach
            # In a real implementation, you would use BeautifulSoup or similar
            import re
            clean_text = re.sub(r'<[^>]+>', ' ', content)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            return clean_text
        except Exception as e:
            raise ValueError(f"Error extracting text from HTML: {str(e)}")

    def _split_text_into_chunks(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunks.append(text[i:i + chunk_size])
            if i + chunk_size >= len(text):
                break
        return chunks

    async def _execute_llm_entity_extractor_step(
        self,
        config: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute LLM entity extractor step"""
        try:
            # Import OpenAI
            import openai
            from app.core.config import settings
            
            # Get OpenAI API key from settings
            api_key = settings.OPENAI_API_KEY
            if not api_key:
                raise ValueError("OpenAI API key not configured")
            
            # Get input text
            input_text = None
            
            # Check for text extractor input
            for input_id, input_data in inputs.items():
                if "text" in input_data:
                    input_text = input_data["text"]
                    break
                elif "chunks" in input_data and input_data["chunks"]:
                    # Use the first chunk if multiple chunks are available
                    input_text = input_data["chunks"][0]
                    break
                elif "content" in input_data:
                    input_text = input_data["content"]
                    break
            
            if not input_text:
                raise ValueError("No input text found")
            
            # Get entity types to extract
            entity_types = config.get("entity_types", [])
            if not entity_types:
                raise ValueError("No entity types specified")
            
            # Prepare prompt
            prompt_template = config.get("prompt_template")
            if not prompt_template:
                # Default prompt template
                prompt_template = """
                Extract all entities of the following types from the text: {entity_types}.
                
                For each entity, provide:
                1. The entity text exactly as it appears
                2. The entity type
                3. Start and end position in the text (if possible)
                
                Return the results in the following JSON format:
                {{
                    "entities": [
                        {{
                            "text": "entity text",
                            "type": "entity type",
                            "start": start_position,
                            "end": end_position
                        }},
                        ...
                    ]
                }}
                
                Text:
                {text}
                """
            
            # Format prompt
            prompt = prompt_template.format(
                entity_types=", ".join(entity_types),
                text=input_text
            )
            
            # Call OpenAI API
            model = config.get("model", "gpt-3.5-turbo-0125")
            temperature = config.get("temperature", 0.2)
            max_tokens = config.get("max_tokens", 1000)
            
            openai.api_key = api_key
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a precise entity extraction system for financial and banking domain."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Extract relationships if requested
            relationships = []
            if config.get("extract_relationships", False):
                # Call for relationship extraction
                rel_prompt = f"""
                Based on the entities I've identified:
                {json.dumps(result['entities'], indent=2)}
                
                Please identify any relationships between these entities.
                For each relationship, provide:
                1. The source entity (text and type)
                2. The target entity (text and type)
                3. The relationship type
                
                Return the results in the following JSON format:
                {{
                    "relationships": [
                        {{
                            "source": {{"text": "source text", "type": "source type"}},
                            "target": {{"text": "target text", "type": "target type"}},
                            "type": "relationship type"
                        }},
                        ...
                    ]
                }}
                """
                
                rel_response = await openai.ChatCompletion.acreate(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a precise relationship extraction system for financial and banking domain."},
                        {"role": "user", "content": rel_prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )
                
                rel_result = json.loads(rel_response.choices[0].message.content)
                relationships = rel_result.get("relationships", [])
            
            return {
                "entities": result.get("entities", []),
                "relationships": relationships,
                "source_text": input_text
            }
        except Exception as e:
            raise ValueError(f"Error executing LLM entity extractor step: {str(e)}")

    async def _execute_fibo_mapper_step(
        self,
        config: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute FIBO mapper step"""
        try:
            from app.services.fibo import FIBOService
            
            # Get FIBO service
            fibo_service = FIBOService()
            
            # Get input entities
            input_entities = []
            
            # Check for entity extractor input
            for input_id, input_data in inputs.items():
                if "entities" in input_data:
                    input_entities = input_data["entities"]
                    break
            
            if not input_entities:
                raise ValueError("No input entities found")
            
            # Get config parameters
            confidence_threshold = config.get("mapping_confidence_threshold", 0.7)
            save_mappings = config.get("save_mappings", True)
            
            # Map entities to FIBO classes
            mapped_entities = []
            for entity in input_entities:
                entity_text = entity.get("text", "")
                entity_type = entity.get("type", "")
                
                # Get FIBO class suggestions
                suggestions = await fibo_service.suggest_fibo_class_for_entity(
                    entity_text=entity_text,
                    entity_type=entity_type
                )
                
                # Take the top suggestion
                fibo_class = None
                confidence = 0.0
                
                if suggestions:
                    # Simple confidence calculation - could be more sophisticated
                    # Assign higher confidence to more specific classes
                    confidence = 0.8  # Default confidence for first suggestion
                    fibo_class = suggestions[0]
                
                # Create mapped entity
                mapped_entity = {
                    **entity,
                    "fibo_class": fibo_class["uri"] if fibo_class else None,
                    "fibo_class_label": fibo_class["label"] if fibo_class else None,
                    "mapping_confidence": confidence,
                    "suggestions": [s["uri"] for s in suggestions[:3]] if suggestions else []
                }
                
                mapped_entities.append(mapped_entity)
                
                # Save mapping if requested and confidence is high enough
                if save_mappings and fibo_class and confidence >= confidence_threshold:
                    try:
                        await fibo_service.create_entity_mapping(
                            mapping={
                                "entity_type": entity_type,
                                "fibo_class_uri": fibo_class["uri"],
                                "confidence": confidence,
                                "is_verified": False
                            }
                        )
                    except Exception as mapping_error:
                        print(f"Error saving entity mapping: {mapping_error}")
            
            # Get input relationships
            input_relationships = []
            for input_id, input_data in inputs.items():
                if "relationships" in input_data:
                    input_relationships = input_data["relationships"]
                    break
            
            # Map relationships to FIBO properties
            mapped_relationships = []
            for relationship in input_relationships:
                rel_type = relationship.get("type", "")
                source = relationship.get("source", {})
                target = relationship.get("target", {})
                
                source_type = source.get("type", "")
                target_type = target.get("type", "")
                
                # Get FIBO property suggestions
                suggestions = await fibo_service.suggest_fibo_property_for_relationship(
                    relationship_type=rel_type,
                    source_entity_type=source_type,
                    target_entity_type=target_type
                )
                
                # Take the top suggestion
                fibo_property = None
                confidence = 0.0
                
                if suggestions:
                    confidence = 0.8  # Default confidence for first suggestion
                    fibo_property = suggestions[0]
                
                # Create mapped relationship
                mapped_relationship = {
                    **relationship,
                    "fibo_property": fibo_property["uri"] if fibo_property else None,
                    "fibo_property_label": fibo_property["label"] if fibo_property else None,
                    "mapping_confidence": confidence,
                    "suggestions": [s["uri"] for s in suggestions[:3]] if suggestions else []
                }
                
                mapped_relationships.append(mapped_relationship)
                
                # Save mapping if requested and confidence is high enough
                if save_mappings and fibo_property and confidence >= confidence_threshold:
                    try:
                        await fibo_service.create_relationship_mapping(
                            mapping={
                                "relationship_type": rel_type,
                                "fibo_property_uri": fibo_property["uri"],
                                "confidence": confidence,
                                "is_verified": False
                            }
                        )
                    except Exception as mapping_error:
                        print(f"Error saving relationship mapping: {mapping_error}")
            
            return {
                "entities": mapped_entities,
                "relationships": mapped_relationships,
                "mapping_stats": {
                    "entity_count": len(mapped_entities),
                    "mapped_entity_count": len([e for e in mapped_entities if e.get("fibo_class")]),
                    "relationship_count": len(mapped_relationships),
                    "mapped_relationship_count": len([r for r in mapped_relationships if r.get("fibo_property")])
                }
            }
        except Exception as e:
            raise ValueError(f"Error executing FIBO mapper step: {str(e)}")

    async def _execute_entity_resolution_step(
        self,
        config: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute entity resolution step"""
        try:
            # Get input entities
            input_entities = []
            
            # Check for mapper or extractor input
            for input_id, input_data in inputs.items():
                if "entities" in input_data:
                    input_entities = input_data["entities"]
                    break
            
            if not input_entities:
                raise ValueError("No input entities found")
            
            # Get config parameters
            resolution_strategy = config.get("resolution_strategy", "exact_match")
            similarity_threshold = config.get("similarity_threshold", 0.8)
            match_on = config.get("match_on", ["text"])
            handle_conflicts = config.get("handle_conflicts", "keep_both")
            
            # Group entities by type
            entities_by_type = {}
            for entity in input_entities:
                entity_type = entity.get("type")
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(entity)
            
            # Resolve entities
            resolved_entities = []
            entity_groups = []
            
            for entity_type, entities in entities_by_type.items():
                # Skip if only one entity of this type
                if len(entities) <= 1:
                    resolved_entities.extend(entities)
                    continue
                
                # Group similar entities
                groups = []
                
                if resolution_strategy == "exact_match":
                    # Group by exact text match
                    exact_match_groups = {}
                    for entity in entities:
                        key = entity.get("text", "").lower()
                        if key not in exact_match_groups:
                            exact_match_groups[key] = []
                        exact_match_groups[key].append(entity)
                    
                    groups = list(exact_match_groups.values())
                
                elif resolution_strategy == "fuzzy_match":
                    # Simple fuzzy matching
                    from difflib import SequenceMatcher
                    
                    # Start with each entity in its own group
                    remaining_entities = entities.copy()
                    
                    while remaining_entities:
                        current_entity = remaining_entities.pop(0)
                        current_group = [current_entity]
                        
                        i = 0
                        while i < len(remaining_entities):
                            entity = remaining_entities[i]
                            
                            # Calculate similarity
                            similarity = 0
                            for field in match_on:
                                if field in current_entity and field in entity:
                                    text1 = str(current_entity[field]).lower()
                                    text2 = str(entity[field]).lower()
                                    field_similarity = SequenceMatcher(None, text1, text2).ratio()
                                    similarity = max(similarity, field_similarity)
                            
                            if similarity >= similarity_threshold:
                                current_group.append(entity)
                                remaining_entities.pop(i)
                            else:
                                i += 1
                        
                        groups.append(current_group)
                
                elif resolution_strategy == "embedding":
                    # Placeholder for embedding-based similarity
                    # In a real implementation, you would use embeddings
                    # For now, just use exact match as fallback
                    exact_match_groups = {}
                    for entity in entities:
                        key = entity.get("text", "").lower()
                        if key not in exact_match_groups:
                            exact_match_groups[key] = []
                        exact_match_groups[key].append(entity)
                    
                    groups = list(exact_match_groups.values())
                
                # Process each group
                for group in groups:
                    if len(group) == 1:
                        # Only one entity in group, no resolution needed
                        resolved_entities.append(group[0])
                    else:
                        entity_groups.append(group)
                        
                        # Select representative entity
                        if handle_conflicts == "keep_both":
                            # Keep all entities
                            resolved_entities.extend(group)
                        elif handle_conflicts == "keep_newest":
                            # Keep the newest entity (just an example, could use other criteria)
                            resolved_entities.append(group[-1])
                        elif handle_conflicts == "keep_highest_confidence":
                            # Keep the entity with highest mapping confidence
                            highest_conf_entity = max(
                                group, 
                                key=lambda e: e.get("mapping_confidence", 0)
                            )
                            resolved_entities.append(highest_conf_entity)
                        else:
                            # Default: keep first entity
                            resolved_entities.append(group[0])
            
            # Get input relationships
            input_relationships = []
            for input_id, input_data in inputs.items():
                if "relationships" in input_data:
                    input_relationships = input_data["relationships"]
                    break
            
            # Update relationships to use resolved entities
            resolved_relationships = input_relationships
            
            return {
                "entities": resolved_entities,
                "relationships": resolved_relationships,
                "entity_groups": entity_groups,
                "resolution_stats": {
                    "input_entity_count": len(input_entities),
                    "resolved_entity_count": len(resolved_entities),
                    "duplicate_groups": len(entity_groups)
                }
            }
        except Exception as e:
            raise ValueError(f"Error executing entity resolution step: {str(e)}")

    async def _execute_knowledge_graph_writer_step(
        self,
        config: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute knowledge graph writer step"""
        try:
            from app.services.knowledge_graph import KnowledgeGraphService
            
            # Get knowledge graph service
            kg_service = KnowledgeGraphService()
            
            # Get input entities and relationships
            input_entities = []
            input_relationships = []
            source_document_id = None
            
            # Check for entity input
            for input_id, input_data in inputs.items():
                if "entities" in input_data:
                    input_entities = input_data["entities"]
                if "relationships" in input_data:
                    input_relationships = input_data["relationships"]
                if "source_document_id" in input_data:
                    source_document_id = input_data["source_document_id"]
                elif "file_info" in input_data and "id" in input_data["file_info"]:
                    source_document_id = input_data["file_info"]["id"]
            
            # Get config parameters
            batch_size = config.get("batch_size", 100)
            create_if_not_exists = config.get("create_if_not_exists", True)
            update_if_exists = config.get("update_if_exists", False)
            store_metadata = config.get("store_metadata", True)
            
            # Process entities
            created_entities = []
            updated_entities = []
            errors = []
            entity_id_map = {}  # Map from entity text to neo4j id
            
            for i in range(0, len(input_entities), batch_size):
                batch = input_entities[i:i+batch_size]
                
                for entity in batch:
                    try:
                        entity_text = entity.get("text")
                        entity_type = entity.get("type")
                        
                        if not entity_text or not entity_type:
                            continue
                        
                        # Prepare properties
                        properties = {}
                        
                        # Add FIBO information if available
                        fibo_class = entity.get("fibo_class")
                        
                        # Add all entity fields as properties (excluding special fields)
                        for key, value in entity.items():
                            if key not in ["text", "type"]:
                                properties[key] = value
                        
                        # Add source document if available
                        if source_document_id:
                            properties["source_document_id"] = source_document_id
                        
                        if create_if_not_exists:
                            # Create or merge entity
                            entity_id = await kg_service.create_or_merge_entity(
                                entity_text=entity_text,
                                entity_type=entity_type,
                                properties=properties,
                                fibo_class=fibo_class,
                                source_document_id=source_document_id
                            )
                            
                            # Store mapping from entity text to ID
                            entity_id_map[entity_text] = entity_id
                            created_entities.append(entity_id)
                    except Exception as entity_error:
                        errors.append(f"Error creating entity {entity_text}: {str(entity_error)}")
            
            # Process relationships
            created_relationships = []
            
            for relationship in input_relationships:
                try:
                    rel_type = relationship.get("type")
                    source = relationship.get("source", {})
                    target = relationship.get("target", {})
                    
                    source_text = source.get("text")
                    target_text = target.get("text")
                    
                    if not rel_type or not source_text or not target_text:
                        continue
                    
                    # Get entity IDs
                    source_id = entity_id_map.get(source_text)
                    target_id = entity_id_map.get(target_text)
                    
                    if not source_id or not target_id:
                        continue
                    
                    # Prepare properties
                    properties = {}
                    
                    # Add FIBO information if available
                    fibo_property = relationship.get("fibo_property")
                    
                    # Add all relationship fields as properties (excluding special fields)
                    for key, value in relationship.items():
                        if key not in ["type", "source", "target"]:
                            properties[key] = value
                    
                    # Add source document if available
                    if source_document_id:
                        properties["source_document_id"] = source_document_id
                    
                    # Create relationship
                    rel_result = await kg_service.create_relationship(
                        source_id=source_id,
                        target_id=target_id,
                        relationship_type=rel_type,
                        properties=properties,
                        fibo_property=fibo_property,
                        source_document_id=source_document_id
                    )
                    
                    created_relationships.append(rel_result["id"])
                except Exception as rel_error:
                    errors.append(f"Error creating relationship {rel_type}: {str(rel_error)}")
            
            return {
                "created_entities": created_entities,
                "updated_entities": updated_entities,
                "created_relationships": created_relationships,
                "errors": errors,
                "stats": {
                    "entity_count": len(created_entities) + len(updated_entities),
                    "relationship_count": len(created_relationships),
                    "error_count": len(errors)
                }
            }
        except Exception as e:
            raise ValueError(f"Error executing knowledge graph writer step: {str(e)}")

    async def _execute_api_fetcher_step(
        self,
        config: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute API fetcher step"""
        try:
            import aiohttp
            
            # Get API config
            url = config.get("url")
            if not url:
                raise ValueError("URL is required for API fetcher step")
            
            method = config.get("method", "GET")
            headers = config.get("headers", {})
            params = config.get("params", {})
            body = config.get("body")
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=body if body else None
                ) as response:
                    status_code = response.status
                    content_type = response.headers.get("Content-Type", "")
                    
                    if status_code >= 400:
                        error_text = await response.text()
                        raise ValueError(f"API request failed with status {status_code}: {error_text}")
                    
                    # Parse response based on content type
                    if "application/json" in content_type:
                        data = await response.json()
                    else:
                        data = await response.text()
            
            return {
                "status_code": status_code,
                "content_type": content_type,
                "data": data
            }
        except Exception as e:
            raise ValueError(f"Error executing API fetcher step: {str(e)}")

    async def _execute_database_extractor_step(
        self,
        config: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute database extractor step"""
        try:
            import asyncpg
            
            # Get database config
            connection_string = config.get("connection_string")
            if not connection_string:
                raise ValueError("Connection string is required for database extractor step")
            
            query = config.get("query")
            if not query:
                raise ValueError("Query is required for database extractor step")
            
            params = config.get("params", [])
            batch_size = config.get("batch_size", 1000)
            
            # Connect to database
            conn = await asyncpg.connect(connection_string)
            
            try:
                # Execute query
                results = await conn.fetch(query, *params)
                
                # Convert to dict
                data = [dict(row) for row in results]
                
                return {
                    "data": data,
                    "row_count": len(data),
                    "columns": list(data[0].keys()) if data else []
                }
            finally:
                # Close connection
                await conn.close()
        except Exception as e:
            raise ValueError(f"Error executing database extractor step: {str(e)}")

    async def _execute_custom_python_step(
        self,
        config: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute custom Python code step"""
        try:
            # WARNING: Executing custom code is a security risk
            # In a production environment, this should be done in a sandboxed environment
            
            code = config.get("code")
            if not code:
                raise ValueError("Code is required for custom Python step")
            
            # Get input and output mapping
            input_mapping = config.get("input_mapping", {})
            
            # Map inputs to variables
            globals_dict = {}
            locals_dict = {"inputs": inputs}
            
            for var_name, input_path in input_mapping.items():
                parts = input_path.split(".")
                value = inputs
                
                for part in parts:
                    if part in value:
                        value = value[part]
                    else:
                        value = None
                        break
                
                locals_dict[var_name] = value
            
            # Execute code
            exec(code, globals_dict, locals_dict)
            
            # Get output from locals
            output = locals_dict.get("output", {})
            
            return output
        except Exception as e:
            raise ValueError(f"Error executing custom Python step: {str(e)}")
