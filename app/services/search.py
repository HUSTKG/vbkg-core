import json
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from fastapi import HTTPException, Path, Query, status
from py2neo import Graph, NodeMatcher, RelationshipMatcher

from app.core.config import settings
from app.schemas.search import (EmbeddingRequest, EntitySearchResult,
                                GraphSearchQuery, SearchRequest,
                                SearchResponse, SearchType,
                                SimilarEntityRequest, SortOrder)


class SearchService:
    def __init__(self):
        # Connect to Neo4j database
        self.graph = Graph(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self.node_matcher = NodeMatcher(self.graph)
        self.rel_matcher = RelationshipMatcher(self.graph)

        # Initialize OpenAI for embeddings if API key is available
        self.openai_available = False
        if settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            
            aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.openai_available = True

    async def search_entities(self, search_request: SearchRequest) -> SearchResponse:
        """Search for entities based on the search request"""
        try:
            start_time = time.time()

            # Choose search strategy based on search_type
            if search_request.search_type == SearchType.EXACT:
                results, total = await self._exact_search(search_request)
            elif search_request.search_type == SearchType.FUZZY:
                results, total = await self._fuzzy_search(search_request)
            elif search_request.search_type == SearchType.SEMANTIC:
                results, total = await self._semantic_search(search_request)
            elif search_request.search_type == SearchType.HYBRID:
                results, total = await self._hybrid_search(search_request)
            else:
                raise ValueError(f"Unknown search type: {search_request.search_type}")

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Include relationships if requested
            if search_request.include_relationships:
                for entity in results:
                    entity.relationships = await self._get_entity_relationships(entity.id)

            # Include similar entities if requested
            if search_request.include_similar_entities:
                for entity in results:
                    entity.similar_entities = await self._get_similar_entities(
                        entity_id=entity.id,
                        limit=5,
                        similarity_threshold=search_request.similarity_threshold or 0.7,
                        entity_types=search_request.entity_types
                    )

            return SearchResponse(
                results=results,
                total=total,
                query=search_request.query,
                search_type=search_request.search_type,
                execution_time_ms=execution_time_ms
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching entities: {str(e)}"
            )

    async def _exact_search(
        self, 
        search_request: SearchRequest
    ) -> Tuple[List[EntitySearchResult], int]:
        """Perform exact text search"""
        query = search_request.query

        # Build Cypher query
        cypher_query = "MATCH (n) WHERE "

        # Add text condition
        cypher_query += f"toLower(n.text) CONTAINS toLower('{query}') "

        # Add entity type filter if provided
        if search_request.entity_types:
            entity_types = [f"n:{entity_type}" for entity_type in search_request.entity_types]
            cypher_query += f"AND ({' OR '.join(entity_types)}) "

        # Add additional filters if provided
        if search_request.filters:
            for filter_item in search_request.filters:
                cypher_query += f"AND n.{filter_item.field} "

                if filter_item.operator == "eq":
                    cypher_query += f"= '{filter_item.value}' "
                elif filter_item.operator == "gt":
                    cypher_query += f"> {filter_item.value} "
                elif filter_item.operator == "lt":
                    cypher_query += f"< {filter_item.value} "
                elif filter_item.operator == "gte":
                    cypher_query += f">= {filter_item.value} "
                elif filter_item.operator == "lte":
                    cypher_query += f"<= {filter_item.value} "
                elif filter_item.operator == "contains":
                    cypher_query += f"CONTAINS '{filter_item.value}' "
                elif filter_item.operator == "in":
                    values = [f"'{v}'" for v in filter_item.value]
                    cypher_query += f"IN [{', '.join(values)}] "

        # Add relationship filters if provided
        if search_request.relationship_filters:
            for rel_filter in search_request.relationship_filters:
                direction = rel_filter.direction
                rel_type = rel_filter.relationship_type

                # Build relationship pattern
                if direction == "outgoing":
                    rel_pattern = f"-[r:{rel_type if rel_type else ''}]->"
                elif direction == "incoming":
                    rel_pattern = f"<-[r:{rel_type if rel_type else ''}]-"
                else:  # both
                    rel_pattern = f"-[r:{rel_type if rel_type else ''}]-"

                # Add target node conditions
                target_conditions = []

                if rel_filter.target_type:
                    target_conditions.append(f":{rel_filter.target_type}")

                if rel_filter.target_property and rel_filter.target_value is not None:
                    target_conditions.append(f"{{{rel_filter.target_property}: '{rel_filter.target_value}'}}")

                target_pattern = f"(m{''.join(target_conditions)})"

                cypher_query += f"AND (n){rel_pattern}{target_pattern} "

        # Add return and count query
        count_query = cypher_query + "RETURN COUNT(n) as total"

        # Add sorting if provided
        if search_request.sort:
            cypher_query += "RETURN n "
            cypher_query += "ORDER BY "

            sort_conditions = []
            for sort_item in search_request.sort:
                direction = "ASC" if sort_item.order == SortOrder.ASC else "DESC"
                sort_conditions.append(f"n.{sort_item.field} {direction}")

            cypher_query += ", ".join(sort_conditions) + " "
        else:
            # Default sort by relevance (exact match score)
            cypher_query += "RETURN n "

        # Add pagination
        cypher_query += f"SKIP {search_request.offset} LIMIT {search_request.limit}"

        # Execute count query
        count_result = self.graph.run(count_query).data()
        total: Any = count_result[0]["total"] if count_result else 0

        # Execute search query
        results = self.graph.run(cypher_query).data()

        # Transform to EntitySearchResult
        entity_results = []
        for item in results:
            node: Any = item["n"]

            # Extract properties

            raw_properties = dict(node)
            properties = self._convert_neo4j_properties(raw_properties)

            # Remove standard fields from properties
            for field in ["id", "text", "type", "fibo_class"]:
                if field in properties:
                    properties.pop(field)

            # Create search result
            entity_result = EntitySearchResult(
                id=node.get("id", str(node.identity)),
                text=node.get("text", ""),
                type=next(iter(node.labels), "Unknown"),
                properties=properties,
                fibo_class=node.get("fibo_class"),
                score=1.0,  # For exact search, all results have score 1.0
                relationships=None,
                similar_entities=None
            )

            entity_results.append(entity_result)

        return entity_results, total

    def _convert_neo4j_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Neo4j properties, handling DateTime objects"""
        converted = {}
        
        for key, value in properties.items():
            if hasattr(value, '__class__') and 'DateTime' in str(value.__class__):
                # Convert Neo4j DateTime to ISO string
                if hasattr(value, 'isoformat'):
                    converted[key] = value.isoformat()
                else:
                    converted[key] = str(value)
            elif hasattr(value, 'strftime'):
                # Handle standard datetime
                converted[key] = value.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            elif isinstance(value, (list, tuple)):
                # Handle lists that might contain DateTime
                converted[key] = [
                    item.isoformat() if hasattr(item, 'isoformat')
                    else str(item) if hasattr(item, '__class__') and 'DateTime' in str(item.__class__)
                    else item
                    for item in value
                ]
            elif isinstance(value, dict):
                # Recursive for nested dicts
                converted[key] = self._convert_neo4j_properties(value)
            else:
                converted[key] = value
        
        return converted

    async def _fuzzy_search(
        self, 
        search_request: SearchRequest
    ) -> Tuple[List[EntitySearchResult], int]:
        """Perform fuzzy text search"""
        query = search_request.query

        # Build Cypher query with apoc.text.fuzzyMatch if available
        # Note: This requires APOC extension in Neo4j
        try:
            # Check if apoc.text.fuzzyMatch is available
            check_query = "CALL dbms.procedures() YIELD name WHERE name = 'apoc.text.fuzzyMatch' RETURN count(*) as count"
            check_result: Any = self.graph.run(check_query).data()
            apoc_available = check_result[0]["count"] > 0 if check_result else False

            if apoc_available:
                # Use APOC for fuzzy matching
                cypher_query = """
                MATCH (n)
                WHERE apoc.text.fuzzyMatch(n.text, $query) > $threshold
                """

                # Add entity type filter if provided
                if search_request.entity_types:
                    entity_types = [f"n:{entity_type}" for entity_type in search_request.entity_types]
                    cypher_query += f"AND ({' OR '.join(entity_types)}) "

                # Add additional filters
                # (similar to exact search implementation)

                # Add return statement with scoring
                cypher_query += """
                RETURN n, apoc.text.fuzzyMatch(n.text, $query) AS score
                ORDER BY score DESC
                SKIP $offset LIMIT $limit
                """

                # Execute query with parameters
                results = self.graph.run(
                    cypher_query, 
                    query=query, 
                    threshold=0.5,  # Adjust threshold as needed
                    offset=search_request.offset,
                    limit=search_request.limit
                ).data()

                # For count query
                count_query = """
                MATCH (n)
                WHERE apoc.text.fuzzyMatch(n.text, $query) > $threshold
                """

                # Add entity type filter for count
                if search_request.entity_types:
                    entity_types = [f"n:{entity_type}" for entity_type in search_request.entity_types]
                    count_query += f"AND ({' OR '.join(entity_types)}) "

                count_query += "RETURN COUNT(n) as total"

                count_result = self.graph.run(count_query, query=query, threshold=0.5).data()
                total: Any = count_result[0]["total"] if count_result else 0
            else:
                # Fallback to a simpler fuzzy search using CONTAINS
                # This is less effective but works without APOC
                return await self._exact_search(search_request)

            # Transform to EntitySearchResult
            entity_results = []
            for item in results:
                node: Any = item["n"]
                score: Any = item.get("score", 0.5)  # Default score if not available

                # Extract properties
                raw_properties = dict(node)
                properties = self._convert_neo4j_properties(raw_properties)

                # Remove standard fields from properties
                for field in ["id", "text", "type", "fibo_class"]:
                    if field in properties:
                        properties.pop(field)

                # Create search result
                entity_result = EntitySearchResult(
                    id=node.get("id", str(node.identity)),
                    text=node.get("text", ""),
                    type=next(iter(node.labels), "Unknown"),
                    properties=properties,
                    fibo_class=node.get("fibo_class"),
                    score=score,
                    relationships=None,
                    similar_entities=None
                )

                entity_results.append(entity_result)

            return entity_results, total
        except Exception as e:
            # Log the error and fall back to exact search
            print(f"Error in fuzzy search, falling back to exact search: {e}")
            return await self._exact_search(search_request)

    async def _semantic_search(
        self, 
        search_request: SearchRequest
    ) -> Tuple[List[EntitySearchResult], int]:
        """Perform semantic search using embeddings"""
        if not self.openai_available:
            # Fall back to fuzzy search if OpenAI is not available
            return await self._fuzzy_search(search_request)

        try:
            from openai import AsyncOpenAI
            
            aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            # Generate embedding for query
            query_embedding = await self._generate_embedding(
                search_request.query, 
                search_request.embedding_model
            )

            # Check if Neo4j has vector capabilities (Neo4j 5.0+)
            # This requires the Neo4j Vector Index plugin
            try:
                check_query = "CALL dbms.procedures() YIELD name WHERE name CONTAINS 'vector' RETURN count(*) as count"
                check_result: Any = self.graph.run(check_query).data()
                vector_plugin_available = check_result[0]["count"] > 0 if check_result else False

                if vector_plugin_available:
                    # Use Neo4j Vector Search if available
                    cypher_query = """
                    CALL db.index.vector.queryNodes('entity_embeddings', $k, $embedding) YIELD node, score
                    WITH node AS n, score
                    """

                    # Add entity type filter if provided
                    if search_request.entity_types:
                        entity_types = [f"n:{entity_type}" for entity_type in search_request.entity_types]
                        cypher_query += f"WHERE ({' OR '.join(entity_types)}) "

                    # Add return statement
                    cypher_query += """
                    RETURN n, score
                    ORDER BY score DESC
                    SKIP $offset LIMIT $limit
                    """

                    # Execute query with parameters
                    results = self.graph.run(
                        cypher_query, 
                        k=search_request.limit + search_request.offset,  # Total records to retrieve
                        embedding=query_embedding,
                        offset=search_request.offset,
                        limit=search_request.limit
                    ).data()

                    # For this approach, we don't have an exact total count
                    # We can estimate based on what we see or run a separate count query
                    total = len(results) + search_request.offset
                else:
                    # Fallback to manual semantic search
                    # This approach is less efficient but works without vector search capabilities

                    # First, get all potential entities with embeddings
                    cypher_query = "MATCH (n) WHERE n.embedding IS NOT NULL "

                    # Add entity type filter if provided
                    if search_request.entity_types:
                        entity_types = [f"n:{entity_type}" for entity_type in search_request.entity_types]
                        cypher_query += f"AND ({' OR '.join(entity_types)}) "

                    cypher_query += "RETURN n"

                    nodes = self.graph.run(cypher_query).data()

                    # Calculate similarity for each node
                    results = []
                    for node_data in nodes:
                        node: Any = node_data["n"]

                        # Get node embedding
                        node_embedding_str = node.get("embedding")
                        if not node_embedding_str:
                            continue

                        # Parse embedding string to list of floats
                        try:
                            node_embedding = json.loads(node_embedding_str)
                        except json.JSONDecodeError:
                            continue

                        # Calculate cosine similarity
                        score = self._cosine_similarity(query_embedding, node_embedding)

                        # Add to results if score is above threshold
                        if score >= (search_request.similarity_threshold or 0.5):
                            results.append({"n": node, "score": score})

                    # Sort by score
                    results.sort(key=lambda x: x["score"], reverse=True)

                    # Apply offset and limit
                    results = results[search_request.offset:search_request.offset + search_request.limit]

                    # Total count
                    total = len(results)
            except Exception as vector_error:
                # Fallback if Neo4j vector search fails
                print(f"Vector search error, falling back to fuzzy search: {vector_error}")
                return await self._fuzzy_search(search_request)

            # Transform to EntitySearchResult
            entity_results = []
            for item in results:
                node = item["n"]
                score: Any = item.get("score", 0.0)

                # Extract properties
                raw_properties = dict(node)
                properties = self._convert_neo4j_properties(raw_properties)

                # Remove standard and large fields from properties
                for field in ["id", "text", "type", "fibo_class", "embedding"]:
                    if field in properties:
                        properties.pop(field)

                # Create search result
                entity_result = EntitySearchResult(
                    id=node.get("id", str(node.identity)),
                    text=node.get("text", ""),
                    type=next(iter(node.labels), "Unknown"),
                    properties=properties,
                    fibo_class=node.get("fibo_class"),
                    score=score,
                    relationships=None,
                    similar_entities=None
                )

                entity_results.append(entity_result)

            return entity_results, total
        except Exception as e:
            # Log the error and fall back to fuzzy search
            print(f"Error in semantic search, falling back to fuzzy search: {e}")
            return await self._fuzzy_search(search_request)

    async def _hybrid_search(
        self, 
        search_request: SearchRequest
    ) -> Tuple[List[EntitySearchResult], int]:
        """Perform hybrid search (combination of exact, fuzzy, and semantic)"""
        try:
            # Perform both exact and semantic searches
            exact_results, exact_total = await self._exact_search(search_request)

            # Only perform semantic search if OpenAI is available
            if self.openai_available:
                semantic_results, semantic_total = await self._semantic_search(search_request)

                # Combine results
                combined_results = {}

                # Add exact results
                for result in exact_results:
                    combined_results[result.id] = result
                    # Boost exact match score
                    combined_results[result.id].score = 1.0

                # Add semantic results, combining scores if entity already exists
                for result in semantic_results:
                    if result.id in combined_results:
                        # Combine scores - you can adjust the weighting
                        combined_results[result.id].score = 0.7 * combined_results[result.id].score + 0.3 * result.score
                    else:
                        combined_results[result.id] = result

                # Convert back to list and sort by score
                results = list(combined_results.values())
                results.sort(key=lambda x: x.score, reverse=True)

                # Apply offset and limit
                results = results[search_request.offset:search_request.offset + search_request.limit]

                # Total count
                total = len(combined_results)

                return results, total
            else:
                # If OpenAI is not available, just return exact results
                return exact_results, exact_total
        except Exception as e:
            # Log the error and fall back to exact search
            print(f"Error in hybrid search, falling back to exact search: {e}")
            return await self._exact_search(search_request)

    async def _get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get relationships for an entity"""
        try:
            # Query outgoing relationships
            outgoing_query = f"""
            MATCH (n {{id: '{entity_id}'}})-[r]->(m)
            RETURN r, m
            """

            outgoing_results = self.graph.run(outgoing_query).data()

            # Query incoming relationships
            incoming_query = f"""
            MATCH (n)-[r]->(m {{id: '{entity_id}'}})
            RETURN r, n as m
            """

            incoming_results = self.graph.run(incoming_query).data()

            # Combine results
            relationships = []

            # Process outgoing relationships
            for item in outgoing_results:
                rel: Any = item["r"]
                target: Any = item["m"]

                raw_properties = dict(rel)
                properties = self._convert_neo4j_properties(raw_properties)

                rel_data = {
                    "id": rel.get("id", str(rel.identity)),
                    "type": type(rel).__name__,
                    "direction": "outgoing",
                    "properties": properties,
                    "target_id": target.get("id", str(target.identity)),
                    "target_text": target.get("text", ""),
                    "target_type": next(iter(target.labels), "Unknown")
                }

                relationships.append(rel_data)

            # Process incoming relationships
            for item in incoming_results:
                rel: Any = item["r"]
                source: Any = item["m"]
                raw_properties = dict(rel)
                properties = self._convert_neo4j_properties(raw_properties)

                rel_data = {
                    "id": rel.get("id", str(rel.identity)),
                    "type": type(rel).__name__,
                    "direction": "incoming",
                    "properties": properties,
                    "source_id": source.get("id", str(source.identity)),
                    "source_text": source.get("text", ""),
                    "source_type": next(iter(source.labels), "Unknown")
                }

                relationships.append(rel_data)

            return relationships
        except Exception as e:
            print(f"Error getting entity relationships: {e}")
            return []

    async def _get_similar_entities(
        self,
        entity_id: str,
        limit: int = 5,
        similarity_threshold: float = 0.7,
        entity_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get similar entities based on embedding similarity"""
        if not self.openai_available:
            return []

        try:
            # First get the entity's embedding
            entity_query = f"""
            MATCH (n {{id: '{entity_id}'}})
            RETURN n
            """

            entity_result: Any = self.graph.run(entity_query).data()

            if not entity_result:
                return []

            entity = entity_result[0]["n"]
            entity_embedding_str = entity.get("embedding")

            if not entity_embedding_str:
                # If entity doesn't have embedding, generate one
                entity_text = entity.get("text", "")
                if not entity_text:
                    return []

                entity_embedding = await self._generate_embedding(entity_text)

                # Update entity with embedding
                update_query = f"""
                MATCH (n {{id: '{entity_id}'}})
                SET n.embedding = '{json.dumps(entity_embedding)}'
                """

                self.graph.run(update_query)
            else:
                # Parse existing embedding
                entity_embedding = json.loads(entity_embedding_str)

            # Now find similar entities
            # Check if Neo4j has vector capabilities
            try:
                check_query = "CALL dbms.procedures() YIELD name WHERE name CONTAINS 'vector' RETURN count(*) as count"
                check_result: Any = self.graph.run(check_query).data()
                vector_plugin_available = check_result[0]["count"] > 0 if check_result else False

                similar_entities = []

                if vector_plugin_available:
                    # Use Neo4j Vector Search
                    cypher_query = """
                    CALL db.index.vector.queryNodes('entity_embeddings', $k, $embedding) YIELD node, score
                    WITH node AS m, score
                    WHERE m.id <> $entity_id
                    """

                    # Add entity type filter if provided
                    if entity_types:
                        entity_types_filter = [f"m:{t}" for t in entity_types]
                        cypher_query += f"AND ({' OR '.join(entity_types_filter)}) "

                    cypher_query += """
                    AND score >= $threshold
                    RETURN m, score
                    ORDER BY score DESC
                    LIMIT $limit
                    """

                    # Execute query
                    similar_results = self.graph.run(
                        cypher_query,
                        k=limit + 1,  # Add 1 to account for the entity itself
                        embedding=entity_embedding,
                        entity_id=entity_id,
                        threshold=similarity_threshold,
                        limit=limit
                    ).data()

                    # Process results
                    for item in similar_results:
                        node: Any = item["m"]
                        score = item.get("score", 0.0)

                        similar_entity = {
                            "id": node.get("id", str(node.identity)),
                            "text": node.get("text", ""),
                            "type": next(iter(node.labels), "Unknown"),
                            "similarity_score": score
                        }

                        similar_entities.append(similar_entity)
                else:
                    # Manual approach using string embeddings
                    # This is much less efficient but works without vector index

                    # Get all entities with embeddings
                    cypher_query = "MATCH (m) WHERE m.embedding IS NOT NULL AND m.id <> $entity_id "

                    # Add entity type filter if provided
                    if entity_types:
                        entity_types_filter = [f"m:{t}" for t in entity_types]
                        cypher_query += f"AND ({' OR '.join(entity_types_filter)}) "

                    cypher_query += "RETURN m"

                    nodes = self.graph.run(cypher_query, entity_id=entity_id).data()

                    # app/services/search.py (continued)

                    # Calculate similarity for each node
                    results = []
                    for node_data in nodes:
                        node = node_data["m"]

                        # Get node embedding
                        node_embedding_str = node.get("embedding")
                        if not node_embedding_str:
                            continue

                        # Parse embedding string to list of floats
                        try:
                            node_embedding = json.loads(node_embedding_str)
                        except json.JSONDecodeError:
                            continue

                        # Calculate cosine similarity
                        score = self._cosine_similarity(entity_embedding, node_embedding)

                        # Add to results if score is above threshold
                        if score >= similarity_threshold:
                            results.append({"m": node, "score": score})

                    # Sort by score and limit results
                    results.sort(key=lambda x: x["score"], reverse=True)
                    results = results[:limit]

                    # Format results
                    for item in results:
                        node = item["m"]
                        score = item["score"]

                        similar_entity = {
                            "id": node.get("id", str(node.identity)),
                            "text": node.get("text", ""),
                            "type": next(iter(node.labels), "Unknown"),
                            "similarity_score": score
                        }

                        similar_entities.append(similar_entity)

                return similar_entities
            except Exception as vector_error:
                print(f"Vector search error: {vector_error}")
                return []
        except Exception as e:
            print(f"Error getting similar entities: {e}")
            return []

    async def _generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding for a text using OpenAI API"""
        if not self.openai_available:
            raise ValueError("OpenAI API is not available")

        from openai import AsyncOpenAI
        
        aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        try:
            # Use specified model or default
            embedding_model = model or "text-embedding-ada-002"

            # Call OpenAI API
            response = await aclient.embeddings.create(model=embedding_model,
            input=text,
            encoding_format="float")

            # Extract embedding
            embedding = response.data[0].embedding

            return embedding
        except Exception as e:
            raise ValueError(f"Error generating embedding: {e}")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same dimension")

        # Convert to numpy arrays for efficient computation
        a = np.array(vec1)
        b = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    async def generate_embedding(self, request: EmbeddingRequest) -> Dict[str, Any]:
        """Generate embedding for a text"""
        if not self.openai_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API is not configured"
            )

        try:
            embedding = await self._generate_embedding(
                text=request.text,
                model=request.model
            )

            return {
                "embedding": embedding,
                "model": request.model or "text-embedding-ada-002",
                "text": request.text,
                "vector_size": len(embedding)
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating embedding: {str(e)}"
            )

    async def find_similar_entities(
        self,
        request: SimilarEntityRequest
    ) -> List[Dict[str, Any]]:
        """Find entities similar to a given entity"""
        try:
            similar_entities = await self._get_similar_entities(
                entity_id=request.entity_id,
                limit=request.limit,
                similarity_threshold=request.similarity_threshold,
                entity_types=request.entity_types
            )

            return similar_entities
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error finding similar entities: {str(e)}"
            )

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
                WHERE toLower(n.text) CONTAINS toLower('{start_entity_text}')
                RETURN n LIMIT 1
                """

                start_entity_result = self.graph.run(start_entity_query).data()

                if not start_entity_result:
                    return {
                        "paths": [],
                        "total": 0,
                        "execution_time_ms": int((time.time() - start_time) * 1000)
                    }

                start_entity = start_entity_result[0]["n"]
                if not start_entity:
                    raise ValueError("Start entity not found")
                start_entity_id = start_entity.get("id", str(start_entity["identity"]))

            if not start_entity_id:
                raise ValueError("Start entity not found")

            # Build Cypher query for path traversal
            cypher_query = f"MATCH (start {{id: '{start_entity_id}'}})"

            # Build path pattern
            if relationship_path:
                path = "(start)"

                # Handle each relationship in the path
                for i, rel_type in enumerate(relationship_path):
                    var_name = f"n{i}"
                    path += f"-[r{i}:{rel_type}]->{var_name}"

                # Add end entity type constraint if provided
                if end_entity_type and relationship_path:
                    last_var = f"n{len(relationship_path)-1}"
                    path += f" WHERE {last_var}:{end_entity_type}"

                cypher_query += f" MATCH path = {path}"
            else:
                # Use variable length path if no specific path is provided
                rel_constraint = ""

                # Add end entity type constraint if provided
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
                path: Any = item["path"]

                # Convert path to a list of nodes and relationships
                path_data = {
                    "nodes": [],
                    "relationships": []
                }



                # Extract nodes
                for node in path.nodes:
                    raw_properties = dict(node)
                    properties = self._convert_neo4j_properties(raw_properties)
                    node_data = {
                        "id": node.get("id", str(node.identity)),
                        "text": node.get("text", ""),
                        "type": next(iter(node.labels), "Unknown"),
                        "properties": properties
                    }

                    path_data["nodes"].append(node_data)

                # Extract relationships
                for rel in path.relationships:
                    raw_properties = dict(rel)
                    properties = self._convert_neo4j_properties(raw_properties)
                    rel_data = {
                        "id": rel.get("id", str(rel.identity)),
                        "type": type(rel).__name__,
                        "source_id": rel.start_node.get("id", str(rel.start_node.identity)),
                        "target_id": rel.end_node.get("id", str(rel.end_node.identity)),
                        "properties":properties
                    }

                    path_data["relationships"].append(rel_data)

                paths.append(path_data)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            return {
                "paths": paths,
                "total": len(paths),
                "execution_time_ms": execution_time_ms
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in graph search: {str(e)}"
            )

    async def create_entity_embedding(self, entity_id: str = Path(...), model: Optional[str] = None,) -> Dict[str, Any]:
        """Create embedding for a new entity"""
        if not self.openai_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API is not configured"
            )

        try:
            # Get entity
            entity_query = f"""
            MATCH (n {{id: '{entity_id}'}})
            RETURN n
            """

            entity_result = self.graph.run(entity_query).data()

            if not entity_result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity not found"
                )

            entity = entity_result[0]["n"]
            if not entity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity not found"
                )
            entity_text = entity.get("text", "")

            if not entity_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Entity has no text to embed"
                )

            # Generate embedding
            embedding = await self._generate_embedding(entity_text, model)

            # Update entity
            update_query = f"""
            MATCH (n {{id: '{entity_id}'}})
            SET n.embedding = '{json.dumps(embedding)}'
            RETURN n
            """

            update_result = self.graph.run(update_query).data()

            if not update_result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create entity embedding"
                )

            updated_entity: Any = update_result[0]["n"]

            if not updated_entity:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create entity embedding"
                )

            return {
                "id": updated_entity.get("id", str(updated_entity["identity"])),
                "text": updated_entity.get("text", ""),
                "type": next(iter(updated_entity["labels"]), "Unknown"),
                "embedding_created": True,
                "vector_size": len(embedding)
            }
        except HTTPException:
            raise 
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating entity embedding: {str(e)}"
            )

    async def update_entity_embedding(self, entity_id: str) -> Dict[str, Any]:
        """Update embedding for an entity"""
        if not self.openai_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API is not configured"
            )

        try:
            # Get entity
            entity_query = f"""
            MATCH (n {{id: '{entity_id}'}})
            RETURN n
            """

            entity_result = self.graph.run(entity_query).data()

            if not entity_result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity not found"
                )

            entity = entity_result[0]["n"]
            if not entity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity not found"
                )
            entity_text = entity.get("text", "")

            if not entity_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Entity has no text to embed"
                )

            # Generate embedding
            embedding = await self._generate_embedding(entity_text)

            # Update entity
            update_query = f"""
            MATCH (n {{id: '{entity_id}'}})
            SET n.embedding = '{json.dumps(embedding)}'
            RETURN n
            """

            update_result = self.graph.run(update_query).data()

            if not update_result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update entity embedding"
                )

            updated_entity: Any = update_result[0]["n"]

            if not updated_entity:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update entity embedding"
                )

            return {
                "id": updated_entity.get("id", str(updated_entity["identity"])),
                "text": updated_entity.get("text", ""),
                "type": next(iter(updated_entity["labels"]), "Unknown"),
                "embedding_updated": True,
                "vector_size": len(embedding)
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating entity embedding: {str(e)}"
            )

    async def update_entity_embeddings_batch(
        self,
        entity_type: Optional[str] = None,
        limit: int = Query(100, ge=1, le=1000),
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update embeddings for a batch of entities"""
        if not self.openai_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API is not configured"
            )

        try:
            # Build Cypher query
            cypher_query = "MATCH (n) "

            if entity_type:
                cypher_query += f"WHERE n:{entity_type} "

            cypher_query += "RETURN n LIMIT $limit"

            # Execute query
            results = self.graph.run(cypher_query, limit=limit).data()

            if not results:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No entities found to update"
                )

            updated_entities = []

            for item in results:
                node: Any = item["n"]

                # Get entity ID and text
                entity_id = node.get("id", str(node.identity))
                entity_text = node.get("text", "")

                if not entity_text:
                    continue

                # Generate embedding
                embedding = await self._generate_embedding(entity_text, model)

                # Update entity
                update_query = f"""
                MATCH (n {{id: '{entity_id}'}})
                SET n.embedding = '{json.dumps(embedding)}'
                RETURN n
                """

                update_result = self.graph.run(update_query).data()

                if not update_result:
                    continue

                updated_entity: Any = update_result[0]["n"]

                if not updated_entity:
                    continue

                updated_entities.append({
                    "id": updated_entity.get("id", str(updated_entity["identity"])),
                    "text": updated_entity.get("text", ""),
                    "type": next(iter(updated_entity["labels"]), "Unknown"),
                    "embedding_updated": True,
                    "vector_size": len(embedding)
                })

            return {
                "updated_entities": updated_entities,
                "total_updated": len(updated_entities)
            }
        except HTTPException:
            raise 
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating entity embeddings: {str(e)}"
            )
