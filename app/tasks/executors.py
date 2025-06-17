import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.schemas.pipeline_step import PipelineStepType
from app.tasks.data_ingestion import DataIngestionTask
from app.utils.incremental_processor import incremental_processor

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphDataType(Enum):
    """Types of data trong graph state"""

    RAW_TEXT = "raw_text"
    PROCESSED_CHUNKS = "processed_chunks"
    ENTITIES = "entities"
    RELATIONSHIPS = "relationships"
    METADATA = "metadata"


@dataclass
class GraphState:
    """Global state để maintain graph data xuyên suốt pipeline"""

    def __init__(self):
        self.entities: List[Dict[str, Any]] = []
        self.relationships: List[Dict[str, Any]] = []
        self.raw_text_data: List[Dict[str, Any]] = []
        self.processed_chunks: List[Dict[str, Any]] = []
        self.cleaned_data: List[Dict[str, Any]] = []
        self.validation_results: Optional[Dict[str, Any]] = None
        self.metadata: Dict[str, Any] = {}
        self.step_history: List[str] = []

    def add_entities(self, new_entities: List[Dict[str, Any]], source_step: str):
        """Add hoặc merge entities from a step"""
        if new_entities:
            # Merge strategy: replace nếu có cặp text-type, add nếu mới
            existing_set = set()

            for entity in self.entities:
                existing_set.add((entity.get("entity_type"), 
                    entity.get("text", entity.get("entity_text")),
                ))

            for entity in new_entities:
                entity_key = (
                    entity.get("entity_type"),
                    entity.get("text", entity.get("entity_text")),
                )
                if entity_key in existing_set:
                    # Update existing entity
                    for i, existing_entity in enumerate(self.entities):
                        existing_key = (
                            existing_entity.get("entity_type"),
                            existing_entity.get("text", entity.get("entity_text")),
                        )
                        if entity_key == existing_key:
                            self.entities[i] = self._merge_entity(
                                existing_entity, entity, source_step
                            )
                            break
                else:
                    # Add new entity
                    entity["_source_step"] = source_step
                    entity["_added_at"] = datetime.now(timezone.utc).isoformat()
                    self.entities.append(entity)

            logger.info(
                f"Added {len(new_entities)} entities from {source_step}. Total: {len(self.entities)}"
            )

    def add_relationships(
        self, new_relationships: List[Dict[str, Any]], source_step: str
    ):
        """Add hoặc merge relationships from a step"""
        if new_relationships:
            for relationship in new_relationships:
                relationship["_source_step"] = source_step
                relationship["_added_at"] = datetime.now(timezone.utc).isoformat()
                self.relationships.append(relationship)

            logger.info(
                f"Added {len(new_relationships)} relationships from {source_step}. Total: {len(self.relationships)}"
            )

    def set_text_data(
        self,
        text_data: List[Dict[str, Any]],
        data_type: GraphDataType,
        source_step: str,
    ):
        """Set text data based on type"""
        if data_type == GraphDataType.RAW_TEXT:
            self.raw_text_data = text_data
        elif data_type == GraphDataType.PROCESSED_CHUNKS:
            self.processed_chunks = text_data

        logger.info(f"Set {len(text_data)} {data_type.value} items from {source_step}")

    def set_cleaned_data(self, cleaned_data: List[Dict[str, Any]], source_step: str):
        """Set cleaned data"""
        self.cleaned_data = cleaned_data
        logger.info(f"Set {len(cleaned_data)} cleaned data items from {source_step}")

    def set_validation_results(
        self, validation_results: Dict[str, Any], source_step: str
    ):
        """Set validation results"""
        self.validation_results = validation_results
        logger.info(f"Set validation results from {source_step}")

    def add_step_to_history(self, step_name: str):
        """Track step execution history"""
        if step_name not in self.step_history:
            self.step_history.append(step_name)

    def has_step_completed(self, step_name: str) -> bool:
        """Check if a step has been completed"""
        return step_name in self.step_history

    def get_latest_entities(self) -> List[Dict[str, Any]]:
        """Get latest version của entities"""
        return self.entities

    def get_latest_relationships(self) -> List[Dict[str, Any]]:
        """Get latest version của relationships"""
        return self.relationships

    def get_best_text_data(self) -> List[Dict[str, Any]]:
        """Get best available text data, priority: cleaned > chunks > raw"""
        if self.cleaned_data:
            return self.cleaned_data
        elif self.processed_chunks:
            return self.processed_chunks
        else:
            return self.raw_text_data

    def _merge_entity(
        self, existing: Dict[str, Any], new: Dict[str, Any], source_step: str
    ) -> Dict[str, Any]:
        """Merge entity data, keeping provenance"""
        merged = existing.copy()

        # Update with new data
        for key, value in new.items():
            if key.startswith("_"):
                continue  # Skip internal fields

            if value is not None:
                merged[key] = value

        # Add provenance info
        if "_update_history" not in merged:
            merged["_update_history"] = []

        merged["_update_history"].append(
            {
                "step": source_step,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "updated_fields": list(new.keys()),
            }
        )

        return merged

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "entities": self.entities,
            "relationships": self.relationships,
            "raw_text_data": self.raw_text_data,
            "processed_chunks": self.processed_chunks,
            "cleaned_data": self.cleaned_data,
            "validation_results": self.validation_results,
            "metadata": self.metadata,
            "step_history": self.step_history,
            "summary": {
                "entity_count": len(self.entities),
                "relationship_count": len(self.relationships),
                "text_data_count": len(self.raw_text_data),
                "chunks_count": len(self.processed_chunks),
                "completed_steps": self.step_history,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphState":
        """Create GraphState from dictionary"""
        graph_state = cls()
        if data:
            graph_state.entities = data.get("entities", [])
            graph_state.relationships = data.get("relationships", [])
            graph_state.raw_text_data = data.get("raw_text_data", [])
            graph_state.processed_chunks = data.get("processed_chunks", [])
            graph_state.cleaned_data = data.get("cleaned_data", [])
            graph_state.validation_results = data.get("validation_results")
            graph_state.metadata = data.get("metadata", {})
            graph_state.step_history = data.get("step_history", [])
        return graph_state


class PipelineExecutionError(Exception):
    """Exception raised when pipeline step execution fails"""

    pass


class BaseStepExecutor:
    """Enhanced base class với graph state support"""

    def __init__(
        self,
        step_config: Dict[str, Any],
        step_metadata: Dict[str, Any],
        graph_state: Optional[GraphState] = None,
    ):
        self.config = step_config
        self.metadata = step_metadata
        self.step_id = step_metadata.get("step_id")
        self.step_name = step_metadata.get("step_name", "Unknown")
        self.pipeline_id = step_metadata.get("pipeline_id")
        self.graph_state = graph_state or GraphState()

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the step với graph state management"""

        # 1. Update graph state with any new data from input
        self._update_graph_state_from_input(input_data)

        # 2. Check prerequisites
        if not self._check_prerequisites():
            logger.warning(
                f"Prerequisites not fully met for {self.step_name}, but continuing..."
            )

        # 3. Execute step-specific logic
        step_result = await self._execute_step_logic(input_data)

        # 4. Update graph state with step results
        self._update_graph_state_from_results(step_result)

        # 5. Add step to history
        self.graph_state.add_step_to_history(self.step_name)

        # 6. Return combined result với graph_state trong output
        return {"graph_state": self.graph_state.to_dict()}

    async def _handle_incremental_processing(
        self, input_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Handle incremental processing if enabled"""
        incremental_config = self.config.get("incremental_config", {})

        if incremental_config.get("enabled", False):
            filtered_data, checkpoint = (
                await incremental_processor.process_incremental_data(
                    step_id=self.step_id,
                    pipeline_id=self.pipeline_id,
                    input_data=input_data,
                    incremental_config=incremental_config,
                )
            )
            return filtered_data, {"checkpoint": checkpoint}

        return input_data, None

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclasses - core step logic"""
        raise NotImplementedError

    def _check_prerequisites(self) -> bool:
        """Check if prerequisites are met - override in subclasses"""
        return True

    def _update_graph_state_from_input(self, input_data: Dict[str, Any]):
        """Update graph state với data từ previous steps"""

        # Extract graph state from input if available
        if "graph_state" in input_data:
            previous_state_dict = input_data["graph_state"]
            if previous_state_dict:
                previous_state = GraphState.from_dict(previous_state_dict)

                # Merge previous state vào current state
                self.graph_state.entities = previous_state.entities
                self.graph_state.relationships = previous_state.relationships
                self.graph_state.raw_text_data = previous_state.raw_text_data
                self.graph_state.processed_chunks = previous_state.processed_chunks
                self.graph_state.cleaned_data = previous_state.cleaned_data
                self.graph_state.validation_results = previous_state.validation_results
                self.graph_state.metadata = previous_state.metadata
                self.graph_state.step_history = previous_state.step_history

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với results from current step - override in subclasses"""
        pass

    def _get_best_entities(self) -> List[Dict[str, Any]]:
        """Get best available entities từ graph state"""
        return self.graph_state.get_latest_entities()

    def _get_best_relationships(self) -> List[Dict[str, Any]]:
        """Get best available relationships từ graph state"""
        return self.graph_state.get_latest_relationships()

    def _get_best_text_data(self) -> List[Dict[str, Any]]:
        """Get best available text data"""
        return self.graph_state.get_best_text_data()

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


class FileIngestionExecutor(BaseStepExecutor):
    """Executor for file ingestion với graph state support"""

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.tasks.data_ingestion import DataIngestionTask

            # Initialize DataIngestionTask
            ingestion_task = DataIngestionTask()

            datasource_id = self.config.get("datasource_id")
            encoding = self.config.get("encoding", "utf-8")
            extract_metadata = self.config.get("extract_metadata", True)

            if not datasource_id:
                raise PipelineExecutionError(
                    "datasource_id is required for file ingestion"
                )

            logger.info(f"Starting file ingestion for data source {datasource_id}")

            # Use DataIngestionTask to handle multiple file ingestion
            ingestion_result = await ingestion_task.ingest_multiple_files(
                datasource_id=UUID(datasource_id),
                encoding=encoding,
                extract_metadata=extract_metadata,
            )

            if "error" in ingestion_result:
                raise PipelineExecutionError(
                    f"File ingestion failed: {ingestion_result['error']}"
                )

            # Process each file with provenance tracking
            processed_files = []
            for file_record in ingestion_result["processed_files"]:
                processed_files.append(
                    self._track_provenance(file_record, file_record.get("file_name"))
                )

            return {
                "files": processed_files,
                "total_files": ingestion_result["total_files"],
                "successful_files": ingestion_result["successful_files"],
                "failed_files": ingestion_result["failed_files"],
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "file_ingestion",
                    "ingestion_stats": ingestion_result.get("metadata", {}),
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"File ingestion execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với ingested file data"""
        if "files" in step_result:
            text_data = []
            for file_item in step_result["files"]:
                if isinstance(file_item, dict) and "data" in file_item:
                    file_info = file_item["data"]
                    text_data.append(
                        {
                            "text": str(file_info.get("text_content", "")),
                            "source": file_info.get("file_name", "unknown"),
                            "metadata": file_info,
                            "provenance": file_item.get("provenance", {}),
                        }
                    )

            if text_data:
                self.graph_state.set_text_data(
                    text_data, GraphDataType.RAW_TEXT, self.step_name
                )


class ApiIngestionExecutor(BaseStepExecutor):
    """Enhanced API data ingestion với graph state support"""

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Initialize DataIngestionTask
            ingestion_task = DataIngestionTask()

            api_url = self.config.get("url")
            auth_params = self.config.get("auth_config", {})
            query_params = self.config.get("params", {})
            headers = self.config.get("headers", {})
            response_format = self.config.get("response_format", "json")
            datasource_id = self.config.get("datasource_id")
            user_id = self.config.get("user_id")

            if not api_url or not datasource_id:
                raise PipelineExecutionError(
                    "api_url and datasource_id are required for API ingestion"
                )

            # Use DataIngestionTask to handle API ingestion
            api_record = await ingestion_task.ingest_api_data(
                api_url=api_url,
                data_format=response_format,
                datasource_id=UUID(datasource_id),
                user_id=UUID(user_id) if user_id else None,
                auth_params=auth_params,
                query_params=query_params,
                headers=headers,
            )

            if not api_record:
                raise PipelineExecutionError("API ingestion failed")

            result = self._track_provenance(api_record, api_url)

            # Handle incremental processing
            api_data = {"api_response": result}
            filtered_data, incremental_info = await self._handle_incremental_processing(
                api_data
            )

            return {
                **filtered_data,
                "record_count": 1,
                "incremental_info": incremental_info,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "api_ingestion",
                    "api_url": api_url,
                    "response_format": response_format,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"API ingestion execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với API data"""
        if "api_response" in step_result:
            api_data = step_result["api_response"]
            if isinstance(api_data, dict) and "data" in api_data:
                api_content = api_data["data"]
                text_data = [
                    {
                        "text": str(api_content),
                        "source": "api",
                        "metadata": api_content,
                        "provenance": api_data.get("provenance", {}),
                    }
                ]

                self.graph_state.set_text_data(
                    text_data, GraphDataType.RAW_TEXT, self.step_name
                )


class DatabaseIngestionExecutor(BaseStepExecutor):
    """Enhanced Database data ingestion với graph state support"""

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Initialize DataIngestionTask
            ingestion_task = DataIngestionTask()

            connection_string = self.config.get("connection_string")
            query = self.config.get("query")
            output_format = self.config.get("output_format", "json")
            datasource_id = self.config.get("datasource_id")
            user_id = self.config.get("user_id")

            if not connection_string or not query or not datasource_id:
                raise PipelineExecutionError(
                    "connection_string, query, and datasource_id are required for database ingestion"
                )

            # Use DataIngestionTask to handle database ingestion
            db_record = await ingestion_task.ingest_database_data(
                connection_string=connection_string,
                query=query,
                datasource_id=UUID(datasource_id),
                user_id=UUID(user_id) if user_id else None,
                output_format=output_format,
            )

            if not db_record:
                raise PipelineExecutionError("Database ingestion failed")

            result = self._track_provenance(db_record, connection_string)

            # Handle incremental processing
            db_data = {"database_result": result}
            filtered_data, incremental_info = await self._handle_incremental_processing(
                db_data
            )

            return {
                **filtered_data,
                "record_count": db_record.get("metadata", {}).get("row_count", 0),
                "incremental_info": incremental_info,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "database_ingestion",
                    "output_format": output_format,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Database ingestion execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với database data"""
        if "database_result" in step_result:
            db_data = step_result["database_result"]
            if isinstance(db_data, dict) and "data" in db_data:
                db_content = db_data["data"]
                text_data = [
                    {
                        "text": str(db_content),
                        "source": "database",
                        "metadata": db_content,
                        "provenance": db_data.get("provenance", {}),
                    }
                ]

                self.graph_state.set_text_data(
                    text_data, GraphDataType.RAW_TEXT, self.step_name
                )


class TextChunkingExecutor(BaseStepExecutor):
    """Executor for text chunking với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Text chunking cần text data"""
        text_data = self._get_best_text_data()
        if not text_data:
            logger.warning("No text data available for chunking")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.nlp.text_chunking import TextChunker

            text_chunker = TextChunker()
            chunk_size = self.config.get("chunk_size", 1000)
            chunk_overlap = self.config.get("chunk_overlap", 200)
            chunking_strategy = self.config.get("chunking_strategy", "recursive")

            # Get text data từ graph state
            text_data = self._get_best_text_data()

            chunked_data = []

            for text_item in text_data:
                text_content: str = text_item.get("text", "") or text_item.get(
                    "content", ""
                )

                if chunking_strategy == "structured":
                    if isinstance(text_content, (dict, list)):
                        chunks = text_chunker.text_chunk(text_content, chunk_size)
                    else:
                        chunks = text_chunker.text_chunk(
                            text_content, chunk_size, chunk_overlap
                        )
                else:
                    chunks = text_chunker.text_chunk(
                        text_content, chunk_size, chunk_overlap
                    )

                logger.info(
                    f"Chunking text from source '{text_item.get('source', 'unknown')}' "
                    f"into {len(chunks)} chunks with size {chunk_size} and overlap {chunk_overlap}"
                )

                for i, chunk in enumerate(chunks):
                    chunked_item = {
                        "chunk_id": f"{text_item.get('source', 'unknown')}_{i}",
                        "content": (
                            chunk.get("text", chunk)
                            if isinstance(chunk, dict)
                            else chunk
                        ),
                        "section": (
                            chunk.get("section", "unknown")
                            if isinstance(chunk, dict)
                            else "unknown"
                        ),
                        "chunk_type": (
                            chunk.get("chunk_type", "text")
                            if isinstance(chunk, dict)
                            else "text"
                        ),
                        "char_count": chunk.get("char_count", len(str(chunk))),
                        "estimated_tokens": chunk.get("estimated_tokens", 0),
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
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Text chunking execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với processed chunks"""
        if "chunks" in step_result:
            chunk_data = []
            for chunk_item in step_result["chunks"]:
                if isinstance(chunk_item, dict) and "data" in chunk_item:
                    chunk_data.append(chunk_item["data"])

            if chunk_data:
                self.graph_state.set_text_data(
                    chunk_data, GraphDataType.PROCESSED_CHUNKS, self.step_name
                )


class DataCleanerExecutor(BaseStepExecutor):
    """Enhanced Data cleaner với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Data cleaning cần text data"""
        text_data = self._get_best_text_data()
        if not text_data:
            logger.warning("No text data available for cleaning")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            cleaning_rules = self.config.get("cleaning_rules", {})
            remove_duplicates = cleaning_rules.get("remove_duplicates", True)
            normalize_text = cleaning_rules.get("normalize_text", True)
            remove_empty = cleaning_rules.get("remove_empty", True)
            custom_rules = cleaning_rules.get("custom_rules", [])

            # Use best text data từ graph state
            data_to_clean = self._get_best_text_data()

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

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với cleaned data"""
        if "cleaned_data" in step_result:
            cleaned = step_result["cleaned_data"]
            if isinstance(cleaned, dict) and "data" in cleaned:
                cleaned_items = cleaned["data"]
                if isinstance(cleaned_items, list):
                    self.graph_state.set_cleaned_data(cleaned_items, self.step_name)

    def _generate_item_key(self, item: Dict[str, Any]) -> str:
        """Generate a unique key for duplicate detection"""
        if isinstance(item, dict):
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
            return any(v for v in item.values() if v)

        return bool(str(item).strip())

    def _normalize_item_text(self, item: Dict[str, Any]) -> bool:
        """Normalize text content in item"""
        normalized = False

        if isinstance(item, dict):
            for key in ["content", "text", "entity_text"]:
                if key in item and isinstance(item[key], str):
                    original = item[key]
                    normalized_text = re.sub(r"\s+", " ", original.strip())
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
    """Enhanced Data validator với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Data validation cần text data"""
        text_data = self._get_best_text_data()
        if not text_data:
            logger.warning("No text data available for validation")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validation_rules = self.config.get("validation_rules", {})
            schema_validation = validation_rules.get("schema_validation", True)
            quality_checks = validation_rules.get("quality_checks", True)
            business_rules = validation_rules.get("business_rules", [])
            required_fields = validation_rules.get("required_fields", [])

            # Use best text data từ graph state
            data_to_validate = self._get_best_text_data()

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
                    "validated_data": data_to_validate,
                    "metadata": {
                        "execution_time": datetime.now(timezone.utc).isoformat(),
                        "step_type": "data_validator",
                    },
                }

            valid_items = 0
            field_counts = {}

            for item in data_to_validate:
                item_valid = True

                if schema_validation:
                    schema_errors = self._validate_item_schema(item, required_fields)
                    if schema_errors:
                        validation_results["validation_errors"].extend(schema_errors)
                        item_valid = False

                if quality_checks:
                    quality_issues = self._check_item_quality(item)
                    if quality_issues:
                        validation_results["validation_errors"].extend(quality_issues)
                        item_valid = False

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
                "validated_data": data_to_validate,
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "data_validator",
                    "total_items_validated": total_items,
                    "valid_items": valid_items,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Data validator execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với validation results"""
        if "validation_results" in step_result:
            validation_data = step_result["validation_results"]
            if isinstance(validation_data, dict) and "data" in validation_data:
                self.graph_state.set_validation_results(
                    validation_data["data"], self.step_name
                )

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
            for key in ["content", "text", "entity_text"]:
                if key in item and isinstance(item[key], str):
                    if len(item[key].strip()) < 3:
                        issues.append(f"Suspiciously short {key}: '{item[key]}'")

            placeholder_values = ["TODO", "TBD", "N/A", "null", "undefined", ""]
            for key, value in item.items():
                if str(value).strip() in placeholder_values:
                    issues.append(f"Placeholder value in {key}: '{value}'")

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


class KnowledgeExtractorExecutor(BaseStepExecutor):
    """Enhanced Knowledge Extractor với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Knowledge extraction cần text data"""
        text_data = self._get_best_text_data()
        if not text_data:
            logger.warning("No text data available for knowledge extraction")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.tasks.kg_extraction import KgExtractionTask

            kg_extraction_task = KgExtractionTask()

            domain = self.config.get("domain")
            user_id = self.config.get("user_id")
            confidence_threshold = self.config.get("confidence_threshold", 0.7)
            auto_save = self.config.get("auto_save", True)
            custom_extractors = self.config.get("custom_extractors", [])

            # Get text data từ graph state
            text_data = self._get_best_text_data()
            if not text_data:
                logger.warning("No text data found for knowledge extraction")
                return {
                    "extraction_result": self._track_provenance(
                        {
                            "entities": [],
                            "relationships": [],
                            "extraction_id": None,
                        }
                    ),
                    "entity_count": 0,
                    "relationship_count": 0,
                    "metadata": {
                        "execution_time": datetime.now(timezone.utc).isoformat(),
                        "step_type": "knowledge_extraction",
                    },
                }

            # Process based on data type
            if len(text_data) > 1 or any("chunk_id" in item for item in text_data):

                logger.info(f"Extracting knowledge from {len(text_data)} text chunks")
                # Process as chunks
                result = await kg_extraction_task.extract_knowledge_from_chunks(
                    text_chunks=text_data,
                    domain=domain,
                    user_id=UUID(user_id) if user_id else None,
                    confidence_threshold=confidence_threshold,
                    auto_save=auto_save,
                    step_id=self.step_id,
                    pipeline_id=self.pipeline_id,
                )
            else:
                # Process as single text
                text_content = text_data[0].get("text", "") or text_data[0].get(
                    "content", ""
                )

                logger.info(
                    f"Extracting knowledge from text content: {text_content[:100]}..."
                )

                if custom_extractors:
                    result = await kg_extraction_task.extract_knowledge_with_custom_extractors(
                        text_content=text_content,
                        custom_extractors=custom_extractors,
                        domain=domain,
                        user_id=UUID(user_id) if user_id else None,
                        confidence_threshold=confidence_threshold,
                    )
                else:
                    result = await kg_extraction_task.extract_knowledge_from_text(
                        text_content=text_content,
                        domain=domain,
                        user_id=UUID(user_id) if user_id else None,
                        confidence_threshold=confidence_threshold,
                        auto_save=auto_save,
                        step_id=self.step_id,
                        pipeline_id=self.pipeline_id,
                        incremental_config=self.config.get("incremental_config"),
                    )

            entities = result.get("entities", [])
            relationships = result.get("relationships", [])
            extraction_id = result.get("extraction_id")

            return {
                "extraction_result": self._track_provenance(
                    {
                        "entities": entities,
                        "relationships": relationships,
                        "extraction_id": extraction_id,
                        "statistics": result.get("statistics", {}),
                    }
                ),
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "knowledge_extraction",
                    "domain": domain,
                    "confidence_threshold": confidence_threshold,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Knowledge extraction execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với extracted entities/relationships"""

        if "extraction_result" in step_result:
            extraction_data = step_result["extraction_result"]

            if "data" in extraction_data:
                data = extraction_data["data"]

                # Add entities to graph state
                entities = data.get("entities", [])
                if entities:
                    self.graph_state.add_entities(entities, self.step_name)

                # Add relationships to graph state
                relationships = data.get("relationships", [])
                if relationships:
                    self.graph_state.add_relationships(relationships, self.step_name)


class OntologyEnrichmentExecutor(BaseStepExecutor):
    """Enhanced Ontology Enrichment với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Ontology enrichment cần entities từ knowledge extraction"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for ontology enrichment")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.tasks.ontology_enrichment import OntologyEnrichmentTask

            ontology_task = OntologyEnrichmentTask()

            domain = self.config.get("domain")
            user_id = self.config.get("user_id")
            auto_apply_suggestions = self.config.get("auto_apply_suggestions", False)
            confidence_threshold = self.config.get("confidence_threshold", 0.8)
            use_existing_mappings = self.config.get("use_existing_mappings", True)
            enable_ontology_extensions = self.config.get(
                "enable_ontology_extensions", False
            )

            # Get entities and relationships từ graph state
            entities = self._get_best_entities()
            relationships = self._get_best_relationships()

            if not entities and not relationships:
                logger.warning(
                    "No entities or relationships found for ontology enrichment"
                )
                return {
                    "ontology_result": self._track_provenance(
                        {
                            "enriched_entities": [],
                            "enriched_relationships": [],
                            "entity_mapping_suggestions": [],
                            "relationship_mapping_suggestions": [],
                            "current_ontology": {},
                            "updated_ontology": {},
                        }
                    ),
                    "entity_count": 0,
                    "relationship_count": 0,
                    "mapping_suggestions_count": 0,
                    "metadata": {
                        "execution_time": datetime.now(timezone.utc).isoformat(),
                        "step_type": "ontology_enrichment",
                    },
                }

            # Perform ontology enrichment
            enrichment_result = await ontology_task.enrich_with_ontology_mapping(
                entities=entities,
                relationships=relationships,
                domain=domain,
                user_id=user_id if user_id else None,
                auto_apply_suggestions=auto_apply_suggestions,
                confidence_threshold=confidence_threshold,
                use_existing_mappings=use_existing_mappings,
            )

            # Generate extension suggestions if enabled
            extension_suggestions = []
            if enable_ontology_extensions:
                extension_result = await ontology_task.suggest_ontology_extensions(
                    entities=entities,
                    relationships=relationships,
                    domain=domain,
                    user_id=user_id if user_id else None,
                )
                extension_suggestions = extension_result.get(
                    "extension_suggestions", []
                )

            enriched_entities = enrichment_result.get("enriched_entities", [])
            enriched_relationships = enrichment_result.get("enriched_relationships", [])
            entity_mapping_suggestions = enrichment_result.get(
                "entity_mapping_suggestions", []
            )
            relationship_mapping_suggestions = enrichment_result.get(
                "relationship_mapping_suggestions", []
            )

            total_suggestions = len(entity_mapping_suggestions) + len(
                relationship_mapping_suggestions
            )

            return {
                "ontology_result": self._track_provenance(
                    {
                        "enriched_entities": enriched_entities,
                        "enriched_relationships": enriched_relationships,
                        "entity_mapping_suggestions": entity_mapping_suggestions,
                        "relationship_mapping_suggestions": relationship_mapping_suggestions,
                        "current_ontology": enrichment_result.get(
                            "current_ontology", {}
                        ),
                        "updated_ontology": enrichment_result.get(
                            "updated_ontology", {}
                        ),
                        "extension_suggestions": extension_suggestions,
                        "mapping_record_id": enrichment_result.get("mapping_record_id"),
                        "statistics": enrichment_result.get("statistics", {}),
                    }
                ),
                "entity_count": len(enriched_entities),
                "relationship_count": len(enriched_relationships),
                "mapping_suggestions_count": total_suggestions,
                "extension_suggestions_count": len(extension_suggestions),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "ontology_enrichment",
                    "domain": domain,
                    "auto_apply_suggestions": auto_apply_suggestions,
                    "confidence_threshold": confidence_threshold,
                    "ontology_extensions_enabled": enable_ontology_extensions,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Ontology enrichment execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với enriched entities/relationships"""

        if "ontology_result" in step_result:
            ontology_data = step_result["ontology_result"]

            if "data" in ontology_data:
                data = ontology_data["data"]

                # Update entities in graph state
                enriched_entities = data.get("enriched_entities", [])
                if enriched_entities:
                    self.graph_state.add_entities(enriched_entities, self.step_name)

                # Update relationships in graph state
                enriched_relationships = data.get("enriched_relationships", [])
                if enriched_relationships:
                    self.graph_state.add_relationships(
                        enriched_relationships, self.step_name
                    )


class EntityResolutionExecutor(BaseStepExecutor):
    """Enhanced Entity Resolution với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Entity resolution cần entities"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for entity resolution")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.tasks.entity_resolution import EntityResolutionTask

            resolution_strategy = self.config.get("resolution_strategy", "fuzzy_match")
            similarity_threshold = self.config.get("similarity_threshold", 0.8)
            clustering_method = self.config.get("clustering_method", "single_linkage")
            auto_save = self.config.get("auto_save", True)
            user_id = self.config.get("user_id")

            # Get entities từ graph state
            entities = self._get_best_entities()

            # Create task and execute
            task = EntityResolutionTask()
            result = await task.resolve_entities(
                entities=entities,
                resolution_strategy=resolution_strategy,
                similarity_threshold=similarity_threshold,
                clustering_method=clustering_method,
                auto_save=auto_save,
                user_id=user_id,
            )

            return {
                "resolution_result": self._track_provenance(result),
                "input_entity_count": len(entities),
                "resolved_entity_count": len(result.get("resolved_entities", [])),
                "cluster_count": len(result.get("entity_clusters", [])),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "entity_resolution",
                    "resolution_strategy": resolution_strategy,
                    "similarity_threshold": similarity_threshold,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Entity resolution execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với resolved entities"""

        if "resolution_result" in step_result:
            resolution_data = step_result["resolution_result"]

            if "data" in resolution_data:
                data = resolution_data["data"]

                # Update entities với resolved versions
                resolved_entities = data.get("resolved_entities", [])
                if resolved_entities:
                    self.graph_state.add_entities(resolved_entities, self.step_name)


class EntityFusionExecutor(BaseStepExecutor):
    """Enhanced Entity fusion với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Entity fusion cần resolved entities"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for entity fusion")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.tasks.entity_fusion import EntityFusionTask

            fusion_strategy = self.config.get("fusion_strategy", "most_recent")
            preserve_provenance = self.config.get("preserve_provenance", True)
            conflict_resolution = self.config.get(
                "conflict_resolution", "highest_confidence"
            )
            auto_save = self.config.get("auto_save", True)
            user_id = self.config.get("user_id")

            # Get entities từ graph state thay vì từ input
            entities = self._get_best_entities()

            # Create simple clusters from entities if not available
            entity_clusters = [{"entities": entities, "cluster_id": "default"}]

            # Create task and execute
            task = EntityFusionTask()
            result = await task.fuse_entities(
                resolved_entities=entities,
                entity_clusters=entity_clusters,
                fusion_strategy=fusion_strategy,
                preserve_provenance=preserve_provenance,
                conflict_resolution=conflict_resolution,
                auto_save=auto_save,
                user_id=user_id,
            )

            return {
                "fusion_result": self._track_provenance(result),
                "input_entity_count": len(entities),
                "fused_entity_count": len(result.get("fused_entities", [])),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "entity_fusion",
                    "fusion_strategy": fusion_strategy,
                    "conflict_resolution": conflict_resolution,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Entity fusion execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với fused entities"""
        if "fusion_result" in step_result:
            fusion_data = step_result["fusion_result"]

            if "data" in fusion_data:
                data = fusion_data["data"]

                # Update entities với fused versions
                fused_entities = data.get("fused_entities", [])
                if fused_entities:
                    self.graph_state.add_entities(fused_entities, self.step_name)


class EntityEnrichmentExecutor(BaseStepExecutor):
    """Enhanced Entity enrichment với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Entity enrichment cần entities"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for entity enrichment")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.tasks.entity_enrichment import EntityEnrichmentTask

            # Initialize EntityEnrichmentTask
            enrichment_task = EntityEnrichmentTask()

            enrichment_sources = self.config.get("enrichment_sources", [])
            enrichment_types = self.config.get("enrichment_types", ["embeddings"])
            batch_size = self.config.get("batch_size", 100)
            force_update = self.config.get("force_update", False)

            # Get entities từ graph state
            entities = self._get_best_entities()

            enrichment_results = {}
            enriched_entities = []  # Start with original entities

            # Add embeddings if requested
            if "embeddings" in enrichment_types and entities:
                entity_ids = [e["id"] for e in entities if e.get("id")]
                embedding_result = (
                    await enrichment_task.enrich_entities_with_embeddings(
                        entity_ids=entity_ids,
                        batch_size=batch_size,
                        force_update=force_update,
                    )
                )

                if embedding_result["status"] == "failed":
                    raise PipelineExecutionError(
                        f"Embedding enrichment failed: {embedding_result['error']}"
                    )
                enrichment_results["embeddings"] = embedding_result
                enriched_entities = embedding_result.get("enriched_entities", entities)

            # Sync to Neo4j if requested
            if "neo4j_sync" in enrichment_types and entities:
                entity_ids = [e["id"] for e in entities if e.get("id")]
                if entity_ids:
                    neo4j_result = await enrichment_task.sync_entities_to_neo4j(
                        entity_ids=entity_ids,
                        batch_size=batch_size,
                    )
                    enrichment_results["neo4j_sync"] = neo4j_result

            # External data enrichment if requested
            if "external_data" in enrichment_types and entities and enrichment_sources:
                entity_ids = [e["id"] for e in entities if e.get("id")]
                if entity_ids:
                    external_result = (
                        await enrichment_task.enrich_entities_with_external_data(
                            entity_ids=entity_ids,
                            enrichment_sources=enrichment_sources,
                            batch_size=batch_size,
                        )
                    )
                    enrichment_results["external_data"] = external_result

            # Conflict detection if requested
            if "conflict_detection" in enrichment_types:
                conflict_threshold = self.config.get("conflict_threshold", 0.75)
                entity_types = self.config.get("entity_types_for_conflicts")

                conflict_result = await enrichment_task.detect_entity_conflicts(
                    threshold=conflict_threshold,
                    batch_size=batch_size,
                    entity_types=entity_types,
                )
                enrichment_results["conflict_detection"] = conflict_result

            return {
                "enrichment_result": self._track_provenance(
                    {
                        "enriched_entities": enriched_entities,
                        "enrichment_stats": enrichment_results,
                    }
                ),
                "entity_count": len(enriched_entities),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "entity_enrichment",
                    "enrichment_types": enrichment_types,
                    "enrichment_sources": enrichment_sources,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Entity enrichment execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với enriched entities"""
        if "enrichment_result" in step_result:
            enrichment_data = step_result["enrichment_result"]

            if "data" in enrichment_data:
                data = enrichment_data["data"]

                # Update entities với enriched versions
                enriched_entities = data.get("enriched_entities", [])
                if enriched_entities:
                    self.graph_state.add_entities(enriched_entities, self.step_name)


class KgCompletionExecutor(BaseStepExecutor):
    """Enhanced KG completion với graph state support"""

    def _check_prerequisites(self) -> bool:
        """KG completion cần entities"""
        entities = self._get_best_entities()
        if not entities:
            logger.warning("No entities available for KG completion")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.tasks.kg_completion import KnowledgeGraphCompletionTask

            completion_types = self.config.get(
                "completion_types", ["missing_entities", "missing_relationships"]
            )
            auto_apply_suggestions = self.config.get("auto_apply_suggestions", False)
            confidence_threshold = self.config.get("confidence_threshold", 0.8)
            user_id = self.config.get("user_id")

            # Get entities and relationships từ graph state
            entities = self._get_best_entities()
            relationships = self._get_best_relationships()

            # Create task and execute
            task = KnowledgeGraphCompletionTask()
            result = await task.complete_knowledge_graph(
                entities=entities,
                relationships=relationships,
                completion_types=completion_types,
                auto_apply_suggestions=auto_apply_suggestions,
                confidence_threshold=confidence_threshold,
                user_id=user_id,
            )

            return {
                "completion_result": self._track_provenance(result),
                "input_entity_count": len(entities),
                "input_relationship_count": len(relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "kg_completion",
                    "completion_types": completion_types,
                    "confidence_threshold": confidence_threshold,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"KG completion execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state với completion suggestions"""
        if "completion_result" in step_result:
            completion_data = step_result["completion_result"]

            if "data" in completion_data:
                data = completion_data["data"]

                # Add suggested entities if any
                suggested_entities = data.get("suggested_entities", [])
                if suggested_entities:
                    self.graph_state.add_entities(suggested_entities, self.step_name)

                # Add suggested relationships if any
                suggested_relationships = data.get("suggested_relationships", [])
                if suggested_relationships:
                    self.graph_state.add_relationships(
                        suggested_relationships, self.step_name
                    )


class QualityMonitoringExecutor(BaseStepExecutor):
    """Enhanced Quality monitoring với graph state support"""

    def _check_prerequisites(self) -> bool:
        """Quality monitoring cần entities hoặc relationships"""
        entities = self._get_best_entities()
        relationships = self._get_best_relationships()
        if not entities and not relationships:
            logger.warning(
                "No entities or relationships available for quality monitoring"
            )
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.tasks.quality_monitoring import QualityMonitoringTask

            quality_threshold = self.config.get("quality_threshold", 0.8)
            generate_recommendations = self.config.get("generate_recommendations", True)

            # Get entities and relationships từ graph state
            entities = self._get_best_entities()
            relationships = self._get_best_relationships()

            # Create task and execute
            task = QualityMonitoringTask()
            result = await task.monitor_quality(
                entities=entities,
                relationships=relationships,
                step_id=self.step_id,
                pipeline_run_id=self.pipeline_id,
                quality_threshold=quality_threshold,
                generate_recommendations=generate_recommendations,
            )

            return {
                "quality_result": self._track_provenance(result),
                "monitored_entity_count": len(entities),
                "monitored_relationship_count": len(relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "quality_monitoring",
                    "quality_threshold": quality_threshold,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"Quality monitoring execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state metadata với quality results"""
        if "quality_result" in step_result:
            quality_data = step_result["quality_result"]
            if "data" in quality_data:
                # Store quality results in metadata
                self.graph_state.metadata["quality_monitoring"] = quality_data["data"]


class KgWriterExecutor(BaseStepExecutor):
    """Enhanced KG writer với graph state support"""

    def _check_prerequisites(self) -> bool:
        """KG writer cần entities hoặc relationships"""
        entities = self._get_best_entities()
        relationships = self._get_best_relationships()
        if not entities and not relationships:
            logger.warning("No entities or relationships available for KG writing")
            return False
        return True

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from app.tasks.kg_writer import KnowledgeGraphWriterTask

            graph_format = self.config.get("graph_format", "neo4j")
            batch_size = self.config.get("batch_size", 1000)
            validate_before_write = self.config.get("validate_before_write", True)
            user_id = self.config.get("user_id")

            # Get entities and relationships từ graph state
            entities = self._get_best_entities()
            relationships = self._get_best_relationships()

            # Create task and execute
            task = KnowledgeGraphWriterTask()
            result = await task.write_knowledge_graph(
                entities=entities,
                relationships=relationships,
                graph_format=graph_format,
                batch_size=batch_size,
                validate_before_write=validate_before_write,
                user_id=user_id,
            )

            return {
                "write_result": self._track_provenance(result),
                "written_entity_count": len(entities),
                "written_relationship_count": len(relationships),
                "metadata": {
                    "execution_time": datetime.now(timezone.utc).isoformat(),
                    "step_type": "kg_writer",
                    "graph_format": graph_format,
                    "batch_size": batch_size,
                },
            }

        except Exception as e:
            raise PipelineExecutionError(f"KG writer execution failed: {e}")

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state metadata với write results"""
        if "write_result" in step_result:
            write_data = step_result["write_result"]
            if "data" in write_data:
                # Store write results in metadata
                self.graph_state.metadata["kg_writer"] = write_data["data"]

                write_result = write_data["data"]["write_result"]
                saved_entities = write_result.get("saved_entities", [])
                logger.info(f"SAVED: {saved_entities}")
                saved_relationships = write_result.get("saved_relationships", [])

                if saved_entities:
                    self.graph_state.add_entities(saved_entities, self.step_name)
                if saved_relationships:
                    self.graph_state.add_relationships(
                        saved_relationships, self.step_name
                    )


class CustomPythonExecutor(BaseStepExecutor):
    """Enhanced Custom Python executor với graph state support"""

    async def _execute_step_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
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

            # Prepare execution environment with graph state
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

    def _update_graph_state_from_results(self, step_result: Dict[str, Any]):
        """Update graph state từ custom Python results"""
        if "custom_result" in step_result:
            custom_data = step_result["custom_result"]
            if "data" in custom_data:
                mapped_output = custom_data["data"].get("mapped_output")

                # Check if output contains entities or relationships
                if isinstance(mapped_output, dict):
                    if "entities" in mapped_output:
                        entities = mapped_output["entities"]
                        if isinstance(entities, list):
                            self.graph_state.add_entities(entities, self.step_name)

                    if "relationships" in mapped_output:
                        relationships = mapped_output["relationships"]
                        if isinstance(relationships, list):
                            self.graph_state.add_relationships(
                                relationships, self.step_name
                            )

    def _prepare_execution_environment(
        self, input_data: Dict[str, Any], input_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """Prepare the execution environment with input data và graph state"""
        env = {
            "input_data": input_data,
            "graph_state": self.graph_state,
            "entities": self._get_best_entities(),
            "relationships": self._get_best_relationships(),
            "text_data": self._get_best_text_data(),
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


# Updated step executor registry
STEP_EXECUTORS = {
    PipelineStepType.FILE_INGESTION: FileIngestionExecutor,
    PipelineStepType.API_INGESTION: ApiIngestionExecutor,
    PipelineStepType.DATABASE_INGESTION: DatabaseIngestionExecutor,
    PipelineStepType.TEXT_CHUNKING: TextChunkingExecutor,
    PipelineStepType.DATA_CLEANER: DataCleanerExecutor,
    PipelineStepType.DATA_VALIDATOR: DataValidatorExecutor,
    PipelineStepType.KNOWLEDGE_EXTRACTOR: KnowledgeExtractorExecutor,
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
    graph_state: Optional[GraphState] = None,
):
    """Get enhanced executor instance với graph state support"""
    executor_class = STEP_EXECUTORS.get(step_type)
    if not executor_class:
        raise ValueError(f"No executor found for step type: {step_type}")

    # Return enhanced executor với graph state
    return executor_class(step_config, step_metadata, graph_state)
