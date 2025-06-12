import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse

from app.core.supabase import get_supabase
from app.schemas.pipeline_step import (PipelineStepCreate,
                                       PipelineStepRunCreate,
                                       PipelineStepRunUpdate, PipelineStepType,
                                       PipelineStepUpdate)


class PipelineStepService:
    """Service for managing pipeline steps and their execution."""

    async def create_pipeline_step(
        self, step_in: PipelineStepCreate, pipeline_id: str
    ) -> Dict[str, Any]:
        """Create a new pipeline step with validation"""
        try:
            supabase = await get_supabase()
            step_dict = step_in.model_dump()
            step_dict["pipeline_id"] = pipeline_id

            # Validate step dependencies
            if step_dict.get("depends_on"):
                await self._validate_step_dependencies(
                    step_dict["depends_on"], pipeline_id
                )

            # Convert complex fields to JSON strings for database
            if "config" in step_dict:
                step_dict["config"] = json.dumps(step_dict["config"])
            if "incremental_config" in step_dict and step_dict["incremental_config"]:
                step_dict["incremental_config"] = json.dumps(
                    step_dict["incremental_config"]
                )
            if "inputs" in step_dict and isinstance(step_dict["inputs"], list):
                step_dict["inputs"] = ",".join(step_dict["inputs"])

            response = (
                await supabase.from_("pipeline_steps").insert(step_dict).execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline step",
                )

            return response.data[0]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline step: {str(e)}",
            )

    async def get_pipeline_step(self, step_id: str, pipeline_id: str) -> Dict[str, Any]:
        """Get a pipeline step by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_steps")
                .select("*")
                .filter("id", "eq", step_id)
                .filter("pipeline_id", "eq", pipeline_id)
                .maybe_single()
                .execute()
            )

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline step not found",
                )

            # Parse JSON fields
            step_data = response.data
            if step_data.get("config"):
                step_data["config"] = json.loads(step_data["config"])
            if step_data.get("incremental_config"):
                step_data["incremental_config"] = json.loads(
                    step_data["incremental_config"]
                )
            if step_data.get("inputs"):
                step_data["inputs"] = [
                    inp.strip() for inp in step_data["inputs"].split(",") if inp.strip()
                ]

            return step_data

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline step: {str(e)}",
            )

    async def update_pipeline_step(
        self, step_id: str, step_update: PipelineStepUpdate, pipeline_id: str
    ) -> Dict[str, Any]:
        """Update a pipeline step"""
        try:
            supabase = await get_supabase()

            # Check if step exists
            await self.get_pipeline_step(step_id, pipeline_id)

            # Prepare update data
            update_data = step_update.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Convert complex fields to JSON strings
            if "config" in update_data:
                update_data["config"] = json.dumps(update_data["config"])
            if (
                "incremental_config" in update_data
                and update_data["incremental_config"]
            ):
                update_data["incremental_config"] = json.dumps(
                    update_data["incremental_config"]
                )
            if "depends_on" in update_data and isinstance(
                update_data["depends_on"], list
            ):
                update_data["depends_on"] = update_data[
                    "depends_on"
                ]  # PostgreSQL array

            # Validate dependencies if updated
            if update_data.get("depends_on"):
                await self._validate_step_dependencies(
                    update_data["depends_on"], pipeline_id
                )

            response = (
                await supabase.from_("pipeline_steps")
                .update(update_data)
                .eq("id", step_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline step",
                )

            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline step: {str(e)}",
            )

    async def delete_pipeline_step(
        self, step_id: str, pipeline_id: str
    ) -> Dict[str, Any]:
        """Delete a pipeline step"""
        try:
            supabase = await get_supabase()

            # Check if step exists
            await self.get_pipeline_step(step_id, pipeline_id)

            # Check for dependent steps
            dependent_steps = await self._get_dependent_steps(step_id, pipeline_id)
            if dependent_steps:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete step with dependencies: {[s['name'] for s in dependent_steps]}",
                )

            # Delete step
            await supabase.from_("pipeline_steps").delete().eq("id", step_id).execute()

            return {"success": True, "message": "Pipeline step deleted"}

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting pipeline step: {str(e)}",
            )

    async def get_pipeline_steps(
        self, pipeline_id: str, limit: int = 100, skip: int = 0
    ) -> APIResponse[Dict[str, Any]]:
        """Get pipeline steps with filtering and pagination"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_steps")
                .select("*")
                .eq("pipeline_id", pipeline_id)
                .order("run_order")
                .range(skip, skip + limit - 1)
                .execute()
            )

            # Process the response data
            processed_data = []
            for step_data in response.data:
                processed_step = {
                    "id": step_data["id"],
                    "pipeline_id": step_data["pipeline_id"],
                    "name": step_data["name"],
                    "step_type": step_data["step_type"],
                    "config": (
                        json.loads(step_data["config"]) if step_data["config"] else {}
                    ),
                    "run_order": step_data["run_order"],
                    "description": step_data.get("description"),
                    "enabled": step_data.get("enabled", True),
                    "depends_on": step_data.get("depends_on", []),
                    "inputs": [
                        inp.strip()
                        for inp in (step_data.get("inputs") or "").split(",")
                        if inp.strip()
                    ],
                    "is_incremental_capable": step_data.get(
                        "is_incremental_capable", False
                    ),
                    "incremental_config": (
                        json.loads(step_data["incremental_config"])
                        if step_data.get("incremental_config")
                        else None
                    ),
                    "created_at": step_data["created_at"],
                    "updated_at": step_data["updated_at"],
                }
                processed_data.append(processed_step)

            return APIResponse(data=processed_data, count=response.count)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline steps: {str(e)}",
            )

    async def get_step_execution_order(self, pipeline_id: str) -> List[List[str]]:
        """Get steps organized by execution order, considering dependencies"""
        try:
            steps_response = await self.get_pipeline_steps(pipeline_id)
            steps = steps_response.data

            # Build dependency graph
            dependency_graph = {}
            all_steps = {}

            for step in steps:
                if not step["enabled"]:
                    continue

                step_id = step["id"]
                all_steps[step_id] = step
                dependency_graph[step_id] = step.get("depends_on", [])

            # Topological sort to determine execution order
            execution_levels = []
            remaining_steps = set(all_steps.keys())

            while remaining_steps:
                # Find steps with no unresolved dependencies
                ready_steps = []
                for step_id in remaining_steps:
                    dependencies = dependency_graph[step_id]
                    if not dependencies or all(
                        dep not in remaining_steps for dep in dependencies
                    ):
                        ready_steps.append(step_id)

                if not ready_steps:
                    # Circular dependency detected
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Circular dependency detected in pipeline steps",
                    )

                execution_levels.append(ready_steps)
                remaining_steps -= set(ready_steps)

            return execution_levels

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error determining execution order: {str(e)}",
            )

    async def get_pipeline_step_runs(
        self,
        pipeline_run_id: str,
        step_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get pipeline step runs with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = (
                supabase.from_("pipeline_step_runs")
                .select("*")
                .filter("pipeline_run_id", "eq", pipeline_run_id)
            )

            if step_id:
                query = query.filter("step_id", "eq", step_id)
            if status:
                query = query.filter("status", "eq", status)

            response = (
                await query.order("created_at", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )

            if "output_data" in response.data[0]:
                for step_run in response.data:
                    if step_run["output_data"]:
                        step_run["output_data"] = json.loads(step_run["output_data"])
            if "input_data" in response.data[0]:
                for step_run in response.data:
                    if step_run["input_data"]:
                        step_run["input_data"] = json.loads(step_run["input_data"])

            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline step runs: {str(e)}",
            )

    async def get_pipeline_step_run(
        self, pipeline_run_id: str, step_run_id: str
    ) -> Dict[str, Any]:
        """Get a pipeline step run by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("pipeline_step_runs")
                .select("*")
                .filter("id", "eq", step_run_id)
                .filter("pipeline_run_id", "eq", pipeline_run_id)
                .maybe_single()
                .execute()
            )
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Pipeline step run not found",
                )
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving pipeline step run: {str(e)}",
            )

    async def create_step_run(
        self, step_run_in: PipelineStepRunCreate
    ) -> Dict[str, Any]:
        """Create a new pipeline step run"""
        try:
            supabase = await get_supabase()

            step_run_data = step_run_in.model_dump(exclude_unset=True)

            if "input_data" in step_run_data and step_run_data["input_data"]:
                step_run_data["input_data"] = json.dumps(step_run_data["input_data"])

            if "start_time" in step_run_data:
                step_run_data["start_time"] = step_run_data["start_time"].isoformat()
            if "end_time" in step_run_data:
                step_run_data["end_time"] = step_run_data["end_time"].isoformat()

            response = (
                await supabase.from_("pipeline_step_runs")
                .insert(step_run_data)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create pipeline step run",
                )

            return response.data[0]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pipeline step run: {str(e)}",
            )

    async def update_pipeline_step_run(
        self,
        step_run_id: str,
        pipeline_run_id: str,
        step_run_update: PipelineStepRunUpdate,
    ) -> Dict[str, Any]:
        """Update a pipeline step run"""
        try:
            supabase = await get_supabase()

            update_data = step_run_update.model_dump(exclude_unset=True)

            # Convert complex fields to JSON
            if "output_data" in update_data and update_data["output_data"]:
                update_data["output_data"] = json.dumps(update_data["output_data"])

            if "start_time" in update_data:
                update_data["start_time"] = update_data["start_time"].isoformat()

            if "end_time" in update_data:
                update_data["end_time"] = update_data["end_time"].isoformat()

            response = (
                await supabase.from_("pipeline_step_runs")
                .update(update_data)
                .eq("id", step_run_id)
                .eq("pipeline_run_id", pipeline_run_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update pipeline step run",
                )

            return response.data[0]

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating pipeline step run: {str(e)}",
            )

    async def delete_pipeline_step_run(
        self, step_run_id: str, pipeline_run_id: str
    ) -> Dict[str, Any]:
        """Delete a pipeline step run"""
        try:
            supabase = await get_supabase()
            # Check if step run exists
            await self.get_pipeline_step_run(step_run_id, pipeline_run_id)
            # Delete step run
            await supabase.from_("pipeline_step_runs").delete().eq(
                "id", step_run_id
            ).execute()
            return {"success": True, "message": "Pipeline step run deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting pipeline step run: {str(e)}",
            )

    async def _generate_steps_from_template(
        self,
        datasource: Dict[str, Any],
        template: Dict[str, Any],
        custom_options: Dict[str, Any],
    ) -> List[PipelineStepCreate]:
        """Generate pipeline steps from template based on paper recommendations"""

        steps = []
        trust_score = datasource.get("trust_score", 0.5)
        source_type = datasource.get("source_type", "unknown")

        # Get step configurations from custom options
        step_configs = custom_options.get("steps", {})

        for i, step_type in enumerate(template["steps"]):
            step_key = f"{step_type}_{i}"
            step_custom_config = step_configs.get(step_key, {})

            step_config = await self._get_step_config_for_datasource(
                step_type=step_type,
                datasource=datasource,
                custom_options=custom_options,
                step_custom_config=step_custom_config,
                trust_score=trust_score,
            )

            # Determine dependencies
            inputs = []
            depends_on = []
            if i > 0:
                inputs = [f"{steps[i-1].id}"]
                depends_on = [steps[i - 1].id]

            step = PipelineStepCreate(
                id=str(uuid4()),
                name=self._get_step_display_name(step_type),
                step_type=PipelineStepType(step_type),
                config=step_config,
                run_order=i + 1,
                inputs=inputs,
                depends_on=depends_on,
                enabled=True,
                is_incremental_capable=self._is_step_incremental_capable(step_type),
                incremental_config=(
                    self._get_incremental_config(step_type, datasource)
                    if self._is_step_incremental_capable(step_type)
                    else None
                ),
            )
            steps.append(step)

        return steps

    async def _get_step_config_for_datasource(
        self,
        step_type: str,
        datasource: Dict[str, Any],
        custom_options: Dict[str, Any],
        step_custom_config: Optional[Dict[str, Any]] = None,
        trust_score: float = 0.5,
    ) -> Dict[str, Any]:
        """Get step configuration based on datasource and step type"""

        base_config = {
            "datasource_id": datasource["id"],
            "trust_score": trust_score,
            "metadata_tracking": True,
        }

        connection_details = datasource.get("connection_details", {})
        source_type = datasource.get("source_type", "unknown")

        if step_custom_config is None:
            step_custom_config = {}

        # Configure based on step type and source type
        if step_type == "file_ingestion":
            config = {
                **base_config,
                "file_paths": connection_details.get("file_paths", []),
                "encoding": connection_details.get("encoding", "utf-8"),
                "supported_formats": connection_details.get(
                    "supported_formats", ["txt", "pdf", "json"]
                ),
                "extract_metadata": True,
                **step_custom_config,
            }

        elif step_type == "api_ingestion":
            config = {
                **base_config,
                "url": connection_details.get("base_url"),
                "method": connection_details.get("method", "GET"),
                "headers": connection_details.get("headers", {}),
                "auth_type": connection_details.get("auth_type"),
                "rate_limit": connection_details.get("rate_limit", {}),
                **step_custom_config,
            }

        elif step_type == "database_ingestion":
            config = {
                **base_config,
                "connection_string": self._build_connection_string(connection_details),
                "query": step_custom_config.get("query", "SELECT * FROM main_table"),
                "batch_size": step_custom_config.get("batch_size", 1000),
                "incremental_column": connection_details.get("incremental_column"),
                **step_custom_config,
            }

        elif step_type == "text_chunking":
            config = {
                **base_config,
                "chunk_size": step_custom_config.get("chunk_size", 1000),
                "chunk_overlap": step_custom_config.get("chunk_overlap", 200),
                "chunking_strategy": step_custom_config.get(
                    "chunking_strategy", "recursive"
                ),
                "preserve_structure": True,
                **step_custom_config,
            }

        elif step_type == "data_cleaner":
            config = {
                **base_config,
                "remove_duplicates": step_custom_config.get("remove_duplicates", True),
                "normalize_text": step_custom_config.get("normalize_text", True),
                "remove_empty_values": step_custom_config.get(
                    "remove_empty_values", True
                ),
                "standardize_formats": step_custom_config.get(
                    "standardize_formats", True
                ),
                **step_custom_config,
            }

        elif step_type == "data_validator":
            config = {
                **base_config,
                "validation_rules": step_custom_config.get("validation_rules", []),
                "schema_validation": step_custom_config.get("schema_validation", True),
                "quality_thresholds": step_custom_config.get("quality_thresholds", {}),
                **step_custom_config,
            }

        elif step_type == "knowledge_extractor":
            config = {
                **base_config,
                "extraction_method": step_custom_config.get(
                    "extraction_method", "rule_based"
                ),
                "entity_types": step_custom_config.get(
                    "entity_types", ["PERSON", "ORG", "LOCATION"]
                ),
                "relation_types": step_custom_config.get("relation_types", []),
                "confidence_threshold": max(0.7, trust_score),
                **step_custom_config,
            }

        elif step_type == "knowledge_mapping":
            config = {
                **base_config,
                "model": step_custom_config.get("model", "gpt-4o-mini"),
                "entity_types": step_custom_config.get(
                    "entity_types", ["PERSON", "ORG", "LOCATION"]
                ),
                "relation_types": step_custom_config.get("relation_types", []),
                "confidence_threshold": max(0.7, trust_score),
                "context_window": step_custom_config.get("context_window", 4000),
                **step_custom_config,
            }

        elif step_type == "ontology_enrichment":
            config = {
                **base_config,
                "ontology_source": step_custom_config.get("ontology_source", "custom"),
                "enrichment_strategy": step_custom_config.get(
                    "enrichment_strategy", "mapping"
                ),
                "similarity_threshold": max(0.8, trust_score),
                "auto_enrichment": step_custom_config.get("auto_enrichment", True),
                **step_custom_config,
            }

        elif step_type == "entity_resolution":
            # Adjust resolution strategy based on trust score
            resolution_strategy = "exact_match" if trust_score > 0.8 else "fuzzy_match"
            config = {
                **base_config,
                "resolution_strategy": resolution_strategy,
                "similarity_threshold": max(0.8, trust_score + 0.1),
                "blocking_strategy": "standard",
                "batch_size": 1000,
                **step_custom_config,
            }

        elif step_type == "entity_fusion":
            config = {
                **base_config,
                "fusion_strategy": "weighted" if trust_score < 0.6 else "most_recent",
                "preserve_provenance": True,
                "quality_threshold": trust_score,
                **step_custom_config,
            }

        elif step_type == "entity_enrichment":
            config = {
                **base_config,
                "enrichment_sources": step_custom_config.get("enrichment_sources", []),
                "enrichment_types": step_custom_config.get(
                    "enrichment_types", ["attributes"]
                ),
                "enrichment_strategy": step_custom_config.get(
                    "enrichment_strategy", "append"
                ),
                "confidence_threshold": max(0.7, trust_score),
                **step_custom_config,
            }

        elif step_type == "kg_writer":
            config = {
                **base_config,
                "graph_format": step_custom_config.get("graph_format", "rdf"),
                "batch_size": step_custom_config.get("batch_size", 1000),
                "validate_before_write": trust_score < 0.7,
                "update_if_exists": "merge",
                **step_custom_config,
            }

        elif step_type == "kg_completion":
            config = {
                **base_config,
                "completion_method": step_custom_config.get(
                    "completion_method", "embedding"
                ),
                "link_prediction": step_custom_config.get("link_prediction", True),
                "confidence_threshold": max(0.8, trust_score),
                **step_custom_config,
            }

        elif step_type == "quality_monitoring":
            # More rigorous quality checks for low-trust sources
            metrics = ["completeness", "consistency"]
            if trust_score < 0.6:
                metrics.extend(["accuracy"])

            config = {
                **base_config,
                "metrics": metrics,
                "quality_threshold": min(0.8, trust_score + 0.2),
                "monitoring_frequency": "batch",
                **step_custom_config,
            }

        else:
            # Default configuration for unknown step types
            config = {**base_config, **step_custom_config}

        return config

    def _get_step_display_name(self, step_type: str) -> str:
        """Get display name for step type"""
        names = {
            "file_ingestion": "File Ingestion",
            "api_ingestion": "API Data Ingestion",
            "database_ingestion": "Database Ingestion",
            "text_chunking": "Text Chunking",
            "data_cleaner": "Data Cleaner",
            "data_validator": "Data Validator",
            "knowledge_extractor": "Knowledge Extractor",
            "knowledge_mapping": "Knowledge Mapping",
            "ontology_enrichment": "Ontology Enrichment",
            "entity_resolution": "Entity Resolution",
            "entity_fusion": "Entity Fusion",
            "entity_enrichment": "Entity Enrichment",
            "kg_writer": "Knowledge Graph Writer",
            "kg_completion": "Knowledge Graph Completion",
            "quality_monitoring": "Quality Monitoring",
            "custom_python": "Custom Python Script",
        }
        return names.get(step_type, step_type.replace("_", " ").title())

    def _is_step_incremental_capable(self, step_type: str) -> bool:
        """Check if step type supports incremental processing"""
        incremental_capable_types = {
            "file_ingestion",
            "api_ingestion",
            "database_ingestion",
            "knowledge_extractor",
            "knowledge_mapping",
            "entity_resolution",
            "kg_writer",
            "quality_monitoring",
        }
        return step_type in incremental_capable_types

    def _get_incremental_config(
        self, step_type: str, datasource: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get incremental configuration for step type"""
        connection_details = datasource.get("connection_details", {})

        if step_type in ["database_ingestion", "api_ingestion"]:
            return {
                "enabled": True,
                "strategy": "timestamp",
                "checkpoint_field": connection_details.get(
                    "incremental_column", "updated_at"
                ),
                "change_detection": "polling",
            }
        elif step_type == "file_ingestion":
            return {
                "enabled": True,
                "strategy": "file_modification",
                "checkpoint_field": "file_mtime",
                "change_detection": "polling",
            }

        return None

    def _build_connection_string(self, connection_details: Dict) -> str:
        """Build database connection string"""
        db_type = connection_details.get("db_type", "postgresql")
        host = connection_details.get("host", "localhost")
        port = connection_details.get("port", 5432)
        database = connection_details.get("database", "")
        username = connection_details.get("username", "")
        password = connection_details.get("password", "")

        if db_type == "postgresql":
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "mysql":
            return f"mysql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == "sqlite":
            return f"sqlite:///{database}"

        return f"{db_type}://{username}:{password}@{host}:{port}/{database}"

    # Helper methods
    async def _validate_step_dependencies(
        self, depends_on: List[str], pipeline_id: str
    ):
        """Validate that all dependencies exist in the pipeline"""
        if not depends_on:
            return

        supabase = await get_supabase()
        response = (
            await supabase.from_("pipeline_steps")
            .select("id")
            .eq("pipeline_id", pipeline_id)
            .in_("id", depends_on)
            .execute()
        )

        found_ids = {step["id"] for step in response.data}
        missing_ids = set(depends_on) - found_ids

        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dependency steps not found: {list(missing_ids)}",
            )

    async def _get_dependent_steps(
        self, step_id: str, pipeline_id: str
    ) -> List[Dict[str, Any]]:
        """Get steps that depend on the given step"""
        supabase = await get_supabase()
        response = (
            await supabase.from_("pipeline_steps")
            .select("id, name")
            .eq("pipeline_id", pipeline_id)
            .contains("depends_on", [step_id])
            .execute()
        )

        return response.data
