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
                data["encrypted_credentials"] = encrypted_data.data

            # pop the credentials
            data.pop("credentials", None)

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

    async def get_datasource_with_credentials(
        self, datasource_id: str
    ) -> Dict[str, Any]:
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

            # Decrypt credentials if they exist
            if response.data.get("encrypted_credentials"):
                decrypted_credentials = await supabase.rpc(
                    "decrypt_data_source_credentials",
                    {
                        "p_id": datasource_id,
                        "p_encryption_key": settings.ENCRYPTION_KEY,
                    },
                ).execute()

                if decrypted_credentials.data:
                    response.data["credentials"] = decrypted_credentials.data

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving data source: {str(e)}",
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

                print(encrypted_data.data)
                data["encrypted_credentials"] = encrypted_data.data

            # remove the original credentials field if it exists
            if "credentials" in data:
                data.pop("credentials")

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
                    "name": "File Analysis",
                    "description": "Complete file analysis with validation and FIBO mapping",
                    "steps": [
                        "file_reader",
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

        pipeline_name = f"{datasource['name']} - {template_name}"
        if custom_options and "name" in custom_options:
            pipeline_name = custom_options["name"]
        pipeline_description = (
            f"Pipeline created from template: {template['description']}"
        )
        if custom_options and "description" in custom_options:
            pipeline_description = custom_options["description"]

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

        response = await pipeline_service.create_pipeline(pipeline_create, user_id)
        await self.user_service._log_user_activity(
            user_id=user_id,
            action="create_pipeline_from_template",
            resource_type="pipeline",
            resource_id=response["id"],
            details={
                "datasource_id": datasource_id,
                "template_name": template_name,
                "custom_options": custom_options or {},
            },
        )

        return response

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

        # Extract step configurations from custom_options
        step_configs = custom_options.get("steps", {})
        print("Step configurations from frontend:", step_configs)

        for i, step_type in enumerate(template["steps"]):
            # Create step key to match frontend format: stepName_index
            step_key = f"{step_type}_{i}"

            # Get custom configuration for this specific step
            step_custom_config = step_configs.get(step_key, {})

            step_config = await self._get_step_config_for_datasource(
                step_type=step_type,
                datasource=datasource,
                custom_options=custom_options,
                step_custom_config=step_custom_config,
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
        self,
        step_type: str,
        datasource: Dict[str, Any],
        custom_options: Dict[str, Any],
        step_custom_config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Get step configuration based on data source and custom step configuration"""

        from app.services.domain import DomainService

        base_config = {"datasource_id": datasource["id"]}
        source_type = datasource["source_type"]
        connection_details = datasource["connection_details"]

        # If no custom step config provided, use empty dict
        if step_custom_config is None:
            step_custom_config = {}

        if step_type == "file_reader":
            config = {
                **base_config,
                "encoding": step_custom_config.get(
                    "encoding", connection_details.get("encoding", "utf-8")
                ),
                "file_format": step_custom_config.get(
                    "file_format", connection_details.get("file_format", "auto")
                ),
            }

        elif step_type == "api_fetcher":
            # Handle headers - if it's a string (from textarea), try to parse as JSON
            headers = step_custom_config.get("headers", "{}")
            if isinstance(headers, str):
                try:
                    import json

                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            config = {
                **base_config,
                "url": connection_details["url"],
                "method": step_custom_config.get(
                    "method", connection_details.get("method", "GET")
                ),
                "headers": headers,
                "auth_type": connection_details.get("auth_type"),
                "data_format": step_custom_config.get(
                    "data_format", custom_options.get("data_format", "json")
                ),
            }

        elif step_type == "database_extractor":
            # Build connection string from datasource credentials
            credentials = await self.get_data_source_credentials(datasource["id"])
            connection_string = self._build_connection_string(
                connection_details, credentials
            )

            config = {
                **base_config,
                "connection_string": connection_string,
                "query": step_custom_config.get(
                    "query", connection_details.get("query", "SELECT * FROM your_table")
                ),
                "batch_size": step_custom_config.get(
                    "batch_size", custom_options.get("batch_size", 1000)
                ),
            }

        elif step_type == "text_extractor":
            config = {
                **base_config,
                "input_format": step_custom_config.get(
                    "input_format", custom_options.get("input_format", "auto")
                ),
                "extract_tables": step_custom_config.get(
                    "extract_tables", custom_options.get("extract_tables", True)
                ),
                "extract_metadata": step_custom_config.get(
                    "extract_metadata", custom_options.get("extract_metadata", True)
                ),
                "chunk_size": step_custom_config.get(
                    "chunk_size", custom_options.get("chunk_size", 1000)
                ),
            }

        elif step_type == "llm_entity_extractor":
            # Handle entity_types - ensure it's a list
            domain = step_custom_config.get("domain")
            prompt_template = step_custom_config.get(
                "prompt_template", custom_options.get("prompt_template", "")
            )
            domain_service = DomainService()
            entity_types = step_custom_config.get("entity_types", [])
            relationship_types = step_custom_config.get("relationship_types", [])
            if domain:
                entity_types = await domain_service._get_domain_entity_types(
                    domain_id=domain
                )
                relationship_types = (
                    await domain_service._get_domain_relationship_types(
                        domain_id=domain
                    )
                )

            config = {
                **base_config,
                "model": step_custom_config.get(
                    "llm_model", custom_options.get("llm_model", "gpt-4o-mini")
                ),
                "entity_types": [entity_type["name"] for entity_type in entity_types],
                "relationship_types": [relationship_type['name'] for relationship_type in relationship_types],
                "prompt_template": prompt_template,
                "extract_relationships": step_custom_config.get(
                    "extract_relationships",
                    custom_options.get("extract_relationships", True),
                ),
                "temperature": step_custom_config.get("temperature", 0.2),
            }

        elif step_type == "data_validation":
            # Handle validation_rules - if it's a string, try to parse as JSON
            validation_rules = step_custom_config.get(
                "validation_rules", custom_options.get("validation_rules", [])
            )
            if isinstance(validation_rules, str):
                try:
                    import json

                    validation_rules = json.loads(validation_rules)
                except json.JSONDecodeError:
                    validation_rules = []

            config = {
                **base_config,
                "validation_rules": validation_rules,
                "quality_threshold": step_custom_config.get(
                    "quality_threshold", custom_options.get("quality_threshold", 0.8)
                ),
            }

        elif step_type == "entity_resolution":
            config = {
                **base_config,
                "similarity_threshold": step_custom_config.get(
                    "similarity_threshold",
                    custom_options.get("similarity_threshold", 0.8),
                ),
                "resolution_strategy": step_custom_config.get(
                    "resolution_strategy", "fuzzy_match"
                ),
            }

        elif step_type == "fibo_mapper":
            # Handle fibo_domains - ensure it's a list
            fibo_domains = step_custom_config.get(
                "fibo_domains", custom_options.get("fibo_domains", [])
            )
            create_unmapped = step_custom_config.get(
                "create_unmapped", custom_options.get("create_unmapped", True)
            )
            batch_size = step_custom_config.get(
                "batch_size", custom_options.get("batch_size", 100)
            )
            fuzzy_matching = step_custom_config.get(
                "fuzzy_matching", custom_options.get("fuzzy_matching", True)
            )
            similarity_threshold = step_custom_config.get(
                "similarity_threshold", custom_options.get("similarity_threshold", 0.6)
            )
            if isinstance(fibo_domains, str):
                # If it's a string from the frontend, split by comma
                fibo_domains = [
                    domain.strip()
                    for domain in fibo_domains.split(",")
                    if domain.strip()
                ]
            elif not isinstance(fibo_domains, list):
                fibo_domains = []

            config = {
                **base_config,
                "mapping_confidence_threshold": step_custom_config.get(
                    "mapping_confidence_threshold", 0.7
                ),
                "create_unmapped": create_unmapped,
                "batch_size": batch_size,
                "fuzzy_matching": fuzzy_matching,
                "similarity_threshold": similarity_threshold,
                "domains": fibo_domains,
            }

        elif step_type == "knowledge_graph_writer":
            config = {
                **base_config,
                "batch_size": step_custom_config.get("batch_size", 100),
                "create_unmapped": step_custom_config.get(
                    "create_unmapped", True
                ),
                "sync_to_neo4j": custom_options.get("sync_to_neo4j", True),
                "track_provenance": step_custom_config.get("track_provenance", True),
            }

        elif step_type == "data_profiling":
            config = {
                **base_config,
                "profile_columns": step_custom_config.get("profile_columns", True),
                "sample_size": step_custom_config.get("sample_size", 10000),
            }

        else:
            config = base_config

        print(f"Generated config for {step_type}: {config}")
        return config

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
            "data_transformation": "Transform Data",
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
