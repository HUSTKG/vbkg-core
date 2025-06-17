import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.nlp.entity_extraction import EntityExtractionService
from app.nlp.relation_extraction import RelationshipExtractionService

logger = logging.getLogger(__name__)


class KgExtractionTask:
    """Task for knowledge graph extraction from text using NLP services"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.entity_service = EntityExtractionService()
        self.relationship_service = RelationshipExtractionService()

    async def extract_knowledge_from_text(
        self,
        text_content: str,
        domain: Optional[str] = None,
        user_id: Optional[UUID] = None,
        confidence_threshold: float = 0.5,
        auto_save: bool = False,
        step_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        incremental_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Extract entities and relationships from text content.

        Args:
            text_content: Text to extract knowledge from
            domain: Domain context for extraction
            user_id: User ID for tracking
            confidence_threshold: Minimum confidence threshold
            auto_save: Whether to save results automatically
            step_id: Pipeline step ID
            pipeline_id: Pipeline ID
            incremental_config: Configuration for incremental processing

        Returns:
            Dictionary containing extracted entities and relationships
        """
        try:
            self.logger.info(
                f"Starting knowledge extraction from text (length: {len(text_content)})"
            )

            # Extract entities
            entity_result = await self.entity_service.extract_entities(
                text=text_content,
                domain=domain,
                user_id=user_id,
                auto_save=False,  # We'll save later if needed
                step_id=step_id,
                pipeline_id=pipeline_id,
                incremental_config=incremental_config,
            )

            entities = entity_result.get("entities", [])
            self.logger.info(entities)
            self.logger.info(confidence_threshold)
            self.logger.info(f"Extracted {len(entities)} entities")

            # Filter entities by confidence
            filtered_entities = [
                entity
                for entity in entities
                if entity.get("confidence", 0.0) >= confidence_threshold
            ]

            self.logger.info(
                f"Filtered to {len(filtered_entities)} entities above confidence threshold"
            )

            # Extract relationships using filtered entities
            relationship_result = await self.relationship_service.extract_relationships(
                text=text_content,
                entities=filtered_entities,
                domain=domain,
                user_id=user_id,
                auto_save=False,  # We'll save later if needed
            )

            relationships = relationship_result.get("relationships", [])
            self.logger.info(f"Extracted {len(relationships)} relationships")

            # Filter relationships by confidence
            filtered_relationships = [
                rel
                for rel in relationships
                if rel.get("confidence", 0.0) >= confidence_threshold
            ]

            self.logger.info(
                f"Filtered to {len(filtered_relationships)} relationships above confidence threshold"
            )

            # Save results if auto_save is enabled
            extraction_id = None
            if auto_save and filtered_entities:
                extraction_id = await self._save_extraction_results(
                    text_content, filtered_entities, filtered_relationships, user_id
                )

            return {
                "entities": filtered_entities,
                "relationships": filtered_relationships,
                "extraction_id": extraction_id,
                "statistics": {
                    "total_entities_extracted": len(entities),
                    "filtered_entities": len(filtered_entities),
                    "total_relationships_extracted": len(relationships),
                    "filtered_relationships": len(filtered_relationships),
                    "confidence_threshold": confidence_threshold,
                    "text_length": len(text_content),
                    "extraction_time": datetime.now(timezone.utc).isoformat(),
                },
            }

        except Exception as e:
            self.logger.error(f"Error in knowledge extraction: {str(e)}")
            return {
                "entities": [],
                "relationships": [],
                "extraction_id": None,
                "error": str(e),
                "statistics": {
                    "total_entities_extracted": 0,
                    "filtered_entities": 0,
                    "total_relationships_extracted": 0,
                    "filtered_relationships": 0,
                    "confidence_threshold": confidence_threshold,
                    "text_length": len(text_content),
                    "extraction_time": datetime.now(timezone.utc).isoformat(),
                },
            }

    async def extract_knowledge_from_chunks(
        self,
        text_chunks: List[Dict[str, Any]],
        domain: Optional[str] = None,
        user_id: Optional[UUID] = None,
        confidence_threshold: float = 0.7,
        auto_save: bool = True,
        step_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        batch_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Extract knowledge from multiple text chunks.

        Args:
            text_chunks: List of text chunks to process
            domain: Domain context for extraction
            user_id: User ID for tracking
            confidence_threshold: Minimum confidence threshold
            auto_save: Whether to save results automatically
            step_id: Pipeline step ID
            pipeline_id: Pipeline ID
            batch_size: Number of chunks to process in each batch

        Returns:
            Dictionary containing aggregated extraction results
        """
        try:
            self.logger.info(
                f"Starting knowledge extraction from {len(text_chunks)} chunks"
            )

            all_entities = []
            all_relationships = []
            chunk_results = []

            # Process chunks in batches
            for i in range(0, len(text_chunks), batch_size):
                batch = text_chunks[i : i + batch_size]

                for chunk in batch:
                    chunk_content = chunk.get("text", chunk.get("content"))

                    if not chunk_content:
                        continue

                    # Extract knowledge from this chunk
                    chunk_result = await self.extract_knowledge_from_text(
                        text_content=chunk_content,
                        domain=domain,
                        user_id=user_id,
                        confidence_threshold=confidence_threshold,
                        auto_save=False,  # We'll save aggregated results
                        step_id=step_id,
                        pipeline_id=pipeline_id,
                    )

                    logger.info(
                        f"Processed chunk {chunk.get('chunk_id')} with {len(chunk_result.get('entities', []))} entities and {len(chunk_result.get('relationships', []))} relationships"
                    )

                    # Add chunk metadata to extracted entities and relationships
                    chunk_entities = chunk_result.get("entities", [])
                    chunk_relationships = chunk_result.get("relationships", [])

                    # Add chunk context to entities
                    for entity in chunk_entities:
                        entity["chunk_id"] = chunk.get("chunk_id")
                        entity["chunk_index"] = chunk.get("chunk_index")
                        entity["source"] = chunk.get("source")

                    # Add chunk context to relationships
                    for relationship in chunk_relationships:
                        relationship["chunk_id"] = chunk.get("chunk_id")
                        relationship["chunk_index"] = chunk.get("chunk_index")
                        relationship["source"] = chunk.get("source")

                    all_entities.extend(chunk_entities)
                    all_relationships.extend(chunk_relationships)

                    chunk_results.append(
                        {
                            "chunk_id": chunk.get("chunk_id"),
                            "entities_count": len(chunk_entities),
                            "relationships_count": len(chunk_relationships),
                            "statistics": chunk_result.get("statistics", {}),
                        }
                    )

            # Deduplicate entities and relationships
            deduplicated_entities = await self._deduplicate_entities(all_entities)
            deduplicated_relationships = await self._deduplicate_relationships(
                all_relationships
            )

            self.logger.info(
                f"Aggregated results: {len(deduplicated_entities)} unique entities, {len(deduplicated_relationships)} unique relationships"
            )

            # Save results if auto_save is enabled
            extraction_id = None
            if auto_save and deduplicated_entities:
                extraction_id = await self._save_extraction_results(
                    text_content="Multiple chunks",  # Placeholder for aggregated content
                    entities=deduplicated_entities,
                    relationships=deduplicated_relationships,
                    user_id=user_id,
                )

            return {
                "entities": deduplicated_entities,
                "relationships": deduplicated_relationships,
                "extraction_id": extraction_id,
                "chunk_results": chunk_results,
                "statistics": {
                    "total_chunks_processed": len(text_chunks),
                    "total_entities_extracted": len(all_entities),
                    "deduplicated_entities": len(deduplicated_entities),
                    "total_relationships_extracted": len(all_relationships),
                    "deduplicated_relationships": len(deduplicated_relationships),
                    "confidence_threshold": confidence_threshold,
                    "extraction_time": datetime.now(timezone.utc).isoformat(),
                },
            }

        except Exception as e:
            self.logger.error(f"Error in chunk knowledge extraction: {str(e)}")
            return {
                "entities": [],
                "relationships": [],
                "extraction_id": None,
                "chunk_results": [],
                "error": str(e),
                "statistics": {
                    "total_chunks_processed": len(text_chunks),
                    "total_entities_extracted": 0,
                    "deduplicated_entities": 0,
                    "total_relationships_extracted": 0,
                    "deduplicated_relationships": 0,
                    "confidence_threshold": confidence_threshold,
                    "extraction_time": datetime.now(timezone.utc).isoformat(),
                },
            }

    # Helper methods
    async def _save_extraction_results(
        self,
        text_content: str,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        user_id: Optional[UUID],
    ) -> Optional[str]:
        """Save extraction results and return extraction ID"""
        try:
            extraction_id = await self.entity_service.save_extraction_results(
                text=text_content,
                entities=entities,
                user_id=user_id,
            )

            if relationships and extraction_id:
                await self.relationship_service.save_extraction_results(
                    relationships=relationships, extraction_result_id=extraction_id
                )

            return extraction_id

        except Exception as e:
            self.logger.error(f"Error saving extraction results: {str(e)}")
            return None

    async def _deduplicate_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate entities based on text and type"""
        logger.info(f"Deduplicating {entities} entities")
        seen = set()
        deduplicated = []

        for entity in entities:

            logger.info(f"Processing entity: {entity}")
            entity_key = (
                entity.get("text", "").lower().strip(),
                entity.get("entity_type", "").lower().strip(),
            )

            logger.info(f"Entity key: {entity_key}, {entity_key[0]}")

            if entity_key not in seen and entity_key[0]:  # Skip empty entities
                seen.add(entity_key)
                deduplicated.append(entity)

        logger.info(f"Seen entities: {seen}")
        logger.info(f"Total deduplicated entities: {deduplicated}")
        return deduplicated

    async def _deduplicate_relationships(
        self, relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicate relationships based on source, target, and type"""
        seen = set()
        deduplicated = []

        for relationship in relationships:
            logger.info(f"Processing relationship: {relationship}")
            rel_key = (
                relationship.get("source_entity", "").lower().strip(),
                relationship.get("target_entity", "").lower().strip(),
                relationship.get("relationship_type", "").lower().strip(),
            )

            if rel_key not in seen and all(rel_key):  # Skip incomplete relationships
                seen.add(rel_key)
                deduplicated.append(relationship)

        return deduplicated

    async def _apply_regex_extractor(
        self, text: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply regex-based extraction"""
        import re

        entities = []
        relationships = []

        patterns = config.get("patterns", [])
        entity_type = config.get("entity_type", "CUSTOM")

        for pattern_config in patterns:
            pattern = pattern_config.get("pattern")
            if not pattern:
                continue

            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                entity_text = match.group(0).strip()
                if entity_text:
                    entities.append(
                        {
                            "entity_text": entity_text,
                            "entity_type": entity_type,
                            "confidence": pattern_config.get("confidence", 0.8),
                            "start_pos": match.start(),
                            "end_pos": match.end(),
                            "extractor": "regex",
                            "pattern": pattern,
                        }
                    )

        return {"entities": entities, "relationships": relationships}

    async def _apply_pattern_extractor(
        self, text: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply pattern-based extraction"""
        # Implement pattern-based extraction logic
        # This could use spaCy patterns, linguistic patterns, etc.
        return {"entities": [], "relationships": []}

    async def _apply_ml_extractor(
        self, text: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply ML model-based extraction"""
        # Implement ML model extraction logic
        # This could use custom trained models
        return {"entities": [], "relationships": []}

    async def validate_extraction_results(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        validation_rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate extraction results against quality rules.

        Args:
            entities: List of extracted entities
            relationships: List of extracted relationships
            validation_rules: Custom validation rules

        Returns:
            Validation results with quality metrics
        """
        try:
            validation_results = {
                "is_valid": True,
                "entity_validation": {},
                "relationship_validation": {},
                "quality_score": 0.0,
                "issues": [],
            }

            # Validate entities
            entity_issues = []
            valid_entities = 0

            for entity in entities:
                entity_valid = True

                # Check required fields
                if not entity.get("entity_text"):
                    entity_issues.append(f"Entity missing text: {entity}")
                    entity_valid = False

                if not entity.get("entity_type"):
                    entity_issues.append(f"Entity missing type: {entity}")
                    entity_valid = False

                # Check confidence score
                confidence = entity.get("confidence", 0.0)
                if not isinstance(confidence, (int, float)) or not (
                    0.0 <= confidence <= 1.0
                ):
                    entity_issues.append(
                        f"Invalid confidence score for entity: {entity}"
                    )
                    entity_valid = False

                if entity_valid:
                    valid_entities += 1

            validation_results["entity_validation"] = {
                "total": len(entities),
                "valid": valid_entities,
                "issues": entity_issues,
            }

            # Validate relationships
            relationship_issues = []
            valid_relationships = 0

            for relationship in relationships:
                relationship_valid = True

                # Check required fields
                required_fields = [
                    "source_entity_text",
                    "target_entity_text",
                    "relationship_type",
                ]
                for field in required_fields:
                    if not relationship.get(field):
                        relationship_issues.append(
                            f"Relationship missing {field}: {relationship}"
                        )
                        relationship_valid = False

                # Check confidence score
                confidence = relationship.get("confidence", 0.0)
                if not isinstance(confidence, (int, float)) or not (
                    0.0 <= confidence <= 1.0
                ):
                    relationship_issues.append(
                        f"Invalid confidence score for relationship: {relationship}"
                    )
                    relationship_valid = False

                if relationship_valid:
                    valid_relationships += 1

            validation_results["relationship_validation"] = {
                "total": len(relationships),
                "valid": valid_relationships,
                "issues": relationship_issues,
            }

            # Calculate overall quality score
            total_items = len(entities) + len(relationships)
            valid_items = valid_entities + valid_relationships

            if total_items > 0:
                validation_results["quality_score"] = valid_items / total_items
            else:
                validation_results["quality_score"] = 1.0

            # Determine if results are valid
            validation_results["is_valid"] = (
                len(entity_issues) == 0 and len(relationship_issues) == 0
            )

            validation_results["issues"] = entity_issues + relationship_issues

            return validation_results

        except Exception as e:
            self.logger.error(f"Error validating extraction results: {str(e)}")
            return {
                "is_valid": False,
                "error": str(e),
                "quality_score": 0.0,
                "issues": [f"Validation error: {str(e)}"],
            }
