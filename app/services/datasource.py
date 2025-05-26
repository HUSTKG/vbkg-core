from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.core.config import settings
from app.core.supabase import get_supabase
from app.schemas.datasource import DataSourceCreate, DataSourceUpdate
from app.schemas.pipeline import PipelineCreate, PipelineType
from app.schemas.pipeline_step import PipelineStepCreate, PipelineStepType
from app.services.user import UserService


class DataSourceService:
    def __init__(self):
        self.user_service = UserService()

    async def create_datasource(
        self, datasource_in: DataSourceCreate, user_id: str
    ) -> Dict[str, Any]:
        """Create a new data source"""
        try:
            supabase = await get_supabase()
            data = datasource_in.model_dump()
            data["created_by"] = user_id

            # Convert Enum to string
            data["source_type"] = data["source_type"].value

            # Handle sensitive credentials - encrypt if needed
            if data.get("credentials"):
                encrypted_data = await supabase.rpc(
                    "encrypt_data_source_credentials",
                    {
                        "p_credentials": data["credentials"],
                        "p_encryption_key": settings.ENCRYPTION_KEY,
                    },
                ).execute()
                data["credentials"] = encrypted_data.data[0]["encrypted_credentials"]

            response = await supabase.from_("data_sources").insert(data).execute()

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create data source",
                )

            await self.user_service._log_user_activity(
                user_id=user_id,
                action="create_datasource",
                resource_type="datasource",
                resource_id=response.data[0]["id"],
                details={
                    "datasource_id": response.data[0]["id"],
                    "name": response.data[0]["name"],
                },
            )
            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating data source: {str(e)}",
            )

    async def get_datasource(self, datasource_id: str) -> Dict[str, Any]:
        """Get a data source by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.table("data_sources")
                .select("*")
                .eq("id", datasource_id)
                .maybe_single()
                .execute()
            )

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Data source not found",
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data source: {str(e)}",
            )

    async def update_datasource(
        self, datasource_id: str, datasource_in: DataSourceUpdate
    ) -> Dict[str, Any]:
        """Update a data source"""
        try:
            supabase = await get_supabase()
            # First check if data source exists
            await self.get_datasource(datasource_id)

            # Update the data source
            data = datasource_in.model_dump(exclude_unset=True)

            # Convert Enum to string if present
            if "source_type" in data:
                data["source_type"] = str(data["source_type"])

            if "credentials" in data:
                encrypted_data = await supabase.rpc(
                    "encrypt_data_source_credentials",
                    {
                        "p_credentials": data["credentials"],
                        "p_encryption_key": settings.ENCRYPTION_KEY,
                    },
                ).execute()

                data["encrypted_credentials"] = encrypted_data.data[0]

            response = (
                await supabase.from_("data_sources")
                .update(data)
                .eq("id", datasource_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update data source",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating data source: {str(e)}",
            )

    async def delete_datasource(self, datasource_id: str) -> Dict[str, Any]:
        """Delete a data source"""
        try:
            supabase = await get_supabase()
            # First check if data source exists
            await self.get_datasource(datasource_id)

            # Delete the data source
            await supabase.from_("data_sources").delete().eq(
                "id", datasource_id
            ).execute()

            return {"success": True, "message": "Data source deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting data source: {str(e)}",
            )

    async def get_datasources(
        self,
        skip: int = 0,
        limit: int = 100,
        source_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> APIResponse[Dict[str, Any]]:
        """Get all data sources with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("data_sources").select("*", count=CountMethod.exact)

            if source_type:
                query = query.eq("source_type", source_type)

            if is_active is not None:
                query = query.eq("is_active", is_active)

            response = (
                await query.order("created_at", desc=False)
                .range(skip, skip + limit - 1)
                .execute()
            )

            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data sources: {str(e)}",
            )

    async def get_data_source_credentials(
        self,
        data_source_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get the credentials for a data source"""
        try:
            supabase = await get_supabase()
            # Get the data source
            datasource = await self.get_datasource(data_source_id)
            if not datasource:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Data source not found",
                )
            # Decrypt credentials if they exist
            if datasource.get("credentials"):
                encrypted_credentials = datasource["credentials"]
                decrypted_credentials = await supabase.rpc(
                    "decrypt_data_source_credentials",
                    {
                        "p_encrypted_credentials": encrypted_credentials,
                        "p_encryption_key": settings.ENCRYPTION_KEY,
                    },
                ).execute()
                return decrypted_credentials.data["decrypted_credentials"]
            return None
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data source credentials: {str(e)}",
            )

    async def get_pipeline_templates(self, datasource_id: str) -> List[Dict[str, Any]]:
        """Get available pipeline templates for this data source"""
        datasource = await self.get_datasource(datasource_id)
        source_type = datasource["source_type"]

        templates = {
            "file": [
                {
                    "name": "Basic File Processing",
                    "description": "Extract text and entities from file",
                    "steps": [
                        "file_reader",
                        "text_extractor",
                        "llm_entity_extractor",
                        "knowledge_graph_writer",
                    ],
                    "estimated_duration": "5-10 minutes",
                },
                {
                    "name": "Advanced File Analysis",
                    "description": "Complete file analysis with validation and FIBO mapping",
                    "steps": [
                        "file_reader",
                        "data_validation",
                        "text_extractor",
                        "llm_entity_extractor",
                        "entity_resolution",
                        "fibo_mapper",
                        "knowledge_graph_writer",
                    ],
                    "estimated_duration": "15-20 minutes",
                },
            ],
            "api": [
                {
                    "name": "API Data Ingestion",
                    "description": "Fetch and process API data",
                    "steps": [
                        "api_fetcher",
                        "data_validation",
                        "llm_entity_extractor",
                        "knowledge_graph_writer",
                    ],
                    "estimated_duration": "3-8 minutes",
                }
            ],
            "database": [
                {
                    "name": "Database ETL",
                    "description": "Extract, transform and load database data",
                    "steps": [
                        "database_extractor",
                        "data_profiling",
                        "data_transformation",
                        "llm_entity_extractor",
                        "knowledge_graph_writer",
                    ],
                    "estimated_duration": "10-15 minutes",
                }
            ],
        }

        return templates.get(source_type, [])

    async def create_pipeline_from_template(
        self,
        datasource_id: str,
        template_name: str,
        user_id: str,
        custom_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a pipeline from a predefined template"""

        datasource = await self.get_datasource(datasource_id)
        templates = await self.get_pipeline_templates(datasource_id)

        # Find the requested template
        template = next((t for t in templates if t["name"] == template_name), None)
        if not template:
            raise ValueError(
                f"Template '{template_name}' not found for this data source"
            )

        # Generate pipeline steps based on template
        steps = await self._generate_steps_from_template(
            datasource=datasource,
            template=template,
            custom_options=custom_options or {},
        )

        # Create pipeline
        from app.services.pipeline import PipelineService

        pipeline_service = PipelineService()

        pipeline_create = PipelineCreate(
            name=f"{datasource['name']} - {template_name}",
            description=f"Auto-generated pipeline from template: {template['description']}",
            pipeline_type=PipelineType.COMPLETE,
            schedule=custom_options.get("schedule"),
            is_active=True,
            steps=steps,
        )

        await self.user_service._log_user_activity(
            user_id=user_id,
            action="create_pipeline_from_template",
            resource_type="pipeline",
            resource_id=pipeline_create.name,
            details={
                "datasource_id": datasource_id,
                "template_name": template_name,
                "custom_options": custom_options or {},
            },
        )

        return await pipeline_service.create_pipeline(pipeline_create, user_id)

    async def _generate_steps_from_template(
        self,
        datasource: Dict[str, Any],
        template: Dict[str, Any],
        custom_options: Dict[str, Any],
    ) -> List[PipelineStepCreate]:
        """Generate pipeline steps from template"""

        steps = []
        source_type = datasource["source_type"]
        connection_details = datasource["connection_details"]

        for i, step_type in enumerate(template["steps"]):
            step_config = await self._get_step_config_for_datasource(
                step_type=step_type,
                datasource=datasource,
                custom_options=custom_options,
            )

            step = PipelineStepCreate(
                id=str(uuid4()),
                name=self._get_step_display_name(step_type),
                step_type=PipelineStepType(step_type),
                config=step_config,
                run_order=i + 1,
                inputs=[f"{steps[i-1].id}"] if i > 0 else [],
                enabled=True,
            )
            steps.append(step)

        return steps

    async def _get_step_config_for_datasource(
        self, step_type: str, datasource: Dict[str, Any], custom_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get step configuration based on data source"""

        base_config = {"datasource_id": datasource["id"]}
        source_type = datasource["source_type"]
        connection_details = datasource["connection_details"]

        if step_type == "file_reader":
            return {
                **base_config,
                "encoding": connection_details.get("encoding", "utf-8"),
                "file_format": connection_details.get("file_format", "auto"),
            }

        elif step_type == "api_fetcher":
            return {
                **base_config,
                "url": connection_details["url"],
                "method": connection_details.get("method", "GET"),
                "headers": connection_details.get("headers", {}),
                "auth_type": connection_details.get("auth_type"),
                "data_format": custom_options.get("data_format", "json"),
            }

        elif step_type == "database_extractor":
            # Build connection string from datasource credentials
            credentials = await self.get_data_source_credentials(datasource["id"])
            connection_string = self._build_connection_string(
                connection_details, credentials
            )

            return {
                **base_config,
                "connection_string": connection_string,
                "query": connection_details.get("query", "SELECT * FROM your_table"),
                "batch_size": custom_options.get("batch_size", 1000),
            }

        elif step_type == "text_extractor":
            return {
                **base_config,
                "input_format": custom_options.get("input_format", "auto"),
                "extract_tables": custom_options.get("extract_tables", True),
                "extract_metadata": custom_options.get("extract_metadata", True),
                "chunk_size": custom_options.get("chunk_size", 1000),
            }

        elif step_type == "llm_entity_extractor":
            return {
                **base_config,
                "model": custom_options.get("llm_model", "gpt-4o-mini"),
                "entity_types": custom_options.get(
                    "entity_types", ["PERSON", "ORGANIZATION", "LOCATION"]
                ),
                "extract_relationships": custom_options.get(
                    "extract_relationships", True
                ),
                "temperature": 0.2,
            }

        elif step_type == "data_validation":
            return {
                **base_config,
                "validation_rules": custom_options.get("validation_rules", []),
                "quality_threshold": custom_options.get("quality_threshold", 0.8),
            }

        elif step_type == "entity_resolution":
            return {
                **base_config,
                "similarity_threshold": custom_options.get("similarity_threshold", 0.8),
                "resolution_strategy": "fuzzy_match",
            }

        elif step_type == "fibo_mapper":
            return {
                **base_config,
                "mapping_confidence_threshold": 0.7,
                "domains": custom_options.get("fibo_domains", []),
            }

        elif step_type == "knowledge_graph_writer":
            return {**base_config, "batch_size": 100, "track_provenance": True}

        else:
            return base_config

    def _get_step_display_name(self, step_type: str) -> str:
        """Get display name for step type"""
        names = {
            "file_reader": "Read File",
            "api_fetcher": "Fetch API Data",
            "database_extractor": "Extract Database Data",
            "text_extractor": "Extract Text",
            "llm_entity_extractor": "Extract Entities",
            "data_validation": "Validate Data",
            "entity_resolution": "Resolve Entities",
            "fibo_mapper": "Map to FIBO",
            "knowledge_graph_writer": "Write to Knowledge Graph",
            "data_profiling": "Profile Data",
        }
        return names.get(step_type, step_type.replace("_", " ").title())

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
