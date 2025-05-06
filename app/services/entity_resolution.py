from typing import List, Dict, Any, Optional, Tuple, Set, Union
from uuid import UUID
import logging
import asyncio

from postgrest.types import CountMethod
import numpy as np
from datetime import datetime
import json

from app.core.supabase import get_supabase
from app.utils.neo4j import get_neo4j_driver
from app.nlp.embeddings import get_entity_embedding, calculate_similarity
from app.schemas.entity import EntityConflict, EntityResolution, Entity

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_TEXT_SIMILARITY_THRESHOLD = 0.8
DEFAULT_EMBEDDING_SIMILARITY_THRESHOLD = 0.9
DEFAULT_MAX_CONFLICTS_PER_ENTITY = 5
ENTITY_BATCH_SIZE = 100

class EntityResolutionService:
    """Service for detecting and resolving entity conflicts in the knowledge graph."""

    def __init__(self):
        self.neo4j_driver = get_neo4j_driver()

    async def find_entity_conflicts(
        self,
        entity_id: UUID,
        text_threshold: float = DEFAULT_TEXT_SIMILARITY_THRESHOLD,
        embedding_threshold: float = DEFAULT_EMBEDDING_SIMILARITY_THRESHOLD,
        max_conflicts: int = DEFAULT_MAX_CONFLICTS_PER_ENTITY
    ) -> List[Dict[str, Any]]:
        """
        Find potential conflicts for a given entity.
        
        Args:
            entity_id: ID of the entity to check for conflicts
            text_threshold: Text similarity threshold
            embedding_threshold: Embedding similarity threshold
            max_conflicts: Maximum number of conflicts to return
            
        Returns:
            List of potential conflicts
        """
        try:
            supabase = await get_supabase()
            # Get the entity
            entity_response = await supabase.table("kg_entities").select("*").eq("id", str(entity_id)).execute()
            if not entity_response.data:
                logger.warning(f"Entity {entity_id} not found")
                return []
            
            entity = entity_response.data[0]
            entity_text = entity["entity_text"].lower()
            entity_type = entity["entity_type"]
            entity_embedding = entity.get("embedding")
            
            # Search for similar entities of the same type
            similar_entities_response = await supabase.table("kg_entities") \
                .select("*") \
                .neq("id", str(entity_id)) \
                .eq("entity_type", entity_type) \
                .execute()
            
            similar_entities = similar_entities_response.data
            
            # Calculate similarities and identify conflicts
            conflicts = []
            
            for similar_entity in similar_entities:
                similar_text = similar_entity["entity_text"].lower()
                
                # Calculate text similarity score
                text_similarity = self._calculate_text_similarity(entity_text, similar_text)
                
                # Check text similarity first as a quick filter
                if text_similarity >= text_threshold:
                    conflict_type = "possible_duplicate"
                    similarity_score = text_similarity
                    
                    # If embeddings are available, calculate embedding similarity for more accuracy
                    if entity_embedding and similar_entity.get("embedding"):
                        embedding_similarity = await calculate_similarity(
                            entity_embedding, 
                            similar_entity["embedding"]
                        )
                        
                        if embedding_similarity >= embedding_threshold:
                            # Higher confidence due to embedding similarity
                            similarity_score = (text_similarity + embedding_similarity) / 2
                            conflict_type = "high_confidence_duplicate"
                    
                    conflicts.append({
                        "entity_id_1": str(entity_id),
                        "entity_id_2": similar_entity["id"],
                        "similarity_score": similarity_score,
                        "conflict_type": conflict_type,
                        "detection_method": "embedding_similarity" if entity_embedding else "text_similarity"
                    })
                
                # Check for property conflicts
                elif self._has_property_conflicts(entity, similar_entity):
                    conflicts.append({
                        "entity_id_1": str(entity_id),
                        "entity_id_2": similar_entity["id"],
                        "similarity_score": 0.7,  # Default score for property conflicts
                        "conflict_type": "inconsistent_attributes",
                        "detection_method": "property_comparison"
                    })
                
                if len(conflicts) >= max_conflicts:
                    break
            
            # Sort conflicts by similarity score (descending)
            conflicts.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return conflicts[:max_conflicts]
            
        except Exception as e:
            logger.error(f"Error finding entity conflicts: {e}")
            return []

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity between two strings.
        Uses a combination of Jaccard similarity and character-level matching.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        # Guard against empty strings
        if not text1 or not text2:
            return 0.0
        
        # Simple exact match
        if text1 == text2:
            return 1.0
        
        # Compute Jaccard similarity on word tokens
        set1 = set(text1.lower().split())
        set2 = set(text2.lower().split())
        
        if not set1 or not set2:
            return 0.0
        
        jaccard = len(set1.intersection(set2)) / len(set1.union(set2))
        
        # Add character-level similarity for Vietnamese text
        # (to handle accents and special characters better)
        chars1 = set(text1.lower())
        chars2 = set(text2.lower())
        
        if chars1 and chars2:
            char_jaccard = len(chars1.intersection(chars2)) / len(chars1.union(chars2))
            return (jaccard + char_jaccard) / 2
        
        return jaccard

    def _has_property_conflicts(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> bool:
        """
        Check if two entities have conflicting properties.
        
        Args:
            entity1: First entity
            entity2: Second entity
            
        Returns:
            True if entities have conflicting properties, False otherwise
        """
        # Extract properties
        props1 = entity1.get("properties", {})
        props2 = entity2.get("properties", {})
        
        # If no properties, no conflicts
        if not props1 or not props2:
            return False
        
        # Find common properties
        common_props = set(props1.keys()).intersection(set(props2.keys()))
        
        # Check for conflicts in common properties
        for prop in common_props:
            # Skip if values are identical
            if props1[prop] == props2[prop]:
                continue
                
            # For non-string values, we consider any difference a conflict
            if not isinstance(props1[prop], str) or not isinstance(props2[prop], str):
                return True
                
            # For string values, check if they're significantly different
            # (allows for minor variations in formatting, etc.)
            if self._calculate_text_similarity(str(props1[prop]), str(props2[prop])) < 0.7:
                return True
                
        return False

    async def create_entity_conflict(
        self,
        entity_id_1: UUID,
        entity_id_2: UUID,
        similarity_score: float,
        conflict_type: str = "possible_duplicate",
        detection_method: str = "text_similarity"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new entity conflict record.
        
        Args:
            entity_id_1: First entity ID
            entity_id_2: Second entity ID
            similarity_score: Calculated similarity score
            conflict_type: Type of conflict
            detection_method: Method used to detect the conflict
            
        Returns:
            Created conflict record or None on error
        """
        try:
            supabase = await get_supabase()
            # Check if conflict already exists
            existing_response = await supabase.table("entity_conflicts") \
                .select("*") \
                .eq("entity_id_1", str(entity_id_1)) \
                .eq("entity_id_2", str(entity_id_2)) \
                .execute()
                
            if existing_response.data:
                # Conflict already exists
                return existing_response.data[0]
            
            # Also check for the reverse order (entity_id_2, entity_id_1)
            existing_response = await supabase.table("entity_conflicts") \
                .select("*") \
                .eq("entity_id_1", str(entity_id_2)) \
                .eq("entity_id_2", str(entity_id_1)) \
                .execute()
                
            if existing_response.data:
                # Conflict already exists in reverse order
                return existing_response.data[0]
            
            # Create new conflict
            conflict_data = {
                "entity_id_1": str(entity_id_1),
                "entity_id_2": str(entity_id_2),
                "similarity_score": similarity_score,
                "conflict_type": conflict_type,
                "status": "pending",
                "metadata": {
                    "detection_method": detection_method,
                    "detection_time": datetime.utcnow().isoformat()
                }
            }
            
            response = await supabase.table("entity_conflicts").insert(conflict_data).execute()
            if response.data:
                logger.info(f"Created entity conflict between {entity_id_1} and {entity_id_2} with score {similarity_score}")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating entity conflict: {e}")
            return None

    async def resolve_entity_conflict(
        self,
        conflict_id: UUID,
        resolution: EntityResolution,
        resolved_by: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve an entity conflict.
        
        Args:
            conflict_id: ID of the conflict to resolve
            resolution: Resolution details
            resolved_by: ID of the user who resolved the conflict
            
        Returns:
            Updated conflict record or None on error
        """
        try:
            supabase = await get_supabase() 
            # Get conflict details
            conflict_response = await supabase.table("entity_conflicts") \
                .select("*, entity_id_1(*), entity_id_2(*)") \
                .eq("id", str(conflict_id)) \
                .execute()
                
            if not conflict_response.data:
                logger.warning(f"Conflict {conflict_id} not found")
                return None
                
            conflict = conflict_response.data[0]
            
            # Extract entity information
            entity1 = conflict["entity_id_1"]
            entity2 = conflict["entity_id_2"]
            
            # Apply resolution based on resolution type
            resolution_result = {}
            
            if resolution.resolution_type == "merge":
                # Merge the two entities
                merged_entity = await self.merge_entities(
                    entity1_id=UUID(entity1["id"]),
                    entity2_id=UUID(entity2["id"]),
                    keep_id=resolution.keep_entity_id if resolution.keep_entity_id else None,
                    merged_properties=resolution.merged_properties,
                    resolved_by=resolved_by
                )
                
                resolution_result = {
                    "action": "merge",
                    "merged_entity_id": merged_entity["id"] if merged_entity else None
                }
                resolution_status = "resolved"
                
            elif resolution.resolution_type == "keep_separate":
                # Keep entities separate, just mark as resolved
                resolution_result = {
                    "action": "keep_separate",
                    "reason": resolution.notes or "Manually determined to be separate entities"
                }
                resolution_status = "resolved"
                
            else:  # "delete" resolution type
                # Delete one entity and keep the other
                entity_to_keep = entity2["id"] if resolution.keep_entity_id == entity1["id"] else entity1["id"]
                entity_to_delete = entity1["id"] if entity_to_keep == entity2["id"] else entity2["id"]
                
                delete_success = await self.delete_entity(UUID(entity_to_delete))
                
                resolution_result = {
                    "action": "delete",
                    "deleted_entity_id": entity_to_delete,
                    "kept_entity_id": entity_to_keep,
                    "success": delete_success
                }
                resolution_status = "resolved"
            
            # Update conflict status
            update_data = {
                "status": resolution_status,
                "resolution_notes": resolution.notes,
                "resolved_by": str(resolved_by),
                "resolution_time": datetime.utcnow().isoformat(),
                "resolution_details": resolution_result
            }
            
            response = await supabase.table("entity_conflicts") \
                .update(update_data) \
                .eq("id", str(conflict_id)) \
                .execute()
                
            if response.data:
                logger.info(f"Resolved entity conflict {conflict_id} with action {resolution.resolution_type}")
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error resolving entity conflict {conflict_id}: {e}")
            return None

    async def merge_entities(
        self,
        entity1_id: UUID,
        entity2_id: UUID,
        keep_id: Optional[UUID] = None,
        merged_properties: Optional[Dict[str, Any]] = None,
        resolved_by: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Merge two entities into one.
        
        Args:
            entity1_id: First entity ID
            entity2_id: Second entity ID
            keep_id: ID of the entity to keep (if None, create a new entity)
            merged_properties: Properties for the merged entity
            resolved_by: ID of the user who initiated the merge
            
        Returns:
            The merged entity or None on error
        """
        try:
            supabase = await get_supabase()
            # Get both entities
            entity1_response = await supabase.table("kg_entities").select("*").eq("id", str(entity1_id)).execute()
            entity2_response = await supabase.table("kg_entities").select("*").eq("id", str(entity2_id)).execute()
            
            if not entity1_response.data or not entity2_response.data:
                logger.warning(f"One or both entities not found: {entity1_id}, {entity2_id}")
                return None
                
            entity1 = entity1_response.data[0]
            entity2 = entity2_response.data[0]
            
            # Determine which entity to keep
            if keep_id is None:
                # Create a new entity with merged properties
                target_entity_id = None
                create_new = True
            else:
                target_entity_id = keep_id
                create_new = False
            
            # Merge properties if provided, otherwise use defaults
            if not merged_properties:
                # Default merging strategy
                merged_properties = self._merge_entity_properties(entity1, entity2)
            
            # Handle the database update
            async with asyncio.Lock():  # Ensure atomicity of the merge operation
                # Create new entity if needed
                if create_new:
                    new_entity_data = {
                        "entity_text": merged_properties["entity_text"],
                        "entity_type": entity1["entity_type"],  # Use type from entity1
                        "properties": merged_properties["properties"],
                        "is_verified": True,
                        "verified_by": str(resolved_by) if resolved_by else None,
                        "verification_notes": "Created by entity merge",
                        "source_document_id": entity1.get("source_document_id") or entity2.get("source_document_id")
                    }
                    
                    # Generate a new embedding for the merged entity if both entities had embeddings
                    if entity1.get("embedding") and entity2.get("embedding"):
                        from app.nlp.embeddings import get_text_embedding
                        
                        # Create the text for embedding
                        embedding_text = f"{entity1['entity_type']}: {merged_properties['entity_text']}"
                        new_embedding = await get_text_embedding(embedding_text)
                        
                        if new_embedding:
                            new_entity_data["embedding"] = new_embedding
                    
                    new_entity_response = await supabase.table("kg_entities").insert(new_entity_data).execute()
                    if not new_entity_response.data:
                        logger.error(f"Failed to create new entity during merge of {entity1_id} and {entity2_id}")
                        return None
                        
                    merged_entity = new_entity_response.data[0]
                    target_entity_id = UUID(merged_entity["id"])
                else:
                    # Update existing entity
                    target_entity = entity1 if str(target_entity_id) == entity1["id"] else entity2
                    
                    update_data = {
                        "entity_text": merged_properties["entity_text"],
                        "properties": merged_properties["properties"],
                        "is_verified": True,
                        "verified_by": str(resolved_by) if resolved_by else target_entity.get("verified_by"),
                        "verification_notes": target_entity.get("verification_notes", "") + " | Updated by entity merge"
                    }
                    
                    # Generate a new embedding for the merged entity if both entities had embeddings
                    if entity1.get("embedding") and entity2.get("embedding"):
                        from app.nlp.embeddings import get_text_embedding
                        
                        # Create the text for embedding
                        embedding_text = f"{target_entity['entity_type']}: {merged_properties['entity_text']}"
                        new_embedding = await get_text_embedding(embedding_text)
                        
                        if new_embedding:
                            update_data["embedding"] = new_embedding
                    
                    update_response = await supabase.table("kg_entities") \
                        .update(update_data) \
                        .eq("id", str(target_entity_id)) \
                        .execute()
                    
                    if not update_response.data:
                        logger.error(f"Failed to update entity {target_entity_id} during merge")
                        return None
                    
                    merged_entity = update_response.data[0]
                
                # Update relationships pointing to the entities being merged
                await self._update_entity_relationships(
                    source_id1=entity1_id,
                    source_id2=entity2_id,
                    target_id=target_entity_id
                )
                
                # Update Neo4j graph if available
                if hasattr(self, 'neo4j_driver') and self.neo4j_driver:
                    await self._merge_entities_in_neo4j(
                        entity1_id=entity1_id,
                        entity2_id=entity2_id,
                        target_entity_id=target_entity_id,
                        create_new=create_new
                    )
                
                # Delete the merged entities if they're not the target
                if str(entity1_id) != str(target_entity_id):
                    await supabase.table("kg_entities").delete().eq("id", str(entity1_id)).execute()
                
                if str(entity2_id) != str(target_entity_id):
                    await supabase.table("kg_entities").delete().eq("id", str(entity2_id)).execute()
            
            # Log the merge
            logger.info(f"Merged entities {entity1_id} and {entity2_id} into {target_entity_id}")
            
            # Return the merged entity
            return merged_entity
            
        except Exception as e:
            logger.error(f"Error merging entities {entity1_id} and {entity2_id}: {e}")
            return None

    def _merge_entity_properties(self, entity1: Dict[str, Any], entity2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge properties of two entities.
        
        Args:
            entity1: First entity
            entity2: Second entity
            
        Returns:
            Dictionary with merged properties
        """
        # Choose the entity text (prefer the longer or more detailed one)
        if len(entity1["entity_text"]) > len(entity2["entity_text"]):
            entity_text = entity1["entity_text"]
        else:
            entity_text = entity2["entity_text"]
        
        # Merge properties, giving priority to verified entities
        props1 = entity1.get("properties", {})
        props2 = entity2.get("properties", {})
        
        # Start with all properties from both entities
        merged_props = {**props1, **props2}
        
        # For conflicting properties, use values from the verified entity if possible
        for key in set(props1.keys()).intersection(set(props2.keys())):
            if entity1.get("is_verified", False) and not entity2.get("is_verified", False):
                merged_props[key] = props1[key]
            elif entity2.get("is_verified", False) and not entity1.get("is_verified", False):
                merged_props[key] = props2[key]
            # If both are verified or both are unverified, keep the more informative value
            elif isinstance(props1[key], str) and isinstance(props2[key], str):
                if len(str(props1[key])) > len(str(props2[key])):
                    merged_props[key] = props1[key]
                else:
                    merged_props[key] = props2[key]
        
        return {
            "entity_text": entity_text,
            "properties": merged_props
        }

    async def _update_entity_relationships(
        self,
        source_id1: UUID,
        source_id2: UUID,
        target_id: UUID | None
    ) -> None:
        """
        Update relationships when merging entities.
        
        Args:
            source_id1: First entity ID being merged
            source_id2: Second entity ID being merged
            target_id: Target entity ID that will remain after merge
        """
        try:
            supabase = await get_supabase()
            # Update relationships where the entities are the source
            await supabase.table("kg_relationships") \
                .update({"source_entity_id": str(target_id)}) \
                .eq("source_entity_id", str(source_id1)) \
                .execute()
                
            await supabase.table("kg_relationships") \
                .update({"source_entity_id": str(target_id)}) \
                .eq("source_entity_id", str(source_id2)) \
                .execute()
            
            # Update relationships where the entities are the target
            await supabase.table("kg_relationships") \
                .update({"target_entity_id": str(target_id)}) \
                .eq("target_entity_id", str(source_id1)) \
                .execute()
                
            await supabase.table("kg_relationships") \
                .update({"target_entity_id": str(target_id)}) \
                .eq("target_entity_id", str(source_id2)) \
                .execute()
            
            # Delete any duplicate relationships that might have been created
            # This requires a more complex query or a custom function in the database
            # For now, we'll handle it with a basic approach
            
            # Get all relationships for the target entity
            source_rels_response = await supabase.table("kg_relationships") \
                .select("*") \
                .eq("source_entity_id", str(target_id)) \
                .execute()
                
            target_rels_response = await supabase.table("kg_relationships") \
                .select("*") \
                .eq("target_entity_id", str(target_id)) \
                .execute()
            
            source_rels = source_rels_response.data
            target_rels = target_rels_response.data
            
            # Identify duplicates in source relationships
            seen_source_relations = {}
            duplicate_ids = []
            
            for rel in source_rels:
                key = f"{rel['relationship_type']}_{rel['target_entity_id']}"
                if key in seen_source_relations:
                    # This is a duplicate
                    duplicate_ids.append(rel["id"])
                else:
                    seen_source_relations[key] = rel["id"]
            
            # Identify duplicates in target relationships
            seen_target_relations = {}
            
            for rel in target_rels:
                key = f"{rel['relationship_type']}_{rel['source_entity_id']}"
                if key in seen_target_relations:
                    # This is a duplicate
                    duplicate_ids.append(rel["id"])
                else:
                    seen_target_relations[key] = rel["id"]
            
            # Delete duplicate relationships
            if duplicate_ids:
                for dup_id in duplicate_ids:
                    await supabase.table("kg_relationships").delete().eq("id", dup_id).execute()
                
                logger.info(f"Deleted {len(duplicate_ids)} duplicate relationships after merging entities")
        
        except Exception as e:
            logger.error(f"Error updating relationships during entity merge: {e}")
            raise

    async def _merge_entities_in_neo4j(
        self,
        entity1_id: UUID,
        entity2_id: UUID,
        target_entity_id: UUID | None,
        create_new: bool
    ) -> bool:
        """
        Update Neo4j graph when merging entities.
        
        Args:
            entity1_id: First entity ID being merged
            entity2_id: Second entity ID being merged
            target_entity_id: Target entity ID that will remain after merge
            create_new: Whether a new entity will be created
            
        Returns:
            True if successful, False otherwise
        """
        try:
            supabase = await get_supabase()
            # Get Neo4j IDs
            entity1_response = await supabase.table("kg_entities").select("neo4j_id").eq("id", str(entity1_id)).execute()
            entity2_response = await supabase.table("kg_entities").select("neo4j_id").eq("id", str(entity2_id)).execute()
            
            if not entity1_response.data or not entity2_response.data:
                return False
                
            entity1_neo4j_id = entity1_response.data[0].get("neo4j_id")
            entity2_neo4j_id = entity2_response.data[0].get("neo4j_id")
            
            # If Neo4j IDs don't exist, no need to update Neo4j
            if not entity1_neo4j_id or not entity2_neo4j_id:
                return False
            
            async with self.neo4j_driver.session() as session:
                if create_new:
                    # Create a new node and transfer all relationships
                    # First, create the new entity in Neo4j
                    target_response = await supabase.table("kg_entities").select("*").eq("id", str(target_entity_id)).execute()
                    if not target_response.data:
                        return False
                        
                    target_entity = target_response.data[0]
                    
                    create_result = await session.run("""
                        CREATE (e:Entity:`{}` {{
                            entity_id: $entity_id,
                            entity_text: $entity_text,
                            properties: $properties
                        }})
                        RETURN id(e) as neo4j_id
                    """.format(target_entity["entity_type"]), {
                        "entity_id": str(target_entity_id),
                        "entity_text": target_entity["entity_text"],
                        "properties": target_entity.get("properties", {})
                    })
                    
                    record = await create_result.single()
                    if not record:
                        return False
                        
                    target_neo4j_id = record["neo4j_id"]
                    
                    # Update the Neo4j ID in the database
                    await supabase.table("kg_entities").update({
                        "neo4j_id": str(target_neo4j_id)
                    }).eq("id", str(target_entity_id)).execute()
                    
                    # Transfer incoming relationships from entity1 and entity2 to the new entity
                    await session.run("""
                        MATCH (source)-[r]->(e)
                        WHERE id(e) = $entity1_id
                        WITH source, r, e
                        MATCH (target)
                        WHERE id(target) = $target_id
                        CREATE (source)-[r2:SAME_TYPE]->(target)
                        SET r2 = r
                        WITH r
                        DELETE r
                    """, {
                        "entity1_id": int(entity1_neo4j_id),
                        "target_id": int(target_neo4j_id)
                    })
                    
                    await session.run("""
                        MATCH (source)-[r]->(e)
                        WHERE id(e) = $entity2_id
                        WITH source, r, e
                        MATCH (target)
                        WHERE id(target) = $target_id
                        CREATE (source)-[r2:SAME_TYPE]->(target)
                        SET r2 = r
                        WITH r
                        DELETE r
                    """, {
                        "entity2_id": int(entity2_neo4j_id),
                        "target_id": int(target_neo4j_id)
                    })
                    
                    # Transfer outgoing relationships
                    await session.run("""
                        MATCH (e)-[r]->(target)
                        WHERE id(e) = $entity1_id
                        WITH e, r, target
                        MATCH (source)
                        WHERE id(source) = $target_id
                        CREATE (source)-[r2:SAME_TYPE]->(target)
                        SET r2 = r
                        WITH r
                        DELETE r
                    """, {
                        "entity1_id": int(entity1_neo4j_id),
                        "target_id": int(target_neo4j_id)
                    })
                    
                    await session.run("""
                        MATCH (e)-[r]->(target)
                        WHERE id(e) = $entity2_id
                        WITH e, r, target
                        MATCH (source)
                        WHERE id(source) = $target_id
                        CREATE (source)-[r2:SAME_TYPE]->(target)
                        SET r2 = r
                        WITH r
                        DELETE r
                    """, {
                        "entity2_id": int(entity2_neo4j_id),
                        "target_id": int(target_neo4j_id)
                    })
                    
                    # Delete the old entities
                    await session.run("""
                        MATCH (e)
                        WHERE id(e) IN [$entity1_id, $entity2_id]
                        DETACH DELETE e
                    """, {
                        "entity1_id": int(entity1_neo4j_id),
                        "entity2_id": int(entity2_neo4j_id)
                    })
                    
                else:
                    # Keep one of the existing entities and transfer relationships to it
                    target_neo4j_id = None
                    entity_to_delete_id = None
                    
                    # Determine which entity to keep in Neo4j
                    if str(target_entity_id) == str(entity1_id):
                        target_neo4j_id = entity1_neo4j_id
                        entity_to_delete_id = entity2_neo4j_id
                    else:
                        target_neo4j_id = entity2_neo4j_id
                        entity_to_delete_id = entity1_neo4j_id
                    
                    # Transfer incoming relationships
                    await session.run("""
                        MATCH (source)-[r]->(e)
                        WHERE id(e) = $delete_id
                        WITH source, r, e
                        MATCH (target)
                        WHERE id(target) = $target_id
                        CREATE (source)-[r2:SAME_TYPE]->(target)
                        SET r2 = r
                        WITH r
                        DELETE r
                    """, {
                        "delete_id": int(entity_to_delete_id),
                        "target_id": int(target_neo4j_id)
                    })
                    
                    # Transfer outgoing relationships
                    await session.run("""
                        MATCH (e)-[r]->(target)
                        WHERE id(e) = $delete_id
                        WITH e, r, target
                        MATCH (source)
                        WHERE id(source) = $target_id
                        CREATE (source)-[r2:SAME_TYPE]->(target)
                        SET r2 = r
                        WITH r
                        DELETE r
                    """, {
                        "delete_id": int(entity_to_delete_id),
                        "target_id": int(target_neo4j_id)
                    })
                    
                    # Delete the entity being merged
                    await session.run("""
                        MATCH (e)
                        WHERE id(e) = $delete_id
                        DETACH DELETE e
                    """, {
                        "delete_id": int(entity_to_delete_id)
                    })
                    
                    # Update the properties of the remaining entity
                    target_response = await supabase.table("kg_entities").select("*").eq("id", str(target_entity_id)).execute()
                    if target_response.data:
                        target_entity = target_response.data[0]
                        
                        await session.run("""
                            MATCH (e)
                            WHERE id(e) = $target_id
                            SET e.entity_text = $entity_text,
                                e.properties = $properties
                        """, {
                            "target_id": int(target_neo4j_id),
                            "entity_text": target_entity["entity_text"],
                            "properties": target_entity.get("properties", {})
                        })
            
            return True
            
        except Exception as e:
            logger.error(f"Error merging entities in Neo4j: {e}")
            return False

    async def delete_entity(self, entity_id: UUID) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_id: ID of the entity to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            supabase = await get_supabase()
            # Get the entity
            entity_response = await supabase.table("kg_entities").select("*").eq("id", str(entity_id)).execute()
            if not entity_response.data:
                logger.warning(f"Entity {entity_id} not found for deletion")
                return False
                
            entity = entity_response.data[0]
            
            # Delete the entity's relationships
            await supabase.table("kg_relationships").delete().eq("source_entity_id", str(entity_id)).execute()
            await supabase.table("kg_relationships").delete().eq("target_entity_id", str(entity_id)).execute()
            
            # Delete from Neo4j if Neo4j ID exists
            if entity.get("neo4j_id"):
                try:
                    async with self.neo4j_driver.session() as session:
                        await session.run("""
                            MATCH (e)
                            WHERE id(e) = $neo4j_id
                            DETACH DELETE e
                        """, {"neo4j_id": int(entity["neo4j_id"])})
                except Exception as neo4j_error:
                    logger.error(f"Error deleting entity from Neo4j: {neo4j_error}")
                    # Continue with deletion from database even if Neo4j deletion fails
            
            # Delete from database
            await supabase.table("kg_entities").delete().eq("id", str(entity_id)).execute()
            
            logger.info(f"Successfully deleted entity {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entity {entity_id}: {e}")
            return False

    async def batch_detect_conflicts(
        self,
        entity_type: Optional[str] = None,
        threshold: float = DEFAULT_TEXT_SIMILARITY_THRESHOLD,
        batch_size: int = ENTITY_BATCH_SIZE,
        max_conflicts_per_entity: int = DEFAULT_MAX_CONFLICTS_PER_ENTITY
    ) -> Dict[str, Any]:
        """
        Detect conflicts in a batch of entities.
        
        Args:
            entity_type: Optional filter for entity type
            threshold: Similarity threshold for conflict detection
            batch_size: Number of entities to process in each batch
            max_conflicts_per_entity: Maximum conflicts to detect per entity
            
        Returns:
            Dictionary with statistics about the batch process
        """
        try:
            supabase = await get_supabase()
            # Build the query for entities
            query = supabase.table("kg_entities").select("id, entity_text, entity_type")
            
            if entity_type:
                query = query.eq("entity_type", entity_type)
            
            response = await query.limit(batch_size).execute()
            entities = response.data
            
            if not entities:
                return {
                    "status": "completed",
                    "message": "No entities found to process",
                    "entities_processed": 0,
                    "conflicts_detected": 0
                }
            
            stats = {
                "entities_processed": 0,
                "conflicts_detected": 0,
                "errors": 0
            }
            
            # Process entities one by one
            for entity in entities:
                try:
                    # Find conflicts for this entity
                    conflicts = await self.find_entity_conflicts(
                        entity_id=UUID(entity["id"]),
                        text_threshold=threshold,
                        max_conflicts=max_conflicts_per_entity
                    )
                    
                    # Create conflict records
                    for conflict in conflicts:
                        await self.create_entity_conflict(
                            entity_id_1=UUID(conflict["entity_id_1"]),
                            entity_id_2=UUID(conflict["entity_id_2"]),
                            similarity_score=conflict["similarity_score"],
                            conflict_type=conflict["conflict_type"],
                            detection_method=conflict.get("detection_method", "text_similarity")
                        )
                        
                        stats["conflicts_detected"] += 1
                    
                    stats["entities_processed"] += 1
                
                except Exception as e:
                    logger.error(f"Error processing entity {entity['id']} in batch: {e}")
                    stats["errors"] += 1
                    stats["entities_processed"] += 1
            
            return {
                "status": "completed",
                "message": f"Processed {stats['entities_processed']} entities, detected {stats['conflicts_detected']} conflicts",
                **stats
            }
            
        except Exception as e:
            logger.error(f"Error in batch conflict detection: {e}")
            return {
                "status": "failed",
                "message": f"Batch processing failed: {str(e)}",
                "error": str(e)
            }

    async def get_entity_conflicts(
        self,
        status: Optional[str] = "pending",
        conflict_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[EntityConflict]:
        """
        Get entity conflicts with optional filtering.
        
        Args:
            status: Filter by conflict status
            conflict_type: Filter by conflict type
            entity_id: Filter by entity ID (either entity_id_1 or entity_id_2)
            limit: Maximum number of conflicts to return
            offset: Offset for pagination
            
        Returns:
            List of conflict records
        """
        try:
            supabase = await get_supabase()
            # Build the query
            query = supabase.table("entity_conflicts").select("*, entity_id_1(*), entity_id_2(*)")
            
            if status:
                query = query.eq("status", status)
            
            if conflict_type:
                query = query.eq("conflict_type", conflict_type)
            
            if entity_id:
                # Need to query both entity_id_1 and entity_id_2
                # This approach depends on the database's capabilities
                entity_id_str = str(entity_id)
                query = query.or_(f"entity_id_1.eq.{entity_id_str},entity_id_2.eq.{entity_id_str}")
            
            # Apply pagination
            response = await query.range(offset, offset + limit - 1).execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"Error getting entity conflicts: {e}")
            return []

    async def get_conflict_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about entity conflicts.
        
        Returns:
            Dictionary with conflict statistics
        """
        try:
            supabase = await get_supabase()
            
            # Total conflicts
            total_response = await supabase.table("entity_conflicts").select("count", count=CountMethod.exact).execute()
            total_count = total_response.count if hasattr(total_response, 'count') else 0
            
            # Pending conflicts
            pending_response = await supabase.table("entity_conflicts").select("count", count=CountMethod.exact).eq("status", "pending").execute()
            pending_count = pending_response.count if hasattr(pending_response, 'count') else 0
            
            # Resolved conflicts
            resolved_response = await supabase.table("entity_conflicts").select("count", count=CountMethod.exact).eq("status", "resolved").execute()
            resolved_count = resolved_response.count if hasattr(resolved_response, 'count') else 0
            
            # Ignored conflicts
            ignored_response = await supabase.table("entity_conflicts").select("count", count=CountMethod.exact).eq("status", "ignored").execute()
            ignored_count = ignored_response.count if hasattr(ignored_response, 'count') else 0
            
            # Conflicts by type
            type_response = await supabase.rpc(
                "count_conflicts_by_type",
                {}
            ).execute()
            
            conflict_types = type_response.data if type_response.data else []

            if resolved_count is None:
                resolved_count = 0

            if total_count is None:
                total_count = 0
            
            return {
                "total": total_count,
                "pending": pending_count,
                "resolved": resolved_count,
                "ignored": ignored_count,
                "by_type": conflict_types,
                "resolution_rate": (resolved_count / total_count) if total_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting conflict statistics: {e}")
            return {
                "total": 0,
                "pending": 0,
                "resolved": 0,
                "ignored": 0,
                "by_type": [],
                "resolution_rate": 0,
                "error": str(e)
            }

# Initialize service
entity_resolution_service = EntityResolutionService()

# Exported functions that wrap the service methods
async def find_entity_conflicts(
    entity_id: UUID,
    threshold: float = DEFAULT_TEXT_SIMILARITY_THRESHOLD,
    max_conflicts: int = DEFAULT_MAX_CONFLICTS_PER_ENTITY
) -> List[Dict[str, Any]]:
    """
    Find potential conflicts for a given entity.
    """
    return await entity_resolution_service.find_entity_conflicts(
        entity_id=entity_id,
        text_threshold=threshold,
        max_conflicts=max_conflicts
    )

async def create_entity_conflict(
    entity_id_1: UUID,
    entity_id_2: UUID,
    similarity_score: float,
    conflict_type: str = "possible_duplicate"
) -> Optional[Dict[str, Any]]:
    """
    Create a new entity conflict record.
    """
    return await entity_resolution_service.create_entity_conflict(
        entity_id_1=entity_id_1,
        entity_id_2=entity_id_2,
        similarity_score=similarity_score,
        conflict_type=conflict_type
    )

async def resolve_entity_conflict(
    conflict_id: UUID,
    resolution: EntityResolution,
    resolved_by: UUID
) -> Optional[Dict[str, Any]]:
    """
    Resolve an entity conflict.
    """
    return await entity_resolution_service.resolve_entity_conflict(
        conflict_id=conflict_id,
        resolution=resolution,
        resolved_by=resolved_by
    )

async def merge_entities(
    entity1_id: UUID,
    entity2_id: UUID,
    keep_id: Optional[UUID] = None,
    merged_properties: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Merge two entities into one.
    """
    return await entity_resolution_service.merge_entities(
        entity1_id=entity1_id,
        entity2_id=entity2_id,
        keep_id=keep_id,
        merged_properties=merged_properties
    )

async def delete_entity(entity_id: UUID) -> bool:
    """
    Delete an entity.
    """
    return await entity_resolution_service.delete_entity(entity_id=entity_id)

async def batch_detect_conflicts(
    entity_type: Optional[str] = None,
    threshold: float = DEFAULT_TEXT_SIMILARITY_THRESHOLD,
    batch_size: int = ENTITY_BATCH_SIZE
) -> Dict[str, Any]:
    """
    Detect conflicts in a batch of entities.
    """
    return await entity_resolution_service.batch_detect_conflicts(
        entity_type=entity_type,
        threshold=threshold,
        batch_size=batch_size
    )

async def get_entity_conflicts(
    status: Optional[str] = "pending",
    conflict_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    limit: int = 100,
    offset: int = 0
) -> List[EntityConflict]:
    """
    Get entity conflicts with optional filtering.
    """
    return await entity_resolution_service.get_entity_conflicts(
        status=status,
        conflict_type=conflict_type,
        entity_id=entity_id,
        limit=limit,
        offset=offset
    )

async def get_conflict_statistics() -> Dict[str, Any]:
    """
    Get statistics about entity conflicts.
    """
    return await entity_resolution_service.get_conflict_statistics()
