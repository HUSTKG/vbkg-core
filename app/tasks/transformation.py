import logging
from typing import Any, Dict, List
from uuid import UUID

from neo4j import Query

from app.core.supabase import get_supabase
from app.nlp.embeddings import get_entity_embedding, get_text_embedding
from app.utils.neo4j import get_neo4j_driver

logger = logging.getLogger(__name__)

async def enrich_entities_with_embeddings(
    entity_ids: List[UUID] | None = None,
    batch_size: int = 100,
    force_update: bool = False
) -> Dict[str, Any]:
    """
    Enrich entities with embeddings.
    
    Args:
        entity_ids: List of entity IDs to enrich, or None to process all entities without embeddings
        batch_size: Number of entities to process in each batch
        force_update: Whether to update embeddings even if they already exist
        
    Returns:
        Dictionary with statistics about the operation
    """
    try:
        supabase = await get_supabase()

        response: Any = None
        
        # Get entities to process
        if entity_ids:
            # Process specific entities
            query = supabase.table("kg_entities").select("id", "entity_text", "entity_type")
            
            for i in range(0, len(entity_ids), 50):  # Process in chunks to avoid URI too long
                batch_ids = [str(id) for id in entity_ids[i:i+50]]
                response = query.in_("id", batch_ids)
                
                if force_update:
                    response = await response.execute()
                else:
                    # Only get entities without embeddings
                    response = await response.is_("embedding", "null").execute()
        else:
            # Process all entities without embeddings
            response = await supabase.table("kg_entities").select("id", "entity_text", "entity_type").is_("embedding", "null").limit(batch_size).execute()
        
        entities = response.data
        
        if not entities:
            logger.info("No entities to enrich with embeddings")
            return {
                "status": "completed",
                "entities_processed": 0,
                "entities_enriched": 0,
                "errors": 0
            }
        
        # Process entities in batches
        total_processed = 0
        total_enriched = 0
        total_errors = 0
        
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i+batch_size]
            
            for entity in batch:
                try:
                    # Create combined text for embedding
                    entity_text = f"{entity['entity_type']}: {entity['entity_text']}"

                    text_to_embed = entity_text
                    properties = entity.get("properties", {})

                    if properties:
                        # Add properties to the text if available
                        text_to_embed += " " + " ".join(f"{key}: {value}" for key, value in properties.items())
                    
                    # Generate embedding
                    embedding = await get_text_embedding(text_to_embed)
                    
                    if embedding:
                        # Update entity with embedding
                        await supabase.table("kg_entities").update({
                            "embedding": embedding
                        }).eq("id", entity["id"]).execute()
                        
                        total_enriched += 1
                    else:
                        logger.warning(f"Failed to generate embedding for entity {entity['id']}")
                        total_errors += 1
                    
                    total_processed += 1
                
                except Exception as e:
                    logger.error(f"Error enriching entity {entity['id']}: {str(e)}")
                    total_errors += 1
                    total_processed += 1
        
        return {
            "status": "completed",
            "entities_processed": total_processed,
            "entities_enriched": total_enriched,
            "errors": total_errors
        }
    
    except Exception as e:
        logger.error(f"Error enriching entities with embeddings: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }

async def sync_entities_to_neo4j(
    entity_ids: List[UUID] | None = None,
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Synchronize entities from database to Neo4j.
    
    Args:
        entity_ids: List of entity IDs to synchronize, or None to process all entities without Neo4j ID
        batch_size: Number of entities to process in each batch
        
    Returns:
        Dictionary with statistics about the operation
    """
    try:
        supabase = await get_supabase()
        neo4j_driver = get_neo4j_driver()

        response: Any = None
        
        # Get entities to process
        if entity_ids:
            # Process specific entities
            query = supabase.table("kg_entities").select("*")
            
            for i in range(0, len(entity_ids), 50):  # Process in chunks to avoid URI too long
                batch_ids = [str(id) for id in entity_ids[i:i+50]]
                response = query.in_("id", batch_ids).execute()
        else:
            # Process all entities without Neo4j ID
            response = supabase.table("kg_entities").select("*").is_("neo4j_id", "null").limit(batch_size).execute()
        
        entities = response.data
        
        if not entities:
            logger.info("No entities to synchronize to Neo4j")
            return {
                "status": "completed",
                "entities_processed": 0,
                "entities_created": 0,
                "errors": 0
            }
        
        # Process entities in batches
        total_processed = 0
        total_created = 0
        total_errors = 0
        
        async with neo4j_driver.session() as session:
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i+batch_size]
                
                for entity in batch:
                    try:
                        # Create entity in Neo4j
                        result = await session.run("""
                            CREATE (e:`Entity`:`{}` {{
                                entity_id: $entity_id,
                                entity_text: $entity_text,
                                properties: $properties
                            }})
                            RETURN id(e) as neo4j_id
                            """.format(entity["entity_type"]),
                            {
                                "entity_id": entity["id"],
                                "entity_text": entity["entity_text"],
                                "properties": entity.get("properties", {})
                            }
                        )

                        
                        record = await result.single()
                        
                        if record:
                            neo4j_id = record["neo4j_id"]
                            
                            # Update entity with Neo4j ID
                            await supabase.table("kg_entities").update({
                                "neo4j_id": str(neo4j_id)
                            }).eq("id", entity["id"]).execute()
                            
                            total_created += 1
                        else:
                            logger.warning(f"Failed to create entity in Neo4j: {entity['id']}")
                            total_errors += 1
                        
                        total_processed += 1
                    
                    except Exception as e:
                        logger.error(f"Error creating entity in Neo4j {entity['id']}: {str(e)}")
                        total_errors += 1
                        total_processed += 1
        
        return {
            "status": "completed",
            "entities_processed": total_processed,
            "entities_created": total_created,
            "errors": total_errors
        }
    
    except Exception as e:
        logger.error(f"Error synchronizing entities to Neo4j: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }

async def sync_relationships_to_neo4j(
    relationship_ids: List[UUID] | None = None,
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Synchronize relationships from database to Neo4j.
    
    Args:
        relationship_ids: List of relationship IDs to synchronize, or None to process all relationships without Neo4j ID
        batch_size: Number of relationships to process in each batch
        
    Returns:
        Dictionary with statistics about the operation
    """
    try:
        supabase = await get_supabase()
        neo4j_driver = get_neo4j_driver()

        response: Any = None
        
        # Get relationships to process
        if relationship_ids:
            # Process specific relationships
            query = supabase.table("kg_relationships").select("*")
            
            for i in range(0, len(relationship_ids), 50):  # Process in chunks to avoid URI too long
                batch_ids = [str(id) for id in relationship_ids[i:i+50]]
                response = await query.in_("id", batch_ids).execute()
        else:
            # Process all relationships without Neo4j ID
            response = await supabase.table("kg_relationships").select("*").is_("neo4j_id", "null").limit(batch_size).execute()
        
        relationships = response.data
        
        if not relationships:
            logger.info("No relationships to synchronize to Neo4j")
            return {
                "status": "completed",
                "relationships_processed": 0,
                "relationships_created": 0,
                "errors": 0
            }
        
        # Process relationships in batches
        total_processed = 0
        total_created = 0
        total_errors = 0
        
        async with neo4j_driver.session() as session:
            for i in range(0, len(relationships), batch_size):
                batch = relationships[i:i+batch_size]
                
                for relationship in batch:
                    try:
                        # Get Neo4j IDs of source and target entities
                        source_response = await supabase.table("kg_entities").select("neo4j_id").eq("id", relationship["source_entity_id"]).execute()
                        target_response = await supabase.table("kg_entities").select("neo4j_id").eq("id", relationship["target_entity_id"]).execute()
                        
                        if not source_response.data or not target_response.data:
                            logger.warning(f"Source or target entity not found for relationship {relationship['id']}")
                            total_errors += 1
                            total_processed += 1
                            continue
                        
                        source_neo4j_id = source_response.data[0].get("neo4j_id")
                        target_neo4j_id = target_response.data[0].get("neo4j_id")
                        
                        if not source_neo4j_id or not target_neo4j_id:
                            logger.warning(f"Source or target entity not yet in Neo4j for relationship {relationship['id']}")
                            total_errors += 1
                            total_processed += 1
                            continue
                        
                        # Create relationship in Neo4j
                        result = await session.run("""
                            MATCH (source), (target)
                            WHERE id(source) = $source_id AND id(target) = $target_id
                            CREATE (source)-[r:`{}`  {{
                                relationship_id: $relationship_id,
                                properties: $properties
                            }}]->(target)
                            RETURN id(r) as neo4j_id
                        """.format(relationship["relationship_type"]), {
                            "source_id": int(source_neo4j_id),
                            "target_id": int(target_neo4j_id),
                            "relationship_id": relationship["id"],
                            "properties": relationship.get("properties", {})
                        })
                        
                        record = await result.single()
                        
                        if record:
                            neo4j_id = record["neo4j_id"]
                            
                            # Update relationship with Neo4j ID
                            await supabase.table("kg_relationships").update({
                                "neo4j_id": str(neo4j_id)
                            }).eq("id", relationship["id"]).execute()
                            
                            total_created += 1
                        else:
                            logger.warning(f"Failed to create relationship in Neo4j: {relationship['id']}")
                            total_errors += 1
                        
                        total_processed += 1
                    
                    except Exception as e:
                        logger.error(f"Error creating relationship in Neo4j {relationship['id']}: {str(e)}")
                        total_errors += 1
                        total_processed += 1
        
        return {
            "status": "completed",
            "relationships_processed": total_processed,
            "relationships_created": total_created,
            "errors": total_errors
        }
    
    except Exception as e:
        logger.error(f"Error synchronizing relationships to Neo4j: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }

async def detect_entity_conflicts(
    threshold: float = 0.75,
    batch_size: int = 100,
    entity_types: List[str] | None = None
) -> Dict[str, Any]:
    """
    Detect conflicts between entities.
    
    Args:
        threshold: Similarity threshold for conflict detection
        batch_size: Number of entities to process in each batch
        entity_types: Types of entities to process, or None to process all types
        
    Returns:
        Dictionary with statistics about the operation
    """
    from app.services.entity_resolution import (create_entity_conflict,
                                                find_entity_conflicts)
    
    try:
        supabase = await get_supabase()
        
        # Get entities to process
        query = supabase.table("kg_entities").select("id, entity_text, entity_type")
        
        if entity_types:
            query = query.in_("entity_type", entity_types)
        
        response = await query.limit(batch_size).execute()
        entities = response.data
        
        if not entities:
            logger.info("No entities to process for conflict detection")
            return {
                "status": "completed",
                "entities_processed": 0,
                "conflicts_detected": 0,
                "errors": 0
            }
        
        # Process entities
        total_processed = 0
        total_conflicts = 0
        total_errors = 0
        
        for entity in entities:
            try:
                # Find conflicts for this entity
                conflicts = await find_entity_conflicts(
                    entity_id=UUID(entity["id"]),
                    threshold=threshold
                )
                
                # Create conflict records
                for conflict in conflicts:
                    await create_entity_conflict(
                        entity_id_1=UUID(conflict["entity_id_1"]),
                        entity_id_2=UUID(conflict["entity_id_2"]),
                        similarity_score=conflict["similarity_score"],
                        conflict_type=conflict["conflict_type"]
                    )
                    
                    total_conflicts += 1
                
                total_processed += 1
            
            except Exception as e:
                logger.error(f"Error detecting conflicts for entity {entity['id']}: {str(e)}")
                total_errors += 1
                total_processed += 1
        
        return {
            "status": "completed",
            "entities_processed": total_processed,
            "conflicts_detected": total_conflicts,
            "errors": total_errors
        }
    
    except Exception as e:
        logger.error(f"Error detecting entity conflicts: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }
