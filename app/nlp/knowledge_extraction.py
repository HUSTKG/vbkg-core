import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.supabase import get_supabase
from app.nlp.entity_extraction import EntityExtractionService
from app.nlp.ontogpt import OntoGPTService
from app.nlp.relation_extraction import RelationshipExtractionService
from app.nlp.text_chunking import TextChunker
from app.services.ontology import OntologyService

logger = logging.getLogger(__name__)


class KnowledgeExtractionService:
    """
    Complete workflow for knowledge extraction, ontology-guided processing,
    and automatic ontology enrichment with Vietnamese language support
    """

    def __init__(self):
        self.ontogpt_service = OntoGPTService()
        self.entity_service = EntityExtractionService()
        self.relationship_service = RelationshipExtractionService()
        self.ontology_service = OntologyService()
        self.chunker = TextChunker()

    async def extract_knowledge_pipeline(
        self,
        text: str,
        domain: Optional[str] = None,
        user_id: Optional[str] = None,
        extraction_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Complete knowledge extraction pipeline with Vietnamese support and chunking

        Args:
            text: Input Vietnamese text to process
            domain: Domain focus (e.g., 'banking' for banking)
            user_id: User performing extraction
            extraction_options: Additional options for extraction

        Returns:
            Complete extraction results with ontology enrichment
        """
        try:
            # Set default options with Vietnamese-specific settings
            options = extraction_options or {}
            # use_ontogpt = options.get("use_ontogpt", True)
            enrich_ontology = options.get("enrich_ontology", True)
            auto_create_mappings = options.get("auto_create_mappings", False)
            confidence_threshold = options.get("confidence_threshold", 0.8)
            chunk_size = options.get("chunk_size", 3000)
            chunk_overlap = options.get("chunk_overlap", 300)
            use_chunking = options.get("use_chunking", len(text) > chunk_size * 2)

            logger.info(
                f"Starting Vietnamese knowledge extraction pipeline for text length: {len(text)}"
            )

            # Phase 0: Text preprocessing and chunking for large texts
            if use_chunking:
                logger.info("Phase 0: Chunking large Vietnamese text")
                chunks = self.chunker.text_chunk(
                    text, 
                    max_tokens=chunk_size, 
                    overlap_tokens=chunk_overlap
                )
                logger.info(f"Created {len(chunks)} chunks")
            else:
                chunks = [{'text': text, 'section': 'full', 'chunk_type': 'full'}]

            # Initialize aggregated results
            all_entities = []
            all_relationships = []
            all_new_concepts = {"classes": [], "properties": []}
            chunk_results = []

            # Process each chunk
            for chunk_idx, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {chunk_idx + 1}/{len(chunks)}")
                
                chunk_text = chunk['text']
                chunk_result = await self._process_single_chunk(
                    chunk_text, domain, user_id, options, chunk_idx
                )
                
                chunk_results.append({
                    "chunk_index": chunk_idx,
                    "chunk_metadata": chunk,
                    "extraction_result": chunk_result
                })
                
                # Aggregate results
                if chunk_result.get("success"):
                    all_entities.extend(chunk_result.get("entities", []))
                    all_relationships.extend(chunk_result.get("relationships", []))
                    
                    # Merge new concepts
                    chunk_new_concepts = chunk_result.get("new_concepts", {})
                    if chunk_new_concepts.get("classes"):
                        all_new_concepts["classes"].extend(chunk_new_concepts["classes"])
                    if chunk_new_concepts.get("properties"):
                        all_new_concepts["properties"].extend(chunk_new_concepts["properties"])

            # Phase 1: Post-process and deduplicate results
            logger.info("Phase 1: Post-processing and deduplication")
            all_entities = await self._deduplicate_entities(all_entities)
            all_relationships = await self._deduplicate_relationships(all_relationships)
            all_new_concepts = self._deduplicate_new_concepts(all_new_concepts)

            # Phase 2: Cross-chunk relationship detection
            logger.info("Phase 2: Cross-chunk relationship detection")
            cross_chunk_relationships = await self._detect_cross_chunk_relationships(
                all_entities, chunks
            )
            all_relationships.extend(cross_chunk_relationships)

            # Phase 3: Validate consolidated extraction against ontology
            # logger.info("Phase 3: Validating consolidated extraction against ontology")
            # validation_result = (
            #     await self.ontogpt_service.validate_extraction_against_ontology(
            #         entities=all_entities, relationships=all_relationships
            #     )
            # )

            # Phase 4: Auto-create mappings if enabled
            # mapping_result = None
            # if auto_create_mappings:
            #     logger.info("Phase 4: Auto-creating ontology mappings")
            #     mapping_result = await self._auto_create_mappings_from_extraction(
            #         entities=all_entities,
            #         relationships=all_relationships,
            #         user_id=user_id,
            #         confidence_threshold=confidence_threshold,
            #     )

            # Phase 5: Enrich ontology with new concepts
            # enrichment_result = None
            # if enrich_ontology and (all_new_concepts.get("classes") or all_new_concepts.get("properties")):
            #     logger.info("Phase 5: Enriching ontology with new concepts")
            #     enrichment_result = await self.ontogpt_service.enrich_ontology_with_new_concepts(
            #         all_new_concepts, user_id
            #     )

            # Phase 6: Save extraction results
            logger.info("Phase 6: Saving extraction results")
            extraction_metadata = {
                "chunk_count": len(chunks),
                "chunk_results": chunk_results,
                # "validation": validation_result,
                # "mapping_creation": mapping_result,
                # "ontology_enrichment": enrichment_result,
                "options": options,
                "domain": domain,
                "language": "vietnamese",
                "processing_pipeline": "chunked" if use_chunking else "single"
            }

            extraction_id = await self.entity_service.save_extraction_results(
                text=text,
                entities=all_entities,
                extraction_metadata=extraction_metadata,
                user_id=user_id,
            )

            # Save relationships
            await self.relationship_service.save_extraction_results(
                relationships=all_relationships, extraction_result_id=extraction_id
            )

            # Phase 7: Generate completion suggestions
            # logger.info("Phase 7: Generating completion suggestions")
            # completion_suggestions = (
            #     await self.ontogpt_service.suggest_knowledge_graph_completion(
            #         extraction_result_id=extraction_id, domain=domain
            #     )
            # )

            # Compile final results
            final_result = {
                "extraction_id": extraction_id,
                "success": True,
                "summary": {
                    "text_length": len(text),
                    "chunks_processed": len(chunks),
                    "entities_extracted": len(all_entities),
                    "relationships_extracted": len(all_relationships),
                    "entities_mapped": len(
                        [e for e in all_entities if e.get("is_mapped", False)]
                    ),
                    "relationships_mapped": len(
                        [r for r in all_relationships if r.get("is_mapped", False)]
                    ),
                    # "validation_score": validation_result.get("overall_score", 0.0),
                    "new_classes_found": len(all_new_concepts.get("classes", [])),
                    "new_properties_found": len(all_new_concepts.get("properties", [])),
                },
                "entities": all_entities,
                "relationships": all_relationships,
                # "validation": validation_result,
                # "ontology_enrichment": enrichment_result,
                "new_concepts": all_new_concepts,
                # "mapping_creation": mapping_result,
                # "completion_suggestions": completion_suggestions,
                "metadata": extraction_metadata,
            }

            logger.info("Vietnamese knowledge extraction pipeline completed successfully")
            return final_result

        except Exception as e:
            logger.error(f"Error in Vietnamese knowledge extraction pipeline: {e}")
            return {
                "success": False,
                "error": str(e),
                "entities": [],
                "relationships": [],
                "extraction_id": None,
            }

    async def _process_single_chunk(
        self,
        chunk_text: str,
        domain: Optional[str],
        user_id: Optional[str],
        options: Dict[str, Any],
        chunk_index: int
    ) -> Dict[str, Any]:
        """
        Process a single chunk of text through the extraction pipeline
        """
        try:
            # use_ontogpt = options.get("use_ontogpt", True)
            enrich_ontology = options.get("enrich_ontology", True)

            # Phase 1: Extract entities from chunk
            entity_result = await self.entity_service.extract_entities(
                text=chunk_text,
                domain=domain,
                use_ontogpt=False,
                enrich_ontology=enrich_ontology,
                user_id=user_id,
            )

            entities = entity_result.get("entities", [])

            logger.info(
                    f"Chunk {chunk_index} entity extraction complete: {len(entities)} entities found"
                                )

            # Phase 2: Extract relationships from chunk
            relationship_result = await self.relationship_service.extract_relationships(
                text=chunk_text,
                entities=entities,
                domain=domain,
                use_ontogpt=False,
                enrich_ontology=enrich_ontology,
                user_id=user_id,
            )

            relationships = relationship_result.get("relationships", [])

            # Combine new concepts from both extractions

            logger.info(
                    f"Chunk {chunk_index} relationship extraction complete: {len(relationships)} relationships found"
                                )
            new_concepts = {"classes": [], "properties": []}
            
            entity_new_concepts = entity_result.get("new_concepts", {})
            if entity_new_concepts:
                new_concepts["classes"].extend(entity_new_concepts.get("classes", []))
                new_concepts["properties"].extend(entity_new_concepts.get("properties", []))
            
            relationship_new_concepts = relationship_result.get("new_concepts", {})
            if relationship_new_concepts:
                new_concepts["classes"].extend(relationship_new_concepts.get("classes", []))
                new_concepts["properties"].extend(relationship_new_concepts.get("properties", []))

            return {
                "success": True,
                "entities": entities,
                "relationships": relationships,
                "new_concepts": new_concepts,
                "entity_extraction": entity_result,
                "relationship_extraction": relationship_result,
                "chunk_index": chunk_index
            }

        except Exception as e:
            logger.error(f"Error processing chunk {chunk_index}: {e}")
            return {
                "success": False,
                "error": str(e),
                "entities": [],
                "relationships": [],
                "chunk_index": chunk_index
            }

    async def _deduplicate_entities(
        self, 
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate entities across chunks using Vietnamese-aware similarity
        """
        unique_entities = []
        seen_entities = set()
        
        for entity in entities:
            entity_text = entity.get("text", "").lower().strip()
            entity_type = entity.get("entity_type", "")
            
            # Create a normalized key for Vietnamese text
            normalized_text = self._normalize_vietnamese_text(entity_text)
            entity_key = f"{normalized_text}:{entity_type}"
            
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                unique_entities.append(entity)
            else:
                # If duplicate found, keep the one with higher confidence
                for i, existing_entity in enumerate(unique_entities):
                    existing_text = self._normalize_vietnamese_text(
                        existing_entity.get("text", "").lower()
                    )
                    existing_type = existing_entity.get("entity_type", "")
                    
                    if (existing_text == normalized_text and 
                        existing_type == entity_type):
                        # Compare confidence scores
                        existing_confidence = existing_entity.get("confidence", 0)
                        new_confidence = entity.get("confidence", 0)
                        
                        if new_confidence > existing_confidence:
                            unique_entities[i] = entity
                        break
        
        logger.info(f"Deduplicated entities: {len(entities)} -> {len(unique_entities)}")
        return unique_entities

    async def _deduplicate_relationships(
        self, 
        relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate relationships across chunks using Vietnamese-aware similarity
        """
        unique_relationships = []
        seen_relationships = set()
        
        for relationship in relationships:
            source_entity = self._normalize_vietnamese_text(
                relationship.get("source_entity", "").lower()
            )
            target_entity = self._normalize_vietnamese_text(
                relationship.get("target_entity", "").lower()
            )
            relationship_type = relationship.get("relationship_type", "")
            
            rel_key = f"{source_entity}:{target_entity}:{relationship_type}"
            
            if rel_key not in seen_relationships:
                seen_relationships.add(rel_key)
                unique_relationships.append(relationship)
            else:
                # Keep the one with higher confidence
                for i, existing_rel in enumerate(unique_relationships):
                    existing_source = self._normalize_vietnamese_text(
                        existing_rel.get("source_entity", "").lower()
                    )
                    existing_target = self._normalize_vietnamese_text(
                        existing_rel.get("target_entity", "").lower()
                    )
                    existing_type = existing_rel.get("relationship_type", "")
                    
                    if (existing_source == source_entity and 
                        existing_target == target_entity and 
                        existing_type == relationship_type):
                        # Compare confidence scores
                        existing_confidence = existing_rel.get("confidence", 0)
                        new_confidence = relationship.get("confidence", 0)
                        
                        if new_confidence > existing_confidence:
                            unique_relationships[i] = relationship
                        break
        
        logger.info(f"Deduplicated relationships: {len(relationships)} -> {len(unique_relationships)}")
        return unique_relationships

    def _normalize_vietnamese_text(self, text: str) -> str:
        """
        Normalize Vietnamese text for comparison
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common Vietnamese prefixes/suffixes for person names
        text = re.sub(r'^(ông|bà|anh|chị|em|cô|chú|bác)\s+', '', text)
        text = re.sub(r'\s+(ạ|à|ơi|nhé)$', '', text)
        
        # Normalize some common variations
        text = text.replace('tk', 'tài khoản')
        text = text.replace('nh', 'ngân hàng')
        text = text.replace('kh', 'khách hàng')
        
        return text

    def _deduplicate_new_concepts(
        self, 
        new_concepts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deduplicate new concepts found across chunks
        """
        # Deduplicate classes
        unique_classes = []
        seen_class_labels = set()
        
        for cls in new_concepts.get("classes", []):
            label = cls.get("label", "").lower()
            if label not in seen_class_labels:
                seen_class_labels.add(label)
                unique_classes.append(cls)
        
        # Deduplicate properties
        unique_properties = []
        seen_property_labels = set()
        
        for prop in new_concepts.get("properties", []):
            label = prop.get("label", "").lower()
            if label not in seen_property_labels:
                seen_property_labels.add(label)
                unique_properties.append(prop)
        
        return {
            "classes": unique_classes,
            "properties": unique_properties
        }

    async def _detect_cross_chunk_relationships(
        self,
        all_entities: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect relationships that span across chunks (e.g., entity mentioned in multiple chunks)
        """
        cross_chunk_relationships = []
        
        # Group entities by normalized text
        entity_groups = {}
        for entity in all_entities:
            normalized_text = self._normalize_vietnamese_text(
                entity.get("text", "").lower()
            )
            if normalized_text not in entity_groups:
                entity_groups[normalized_text] = []
            entity_groups[normalized_text].append(entity)
        
        # Find entities that appear in multiple chunks
        for normalized_text, entities in entity_groups.items():
            if len(entities) > 1:
                # These entities likely refer to the same real-world entity
                # Create co-reference relationships
                primary_entity = max(entities, key=lambda e: e.get("confidence", 0))
                
                for entity in entities:
                    if entity != primary_entity:
                        cross_chunk_relationships.append({
                            "source_entity": entity.get("text"),
                            "target_entity": primary_entity.get("text"),
                            "relationship_type": "same_as",
                            "confidence": 0.9,
                            "extraction_method": "cross_chunk_coreference",
                            "is_mapped": False
                        })
        
        # Additional cross-chunk relationship detection based on Vietnamese banking patterns
        # For example, if person X appears in chunk 1 and account Y appears in chunk 2,
        # and there are contextual clues they are related
        
        logger.info(f"Detected {len(cross_chunk_relationships)} cross-chunk relationships")
        return cross_chunk_relationships

    async def _auto_create_mappings_from_extraction(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        confidence_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Automatically create ontology mappings for high-confidence extractions
        """
        try:
            supabase = await get_supabase()
            
            mappings_created = {
                "entity_mappings": 0,
                "relationship_mappings": 0,
                "errors": []
            }
            
            # Auto-map high-confidence entities
            for entity in entities:
                if (entity.get("confidence", 0) >= confidence_threshold and 
                    not entity.get("is_mapped", False)):
                    
                    # Get mapping suggestions
                    suggestions = await self.entity_service.get_entity_mapping_suggestions(
                        entity_text=entity.get("text", ""),
                        entity_type=entity.get("entity_type", ""),
                        max_suggestions=1
                    )
                    
                    if suggestions and suggestions[0].get("similarity_score", 0) >= confidence_threshold:
                        try:
                            # Update entity with mapping
                            entity["ontology_class_id"] = suggestions[0]["ontology_class_id"]
                            entity["is_mapped"] = True
                            mappings_created["entity_mappings"] += 1
                            
                        except Exception as e:
                            mappings_created["errors"].append(f"Error mapping entity: {str(e)}")
            
            # Auto-map high-confidence relationships
            for relationship in relationships:
                if (relationship.get("confidence", 0) >= confidence_threshold and 
                    not relationship.get("is_mapped", False)):
                    
                    # Get mapping suggestions
                    suggestions = await self.relationship_service.get_relationship_mapping_suggestions(
                        relationship_type=relationship.get("relationship_type", ""),
                        max_suggestions=1
                    )
                    
                    if suggestions and suggestions[0].get("similarity_score", 0) >= confidence_threshold:
                        try:
                            # Update relationship with mapping
                            relationship["ontology_property_id"] = suggestions[0]["ontology_property_id"]
                            relationship["is_mapped"] = True
                            mappings_created["relationship_mappings"] += 1
                            
                        except Exception as e:
                            mappings_created["errors"].append(f"Error mapping relationship: {str(e)}")
            
            logger.info(f"Auto-created mappings: {mappings_created['entity_mappings']} entities, {mappings_created['relationship_mappings']} relationships")
            return mappings_created
            
        except Exception as e:
            logger.error(f"Error in auto-creating mappings: {e}")
            return {"entity_mappings": 0, "relationship_mappings": 0, "errors": [str(e)]}

    async def enrich_ontology_from_extractions(
        self,
        extraction_result_ids: List[int],
        user_id: Optional[str] = None,
        auto_apply_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Enrich ontology based on multiple extraction results with Vietnamese concepts
        """
        try:
            logger.info(
                f"Starting ontology enrichment from {len(extraction_result_ids)} Vietnamese extractions"
            )

            supabase = await get_supabase()
            extraction_results = []

            # Get extraction results with entities and relationships
            for result_id in extraction_result_ids:
                response = (
                    await supabase.from_("extraction_results")
                    .select("*, kg_entities(*), kg_relationships(*)")
                    .eq("id", result_id)
                    .single()
                    .execute()
                )

                if response.data:
                    extraction_results.append(response.data)

            # Analyze patterns in Vietnamese banking data
            logger.info("Analyzing Vietnamese banking patterns for ontology extensions")
            extension_suggestions = await self._suggest_vietnamese_ontology_extensions(
                extraction_results=extraction_results
            )

            # Apply extensions
            logger.info("Applying Vietnamese ontology extensions")
            application_result = await self._apply_ontology_extensions(
                suggested_extensions=extension_suggestions,
                user_id=user_id,
                auto_apply_threshold=auto_apply_threshold,
            )

            # Generate coverage report
            logger.info("Generating coverage report")
            coverage_report = await self._get_vietnamese_ontology_coverage_report(
                extraction_result_ids=extraction_result_ids
            )

            enrichment_result = {
                "success": True,
                "suggestions": extension_suggestions,
                "applications": application_result,
                "coverage_report": coverage_report,
                "summary": {
                    "extractions_analyzed": len(extraction_results),
                    "classes_suggested": len(
                        extension_suggestions.get("suggested_classes", [])
                    ),
                    "properties_suggested": len(
                        extension_suggestions.get("suggested_properties", [])
                    ),
                    "classes_added": application_result.get("classes_added", 0),
                    "properties_added": application_result.get("properties_added", 0),
                    "pending_review": application_result.get("pending_review", 0),
                },
            }

            logger.info("Vietnamese ontology enrichment completed successfully")
            return enrichment_result

        except Exception as e:
            logger.error(f"Error in Vietnamese ontology enrichment: {e}")
            return {"success": False, "error": str(e)}

    async def _suggest_vietnamese_ontology_extensions(
        self,
        extraction_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Suggest Vietnamese-specific ontology extensions based on extraction patterns
        """
        try:
            # Analyze frequent unmapped entities and relationships
            unmapped_entities = {}
            unmapped_relationships = {}
            
            for result in extraction_results:
                entities = result.get("kg_entities", [])
                relationships = result.get("kg_relationships", [])
                
                # Count unmapped entities
                for entity in entities:
                    if not entity.get("ontology_class_id"):
                        entity_text = entity.get("entity_text", "").lower()
                        unmapped_entities[entity_text] = unmapped_entities.get(entity_text, 0) + 1
                
                # Count unmapped relationships
                for rel in relationships:
                    if not rel.get("ontology_property_id"):
                        rel_type = rel.get("properties", {}).get("relationship_type", "").lower()
                        if rel_type:
                            unmapped_relationships[rel_type] = unmapped_relationships.get(rel_type, 0) + 1
            
            # Suggest new classes for frequent unmapped entities
            suggested_classes = []
            frequency_threshold = max(1, len(extraction_results) // 4)  # Appear in at least 25% of extractions
            
            for entity_text, count in unmapped_entities.items():
                if count >= frequency_threshold:
                    # Determine Vietnamese entity category
                    category = self._categorize_vietnamese_entity(entity_text)
                    if category:
                        suggested_classes.append({
                            "uri": f"http://vietnamese.banking.ontology/{category}/{entity_text.replace(' ', '_')}",
                            "label": entity_text.title(),
                            "description": f"Khái niệm {category} trong ngân hàng Việt Nam: {entity_text}",
                            "domain": "banking",
                            "frequency": count,
                            "confidence": min(0.9, count / len(extraction_results)),
                            "vietnamese_category": category
                        })
            
            # Suggest new properties for frequent unmapped relationships
            suggested_properties = []
            for rel_type, count in unmapped_relationships.items():
                if count >= frequency_threshold:
                    suggested_properties.append({
                        "uri": f"http://vietnamese.banking.ontology/property/{rel_type.replace(' ', '_')}",
                        "label": rel_type.title(),
                        "description": f"Mối quan hệ trong ngân hàng Việt Nam: {rel_type}",
                        "property_type": "object",
                        "domain": "banking",
                        "frequency": count,
                        "confidence": min(0.9, count / len(extraction_results))
                    })
            
            return {
                "suggested_classes": suggested_classes,
                "suggested_properties": suggested_properties,
                "analysis_metadata": {
                    "extraction_count": len(extraction_results),
                    "frequency_threshold": frequency_threshold,
                    "unmapped_entity_count": len(unmapped_entities),
                    "unmapped_relationship_count": len(unmapped_relationships)
                }
            }
            
        except Exception as e:
            logger.error(f"Error suggesting Vietnamese ontology extensions: {e}")
            return {"suggested_classes": [], "suggested_properties": []}

    def _categorize_vietnamese_entity(self, entity_text: str) -> Optional[str]:
        """
        Categorize Vietnamese entity text into banking categories
        """
        entity_lower = entity_text.lower()
        
        # Vietnamese banking categories
        if any(word in entity_lower for word in ['ngân hàng', 'nh', 'bank']):
            return 'Bank'
        elif any(word in entity_lower for word in ['tài khoản', 'tk', 'account']):
            return 'Account'
        elif any(word in entity_lower for word in ['thẻ', 'card', 'visa', 'master']):
            return 'Card'
        elif any(word in entity_lower for word in ['giao dịch', 'transaction', 'chuyển khoản']):
            return 'Transaction'
        elif any(word in entity_lower for word in ['vay', 'loan', 'cho vay']):
            return 'Loan'
        elif any(word in entity_lower for word in ['tiết kiệm', 'savings', 'gửi tiết kiệm']):
            return 'Savings'
        elif any(word in entity_lower for word in ['bảo hiểm', 'insurance']):
            return 'Insurance'
        elif any(word in entity_lower for word in ['chi nhánh', 'phòng giao dịch', 'branch']):
            return 'Branch'
        elif re.match(r'^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+', entity_text):
            return 'Person'
        elif re.match(r'\d+.*(?:vnd|đồng|usd|triệu|tỷ)', entity_lower):
            return 'Money'
        elif re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', entity_text):
            return 'Date'
        else:
            return None

    async def _apply_ontology_extensions(
        self,
        suggested_extensions: Dict[str, Any],
        user_id: Optional[str] = None,
        auto_apply_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Apply suggested ontology extensions to the database
        """
        try:
            supabase = await get_supabase()
            
            results = {
                "classes_added": 0,
                "properties_added": 0,
                "pending_review": 0,
                "errors": []
            }
            
            # Apply high-confidence class suggestions
            for suggested_class in suggested_extensions.get("suggested_classes", []):
                try:
                    confidence = suggested_class.get("confidence", 0)
                    
                    if confidence >= auto_apply_threshold:
                        class_data = {
                            "uri": suggested_class["uri"],
                            "label": suggested_class["label"],
                            "description": suggested_class["description"],
                            "domain": suggested_class.get("domain"),
                            "is_custom": True,
                            "properties": {
                                "vietnamese_category": suggested_class.get("vietnamese_category"),
                                "frequency": suggested_class.get("frequency"),
                                "auto_created": True,
                                "confidence": confidence
                            }
                        }
                        
                        response = await supabase.from_("ontology_classes").insert(class_data).execute()
                        if response.data:
                            results["classes_added"] += 1
                            logger.info(f"Auto-added Vietnamese ontology class: {suggested_class['label']}")
                    else:
                        results["pending_review"] += 1
                        
                except Exception as e:
                    error_msg = f"Error adding class {suggested_class.get('label', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Apply high-confidence property suggestions
            for suggested_property in suggested_extensions.get("suggested_properties", []):
                try:
                    confidence = suggested_property.get("confidence", 0)
                    
                    if confidence >= auto_apply_threshold:
                        property_data = {
                            "uri": suggested_property["uri"],
                            "label": suggested_property["label"],
                            "description": suggested_property["description"],
                            "property_type": suggested_property.get("property_type", "object"),
                            "domain": suggested_property.get("domain"),
                            "is_custom": True
                        }
                        
                        response = await supabase.from_("ontology_properties").insert(property_data).execute()
                        if response.data:
                            results["properties_added"] += 1
                            logger.info(f"Auto-added Vietnamese ontology property: {suggested_property['label']}")
                    else:
                        results["pending_review"] += 1
                        
                except Exception as e:
                    error_msg = f"Error adding property {suggested_property.get('label', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Error applying ontology extensions: {e}")
            return {"classes_added": 0, "properties_added": 0, "pending_review": 0, "errors": [str(e)]}

    async def _get_vietnamese_ontology_coverage_report(
        self,
        extraction_result_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Generate coverage report for Vietnamese ontology
        """
        try:
            supabase = await get_supabase()
            
            # Get all entities and relationships from the extractions
            total_entities = 0
            mapped_entities = 0
            total_relationships = 0
            mapped_relationships = 0
            
            for result_id in extraction_result_ids:
                # Count entities
                entities_response = await supabase.from_("kg_entities").select("ontology_class_id").execute()
                total_entities += len(entities_response.data)
                mapped_entities += len([e for e in entities_response.data if e.get("ontology_class_id")])
                
                # Count relationships
                relationships_response = await supabase.from_("kg_relationships").select("ontology_property_id").execute()
                total_relationships += len(relationships_response.data)
                mapped_relationships += len([r for r in relationships_response.data if r.get("ontology_property_id")])
            
            # Calculate coverage percentages
            entity_coverage = (mapped_entities / total_entities * 100) if total_entities > 0 else 0
            relationship_coverage = (mapped_relationships / total_relationships * 100) if total_relationships > 0 else 0
            
            return {
                "entity_coverage": {
                    "total": total_entities,
                    "mapped": mapped_entities,
                    "percentage": entity_coverage
                },
                "relationship_coverage": {
                    "total": total_relationships,
                    "mapped": mapped_relationships,
                    "percentage": relationship_coverage
                },
                "overall_coverage": (entity_coverage + relationship_coverage) / 2,
                "recommendations": self._generate_coverage_recommendations(
                    entity_coverage, relationship_coverage
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating coverage report: {e}")
            return {}

    def _generate_coverage_recommendations(
        self,
        entity_coverage: float,
        relationship_coverage: float
    ) -> List[str]:
        """
        Generate recommendations based on coverage percentages
        """
        recommendations = []
        
        if entity_coverage < 70:
            recommendations.append(
                "Độ bao phủ thực thể thấp. Cần mở rộng ontology với các khái niệm thực thể mới trong ngân hàng Việt Nam."
            )
        
        if relationship_coverage < 60:
            recommendations.append(
                "Độ bao phủ mối quan hệ thấp. Cần bổ sung các loại mối quan hệ phổ biến trong ngành ngân hàng Việt Nam."
            )
        
        if entity_coverage > 90 and relationship_coverage > 90:
            recommendations.append(
                "Ontology có độ bao phủ tốt cho dữ liệu ngân hàng Việt Nam."
            )
        
        return recommendations

    async def complete_knowledge_graph(
        self,
        extraction_result_id: int,
        user_id: Optional[str] = None,
        auto_apply_suggestions: bool = False,
    ) -> Dict[str, Any]:
        """
        Complete knowledge graph by suggesting and optionally applying missing elements
        """
        try:
            logger.info(
                f"Starting Vietnamese knowledge graph completion for extraction {extraction_result_id}"
            )

            # Get completion suggestions
            suggestions = await self.ontogpt_service.suggest_knowledge_graph_completion(
                extraction_result_id=extraction_result_id
            )

            completion_result = {
                "success": True,
                "extraction_result_id": extraction_result_id,
                "suggestions": suggestions,
                "applied_suggestions": None,
            }

            if auto_apply_suggestions:
                logger.info("Auto-applying Vietnamese completion suggestions")
                applied_result = await self._apply_completion_suggestions(
                    extraction_result_id, suggestions, user_id
                )
                completion_result["applied_suggestions"] = applied_result

            logger.info("Vietnamese knowledge graph completion finished successfully")
            return completion_result

        except Exception as e:
            logger.error(f"Error in Vietnamese knowledge graph completion: {e}")
            return {
                "success": False,
                "error": str(e),
                "extraction_result_id": extraction_result_id,
            }

    async def _apply_completion_suggestions(
        self,
        extraction_result_id: int,
        suggestions: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply completion suggestions to the knowledge graph
        """
        try:
            supabase = await get_supabase()
            applied_count = {"entities": 0, "relationships": 0, "errors": []}

            # Apply missing entity suggestions
            for entity_suggestion in suggestions.get("missing_entities", []):
                if (entity_suggestion.get("priority") == "high" and 
                    entity_suggestion.get("confidence", 0) > 0.8):
                    
                    try:
                        entity_data = {
                            "entity_text": entity_suggestion["suggested_text"],
                            "ontology_class_id": entity_suggestion.get("suggested_ontology_class_id"),
                            "confidence": entity_suggestion.get("confidence"),
                            "extraction_confidence": entity_suggestion.get("confidence"),
                            "is_verified": False,
                            "validation_status": "auto_suggested",
                            "created_by": user_id,
                            "properties": {
                                "auto_suggested": True,
                                "reason": entity_suggestion.get("reason"),
                                "suggestion_source": "vietnamese_completion"
                            }
                        }

                        await supabase.from_("kg_entities").insert(entity_data).execute()
                        applied_count["entities"] += 1

                    except Exception as e:
                        applied_count["errors"].append(f"Error applying entity suggestion: {str(e)}")

            # Apply missing relationship suggestions
            for rel_suggestion in suggestions.get("missing_relationships", []):
                if (rel_suggestion.get("priority") == "high" and 
                    rel_suggestion.get("confidence", 0) > 0.8):
                    
                    try:
                        # Find source and target entity IDs
                        source_entity_id = await self._find_entity_by_text(
                            rel_suggestion.get("source_entity", "")
                        )
                        target_entity_id = await self._find_entity_by_text(
                            rel_suggestion.get("target_entity", "")
                        )

                        if source_entity_id and target_entity_id:
                            relationship_data = {
                                "source_entity_id": source_entity_id,
                                "target_entity_id": target_entity_id,
                                "ontology_property_id": rel_suggestion.get("suggested_ontology_property_id"),
                                "confidence": rel_suggestion.get("confidence"),
                                "extraction_confidence": rel_suggestion.get("confidence"),
                                "is_verified": False,
                                "validation_status": "auto_suggested",
                                "properties": {
                                    "auto_suggested": True,
                                    "reason": rel_suggestion.get("reason"),
                                    "relationship_type": rel_suggestion.get("suggested_type"),
                                    "suggestion_source": "vietnamese_completion"
                                }
                            }

                            await supabase.from_("kg_relationships").insert(relationship_data).execute()
                            applied_count["relationships"] += 1

                    except Exception as e:
                        applied_count["errors"].append(f"Error applying relationship suggestion: {str(e)}")

            return applied_count

        except Exception as e:
            logger.error(f"Error applying completion suggestions: {e}")
            return {"entities": 0, "relationships": 0, "errors": [str(e)]}

    async def _find_entity_by_text(self, entity_text: str) -> Optional[str]:
        """
        Find entity ID by text with Vietnamese-aware matching
        """
        try:
            supabase = await get_supabase()
            
            # First try exact match
            response = await supabase.from_("kg_entities").select("id").eq("entity_text", entity_text).limit(1).execute()
            
            if response.data:
                return response.data[0]["id"]
            
            # Try normalized matching
            normalized_text = self._normalize_vietnamese_text(entity_text.lower())
            response = await supabase.from_("kg_entities").select("id, entity_text").execute()
            
            for entity in response.data:
                entity_normalized = self._normalize_vietnamese_text(entity["entity_text"].lower())
                if entity_normalized == normalized_text:
                    return entity["id"]
            
            return None
            
        except Exception as e:
            logger.warning(f"Error finding entity by text {entity_text}: {e}")
            return None

    async def batch_process_documents(
        self,
        documents: List[Dict[str, Any]],
        domain: Optional[str] = None,
        user_id: Optional[str] = None,
        batch_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process multiple Vietnamese documents in batch for knowledge extraction
        """
        try:
            options = batch_options or {}
            max_parallel = options.get("max_parallel", 3)  # Lower for Vietnamese processing
            enrich_after_batch = options.get("enrich_after_batch", True)

            logger.info(f"Starting batch processing of {len(documents)} Vietnamese documents")

            batch_results = []
            extraction_ids = []

            # Process documents in smaller chunks for Vietnamese
            import asyncio

            for i in range(0, len(documents), max_parallel):
                chunk = documents[i : i + max_parallel]

                # Process chunk in parallel
                tasks = []
                for doc in chunk:
                    task = self.extract_knowledge_pipeline(
                        text=doc["text"],
                        domain=domain,
                        user_id=user_id,
                        extraction_options=options.get("extraction_options", {}),
                    )
                    tasks.append(task)

                chunk_results = await asyncio.gather(*tasks, return_exceptions=True)

                for j, result in enumerate(chunk_results):
                    if isinstance(result, Exception):
                        batch_results.append(
                            {
                                "document_index": i + j,
                                "success": False,
                                "error": str(result),
                            }
                        )
                    else:
                        batch_results.append(
                            {
                                "document_index": i + j,
                                "success": result.get("success", False),
                                "extraction_id": result.get("extraction_id"),
                                "summary": result.get("summary", {}),
                            }
                        )

                        if result.get("extraction_id"):
                            extraction_ids.append(result["extraction_id"])

                logger.info(
                    f"Processed Vietnamese batch {i//max_parallel + 1}/{(len(documents) + max_parallel - 1)//max_parallel}"
                )

            # Enrich ontology if requested
            enrichment_result = None
            if enrich_after_batch and extraction_ids:
                logger.info("Enriching Vietnamese ontology from batch results")
                enrichment_result = await self.enrich_ontology_from_extractions(
                    extraction_result_ids=extraction_ids, user_id=user_id
                )

            # Calculate batch statistics
            successful_extractions = [
                r for r in batch_results if r.get("success", False)
            ]
            total_entities = sum(
                [
                    r.get("summary", {}).get("entities_extracted", 0)
                    for r in successful_extractions
                ]
            )
            total_relationships = sum(
                [
                    r.get("summary", {}).get("relationships_extracted", 0)
                    for r in successful_extractions
                ]
            )

            final_result = {
                "success": True,
                "language": "vietnamese",
                "batch_summary": {
                    "total_documents": len(documents),
                    "successful_extractions": len(successful_extractions),
                    "failed_extractions": len(documents) - len(successful_extractions),
                    "total_entities_extracted": total_entities,
                    "total_relationships_extracted": total_relationships,
                    "extraction_ids": extraction_ids,
                },
                "individual_results": batch_results,
                "ontology_enrichment": enrichment_result,
            }

            logger.info("Vietnamese batch processing completed successfully")
            return final_result

        except Exception as e:
            logger.error(f"Error in Vietnamese batch processing: {e}")
            return {
                "success": False,
                "error": str(e),
                "batch_summary": {
                    "total_documents": len(documents),
                    "successful_extractions": 0,
                },
            }

    async def analyze_extraction_quality(
        self, extraction_result_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Analyze quality of Vietnamese extractions across multiple results
        """
        try:
            logger.info(
                f"Analyzing Vietnamese extraction quality for {len(extraction_result_ids)} results"
            )

            supabase = await get_supabase()

            # Collect extraction data
            all_extractions = []
            for result_id in extraction_result_ids:
                response = (
                    await supabase.from_("extraction_results")
                    .select("*, kg_entities(*), kg_relationships(*)")
                    .eq("id", result_id)
                    .single()
                    .execute()
                )

                if response.data:
                    all_extractions.append(response.data)

            # Calculate Vietnamese-specific quality metrics
            total_entities = sum([len(e.get("kg_entities", [])) for e in all_extractions])
            total_relationships = sum(
                [len(e.get("kg_relationships", [])) for e in all_extractions]
            )

            mapped_entities = sum(
                [
                    len(
                        [
                            ent
                            for ent in e.get("kg_entities", [])
                            if ent.get("ontology_class_id")
                        ]
                    )
                    for e in all_extractions
                ]
            )

            mapped_relationships = sum(
                [
                    len(
                        [
                            rel
                            for rel in e.get("kg_relationships", [])
                            if rel.get("ontology_property_id")
                        ]
                    )
                    for e in all_extractions
                ]
            )

            # Calculate confidence distributions
            entity_confidences = []
            relationship_confidences = []

            for extraction in all_extractions:
                entity_confidences.extend(
                    [e.get("confidence", 0) for e in extraction.get("kg_entities", [])]
                )
                relationship_confidences.extend(
                    [
                        r.get("confidence", 0)
                        for r in extraction.get("kg_relationships", [])
                    ]
                )

            import statistics

            quality_report = {
                "language": "vietnamese",
                "summary": {
                    "total_extractions": len(all_extractions),
                    "total_entities": total_entities,
                    "total_relationships": total_relationships,
                    "mapping_coverage": {
                        "entities_mapped_percent": (
                            (mapped_entities / total_entities * 100)
                            if total_entities > 0
                            else 0
                        ),
                        "relationships_mapped_percent": (
                            (mapped_relationships / total_relationships * 100)
                            if total_relationships > 0
                            else 0
                        ),
                    },
                },
                "confidence_analysis": {
                    "entity_confidence": {
                        "mean": (
                            statistics.mean(entity_confidences)
                            if entity_confidences
                            else 0
                        ),
                        "median": (
                            statistics.median(entity_confidences)
                            if entity_confidences
                            else 0
                        ),
                        "std_dev": (
                            statistics.stdev(entity_confidences)
                            if len(entity_confidences) > 1
                            else 0
                        ),
                        "min": min(entity_confidences) if entity_confidences else 0,
                        "max": max(entity_confidences) if entity_confidences else 0,
                    },
                    "relationship_confidence": {
                        "mean": (
                            statistics.mean(relationship_confidences)
                            if relationship_confidences
                            else 0
                        ),
                        "median": (
                            statistics.median(relationship_confidences)
                            if relationship_confidences
                            else 0
                        ),
                        "std_dev": (
                            statistics.stdev(relationship_confidences)
                            if len(relationship_confidences) > 1
                            else 0
                        ),
                        "min": (
                            min(relationship_confidences)
                            if relationship_confidences
                            else 0
                        ),
                        "max": (
                            max(relationship_confidences)
                            if relationship_confidences
                            else 0
                        ),
                    },
                },
                "vietnamese_specific_metrics": await self._analyze_vietnamese_specific_quality(all_extractions),
                "recommendations": [],
            }

            # Generate Vietnamese-specific quality recommendations
            recommendations = self._generate_vietnamese_quality_recommendations(quality_report)
            quality_report["recommendations"] = recommendations

            logger.info("Vietnamese extraction quality analysis completed")
            return quality_report

        except Exception as e:
            logger.error(f"Error in Vietnamese extraction quality analysis: {e}")
            return {"success": False, "error": str(e)}

    async def _analyze_vietnamese_specific_quality(
        self, 
        all_extractions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze Vietnamese-specific quality metrics
        """
        vietnamese_entities = []
        vietnamese_relationships = []
        
        for extraction in all_extractions:
            for entity in extraction.get("kg_entities", []):
                entity_text = entity.get("entity_text", "")
                if self._is_vietnamese_text(entity_text):
                    vietnamese_entities.append(entity)
            
            for rel in extraction.get("kg_relationships", []):
                rel_props = rel.get("properties", {})
                if (rel_props.get("source_entity_text") and 
                    self._is_vietnamese_text(rel_props.get("source_entity_text", ""))):
                    vietnamese_relationships.append(rel)
        
        # Calculate Vietnamese-specific metrics
        vietnamese_entity_count = len(vietnamese_entities)
        vietnamese_relationship_count = len(vietnamese_relationships)
        
        # Vietnamese entity categories
        vietnamese_categories = {}
        for entity in vietnamese_entities:
            category = self._categorize_vietnamese_entity(entity.get("entity_text", ""))
            if category:
                vietnamese_categories[category] = vietnamese_categories.get(category, 0) + 1
        
        return {
            "vietnamese_entity_count": vietnamese_entity_count,
            "vietnamese_relationship_count": vietnamese_relationship_count,
            "vietnamese_entity_categories": vietnamese_categories,
            "vietnamese_text_percentage": (
                vietnamese_entity_count / max(1, vietnamese_entity_count) * 100
            )
        }

    def _is_vietnamese_text(self, text: str) -> bool:
        """
        Check if text contains Vietnamese characters
        """
        vietnamese_chars = "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
        return any(char in text.lower() for char in vietnamese_chars)

    def _generate_vietnamese_quality_recommendations(
        self, 
        quality_report: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate Vietnamese-specific quality recommendations
        """
        recommendations = []
        
        entity_mapping_percent = quality_report["summary"]["mapping_coverage"]["entities_mapped_percent"]
        relationship_mapping_percent = quality_report["summary"]["mapping_coverage"]["relationships_mapped_percent"]
        
        if entity_mapping_percent < 70:
            recommendations.append({
                "type": "vietnamese_entity_mapping",
                "priority": "high",
                "description": f"Độ bao phủ mapping thực thể tiếng Việt là {entity_mapping_percent:.1f}%. Cần mở rộng ontology với các khái niệm ngân hàng Việt Nam.",
                "suggested_actions": [
                    "Thêm các loại thực thể phổ biến trong ngân hàng Việt Nam",
                    "Tạo mapping cho các thuật ngữ tiếng Việt",
                    "Sử dụng từ điển thuật ngữ ngân hàng Việt Nam"
                ]
            })
        
        if relationship_mapping_percent < 60:
            recommendations.append({
                "type": "vietnamese_relationship_mapping",
                "priority": "high",
                "description": f"Độ bao phủ mapping mối quan hệ tiếng Việt là {relationship_mapping_percent:.1f}%. Cần bổ sung các loại mối quan hệ trong ngân hàng Việt Nam.",
                "suggested_actions": [
                    "Định nghĩa các mối quan hệ phổ biến trong ngân hàng Việt Nam",
                    "Tạo mapping cho các cụm từ chỉ quan hệ tiếng Việt",
                    "Sử dụng pattern matching cho quan hệ tiếng Việt"
                ]
            })
        
        vietnamese_metrics = quality_report.get("vietnamese_specific_metrics", {})
        vietnamese_percentage = vietnamese_metrics.get("vietnamese_text_percentage", 0)
        
        if vietnamese_percentage > 80:
            recommendations.append({
                "type": "vietnamese_processing_optimization",
                "priority": "medium",
                "description": f"Văn bản chủ yếu là tiếng Việt ({vietnamese_percentage:.1f}%). Nên tối ưu hóa cho xử lý tiếng Việt.",
                "suggested_actions": [
                    "Sử dụng specialized Vietnamese NLP tools",
                    "Áp dụng Vietnamese-specific chunking strategies",
                    "Tối ưu hóa pattern matching cho tiếng Việt"
                ]
            })
        
        return recommendations
