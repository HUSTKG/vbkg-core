import json
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from app.schemas.search import GraphSearchQuery, SimilarEntityRequest
from app.utils.similarity import calculate_similarity

from .base import BaseSearchService

logger = logging.getLogger(__name__)


class GraphService(BaseSearchService):
    """Service for graph operations and relationship management"""

    async def graph_search(self, query: GraphSearchQuery) -> Dict[str, Any]:
        """Perform graph traversal search"""
        try:
            start_time = time.time()

            # Extract parameters
            start_entity_id = query.start_entity_id
            start_entity_type = query.start_entity_type
            start_entity_text = query.start_entity_text
            relationship_path = query.relationship_path
            end_entity_type = query.end_entity_type
            max_depth = query.max_depth
            limit = query.limit

            # Find start entity if ID not provided
            if not start_entity_id and start_entity_type and start_entity_text:
                start_entity_query = f"""
                MATCH (n:{start_entity_type})
                WHERE toLower(n.entity_text) CONTAINS toLower('{start_entity_text}')
                RETURN n LIMIT 1
                """

                start_entity_result = self.graph.run(start_entity_query).data()

                if not start_entity_result:
                    return {
                        "paths": [],
                        "total": 0,
                        "execution_time_ms": int((time.time() - start_time) * 1000),
                    }

                start_entity = start_entity_result[0]["n"]
                start_entity_id = start_entity.get(
                    "entity_id", str(start_entity.identity)
                )

            if not start_entity_id:
                raise ValueError("Start entity not found")

            # Build Cypher query for path traversal
            cypher_query = f"MATCH (start {{entity_id: '{start_entity_id}'}})"

            # Build path pattern
            if relationship_path:
                path = "(start)"

                # Handle each relationship in the path
                for i, rel_type in enumerate(relationship_path):
                    var_name = f"n{i}"
                    path += f"-[r{i}:{rel_type}]-({var_name})"

                # Add end entity type constraint if provided
                if end_entity_type and relationship_path:
                    last_var = f"n{len(relationship_path)-1}"
                    path += f" WHERE {last_var}:{end_entity_type}"

                cypher_query += f" MATCH path = {path}"
            else:
                # Use variable length path if no specific path is provided
                if end_entity_type:
                    cypher_query += f" MATCH path = (start)-[*1..{max_depth}]->(end:{end_entity_type})"
                else:
                    cypher_query += f" MATCH path = (start)-[*1..{max_depth}]->(end)"

            # Add return statement and limit
            cypher_query += f" RETURN path LIMIT {limit}"

            # Execute query
            results = self.graph.run(cypher_query).data()

            # Process results
            paths = []
            for item in results:
                path = item["path"]

                # Convert path to a list of nodes and relationships
                path_data = {"nodes": [], "relationships": []}

                # Extract nodes
                for node in path.nodes:
                    raw_properties = dict(node)
                    properties = self._convert_neo4j_properties(raw_properties)
                    node_data = {
                        "id": node.get("entity_id", str(node.identity)),
                        "text": node.get("entity_text", ""),
                        "type": node.get("entity_type", "Unknown"),
                        "properties": properties,
                    }

                    path_data["nodes"].append(node_data)

                # Extract relationships
                for rel in path.relationships:
                    raw_properties = dict(rel)
                    properties = self._convert_neo4j_properties(raw_properties)
                    rel_data = {
                        "id": rel.get("relationship_id", str(rel.identity)),
                        "type": type(rel).__name__,
                        "source_id": rel.start_node.get(
                            "entity_id", str(rel.start_node.identity)
                        ),
                        "target_id": rel.end_node.get(
                            "entity_id", str(rel.end_node.identity)
                        ),
                        "properties": properties,
                    }

                    path_data["relationships"].append(rel_data)

                paths.append(path_data)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            return {
                "paths": paths,
                "total": len(paths),
                "execution_time_ms": execution_time_ms,
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in graph search: {str(e)}",
            )

    async def get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get relationships for an entity"""
        try:
            # Query outgoing relationships
            outgoing_query = f"""
            MATCH (n {{entity_id: '{entity_id}'}})-[r]->(m)
            RETURN r, m
            """

            outgoing_results = self.graph.run(outgoing_query).data()

            # Query incoming relationships
            incoming_query = f"""
            MATCH (n)-[r]->(m {{entity_id: '{entity_id}'}})
            RETURN r, n as m
            """

            incoming_results = self.graph.run(incoming_query).data()

            # Combine results
            relationships = []

            # Process outgoing relationships
            for item in outgoing_results:
                rel = item["r"]
                target = item["m"]

                raw_properties = dict(rel)
                properties = self._convert_neo4j_properties(raw_properties)

                rel_data = {
                    "id": rel.get("relationship_id", str(rel.identity)),
                    "type": type(rel).__name__,
                    "direction": "outgoing",
                    "properties": properties,
                    "target_id": target.get("entity_id", str(target.identity)),
                    "target_text": target.get("entity_text", ""),
                    "target_type": target.get("entity_type", "Unknown"),
                }

                relationships.append(rel_data)

            # Process incoming relationships
            for item in incoming_results:
                rel = item["r"]
                source = item["m"]
                raw_properties = dict(rel)
                properties = self._convert_neo4j_properties(raw_properties)

                rel_data = {
                    "id": rel.get("relationship_id", str(rel.identity)),
                    "type": type(rel).__name__,
                    "direction": "incoming",
                    "properties": properties,
                    "source_id": source.get("entity_id", str(source.identity)),
                    "source_text": source.get("entity_text", ""),
                    "source_type": source.get("entity_type", "Unknown"),
                }

                relationships.append(rel_data)

            return relationships
        except Exception as e:
            logger.error(f"Error getting entity relationships: {e}")
            return []

    async def get_similar_entities(
        self,
        entity_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        entity_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get similar entities based on embedding similarity"""
        if not self.openai_available:
            return []

        try:
            # Get entity from PostgreSQL
            supabase = await self.get_supabase_client()

            entity_response = await (
                supabase.table("kg_entities")
                .select("id, entity_text, embedding")
                .eq("id", entity_id)
                .eq("is_active", True)
                .single()
                .execute()
            )

            if not entity_response.data:
                return []

            entity = entity_response.data
            entity_embedding_str = entity.get("embedding")

            if not entity_embedding_str:
                # If entity doesn't have embedding, generate one
                from .embedding_service import EmbeddingService
                embedding_service = EmbeddingService()
                
                entity_text = entity.get("entity_text", "")
                if not entity_text:
                    return []

                entity_embedding = await embedding_service._generate_embedding(entity_text)

                # Update entity with embedding
                await (
                    supabase.table("kg_entities")
                    .update({"embedding": json.dumps(entity_embedding)})
                    .eq("id", entity_id)
                    .execute()
                )
            else:
                # Parse existing embedding
                entity_embedding = json.loads(entity_embedding_str)

            # Get all entities with embeddings
            db_query = (
                supabase.table("kg_entities")
                .select("id, entity_text, entity_type, embedding")
                .eq("is_active", True)
                .not_.is_("embedding", "null")
                .neq("id", entity_id)
            )

            if entity_types:
                db_query = db_query.in_("entity_type", entity_types)

            response = await db_query.execute()
            entities = response.data

            # Calculate similarity for each entity
            similar_entities = []
            for other_entity in entities:
                if other_entity.get("embedding"):
                    try:
                        other_embedding = json.loads(other_entity["embedding"])
                        similarity = calculate_similarity(
                            entity_embedding, other_embedding, method="cosine"
                        )

                        if similarity >= similarity_threshold:
                            similar_entities.append(
                                {
                                    "id": other_entity["id"],
                                    "text": other_entity["entity_text"],
                                    "type": other_entity["entity_type"],
                                    "similarity_score": float(similarity),
                                }
                            )
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(
                            f"Error processing embedding for entity {other_entity['id']}: {e}"
                        )
                        continue

            # Sort by similarity and limit
            similar_entities.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar_entities[:limit]

        except Exception as e:
            logger.error(f"Error getting similar entities: {e}")
            return []

    async def find_similar_entities(
        self, request: SimilarEntityRequest
    ) -> List[Dict[str, Any]]:
        """Find entities similar to a given entity"""
        try:
            similar_entities = await self.get_similar_entities(
                entity_id=request.entity_id,
                limit=request.limit,
                similarity_threshold=request.similarity_threshold,
                entity_types=request.entity_types,
            )

            return similar_entities
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error finding similar entities: {str(e)}",
            )

    async def get_search_suggestions(
        self, partial_query: str, limit: int = 5
    ) -> List[str]:
        """Get search suggestions based on partial query for banking context"""

        if len(partial_query) < 2:
            return []

        supabase = await self.get_supabase_client()

        # Search for banking entities that start with or contain the partial query
        response = await (
            supabase.table("kg_entities")
            .select("entity_text, entity_type")
            .ilike("entity_text", f"%{partial_query}%")
            .eq("is_active", True)
            .order("confidence", desc=True)
            .limit(limit * 2)  # Get more to diversify
            .execute()
        )

        suggestions = []
        seen_texts = set()

        # Prioritize banking-related entities
        banking_priority_types = [
            "BANK", "BRANCH", "ACCOUNT", "PRODUCT", "SERVICE", 
            "REGULATION", "CUSTOMER", "TRANSACTION", "CARD", "LOAN"
        ]

        # First, add high-priority banking entities
        for entity in response.data:
            text = entity["entity_text"]
            entity_type = entity.get("entity_type", "")
            
            if (text not in seen_texts and len(suggestions) < limit and 
                entity_type.upper() in banking_priority_types):
                suggestions.append(text)
                seen_texts.add(text)

        # Then fill remaining slots with other entities
        for entity in response.data:
            text = entity["entity_text"]
            if text not in seen_texts and len(suggestions) < limit:
                suggestions.append(text)
                seen_texts.add(text)

        return suggestions
