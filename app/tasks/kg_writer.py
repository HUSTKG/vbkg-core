from typing import Any, Dict, List, Optional

from app.core.supabase import get_supabase
from app.tasks.executors import StepLogger
from app.utils.neo4j import get_neo4j_driver


class KnowledgeGraphWriterTask:
    """
    Task for writing knowledge graph to various formats with Vietnamese support
    Now focuses on Neo4j sync and export formats since entities/relationships are already in Supabase
    """

    def __init__(self, logger: Optional[StepLogger] = None):
        self.logger = logger

    async def write_knowledge_graph(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        graph_format: str = "neo4j",
        batch_size: int = 1000,
        validate_before_write: bool = True,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Write knowledge graph to specified format
        
        Since entities and relationships are now saved in Supabase during extraction,
        this method focuses on syncing to Neo4j and exporting to other formats

        Args:
            entities: List of entities (should have database IDs from Supabase)
            relationships: List of relationships (should have database IDs from Supabase)
            graph_format: Target format (neo4j, rdf, cypher, json)
            batch_size: Batch size for writing
            validate_before_write: Whether to validate data before writing
            user_id: User performing the write operation

        Returns:
            Dictionary containing write results
        """
        try:
            await self.logger.info(
                f"Starting knowledge graph write to {graph_format} format with {len(entities)} entities and {len(relationships)} relationships"
            )

            # Validate data before writing if requested
            validation_result = None
            if validate_before_write:
                validation_result = await self._validate_graph_data(
                    entities, relationships
                )
                if not validation_result.get("is_valid", False):
                    return {
                        "success": False,
                        "error": "Graph data validation failed",
                        "validation_result": validation_result,
                    }

            # Write based on format
            write_result = {}
            if graph_format == "neo4j":
                write_result = await self._sync_to_neo4j(
                    user_id, entities, relationships, batch_size
                )
            elif graph_format == "rdf":
                write_result = await self._write_to_rdf(entities, relationships)
            elif graph_format == "cypher":
                write_result = await self._generate_cypher(entities, relationships)
            elif graph_format == "json":
                write_result = await self._write_to_json(entities, relationships)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported graph format: {graph_format}",
                }

            result = {
                "success": True,
                "graph_format": graph_format,
                "write_stats": {
                    "entities_processed": len(entities),
                    "relationships_processed": len(relationships),
                    "batch_size": batch_size,
                },
                "validation_result": validation_result,
                "write_result": write_result,
            }

            await self.logger.info(
                f"Knowledge graph write completed successfully to {graph_format}"
            )
            return result

        except Exception as e:
            await self.logger.error(f"Error in knowledge graph write: {e}")
            return {
                "success": False,
                "error": str(e),
                "graph_format": graph_format,
            }

    def _safe_get_text(self, obj: Dict[str, Any], *keys: str) -> str:
        """Safely get text value from object, handling None values"""
        for key in keys:
            value = obj.get(key)
            if value is not None:
                return str(value).strip()
        return ""

    async def _validate_graph_data(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate graph data before writing with Vietnamese-aware checks"""
        validation_result = {
            "is_valid": True,
            "validation_errors": [],
            "entity_issues": [],
            "relationship_issues": [],
            "vietnamese_specific_issues": [],
        }

        # Validate entities
        entity_texts = set()
        for i, entity in enumerate(entities):
            # Check required fields - use safe text extraction
            entity_text = self._safe_get_text(entity, "text", "entity_text")
            if not entity_text:
                validation_result["entity_issues"].append(
                    {
                        "index": i,
                        "issue": "Missing entity text",
                        "entity": entity.get("id", f"entity_{i}"),
                    }
                )
                validation_result["is_valid"] = False
                continue

            # Check for duplicate entity texts (Vietnamese-aware)
            normalized_text = self._normalize_vietnamese_text(entity_text)
            if normalized_text in entity_texts:
                validation_result["entity_issues"].append(
                    {
                        "index": i,
                        "issue": "Duplicate entity text",
                        "entity_text": entity_text,
                    }
                )
            else:
                entity_texts.add(normalized_text)

            # Vietnamese-specific validation
            vietnamese_issues = self._validate_vietnamese_entity(entity)
            if vietnamese_issues:
                validation_result["vietnamese_specific_issues"].extend(
                    vietnamese_issues
                )

        # Validate relationships
        for i, relationship in enumerate(relationships):
            # Check required fields - use safe text extraction
            source_entity = self._safe_get_text(relationship, "source_entity")
            target_entity = self._safe_get_text(relationship, "target_entity")
            source_entity_id = relationship.get("source_entity_id")
            target_entity_id = relationship.get("target_entity_id")

            if not source_entity and not source_entity_id:
                validation_result["relationship_issues"].append(
                    {
                        "index": i,
                        "issue": "Missing source entity",
                        "relationship": relationship.get("id", f"relationship_{i}"),
                    }
                )
                validation_result["is_valid"] = False

            if not target_entity and not target_entity_id:
                validation_result["relationship_issues"].append(
                    {
                        "index": i,
                        "issue": "Missing target entity",
                        "relationship": relationship.get("id", f"relationship_{i}"),
                    }
                )
                validation_result["is_valid"] = False

            # Check if source and target entities exist (only if we have entity text)
            if source_entity:
                source_exists = any(
                    self._entities_match(entity, source_entity) for entity in entities
                )
                if not source_exists:
                    validation_result["relationship_issues"].append(
                        {
                            "index": i,
                            "issue": "Source entity not found in entity list",
                            "source_entity": source_entity,
                        }
                    )

            if target_entity:
                target_exists = any(
                    self._entities_match(entity, target_entity) for entity in entities
                )
                if not target_exists:
                    validation_result["relationship_issues"].append(
                        {
                            "index": i,
                            "issue": "Target entity not found in entity list",
                            "target_entity": target_entity,
                        }
                    )

        # Count total validation errors
        total_errors = (
            len(validation_result["entity_issues"])
            + len(validation_result["relationship_issues"])
            + len(validation_result["vietnamese_specific_issues"])
        )
        validation_result["validation_errors"] = [
            f"Found {total_errors} validation issues"
        ]

        return validation_result

    def _validate_vietnamese_entity(
        self, entity: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate Vietnamese-specific entity requirements"""
        issues = []
        entity_text = self._safe_get_text(entity, "text", "entity_text")
        entity_type = self._safe_get_text(entity, "entity_type")

        if not entity_text:
            return issues

        # Check Vietnamese name patterns for Person entities
        if entity_type == "Person":
            if not self._is_valid_vietnamese_name(entity_text):
                issues.append(
                    {
                        "entity_text": entity_text,
                        "issue": "Invalid Vietnamese name pattern",
                        "suggestion": "Vietnamese names should have proper capitalization and structure",
                    }
                )

        # Check Vietnamese banking terms
        if entity_type == "Bank":
            if not self._is_valid_vietnamese_bank_name(entity_text):
                issues.append(
                    {
                        "entity_text": entity_text,
                        "issue": "Invalid Vietnamese bank name",
                        "suggestion": "Should contain 'ngân hàng' or be a recognized Vietnamese bank",
                    }
                )

        # Check Vietnamese money format
        if entity_type == "Money":
            if not self._is_valid_vietnamese_money_format(entity_text):
                issues.append(
                    {
                        "entity_text": entity_text,
                        "issue": "Invalid Vietnamese money format",
                        "suggestion": "Should use Vietnamese currency terms like 'đồng', 'triệu', 'tỷ'",
                    }
                )

        return issues

    def _is_valid_vietnamese_name(self, name: str) -> bool:
        """Check if text follows Vietnamese name patterns"""
        if not name or not isinstance(name, str):
            return False

        import re

        # Basic Vietnamese name pattern check
        vietnamese_name_pattern = r"^[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+(\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+)*$"
        return bool(re.match(vietnamese_name_pattern, name.strip()))

    def _is_valid_vietnamese_bank_name(self, bank_name: str) -> bool:
        """Check if text is a valid Vietnamese bank name"""
        if not bank_name or not isinstance(bank_name, str):
            return False

        bank_name_lower = bank_name.lower()
        vietnamese_banks = [
            "vietcombank",
            "bidv",
            "vietinbank",
            "acb",
            "techcombank",
            "mb bank",
            "vpbank",
            "tpbank",
            "seabank",
            "ngân hàng",
        ]
        return any(bank in bank_name_lower for bank in vietnamese_banks)

    def _is_valid_vietnamese_money_format(self, money_text: str) -> bool:
        """Check if text follows Vietnamese money format"""
        if not money_text or not isinstance(money_text, str):
            return False

        money_text_lower = money_text.lower()
        vietnamese_money_terms = ["đồng", "vnd", "vnđ", "triệu", "tỷ", "nghìn", "ngàn"]
        return any(term in money_text_lower for term in vietnamese_money_terms)

    def _entities_match(self, entity: Dict[str, Any], entity_text: str) -> bool:
        """Check if entity matches the given text with Vietnamese normalization"""
        if not entity_text:
            return False

        entity_actual_text = self._safe_get_text(entity, "text", "entity_text")
        if not entity_actual_text:
            return False

        return self._normalize_vietnamese_text(
            entity_actual_text
        ) == self._normalize_vietnamese_text(entity_text)

    def _normalize_vietnamese_text(self, text: str) -> str:
        """Normalize Vietnamese text for comparison"""
        if not text or not isinstance(text, str):
            return ""

        import re

        text = text.lower().strip()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common Vietnamese prefixes/suffixes
        text = re.sub(r"^(ông|bà|anh|chị|em|cô|chú|bác)\s+", "", text)
        text = re.sub(r"\s+(ạ|à|ơi|nhé)$", "", text)

        return text

    async def _sync_to_neo4j(
        self,
        user_id: Optional[str],
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        batch_size: int,
    ) -> Dict[str, Any]:
        """
        Sync entities and relationships to Neo4j (they are already in Supabase)
        Update Neo4j IDs in Supabase after successful creation
        """
        try:
            supabase = await get_supabase()
            neo4j_driver = get_neo4j_driver()
            
            sync_stats = {
                "entities_synced": 0,
                "relationships_synced": 0,
                "errors": [],
            }

            async with neo4j_driver.session() as session:
                # Sync entities in batches
                for i in range(0, len(entities), batch_size):
                    batch = entities[i : i + batch_size]

                    for entity in batch:
                        try:
                            # Check if entity already exists in Neo4j
                            entity_db_id = entity.get("id")
                            neo4j_id = entity.get("neo4j_id")
                            
                            if neo4j_id:
                                await self.logger.info(f"Entity {entity_db_id} already synced to Neo4j with ID {neo4j_id}")
                                sync_stats["entities_synced"] += 1
                                continue

                            # Safe text extraction
                            entity_text = self._safe_get_text(entity, "text", "entity_text")
                            if not entity_text:
                                sync_stats["errors"].append(
                                    f"Skipping entity with missing text: {entity_db_id}"
                                )
                                continue

                            entity_type = self._safe_get_text(entity, "entity_type") or "Entity"
                            properties = entity.get("properties", {})

                            # Add Vietnamese-specific properties
                            neo4j_properties = {
                                "entity_id": str(entity_db_id),
                                "entity_text": entity_text,
                                "entity_type": entity_type,
                                "confidence": float(entity.get("confidence", 0)),
                                "is_vietnamese": self._contains_vietnamese_characters(entity_text),
                                **{k: v for k, v in properties.items() if v is not None},
                            }

                            await self.logger.info(f"Syncing Neo4j entity: {neo4j_properties.get('entity_text', 'unknown')}")

                            # Use Vietnamese-safe entity type as label
                            safe_label = self._make_neo4j_safe_label(entity_type)

                            cypher_query = f"""
                            CREATE (e:`Entity`:`{safe_label}` $properties)
                            RETURN id(e) as neo4j_id
                            """

                            result = await session.run(
                                cypher_query, properties=neo4j_properties
                            )

                            record = await result.single()

                            if record:
                                new_neo4j_id = str(record["neo4j_id"])
                                
                                # Update Supabase with Neo4j ID
                                await supabase.from_("kg_entities").update(
                                    {"neo4j_id": new_neo4j_id}
                                ).eq("id", entity_db_id).execute()
                                
                                sync_stats["entities_synced"] += 1
                                await self.logger.info(f"Successfully synced entity {entity_db_id} to Neo4j with ID {new_neo4j_id}")

                        except Exception as e:
                            await self.logger.error(f"Error syncing entity {entity.get('id', 'unknown')}: {e}")
                            sync_stats["errors"].append(
                                f"Error syncing entity {entity.get('id', 'unknown')}: {str(e)}"
                            )

                # Sync relationships in batches
                for i in range(0, len(relationships), batch_size):
                    batch = relationships[i : i + batch_size]

                    for relationship in batch:
                        try:
                            # Check if relationship already exists in Neo4j
                            rel_db_id = relationship.get("id")
                            neo4j_id = relationship.get("neo4j_id")
                            
                            if neo4j_id:
                                await self.logger.info(f"Relationship {rel_db_id} already synced to Neo4j with ID {neo4j_id}")
                                sync_stats["relationships_synced"] += 1
                                continue

                            # Safe text extraction for relationships
                            source_entity_text = self._safe_get_text(relationship, "source_entity")
                            target_entity_text = self._safe_get_text(relationship, "target_entity")

                            if not source_entity_text or not target_entity_text:
                                sync_stats["errors"].append(
                                    f"Skipping relationship with missing entity text: {rel_db_id}"
                                )
                                continue

                            rel_type = self._safe_get_text(relationship, "relationship_type") or "RELATED_TO"
                            properties = relationship.get("properties", {})

                            # Add Vietnamese-specific properties
                            neo4j_properties = {
                                "relationship_id": str(rel_db_id),
                                "confidence": float(relationship.get("confidence", 0)),
                                "source_entity_text": source_entity_text,
                                "target_entity_text": target_entity_text,
                                **{k: v for k, v in properties.items() if v is not None},
                            }

                            # Use Vietnamese-safe relationship type
                            safe_rel_type = self._make_neo4j_safe_label(rel_type)

                            cypher_query = f"""
                            MATCH (source:Entity {{entity_text: $source_text}})
                            MATCH (target:Entity {{entity_text: $target_text}})
                            CREATE (source)-[r:`{safe_rel_type}` $properties]->(target)
                            RETURN id(r) as neo4j_id
                            """

                            result = await session.run(
                                cypher_query,
                                source_text=source_entity_text,
                                target_text=target_entity_text,
                                properties=neo4j_properties,
                            )
                            record = await result.single()

                            if record:
                                new_neo4j_id = str(record["neo4j_id"])
                                
                                # Update Supabase with Neo4j ID
                                await supabase.from_("kg_relationships").update(
                                    {"neo4j_id": new_neo4j_id}
                                ).eq("id", rel_db_id).execute()
                                
                                sync_stats["relationships_synced"] += 1
                                await self.logger.info(f"Successfully synced relationship {rel_db_id} to Neo4j with ID {new_neo4j_id}")

                        except Exception as e:
                            await self.logger.error(f"Error syncing relationship {relationship.get('id', 'unknown')}: {e}")
                            sync_stats["errors"].append(
                                f"Error syncing relationship {relationship.get('id', 'unknown')}: {str(e)}"
                            )

            await self.logger.info(f"Neo4j sync completed: {sync_stats}")
            return sync_stats

        except Exception as e:
            await self.logger.error(f"Error syncing to Neo4j: {e}")
            return {"error": str(e)}

    def _contains_vietnamese_characters(self, text: str) -> bool:
        """Check if text contains Vietnamese characters"""
        if not text or not isinstance(text, str):
            return False

        vietnamese_chars = (
            "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ"
        )
        return any(char in text.lower() for char in vietnamese_chars)

    def _make_neo4j_safe_label(self, label: str) -> str:
        """Make label safe for Neo4j by removing special characters"""
        if not label or not isinstance(label, str):
            return "UnknownLabel"

        import re

        # Replace spaces and special characters with underscores
        safe_label = re.sub(r"[^a-zA-Z0-9_]", "_", label)

        # Ensure it starts with a letter
        if safe_label and not safe_label[0].isalpha():
            safe_label = f"Label_{safe_label}"

        return safe_label or "UnknownLabel"

    async def _write_to_rdf(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Write knowledge graph to RDF format with Vietnamese support"""
        try:
            from rdflib import RDF, RDFS, Graph, Literal, Namespace, URIRef

            # Create RDF graph
            g = Graph()

            # Define Vietnamese banking namespace
            VN_BANKING = Namespace("http://vietnamese.banking.ontology/")
            g.bind("vnbank", VN_BANKING)

            write_stats = {
                "triples_created": 0,
                "entities_processed": 0,
                "relationships_processed": 0,
                "rdf_content": "",
            }

            # Add entities as RDF triples
            for entity in entities:
                entity_text = self._safe_get_text(entity, "text", "entity_text")
                if not entity_text:
                    continue

                entity_type = self._safe_get_text(entity, "entity_type") or "Entity"
                entity_id = entity.get("id", f"entity_{entity_text}")

                # Create URI for entity (Vietnamese-safe)
                entity_uri = URIRef(VN_BANKING[self._make_uri_safe(str(entity_id))])

                # Add type triple
                g.add((entity_uri, RDF.type, VN_BANKING[entity_type]))
                write_stats["triples_created"] += 1

                # Add label (Vietnamese text)
                g.add((entity_uri, RDFS.label, Literal(entity_text, lang="vi")))
                write_stats["triples_created"] += 1

                # Add properties
                properties = entity.get("properties", {})
                for prop_key, prop_value in properties.items():
                    if prop_value is not None:
                        prop_uri = VN_BANKING[self._make_uri_safe(prop_key)]
                        g.add((entity_uri, prop_uri, Literal(str(prop_value))))
                        write_stats["triples_created"] += 1

                write_stats["entities_processed"] += 1

            # Add relationships as RDF triples
            for relationship in relationships:
                source_text = self._safe_get_text(relationship, "source_entity")
                target_text = self._safe_get_text(relationship, "target_entity")
                rel_type = (
                    self._safe_get_text(relationship, "relationship_type")
                    or "relatedTo"
                )

                if not source_text or not target_text:
                    continue

                # Find entity URIs
                source_uri = None
                target_uri = None

                for entity in entities:
                    entity_text = self._safe_get_text(entity, "text", "entity_text")
                    if not entity_text:
                        continue

                    if self._normalize_vietnamese_text(
                        entity_text
                    ) == self._normalize_vietnamese_text(source_text):
                        source_uri = URIRef(
                            VN_BANKING[
                                self._make_uri_safe(
                                    str(entity.get("id", f"entity_{entity_text}"))
                                )
                            ]
                        )
                    if self._normalize_vietnamese_text(
                        entity_text
                    ) == self._normalize_vietnamese_text(target_text):
                        target_uri = URIRef(
                            VN_BANKING[
                                self._make_uri_safe(
                                    str(entity.get("id", f"entity_{entity_text}"))
                                )
                            ]
                        )

                if source_uri and target_uri:
                    # Add relationship triple
                    rel_uri = VN_BANKING[self._make_uri_safe(rel_type)]
                    g.add((source_uri, rel_uri, target_uri))
                    write_stats["triples_created"] += 1
                    write_stats["relationships_processed"] += 1

            # Serialize to RDF/XML with Vietnamese support
            rdf_content = g.serialize(format="xml", encoding="utf-8").decode("utf-8")
            write_stats["rdf_content"] = rdf_content

            return write_stats

        except Exception as e:
            await self.logger.error(f"Error writing to RDF: {e}")
            return {"error": str(e)}

    def _make_uri_safe(self, text: str) -> str:
        """Make text safe for URI by removing special characters"""
        if not text or not isinstance(text, str):
            return "unknown"

        import re

        # Replace spaces and special characters with underscores
        safe_text = re.sub(r"[^a-zA-Z0-9_]", "_", str(text))

        # Remove multiple consecutive underscores
        safe_text = re.sub(r"_+", "_", safe_text)

        # Remove leading/trailing underscores
        safe_text = safe_text.strip("_")

        return safe_text or "unknown"

    async def _generate_cypher(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate Cypher queries for the knowledge graph with Vietnamese support"""
        cypher_queries = []

        # Generate entity creation queries
        entity_queries = []
        for entity in entities:
            entity_text = self._safe_get_text(entity, "text", "entity_text")
            if not entity_text:
                continue

            entity_type = self._safe_get_text(entity, "entity_type") or "Entity"
            entity_id = entity.get("id", "")
            properties = entity.get("properties", {})

            # Build properties string with Vietnamese-safe escaping
            props_str = self._build_cypher_properties(
                {
                    "entity_id": str(entity_id),
                    "entity_text": entity_text,
                    "entity_type": entity_type,
                    "confidence": entity.get("confidence", 0),
                    **{k: v for k, v in properties.items() if v is not None},
                }
            )

            safe_label = self._make_neo4j_safe_label(entity_type)
            query = f"CREATE (e:`Entity`:`{safe_label}` {props_str})"
            entity_queries.append(query)

        # Generate relationship creation queries
        relationship_queries = []
        for relationship in relationships:
            source_text = self._safe_get_text(relationship, "source_entity")
            target_text = self._safe_get_text(relationship, "target_entity")
            rel_type = (
                self._safe_get_text(relationship, "relationship_type") or "RELATED_TO"
            )

            if not source_text or not target_text:
                continue

            properties = relationship.get("properties", {})

            # Build properties string
            props_str = self._build_cypher_properties(
                {
                    "relationship_id": str(relationship.get("id", "")),
                    "confidence": relationship.get("confidence", 0),
                    **{k: v for k, v in properties.items() if v is not None},
                }
            )

            safe_rel_type = self._make_neo4j_safe_label(rel_type)

            query = f"""
            MATCH (source:Entity {{entity_text: "{self._escape_cypher_string(source_text)}"}})
            MATCH (target:Entity {{entity_text: "{self._escape_cypher_string(target_text)}"}})
            CREATE (source)-[r:`{safe_rel_type}` {props_str}]->(target)
            """
            relationship_queries.append(query.strip())

        return {
            "entity_queries": entity_queries,
            "relationship_queries": relationship_queries,
            "all_queries": entity_queries + relationship_queries,
            "total_queries": len(entity_queries) + len(relationship_queries),
        }

    def _build_cypher_properties(self, properties: Dict[str, Any]) -> str:
        """Build Cypher properties string with Vietnamese-safe escaping"""
        if not properties:
            return "{}"

        prop_pairs = []
        for key, value in properties.items():
            if value is None:
                continue

            safe_key = self._make_neo4j_safe_label(key)

            if isinstance(value, str):
                escaped_value = self._escape_cypher_string(value)
                prop_pairs.append(f'{safe_key}: "{escaped_value}"')
            elif isinstance(value, (int, float)):
                prop_pairs.append(f"{safe_key}: {value}")
            elif isinstance(value, bool):
                prop_pairs.append(f"{safe_key}: {str(value).lower()}")
            else:
                escaped_value = self._escape_cypher_string(str(value))
                prop_pairs.append(f'{safe_key}: "{escaped_value}"')

        return "{" + ", ".join(prop_pairs) + "}"

    def _escape_cypher_string(self, text: str) -> str:
        """Escape string for Cypher with Vietnamese character support"""
        if not text or not isinstance(text, str):
            return ""

        # Escape quotes and backslashes
        text = text.replace("\\", "\\\\")
        text = text.replace('"', '\\"')
        return text

    async def _write_to_json(
        self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Write knowledge graph to JSON format with Vietnamese metadata"""
        json_graph = {
            "metadata": {
                "format": "vietnamese_banking_kg",
                "entity_count": len(entities),
                "relationship_count": len(relationships),
                "language": "vietnamese",
                "domain": "banking",
            },
            "entities": [],
            "relationships": [],
            "statistics": {
                "entity_types": {},
                "relationship_types": {},
                "vietnamese_entities": 0,
            },
        }

        # Process entities
        entity_types = {}
        vietnamese_entity_count = 0

        for entity in entities:
            entity_text = self._safe_get_text(entity, "text", "entity_text")
            if not entity_text:
                continue

            entity_type = self._safe_get_text(entity, "entity_type") or "Unknown"

            # Count entity types
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

            # Count Vietnamese entities
            if self._contains_vietnamese_characters(entity_text):
                vietnamese_entity_count += 1

            # Add to JSON with Vietnamese-specific metadata
            json_entity = {
                "id": entity.get("id", ""),
                "text": entity_text,
                "type": entity_type,
                "confidence": entity.get("confidence", 0),
                "properties": entity.get("properties", {}),
                "is_vietnamese": self._contains_vietnamese_characters(entity_text),
                "normalized_text": self._normalize_vietnamese_text(entity_text),
            }
            json_graph["entities"].append(json_entity)

        # Process relationships
        relationship_types = {}

        for relationship in relationships:
            source_text = self._safe_get_text(relationship, "source_entity")
            target_text = self._safe_get_text(relationship, "target_entity")
            rel_type = (
                self._safe_get_text(relationship, "relationship_type") or "unknown"
            )

            if not source_text or not target_text:
                continue

            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1

            json_relationship = {
                "id": relationship.get("id", ""),
                "source_entity": source_text,
                "target_entity": target_text,
                "relationship_type": rel_type,
                "confidence": relationship.get("confidence", 0),
                "properties": relationship.get("properties", {}),
            }
            json_graph["relationships"].append(json_relationship)

        # Update statistics
        json_graph["statistics"]["entity_types"] = entity_types
        json_graph["statistics"]["relationship_types"] = relationship_types
        json_graph["statistics"]["vietnamese_entities"] = vietnamese_entity_count

        return {
            "json_content": json_graph,
            "file_size": len(str(json_graph)),
            "entities_processed": len(json_graph["entities"]),
            "relationships_processed": len(json_graph["relationships"]),
        }
