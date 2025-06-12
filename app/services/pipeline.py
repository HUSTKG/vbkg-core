import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse

from app.core.supabase import get_supabase
from app.schemas.pipeline import (Pipeline, PipelineCreate, PipelineRunCreate,
                                  PipelineRunStatus, PipelineRunUpdate,
                                  PipelineType, PipelineUpdate)


class PipelineService:
    """Service for managing pipelines and their execution."""

    async def create_pipeline(
        self, pipeline_in: PipelineCreate, user_id: str
    ) -> Dict[str, Any]:
        """Create a new pipeline with enhanced step validation"""
        try:
            supabase = await get_supabase()

            pipeline_dict = pipeline_in.model_dump()

            # Create pipeline
            pipeline_response = (
                await supabase.from_("pipelines")
                .insert(
                    {
                        "name": pipeline_dict["name"],
                        "description": pipeline_dict["description"],
                        "pipeline_type": pipeline_dict["pipeline_type"],
                        "schedule": pipeline_dict["schedule"],
                        "is_active": pipeline_dict["is_active"],
                        "created_by": user_id,
                    }
                )
                .execute()
            )

            if not pipeline_response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline",
                )

            pipeline_id = pipeline_response.data[0]["id"]

            # Create pipeline steps if provided
            if pipeline_dict.get("steps"):
                await self._create_pipeline_steps(pipeline_dict["steps"], pipeline_id)

            return pipeline_response.data[0]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline: {str(e)}",
            )

    async def _create_pipeline_steps(self, steps: List[Dict], pipeline_id: str):
        """Create pipeline steps with proper validation and dependency handling"""
        supabase = await get_supabase()

        processed_steps = []

        for step in steps:
            step_data = {
                "id": step.get("id"),
                "name": step["name"],
                "step_type": step["step_type"],
                "config": json.dumps(step["config"]),
                "run_order": step["run_order"],
                "pipeline_id": pipeline_id,
                "description": step.get("description"),
                "enabled": step.get("enabled", True),
                "depends_on": step.get("depends_on", []),
                "is_incremental_capable": step.get("is_incremental_capable", False),
            }

            # Handle inputs
            if "inputs" in step and isinstance(step["inputs"], list):
                step_data["inputs"] = ",".join(step["inputs"])

            # Handle incremental config
            if step.get("incremental_config"):
                step_data["incremental_config"] = json.dumps(step["incremental_config"])

            processed_steps.append(step_data)

        # Insert all steps
        response = (
            await supabase.from_("pipeline_steps").insert(processed_steps).execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create pipeline steps",
            )

    async def get_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Get a pipeline by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipelines")
                .select("*")
                .eq("id", pipeline_id)
                .single()
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline: {str(e)}",
            )

    async def update_pipeline(
        self, pipeline_id: str, pipeline_in: PipelineUpdate
    ) -> Dict[str, Any]:
        """Update a pipeline"""
        try:
            supabase = await get_supabase()
            # Check if pipeline exists
            await self.get_pipeline(pipeline_id)

            # Update pipeline
            data = pipeline_in.model_dump(exclude_unset=True)

            response = (
                await supabase.from_("pipelines")
                .update(data)
                .eq("id", pipeline_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline: {str(e)}",
            )

    async def delete_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Delete a pipeline"""
        try:
            supabase = await get_supabase()
            # Check if pipeline exists
            await self.get_pipeline(pipeline_id)

            # Delete pipeline
            await supabase.from_("pipelines").delete().eq("id", pipeline_id).execute()

            return {"success": True, "message": "Pipeline deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting pipeline: {str(e)}",
            )

    async def get_pipelines(
        self,
        pipeline_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        created_by: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Pipeline]:
        """Get pipelines with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("pipelines").select("*")

            if pipeline_type:
                query = query.eq("pipeline_type", pipeline_type)

            if is_active is not None:
                query = query.eq("is_active", is_active)

            if created_by:
                query = query.eq("created_by", created_by)

            response = (
                await query.order("created_at", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )

            return APIResponse(
                data=[Pipeline(**data) for data in response.data], count=response.count
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipelines: {str(e)}",
            )

    async def execute_pipeline(
        self,
        pipeline_id: str,
        user_id: Optional[str] = None,
        input_parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a pipeline with enhanced monitoring and error handling"""
        try:
            from app.tasks.worker import run_pipeline_task

            # Check if pipeline exists and is active
            pipeline = await self.get_pipeline(pipeline_id)

            if not pipeline["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pipeline is not active",
                )

            # Check for concurrent executions
            concurrent_runs = await self._get_running_pipeline_runs(pipeline_id)
            if len(concurrent_runs) > 0:
                if not input_parameters or not input_parameters.get(
                    "allow_concurrent", False
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Pipeline is already running. Set 'allow_concurrent' to true to allow parallel execution.",
                    )

            # Validate input parameters against pipeline requirements
            if input_parameters:
                await self._validate_input_parameters(pipeline_id, input_parameters)

            # Create pipeline run with enhanced metadata
            run_data = PipelineRunCreate(
                pipeline_id=pipeline_id,
                status=PipelineRunStatus.PENDING,
                start_time=datetime.now(timezone.utc),
                triggered_by=user_id,
                input_parameters=input_parameters or {},
            )

            run = await self.create_pipeline_run(run_data)

            # Start the pipeline task asynchronously
            task = run_pipeline_task.delay(
                pipeline_id=pipeline_id, run_id=run["id"], user_id=user_id
            )

            # Update run with celery task ID
            await self.update_pipeline_run(
                run_id=run["id"],
                pipeline_id=pipeline_id,
                run_update=PipelineRunUpdate(celery_task_id=task.id),
            )

            return {
                **run,
                "celery_task_id": task.id,
                "message": f"Pipeline {pipeline_id} execution started",
                "estimated_duration": await self._estimate_pipeline_duration(
                    pipeline_id
                ),
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing pipeline: {str(e)}",
            )

    async def _get_running_pipeline_runs(
        self, pipeline_id: str
    ) -> List[Dict[str, Any]]:
        """Get currently running pipeline runs"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_runs")
                .select("*")
                .eq("pipeline_id", pipeline_id)
                .eq("status", PipelineRunStatus.RUNNING)
                .execute()
            )
            return response.data
        except Exception:
            return []

    async def _validate_input_parameters(
        self, pipeline_id: str, input_parameters: Dict[str, Any]
    ):
        """Validate input parameters against pipeline requirements"""
        # This could be enhanced to validate against step configurations
        # For now, just basic validation

        if not isinstance(input_parameters, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input parameters must be a dictionary",
            )

    async def _estimate_pipeline_duration(self, pipeline_id: str) -> str:
        """Estimate pipeline duration based on steps and historical data"""
        try:
            supabase = await get_supabase()

            # Get recent successful runs
            response = (
                await supabase.from_("pipeline_runs")
                .select("duration")
                .eq("pipeline_id", pipeline_id)
                .eq("status", PipelineRunStatus.COMPLETED)
                .order("created_at", desc=True)
                .limit(10)
                .execute()
            )

            if response.data:
                durations = [
                    run["duration"] for run in response.data if run["duration"]
                ]
                if durations:
                    avg_duration = sum(durations) / len(durations)
                    return f"{int(avg_duration / 60)} minutes"

            return "15-30 minutes (estimated)"

        except Exception:
            return "15-30 minutes (estimated)"

    async def get_pipeline_execution_metrics(self, pipeline_id: str) -> Dict[str, Any]:
        """Get execution metrics for a pipeline"""
        try:
            supabase = await get_supabase()

            # Get all runs for the pipeline
            response = (
                await supabase.from_("pipeline_runs")
                .select("*")
                .eq("pipeline_id", pipeline_id)
                .order("created_at", desc=True)
                .execute()
            )

            runs = response.data

            if not runs:
                return {
                    "total_runs": 0,
                    "success_rate": 0,
                    "average_duration": 0,
                    "last_run": None,
                }

            total_runs = len(runs)
            successful_runs = [
                r for r in runs if r["status"] == PipelineRunStatus.COMPLETED
            ]
            failed_runs = [r for r in runs if r["status"] == PipelineRunStatus.FAILED]

            success_rate = (
                len(successful_runs) / total_runs * 100 if total_runs > 0 else 0
            )

            # Calculate average duration for successful runs
            successful_durations = [
                r["duration"] for r in successful_runs if r["duration"]
            ]
            avg_duration = (
                sum(successful_durations) / len(successful_durations)
                if successful_durations
                else 0
            )

            # Get recent run statistics
            recent_runs = runs[:10]  # Last 10 runs
            recent_success_rate = (
                len(
                    [
                        r
                        for r in recent_runs
                        if r["status"] == PipelineRunStatus.COMPLETED
                    ]
                )
                / len(recent_runs)
                * 100
                if recent_runs
                else 0
            )

            return {
                "total_runs": total_runs,
                "successful_runs": len(successful_runs),
                "failed_runs": len(failed_runs),
                "success_rate": round(success_rate, 2),
                "recent_success_rate": round(recent_success_rate, 2),
                "average_duration": (
                    round(avg_duration / 60, 2) if avg_duration else 0
                ),  # in minutes
                "last_run": runs[0] if runs else None,
                "last_successful_run": successful_runs[0] if successful_runs else None,
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline metrics: {str(e)}",
            )

    async def create_pipeline_run(self, run_in: PipelineRunCreate) -> Dict[str, Any]:
        """Create a new pipeline run"""
        try:
            supabase = await get_supabase()
            data = run_in.model_dump()
            data["start_time"] = datetime.now(timezone.utc).isoformat()

            response = await supabase.from_("pipeline_runs").insert(data).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline run",
                )

            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline run: {str(e)}",
            )

    async def get_pipeline_run(self, run_id: str, pipeline_id: str) -> Dict[str, Any]:
        """Get a pipeline run by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_runs")
                .select("*")
                .filter("id", "eq", run_id)
                .filter("pipeline_id", "eq", pipeline_id)
                .single()
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline run not found",
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline run: {str(e)}",
            )

    async def update_pipeline_run(
        self, run_id: str, pipeline_id: str, run_update: PipelineRunUpdate
    ) -> Dict[str, Any]:
        """Update a pipeline run"""
        try:
            supabase = await get_supabase()
            # Check if run exists
            await self.get_pipeline_run(run_id, pipeline_id)

            # Update run
            data = run_update.model_dump(exclude_unset=True)

            # Calculate duration if not provided
            if (
                run_update.status
                in [PipelineRunStatus.COMPLETED, PipelineRunStatus.FAILED]
                and run_update.end_time
                and not run_update.duration
            ):
                run = await self.get_pipeline_run(run_id, pipeline_id)
                start_time = datetime.fromisoformat(str(run["start_time"]))
                end_time = datetime.fromisoformat(str(run_update.end_time))
                data["duration"] = int((end_time - start_time).total_seconds())

            response = (
                await supabase.from_("pipeline_runs")
                .update(data)
                .eq("id", run_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline run",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline run: {str(e)}",
            )

    async def get_pipeline_runs(
        self,
        pipeline_id: Optional[str] = None,
        _status: Optional[str] = None,
        triggered_by: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get pipeline runs with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("pipeline_runs").select("*")

            if pipeline_id:
                query = query.eq("pipeline_id", pipeline_id)

            if _status:
                query = query.eq("status", _status)

            if triggered_by:
                query = query.eq("triggered_by", triggered_by)

            response = (
                await query.order("created_at", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )

            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline runs: {str(e)}",
            )

    async def get_pipeline_run_logs(self, run_id: str) -> Dict[str, Any]:
        """Get detailed logs for a pipeline run"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_run_logs")
                .select("*")
                .eq("run_id", run_id)
                .single()
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline run logs not found",
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline run logs: {str(e)}",
            )

    async def cancel_pipeline_run(self, run_id: str, pipeline_id: str) -> bool:
        """Cancel a pipeline run"""

        try:
            from app.tasks.worker import cancel_pipeline_run_task

            # Check if pipeline run exists and can be cancelled
            pipeline_run = await self.get_pipeline_run(run_id, pipeline_id)

            if not pipeline_run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline run not found",
                )
            if pipeline_run["pipeline_id"] != pipeline_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Pipeline ID does not match the run's pipeline ID",
                )

            if pipeline_run["status"] in [
                PipelineRunStatus.COMPLETED,
                PipelineRunStatus.FAILED,
                PipelineRunStatus.CANCELLED,
            ]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel pipeline run with status: {pipeline_run['status']}",
                )

            # Cancel via Celery task
            cancel_pipeline_run_task.delay(run_id)

            return True

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error cancelling pipeline: {str(e)}"
            )

    async def create_pipeline_from_template(
        self,
        datasource_id: str,
        template_name: str,
        user_id: str,
        custom_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a pipeline from a predefined template with enhanced customization"""

        from app.services.datasource import DataSourceService
        from app.services.pipeline_step import PipelineStepService
        from app.services.user import UserService

        pipeline_step_service = PipelineStepService()
        datasource_service = DataSourceService()
        user_service = UserService()

        try:
            datasource = await datasource_service.get_datasource(datasource_id)
            templates = await self.get_pipeline_templates(datasource_id)

            # Find the requested template
            template = next((t for t in templates if t["name"] == template_name), None)
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Template '{template_name}' not found for this data source",
                )

            # Generate pipeline steps based on template
            steps = await pipeline_step_service._generate_steps_from_template(
                datasource=datasource,
                template=template,
                custom_options=custom_options or {},
            )

            # Create pipeline
            pipeline_name = custom_options.get("name") if custom_options else None
            if not pipeline_name:
                pipeline_name = f"{datasource['name']} - {template_name}"

            pipeline_description = (
                custom_options.get("description") if custom_options else None
            )
            if not pipeline_description:
                pipeline_description = (
                    f"Pipeline created from template: {template['description']}"
                )

            pipeline_schedule = None
            if custom_options and "schedule_cron" in custom_options:
                pipeline_schedule = custom_options["schedule_cron"]

            pipeline_create = PipelineCreate(
                name=pipeline_name,
                description=pipeline_description,
                pipeline_type=PipelineType.COMPLETE,
                schedule=pipeline_schedule,
                is_active=True,
                steps=steps,
            )

            response = await self.create_pipeline(pipeline_create, user_id)

            # Log user activity
            await user_service._log_user_activity(
                user_id=user_id,
                action="create_pipeline_from_template",
                resource_type="pipeline",
                resource_id=response["id"],
                details={
                    "datasource_id": datasource_id,
                    "template_name": template_name,
                    "custom_options": custom_options or {},
                    "template_metadata": {
                        "complexity": template.get("complexity"),
                        "quality_level": template.get("quality_level"),
                        "estimated_duration": template.get("estimated_duration"),
                    },
                },
            )

            return response

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline from template: {str(e)}",
            )

    def _build_connection_string(
        self, connection_details: Dict, credentials: Dict
    ) -> str:
        """Build database connection string"""
        db_type = connection_details.get("db_type", "postgresql")
        host = connection_details["host"]
        port = connection_details["port"]
        database = connection_details["database"]
        username = credentials.get("username", "")
        password = credentials.get("password", "")

        if db_type == "postgresql":
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "mysql":
            return f"mysql://{username}:{password}@{host}:{port}/{database}"
        # Add more database types as needed

        return f"{db_type}://{username}:{password}@{host}:{port}/{database}"

    async def get_pipeline_templates(self, datasource_id: str) -> List[Dict[str, Any]]:
        """Get available pipeline templates based on KG construction best practices"""
        from app.services.datasource import DataSourceService

        datasource_service = DataSourceService()
        datasource = await datasource_service.get_datasource(datasource_id)
        source_type = datasource["source_type"]
        trust_score = datasource.get("trust_score", 0.5)

        # Complete pipeline templates based on the research paper
        templates = {
            "file": [
                {
                    "name": "Complete KG Construction Pipeline",
                    "description": "Full knowledge graph construction with quality assurance",
                    "steps": [
                        "file_ingestion",
                        "text_chunking",
                        "knowledge_extractor",
                        "ontology_enrichment",
                        "entity_resolution",
                        "entity_fusion",
                        "entity_enrichment",
                        "quality_monitoring",
                        "kg_writer",
                        "kg_completion",
                    ],
                    "estimated_duration": "45-60 minutes",
                    "use_case": "High-quality domain KG construction",
                    "quality_level": "high",
                    "complexity": "high",
                },
            ],
            "api": [
                {
                    "name": "API Integration",
                    "description": "Integration with structured API data sources",
                    "steps": [
                        "api_ingestion",
                        "data_validator",
                        "knowledge_extractor",
                        "ontology_enrichment",
                        "entity_resolution",
                        "entity_fusion",
                        "entity_enrichment",
                        "quality_monitoring",
                        "kg_writer",
                    ],
                    "estimated_duration": "10-20 minutes",
                    "use_case": "Structured external APIs",
                    "quality_level": "high",
                    "complexity": "medium",
                    "incremental": True,
                },
            ],
            "database": [
                {
                    "name": "Database Integration",
                    "description": "Comprehensive extraction from enterprise databases",
                    "steps": [
                        "database_ingestion",
                        "data_cleaner",
                        "data_validator",
                        "knowledge_mapping",
                        "ontology_enrichment",
                        "entity_resolution",
                        "entity_fusion",
                        "entity_enrichment",
                        "quality_monitoring",
                        "kg_writer",
                        "kg_completion",
                    ],
                    "estimated_duration": "20-35 minutes",
                    "use_case": "Enterprise data integration",
                    "quality_level": "high",
                    "complexity": "high",
                    "incremental": True,
                },
            ],
        }

        # Get templates for the source type
        source_templates = templates.get(source_type, [])

        # Adjust templates based on trust score and add quality measures
        for template in source_templates:
            # Add extra validation steps for low trust sources
            if trust_score < 0.3:
                template = self._enhance_template_for_low_trust(template)
                template["estimated_duration"] = self._adjust_duration_for_trust(
                    template["estimated_duration"], "increase"
                )
            elif trust_score > 0.8:
                # Can skip some validation for high trust sources
                template = self._optimize_template_for_high_trust(template)
                template["estimated_duration"] = self._adjust_duration_for_trust(
                    template["estimated_duration"], "decrease"
                )

            # Add metadata
            template["trust_score_optimized"] = trust_score
            template["source_type"] = source_type
            template["supports_incremental"] = template.get("incremental", False)

        return source_templates

    def _enhance_template_for_low_trust(
        self, template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance template with additional quality checks for low-trust sources"""
        enhanced_template = template.copy()
        steps = enhanced_template["steps"].copy()

        # Add additional quality assurance steps
        quality_steps_to_add = []

        # Add data validation early in pipeline
        if "data_validator" not in steps:
            if "data_cleaner" in steps:
                insert_idx = steps.index("data_cleaner") + 1
            else:
                insert_idx = 1
            quality_steps_to_add.append((insert_idx, "data_validator"))

        # Add quality monitoring before KG writing if not present
        if "quality_monitoring" not in steps and "kg_writer" in steps:
            kg_writer_idx = steps.index("kg_writer")
            quality_steps_to_add.append((kg_writer_idx, "quality_monitoring"))

        # Insert steps in reverse order to maintain indices
        for idx, step in reversed(quality_steps_to_add):
            steps.insert(idx, step)

        enhanced_template["steps"] = steps
        enhanced_template["quality_level"] = "high"
        enhanced_template["description"] += " (Enhanced for low-trust sources)"

        return enhanced_template

    def _optimize_template_for_high_trust(
        self, template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize template for high-trust sources by removing redundant steps"""
        optimized_template = template.copy()
        steps = optimized_template["steps"].copy()

        # Remove some quality checks for high-trust sources
        optional_steps = ["data_validator"]

        for step in optional_steps:
            if step in steps and len(steps) > 4:  # Keep minimum pipeline length
                steps.remove(step)

        optimized_template["steps"] = steps
        optimized_template["description"] += " (Optimized for high-trust sources)"

        return optimized_template

    def _adjust_duration_for_trust(self, duration: str, adjustment: str) -> str:
        """Adjust estimated duration based on trust score"""
        try:
            # Extract numbers from duration string like "45-60 minutes"
            import re

            numbers = re.findall(r"\d+", duration)

            if len(numbers) >= 2:
                min_time = int(numbers[0])
                max_time = int(numbers[1])

                if adjustment == "increase":
                    min_time = int(min_time * 1.3)
                    max_time = int(max_time * 1.3)
                elif adjustment == "decrease":
                    min_time = int(min_time * 0.8)
                    max_time = int(max_time * 0.8)

                return f"{min_time}-{max_time} minutes"
        except:
            pass

        return duration
