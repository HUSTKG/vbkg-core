from typing import Any, Dict, Optional

from .base import BasePipelineStepService


class PipelineStepConfigurationService(BasePipelineStepService):
    """Service for generating step configurations"""

    async def get_step_config_for_datasource(
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

        if step_custom_config is None:
            step_custom_config = {}

        # Generate configuration based on step type
        config_generators = {
            "file_ingestion": self._get_file_ingestion_config,
            "api_ingestion": self._get_api_ingestion_config,
            "database_ingestion": self._get_database_ingestion_config,
            "text_chunking": self._get_text_chunking_config,
            "data_cleaner": self._get_data_cleaner_config,
            "conflict_resolution": self._get_conflict_resolution_config,
            "conflict_detection": self._get_conflict_detection_config,
            "data_validator": self._get_data_validator_config,
            "knowledge_extractor": self._get_knowledge_extractor_config,
            "knowledge_mapping": self._get_knowledge_mapping_config,
            "ontology_enrichment": self._get_ontology_enrichment_config,
            "entity_resolution": self._get_entity_resolution_config,
            "entity_fusion": self._get_entity_fusion_config,
            "entity_enrichment": self._get_entity_enrichment_config,
            "kg_writer": self._get_kg_writer_config,
            "kg_completion": self._get_kg_completion_config,
            "quality_monitoring": self._get_quality_monitoring_config,
        }

        generator = config_generators.get(step_type, self._get_default_config)
        return generator(
            base_config, connection_details, step_custom_config, trust_score
        )

    def _get_file_ingestion_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "file_paths": connection_details.get("file_paths", []),
            "encoding": connection_details.get("encoding", "utf-8"),
            "supported_formats": connection_details.get(
                "supported_formats", ["txt", "pdf", "json"]
            ),
            "extract_metadata": True,
            **step_custom_config,
        }

    def _get_api_ingestion_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "url": connection_details.get("base_url"),
            "method": connection_details.get("method", "GET"),
            "headers": connection_details.get("headers", {}),
            "auth_type": connection_details.get("auth_type"),
            "rate_limit": connection_details.get("rate_limit", {}),
            **step_custom_config,
        }

    def _get_database_ingestion_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "connection_string": self._build_connection_string(connection_details),
            "query": step_custom_config.get("query", "SELECT * FROM main_table"),
            "batch_size": step_custom_config.get("batch_size", 1000),
            "incremental_column": connection_details.get("incremental_column"),
            **step_custom_config,
        }

    def _get_text_chunking_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "chunk_size": step_custom_config.get("chunk_size", 1000),
            "chunk_overlap": step_custom_config.get("chunk_overlap", 200),
            "chunking_strategy": step_custom_config.get(
                "chunking_strategy", "recursive"
            ),
            "preserve_structure": True,
            **step_custom_config,
        }

    def _get_data_cleaner_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "remove_duplicates": step_custom_config.get("remove_duplicates", True),
            "normalize_text": step_custom_config.get("normalize_text", True),
            "remove_empty_values": step_custom_config.get("remove_empty_values", True),
            "standardize_formats": step_custom_config.get("standardize_formats", True),
            **step_custom_config,
        }

    def _get_conflict_resolution_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "similarity_threshold": max(0.8, trust_score),
            **step_custom_config,
        }

    def _get_conflict_detection_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "similarity_threshold": max(0.7, trust_score),
            **step_custom_config,
        }
    def _get_data_validator_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "validation_rules": step_custom_config.get("validation_rules", []),
            "schema_validation": step_custom_config.get("schema_validation", True),
            "quality_thresholds": step_custom_config.get("quality_thresholds", {}),
            **step_custom_config,
        }

    def _get_knowledge_extractor_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "extraction_method": step_custom_config.get(
                "extraction_method", "rule_based"
            ),
            "entity_types": step_custom_config.get(
                "entity_types", ["PERSON", "ORG", "LOCATION"]
            ),
            "relation_types": step_custom_config.get("relation_types", []),
            "confidence_threshold": 0.7,
            **step_custom_config,
        }

    def _get_knowledge_mapping_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
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

    def _get_ontology_enrichment_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "ontology_source": step_custom_config.get("ontology_source", "custom"),
            "enrichment_strategy": step_custom_config.get(
                "enrichment_strategy", "mapping"
            ),
            "similarity_threshold": max(0.8, trust_score),
            "auto_enrichment": step_custom_config.get("auto_enrichment", True),
            **step_custom_config,
        }

    def _get_entity_resolution_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        resolution_strategy = "exact_match" if trust_score > 0.8 else "fuzzy_match"
        return {
            **base_config,
            "resolution_strategy": resolution_strategy,
            "similarity_threshold": max(0.8, trust_score + 0.1),
            "blocking_strategy": "standard",
            "batch_size": 1000,
            **step_custom_config,
        }

    def _get_entity_fusion_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "fusion_strategy": "weighted" if trust_score < 0.6 else "most_recent",
            "preserve_provenance": True,
            "quality_threshold": trust_score,
            **step_custom_config,
        }

    def _get_entity_enrichment_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "enrichment_sources": step_custom_config.get("enrichment_sources", []),
            "enrichment_types": step_custom_config.get(
                "enrichment_types", ["embeddings", "conflict_detection"]
            ),
            "enrichment_strategy": step_custom_config.get(
                "enrichment_strategy", "append"
            ),
            "confidence_threshold": max(0.7, trust_score),
            **step_custom_config,
        }

    def _get_kg_writer_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "graph_format": step_custom_config.get("graph_format", "neo4j"),
            "batch_size": step_custom_config.get("batch_size", 1000),
            "validate_before_write": trust_score < 0.7,
            "update_if_exists": "merge",
            **step_custom_config,
        }

    def _get_kg_completion_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {
            **base_config,
            "completion_method": step_custom_config.get(
                "completion_method", "embedding"
            ),
            "link_prediction": step_custom_config.get("link_prediction", True),
            "confidence_threshold": max(0.8, trust_score),
            **step_custom_config,
        }

    def _get_quality_monitoring_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        metrics = ["completeness", "consistency"]
        if trust_score < 0.6:
            metrics.extend(["accuracy"])

        return {
            **base_config,
            "metrics": metrics,
            "quality_threshold": min(0.8, trust_score + 0.2),
            "monitoring_frequency": "batch",
            **step_custom_config,
        }

    def _get_default_config(
        self,
        base_config: Dict,
        connection_details: Dict,
        step_custom_config: Dict,
        trust_score: float,
    ) -> Dict[str, Any]:
        return {**base_config, **step_custom_config}

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
