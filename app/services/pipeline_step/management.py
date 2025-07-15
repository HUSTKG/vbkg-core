from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import HTTPException
from fastapi import status as HttpStatus
from postgrest.base_request_builder import APIResponse

from app.schemas.pipeline_step import PipelineStepCreate, PipelineStepUpdate

from .base import BasePipelineStepService


class PipelineStepManagementService(BasePipelineStepService):
    """Service for pipeline step CRUD operations"""
    
    async def create_pipeline_step(
        self, 
        step_in: PipelineStepCreate, 
        pipeline_id: str
    ) -> Dict[str, Any]:
        """Create a new pipeline step with validation"""
        try:
            # Validate step data
            validation_errors = await self._validate_step_data(step_in, pipeline_id)
            if validation_errors:
                raise HTTPException(
                    status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                    detail=f"Validation errors: {'; '.join(validation_errors)}"
                )
            
            supabase = await self.get_supabase()
            step_dict = step_in.model_dump()
            step_dict["pipeline_id"] = pipeline_id
            
            # Process complex fields
            step_dict = await self._process_step_fields(step_dict)
            
            response = await supabase.from_("pipeline_steps").insert(step_dict).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline step"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error creating pipeline step: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline step: {str(e)}"
            )
    
    async def get_pipeline_step(
        self, 
        step_id: str, 
        pipeline_id: str
    ) -> Dict[str, Any]:
        """Get a pipeline step by ID"""
        try:
            supabase = await self.get_supabase()
            response = await supabase.from_("pipeline_steps").select("*").filter("id", "eq", step_id).filter("pipeline_id", "eq", pipeline_id).maybe_single().execute()
            
            if not response:
                raise HTTPException(
                    status_code=HttpStatus.HTTP_404_NOT_FOUND,
                    detail="Pipeline step not found"
                )
            
            # Parse complex fields
            step_data = await self._parse_step_fields(response.data)
            return step_data
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving pipeline step {step_id}: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline step: {str(e)}"
            )
    
    async def update_pipeline_step(
        self, 
        step_id: str, 
        step_update: PipelineStepUpdate, 
        pipeline_id: str
    ) -> Dict[str, Any]:
        """Update a pipeline step"""
        try:
            # Check if step exists
            await self.get_pipeline_step(step_id, pipeline_id)
            
            supabase = await self.get_supabase()
            update_data = step_update.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            # Process complex fields
            update_data = await self._process_step_fields(update_data)
            
            # Validate dependencies if updated
            if update_data.get("depends_on"):
                from .dependencies import PipelineStepDependencyService
                dependency_service = PipelineStepDependencyService()
                await dependency_service.validate_step_dependencies(
                    update_data["depends_on"], pipeline_id
                )
            
            response = await supabase.from_("pipeline_steps").update(update_data).eq("id", step_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline step"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating pipeline step {step_id}: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline step: {str(e)}"
            )
    
    async def delete_pipeline_step(
        self, 
        step_id: str, 
        pipeline_id: str
    ) -> Dict[str, Any]:
        """Delete a pipeline step"""
        try:
            # Check if step exists
            await self.get_pipeline_step(step_id, pipeline_id)
            
            # Check for dependent steps
            from .dependencies import PipelineStepDependencyService
            dependency_service = PipelineStepDependencyService()
            dependent_steps = await dependency_service.get_dependent_steps(step_id, pipeline_id)
            
            if dependent_steps:
                raise HTTPException(
                    status_code=HttpStatus.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete step with dependencies: {[s['name'] for s in dependent_steps]}"
                )
            
            supabase = await self.get_supabase()
            await supabase.from_("pipeline_steps").delete().eq("id", step_id).execute()
            
            return {"success": True, "message": "Pipeline step deleted"}
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting pipeline step {step_id}: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting pipeline step: {str(e)}"
            )
    
    async def get_pipeline_steps(
        self, 
        pipeline_id: str, 
        limit: int = 100, 
        skip: int = 0
    ) -> APIResponse[Dict[str, Any]]:
        """Get pipeline steps with filtering and pagination"""
        try:
            supabase = await self.get_supabase()
            response = await supabase.from_("pipeline_steps").select("*").eq("pipeline_id", pipeline_id).order("run_order").range(skip, skip + limit - 1).execute()
            
            # Process the response data
            processed_data = []
            for step_data in response.data:
                processed_step = await self._parse_step_fields(step_data)
                processed_data.append(processed_step)
            
            return APIResponse(data=processed_data, count=response.count)
            
        except Exception as e:
            self.logger.error(f"Error retrieving pipeline steps for pipeline {pipeline_id}: {e}")
            raise HTTPException(
                status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline steps: {str(e)}"
            )
    
    # Private helper methods
    async def _validate_step_data(
        self, 
        step_data: PipelineStepCreate, 
        pipeline_id: str
    ) -> List[str]:
        """Validate step creation data"""
        errors = []
        
        if not step_data.name or not step_data.name.strip():
            errors.append("Step name is required")
        
        if not step_data.step_type:
            errors.append("Step type is required")
        
        # Validate dependencies
        if step_data.depends_on:
            from .dependencies import PipelineStepDependencyService
            dependency_service = PipelineStepDependencyService()
            try:
                await dependency_service.validate_step_dependencies(
                    step_data.depends_on, pipeline_id
                )
            except HTTPException as e:
                errors.append(str(e.detail))
        
        return errors
    
    async def _process_step_fields(self, step_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process complex fields for database storage"""
        processed = step_dict.copy()
        
        # Convert inputs list to comma-separated string
        if "inputs" in processed and isinstance(processed["inputs"], list):
            processed["inputs"] = ",".join(processed["inputs"])
        
        # Keep config and incremental_config as they are (JSONB fields)
        
        return processed
    
    async def _parse_step_fields(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse complex fields from database"""
        parsed = {
            "id": step_data["id"],
            "pipeline_id": step_data["pipeline_id"],
            "name": step_data["name"],
            "step_type": step_data["step_type"],
            "config": step_data.get("config", {}),
            "run_order": step_data["run_order"],
            "description": step_data.get("description"),
            "enabled": step_data.get("enabled", True),
            "depends_on": step_data.get("depends_on", []),
            "inputs": [
                inp.strip()
                for inp in (step_data.get("inputs") or "").split(",")
                if inp.strip()
            ],
            "is_incremental_capable": step_data.get("is_incremental_capable", False),
            "incremental_config": step_data.get("incremental_config"),
            "created_at": step_data["created_at"],
            "updated_at": step_data["updated_at"],
        }
        
        return parsed

