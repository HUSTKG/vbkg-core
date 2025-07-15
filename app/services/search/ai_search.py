import json
import logging
import time
from typing import Any, Dict, List, Tuple

from fastapi import HTTPException, status

from app.nlp.embeddings import get_text_embedding
from app.schemas.search import (AISearchRequest, AISearchResponse,
                                EntityRankResult, SubgraphContext)
from app.utils.personrank import optimize_personalization_vector
from app.utils.similarity import calculate_similarity

from .base import BaseSearchService

logger = logging.getLogger(__name__)


class AISearchService(BaseSearchService):
    """AI-powered search service for knowledge graph"""

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

    async def _semantic_entity_search_for_ai(
        self,
        query: str,
        entity_types: List[str] = None,
        limit: int = 50,
        similarity_threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """Enhanced semantic search for AI pipeline using PostgreSQL"""

        # Generate query embedding
        query_embedding = await get_text_embedding(query)
        if not query_embedding:
            return []

        supabase = await self.get_supabase_client()

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
