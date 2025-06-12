import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.nlp.embeddings import get_embedding_service
from app.nlp.entity_extraction import EntityExtractionService
from app.nlp.knowledge_extraction import KnowledgeExtractionService
from app.nlp.ontogpt import OntoGPTService
from app.nlp.text_chunking import TextChunker
from app.schemas.pipeline_step import PipelineStepType
from app.tasks.ingestion import (ingest_api_data, ingest_database_data,
                                 ingest_file)
from app.tasks.transformation import (enrich_entities_with_embeddings,
                                      sync_entities_to_neo4j,
                                      sync_relationships_to_neo4j)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    """Exception raised when pipeline step execution fails"""

    pass


class BaseStepExecutor:
    """Base class for step executors"""

    def __init__(self, step_config: Dict[str, Any], step_metadata: Dict[str, Any]):
        self.config = step_config
        self.metadata = step_metadata
        self.step_id = step_metadata.get("step_id")
        self.step_name = step_metadata.get("step_name", "Unknown")

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the step and return output data"""
        raise NotImplementedError

    def _track_provenance(
        self, data: Any, source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track provenance information for data"""
        return {
            "data": data,
            "provenance": {
                "step_id": self.step_id,
                "step_name": self.step_name,
                "source": source or "pipeline_step",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trust_score": self.config.get("trust_score", 0.5),
            },
        }

    def _handle_incremental(self, data: Any) -> Tuple[Any, Dict[str, Any]]:
        """Handle incremental processing"""
        incremental_config = self.config.get("incremental_config", {})

        if not incremental_config.get("enabled", False):
            return data, {}

        checkpoint_field = incremental_config.get("checkpoint_field")
        last_value = incremental_config.get("checkpoint_value")

        # Filter data based on checkpoint
        if checkpoint_field and last_value and isinstance(data, list):
            filtered_data = [
                item for item in data if item.get(checkpoint_field, "") > last_value
            ]

            # Update checkpoint value
            new_checkpoint = None
            if filtered_data:
                new_checkpoint = max(
                    item.get(checkpoint_field)
                    for item in filtered_data
                    if item.get(checkpoint_field)
                )

            return filtered_data, {"new_checkpoint": new_checkpoint}

        return data, {}


class FileIngestionExecutor(BaseStepExecutor):
    """Executor for file ingestion"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:

            from app.services.file_upload import UploadService

            upload_service = UploadService()

            datasource_id = self.config.get("datasource_id", [])
            encoding = self.config.get("encoding", "utf-8")
            extract_metadata = self.config.get("extract_metadata", True)

            logger.info(
                f"Starting file ingestion for data source {datasource_id} with encoding {encoding}"
            )

            file_uploads = await upload_service.get_file_uploads(
                data_source_id=datasource_id
            )

            logger.info(
                f"Retrieved {len(file_uploads.data)} file uploads for data source {datasource_id}"
            )

            processed_files = []

            for file in file_uploads.data:
                try:
                    # Use existing ingestion function
                    file_record = await ingest_file(
                        file_id=file["id"],
                        file_name=file["file_name"],
                        datasource_id=UUID(self.config.get("datasource_id")),
                    )

                    if not file_record:
                        logger.error(
                            f"Failed to ingest file {file['file_name']}: No file record returned"
                        )
                        continue

                    logger.info(
                        f"Ingested file {file['file_name']} with ID {file_record["text_content"]}"
                    )

                    if file_record:
                        processed_files.append(
                            self._track_provenance(file_record, file["storage_path"])
                        )

                except Exception as e:
                    logger.error(f"Error ingesting file {file["storage_path"]}: {e}")
                    continue

            return {
                "files": processed_files,
                "total_files": len(processed_files),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "file_ingestion",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"File ingestion execution failed: {e}")


class ApiIngestionExecutor(BaseStepExecutor):
    """Executor for API data ingestion"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            api_url = self.config.get("url")
            auth_params = self.config.get("auth_config", {})
            query_params = self.config.get("params", {})
            headers = self.config.get("headers", {})
            response_format = self.config.get("response_format", "json")

            # Use existing ingestion function
            api_record = await ingest_api_data(
                api_url=api_url,
                data_format=response_format,
                datasource_id=UUID(self.config.get("datasource_id")),
                auth_params=auth_params,
                query_params=query_params,
                headers=headers,
                process_immediately=False,
            )

            if not api_record:
                raise PipelineExecutionError("API ingestion failed")

            # Handle incremental processing
            filtered_data, checkpoint_info = self._handle_incremental(api_record)

            result = self._track_provenance(filtered_data, api_url)

            if checkpoint_info:
                result["checkpoint_info"] = checkpoint_info

            return {
                "api_response": result,
                "record_count": 1,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "api_ingestion",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"API ingestion execution failed: {e}")


class DatabaseIngestionExecutor(BaseStepExecutor):
    """Executor for database data ingestion"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            connection_string = self.config.get("connection_string")
            query = self.config.get("query")
            output_format = self.config.get("output_format", "json")

            # Use existing ingestion function
            db_record = await ingest_database_data(
                connection_string=connection_string,
                query=query,
                datasource_id=UUID(self.config.get("datasource_id")),
                output_format=output_format,
                process_immediately=False,
            )

            if not db_record:
                raise PipelineExecutionError("Database ingestion failed")

            result = self._track_provenance(db_record, connection_string)

            return {
                "database_result": result,
                "record_count": db_record.get("metadata", {}).get("row_count", 0),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "database_ingestion",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Database ingestion execution failed: {e}")


class TextChunkingExecutor(BaseStepExecutor):
    """Executor for text chunking"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            text_chunker = TextChunker()
            chunk_size = self.config.get("chunk_size", 1000)
            chunk_overlap = self.config.get("chunk_overlap", 200)
            chunking_strategy = self.config.get("chunking_strategy", "recursive")

            # Extract text data from input
            text_data = self._extract_text_from_input(input_data)

            chunked_data = []

            for text_item in text_data:
                text_content: str = text_item.get("content", "")

                if chunking_strategy == "structured":
                    # Handle structured data
                    if isinstance(text_content, (dict, list)):
                        chunks = text_chunker.text_chunk(text_content, chunk_size)
                    else:
                        chunks = text_chunker.text_chunk(text_content, chunk_size, chunk_overlap)
                else:
                    # Default text chunking
                    chunks = text_chunker.text_chunk(text_content, chunk_size, chunk_overlap)

                for i, chunk in enumerate(chunks):
                    chunked_item = {
                        "chunk_id": f"{text_item.get('source', 'unknown')}_{i}",
                        "content": chunk,
                        "chunk_index": i,
                        "source": text_item.get("source"),
                        "original_provenance": text_item.get("provenance", {}),
                    }
                    chunked_data.append(self._track_provenance(chunked_item))

            return {
                "chunks": chunked_data,
                "total_chunks": len(chunked_data),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "text_chunking",
                    "chunking_strategy": chunking_strategy,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Text chunking execution failed: {e}")

    def _extract_text_from_input(
        self, input_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract text content from various input formats"""
        text_data = []

        # Handle file ingestion output
        if "files" in input_data:
            for file_data in input_data["files"]:
                if isinstance(file_data, dict) and "data" in file_data:
                    # Read file content if needed
                    file_info = file_data["data"]
                    text_data.append(
                        {
                            "content": str(
                                file_info["text_content"]
                            ),  # Convert to string representation
                            "source": file_info.get("file_name", "unknown"),
                            "provenance": file_data.get("provenance", {}),
                        }
                    )

        # Handle API ingestion output
        elif "api_response" in input_data:
            api_data = input_data["api_response"]
            if isinstance(api_data, dict) and "data" in api_data:
                content = str(api_data["data"])
                text_data.append(
                    {
                        "content": content,
                        "source": "api",
                        "provenance": api_data.get("provenance", {}),
                    }
                )

        # Handle database ingestion output
        elif "database_result" in input_data:
            db_data = input_data["database_result"]
            if isinstance(db_data, dict) and "data" in db_data:
                content = str(db_data["data"])
                text_data.append(
                    {
                        "content": content,
                        "source": "database",
                        "provenance": db_data.get("provenance", {}),
                    }
                )

        return text_data


class DataCleanerExecutor(BaseStepExecutor):
    """Executor for data cleaning"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            cleaning_rules = self.config.get("cleaning_rules", {})
            remove_duplicates = cleaning_rules.get("remove_duplicates", True)
            normalize_text = cleaning_rules.get("normalize_text", True)
            remove_empty = cleaning_rules.get("remove_empty", True)
            custom_rules = cleaning_rules.get("custom_rules", [])

            # Extract data from input
            data_to_clean = self._extract_data_for_cleaning(input_data)

            cleaning_stats = {
                "original_count": len(data_to_clean),
                "duplicates_removed": 0,
                "empty_values_removed": 0,
                "normalization_applied": 0,
                "custom_rules_applied": 0,
            }

            cleaned_data = []

            # Step 1: Remove duplicates
            if remove_duplicates:
                seen = set()
                for item in data_to_clean:
                    item_key = self._generate_item_key(item)
                    if item_key not in seen:
                        seen.add(item_key)
                        cleaned_data.append(item)
                    else:
                        cleaning_stats["duplicates_removed"] += 1
                data_to_clean = cleaned_data

            # Step 2: Remove empty values
            if remove_empty:
                original_count = len(data_to_clean)
                data_to_clean = [
                    item for item in data_to_clean if self._is_not_empty(item)
                ]
                cleaning_stats["empty_values_removed"] = original_count - len(
                    data_to_clean
                )

            # Step 3: Normalize text
            if normalize_text:
                for item in data_to_clean:
                    if self._normalize_item_text(item):
                        cleaning_stats["normalization_applied"] += 1

            # Step 4: Apply custom rules
            for rule in custom_rules:
                rule_type = rule.get("type")
                if rule_type == "regex_replace":
                    pattern = rule.get("pattern")
                    replacement = rule.get("replacement", "")
                    for item in data_to_clean:
                        if self._apply_regex_rule(item, pattern, replacement):
                            cleaning_stats["custom_rules_applied"] += 1

                elif rule_type == "value_mapping":
                    mapping = rule.get("mapping", {})
                    for item in data_to_clean:
                        if self._apply_value_mapping(item, mapping):
                            cleaning_stats["custom_rules_applied"] += 1

            cleaning_stats["final_count"] = len(data_to_clean)

            return {
                "cleaned_data": self._track_provenance(data_to_clean),
                "cleaning_stats": cleaning_stats,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "data_cleaner",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Data cleaner execution failed: {e}")

    def _extract_data_for_cleaning(
        self, input_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract data that needs cleaning from various input formats"""
        data_to_clean = []

        # Handle chunks output
        if "chunks" in input_data:
            for chunk in input_data["chunks"]:
                if isinstance(chunk, dict) and "data" in chunk:
                    data_to_clean.append(chunk["data"])

        # Handle file ingestion output
        elif "files" in input_data:
            for file_data in input_data["files"]:
                if isinstance(file_data, dict) and "data" in file_data:
                    data_to_clean.append(file_data["data"])

        # Handle API/database output
        elif any(key in input_data for key in ["api_response", "database_result"]):
            for key in ["api_response", "database_result"]:
                if key in input_data:
                    item = input_data[key]
                    if isinstance(item, dict) and "data" in item:
                        data_to_clean.append(item["data"])

        # Fallback: treat input as data to clean
        else:
            data_to_clean = [input_data]

        return data_to_clean

    def _generate_item_key(self, item: Dict[str, Any]) -> str:
        """Generate a unique key for duplicate detection"""
        if isinstance(item, dict):
            # Use content or text as primary identifier
            content = item.get("content") or item.get("text") or str(item)
            return hash(
                content.strip().lower() if isinstance(content, str) else str(content)
            )
        return hash(str(item))

    def _is_not_empty(self, item: Dict[str, Any]) -> bool:
        """Check if item is not empty"""
        if not item:
            return False

        if isinstance(item, dict):
            content = item.get("content") or item.get("text")
            if content:
                return bool(str(content).strip())
            # Check if dict has meaningful values
            return any(v for v in item.values() if v)

        return bool(str(item).strip())

    def _normalize_item_text(self, item: Dict[str, Any]) -> bool:
        """Normalize text content in item"""
        normalized = False

        if isinstance(item, dict):
            for key in ["content", "text", "entity_text"]:
                if key in item and isinstance(item[key], str):
                    original = item[key]
                    # Normalize whitespace
                    normalized_text = re.sub(r"\s+", " ", original.strip())
                    # Remove special characters (optional)
                    normalized_text = re.sub(
                        r"[^\w\s\u00C0-\u024F\u1E00-\u1EFF]", "", normalized_text
                    )

                    if normalized_text != original:
                        item[key] = normalized_text
                        normalized = True

        return normalized

    def _apply_regex_rule(
        self, item: Dict[str, Any], pattern: str, replacement: str
    ) -> bool:
        """Apply regex replacement rule"""
        applied = False

        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, str):
                    new_value = re.sub(pattern, replacement, value)
                    if new_value != value:
                        item[key] = new_value
                        applied = True

        return applied

    def _apply_value_mapping(
        self, item: Dict[str, Any], mapping: Dict[str, str]
    ) -> bool:
        """Apply value mapping rule"""
        applied = False

        if isinstance(item, dict):
            for key, value in item.items():
                if str(value) in mapping:
                    item[key] = mapping[str(value)]
                    applied = True

        return applied


class DataValidatorExecutor(BaseStepExecutor):
    """Executor for data validation"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validation_rules = self.config.get("validation_rules", {})
            schema_validation = validation_rules.get("schema_validation", True)
            quality_checks = validation_rules.get("quality_checks", True)
            business_rules = validation_rules.get("business_rules", [])
            required_fields = validation_rules.get("required_fields", [])

            # Extract data for validation
            data_to_validate = self._extract_data_for_validation(input_data)

            validation_results = {
                "is_valid": True,
                "validation_errors": [],
                "quality_score": 0.0,
                "field_completeness": {},
                "business_rule_violations": [],
            }

            total_items = len(data_to_validate)
            if total_items == 0:
                validation_results["quality_score"] = 1.0
                return {
                    "validation_results": self._track_provenance(validation_results),
                    "validated_data": input_data,
                    "metadata": {
                        "execution_time": datetime.now(timezone.utc).isoformat(),
                        "step_type": "data_validator",
                    },
                }

            valid_items = 0
            field_counts = {}

            for item in data_to_validate:
                item_valid = True

                # Schema validation
                if schema_validation:
                    schema_errors = self._validate_item_schema(item, required_fields)
                    if schema_errors:
                        validation_results["validation_errors"].extend(schema_errors)
                        item_valid = False

                # Quality checks
                if quality_checks:
                    quality_issues = self._check_item_quality(item)
                    if quality_issues:
                        validation_results["validation_errors"].extend(quality_issues)
                        item_valid = False

                # Business rule validation
                for rule in business_rules:
                    violations = self._check_business_rule(item, rule)
                    if violations:
                        validation_results["business_rule_violations"].extend(
                            violations
                        )
                        item_valid = False

                # Track field completeness
                if isinstance(item, dict):
                    for field in required_fields:
                        if field in field_counts:
                            field_counts[field] += 1
                        else:
                            field_counts[field] = 1

                        if field in item and item[field]:
                            if f"{field}_filled" in field_counts:
                                field_counts[f"{field}_filled"] += 1
                            else:
                                field_counts[f"{field}_filled"] = 1

                if item_valid:
                    valid_items += 1

            # Calculate quality score
            validation_results["quality_score"] = (
                valid_items / total_items if total_items > 0 else 1.0
            )
            validation_results["is_valid"] = (
                len(validation_results["validation_errors"]) == 0
            )

            # Calculate field completeness
            for field in required_fields:
                total_field = field_counts.get(field, 0)
                filled_field = field_counts.get(f"{field}_filled", 0)
                validation_results["field_completeness"][field] = {
                    "total": total_field,
                    "filled": filled_field,
                    "completeness_rate": (
                        filled_field / total_field if total_field > 0 else 0.0
                    ),
                }

            return {
                "validation_results": self._track_provenance(validation_results),
                "validated_data": input_data,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "data_validator",
                    "total_items_validated": total_items,
                    "valid_items": valid_items,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Data validator execution failed: {e}")

    def _extract_data_for_validation(
        self, input_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract data for validation from various input formats"""
        data_to_validate = []

        # Handle cleaned data output
        if "cleaned_data" in input_data:
            cleaned_data = input_data["cleaned_data"]
            if isinstance(cleaned_data, dict) and "data" in cleaned_data:
                data_to_validate = cleaned_data["data"]
            else:
                data_to_validate = [cleaned_data]

        # Handle chunks output
        elif "chunks" in input_data:
            for chunk in input_data["chunks"]:
                if isinstance(chunk, dict) and "data" in chunk:
                    data_to_validate.append(chunk["data"])

        # Fallback
        else:
            data_to_validate = [input_data]

        return data_to_validate

    def _validate_item_schema(
        self, item: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """Validate item against schema requirements"""
        errors = []

        if not isinstance(item, dict):
            errors.append(f"Item is not a dictionary: {type(item)}")
            return errors

        for field in required_fields:
            if field not in item:
                errors.append(f"Missing required field: {field}")
            elif not item[field]:
                errors.append(f"Empty value for required field: {field}")

        return errors

    def _check_item_quality(self, item: Dict[str, Any]) -> List[str]:
        """Check quality of item data"""
        issues = []

        if isinstance(item, dict):
            # Check for suspiciously short content
            for key in ["content", "text", "entity_text"]:
                if key in item and isinstance(item[key], str):
                    if len(item[key].strip()) < 3:
                        issues.append(f"Suspiciously short {key}: '{item[key]}'")

            # Check for placeholder values
            placeholder_values = ["TODO", "TBD", "N/A", "null", "undefined", ""]
            for key, value in item.items():
                if str(value).strip() in placeholder_values:
                    issues.append(f"Placeholder value in {key}: '{value}'")

            # Check for data type consistency
            if "confidence" in item:
                try:
                    confidence = float(item["confidence"])
                    if not (0.0 <= confidence <= 1.0):
                        issues.append(f"Confidence score out of range: {confidence}")
                except (ValueError, TypeError):
                    issues.append(
                        f"Invalid confidence score type: {type(item['confidence'])}"
                    )

        return issues

    def _check_business_rule(
        self, item: Dict[str, Any], rule: Dict[str, Any]
    ) -> List[str]:
        """Check business rule against item"""
        violations = []

        rule_type = rule.get("type")
        if rule_type == "min_length":
            field = rule.get("field")
            min_length = rule.get("value", 0)
            if field in item and isinstance(item[field], str):
                if len(item[field]) < min_length:
                    violations.append(
                        f"Field {field} below minimum length {min_length}"
                    )

        elif rule_type == "regex_match":
            field = rule.get("field")
            pattern = rule.get("pattern")
            if field in item and isinstance(item[field], str):
                if not re.match(pattern, item[field]):
                    violations.append(f"Field {field} does not match pattern {pattern}")

        elif rule_type == "allowed_values":
            field = rule.get("field")
            allowed_values = rule.get("values", [])
            if field in item and item[field] not in allowed_values:
                violations.append(f"Field {field} has disallowed value: {item[field]}")

        return violations


class KnowledgeMappingExecutor(BaseStepExecutor):
    """Executor for structured knowledge extraction using existing services"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            extraction_method = self.config.get("extraction_method", "ontogpt")
            # entity_types = self.config.get("entity_types", [])
            # relation_types = self.config.get("relation_types", [])
            # domain = self.config.get("domain")
            # use_validation = self.config.get("use_validation", True)

            # Initialize services

            all_entities = []
            all_relationships = []
            extraction_results = []

            # Validate extraction if requested
            validation_result = None

            return {
                "extraction_result": self._track_provenance(
                    {
                        "entities": all_entities,
                        "relationships": all_relationships,
                        "extraction_method": extraction_method,
                        "individual_results": extraction_results,
                        "validation": validation_result,
                    }
                ),
                "entity_count": len(all_entities),
                "relationship_count": len(all_relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "knowledge_mapping",
                    "extraction_method": extraction_method,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Knowledge mapping execution failed: {e}")


class OntologyEnrichmentExecutor(BaseStepExecutor):
    """Executor for ontology enrichment using Knowledge Extraction Service"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Initialize services
            knowledge_service = KnowledgeExtractionService()
            ontogpt_service = OntoGPTService()

            auto_apply_threshold = self.config.get("auto_apply_threshold", 0.8)
            user_id = self.config.get("user_id")
            enrichment_types = self.config.get(
                "enrichment_types", ["classes", "properties"]
            )

            # Extract entities and relationships from input
            entities, relationships = self._extract_entities_and_relationships(
                input_data
            )

            enrichment_results = {
                "new_concepts_suggested": 0,
                "concepts_added": 0,
                "validation_score": 0.0,
                "enrichment_details": {},
            }

            # If we have extraction result IDs, use them for enrichment
            extraction_ids = self._extract_extraction_ids(input_data)

            if extraction_ids:
                # Use batch enrichment for multiple extractions
                enrichment_result = (
                    await knowledge_service.enrich_ontology_from_extractions(
                        extraction_result_ids=extraction_ids,
                        user_id=user_id,
                        auto_apply_threshold=auto_apply_threshold,
                    )
                )

                if enrichment_result.get("success"):
                    enrichment_results = enrichment_result.get(
                        "summary", enrichment_results
                    )
                    enrichment_results["enrichment_details"] = enrichment_result

            else:
                # Use individual entity/relationship enrichment
                if entities and "classes" in enrichment_types:
                    # Suggest new classes based on entities
                    new_classes = await self._suggest_entity_classes(entities)
                    enrichment_results["suggested_classes"] = new_classes
                    enrichment_results["new_concepts_suggested"] += len(new_classes)

                if relationships and "properties" in enrichment_types:
                    # Suggest new properties based on relationships
                    new_properties = await self._suggest_relationship_properties(
                        relationships
                    )
                    enrichment_results["suggested_properties"] = new_properties
                    enrichment_results["new_concepts_suggested"] += len(new_properties)

                # Auto-apply suggestions if threshold is met
                applied_count = 0
                if enrichment_results["new_concepts_suggested"] > 0:
                    applied_count = await self._auto_apply_suggestions(
                        enrichment_results, user_id, auto_apply_threshold
                    )

                enrichment_results["concepts_added"] = applied_count

            # Validate enrichment results
            if entities or relationships:
                validation_result = (
                    await ontogpt_service.validate_extraction_against_ontology(
                        entities=entities, relationships=relationships
                    )
                )
                enrichment_results["validation_score"] = validation_result.get(
                    "overall_score", 0.0
                )

            return {
                "enrichment_result": self._track_provenance(enrichment_results),
                "enriched_entities": entities,
                "enriched_relationships": relationships,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "ontology_enrichment",
                    "auto_apply_threshold": auto_apply_threshold,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Ontology enrichment execution failed: {e}")

    def _extract_entities_and_relationships(
        self, input_data: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Extract entities and relationships from input data"""
        entities = []
        relationships = []

        # Handle extraction result output
        if "extraction_result" in input_data:
            extraction_data = input_data["extraction_result"]
            if "data" in extraction_data:
                entities.extend(extraction_data["data"].get("entities", []))
                relationships.extend(extraction_data["data"].get("relationships", []))

        # Handle mapping result output
        elif "mapping_result" in input_data:
            mapping_data = input_data["mapping_result"]
            if "data" in mapping_data:
                entities.extend(mapping_data["data"].get("entities", []))
                relationships.extend(mapping_data["data"].get("relationships", []))

        return entities, relationships

    def _extract_extraction_ids(self, input_data: Dict[str, Any]) -> List[int]:
        """Extract extraction result IDs from input data"""
        extraction_ids = []

        # Look for extraction IDs in various places
        if "extraction_result" in input_data:
            extraction_data = input_data["extraction_result"]
            if "data" in extraction_data:
                individual_results = extraction_data["data"].get(
                    "individual_results", []
                )
                for result in individual_results:
                    if result.get("extraction_id"):
                        extraction_ids.append(result["extraction_id"])

        return extraction_ids

    async def _suggest_entity_classes(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest new ontology classes based on entities"""
        suggestions = []

        # Group entities by type to find patterns
        entity_types = {}
        for entity in entities:
            entity_type = entity.get("entity_type", "Unknown")
            if entity_type not in entity_types:
                entity_types[entity_type] = []
            entity_types[entity_type].append(entity)

        # Suggest classes for unmapped entity types
        for entity_type, entity_list in entity_types.items():
            unmapped_count = len(
                [e for e in entity_list if not e.get("is_mapped", False)]
            )
            if (
                unmapped_count > 2
            ):  # Suggest if we have multiple unmapped entities of this type
                suggestions.append(
                    {
                        "suggested_class": entity_type,
                        "description": f"Class for {entity_type} entities",
                        "supporting_entities": len(entity_list),
                        "confidence": min(0.9, unmapped_count / len(entity_list)),
                        "examples": [e.get("text", "") for e in entity_list[:3]],
                    }
                )

        return suggestions

    async def _suggest_relationship_properties(
        self, relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest new ontology properties based on relationships"""
        suggestions = []

        # Group relationships by type
        relationship_types = {}
        for relationship in relationships:
            rel_type = relationship.get("relationship_type", "Unknown")
            if rel_type not in relationship_types:
                relationship_types[rel_type] = []
            relationship_types[rel_type].append(relationship)

        # Suggest properties for unmapped relationship types
        for rel_type, rel_list in relationship_types.items():
            unmapped_count = len([r for r in rel_list if not r.get("is_mapped", False)])
            if (
                unmapped_count > 1
            ):  # Suggest if we have multiple unmapped relationships of this type
                suggestions.append(
                    {
                        "suggested_property": rel_type,
                        "description": f"Property for {rel_type} relationships",
                        "supporting_relationships": len(rel_list),
                        "confidence": min(0.9, unmapped_count / len(rel_list)),
                        "examples": [
                            f"{r.get('source_entity', '')} -> {r.get('target_entity', '')}"
                            for r in rel_list[:3]
                        ],
                    }
                )

        return suggestions

    async def _auto_apply_suggestions(
        self, enrichment_results: Dict[str, Any], user_id: str, threshold: float
    ) -> int:
        """Auto-apply suggestions that meet the confidence threshold"""
        applied_count = 0

        # Apply class suggestions
        for suggestion in enrichment_results.get("suggested_classes", []):
            if suggestion.get("confidence", 0) >= threshold:
                # Here you would call the ontology service to actually add the class
                # For now, we'll just count it as applied
                applied_count += 1

        # Apply property suggestions
        for suggestion in enrichment_results.get("suggested_properties", []):
            if suggestion.get("confidence", 0) >= threshold:
                # Here you would call the ontology service to actually add the property
                # For now, we'll just count it as applied
                applied_count += 1

        return applied_count


class EntityResolutionExecutor(BaseStepExecutor):
    """Executor for entity resolution using existing logic"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            resolution_strategy = self.config.get("resolution_strategy", "fuzzy_match")
            similarity_threshold = self.config.get("similarity_threshold", 0.8)
            clustering_method = self.config.get("clustering_method", "single_linkage")

            # Extract entities from input
            entities = self._extract_entities_from_input(input_data)

            if not entities:
                return {
                    "resolution_result": self._track_provenance(
                        {
                            "resolved_entities": [],
                            "entity_clusters": [],
                            "resolution_stats": {
                                "input_entities": 0,
                                "resolved_entities": 0,
                                "clusters_formed": 0,
                                "resolution_strategy": resolution_strategy,
                            },
                        }
                    ),
                    "input_entity_count": 0,
                    "resolved_entity_count": 0,
                    "cluster_count": 0,
                    "metadata": {
                        "execution_time": datetime.now(timezone.utc).isoformat(),
                        "step_type": "entity_resolution",
                    },
                }

            # Perform entity resolution
            resolved_entities, entity_clusters = await self._resolve_entities(
                entities, resolution_strategy, similarity_threshold, clustering_method
            )

            result = self._track_provenance(
                {
                    "resolved_entities": resolved_entities,
                    "entity_clusters": entity_clusters,
                    "resolution_stats": {
                        "input_entities": len(entities),
                        "resolved_entities": len(resolved_entities),
                        "clusters_formed": len(entity_clusters),
                        "resolution_strategy": resolution_strategy,
                        "similarity_threshold": similarity_threshold,
                    },
                }
            )

            return {
                "resolution_result": result,
                "input_entity_count": len(entities),
                "resolved_entity_count": len(resolved_entities),
                "cluster_count": len(entity_clusters),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "entity_resolution",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Entity resolution execution failed: {e}")

    def _extract_entities_from_input(
        self, input_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract entities from various input formats"""
        entities = []

        # Handle extraction result output
        if "extraction_result" in input_data:
            extraction_data = input_data["extraction_result"]
            if "data" in extraction_data:
                entities.extend(extraction_data["data"].get("entities", []))

        # Handle enrichment result output
        elif "enrichment_result" in input_data:
            entities.extend(input_data.get("enriched_entities", []))

        return entities

    async def _resolve_entities(
        self,
        entities: List[Dict[str, Any]],
        strategy: str,
        threshold: float,
        clustering_method: str,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Resolve entities using the specified strategy"""

        if strategy == "fuzzy_match":
            return await self._fuzzy_match_resolution(
                entities, threshold, clustering_method
            )
        elif strategy == "exact_match":
            return await self._exact_match_resolution(entities)
        elif strategy == "semantic_similarity":
            return await self._semantic_similarity_resolution(entities, threshold)
        else:
            # Default to fuzzy match
            return await self._fuzzy_match_resolution(
                entities, threshold, clustering_method
            )

    async def _fuzzy_match_resolution(
        self, entities: List[Dict[str, Any]], threshold: float, clustering_method: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Resolve entities using fuzzy string matching"""
        from difflib import SequenceMatcher

        # Calculate similarity matrix
        n = len(entities)
        similarity_matrix = [[0.0 for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(i + 1, n):
                text1 = (
                    entities[i].get("text", entities[i].get("entity_text", "")).lower()
                )
                text2 = (
                    entities[j].get("text", entities[j].get("entity_text", "")).lower()
                )

                # Check if entities are of the same type
                type1 = entities[i].get("entity_type", "")
                type2 = entities[j].get("entity_type", "")

                if type1 == type2:
                    similarity = SequenceMatcher(None, text1, text2).ratio()
                    similarity_matrix[i][j] = similarity
                    similarity_matrix[j][i] = similarity

        # Form clusters based on similarity threshold
        clusters = []
        assigned = set()

        for i in range(n):
            if i in assigned:
                continue

            cluster = [i]
            assigned.add(i)

            for j in range(i + 1, n):
                if j not in assigned and similarity_matrix[i][j] >= threshold:
                    cluster.append(j)
                    assigned.add(j)

            if len(cluster) > 1:
                clusters.append(cluster)

        # Create resolved entities and cluster information
        resolved_entities = []
        entity_clusters = []

        # Process clusters
        for cluster_indices in clusters:
            cluster_entities = [entities[i] for i in cluster_indices]

            # Select the entity with highest confidence as the canonical one
            canonical_entity = max(
                cluster_entities, key=lambda e: e.get("confidence", 0)
            )
            canonical_entity["cluster_id"] = len(entity_clusters)
            canonical_entity["cluster_size"] = len(cluster_entities)

            resolved_entities.append(canonical_entity)

            entity_clusters.append(
                {
                    "cluster_id": len(entity_clusters),
                    "canonical_entity": canonical_entity,
                    "cluster_entities": cluster_entities,
                    "cluster_size": len(cluster_entities),
                    "avg_similarity": sum(
                        [
                            similarity_matrix[cluster_indices[i]][cluster_indices[j]]
                            for i in range(len(cluster_indices))
                            for j in range(i + 1, len(cluster_indices))
                        ]
                    )
                    / max(1, len(cluster_indices) * (len(cluster_indices) - 1) // 2),
                }
            )

        # Add unclustered entities
        for i, entity in enumerate(entities):
            if not any(i in cluster for cluster in clusters):
                entity["cluster_id"] = None
                entity["cluster_size"] = 1
                resolved_entities.append(entity)

        return resolved_entities, entity_clusters

    async def _exact_match_resolution(
        self, entities: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Resolve entities using exact text matching"""
        entity_map = {}
        clusters = []

        for entity in entities:
            text = entity.get("text", entity.get("entity_text", "")).lower().strip()
            entity_type = entity.get("entity_type", "")
            key = f"{text}_{entity_type}"

            if key in entity_map:
                entity_map[key].append(entity)
            else:
                entity_map[key] = [entity]

        resolved_entities = []
        for key, entity_list in entity_map.items():
            if len(entity_list) > 1:
                # Create cluster
                canonical_entity = max(
                    entity_list, key=lambda e: e.get("confidence", 0)
                )
                canonical_entity["cluster_id"] = len(clusters)
                canonical_entity["cluster_size"] = len(entity_list)

                clusters.append(
                    {
                        "cluster_id": len(clusters),
                        "canonical_entity": canonical_entity,
                        "cluster_entities": entity_list,
                        "cluster_size": len(entity_list),
                        "match_type": "exact",
                    }
                )

                resolved_entities.append(canonical_entity)
            else:
                # Single entity
                entity_list[0]["cluster_id"] = None
                entity_list[0]["cluster_size"] = 1
                resolved_entities.append(entity_list[0])

        return resolved_entities, clusters

    async def _semantic_similarity_resolution(
        self, entities: List[Dict[str, Any]], threshold: float
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Resolve entities using semantic similarity (if embeddings are available)"""
        try:
            # Get embedding service
            embedding_service = get_embedding_service()

            # Get embeddings for all entities
            entity_texts = [e.get("text", e.get("entity_text", "")) for e in entities]
            embeddings = await embedding_service.get_embeddings(entity_texts)

            # Calculate cosine similarity
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity

            similarity_matrix = cosine_similarity(embeddings)

            # Form clusters based on similarity threshold
            n = len(entities)
            clusters = []
            assigned = set()

            for i in range(n):
                if i in assigned:
                    continue

                cluster = [i]
                assigned.add(i)

                for j in range(i + 1, n):
                    if (
                        j not in assigned
                        and similarity_matrix[i][j] >= threshold
                        and entities[i].get("entity_type")
                        == entities[j].get("entity_type")
                    ):
                        cluster.append(j)
                        assigned.add(j)

                if len(cluster) > 1:
                    clusters.append(cluster)

            # Create resolved entities and clusters (similar to fuzzy match logic)
            resolved_entities = []
            entity_clusters = []

            for cluster_indices in clusters:
                cluster_entities = [entities[i] for i in cluster_indices]
                canonical_entity = max(
                    cluster_entities, key=lambda e: e.get("confidence", 0)
                )
                canonical_entity["cluster_id"] = len(entity_clusters)
                canonical_entity["cluster_size"] = len(cluster_entities)

                resolved_entities.append(canonical_entity)
                entity_clusters.append(
                    {
                        "cluster_id": len(entity_clusters),
                        "canonical_entity": canonical_entity,
                        "cluster_entities": cluster_entities,
                        "cluster_size": len(cluster_entities),
                        "avg_similarity": (
                            np.mean(
                                [
                                    similarity_matrix[cluster_indices[i]][
                                        cluster_indices[j]
                                    ]
                                    for i in range(len(cluster_indices))
                                    for j in range(i + 1, len(cluster_indices))
                                ]
                            )
                            if len(cluster_indices) > 1
                            else 1.0
                        ),
                    }
                )

            # Add unclustered entities
            for i, entity in enumerate(entities):
                if not any(i in cluster for cluster in clusters):
                    entity["cluster_id"] = None
                    entity["cluster_size"] = 1
                    resolved_entities.append(entity)

            return resolved_entities, entity_clusters

        except Exception as e:
            logger.warning(
                f"Semantic similarity resolution failed, falling back to fuzzy match: {e}"
            )
            return await self._fuzzy_match_resolution(
                entities, threshold, "single_linkage"
            )


class EntityFusionExecutor(BaseStepExecutor):
    """Executor for entity fusion"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            fusion_strategy = self.config.get("fusion_strategy", "most_recent")
            preserve_provenance = self.config.get("preserve_provenance", True)
            conflict_resolution = self.config.get(
                "conflict_resolution", "highest_confidence"
            )

            # Extract resolved entities from input
            resolved_entities, entity_clusters = self._extract_resolution_data(
                input_data
            )

            # Perform entity fusion
            fused_entities = await self._fuse_entities(
                resolved_entities,
                entity_clusters,
                fusion_strategy,
                preserve_provenance,
                conflict_resolution,
            )

            return {
                "fusion_result": self._track_provenance(
                    {
                        "fused_entities": fused_entities,
                        "fusion_stats": {
                            "input_entities": len(resolved_entities),
                            "input_clusters": len(entity_clusters),
                            "fused_entities": len(fused_entities),
                            "fusion_strategy": fusion_strategy,
                        },
                    }
                ),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "entity_fusion",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Entity fusion execution failed: {e}")

    def _extract_resolution_data(
        self, input_data: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Extract resolved entities and clusters from input"""
        resolved_entities = []
        entity_clusters = []

        if "resolution_result" in input_data:
            resolution_data = input_data["resolution_result"]
            if "data" in resolution_data:
                resolved_entities = resolution_data["data"].get("resolved_entities", [])
                entity_clusters = resolution_data["data"].get("entity_clusters", [])

        return resolved_entities, entity_clusters

    async def _fuse_entities(
        self,
        resolved_entities: List[Dict[str, Any]],
        entity_clusters: List[Dict[str, Any]],
        fusion_strategy: str,
        preserve_provenance: bool,
        conflict_resolution: str,
    ) -> List[Dict[str, Any]]:
        """Fuse entities based on clusters and strategy"""
        fused_entities = []

        # Process clustered entities
        for cluster in entity_clusters:
            cluster_entities = cluster.get("cluster_entities", [])
            if not cluster_entities:
                continue

            # Fuse entities in the cluster
            fused_entity = await self._fuse_entity_cluster(
                cluster_entities,
                fusion_strategy,
                preserve_provenance,
                conflict_resolution,
            )

            # Add cluster metadata
            fused_entity["is_fused"] = True
            fused_entity["source_entities_count"] = len(cluster_entities)
            fused_entity["cluster_id"] = cluster.get("cluster_id")

            fused_entities.append(fused_entity)

        # Add standalone entities (not in clusters)
        for entity in resolved_entities:
            if entity.get("cluster_id") is None:
                entity["is_fused"] = False
                entity["source_entities_count"] = 1
                fused_entities.append(entity)

        return fused_entities

    async def _fuse_entity_cluster(
        self,
        cluster_entities: List[Dict[str, Any]],
        fusion_strategy: str,
        preserve_provenance: bool,
        conflict_resolution: str,
    ) -> Dict[str, Any]:
        """Fuse a cluster of entities into a single entity"""
        if not cluster_entities:
            return {}

        if len(cluster_entities) == 1:
            return cluster_entities[0]

        # Start with the base entity (highest confidence or most recent)
        if fusion_strategy == "highest_confidence":
            base_entity = max(cluster_entities, key=lambda e: e.get("confidence", 0))
        elif fusion_strategy == "most_recent":
            base_entity = max(
                cluster_entities, key=lambda e: e.get("timestamp", "1970-01-01")
            )
        else:
            base_entity = cluster_entities[0]

        fused_entity = base_entity.copy()

        # Merge properties from all entities
        all_properties = {}
        provenance_info = []

        for entity in cluster_entities:
            # Collect properties
            entity_properties = entity.get("properties", {})
            for key, value in entity_properties.items():
                if key not in all_properties:
                    all_properties[key] = []
                all_properties[key].append(
                    {
                        "value": value,
                        "source_entity": entity.get("id"),
                        "confidence": entity.get("confidence", 0),
                        "timestamp": entity.get("timestamp"),
                    }
                )

            # Collect provenance
            if preserve_provenance:
                provenance_info.append(
                    {
                        "entity_id": entity.get("id"),
                        "text": entity.get("text", entity.get("entity_text", "")),
                        "confidence": entity.get("confidence", 0),
                        "source": entity.get("source"),
                        "provenance": entity.get("provenance", {}),
                    }
                )

        # Resolve conflicts in properties
        resolved_properties = {}
        for key, value_list in all_properties.items():
            if len(value_list) == 1:
                resolved_properties[key] = value_list[0]["value"]
            else:
                # Apply conflict resolution strategy
                if conflict_resolution == "highest_confidence":
                    best_value = max(value_list, key=lambda v: v["confidence"])
                    resolved_properties[key] = best_value["value"]
                elif conflict_resolution == "most_recent":
                    best_value = max(
                        value_list, key=lambda v: v.get("timestamp", "1970-01-01")
                    )
                    resolved_properties[key] = best_value["value"]
                elif conflict_resolution == "merge_all":
                    resolved_properties[key] = [v["value"] for v in value_list]
                else:
                    # Default to first value
                    resolved_properties[key] = value_list[0]["value"]

        # Update fused entity
        fused_entity["properties"] = resolved_properties

        if preserve_provenance:
            fused_entity["fusion_provenance"] = provenance_info

        # Calculate combined confidence
        confidences = [e.get("confidence", 0) for e in cluster_entities]
        fused_entity["confidence"] = sum(confidences) / len(confidences)

        return fused_entity


class KgCompletionExecutor(BaseStepExecutor):
    """Executor for knowledge graph completion using Knowledge Extraction Service"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Initialize services
            knowledge_service = KnowledgeExtractionService()

            completion_types = self.config.get(
                "completion_types", ["missing_entities", "missing_relationships"]
            )
            auto_apply_suggestions = self.config.get("auto_apply_suggestions", False)
            confidence_threshold = self.config.get("confidence_threshold", 0.8)
            user_id = self.config.get("user_id")

            # Extract extraction result ID if available
            extraction_result_id = self._extract_extraction_result_id(input_data)

            if not extraction_result_id:
                # Create a temporary extraction result for completion
                extraction_result_id = await self._create_temporary_extraction_result(
                    input_data
                )

            if extraction_result_id:
                # Use the knowledge service for completion
                completion_result = await knowledge_service.complete_knowledge_graph(
                    extraction_result_id=extraction_result_id,
                    user_id=user_id,
                    auto_apply_suggestions=auto_apply_suggestions,
                )

                if completion_result.get("success"):
                    return {
                        "completion_result": self._track_provenance(completion_result),
                        "metadata": {
                            "execution_time": datetime.now(timezone.utc).isoformat(),
                            "step_type": "kg_completion",
                            "extraction_result_id": extraction_result_id,
                        },
                    }

            # Fallback to manual completion suggestions
            completion_suggestions = await self._generate_completion_suggestions(
                input_data, completion_types, confidence_threshold
            )

            return {
                "completion_result": self._track_provenance(
                    {
                        "suggestions": completion_suggestions,
                        "auto_applied": False,
                        "completion_method": "manual_suggestions",
                    }
                ),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "kg_completion",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"KG completion execution failed: {e}")

    def _extract_extraction_result_id(
        self, input_data: Dict[str, Any]
    ) -> Optional[int]:
        """Extract extraction result ID from input data"""
        # Check various possible locations for extraction ID
        if "fusion_result" in input_data:
            fusion_data = input_data["fusion_result"]
            if "data" in fusion_data:
                return fusion_data["data"].get("extraction_result_id")

        if "enrichment_result" in input_data:
            enrichment_data = input_data["enrichment_result"]
            if "data" in enrichment_data:
                return enrichment_data["data"].get("extraction_result_id")

        # Look for individual extraction results
        if "extraction_result" in input_data:
            extraction_data = input_data["extraction_result"]
            if "data" in extraction_data:
                individual_results = extraction_data["data"].get(
                    "individual_results", []
                )
                if individual_results and individual_results[0].get("extraction_id"):
                    return individual_results[0]["extraction_id"]

        return None

    async def _create_temporary_extraction_result(
        self, input_data: Dict[str, Any]
    ) -> Optional[int]:
        """Create a temporary extraction result for completion"""
        try:
            # This is a simplified version - in a real implementation,
            # you would save the current entities and relationships to create
            # a proper extraction result
            return None  # For now, return None to use fallback method
        except Exception as e:
            logger.error(f"Error creating temporary extraction result: {e}")
            return None

    async def _generate_completion_suggestions(
        self,
        input_data: Dict[str, Any],
        completion_types: List[str],
        confidence_threshold: float,
    ) -> Dict[str, Any]:
        """Generate completion suggestions manually"""
        suggestions = {
            "missing_entities": [],
            "missing_relationships": [],
            "completion_stats": {},
        }

        # Extract current entities and relationships
        entities, relationships = (
            self._extract_entities_and_relationships_for_completion(input_data)
        )

        if "missing_entities" in completion_types:
            missing_entities = await self._suggest_missing_entities(
                entities, relationships
            )
            suggestions["missing_entities"] = missing_entities

        if "missing_relationships" in completion_types:
            missing_relationships = await self._suggest_missing_relationships(
                entities, relationships
            )
            suggestions["missing_relationships"] = missing_relationships

        suggestions["completion_stats"] = {
            "current_entities": len(entities),
            "current_relationships": len(relationships),
            "suggested_entities": len(suggestions["missing_entities"]),
            "suggested_relationships": len(suggestions["missing_relationships"]),
        }

        return suggestions

    def _extract_entities_and_relationships_for_completion(
        self, input_data: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Extract entities and relationships for completion"""
        entities = []
        relationships = []

        # Handle fusion result output
        if "fusion_result" in input_data:
            fusion_data = input_data["fusion_result"]
            if "data" in fusion_data:
                entities.extend(fusion_data["data"].get("fused_entities", []))

        # Handle enrichment result output
        elif "enrichment_result" in input_data:
            entities.extend(input_data.get("enriched_entities", []))
            relationships.extend(input_data.get("enriched_relationships", []))

        # Handle extraction result output
        elif "extraction_result" in input_data:
            extraction_data = input_data["extraction_result"]
            if "data" in extraction_data:
                entities.extend(extraction_data["data"].get("entities", []))
                relationships.extend(extraction_data["data"].get("relationships", []))

        return entities, relationships

    async def _suggest_missing_entities(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest missing entities based on relationships"""
        suggestions = []

        # Find entities mentioned in relationships but not in entity list
        entity_texts = set(
            [e.get("text", e.get("entity_text", "")).lower() for e in entities]
        )

        for relationship in relationships:
            source_entity = relationship.get("source_entity", "").lower()
            target_entity = relationship.get("target_entity", "").lower()

            if source_entity and source_entity not in entity_texts:
                suggestions.append(
                    {
                        "suggested_text": relationship.get("source_entity"),
                        "suggested_type": "Unknown",
                        "reason": f"Referenced in relationship as source",
                        "supporting_relationship": relationship.get(
                            "relationship_type"
                        ),
                        "confidence": 0.7,
                        "priority": "medium",
                    }
                )
                entity_texts.add(source_entity)

            if target_entity and target_entity not in entity_texts:
                suggestions.append(
                    {
                        "suggested_text": relationship.get("target_entity"),
                        "suggested_type": "Unknown",
                        "reason": f"Referenced in relationship as target",
                        "supporting_relationship": relationship.get(
                            "relationship_type"
                        ),
                        "confidence": 0.7,
                        "priority": "medium",
                    }
                )
                entity_texts.add(target_entity)

        return suggestions

    async def _suggest_missing_relationships(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Suggest missing relationships based on entity patterns"""
        suggestions = []

        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.get("entity_type", "Unknown")
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # Common relationship patterns in banking domain
        relationship_patterns = [
            {
                "source_type": "Person",
                "target_type": "Bank",
                "relationship": "is_customer_of",
            },
            {
                "source_type": "Person",
                "target_type": "Account",
                "relationship": "owns_account",
            },
            {
                "source_type": "Bank",
                "target_type": "Product",
                "relationship": "offers_product",
            },
            {
                "source_type": "Person",
                "target_type": "Product",
                "relationship": "uses_product",
            },
        ]

        # Suggest relationships based on patterns
        for pattern in relationship_patterns:
            source_entities = entities_by_type.get(pattern["source_type"], [])
            target_entities = entities_by_type.get(pattern["target_type"], [])

            for source_entity in source_entities:
                for target_entity in target_entities:
                    # Check if this relationship already exists
                    existing = any(
                        r.get("source_entity", "").lower()
                        == source_entity.get("text", "").lower()
                        and r.get("target_entity", "").lower()
                        == target_entity.get("text", "").lower()
                        and r.get("relationship_type") == pattern["relationship"]
                        for r in relationships
                    )

                    if not existing:
                        suggestions.append(
                            {
                                "source_entity": source_entity.get(
                                    "text", source_entity.get("entity_text", "")
                                ),
                                "target_entity": target_entity.get(
                                    "text", target_entity.get("entity_text", "")
                                ),
                                "suggested_type": pattern["relationship"],
                                "reason": f"Common pattern in {pattern['source_type']}-{pattern['target_type']} relationships",
                                "confidence": 0.6,
                                "priority": "low",
                            }
                        )

        return suggestions


class QualityMonitoringExecutor(BaseStepExecutor):
    """Executor for quality monitoring using Knowledge Extraction Service"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Initialize services
            knowledge_service = KnowledgeExtractionService()

            metrics = self.config.get(
                "metrics", ["completeness", "consistency", "accuracy"]
            )
            quality_threshold = self.config.get("quality_threshold", 0.8)
            generate_recommendations = self.config.get("generate_recommendations", True)

            # Extract extraction result IDs for analysis
            extraction_ids = self._extract_extraction_ids_for_monitoring(input_data)

            if extraction_ids:
                # Use knowledge service for quality analysis
                quality_analysis = await knowledge_service.analyze_extraction_quality(
                    extraction_ids
                )

                if quality_analysis.get("success", True):
                    overall_quality_score = self._calculate_overall_quality_score(
                        quality_analysis
                    )

                    return {
                        "quality_result": self._track_provenance(
                            {
                                "quality_analysis": quality_analysis,
                                "overall_score": overall_quality_score,
                                "passed_threshold": overall_quality_score
                                >= quality_threshold,
                                "extraction_ids_analyzed": extraction_ids,
                            }
                        ),
                        "metadata": {
                            "execution_time": datetime.now(timezone.utc).isoformat(),
                            "step_type": "quality_monitoring",
                            "metrics_evaluated": metrics,
                        },
                    }

            # Fallback to manual quality monitoring
            quality_results = await self._perform_manual_quality_monitoring(
                input_data, metrics, quality_threshold
            )

            overall_quality_score = quality_results.get("overall_score", 0.0)

            return {
                "quality_result": self._track_provenance(
                    {
                        "quality_metrics": quality_results,
                        "overall_score": overall_quality_score,
                        "passed_threshold": overall_quality_score >= quality_threshold,
                    }
                ),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "quality_monitoring",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Quality monitoring execution failed: {e}")

    def _extract_extraction_ids_for_monitoring(
        self, input_data: Dict[str, Any]
    ) -> List[int]:
        """Extract extraction result IDs for quality monitoring"""
        extraction_ids = []

        # Look through various input data formats
        if "completion_result" in input_data:
            completion_data = input_data["completion_result"]
            if "data" in completion_data:
                extraction_id = completion_data["data"].get("extraction_result_id")
                if extraction_id:
                    extraction_ids.append(extraction_id)

        # Check other possible locations
        for key in ["fusion_result", "enrichment_result", "extraction_result"]:
            if key in input_data:
                data = input_data[key]
                if "data" in data:
                    # Look for individual results
                    individual_results = data["data"].get("individual_results", [])
                    for result in individual_results:
                        if result.get("extraction_id"):
                            extraction_ids.append(result["extraction_id"])

        return extraction_ids

    def _calculate_overall_quality_score(
        self, quality_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score from analysis results"""
        if "summary" in quality_analysis:
            summary = quality_analysis["summary"]
            mapping_coverage = summary.get("mapping_coverage", {})

            entity_mapping_percent = (
                mapping_coverage.get("entities_mapped_percent", 0) / 100
            )
            relationship_mapping_percent = (
                mapping_coverage.get("relationships_mapped_percent", 0) / 100
            )

            # Calculate confidence scores
            confidence_analysis = quality_analysis.get("confidence_analysis", {})
            entity_confidence = confidence_analysis.get("entity_confidence", {}).get(
                "mean", 0
            )
            relationship_confidence = confidence_analysis.get(
                "relationship_confidence", {}
            ).get("mean", 0)

            # Weighted average
            overall_score = (
                entity_mapping_percent * 0.3
                + relationship_mapping_percent * 0.3
                + entity_confidence * 0.2
                + relationship_confidence * 0.2
            )

            return overall_score

        return 0.0

    async def _perform_manual_quality_monitoring(
        self, input_data: Dict[str, Any], metrics: List[str], threshold: float
    ) -> Dict[str, Any]:
        """Perform manual quality monitoring when extraction IDs are not available"""
        quality_results = {
            "completeness_score": 0.0,
            "consistency_score": 0.0,
            "accuracy_score": 0.0,
            "overall_score": 0.0,
            "metric_details": {},
        }

        # Extract entities and relationships
        entities, relationships = self._extract_entities_and_relationships_for_quality(
            input_data
        )

        # Completeness analysis
        if "completeness" in metrics:
            completeness_score = await self._analyze_completeness(
                entities, relationships
            )
            quality_results["completeness_score"] = completeness_score
            quality_results["metric_details"]["completeness"] = {
                "score": completeness_score,
                "total_entities": len(entities),
                "total_relationships": len(relationships),
                "mapped_entities": len(
                    [e for e in entities if e.get("is_mapped", False)]
                ),
                "mapped_relationships": len(
                    [r for r in relationships if r.get("is_mapped", False)]
                ),
            }

        # Consistency analysis
        if "consistency" in metrics:
            consistency_score = await self._analyze_consistency(entities, relationships)
            quality_results["consistency_score"] = consistency_score
            quality_results["metric_details"]["consistency"] = {
                "score": consistency_score,
                "entity_type_consistency": self._check_entity_type_consistency(
                    entities
                ),
                "relationship_type_consistency": self._check_relationship_type_consistency(
                    relationships
                ),
            }

        # Accuracy analysis
        if "accuracy" in metrics:
            accuracy_score = await self._analyze_accuracy(entities, relationships)
            quality_results["accuracy_score"] = accuracy_score
            quality_results["metric_details"]["accuracy"] = {
                "score": accuracy_score,
                "avg_entity_confidence": sum([e.get("confidence", 0) for e in entities])
                / max(1, len(entities)),
                "avg_relationship_confidence": sum(
                    [r.get("confidence", 0) for r in relationships]
                )
                / max(1, len(relationships)),
            }

        # Calculate overall score
        scores = [
            quality_results[f"{metric}_score"]
            for metric in metrics
            if f"{metric}_score" in quality_results
        ]
        quality_results["overall_score"] = sum(scores) / max(1, len(scores))

        return quality_results

    def _extract_entities_and_relationships_for_quality(
        self, input_data: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Extract entities and relationships for quality analysis"""
        entities = []
        relationships = []

        # Handle various input formats
        if "completion_result" in input_data:
            # Extract from completion suggestions
            completion_data = input_data["completion_result"]
            if "data" in completion_data:
                suggestions = completion_data["data"].get("suggestions", {})
                entities.extend(suggestions.get("missing_entities", []))
                relationships.extend(suggestions.get("missing_relationships", []))

        elif "fusion_result" in input_data:
            fusion_data = input_data["fusion_result"]
            if "data" in fusion_data:
                entities.extend(fusion_data["data"].get("fused_entities", []))

        elif "extraction_result" in input_data:
            extraction_data = input_data["extraction_result"]
            if "data" in extraction_data:
                entities.extend(extraction_data["data"].get("entities", []))
                relationships.extend(extraction_data["data"].get("relationships", []))

        return entities, relationships

    async def _analyze_completeness(
        self, entities: List[Dict], relationships: List[Dict]
    ) -> float:
        """Analyze completeness of extracted knowledge"""
        if not entities and not relationships:
            return 0.0

        # Calculate mapping coverage
        mapped_entities = len([e for e in entities if e.get("is_mapped", False)])
        mapped_relationships = len(
            [r for r in relationships if r.get("is_mapped", False)]
        )

        total_items = len(entities) + len(relationships)
        mapped_items = mapped_entities + mapped_relationships

        mapping_coverage = mapped_items / total_items if total_items > 0 else 0.0

        # Calculate field completeness
        required_entity_fields = ["text", "entity_type", "confidence"]
        required_relationship_fields = [
            "source_entity",
            "target_entity",
            "relationship_type",
            "confidence",
        ]

        entity_completeness = 0.0
        if entities:
            entity_field_scores = []
            for field in required_entity_fields:
                filled_count = len([e for e in entities if e.get(field)])
                entity_field_scores.append(filled_count / len(entities))
            entity_completeness = sum(entity_field_scores) / len(entity_field_scores)

        relationship_completeness = 0.0
        if relationships:
            relationship_field_scores = []
            for field in required_relationship_fields:
                filled_count = len([r for r in relationships if r.get(field)])
                relationship_field_scores.append(filled_count / len(relationships))
            relationship_completeness = sum(relationship_field_scores) / len(
                relationship_field_scores
            )

        # Weighted average
        if entities and relationships:
            completeness_score = (
                mapping_coverage * 0.4
                + entity_completeness * 0.3
                + relationship_completeness * 0.3
            )
        elif entities:
            completeness_score = mapping_coverage * 0.5 + entity_completeness * 0.5
        elif relationships:
            completeness_score = (
                mapping_coverage * 0.5 + relationship_completeness * 0.5
            )
        else:
            completeness_score = 0.0

        return completeness_score

    async def _analyze_consistency(
        self, entities: List[Dict], relationships: List[Dict]
    ) -> float:
        """Analyze consistency of extracted knowledge"""
        consistency_scores = []

        # Entity type consistency
        entity_type_consistency = self._check_entity_type_consistency(entities)
        consistency_scores.append(entity_type_consistency)

        # Relationship type consistency
        relationship_type_consistency = self._check_relationship_type_consistency(
            relationships
        )
        consistency_scores.append(relationship_type_consistency)

        # Confidence range consistency
        confidence_consistency = self._check_confidence_consistency(
            entities + relationships
        )
        consistency_scores.append(confidence_consistency)

        return (
            sum(consistency_scores) / len(consistency_scores)
            if consistency_scores
            else 0.0
        )

    def _check_entity_type_consistency(self, entities: List[Dict]) -> float:
        """Check consistency of entity types"""
        if not entities:
            return 1.0

        # Check for consistent entity type naming
        entity_types = [e.get("entity_type", "").lower() for e in entities]
        unique_types = set(entity_types)

        # Penalize if we have too many singleton types (might indicate inconsistency)
        type_counts = {t: entity_types.count(t) for t in unique_types}
        singletons = len([t for t, count in type_counts.items() if count == 1])

        consistency_score = (
            1.0 - (singletons / len(unique_types)) if unique_types else 1.0
        )
        return max(0.0, consistency_score)

    def _check_relationship_type_consistency(self, relationships: List[Dict]) -> float:
        """Check consistency of relationship types"""
        if not relationships:
            return 1.0

        # Similar logic to entity type consistency
        relationship_types = [
            r.get("relationship_type", "").lower() for r in relationships
        ]
        unique_types = set(relationship_types)

        type_counts = {t: relationship_types.count(t) for t in unique_types}
        singletons = len([t for t, count in type_counts.items() if count == 1])

        consistency_score = (
            1.0 - (singletons / len(unique_types)) if unique_types else 1.0
        )
        return max(0.0, consistency_score)

    def _check_confidence_consistency(self, items: List[Dict]) -> float:
        """Check confidence score consistency"""
        if not items:
            return 1.0

        confidences = [
            item.get("confidence", 0) for item in items if "confidence" in item
        ]
        if not confidences:
            return 0.5  # Neutral score if no confidence scores

        # Check if confidences are in valid range [0, 1]
        valid_confidences = [c for c in confidences if 0 <= c <= 1]
        validity_score = len(valid_confidences) / len(confidences)

        # Check for reasonable distribution (not all the same)
        if len(set(confidences)) == 1:
            distribution_score = 0.7  # Slightly penalize uniform confidence
        else:
            distribution_score = 1.0

        return (validity_score + distribution_score) / 2

    async def _analyze_accuracy(
        self, entities: List[Dict], relationships: List[Dict]
    ) -> float:
        """Analyze accuracy of extracted knowledge"""
        accuracy_scores = []

        # Confidence-based accuracy
        all_items = entities + relationships
        if all_items:
            confidences = [
                item.get("confidence", 0) for item in all_items if "confidence" in item
            ]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                accuracy_scores.append(avg_confidence)

        # Mapping accuracy (mapped items are likely more accurate)
        if all_items:
            mapped_items = len(
                [item for item in all_items if item.get("is_mapped", False)]
            )
            mapping_accuracy = mapped_items / len(all_items)
            accuracy_scores.append(mapping_accuracy)

        # Text quality accuracy (basic heuristics)
        text_quality_score = self._assess_text_quality(entities)
        accuracy_scores.append(text_quality_score)

        return sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0

    def _assess_text_quality(self, entities: List[Dict]) -> float:
        """Assess text quality of entities"""
        if not entities:
            return 1.0

        quality_scores = []
        for entity in entities:
            text = entity.get("text", entity.get("entity_text", ""))
            if not text:
                quality_scores.append(0.0)
                continue

            score = 1.0

            # Penalize very short text
            if len(text.strip()) < 3:
                score -= 0.3

            # Penalize text with excessive punctuation or special characters
            special_char_ratio = len(
                [c for c in text if not c.isalnum() and not c.isspace()]
            ) / len(text)
            if special_char_ratio > 0.3:
                score -= 0.2

            # Penalize text that looks like placeholder
            placeholder_indicators = ["todo", "tbd", "xxx", "null", "undefined"]
            if any(indicator in text.lower() for indicator in placeholder_indicators):
                score -= 0.5

            quality_scores.append(max(0.0, score))

        return sum(quality_scores) / len(quality_scores)


class CustomPythonExecutor(BaseStepExecutor):
    """Executor for custom Python code execution"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            code = self.config.get("code", "")
            input_mapping = self.config.get("input_mapping", {})
            output_mapping = self.config.get("output_mapping", {})
            safe_mode = self.config.get("safe_mode", True)
            timeout_seconds = self.config.get("timeout_seconds", 30)

            if not code:
                raise PipelineExecutionError(
                    "No code provided for custom Python execution"
                )

            # Prepare execution environment
            execution_env = self._prepare_execution_environment(
                input_data, input_mapping
            )

            # Execute code safely
            execution_result = await self._execute_code_safely(
                code, execution_env, safe_mode, timeout_seconds
            )

            # Map output
            mapped_output = self._map_output(execution_result, output_mapping)

            return {
                "custom_result": self._track_provenance(
                    {
                        "execution_result": execution_result,
                        "mapped_output": mapped_output,
                        "execution_success": execution_result.get("success", False),
                        "execution_time": execution_result.get("execution_time", 0),
                    }
                ),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "custom_python",
                    "safe_mode": safe_mode,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Custom Python execution failed: {e}")

    def _prepare_execution_environment(
        self, input_data: Dict[str, Any], input_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Prepare the execution environment with input data"""
        env = {
            "input_data": input_data,
            "datetime": datetime,
            "json": json,
            "re": re,
            "logger": logger,
        }

        # Apply input mapping
        for var_name, data_path in input_mapping.items():
            try:
                # Simple dot notation path resolution
                value = input_data
                for key in data_path.split("."):
                    if isinstance(value, dict):
                        value = value.get(key)
                    else:
                        value = None
                        break
                env[var_name] = value
            except Exception as e:
                logger.warning(f"Error mapping input {var_name} from {data_path}: {e}")
                env[var_name] = None

        return env

    async def _execute_code_safely(
        self, code: str, env: Dict[str, Any], safe_mode: bool, timeout_seconds: int
    ) -> Dict[str, Any]:
        """Execute Python code safely with restrictions"""
        if safe_mode:
            # Check for dangerous operations
            dangerous_patterns = [
                r"import\s+os",
                r"import\s+sys",
                r"import\s+subprocess",
                r"__import__",
                r"eval\s*\(",
                r"exec\s*\(",
                r"open\s*\(",
                r"file\s*\(",
                r"input\s*\(",
                r"raw_input\s*\(",
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    return {
                        "success": False,
                        "error": f"Dangerous operation detected: {pattern}",
                        "output": None,
                        "execution_time": 0,
                    }

        # Prepare safe execution environment
        safe_env = {
            **env,
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "range": range,
                "sum": sum,
                "max": max,
                "min": min,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "reversed": reversed,
                "enumerate": enumerate,
                "zip": zip,
                "all": all,
                "any": any,
                "print": print,
            },
        }

        try:
            start_time = datetime.now()

            # Create a namespace for execution
            local_env = {}

            # Execute the code
            exec(code, safe_env, local_env)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Extract result (look for 'result' variable or return the local environment)
            if "result" in local_env:
                output = local_env["result"]
            else:
                # Return all variables created in local scope
                output = {k: v for k, v in local_env.items() if not k.startswith("_")}

            return {
                "success": True,
                "output": output,
                "execution_time": execution_time,
                "local_variables": list(local_env.keys()),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": None,
                "execution_time": 0,
            }

    def _map_output(
        self, execution_result: Dict[str, Any], output_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Map execution output according to output mapping configuration"""
        if not output_mapping or not execution_result.get("success"):
            return execution_result.get("output")

        mapped_output = {}
        output_data = execution_result.get("output", {})

        for output_key, source_path in output_mapping.items():
            try:
                # Simple dot notation path resolution
                value = output_data
                for key in source_path.split("."):
                    if isinstance(value, dict):
                        value = value.get(key)
                    else:
                        value = None
                        break
                mapped_output[output_key] = value
            except Exception as e:
                logger.warning(
                    f"Error mapping output {output_key} from {source_path}: {e}"
                )
                mapped_output[output_key] = None

        return mapped_output


class KnowledgeExtractorExecutor(BaseStepExecutor):
    """Executor for unstructured knowledge mapping using LLMs"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Use existing knowledge extraction workflow
            workflow = KnowledgeExtractionService()

            logger.info(
                "input_data for knowledge extraction: "
                    f"{json.dumps(input_data, indent=2)[:500]}..."
            )

            # Extract text data from input
            text_data = self._extract_text_from_input(input_data)

            all_entities = []
            all_relationships = []

            for text_item in text_data:
                text_content = text_item.get("text", "")
                result = await workflow.extract_knowledge_pipeline(
                    text=text_content,
                    domain=self.config.get("domain"),
                    extraction_options={
                        "confidence_threshold": self.config.get(
                            "confidence_threshold", 0.7
                        ),
                    },
                )

                logger.info(
                        f"Knowledge extraction result: {result}"
                                        )

                if result.get("success"):
                    all_entities.extend(result.get("entities", []))
                    all_relationships.extend(result.get("relationships", []))

            return {
                "extracting_result": self._track_provenance(
                    {
                        "entities": all_entities,
                        "relationships": all_relationships,
                    }
                ),
                "entity_count": len(all_entities),
                "relationship_count": len(all_relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "knowledge_mapping",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Knowledge mapping execution failed: {e}")

    def _extract_text_from_input(
        self, input_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract text content from various input formats"""
        # Reuse logic from KnowledgeExtractorExecutor
        return [chunk["data"]["content"] for chunk in input_data["chunks"]]


class EntityEnrichmentExecutor(BaseStepExecutor):
    """Executor for entity enrichment"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            enrichment_sources = self.config.get("enrichment_sources", [])
            enrichment_types = self.config.get("enrichment_types", ["attributes"])

            # Extract entities from input
            entities = self._extract_entities_from_input(input_data)

            # Use existing enrichment functions
            enrichment_results = {}

            # Add embeddings if requested
            if "embeddings" in enrichment_types and entities:
                entity_ids = [UUID(e["id"]) for e in entities if e.get("id")]
                if entity_ids:
                    embedding_result = await enrich_entities_with_embeddings(
                        entity_ids=entity_ids,
                        batch_size=self.config.get("batch_size", 100),
                    )
                    enrichment_results["embeddings"] = embedding_result

            # TODO: Implement other enrichment types
            # - External API enrichment
            # - Knowledge base lookups
            # - Relationship enrichment

            enriched_entities = entities  # Placeholder - would be actually enriched

            return {
                "enrichment_result": self._track_provenance(
                    {
                        "enriched_entities": enriched_entities,
                        "enrichment_stats": enrichment_results,
                    }
                ),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "entity_enrichment",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Entity enrichment execution failed: {e}")

    def _extract_entities_from_input(
        self, input_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract entities from various input formats"""
        entities = []

        # Handle fusion result output
        if "fusion_result" in input_data:
            fusion_data = input_data["fusion_result"]
            if "data" in fusion_data:
                entities.extend(fusion_data["data"].get("fused_entities", []))

        # Handle resolution result output
        elif "resolution_result" in input_data:
            resolution_data = input_data["resolution_result"]
            if "data" in resolution_data:
                entities.extend(resolution_data["data"].get("resolved_entities", []))

        return entities


class KgWriterExecutor(BaseStepExecutor):
    """Executor for knowledge graph writing"""

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            graph_format = self.config.get("graph_format", "rdf")
            batch_size = self.config.get("batch_size", 1000)
            validate_before_write = self.config.get("validate_before_write", True)

            # Extract entities and relationships from input
            entities, relationships = self._extract_graph_data_from_input(input_data)

            # Use existing sync functions for Neo4j
            write_results = {}

            if entities:
                entity_ids = [UUID(e["id"]) for e in entities if e.get("id")]
                if entity_ids:
                    neo4j_result = await sync_entities_to_neo4j(
                        entity_ids=entity_ids, batch_size=batch_size
                    )
                    write_results["entities"] = neo4j_result

            if relationships:
                relationship_ids = [UUID(r["id"]) for r in relationships if r.get("id")]
                if relationship_ids:
                    neo4j_result = await sync_relationships_to_neo4j(
                        relationship_ids=relationship_ids, batch_size=batch_size
                    )
                    write_results["relationships"] = neo4j_result

            return {
                "write_result": self._track_provenance(
                    {
                        "write_stats": write_results,
                        "graph_format": graph_format,
                    }
                ),
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "kg_writer",
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"KG writer execution failed: {e}")

    def _extract_graph_data_from_input(
        self, input_data: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Extract entities and relationships from input data"""
        entities = []
        relationships = []

        # Handle enrichment result output
        if "enrichment_result" in input_data:
            enrichment_data = input_data["enrichment_result"]
            if "data" in enrichment_data:
                entities.extend(enrichment_data["data"].get("enriched_entities", []))

        # Handle fusion result output
        elif "fusion_result" in input_data:
            fusion_data = input_data["fusion_result"]
            if "data" in fusion_data:
                entities.extend(fusion_data["data"].get("fused_entities", []))

        # Handle mapping result output
        elif "mapping_result" in input_data:
            mapping_data = input_data["mapping_result"]
            if "data" in mapping_data:
                entities.extend(mapping_data["data"].get("entities", []))
                relationships.extend(mapping_data["data"].get("relationships", []))

        return entities, relationships


# Updated step executor registry
STEP_EXECUTORS = {
    PipelineStepType.FILE_INGESTION: FileIngestionExecutor,
    PipelineStepType.API_INGESTION: ApiIngestionExecutor,
    PipelineStepType.DATABASE_INGESTION: DatabaseIngestionExecutor,
    PipelineStepType.TEXT_CHUNKING: TextChunkingExecutor,
    PipelineStepType.DATA_CLEANER: DataCleanerExecutor,
    PipelineStepType.DATA_VALIDATOR: DataValidatorExecutor,
    PipelineStepType.KNOWLEDGE_EXTRACTOR: KnowledgeExtractorExecutor,
    PipelineStepType.KNOWLEDGE_MAPPING: KnowledgeMappingExecutor,
    PipelineStepType.ONTOLOGY_ENRICHMENT: OntologyEnrichmentExecutor,
    PipelineStepType.ENTITY_RESOLUTION: EntityResolutionExecutor,
    PipelineStepType.ENTITY_FUSION: EntityFusionExecutor,
    PipelineStepType.ENTITY_ENRICHMENT: EntityEnrichmentExecutor,
    PipelineStepType.KG_WRITER: KgWriterExecutor,
    PipelineStepType.KG_COMPLETION: KgCompletionExecutor,
    PipelineStepType.QUALITY_MONITORING: QualityMonitoringExecutor,
    PipelineStepType.CUSTOM_PYTHON: CustomPythonExecutor,
}


def get_step_executor(
    step_type: PipelineStepType,
    step_config: Dict[str, Any],
    step_metadata: Dict[str, Any],
):
    """Get executor instance for a step type"""
    executor_class = STEP_EXECUTORS.get(step_type)
    if not executor_class:
        raise ValueError(f"No executor found for step type: {step_type}")

    return executor_class(step_config, step_metadata)
