import json
import logging
import time
from typing import List, Tuple

from fastapi import HTTPException, status

from app.nlp.embeddings import get_text_embedding
from app.schemas.search import (EntitySearchResult, SearchRequest,
                                SearchResponse, SearchType)
from app.utils.similarity import calculate_similarity

from .base import BaseSearchService

logger = logging.getLogger(__name__)


class TraditionalSearchService(BaseSearchService):
    """Traditional search methods: exact, fuzzy, semantic, hybrid"""

    async def search_entities(self, search_request: SearchRequest) -> SearchResponse:
        """Search for entities based on the search request"""
        try:
            start_time = time.time()

            # Validate entity types
            search_request.entity_types = self._validate_entity_types(
                search_request.entity_types
            )

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
                raise ValueError(f"Loại tìm kiếm không xác định: {search_request.search_type}")

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            return SearchResponse(
                results=results,
                total=total,
                query=search_request.query,
                search_type=search_request.search_type,
                execution_time_ms=execution_time_ms,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi khi tìm kiếm thực thể ngân hàng: {str(e)}",
            )

    async def _exact_search(
        self, search_request: SearchRequest
    ) -> Tuple[List[EntitySearchResult], int]:
        """Perform exact text search"""
        query = search_request.query

        # Build Cypher query
        cypher_query = "MATCH (n) WHERE "

        # Add text condition
        cypher_query += f"toLower(n.entity_text) CONTAINS toLower('{query}') "

        # Add entity type filter if provided
        if search_request.entity_types and len(search_request.entity_types) > 0:
            cypher_query += self._build_entity_type_filter(search_request.entity_types)

        # Add additional filters if provided
        if search_request.filters:
            cypher_query += self._build_filter_conditions(search_request.filters)

        # Add return and count query
        count_query = cypher_query + "RETURN COUNT(n) as total"

        # Add sorting if provided
        cypher_query += "RETURN n "
        if search_request.sort:
            cypher_query += self._build_sort_conditions(search_request.sort)

        # Add pagination
        cypher_query += f"SKIP {search_request.offset} LIMIT {search_request.limit}"

        # Execute count query
        count_result = self.graph.run(count_query).data()
        total = count_result[0]["total"] if count_result else 0

        # Execute search query
        results = self.graph.run(cypher_query).data()

        # Transform to EntitySearchResult
        entity_results = []
        for item in results:
            node = item["n"]
            entity_result = self._create_entity_search_result(node, score=1.0)
            entity_results.append(entity_result)

        return entity_results, total

    async def _fuzzy_search(
        self, search_request: SearchRequest
    ) -> Tuple[List[EntitySearchResult], int]:
        """Perform fuzzy text search"""
        query = search_request.query

        try:
            # Check if apoc.text.fuzzyMatch is available
            check_query = "CALL dbms.procedures() YIELD name WHERE name = 'apoc.text.fuzzyMatch' RETURN count(*) as count"
            check_result = self.graph.run(check_query).data()
            apoc_available = check_result[0]["count"] > 0 if check_result else False

            if apoc_available:
                # Use APOC for fuzzy matching
                cypher_query = """
                MATCH (n)
                WHERE apoc.text.fuzzyMatch(n.entity_text, $query) > $threshold
                """

                # Add entity type filter if provided
                if search_request.entity_types and len(search_request.entity_types) > 0:
                    cypher_query += self._build_entity_type_filter(search_request.entity_types)

                # Add return statement with scoring
                cypher_query += """
                RETURN n, apoc.text.fuzzyMatch(n.entity_text, $query) AS score
                ORDER BY score DESC
                SKIP $offset LIMIT $limit
                """

                # Execute query with parameters
                results = self.graph.run(
                    cypher_query,
                    query=query,
                    threshold=0.5,  # Adjust threshold as needed
                    offset=search_request.offset,
                    limit=search_request.limit,
                ).data()

                # For count query
                count_query = """
                MATCH (n)
                WHERE apoc.text.fuzzyMatch(n.entity_text, $query) > $threshold
                """

                # Add entity type filter for count
                if search_request.entity_types and len(search_request.entity_types) > 0:
                    count_query += self._build_entity_type_filter(search_request.entity_types)

                count_query += "RETURN COUNT(n) as total"

                count_result = self.graph.run(
                    count_query, query=query, threshold=0.5
                ).data()
                total = count_result[0]["total"] if count_result else 0
            else:
                # Fallback to exact search
                return await self._exact_search(search_request)

            # Transform to EntitySearchResult
            entity_results = []
            for item in results:
                node = item["n"]
                score = item.get("score", 0.5)  # Default score if not available
                entity_result = self._create_entity_search_result(node, score=score)
                entity_results.append(entity_result)

            return entity_results, total
        except Exception as e:
            # Log the error and fall back to exact search
            logger.error(f"Error in fuzzy search, falling back to exact search: {e}")
            return await self._exact_search(search_request)

    async def _semantic_search(
        self, search_request: SearchRequest
    ) -> Tuple[List[EntitySearchResult], int]:
        """Perform semantic search using embeddings"""
        if not self.openai_available:
            # Fall back to fuzzy search if OpenAI is not available
            return await self._fuzzy_search(search_request)

        try:
            # Generate embedding for query
            query_embedding = await get_text_embedding(search_request.query)

            # Use PostgreSQL for semantic search since embeddings are stored there
            supabase = await self.get_supabase_client()

            # Get entities with embeddings from PostgreSQL
            db_query = (
                supabase.table("kg_entities")
                .select(
                    "id, entity_text, entity_type, properties, confidence, embedding, ontology_class_id"
                )
                .eq("is_active", True)
                .not_.is_("embedding", "null")
            )

            if search_request.entity_types and len(search_request.entity_types) > 0:
                db_query = db_query.in_("entity_type", search_request.entity_types)

            response = await db_query.execute()
            entities = response.data

            # Calculate similarity scores
            scored_entities = []
            for entity in entities:
                if entity.get("embedding"):
                    try:
                        entity_embedding = json.loads(entity["embedding"])
                        similarity = calculate_similarity(
                            query_embedding, entity_embedding, method="cosine"
                        )

                        threshold = search_request.similarity_threshold or 0.3
                        if similarity >= threshold:
                            entity["similarity_score"] = float(similarity)
                            scored_entities.append(entity)

                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(
                            f"Error processing embedding for entity {entity['id']}: {e}"
                        )
                        continue

            # Sort by similarity
            scored_entities.sort(key=lambda x: x["similarity_score"], reverse=True)

            # Apply pagination
            paginated_entities = scored_entities[
                search_request.offset : search_request.offset + search_request.limit
            ]

            # Transform to EntitySearchResult
            entity_results = []
            for entity in paginated_entities:
                # Remove embedding from properties to avoid large response
                properties = entity.get("properties", {})
                if isinstance(properties, str):
                    try:
                        properties = json.loads(properties)
                    except json.JSONDecodeError:
                        properties = {}

                entity_result = EntitySearchResult(
                    id=entity["id"],
                    text=entity["entity_text"],
                    type=entity["entity_type"],
                    properties=properties,
                    ontology_class=entity.get("ontology_class_id"),
                    score=entity["similarity_score"],
                    relationships=None,
                    similar_entities=None,
                )
                entity_results.append(entity_result)

            return entity_results, len(scored_entities)

        except Exception as e:
            # Log the error and fall back to fuzzy search
            logger.error(f"Error in semantic search, falling back to fuzzy search: {e}")
            return await self._fuzzy_search(search_request)

    async def _hybrid_search(
        self, search_request: SearchRequest
    ) -> Tuple[List[EntitySearchResult], int]:
        """Perform hybrid search (combination of exact, fuzzy, and semantic)"""
        try:
            # Perform both exact and semantic searches
            exact_results, exact_total = await self._exact_search(search_request)

            # Only perform semantic search if OpenAI is available
            if self.openai_available:
                semantic_results, semantic_total = await self._semantic_search(
                    search_request
                )

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
                        combined_results[result.id].score = (
                            0.7 * combined_results[result.id].score + 0.3 * result.score
                        )
                    else:
                        combined_results[result.id] = result

                # Convert back to list and sort by score
                results = list(combined_results.values())
                results.sort(key=lambda x: x.score, reverse=True)

                # Apply offset and limit
                results = results[
                    search_request.offset : search_request.offset + search_request.limit
                ]

                # Total count
                total = len(combined_results)

                return results, total
            else:
                # If OpenAI is not available, just return exact results
                return exact_results, exact_total
        except Exception as e:
            # Log the error and fall back to exact search
            logger.error(f"Error in hybrid search, falling back to exact search: {e}")
            return await self._exact_search(search_request)
