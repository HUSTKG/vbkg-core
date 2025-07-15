from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.supabase import get_supabase
from app.nlp.embeddings import get_text_embedding
from app.tasks.executors import StepLogger
from app.utils.neo4j import get_neo4j_driver


class EntityEnrichmentTask:
    """Task for enriching entities with embeddings and external data"""

    def __init__(self, logger: StepLogger):
        self.logger = logger

    async def enrich_entities_with_embeddings(
        self,
        entity_ids: Optional[List[str]] = None,
        batch_size: int = 100,
        force_update: bool = False,
        embedding_model: str = "default",
    ) -> Dict[str, Any]:
        """
        Enrich entities with embeddings.

        Args:
            entity_ids: List of entity IDs to enrich, or None to process all entities without embeddings
            batch_size: Number of entities to process in each batch
            force_update: Whether to update embeddings even if they already exist
            embedding_model: Model to use for embeddings

        Returns:
            Dictionary with statistics about the operation
        """
        try:
            supabase = await get_supabase()

            await self.logger.info(
                f"Starting entity enrichment with embeddings using model: {embedding_model}"
            )
            # Get entities to process
            entities = await self._get_entities_for_embedding(
                supabase, entity_ids, batch_size, force_update
            )

            await self.logger.info(
                f"Found {len(entities)} entities to enrich with embeddings"
            )

            if not entities:
                await self.logger.info("No entities to enrich with embeddings")
                return {
                    "status": "completed",
                    "entities_processed": 0,
                    "entities_enriched": 0,
                    "errors": 0,
                }

            # Process entities in batches
            total_processed = 0
            total_enriched = 0
            total_errors = 0

            await self.logger.info(
                f"Processing {len(entities)} entities in batches of {batch_size}"
            )

            for i in range(0, len(entities), batch_size):
                batch = entities[i : i + batch_size]
                batch_results = await self._process_embedding_batch(supabase, batch)

                total_processed += batch_results["processed"]
                total_enriched += batch_results["enriched"]
                total_errors += batch_results["errors"]

            await self.logger.info(
                f"Enrichment completed: {total_processed} processed, {total_enriched} enriched, {total_errors} errors"
            )

            return {
                "status": "completed",
                "entities_processed": total_processed,
                "entities_enriched": total_enriched,
                "errors": total_errors,
                "embedding_model": embedding_model,
            }

        except Exception as e:
            await self.logger.error(
                f"Error enriching entities with embeddings: {str(e)}"
            )
            return {"status": "failed", "error": str(e)}

    async def enrich_entities_with_external_data(
        self,
        entity_ids: List[str],
        enrichment_sources: List[str],
        batch_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Enrich entities with external data sources.

        Args:
            entity_ids: List of entity IDs to enrich
            enrichment_sources: List of external sources to use
            batch_size: Number of entities to process in each batch

        Returns:
            Dictionary with enrichment statistics
        """
        try:
            supabase = await get_supabase()

            # Get entities
            entities_response = (
                await supabase.table("kg_entities")
                .select("*")
                .in_("id", [str(id) for id in entity_ids])
                .eq("is_active", True)
                .execute()
            )

            entities = entities_response.data

            if not entities:
                return {
                    "status": "completed",
                    "entities_processed": 0,
                    "entities_enriched": 0,
                    "errors": 0,
                }

            total_processed = 0
            total_enriched = 0
            total_errors = 0

            await self.logger.info(
                f"Enriching {len(entities)} entities with external data from sources: {enrichment_sources}"
            )

            for i in range(0, len(entities), batch_size):
                batch = entities[i : i + batch_size]

                for entity in batch:
                    try:
                        enrichment_data = await self._enrich_entity_with_sources(
                            entity, enrichment_sources
                        )

                        if enrichment_data:
                            # Update entity with enrichment data
                            current_properties = entity.get("properties", {})
                            current_properties.update(enrichment_data)

                            await supabase.table("kg_entities").update(
                                {
                                    "properties": current_properties,
                                    "updated_at": datetime.now().isoformat(),
                                }
                            ).eq("id", entity["id"]).execute()

                            total_enriched += 1

                        total_processed += 1

                    except Exception as e:
                        await self.logger.error(
                            f"Error enriching entity {entity['id']}: {str(e)}"
                        )
                        total_errors += 1
                        total_processed += 1

            return {
                "status": "completed",
                "entities_processed": total_processed,
                "entities_enriched": total_enriched,
                "errors": total_errors,
                "sources": enrichment_sources,
            }

        except Exception as e:
            await self.logger.error(
                f"Error enriching entities with external data: {str(e)}"
            )
            return {"status": "failed", "error": str(e)}

    async def sync_entities_to_neo4j(
        self,
        entity_ids: Optional[List[str]] = None,
        batch_size: int = 100,
        create_indexes: bool = True,
    ) -> Dict[str, Any]:
        """
        Synchronize entities from database to Neo4j.

        Args:
            entity_ids: List of entity IDs to synchronize, or None to process all entities without Neo4j ID
            batch_size: Number of entities to process in each batch
            create_indexes: Whether to create indexes in Neo4j

        Returns:
            Dictionary with statistics about the operation
        """
        try:
            supabase = await get_supabase()
            neo4j_driver = get_neo4j_driver()

            # Get entities to process
            entities = await self._get_entities_for_neo4j(
                supabase, entity_ids, batch_size
            )

            if not entities:
                await self.logger.info("No entities to synchronize to Neo4j")
                return {
                    "status": "completed",
                    "entities_processed": 0,
                    "entities_created": 0,
                    "errors": 0,
                }

            # Create indexes if requested
            if create_indexes:
                await self._create_neo4j_indexes(neo4j_driver)

            # Process entities in batches
            total_processed = 0
            total_created = 0
            total_errors = 0

            async with neo4j_driver.session() as session:
                for i in range(0, len(entities), batch_size):
                    batch = entities[i : i + batch_size]
                    batch_results = await self._process_neo4j_batch(
                        session, supabase, batch
                    )

                    total_processed += batch_results["processed"]
                    total_created += batch_results["created"]
                    total_errors += batch_results["errors"]

            return {
                "status": "completed",
                "entities_processed": total_processed,
                "entities_created": total_created,
                "errors": total_errors,
            }

        except Exception as e:
            await self.logger.error(f"Error synchronizing entities to Neo4j: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def sync_relationships_to_neo4j(
        self, relationship_ids: Optional[List[str]] = None, batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Synchronize relationships from database to Neo4j.

        Args:
            relationship_ids: List of relationship IDs to synchronize
            batch_size: Number of relationships to process in each batch

        Returns:
            Dictionary with statistics about the operation
        """
        try:
            supabase = await get_supabase()
            neo4j_driver = get_neo4j_driver()

            # Get relationships to process
            relationships = await self._get_relationships_for_neo4j(
                supabase, relationship_ids, batch_size
            )

            if not relationships:
                await self.logger.info("No relationships to synchronize to Neo4j")
                return {
                    "status": "completed",
                    "relationships_processed": 0,
                    "relationships_created": 0,
                    "errors": 0,
                }

            # Process relationships in batches
            total_processed = 0
            total_created = 0
            total_errors = 0

            async with neo4j_driver.session() as session:
                for i in range(0, len(relationships), batch_size):
                    batch = relationships[i : i + batch_size]
                    batch_results = await self._process_relationship_batch(
                        session, supabase, batch
                    )

                    total_processed += batch_results["processed"]
                    total_created += batch_results["created"]
                    total_errors += batch_results["errors"]

            return {
                "status": "completed",
                "relationships_processed": total_processed,
                "relationships_created": total_created,
                "errors": total_errors,
            }

        except Exception as e:
            await self.logger.error(
                f"Error synchronizing relationships to Neo4j: {str(e)}"
            )
            return {"status": "failed", "error": str(e)}

    async def cleanup_inactive_entities(
        self, batch_size: int = 100, dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up inactive entities from Neo4j.

        Args:
            batch_size: Number of entities to process in each batch
            dry_run: If True, only report what would be cleaned up without actually doing it

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            supabase = await get_supabase()
            neo4j_driver = get_neo4j_driver()

            # Get inactive entities that still have Neo4j IDs
            response = (
                await supabase.table("kg_entities")
                .select("id, neo4j_id, entity_text")
                .eq("is_active", False)
                .not_.is_("neo4j_id", "null")
                .limit(batch_size)
                .execute()
            )

            inactive_entities = response.data

            if not inactive_entities:
                await self.logger.info("No inactive entities to clean up from Neo4j")
                return {
                    "status": "completed",
                    "entities_processed": 0,
                    "entities_cleaned": 0,
                    "errors": 0,
                    "dry_run": dry_run,
                }

            total_processed = 0
            total_cleaned = 0
            total_errors = 0

            await self.logger.info(
                f"Found {len(inactive_entities)} inactive entities to clean up (dry_run: {dry_run})"
            )

            async with neo4j_driver.session() as session:
                for entity in inactive_entities:
                    try:
                        if not dry_run:
                            # Delete entity from Neo4j
                            await session.run(
                                "MATCH (e:Entity) WHERE id(e) = $neo4j_id DETACH DELETE e",
                                {"neo4j_id": int(entity["neo4j_id"])},
                            )

                            # Clear Neo4j ID from PostgreSQL
                            await supabase.table("kg_entities").update(
                                {"neo4j_id": None}
                            ).eq("id", entity["id"]).execute()

                        total_cleaned += 1
                        total_processed += 1

                        await self.logger.debug(
                            f"Cleaned up entity {entity['id']} from Neo4j"
                        )

                    except Exception as e:
                        await self.logger.error(
                            f"Error cleaning up entity {entity['id']}: {str(e)}"
                        )
                        total_errors += 1
                        total_processed += 1

            return {
                "status": "completed",
                "entities_processed": total_processed,
                "entities_cleaned": total_cleaned,
                "errors": total_errors,
                "dry_run": dry_run,
            }

        except Exception as e:
            await self.logger.error(f"Error cleaning up inactive entities: {str(e)}")
            return {"status": "failed", "error": str(e)}

    # Helper methods
    async def _get_entities_for_embedding(
        self, supabase, entity_ids, batch_size, force_update
    ):
        """Get entities that need embedding enrichment"""
        if entity_ids:
            query = (
                supabase.table("kg_entities")
                .select("id, entity_text, entity_type, properties")
                .eq("is_active", True)
            )

            # Process in chunks to avoid URI too long
            entities = []
            for i in range(0, len(entity_ids), 50):
                batch_ids = [str(id) for id in entity_ids[i : i + 50]]
                if force_update:
                    response = await query.in_("id", batch_ids).execute()
                else:
                    response = (
                        await query.in_("id", batch_ids)
                        .is_("embedding", "null")
                        .execute()
                    )
                entities.extend(response.data)
            return entities
        else:
            response = (
                await supabase.table("kg_entities")
                .select("id, entity_text, entity_type, properties")
                .eq("is_active", True)
                .is_("embedding", "null")
                .limit(batch_size)
                .execute()
            )
            return response.data

    async def _process_embedding_batch(self, supabase, batch):
        """Process a batch of entities for embedding"""
        processed = 0
        enriched = 0
        errors = 0

        await self.logger.info(
            f"Processing batch of {len(batch)} entities for embedding enrichment"
        )

        for entity in batch:
            try:
                # Create combined text for embedding
                entity_text = f"{entity['entity_type']}: {entity['entity_text']}"

                properties = entity.get("properties", {})
                if properties:
                    entity_text += " " + " ".join(
                        f"{key}: {value}" for key, value in properties.items()
                    )

                await self.logger.debug(
                    f"Generating embedding for entity {entity['id']} with text: {entity_text}"
                )

                # Generate embedding
                embedding = await get_text_embedding(entity_text)

                await self.logger.debug(
                    f"Generated embedding for entity {entity['id']}: {embedding}"
                )

                if embedding:
                    await supabase.table("kg_entities").update(
                        {
                            "embedding": embedding,
                            "updated_at": datetime.now().isoformat(),
                        }
                    ).eq("id", entity["id"]).execute()
                    enriched += 1
                else:
                    await self.logger.warning(
                        f"Failed to generate embedding for entity {entity['id']}"
                    )
                    errors += 1

                processed += 1

                await self.logger.info(
                    f"Processed entity {entity['id']} for embedding enrichment"
                )

            except Exception as e:
                await self.logger.error(
                    f"Error enriching entity {entity['id']}: {str(e)}"
                )
                errors += 1
                processed += 1

        return {"processed": processed, "enriched": enriched, "errors": errors}

    async def _get_entities_for_neo4j(self, supabase, entity_ids, batch_size):
        """Get entities that need Neo4j synchronization"""
        if entity_ids:
            entities = []
            for i in range(0, len(entity_ids), 50):
                batch_ids = [str(id) for id in entity_ids[i : i + 50]]
                response = (
                    await supabase.table("kg_entities")
                    .select("*")
                    .in_("id", batch_ids)
                    .eq("is_active", True)
                    .execute()
                )
                entities.extend(response.data)
            return entities
        else:
            response = (
                await supabase.table("kg_entities")
                .select("*")
                .eq("is_active", True)
                .is_("neo4j_id", "null")
                .limit(batch_size)
                .execute()
            )
            return response.data

    async def _create_neo4j_indexes(self, neo4j_driver):
        """Create necessary indexes in Neo4j"""
        async with neo4j_driver.session() as session:
            try:
                # Create index on entity_id
                await session.run(
                    "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.entity_id)"
                )

                # Create index on entity_text
                await session.run(
                    "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.entity_text)"
                )

                # Create index on entity_type
                await session.run(
                    "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)"
                )

                await self.logger.info("Created Neo4j indexes")
            except Exception as e:
                await self.logger.warning(f"Error creating Neo4j indexes: {str(e)}")

    async def _process_neo4j_batch(self, session, supabase, batch):
        """Process a batch of entities for Neo4j sync"""
        processed = 0
        created = 0
        errors = 0

        for entity in batch:
            try:
                # Create entity in Neo4j with proper JSON serialization
                import json

                properties_json = json.dumps(entity.get("properties", {}))

                result = await session.run(
                    """
                    CREATE (e:`Entity`:`{}` {{
                        entity_id: $entity_id,
                        entity_text: $entity_text,
                        entity_type: $entity_type,
                        properties: $properties,
                        confidence: $confidence,
                        is_verified: $is_verified,
                        created_at: datetime()
                    }})
                    RETURN id(e) as neo4j_id
                    """.format(
                        entity["entity_type"]
                    ),
                    {
                        "entity_id": entity["id"],
                        "entity_text": entity["entity_text"],
                        "entity_type": entity["entity_type"],
                        "properties": properties_json,
                        "confidence": entity.get("confidence", 0.0),
                        "is_verified": entity.get("is_verified", False),
                    },
                )

                record = await result.single()

                if record:
                    neo4j_id = record["neo4j_id"]

                    # Update entity with Neo4j ID
                    await supabase.table("kg_entities").update(
                        {
                            "neo4j_id": str(neo4j_id),
                            "updated_at": datetime.now().isoformat(),
                        }
                    ).eq("id", entity["id"]).execute()

                    created += 1
                else:
                    await self.logger.warning(
                        f"Failed to create entity in Neo4j: {entity['id']}"
                    )
                    errors += 1

                processed += 1

            except Exception as e:
                await self.logger.error(
                    f"Error creating entity in Neo4j {entity['id']}: {str(e)}"
                )
                errors += 1
                processed += 1

        return {"processed": processed, "created": created, "errors": errors}

    async def _get_relationships_for_neo4j(
        self, supabase, relationship_ids, batch_size
    ):
        """Get relationships that need Neo4j synchronization"""
        if relationship_ids:
            relationships = []
            for i in range(0, len(relationship_ids), 50):
                batch_ids = [str(id) for id in relationship_ids[i : i + 50]]
                response = (
                    await supabase.table("kg_relationships")
                    .select("*")
                    .in_("id", batch_ids)
                    .eq("is_active", True)
                    .execute()
                )
                relationships.extend(response.data)
            return relationships
        else:
            response = (
                await supabase.table("kg_relationships")
                .select("*")
                .eq("is_active", True)
                .is_("neo4j_id", "null")
                .limit(batch_size)
                .execute()
            )
            return response.data

    async def _process_relationship_batch(self, session, supabase, batch):
        """Process a batch of relationships for Neo4j sync"""
        processed = 0
        created = 0
        errors = 0

        for relationship in batch:
            try:
                # Get Neo4j IDs of source and target entities
                source_response = (
                    await supabase.table("kg_entities")
                    .select("neo4j_id")
                    .eq("id", relationship["source_entity_id"])
                    .eq("is_active", True)
                    .execute()
                )
                target_response = (
                    await supabase.table("kg_entities")
                    .select("neo4j_id")
                    .eq("id", relationship["target_entity_id"])
                    .eq("is_active", True)
                    .execute()
                )

                if not source_response.data or not target_response.data:
                    await self.logger.warning(
                        f"Source or target entity not found for relationship {relationship['id']}"
                    )
                    errors += 1
                    processed += 1
                    continue

                source_neo4j_id = source_response.data[0].get("neo4j_id")
                target_neo4j_id = target_response.data[0].get("neo4j_id")

                if not source_neo4j_id or not target_neo4j_id:
                    await self.logger.warning(
                        f"Source or target entity not yet in Neo4j for relationship {relationship['id']}"
                    )
                    errors += 1
                    processed += 1
                    continue

                # Create relationship in Neo4j with proper JSON serialization
                import json

                properties_json = json.dumps(relationship.get("properties", {}))

                result = await session.run(
                    """
                    MATCH (source), (target)
                    WHERE id(source) = $source_id AND id(target) = $target_id
                    CREATE (source)-[r:`{}`  {{
                        relationship_id: $relationship_id,
                        properties: $properties,
                        confidence: $confidence,
                        is_verified: $is_verified,
                        created_at: datetime()
                    }}]->(target)
                    RETURN id(r) as neo4j_id
                """.format(
                        relationship["relationship_type"]
                    ),
                    {
                        "source_id": int(source_neo4j_id),
                        "target_id": int(target_neo4j_id),
                        "relationship_id": relationship["id"],
                        "properties": properties_json,
                        "confidence": relationship.get("confidence", 0.0),
                        "is_verified": relationship.get("is_verified", False),
                    },
                )

                record = await result.single()

                if record:
                    neo4j_id = record["neo4j_id"]

                    # Update relationship with Neo4j ID
                    await supabase.table("kg_relationships").update(
                        {
                            "neo4j_id": str(neo4j_id),
                            "updated_at": datetime.now().isoformat(),
                        }
                    ).eq("id", relationship["id"]).execute()

                    created += 1
                else:
                    await self.logger.warning(
                        f"Failed to create relationship in Neo4j: {relationship['id']}"
                    )
                    errors += 1

                processed += 1

            except Exception as e:
                await self.logger.error(
                    f"Error creating relationship in Neo4j {relationship['id']}: {str(e)}"
                )
                errors += 1
                processed += 1

        return {"processed": processed, "created": created, "errors": errors}

    async def _enrich_entity_with_sources(self, entity, enrichment_sources):
        """Enrich entity with external data sources"""
        enrichment_data = {}

        for source in enrichment_sources:
            try:
                if source == "wikipedia":
                    data = await self._get_wikipedia_data(entity)
                elif source == "wikidata":
                    data = await self._get_wikidata(entity)
                elif source == "google_knowledge_graph":
                    data = await self._get_google_kg_data(entity)
                # Add more sources as needed
                else:
                    await self.logger.warning(f"Unknown enrichment source: {source}")
                    continue

                if data:
                    enrichment_data[f"{source}_data"] = data
                    enrichment_data[f"{source}_enriched_at"] = (
                        datetime.now().isoformat()
                    )

            except Exception as e:
                await self.logger.warning(f"Error enriching from {source}: {str(e)}")
                continue

        return enrichment_data

    async def _get_wikipedia_data(self, entity):
        """Get data from Wikipedia (placeholder implementation)"""
        # TODO: Implement Wikipedia API integration
        # Example implementation would use requests to call Wikipedia API
        await self.logger.debug(
            f"Wikipedia enrichment not implemented for entity: {entity['entity_text']}"
        )
        return None

    async def _get_wikidata(self, entity):
        """Get data from Wikidata (placeholder implementation)"""
        # TODO: Implement Wikidata SPARQL integration
        # Example implementation would use SPARQL queries to Wikidata
        await self.logger.debug(
            f"Wikidata enrichment not implemented for entity: {entity['entity_text']}"
        )
        return None

    async def _get_google_kg_data(self, entity):
        """Get data from Google Knowledge Graph (placeholder implementation)"""
        # TODO: Implement Google Knowledge Graph API integration
        await self.logger.debug(
            f"Google KG enrichment not implemented for entity: {entity['entity_text']}"
        )
        return None
