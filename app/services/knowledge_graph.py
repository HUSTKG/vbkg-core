from typing import List, Dict, Any, Optional, Union
from fastapi import HTTPException, status
from py2neo import Graph, Node, Relationship, NodeMatcher
import uuid

from app.core.config import settings


class KnowledgeGraphService:
    def __init__(self):
        # Connect to Neo4j database
        self.graph = Graph(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self.node_matcher = NodeMatcher(self.graph)

    async def create_entity(
        self,
        entity_text: str,
        entity_type: str,
        properties: Dict[str, Any],
        fibo_class: Optional[str] = None,
        source_document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new entity in the knowledge graph"""
        try:
            # Create a unique ID for the entity
            entity_id = str(uuid.uuid4())
            
            # Prepare properties
            entity_properties = {
                "id": entity_id,
                "text": entity_text,
                "type": entity_type
            }
            
            # Add optional properties
            if fibo_class:
                entity_properties["fibo_class"] = fibo_class
                
            if source_document_id:
                entity_properties["source_document_id"] = source_document_id
                
            # Add custom properties
            entity_properties.update(properties)
            
            # Create node in Neo4j
            tx = self.graph.begin()
            node = Node(entity_type, **entity_properties)
            tx.create(node)
            tx.commit()
            
            # Register entity in Supabase for tracking
            await self._register_entity_in_supabase(
                entity_id=entity_id,
                entity_text=entity_text,
                entity_type=entity_type,
                neo4j_id=str(node.identity),
                fibo_class=fibo_class,
                source_document_id=source_document_id,
                properties=properties
            )
            
            return {
                "id": entity_id,
                "neo4j_id": str(node.identity),
                "text": entity_text,
                "type": entity_type,
                "fibo_class": fibo_class,
                "properties": properties
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating entity: {str(e)}"
            )

    async def create_or_merge_entity(
        self,
        entity_text: str,
        entity_type: str,
        properties: Dict[str, Any],
        fibo_class: Optional[str] = None,
        source_document_id: Optional[str] = None
    ) -> str:
        """Create a new entity or merge with existing one if found"""
        try:
            # Try to find existing entity
            existing_entity = self.node_matcher.match(entity_type).where(
                f"_.text = '{entity_text}'"
            ).first()
            
            if existing_entity:
                # Update properties of existing entity
                existing_entity.update(properties)
                
                # Update FIBO class if provided
                if fibo_class and not existing_entity.get("fibo_class"):
                    existing_entity["fibo_class"] = fibo_class
                
                # Update in Neo4j
                self.graph.push(existing_entity)
                
                return existing_entity["id"]
            else:
                # Create new entity
                result = await self.create_entity(
                    entity_text=entity_text,
                    entity_type=entity_type,
                    properties=properties,
                    fibo_class=fibo_class,
                    source_document_id=source_document_id
                )
                return result["id"]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating or merging entity: {str(e)}"
            )

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Dict[str, Any],
        fibo_property: Optional[str] = None,
        source_document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a relationship between two entities"""
        try:
            # Get the source and target nodes
            source_node = self.node_matcher.match().where(f"_.id = '{source_id}'").first()
            target_node = self.node_matcher.match().where(f"_.id = '{target_id}'").first()
            
            if not source_node:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Source entity not found: {source_id}"
                )
                
            if not target_node:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Target entity not found: {target_id}"
                )
            
            # Prepare properties
            rel_properties = {
                "id": str(uuid.uuid4())
            }
            
            # Add optional properties
            if fibo_property:
                rel_properties["fibo_property"] = fibo_property
                
            if source_document_id:
                rel_properties["source_document_id"] = source_document_id
                
            # Add custom properties
            rel_properties.update(properties)
            
            # Create relationship in Neo4j
            tx = self.graph.begin()
            relationship = Relationship(source_node, relationship_type, target_node, **rel_properties)
            tx.create(relationship)
            tx.commit()
            
            # Register relationship in Supabase for tracking
            await self._register_relationship_in_supabase(
                relationship_id=rel_properties["id"],
                source_entity_id=source_id,
                target_entity_id=target_id,
                relationship_type=relationship_type,
                neo4j_id=str(relationship.identity),
                fibo_property=fibo_property,
                source_document_id=source_document_id,
                properties=properties
            )
            
            return {
                "id": rel_properties["id"],
                "neo4j_id": str(relationship.identity),
                "source_id": source_id,
                "target_id": target_id,
                "type": relationship_type,
                "fibo_property": fibo_property,
                "properties": properties
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating relationship: {str(e)}"
            )

    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Get an entity by ID"""
        try:
            # Find entity in Neo4j
            entity = self.node_matcher.match().where(f"_.id = '{entity_id}'").first()
            
            if not entity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Entity not found: {entity_id}"
                )
            
            # Convert to dict
            entity_dict = dict(entity)
            
            # Add labels
            entity_dict["labels"] = list(entity.labels)
            
            return entity_dict
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving entity: {str(e)}"
            )

    async def get_entity_relationships(
        self, 
        entity_id: str,
        direction: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all relationships for an entity"""
        try:
            # Get relationships based on direction
            if direction == "outgoing":
                query = """
                MATCH (s)-[r]->(t)
                WHERE s.id = $entity_id
                RETURN r, s, t
                """
            elif direction == "incoming":
                query = """
                MATCH (s)<-[r]-(t)
                WHERE s.id = $entity_id
                RETURN r, t, s
                """
            else:
                # Both directions
                query = """
                MATCH (n)-[r]-(m)
                WHERE n.id = $entity_id
                RETURN r, n, m
                """
            
            # Execute query
            results = self.graph.run(query, entity_id=entity_id).data()
            
            # Process results
            relationships = []
            for record in results:
                r = record["r"]
                
                # Determine source and target based on direction
                if direction == "outgoing":
                    source = record["s"]
                    target = record["t"]
                elif direction == "incoming":
                    source = record["t"]
                    target = record["s"]
                else:
                    # For bidirectional, determine which node is our entity
                    if record["n"]["id"] == entity_id:
                        source = record["n"]
                        target = record["m"]
                    else:
                        source = record["m"]
                        target = record["n"]
                
                # Convert relationship to dict
                rel_dict = dict(r)
                rel_dict["source_id"] = source["id"]
                rel_dict["target_id"] = target["id"]
                rel_dict["source_text"] = source["text"]
                rel_dict["target_text"] = target["text"]
                rel_dict["type"] = type(r).__name__
                rel_dict["neo4j_id"] = str(r.identity)
                
                relationships.append(rel_dict)
            
            return relationships
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving entity relationships: {str(e)}"
            )

    async def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        fibo_class: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for entities by text"""
        try:
            # Build Cypher query
            cypher = """
            MATCH (n)
            WHERE toLower(n.text) CONTAINS toLower($query)
            """
            
            # Add filters
            if entity_type:
                cypher += f" AND n:{entity_type}"
                
            if fibo_class:
                cypher += f" AND n.fibo_class = '{fibo_class}'"
            
            # Add return and limit
            cypher += f"""
            RETURN n
            LIMIT {limit}
            """
            
            # Execute query
            results = self.graph.run(cypher, query=query).data()
            
            # Process results
            entities = []
            for record in results:
                node = record["n"]
                entity_dict = dict(node)
                entity_dict["labels"] = list(node.labels)
                entity_dict["neo4j_id"] = str(node.identity)
                entities.append(entity_dict)
            
            return entities
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching entities: {str(e)}"
            )

    async def update_entity(
        self,
        entity_id: str,
        properties: Dict[str, Any],
        fibo_class: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update an entity's properties"""
        try:
            # Find entity in Neo4j
            entity = self.node_matcher.match().where(f"_.id = '{entity_id}'").first()
            
            if not entity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Entity not found: {entity_id}"
                )
            
            # Update properties
            for key, value in properties.items():
                entity[key] = value
                
            # Update FIBO class if provided
            if fibo_class:
                entity["fibo_class"] = fibo_class
            
            # Push changes to Neo4j
            self.graph.push(entity)
            
            # Update in Supabase
            await self._update_entity_in_supabase(
                entity_id=entity_id,
                properties=properties,
                fibo_class=fibo_class
            )
            
            # Return updated entity
            return await self.get_entity(entity_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating entity: {str(e)}"
            )

    async def delete_entity(self, entity_id: str) -> Dict[str, Any]:
        """Delete an entity and all its relationships"""
        try:
            # Find entity in Neo4j
            entity = self.node_matcher.match().where(f"_.id = '{entity_id}'").first()
            
            if not entity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Entity not found: {entity_id}"
                )
            
            # Delete entity and all its relationships
            cypher = """
            MATCH (n)
            WHERE n.id = $entity_id
            DETACH DELETE n
            """
            
            self.graph.run(cypher, entity_id=entity_id)
            
            # Delete from Supabase
            await self._delete_entity_from_supabase(entity_id)
            
            return {"success": True, "message": "Entity deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting entity: {str(e)}"
            )

    async def execute_query(
        self,
        query: str,
        parameters: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query against the knowledge graph"""
        try:
            # Execute query
            results = self.graph.run(query, **(parameters or {})).data()
            return results
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error executing query: {str(e)}"
            )

    async def get_entity_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph entities"""
        try:
            # Get entity counts by type
            query = """
            MATCH (n)
            RETURN labels(n) AS type, count(n) AS count
            """
            
            results = self.graph.run(query).data()
            
            # Process results
            stats = {
                "total_entities": 0,
                "by_type": {},
                "by_fibo_class": {}
            }
            
            for record in results:
                entity_type = record["type"][0] if record["type"] else "unknown"
                count = record["count"]
                stats["by_type"][entity_type] = count
                stats["total_entities"] += count
            
            # Get counts by FIBO class
            query = """
            MATCH (n)
            WHERE n.fibo_class IS NOT NULL
            RETURN n.fibo_class AS fibo_class, count(n) AS count
            """
            
            results = self.graph.run(query).data()
            
            for record in results:
                fibo_class = record["fibo_class"]
                count = record["count"]
                stats["by_fibo_class"][fibo_class] = count
            
            return stats
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting entity statistics: {str(e)}"
            )
    async def sync_entities_to_neo4j(
        self,
        entities: List[Dict[str, Any]],
        source_document_id: Optional[str] = None
    ) -> None:
        """Sync entities to Neo4j"""
        try:
            for entity in entities:
                # Create or merge entity
                await self.create_or_merge_entity(
                    entity_text=entity["text"],
                    entity_type=entity["type"],
                    properties=entity.get("properties", {}),
                    fibo_class=entity.get("fibo_class"),
                    source_document_id=source_document_id
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error syncing entities to Neo4j: {str(e)}"
            )

    async def sync_relationships_to_neo4j(
        self,
        relationships: List[Dict[str, Any]],
        source_document_id: Optional[str] = None
    ) -> None:
        """Sync relationships to Neo4j"""
        try:
            for relationship in relationships:
                # Create relationship
                await self.create_relationship(
                    source_id=relationship["source_id"],
                    target_id=relationship["target_id"],
                    relationship_type=relationship["type"],
                    properties=relationship.get("properties", {}),
                    fibo_property=relationship.get("fibo_property"),
                    source_document_id=source_document_id
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error syncing relationships to Neo4j: {str(e)}"
            )

    async def _register_entity_in_supabase(
        self,
        entity_id: str,
        entity_text: str,
        entity_type: str,
        neo4j_id: str,
        fibo_class: Optional[str] = None,
        source_document_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register an entity in Supabase for tracking"""
        from app.core.supabase import get_supabase
        
        try:
            supabase = await get_supabase()
            
            data = {
                "id": entity_id,
                "neo4j_id": neo4j_id,
                "entity_text": entity_text,
                "entity_type": entity_type,
                "is_verified": False
            }
            
            if fibo_class:
                data["fibo_class_id"] = await self._get_fibo_class_id(fibo_class)
                
            if source_document_id:
                data["source_document_id"] = source_document_id
                
            if properties:
                data["properties"] = properties
            
            await supabase.from_("kg_entities").insert(data).execute()
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Error registering entity in Supabase: {e}")

    async def _register_relationship_in_supabase(
        self,
        relationship_id: str,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: str,
        neo4j_id: str,
        fibo_property: Optional[str] = None,
        source_document_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a relationship in Supabase for tracking"""
        from app.core.supabase import get_supabase
        
        try:
            supabase = await get_supabase()
            
            data = {
                "id": relationship_id,
                "neo4j_id": neo4j_id,
                "source_entity_id": source_entity_id,
                "target_entity_id": target_entity_id,
                "relationship_type": relationship_type,
                "is_verified": False
            }
            
            if fibo_property:
                data["fibo_property_id"] = await self._get_fibo_property_id(fibo_property)
                
            if source_document_id:
                data["source_document_id"] = source_document_id
                
            if properties:
                data["properties"] = properties
            
            await supabase.from_("kg_relationships").insert(data).execute()
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Error registering relationship in Supabase: {e}")

    async def _update_entity_in_supabase(
        self,
        entity_id: str,
        properties: Dict[str, Any],
        fibo_class: Optional[str] = None
    ) -> None:
        """Update entity in Supabase"""
        from app.core.supabase import get_supabase
        
        try:
            supabase = await get_supabase()
            
            data = {
                "properties": properties,
                "updated_at": "now()"
            }
            
            if fibo_class:
                data["fibo_class_id"] = await self._get_fibo_class_id(fibo_class)
            
            await supabase.from_("kg_entities").update(data).eq("id", entity_id).execute()
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Error updating entity in Supabase: {e}")

    async def _delete_entity_from_supabase(self, entity_id: str) -> None:
        """Delete entity from Supabase"""
        from app.core.supabase import get_supabase
        
        try:
            supabase = await get_supabase()
            await supabase.from_("kg_entities").delete().eq("id", entity_id).execute()
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Error deleting entity from Supabase: {e}")

    async def _get_fibo_class_id(self, fibo_class_uri: str) -> Optional[int]:
        """Get FIBO class ID from URI"""
        from app.core.supabase import get_supabase
        
        try:
            supabase = await get_supabase()
            response = await supabase.from_("fibo_classes").select("id").eq("uri", fibo_class_uri).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]["id"]
            return None
        except Exception:
            return None

    async def _get_fibo_property_id(self, fibo_property_uri: str) -> Optional[int]:
        """Get FIBO property ID from URI"""
        from app.core.supabase import get_supabase
        
        try:
            supabase = await get_supabase()
            response = await supabase.from_("fibo_properties").select("id").eq("uri", fibo_property_uri).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]["id"]
            return None
        except Exception:
            return None
