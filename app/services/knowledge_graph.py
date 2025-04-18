from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging
from datetime import datetime

from app.core.supabase import get_supabase
from app.utils.neo4j import get_neo4j_driver

logger = logging.getLogger(__name__)

# Entity Management

async def get_entities(
    skip: int = 0,
    limit: int = 100,
    entity_type: Optional[str] = None,
    is_verified: Optional[bool] = None,
    source_document_id: Optional[UUID] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve entities with optional filtering.
    """
    try:
        supabase = get_supabase()
        query = supabase.table("kg_entities").select("*")
        
        if entity_type:
            query = query.eq("entity_type", entity_type)
        
        if is_verified is not None:
            query = query.eq("is_verified", is_verified)
        
        if source_document_id:
            query = query.eq("source_document_id", str(source_document_id))
        
        response = await query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        return response.data
    
    except Exception as e:
        logger.error(f"Error getting entities: {e}")
        return []

async def get_entity(entity_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a specific entity by ID.
    """
    try:
        supabase = get_supabase()
        response = await supabase.table("kg_entities").select("*").eq("id", str(entity_id)).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    except Exception as e:
        logger.error(f"Error getting entity {entity_id}: {e}")
        return None

async def create_entity(
    entity_in: Dict[str, Any],
    created_by: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new entity.
    """
    try:
        supabase = get_supabase()
        
        # Map to FIBO class if appropriate
        fibo_class_id = None
        if "entity_type" in entity_in:
            fibo_class = await get_entity_type_mapping(entity_in["entity_type"])
            if fibo_class:
                fibo_class_id = fibo_class["fibo_class_id"]
        
        data = {
            "entity_text": entity_in["entity_text"],
            "entity_type": entity_in["entity_type"],
            "source_document_id": str(entity_in["source_document_id"]) if entity_in.get("source_document_id") else None,
            "fibo_class_id": fibo_class_id,
            "properties": entity_in.get("properties", {}),
            "confidence": entity_in.get("confidence", 1.0),
            "is_verified": entity_in.get("is_verified", False),
            "verification_notes": entity_in.get("verification_notes"),
            "verified_by": str(created_by) if entity_in.get("is_verified") and created_by else None
        }
        
        response = await supabase.table("kg_entities").insert(data).execute()
        
        if not response.data:
            return None
        
        entity = response.data[0]
        
        # Create in Neo4j if entity was created successfully
        neo4j_id = await create_entity_in_neo4j(entity)
        
        if neo4j_id:
            # Update the Neo4j ID
            await supabase.table("kg_entities").update({"neo4j_id": str(neo4j_id)}).eq("id", entity["id"]).execute()
            entity["neo4j_id"] = str(neo4j_id)
        
        return entity
    
    except Exception as e:
        logger.error(f"Error creating entity: {e}")
        return None

async def update_entity(
    entity_id: UUID,
    entity_in: Dict[str, Any],
    updated_by: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """
    Update an existing entity.
    """
    try:
        supabase = get_supabase()
        
        # Get the current entity
        entity = await get_entity(entity_id)
        if not entity:
            return None
        
        # Prepare update data
        data = {}
        
        if "entity_text" in entity_in:
            data["entity_text"] = entity_in["entity_text"]
        
        if "entity_type" in entity_in:
            data["entity_type"] = entity_in["entity_type"]
            
            # Update FIBO class if entity type changed
            fibo_class = await get_entity_type_mapping(entity_in["entity_type"])
            if fibo_class:
                data["fibo_class_id"] = fibo_class["fibo_class_id"]
        
        if "properties" in entity_in:
            data["properties"] = entity_in["properties"]
        
        if "confidence" in entity_in:
            data["confidence"] = entity_in["confidence"]
        
        if "is_verified" in entity_in:
            data["is_verified"] = entity_in["is_verified"]
            
            if entity_in["is_verified"] and updated_by:
                data["verified_by"] = str(updated_by)
        
        if "verification_notes" in entity_in:
            data["verification_notes"] = entity_in["verification_notes"]
        
        if not data:
            # Nothing to update
            return entity
        
        response = await supabase.table("kg_entities").update(data).eq("id", str(entity_id)).execute()
        
        if not response.data:
            return None
        
        updated_entity = response.data[0]
        
        # Update in Neo4j if Neo4j ID exists
        if updated_entity.get("neo4j_id"):
            await update_entity_in_neo4j(updated_entity)
        
        return updated_entity
    
    except Exception as e:
        logger.error(f"Error updating entity {entity_id}: {e}")
        return None

async def delete_entity(entity_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Delete an entity.
    """
    try:
        supabase = get_supabase()
        
        # Get the entity first
        entity = await get_entity(entity_id)
        if not entity:
            return None
        
        # Delete from Neo4j if Neo4j ID exists
        if entity.get("neo4j_id"):
            await delete_entity_from_neo4j(entity["neo4j_id"])
        
        # Delete the entity from Supabase
        response = await supabase.table("kg_entities").delete().eq("id", str(entity_id)).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    except Exception as e:
        logger.error(f"Error deleting entity {entity_id}: {e}")
        return None

# Relationship Management

async def get_relationships(
    skip: int = 0,
    limit: int = 100,
    relationship_type: Optional[str] = None,
    source_entity_id: Optional[UUID] = None,
    target_entity_id: Optional[UUID] = None,
    is_verified: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve relationships with optional filtering.
    """
    try:
        supabase = get_supabase()
        query = supabase.table("kg_relationships").select("*")
        
        if relationship_type:
            query = query.eq("relationship_type", relationship_type)
        
        if source_entity_id:
            query = query.eq("source_entity_id", str(source_entity_id))
        
        if target_entity_id:
            query = query.eq("target_entity_id", str(target_entity_id))
        
        if is_verified is not None:
            query = query.eq("is_verified", is_verified)
        
        response = await query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        return response.data
    
    except Exception as e:
        logger.error(f"Error getting relationships: {e}")
        return []

async def get_relationship(relationship_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a specific relationship by ID.
    """
    try:
        supabase = get_supabase()
        response = await supabase.table("kg_relationships").select("*").eq("id", str(relationship_id)).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    except Exception as e:
        logger.error(f"Error getting relationship {relationship_id}: {e}")
        return None

async def create_relationship(
    relationship_in: Dict[str, Any],
    created_by: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new relationship.
    """
    try:
        supabase = get_supabase()
        
        # Map to FIBO property if appropriate
        fibo_property_id = None
        if "relationship_type" in relationship_in:
            fibo_relation = await get_relationship_type_mapping(relationship_in["relationship_type"])
            if fibo_relation:
                fibo_property_id = fibo_relation["fibo_property_id"]
        
        data = {
            "source_entity_id": str(relationship_in["source_entity_id"]),
            "target_entity_id": str(relationship_in["target_entity_id"]),
            "relationship_type": relationship_in["relationship_type"],
            "source_document_id": str(relationship_in["source_document_id"]) if relationship_in.get("source_document_id") else None,
            "fibo_property_id": fibo_property_id,
            "properties": relationship_in.get("properties", {}),
            "confidence": relationship_in.get("confidence", 1.0),
            "is_verified": relationship_in.get("is_verified", False),
            "verification_notes": relationship_in.get("verification_notes"),
            "verified_by": str(created_by) if relationship_in.get("is_verified") and created_by else None
        }
        
        response = await supabase.table("kg_relationships").insert(data).execute()
        
        if not response.data:
            return None
        
        relationship = response.data[0]
        
        # Create in Neo4j if relationship was created successfully
        neo4j_id = await create_relationship_in_neo4j(relationship)
        
        if neo4j_id:
            # Update the Neo4j ID
            await supabase.table("kg_relationships").update({"neo4j_id": str(neo4j_id)}).eq("id", relationship["id"]).execute()
            relationship["neo4j_id"] = str(neo4j_id)
        
        return relationship
    
    except Exception as e:
        logger.error(f"Error creating relationship: {e}")
        return None

async def update_relationship(
    relationship_id: UUID,
    relationship_in: Dict[str, Any],
    updated_by: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """
    Update an existing relationship.
    """
    try:
        supabase = get_supabase()
        
        # Get the current relationship
        relationship = await get_relationship(relationship_id)
        if not relationship:
            return None
        
        # Prepare update data
        data = {}
        
        if "relationship_type" in relationship_in:
            data["relationship_type"] = relationship_in["relationship_type"]
            
            # Update FIBO property if relationship type changed
            fibo_relation = await get_relationship_type_mapping(relationship_in["relationship_type"])
            if fibo_relation:
                data["fibo_property_id"] = fibo_relation["fibo_property_id"]
        
        if "properties" in relationship_in:
            data["properties"] = relationship_in["properties"]
        
        if "confidence" in relationship_in:
            data["confidence"] = relationship_in["confidence"]
        
        if "is_verified" in relationship_in:
            data["is_verified"] = relationship_in["is_verified"]
            
            if relationship_in["is_verified"] and updated_by:
                data["verified_by"] = str(updated_by)
        
        if "verification_notes" in relationship_in:
            data["verification_notes"] = relationship_in["verification_notes"]
        
        if not data:
            # Nothing to update
            return relationship
        
        response = await supabase.table("kg_relationships").update(data).eq("id", str(relationship_id)).execute()
        
        if not response.data:
            return None
        
        updated_relationship = response.data[0]
        
        # Update in Neo4j if Neo4j ID exists
        if updated_relationship.get("neo4j_id"):
            await update_relationship_in_neo4j(updated_relationship)
        
        return updated_relationship
    
    except Exception as e:
        logger.error(f"Error updating relationship {relationship_id}: {e}")
        return None

async def delete_relationship(relationship_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Delete a relationship.
    """
    try:
        supabase = get_supabase()
        
        # Get the relationship first
        relationship = await get_relationship(relationship_id)
        if not relationship:
            return None
        
        # Delete from Neo4j if Neo4j ID exists
        if relationship.get("neo4j_id"):
            await delete_relationship_from_neo4j(relationship["neo4j_id"])
        
        # Delete the relationship from Supabase
        response = await supabase.table("kg_relationships").delete().eq("id", str(relationship_id)).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    except Exception as e:
        logger.error(f"Error deleting relationship {relationship_id}: {e}")
        return None

# Search and Query

async def search_entities(
    query_text: str,
    entity_type: Optional[str] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search entities by text.
    """
    try:
        supabase = get_supabase()
        
        # Basic search using PostgreSQL's text search capabilities
        query = supabase.table("kg_entities").select("*")
        
        # Add entity_text search condition
        query = query.ilike("entity_text", f"%{query_text}%")
        
        if entity_type:
            query = query.eq("entity_type", entity_type)
        
        response = await query.limit(limit).execute()
        return response.data
    
    except Exception as e:
        logger.error(f"Error searching entities: {e}")
        return []

async def get_entity_conflicts(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = "pending"
) -> List[Dict[str, Any]]:
    """
    Retrieve entity conflicts that need resolution.
    """
    try:
        supabase = get_supabase()
        query = supabase.table("entity_conflicts").select("*, entity_id_1(*), entity_id_2(*)")
        
        if status:
            query = query.eq("status", status)
        
        response = await query.range(skip, skip + limit - 1).order("created_at", desc=True).execute()
        return response.data
    
    except Exception as e:
        logger.error(f"Error getting entity conflicts: {e}")
        return []

async def execute_knowledge_query(
    query_text: str,
    query_type: str,
    parameters: Optional[Dict[str, Any]] = None,
    user_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Execute a knowledge graph query.
    """
    try:
        # Record the query in history
        await record_query_execution(
            query_text=query_text,
            query_type=query_type,
            parameters=parameters,
            user_id=user_id
        )
        
        # Execute based on query type
        if query_type == "cypher":
            return await execute_cypher_query(query_text, parameters)
        
        elif query_type == "natural_language":
            # This would typically use an LLM to convert natural language to Cypher
            converted_query = await convert_nl_to_cypher(query_text)
            return await execute_cypher_query(converted_query, parameters)
        
        else:
            return {
                "error": f"Unsupported query type: {query_type}",
                "results": []
            }
    
    except Exception as e:
        logger.error(f"Error executing knowledge query: {e}")
        
        return {
            "error": str(e),
            "results": []
        }

async def record_query_execution(
    query_text: str,
    query_type: str,
    parameters: Optional[Dict[str, Any]] = None,
    user_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """
    Record a query execution in the history.
    """
    try:
        supabase = get_supabase()
        
        data = {
            "query_text": query_text,
            "parameters": parameters or {},
            "executed_by": str(user_id) if user_id else None,
            "status": "completed",  # Will be updated later
            "execution_time": None,  # Will be updated later
            "result_count": None  # Will be updated later
        }
        
        response = await supabase.table("query_history").insert(data).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    except Exception as e:
        logger.error(f"Error recording query execution: {e}")
        return None

async def update_query_execution(
    query_id: UUID,
    execution_time: int,
    result_count: int,
    status: str,
    error_message: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Update a query execution record.
    """
    try:
        supabase = get_supabase()
        
        data = {
            "execution_time": execution_time,
            "result_count": result_count,
            "status": status
        }
        
        if error_message:
            data["error_message"] = error_message
        
        response = await supabase.table("query_history").update(data).eq("id", str(query_id)).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    except Exception as e:
        logger.error(f"Error updating query execution {query_id}: {e}")
        return None

# Neo4j Operations

async def create_entity_in_neo4j(entity: Dict[str, Any]) -> Optional[int]:
    """
    Create an entity in Neo4j.
    """
    try:
        neo4j_driver = get_neo4j_driver()
        
        async with neo4j_driver.session() as session:
            result = await session.run("""
                CREATE (e:`Entity`:`{}` {{
                    entity_id: $entity_id,
                    entity_text: $entity_text,
                    properties: $properties
                }})
                RETURN id(e) as neo4j_id
            """.format(entity["entity_type"]), {
                "entity_id": entity["id"],
                "entity_text": entity["entity_text"],
                "properties": entity.get("properties", {})
            })
            
            record = await result.single()
            if record:
                return record["neo4j_id"]
            return None
    
    except Exception as e:
        logger.error(f"Error creating entity in Neo4j: {e}")
        return None

async def update_entity_in_neo4j(entity: Dict[str, Any]) -> bool:
    """
    Update an entity in Neo4j.
    """
    try:
        neo4j_driver = get_neo4j_driver()
        
        async with neo4j_driver.session() as session:
            result = await session.run("""
                MATCH (e)
                WHERE id(e) = $neo4j_id
                SET e:`{}`,
                    e.entity_text = $entity_text,
                    e.properties = $properties
                RETURN e
            """.format(entity["entity_type"]), {
                "neo4j_id": int(entity["neo4j_id"]),
                "entity_text": entity["entity_text"],
                "properties": entity.get("properties", {})
            })
            
            return True
    
    except Exception as e:
        logger.error(f"Error updating entity in Neo4j: {e}")
        return False

async def delete_entity_from_neo4j(neo4j_id: str) -> bool:
    """
    Delete an entity from Neo4j.
    """
    try:
        neo4j_driver = get_neo4j_driver()
        
        async with neo4j_driver.session() as session:
            await session.run("""
                MATCH (e)
                WHERE id(e) = $neo4j_id
                DETACH DELETE e
            """, {
                "neo4j_id": int(neo4j_id)
            })
            
            return True
    
    except Exception as e:
        logger.error(f"Error deleting entity from Neo4j: {e}")
        return False

async def create_relationship_in_neo4j(relationship: Dict[str, Any]) -> Optional[int]:
    """
    Create a relationship in Neo4j.
    """
    try:
        neo4j_driver = get_neo4j_driver()
        
        # Get source and target entities
        supabase = get_supabase()
        source_response = await supabase.table("kg_entities").select("neo4j_id").eq("id", relationship["source_entity_id"]).execute()
        target_response = await supabase.table("kg_entities").select("neo4j_id").eq("id", relationship["target_entity_id"]).execute()
        
        if not source_response.data or not target_response.data:
            return None
        
        source_neo4j_id = source_response.data[0].get("neo4j_id")
        target_neo4j_id = target_response.data[0].get("neo4j_id")
        
        if not source_neo4j_id or not target_neo4j_id:
            return None
        
        async with neo4j_driver.session() as session:
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
                return record["neo4j_id"]
            return None
    
    except Exception as e:
        logger.error(f"Error creating relationship in Neo4j: {e}")
        return None

async def update_relationship_in_neo4j(relationship: Dict[str, Any]) -> bool:
    """
    Update a relationship in Neo4j.
    """
    try:
        neo4j_driver = get_neo4j_driver()
        
        async with neo4j_driver.session() as session:
            result = await session.run("""
                MATCH ()-[r]->()
                WHERE id(r) = $neo4j_id
                SET r.properties = $properties
                RETURN r
            """, {
                "neo4j_id": int(relationship["neo4j_id"]),
                "properties": relationship.get("properties", {})
            })
            
            return True
    
    except Exception as e:
        logger.error(f"Error updating relationship in Neo4j: {e}")
        return False

async def delete_relationship_from_neo4j(neo4j_id: str) -> bool:
    """
    Delete a relationship from Neo4j.
    """
    try:
        neo4j_driver = get_neo4j_driver()
        
        async with neo4j_driver.session() as session:
            await session.run("""
                MATCH ()-[r]->()
                WHERE id(r) = $neo4j_id
                DELETE r
            """, {
                "neo4j_id": int(neo4j_id)
            })
            
            return True
    
    except Exception as e:
        logger.error(f"Error deleting relationship from Neo4j: {e}")
        return False

async def execute_cypher_query(
    query: str,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute a Cypher query against Neo4j.
    """
    try:
        neo4j_driver = get_neo4j_driver()
        start_time = datetime.now()
        
        async with neo4j_driver.session() as session:
            result = await session.run(query, parameters or {})
            
            records = []
            async for record in result:
                records.append(record.data())
            
            # Get query summary
            summary = await result.consume()
            
            end_time = datetime.now()
            execution_time = int((end_time - start_time).total_seconds() * 1000)  # in milliseconds
            
            return {
                "results": records,
                "count": len(records),
                "execution_time_ms": execution_time,
                "counters": {
                    "nodes_created": summary.counters.nodes_created,
                    "nodes_deleted": summary.counters.nodes_deleted,
                    "relationships_created": summary.counters.relationships_created,
                    "relationships_deleted": summary.counters.relationships_deleted,
                    "properties_set": summary.counters.properties_set
                }
            }
    
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}")
        
        end_time = datetime.now()
        execution_time = int((end_time - start_time).total_seconds() * 1000) if 'start_time' in locals() else 0
        
        return {
            "error": str(e),
            "results": [],
            "count": 0,
            "execution_time_ms": execution_time
        }

# Ontology and Mapping

async def get_entity_type_mapping(entity_type: str) -> Optional[Dict[str, Any]]:
    """
    Get FIBO class mapping for an entity type.
    """
    try:
        supabase = get_supabase()
        response = await supabase.table("entity_mappings").select("*").eq("entity_type", entity_type).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    except Exception as e:
        logger.error(f"Error getting entity type mapping: {e}")
        return None

async def get_relationship_type_mapping(relationship_type: str) -> Optional[Dict[str, Any]]:
    """
    Get FIBO property mapping for a relationship type.
    """
    try:
        supabase = get_supabase()
        response = await supabase.table("relationship_mappings").select("*").eq("relationship_type", relationship_type).execute()
        
        if response.data:
            return response.data[0]
        return None
    
    except Exception as e:
        logger.error(f"Error getting relationship type mapping: {e}")
        return None

async def sync_entities_to_neo4j() -> int:
    """
    Synchronize entities from Supabase to Neo4j.
    Only sync entities that don't have a Neo4j ID yet.
    """
    try:
        supabase = get_supabase()
        
        # Get entities without Neo4j ID
        response = await supabase.table("kg_entities").select("*").is_("neo4j_id", "null").execute()
        entities = response.data
        
        count = 0
        for entity in entities:
            neo4j_id = await create_entity_in_neo4j(entity)
            
            if neo4j_id:
                # Update the Neo4j ID
                await supabase.table("kg_entities").update({"neo4j_id": str(neo4j_id)}).eq("id", entity["id"]).execute()
                count += 1
        
        return count
    
    except Exception as e:
        logger.error(f"Error syncing entities to Neo4j: {e}")
        return 0

async def sync_relationships_to_neo4j() -> int:
    """
    Synchronize relationships from Supabase to Neo4j.
    Only sync relationships that don't have a Neo4j ID yet.
    """
    try:
        supabase = get_supabase()
        
        # Get relationships without Neo4j ID
        response = await supabase.table("kg_relationships").select("*").is_("neo4j_id", "null").execute()
        relationships = response.data
        
        count = 0
        for relationship in relationships:
            neo4j_id = await create_relationship_in_neo4j(relationship)
            
            if neo4j_id:
                # Update the Neo4j ID
                await supabase.table("kg_relationships").update({"neo4j_id": str(neo4j_id)}).eq("id", relationship["id"]).execute()
                count += 1
        
        return count
    
    except Exception as e:
        logger.error(f"Error syncing relationships to Neo4j: {e}")
        return 0

async def convert_nl_to_cypher(query_text: str) -> str:
    """
    Convert natural language query to Cypher.
    This is a placeholder - in a real system, this would use an LLM or similar.
    """
    # This is a very simple implementation for demonstration
    # In a real system, you would use a more sophisticated approach
    
    lower_query = query_text.lower()
    
    if "list all" in lower_query or "show all" in lower_query or "get all" in lower_query:
        entity_type = None
        
        # Try to detect entity type
        for common_type in ["bank", "customer", "account", "transaction", "product"]:
            if common_type in lower_query:
                entity_type = common_type.capitalize()
                break
        
        if entity_type:
            return f"MATCH (e:{entity_type}) RETURN e LIMIT 100"
        else:
            return "MATCH (e) RETURN e LIMIT 100"
    
    elif "relationship" in lower_query or "connected to" in lower_query or "related to" in lower_query:
        return "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 100"
    
    # Default query
    return "MATCH (n) RETURN n LIMIT 10"
