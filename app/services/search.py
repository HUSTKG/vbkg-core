import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from fastapi import HTTPException, Path, Query, status
from py2neo import Graph, NodeMatcher, RelationshipMatcher

from app.core.config import settings
from app.core.supabase import get_supabase
from app.nlp.embeddings import get_text_embedding
from app.schemas.search import AISearchRequest  # AI Search schemas
from app.schemas.search import (AISearchResponse, EmbeddingRequest,
                                EntityRankResult, EntitySearchResult,
                                GraphSearchQuery, SearchRequest,
                                SearchResponse, SearchType,
                                SimilarEntityRequest, SortOrder,
                                SubgraphContext)
from app.utils.personrank import (PersonRankCalculator,
                                  optimize_personalization_vector)
from app.utils.similarity import calculate_similarity

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        # Connect to Neo4j database
        self.graph = Graph(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self.node_matcher = NodeMatcher(self.graph)
        self.rel_matcher = RelationshipMatcher(self.graph)

        # Initialize OpenAI for embeddings if API key is available
        self.openai_available = False
        if settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI

            self.aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.openai_available = True

        # Initialize PersonRank calculator
        self.personrank_calculator = PersonRankCalculator()

    # ===== MAIN SEARCH METHODS =====

    def _validate_entity_types(self, entity_types: Optional[List[str]]) -> List[str]:
        """Validate and clean entity types list"""
        if not entity_types:
            return []

        # Filter out None, empty strings, and whitespace-only strings
        valid_types = []
        for entity_type in entity_types:
            if entity_type and isinstance(entity_type, str) and entity_type.strip():
                valid_types.append(entity_type.strip())

        return valid_types

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
            elif search_request.search_type == SearchType.AI_POWERED:
                return await self._ai_powered_search(search_request)
            else:
                raise ValueError(f"Loại tìm kiếm không xác định: {search_request.search_type}")

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Include relationships if requested
            if search_request.include_relationships:
                for entity in results:
                    entity.relationships = await self._get_entity_relationships(
                        entity.id
                    )

            # Include similar entities if requested
            if search_request.include_similar_entities:
                for entity in results:
                    entity.similar_entities = await self._get_similar_entities(
                        entity_id=entity.id,
                        limit=5,
                        similarity_threshold=search_request.similarity_threshold or 0.7,
                        entity_types=search_request.entity_types,
                    )

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

    # ===== AI-POWERED SEARCH METHODS =====

    async def ai_search(self, request: AISearchRequest) -> AISearchResponse:
        """
        AI-powered search pipeline for banking knowledge graph:
        1. Tìm kiếm ngữ nghĩa các thực thể ngân hàng bằng embeddings
        2. Tính điểm PersonRank cho các thực thể được truy xuất  
        3. Lấy ngữ cảnh đồ thị con xung quanh các thực thể hàng đầu
        4. Tạo phản hồi LLM sử dụng ngữ cảnh ngân hàng
        """
        start_time = time.time()

        try:
            # Step 1: Semantic search to get relevant banking entities
            logger.info(f"Bắt đầu tìm kiếm AI cho truy vấn ngân hàng: {request.query}")
            candidate_entities = await self._semantic_entity_search_for_ai(
                query=request.query,
                entity_types=request.entity_types,
                limit=request.max_candidates,
                similarity_threshold=request.similarity_threshold,
            )

            if not candidate_entities:
                return AISearchResponse(
                    query=request.query,
                    answer="Tôi không thể tìm thấy thực thể ngân hàng nào liên quan trong đồ thị tri thức cho truy vấn của bạn.",
                    entities=[],
                    subgraph_context=None,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    confidence_score=0.0,
                    total_candidates=0,
                )

            # Step 2: Calculate PersonRank scores
            logger.info(
                f"Tính toán PersonRank cho {len(candidate_entities)} thực thể ngân hàng"
            )
            ranked_entities = await self._calculate_personrank(
                entities=candidate_entities,
                query_embedding=await get_text_embedding(request.query),
                damping_factor=request.damping_factor,
                max_iterations=request.max_iterations,
            )

            # Step 3: Get subgraph context for top entities
            top_entities = ranked_entities[: request.top_k_entities]
            logger.info(
                f"Lấy ngữ cảnh đồ thị con cho {len(top_entities)} thực thể ngân hàng hàng đầu"
            )

            subgraph_context = await self._get_subgraph_context(
                entities=top_entities,
                radius=request.subgraph_radius,
                max_nodes=request.max_subgraph_nodes,
            )

            # Step 4: Generate LLM response
            if self.openai_available and request.generate_answer:
                logger.info("Tạo phản hồi LLM cho ngữ cảnh ngân hàng")
                answer, confidence = await self._generate_llm_response(
                    query=request.query,
                    entities=top_entities,
                    subgraph_context=subgraph_context,
                    model=request.llm_model,
                )
            else:
                answer = "Tìm kiếm hoàn thành thành công. Kích hoạt LLM để nhận câu trả lời được tạo."
                confidence = 0.8

            execution_time = int((time.time() - start_time) * 1000)

            return AISearchResponse(
                query=request.query,
                answer=answer,
                entities=ranked_entities[: request.top_k_entities],
                subgraph_context=subgraph_context,
                execution_time_ms=execution_time,
                confidence_score=confidence,
                total_candidates=len(candidate_entities),
            )

        except Exception as e:
            logger.error(f"Lỗi trong tìm kiếm AI ngân hàng: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi trong tìm kiếm AI ngân hàng: {str(e)}",
            )

    async def _ai_powered_search(self, search_request: SearchRequest) -> SearchResponse:
        """Convert regular search request to AI search for backward compatibility"""

        # Convert SearchRequest to AISearchRequest
        ai_request = AISearchRequest(
            query=search_request.query,
            entity_types=search_request.entity_types,
            max_candidates=min(search_request.limit * 3, 100),
            top_k_entities=search_request.limit,
            generate_answer=False,  # Don't generate answer for regular search
        )

        # Perform AI search
        ai_response = await self.ai_search(ai_request)

        # Convert back to SearchResponse format
        results = []
        for entity in ai_response.entities:
            result = EntitySearchResult(
                id=entity.entity_id,
                text=entity.entity_text,
                type=entity.entity_type,
                properties=entity.properties,
                ontology_class=None,
                score=entity.final_score,
                relationships=None,
                similar_entities=None,
            )
            results.append(result)

        return SearchResponse(
            results=results,
            total=ai_response.total_candidates,
            query=search_request.query,
            search_type=SearchType.AI_POWERED,
            execution_time_ms=ai_response.execution_time_ms,
        )

    # ===== AI SEARCH HELPER METHODS =====

    async def _semantic_entity_search_for_ai(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 50,
        similarity_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """Enhanced semantic search for AI pipeline using PostgreSQL"""

        # Generate query embedding
        query_embedding = await get_text_embedding(query)
        if not query_embedding:
            return []

        supabase = await get_supabase()

        # Get entities with embeddings from PostgreSQL
        db_query = (
            supabase.table("kg_entities")
            .select(
                "id, entity_text, entity_type, properties, confidence, embedding, neo4j_id"
            )
            .eq("is_active", True)
            .not_.is_("embedding", "null")
        )

        if entity_types:
            db_query = db_query.in_("entity_type", entity_types)

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

                    if similarity >= similarity_threshold:
                        entity["similarity_score"] = float(similarity)
                        scored_entities.append(entity)

                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(
                        f"Error processing embedding for entity {entity['id']}: {e}"
                    )
                    continue

        # Sort by similarity and limit
        scored_entities.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_entities[:limit]

    async def _calculate_personrank(
        self,
        entities: List[Dict[str, Any]],
        query_embedding: List[float],
        damping_factor: float = 0.85,
        max_iterations: int = 20,
        convergence_threshold: float = 1e-6,
    ) -> List[EntityRankResult]:
        """Calculate PersonRank scores using Neo4j graph structure"""

        if not entities:
            return []

        # Get entity IDs that have Neo4j representation
        entity_mapping = {e["id"]: e for e in entities if e.get("neo4j_id")}
        pg_entity_ids = list(entity_mapping.keys())

        if not pg_entity_ids:
            # Fallback to similarity-based ranking
            return [
                EntityRankResult(
                    entity_id=e["id"],
                    entity_text=e["entity_text"],
                    entity_type=e["entity_type"],
                    similarity_score=e["similarity_score"],
                    personrank_score=e["similarity_score"],
                    final_score=e["similarity_score"],
                    properties=e.get("properties", {}),
                )
                for e in entities
            ]

        # Query Neo4j for graph structure
        # Using PostgreSQL entity IDs since they're stored in Neo4j nodes
        query = """
        MATCH (n:Entity)
        WHERE n.entity_id IN $entity_ids
        OPTIONAL MATCH (n)-[r]-(connected:Entity)
        WHERE connected.entity_id IN $entity_ids
        RETURN 
            n.entity_id as node_id,
            collect(DISTINCT connected.entity_id) as neighbors,
            count(DISTINCT connected) as degree
        """

        results = self.graph.run(query, entity_ids=pg_entity_ids).data()

        # Build adjacency structure
        graph_structure = {}
        node_degrees = {}

        for record in results:
            node_id = record["node_id"]
            neighbors = record["neighbors"] or []
            degree = record["degree"] or 0

            # Filter out None values from neighbors
            neighbors = [n for n in neighbors if n is not None]

            graph_structure[node_id] = neighbors
            node_degrees[node_id] = max(degree, 1)  # Avoid division by zero

        # Create optimized personalization vector
        personalization_vector = optimize_personalization_vector(
            query_embedding=query_embedding, entities_dict=entity_mapping
        )

        # Calculate PersonRank scores using the calculator
        personrank_scores = self.personrank_calculator.calculate_personrank(
            graph_structure=graph_structure,
            node_degrees=node_degrees,
            personalization_vector=personalization_vector,
            damping_factor=damping_factor,
            max_iterations=max_iterations,
            convergence_threshold=convergence_threshold,
        )

        # Combine scores and create results
        results = []
        for entity in entities:
            entity_id = entity["id"]
            similarity_score = entity["similarity_score"]
            personrank_score = personrank_scores.get(entity_id, 0.0)

            # Weighted combination of similarity and PersonRank
            final_score = (0.4 * similarity_score) + (0.6 * personrank_score)

            results.append(
                EntityRankResult(
                    entity_id=entity_id,
                    entity_text=entity["entity_text"],
                    entity_type=entity["entity_type"],
                    similarity_score=similarity_score,
                    personrank_score=personrank_score,
                    final_score=final_score,
                    properties=entity.get("properties", {}),
                )
            )

        # Sort by final score
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results

    async def _get_subgraph_context(
        self, entities: List[EntityRankResult], radius: int = 2, max_nodes: int = 100
    ) -> SubgraphContext:
        """Get subgraph context around top entities using Neo4j"""

        if not entities:
            return SubgraphContext(nodes=[], edges=[], node_count=0, edge_count=0)

        # Get entity IDs for the top entities
        top_entity_ids = [e.entity_id for e in entities]

        # Query to get subgraph around these entities
        query = f"""
        MATCH (center:Entity)
        WHERE center.entity_id IN $center_ids
        
        MATCH path = (center)-[*1..{radius}]-(connected:Entity)
        WITH DISTINCT connected, center
        ORDER BY connected.confidence DESC
        LIMIT {max_nodes}
        
        WITH collect(DISTINCT connected) + collect(DISTINCT center) as all_nodes
        UNWIND all_nodes as node
        WITH collect(DISTINCT node) as nodes
        
        MATCH (n1)-[rel]-(n2)
        WHERE n1 IN nodes AND n2 IN nodes
        
        RETURN 
            nodes,
            collect(DISTINCT rel) as relationships
        """

        results = self.graph.run(query, center_ids=top_entity_ids).data()

        if not results:
            return SubgraphContext(nodes=[], edges=[], node_count=0, edge_count=0)

        record = results[0]

        # Format nodes
        nodes = []
        for node in record["nodes"]:
            node_props = dict(node)
            nodes.append(
                {
                    "id": node_props.get("entity_id"),
                    "text": node_props.get("entity_text", ""),
                    "type": node_props.get("entity_type", ""),
                    "properties": (
                        json.loads(node_props.get("properties", "{}"))
                        if isinstance(node_props.get("properties"), str)
                        else node_props.get("properties", {})
                    ),
                    "is_top_entity": node_props.get("entity_id") in top_entity_ids,
                }
            )

        # Format edges
        edges = []
        for rel in record["relationships"]:
            rel_props = dict(rel)
            edges.append(
                {
                    "id": rel_props.get("relationship_id"),
                    "source": rel.start_node.get("entity_id"),
                    "target": rel.end_node.get("entity_id"),
                    "type": type(rel).__name__,
                    "properties": (
                        json.loads(rel_props.get("properties", "{}"))
                        if isinstance(rel_props.get("properties"), str)
                        else rel_props.get("properties", {})
                    ),
                }
            )

        return SubgraphContext(
            nodes=nodes, edges=edges, node_count=len(nodes), edge_count=len(edges)
        )

    async def _generate_llm_response(
        self,
        query: str,
        entities: List[EntityRankResult],
        subgraph_context: SubgraphContext,
        model: str = "gpt-4o-mini",
    ) -> Tuple[str, float]:
        """Generate LLM response using context"""

        if not self.openai_available:
            return "LLM không khả dụng để tạo câu trả lời", 0.0

        # Prepare context for LLM
        context_text = self._format_context_for_llm(entities, subgraph_context)

        # Create prompt
        system_prompt = """Bạn là trợ lý tư vấn ngân hàng thông minh có khả năng phân tích đồ thị tri thức về lĩnh vực ngân hàng và tài chính. Bạn có quyền truy cập vào một đồ thị tri thức chứa thông tin về các thực thể ngân hàng và mối quan hệ giữa chúng.

    Định dạng ngữ cảnh:
    - Các thực thể hàng đầu được xếp hạng theo mức độ liên quan đến câu hỏi
    - Mỗi thực thể có các thuộc tính và mối quan hệ riêng
    - Đồ thị con hiển thị cách các thực thể được kết nối với nhau

    Hướng dẫn trả lời:
    1. Dựa câu trả lời chủ yếu vào ngữ cảnh được cung cấp
    2. Nếu ngữ cảnh không chứa đủ thông tin, hãy nói rõ điều đó
    3. Trích dẫn các thực thể và mối quan hệ cụ thể khi phù hợp
    4. Cung cấp câu trả lời có cấu trúc, đầy đủ thông tin về lĩnh vực ngân hàng
    5. Nếu được hỏi về mối quan hệ, hãy giải thích các kết nối trong đồ thị
    6. Tập trung vào các khía cạnh: sản phẩm ngân hàng, quy định, rủi ro, khách hàng, giao dịch
    7. Sử dụng thuật ngữ ngân hàng chuyên nghiệp và chính xác
    8. Đưa ra khuyến nghị thiết thực dựa trên dữ liệu"""

        user_prompt = f"""Câu hỏi: {query}

    Ngữ cảnh từ đồ thị tri thức ngân hàng:
    {context_text}

    Vui lòng cung cấp câu trả lời toàn diện dựa trên ngữ cảnh đồ thị tri thức ngân hàng ở trên."""

        try:
            response = await self.aclient.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=1000,
            )

            answer = response.choices[0].message.content

            # Calculate confidence based on context richness and entity scores
            avg_entity_score = (
                sum(e.final_score for e in entities) / len(entities) if entities else 0
            )
            context_richness = min(
                len(entities) * 0.1 + subgraph_context.node_count * 0.05, 1.0
            )
            confidence = avg_entity_score * 0.6 + context_richness * 0.4

            return answer, confidence

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return f"Lỗi khi tạo câu trả lời: {str(e)}", 0.0

    def _format_context_for_llm(
        self, entities: List[EntityRankResult], subgraph_context: SubgraphContext
    ) -> str:
        """Format context data for LLM consumption"""

        context_parts = []

        # Top entities section
        context_parts.append("=== CÁC THỰC THỂ NGÂN HÀNG LIÊN QUAN NHẤT ===")
        for i, entity in enumerate(entities[:10], 1):  # Limit to top 10
            properties_str = (
                ", ".join([f"{k}: {v}" for k, v in entity.properties.items()])
                if entity.properties
                else "Không có thuộc tính bổ sung"
            )
            context_parts.append(
                f"{i}. {entity.entity_text} ({entity.entity_type})\n"
                f"   Điểm liên quan: {entity.final_score:.3f}\n"
                f"   Thuộc tính: {properties_str}\n"
            )

        # Relationships section
        if subgraph_context.edges:
            context_parts.append("\n=== CÁC MỐI QUAN HỆ QUAN TRỌNG ===")

            # Group relationships by type for better readability
            rel_by_type = {}
            node_lookup = {node["id"]: node for node in subgraph_context.nodes}

            for edge in subgraph_context.edges[:20]:  # Limit to top 20 relationships
                rel_type = edge["type"]
                if rel_type not in rel_by_type:
                    rel_by_type[rel_type] = []

                source_node = node_lookup.get(edge["source"], {})
                target_node = node_lookup.get(edge["target"], {})

                rel_by_type[rel_type].append(
                    {
                        "source": source_node.get("text", edge["source"]),
                        "target": target_node.get("text", edge["target"]),
                        "properties": edge.get("properties", {}),
                    }
                )

            # Mapping relationship types to Vietnamese banking terms
            relationship_translation = {
                "HAS_ACCOUNT": "Có tài khoản",
                "OFFERS_PRODUCT": "Cung cấp sản phẩm", 
                "MANAGES_RISK": "Quản lý rủi ro",
                "FOLLOWS_REGULATION": "Tuân thủ quy định",
                "SERVES_CUSTOMER": "Phục vụ khách hàng",
                "PROCESSES_TRANSACTION": "Xử lý giao dịch",
                "REQUIRES_COMPLIANCE": "Yêu cầu tuân thủ",
                "PROVIDES_SERVICE": "Cung cấp dịch vụ",
                "BELONGS_TO_BRANCH": "Thuộc về chi nhánh",
                "ISSUED_BY": "Được phát hành bởi"
            }

            for rel_type, relationships in rel_by_type.items():
                vietnamese_rel_type = relationship_translation.get(rel_type, rel_type.replace('_', ' ').title())
                context_parts.append(f"\n{vietnamese_rel_type}:")
                for rel in relationships[:5]:  # Limit relationships per type
                    props_str = (
                        f" ({', '.join([f'{k}: {v}' for k, v in rel['properties'].items()])})"
                        if rel["properties"]
                        else ""
                    )
                    context_parts.append(
                        f"  - {rel['source']} → {rel['target']}{props_str}"
                    )

        # Graph statistics
        context_parts.append(f"\n=== THỐNG KÊ NGỮ CẢNH ĐỒ THỊ ===")
        context_parts.append(
            f"Tổng số thực thể trong ngữ cảnh: {subgraph_context.node_count}"
        )
        context_parts.append(f"Tổng số mối quan hệ: {subgraph_context.edge_count}")
        context_parts.append(f"Thực thể hàng đầu được phân tích: {len(entities)}")

        return "\n".join(context_parts)

    async def get_search_suggestions(
    self, partial_query: str, limit: int = 5
) -> List[str]:
        """Get search suggestions based on partial query for banking context"""

        if len(partial_query) < 2:
            return []

        supabase = await get_supabase()

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

    # ===== TRADITIONAL SEARCH METHODS =====

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
            entity_types = [
                f"n:{entity_type}" for entity_type in search_request.entity_types
            ]
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
        total = count_result[0]["total"] if count_result else 0

        # Execute search query
        results = self.graph.run(cypher_query).data()

        # Transform to EntitySearchResult
        entity_results = []
        for item in results:
            node = item["n"]

            # Extract properties
            raw_properties = dict(node)
            properties = self._convert_neo4j_properties(raw_properties)

            # Remove standard fields from properties
            for field in ["entity_id", "entity_text", "entity_type", "ontology_class"]:
                if field in properties:
                    properties.pop(field)

            # Create search result
            entity_result = EntitySearchResult(
                id=node.get("entity_id", str(node.identity)),
                text=node.get("entity_text", ""),
                type=node.get("entity_type", "Unknown"),
                properties=properties,
                ontology_class=node.get("ontology_class"),
                score=1.0,  # For exact search, all results have score 1.0
                relationships=None,
                similar_entities=None,
            )

            entity_results.append(entity_result)

        return entity_results, total

    def _convert_neo4j_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Neo4j properties, handling DateTime objects"""
        converted = {}

        for key, value in properties.items():
            if hasattr(value, "__class__") and "DateTime" in str(value.__class__):
                # Convert Neo4j DateTime to ISO string
                if hasattr(value, "isoformat"):
                    converted[key] = value.isoformat()
                else:
                    converted[key] = str(value)
            elif hasattr(value, "strftime"):
                # Handle standard datetime
                converted[key] = value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            elif isinstance(value, (list, tuple)):
                # Handle lists that might contain DateTime
                converted[key] = [
                    (
                        item.isoformat()
                        if hasattr(item, "isoformat")
                        else (
                            str(item)
                            if hasattr(item, "__class__")
                            and "DateTime" in str(item.__class__)
                            else item
                        )
                    )
                    for item in value
                ]
            elif isinstance(value, dict):
                # Recursive for nested dicts
                converted[key] = self._convert_neo4j_properties(value)
            else:
                converted[key] = value

        return converted

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
                    entity_types = [
                        f"n:{entity_type}"
                        for entity_type in search_request.entity_types
                    ]
                    cypher_query += f"AND ({' OR '.join(entity_types)}) "

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
                    entity_types = [
                        f"n:{entity_type}"
                        for entity_type in search_request.entity_types
                    ]
                    count_query += f"AND ({' OR '.join(entity_types)}) "

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

                # Extract properties
                raw_properties = dict(node)
                properties = self._convert_neo4j_properties(raw_properties)

                # Remove standard fields from properties
                for field in [
                    "entity_id",
                    "entity_text",
                    "entity_type",
                    "ontology_class",
                ]:
                    if field in properties:
                        properties.pop(field)

                # Create search result
                entity_result = EntitySearchResult(
                    id=node.get("entity_id", str(node.identity)),
                    text=node.get("entity_text", ""),
                    type=node.get("entity_type", "Unknown"),
                    properties=properties,
                    ontology_class=node.get("ontology_class"),
                    score=score,
                    relationships=None,
                    similar_entities=None,
                )

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
            query_embedding = await self._generate_embedding(
                search_request.query, search_request.embedding_model
            )

            # Use PostgreSQL for semantic search since embeddings are stored there
            supabase = await get_supabase()

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

    # ===== RELATIONSHIP AND ENTITY METHODS =====

    async def _get_entity_relationships(self, entity_id: str) -> List[Dict[str, Any]]:
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

    async def _get_similar_entities(
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
            supabase = await get_supabase()

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
                entity_text = entity.get("entity_text", "")
                if not entity_text:
                    return []

                entity_embedding = await self._generate_embedding(entity_text)

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

    # ===== EMBEDDING AND UTILITY METHODS =====

    async def _generate_embedding(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding for a text using OpenAI API"""
        if not self.openai_available:
            raise ValueError("OpenAI API is not available")

        try:
            # Use specified model or default
            embedding_model = model or "text-embedding-ada-002"

            # Call OpenAI API
            response = await self.aclient.embeddings.create(
                model=embedding_model, input=text, encoding_format="float"
            )

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

    # ===== API ENDPOINT METHODS =====

    async def generate_embedding(self, request: EmbeddingRequest) -> Dict[str, Any]:
        """Generate embedding for a text"""
        if not self.openai_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API is not configured",
            )

        try:
            embedding = await self._generate_embedding(
                text=request.text, model=request.model
            )

            return {
                "embedding": embedding,
                "model": request.model or "text-embedding-ada-002",
                "text": request.text,
                "vector_size": len(embedding),
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating embedding: {str(e)}",
            )

    async def find_similar_entities(
        self, request: SimilarEntityRequest
    ) -> List[Dict[str, Any]]:
        """Find entities similar to a given entity"""
        try:
            similar_entities = await self._get_similar_entities(
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

    async def create_entity_embedding(
        self, entity_id: str, model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create embedding for a new entity"""
        if not self.openai_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API is not configured",
            )

        try:
            # Get entity from PostgreSQL
            supabase = await get_supabase()

            entity_response = await (
                supabase.table("kg_entities")
                .select("id, entity_text, entity_type")
                .eq("id", entity_id)
                .eq("is_active", True)
                .single()
                .execute()
            )

            if not entity_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Entity not found"
                )

            entity = entity_response.data
            entity_text = entity.get("entity_text", "")

            if not entity_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Entity has no text to embed",
                )

            # Generate embedding
            embedding = await self._generate_embedding(entity_text, model)

            # Update entity with embedding
            await (
                supabase.table("kg_entities")
                .update({"embedding": json.dumps(embedding)})
                .eq("id", entity_id)
                .execute()
            )

            return {
                "id": entity["id"],
                "text": entity["entity_text"],
                "type": entity["entity_type"],
                "embedding_created": True,
                "vector_size": len(embedding),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating entity embedding: {str(e)}",
            )

    async def update_entity_embedding(self, entity_id: str) -> Dict[str, Any]:
        """Update embedding for an entity"""
        return await self.create_entity_embedding(entity_id)

    async def update_entity_embeddings_batch(
        self,
        entity_type: Optional[str] = None,
        limit: int = 100,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update embeddings for a batch of entities"""
        if not self.openai_available:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API is not configured",
            )

        try:
            supabase = await get_supabase()

            # Build query for entities without embeddings
            db_query = (
                supabase.table("kg_entities")
                .select("id, entity_text, entity_type")
                .eq("is_active", True)
                .is_("embedding", "null")
                .limit(limit)
            )

            if entity_type:
                db_query = db_query.eq("entity_type", entity_type)

            response = await db_query.execute()
            entities = response.data

            if not entities:
                return {
                    "updated_entities": [],
                    "total_updated": 0,
                    "message": "No entities found without embeddings",
                }

            updated_entities = []

            for entity in entities:
                entity_id = entity["id"]
                entity_text = entity.get("entity_text", "")

                if not entity_text:
                    continue

                try:
                    # Generate embedding
                    embedding = await self._generate_embedding(entity_text, model)

                    # Update entity with embedding
                    await (
                        supabase.table("kg_entities")
                        .update({"embedding": json.dumps(embedding)})
                        .eq("id", entity_id)
                        .execute()
                    )

                    updated_entities.append(
                        {
                            "id": entity_id,
                            "text": entity_text,
                            "type": entity["entity_type"],
                            "embedding_updated": True,
                            "vector_size": len(embedding),
                        }
                    )

                except Exception as e:
                    logger.error(
                        f"Error updating embedding for entity {entity_id}: {e}"
                    )
                    continue

            return {
                "updated_entities": updated_entities,
                "total_updated": len(updated_entities),
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating entity embeddings: {str(e)}",
            )
