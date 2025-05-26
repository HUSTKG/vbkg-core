import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from neo4j import Query
from postgrest.types import CountMethod

from app.core.supabase import get_supabase
from app.nlp.embeddings import get_text_embedding
from app.utils.neo4j import get_neo4j_driver
from app.utils.similarity import calculate_similarity

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Service for reading and querying knowledge graph data"""

    def __init__(self):
        self.neo4j_driver = get_neo4j_driver()

    # =============================================
    # ENTITY OPERATIONS
    # =============================================

    async def get_entity(
        self, entity_id: str, include_relationships: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get entity by ID with optional relationships"""

        supabase = await get_supabase()

        # Get entity from PostgreSQL
        response = (
            await supabase.table("kg_entities")
            .select(
                "id, entity_text, entity_type, properties, confidence, is_verified, created_at, updated_at"
            )
            .eq("id", entity_id)
            .eq("is_active", True)
            .single()
            .execute()
        )

        if not response.data:
            return None

        entity = response.data

        # Add relationship count
        rel_count_response = (
            await supabase.table("kg_relationships")
            .select("*", count="exact")
            .or_(f"source_entity_id.eq.{entity_id},target_entity_id.eq.{entity_id}")
            .eq("is_active", True)
            .execute()
        )

        entity["relationship_count"] = rel_count_response.count or 0

        # Include relationships if requested
        if include_relationships:
            entity["relationships"] = await self.get_entity_relationships(entity_id)

        return entity

    async def search_entities(
        self,
        query: Optional[str] = None,
        entity_types: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        min_confidence: float = 0.0,
        verified_only: bool = False,
        semantic_search: bool = False,
    ) -> Dict[str, Any]:
        """Search entities with various filters"""

        supabase = await get_supabase()

        # Build query
        db_query = (
            supabase.table("kg_entities")
            .select(
                "id, entity_text, entity_type, properties, confidence, is_verified, created_at"
            )
            .eq("is_active", True)
        )

        # Apply filters
        if entity_types:
            db_query = db_query.in_("entity_type", entity_types)

        if min_confidence > 0:
            db_query = db_query.gte("confidence", min_confidence)

        if verified_only:
            db_query = db_query.eq("is_verified", True)

        # Text search
        if query:
            if semantic_search:
                return await self._semantic_search(query, entity_types, limit, offset)
            else:
                db_query = db_query.ilike("entity_text", f"%{query}%")

        # Apply pagination and execute
        response = (
            await db_query.order("confidence", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        # Count relationships for each entity
        for entity in response.data:
            rel_count_response = (
                await supabase.table("kg_relationships")
                .select("*", count="exact")
                .or_(
                    f"source_entity_id.eq.{entity['id']},target_entity_id.eq.{entity['id']}"
                )
                .eq("is_active", True)
                .execute()
            )
            entity["relationship_count"] = rel_count_response.count or 0

        # Get total count for pagination
        count_query = (
            supabase.table("kg_entities")
            .select("*", count=CountMethod.exact)
            .eq("is_active", True)
        )
        if entity_types:
            count_query = count_query.in_("entity_type", entity_types)
        if query and not semantic_search:
            count_query = count_query.ilike("entity_text", f"%{query}%")

        count_response = await count_query.execute()

        return {
            "entities": response.data,
            "total": count_response.count,
            "limit": limit,
            "offset": offset,
            "has_more": (
                (offset + limit) < count_response.count if count_response.count else 0
            ),
        }

    async def search_relationships(
        self,
        query: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0,
        min_confidence: float = 0.0,
        verified_only: bool = False,
        semantic_search: bool = False,
    ) -> Dict[str, Any]:
        """Search entities with various filters"""

        supabase = await get_supabase()

        # Build query
        db_query = (
            supabase.table("kg_relationships")
            .select(
                "id,relationship_type,properties,confidence,is_verified,source_entity:source_entity_id(*),target_entity:target_entity_id(*),created_at"
            )
            .eq("is_active", True)
        )

        # Apply filters
        if relationship_types:
            db_query = db_query.in_("relationship_type", relationship_types)

        if min_confidence > 0:
            db_query = db_query.gte("confidence", min_confidence)

        if verified_only:
            db_query = db_query.eq("is_verified", True)

        # Text search
        if query:
            if semantic_search:
                return await self._semantic_search(
                    query, relationship_types, limit, offset
                )
            else:
                db_query = db_query.ilike("relationship_type", f"%{query}%")

        # Apply pagination and execute
        response = (
            await db_query.order("confidence", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        # Get total count for pagination
        count_query = (
            supabase.table("kg_relationships")
            .select("*", count=CountMethod.exact)
            .eq("is_active", True)
        )
        if relationship_types:
            count_query = count_query.in_("relationship_type", relationship_types)
        if query and not semantic_search:
            count_query = count_query.ilike("relationship_type", f"%{query}%")

        count_response = await count_query.execute()

        return {
            "relationships": response.data,
            "total": count_response.count,
            "limit": limit,
            "offset": offset,
            "has_more": (
                (offset + limit) < count_response.count if count_response.count else 0
            ),
        }

    async def _semantic_search(
        self, query: str, entity_types: Optional[List[str]], limit: int, offset: int
    ) -> Dict[str, Any]:
        """Perform semantic search using embeddings"""

        # Generate query embedding
        query_embedding = await get_text_embedding(query)
        if not query_embedding:
            return {
                "entities": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
            }

        supabase = await get_supabase()

        # Get entities with embeddings
        db_query = (
            supabase.table("kg_entities")
            .select(
                "id, entity_text, entity_type, properties, confidence, is_verified, created_at, embedding"
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
                similarity = calculate_similarity(
                    query_embedding, entity["embedding"], method="cosine"
                )
                entity["similarity_score"] = similarity
                scored_entities.append(entity)

        # Sort by similarity and apply pagination
        scored_entities.sort(key=lambda x: x["similarity_score"], reverse=True)
        paginated_entities = scored_entities[offset : offset + limit]

        # Remove embedding from response
        for entity in paginated_entities:
            entity.pop("embedding", None)

        return {
            "entities": paginated_entities,
            "total": len(scored_entities),
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < len(scored_entities),
        }

    async def get_entity_types(self) -> List[Dict[str, Any]]:
        """Get all entity types with counts"""

        supabase = await get_supabase()

        response = (
            await supabase.table("kg_entities")
            .select("entity_type")
            .eq("is_active", True)
            .execute()
        )

        # Count manually
        type_counts = {}
        for entity in response.data:
            entity_type = entity["entity_type"]
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

        return [{"entity_type": t, "count": c} for t, c in type_counts.items()]

    # =============================================
    # RELATIONSHIP OPERATIONS
    # =============================================

    async def get_relationship(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """Get relationship by ID"""

        supabase = await get_supabase()

        response = (
            await supabase.table("kg_relationships")
            .select(
                "*, source_entity:source_entity_id(id, entity_text, entity_type), target_entity:target_entity_id(id, entity_text, entity_type)"
            )
            .eq("id", relationship_id)
            .eq("is_active", True)
            .single()
            .execute()
        )

        return response.data

    async def get_entity_relationships(
        self,
        entity_id: str,
        relationship_types: Optional[List[str]] = None,
        direction: str = "both",  # "incoming", "outgoing", "both"
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get relationships for an entity"""

        supabase = await get_supabase()

        # Build query based on direction
        if direction == "outgoing":
            query_filter = f"source_entity_id.eq.{entity_id}"
        elif direction == "incoming":
            query_filter = f"target_entity_id.eq.{entity_id}"
        else:  # both
            query_filter = (
                f"source_entity_id.eq.{entity_id},target_entity_id.eq.{entity_id}"
            )

        db_query = (
            supabase.table("kg_relationships")
            .select(
                "*, source_entity:source_entity_id(id, entity_text, entity_type), target_entity:target_entity_id(id, entity_text, entity_type)"
            )
            .or_(query_filter)
            .eq("is_active", True)
        )

        if relationship_types:
            db_query = db_query.in_("relationship_type", relationship_types)

        response = (
            await db_query.order("confidence", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        # Get total count
        count_query = (
            supabase.table("kg_relationships")
            .select("*", count="exact")
            .or_(query_filter)
            .eq("is_active", True)
        )
        if relationship_types:
            count_query = count_query.in_("relationship_type", relationship_types)

        count_response = await count_query.execute()

        return {
            "relationships": response.data,
            "total": count_response.count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < count_response.count,
        }

    # =============================================
    # GRAPH TRAVERSAL
    # =============================================

    async def get_entity_neighbors(
        self,
        entity_id: str,
        max_depth: int = 1,
        relationship_types: Optional[List[str]] = None,
        limit_per_level: int = 10,
    ) -> Dict[str, Any]:
        """Get neighboring entities using Neo4j"""

        async with self.neo4j_driver.session() as session:
            # Build Cypher query
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":`{rel_types}`"

            query = f"""
            MATCH (start {{entity_id: $entity_id}})
            MATCH path = (start)-[r{rel_filter}*1..{max_depth}]-(connected)
            WITH DISTINCT connected, length(path) as depth, path
            ORDER BY depth, connected.confidence DESC
            WITH depth, collect(connected)[0..{limit_per_level}] as entities_at_depth
            RETURN depth, entities_at_depth
            """

            result = await session.run(query, {"entity_id": entity_id})

            neighbors_by_depth = {}
            async for record in result:
                depth = record["depth"]
                entities = []

                for entity_node in record["entities_at_depth"]:
                    entities.append(
                        {
                            "neo4j_id": entity_node.id,
                            "entity_id": entity_node["entity_id"],
                            "entity_text": entity_node.get("entity_text", ""),
                            "properties": entity_node.get("properties", {}),
                        }
                    )

                neighbors_by_depth[depth] = entities

            return {
                "entity_id": entity_id,
                "max_depth": max_depth,
                "neighbors_by_depth": neighbors_by_depth,
                "total_neighbors": sum(
                    len(entities) for entities in neighbors_by_depth.values()
                ),
            }

    async def get_subgraph(
        self,
        entity_id: str,
        radius: int = 2,
        max_nodes: int = 50,
        relationship_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get subgraph around an entity"""

        async with self.neo4j_driver.session() as session:
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":`{rel_types}`"

            query = f"""
            MATCH (center {{entity_id: $entity_id}})
            MATCH path = (center)-[r{rel_filter}*1..{radius}]-(connected)
            WITH DISTINCT connected, center
            ORDER BY connected.confidence DESC
            LIMIT {max_nodes}

            WITH collect(connected) as connected_nodes, center
            MATCH (n1)-[rel{rel_filter}]-(n2)
            WHERE (n1 = center OR n1 IN connected_nodes) 
              AND (n2 = center OR n2 IN connected_nodes)

            RETURN 
                connected_nodes + [center] as nodes,
                collect(DISTINCT rel) as relationships
            """

            result = await session.run(query, {"entity_id": entity_id})
            record = await result.single()

            if not record:
                return {
                    "nodes": [],
                    "edges": [],
                    "center_entity_id": entity_id,
                    "radius": radius,
                    "node_count": 0,
                    "edge_count": 0,
                }

            # Format nodes
            nodes = []
            for node in record["nodes"]:
                nodes.append(
                    {
                        "id": node["entity_id"],
                        "neo4j_id": node.id,
                        "label": node.get("text", ""),
                        "type": node.get("entity_type", ""),
                        "properties": node.get("properties", {}),
                        "is_center": node["entity_id"] == entity_id,
                    }
                )

            # Format edges
            edges = []
            for rel in record["relationships"]:
                edges.append(
                    {
                        "id": rel["relationship_id"],
                        "neo4j_id": rel.id,
                        "source": rel.start_node["entity_id"],
                        "target": rel.end_node["entity_id"],
                        "type": rel.type,
                        "properties": rel.get("properties", {}),
                    }
                )

            return {
                "nodes": nodes,
                "edges": edges,
                "center_entity_id": entity_id,
                "radius": radius,
                "node_count": len(nodes),
                "edge_count": len(edges),
            }

    async def find_path(
        self,
        source_entity_id: str,
        target_entity_id: str,
        max_depth: int = 5,
        relationship_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Find shortest paths between two entities"""

        async with self.neo4j_driver.session() as session:
            rel_filter = ""
            if relationship_types:
                rel_types = "|".join(relationship_types)
                rel_filter = f":`{rel_types}`"

            query = f"""
            MATCH (source {{entity_id: $source_id}}), (target {{entity_id: $target_id}})
            MATCH path = shortestPath((source)-[r{rel_filter}*1..{max_depth}]-(target))
            RETURN path
            LIMIT 5
            """

            result = await session.run(
                query, {"source_id": source_entity_id, "target_id": target_entity_id}
            )

            paths = []
            async for record in result:
                path = record["path"]

                # Extract nodes and relationships from path
                path_nodes = []
                path_relationships = []

                for node in path.nodes:
                    path_nodes.append(
                        {
                            "entity_id": node["entity_id"],
                            "entity_text": node.get("entity_text", ""),
                            "entity_type": node.get("entity_type", ""),
                        }
                    )

                for rel in path.relationships:
                    path_relationships.append(
                        {
                            "relationship_id": rel["relationship_id"],
                            "type": rel.type,
                            "source": rel.start_node["entity_id"],
                            "target": rel.end_node["entity_id"],
                        }
                    )

                paths.append(
                    {
                        "length": len(path.relationships),
                        "nodes": path_nodes,
                        "relationships": path_relationships,
                    }
                )

            return paths

    # =============================================
    # STATISTICS & ANALYTICS
    # =============================================

    async def get_knowledge_graph_stats(self) -> Dict[str, Any]:
        """Get comprehensive KG statistics"""

        supabase = await get_supabase()

        # Entity stats
        entity_response = (
            await supabase.table("kg_entities")
            .select("*", count="exact")
            .eq("is_active", True)
            .execute()
        )

        # Relationship stats
        rel_response = (
            await supabase.table("kg_relationships")
            .select("*", count="exact")
            .eq("is_active", True)
            .execute()
        )

        # Entity type distribution
        entity_types = await self.get_entity_types()

        # Relationship type distribution
        rel_type_response = (
            await supabase.table("kg_relationships")
            .select("relationship_type")
            .eq("is_active", True)
            .execute()
        )

        rel_type_counts = {}
        for rel in rel_type_response.data:
            rel_type = rel["relationship_type"]
            rel_type_counts[rel_type] = rel_type_counts.get(rel_type, 0) + 1

        # Recent activity
        recent_entities = (
            await supabase.table("kg_entities")
            .select("created_at")
            .eq("is_active", True)
            .gte("created_at", (datetime.now() - timedelta(days=7)).isoformat())
            .execute()
        )

        return {
            "total_entities": entity_response.count,
            "total_relationships": rel_response.count,
            "entity_types": entity_types,
            "relationship_types": [
                {"relationship_type": rt, "count": count}
                for rt, count in rel_type_counts.items()
            ],
            "recent_entities_count": len(recent_entities.data),
            "avg_relationships_per_entity": (rel_response.count * 2)
            / max(entity_response.count, 1),
            "last_updated": datetime.now().isoformat(),
        }

    async def get_investment_insights(
        self, entity_type: str = "ORGANIZATION", limit: int = 20
    ) -> Dict[str, Any]:
        """Get investment-specific insights from the knowledge graph"""

        # Most connected companies
        most_connected = await self._get_most_connected_entities(entity_type, limit)

        # Recent funding relationships
        recent_funding = await self._get_recent_funding_activity(limit)

        # Investment patterns
        investment_patterns = await self._get_investment_patterns(limit)

        return {
            "most_connected_companies": most_connected,
            "recent_funding_activity": recent_funding,
            "investment_patterns": investment_patterns,
            "generated_at": datetime.now().isoformat(),
        }

    async def _get_most_connected_entities(
        self, entity_type: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Get entities with most relationships"""

        async with self.neo4j_driver.session() as session:
            query = """
            MATCH (e:Entity {entity_type: $entity_type})
            OPTIONAL MATCH (e)-[r]-(connected)
            WITH e, count(r) as connection_count
            ORDER BY connection_count DESC
            LIMIT $limit
            RETURN e.entity_id as entity_id, e.entity_text as entity_text, connection_count
            """

            result = await session.run(
                query, {"entity_type": entity_type, "limit": limit}
            )

            entities = []
            async for record in result:
                entities.append(
                    {
                        "entity_id": record["entity_id"],
                        "entity_text": record["entity_text"],
                        "connection_count": record["connection_count"],
                    }
                )

            return entities

    async def _get_recent_funding_activity(self, limit: int) -> List[Dict[str, Any]]:
        """Get recent funding relationships"""

        supabase = await get_supabase()

        funding_types = ["FUNDED_BY", "INVESTED_IN", "RAISED_FUNDING"]

        response = (
            await supabase.table("kg_relationships")
            .select(
                "*, source_entity:source_entity_id(entity_text), target_entity:target_entity_id(entity_text)"
            )
            .in_("relationship_type", funding_types)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return response.data

    async def _get_investment_patterns(self, limit: int) -> Dict[str, Any]:
        """Analyze investment patterns"""

        async with self.neo4j_driver.session() as session:
            # Get frequent investor-company patterns
            query = """
            MATCH (investor)-[:INVESTED_IN]->(company)
            WITH investor, count(company) as investments_count
            WHERE investments_count > 1
            ORDER BY investments_count DESC
            LIMIT $limit
            RETURN investor.entity_text as investor_name, investments_count
            """

            result = await session.run(query, {"limit": limit})

            top_investors = []
            async for record in result:
                top_investors.append(
                    {
                        "investor_name": record["investor_name"],
                        "investments_count": record["investments_count"],
                    }
                )

            return {"top_investors": top_investors}
