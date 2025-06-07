import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from postgrest.types import CountMethod

from app.core.supabase import get_supabase
from app.nlp.embeddings import get_text_embedding
from app.schemas.conflict_resolution import KGEdit, KGEditAction, KGEditResult
from app.services.user import UserService
from app.utils.neo4j import get_neo4j_driver
from app.utils.similarity import calculate_similarity

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Service for reading and querying knowledge graph data"""

    def __init__(self):
        self.neo4j_driver = get_neo4j_driver()
        self.user_service = UserService()

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
            .select("*", count=CountMethod.exact)
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
        skip: int = 0,
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
                return await self._semantic_search(query, entity_types, limit, skip)
            else:
                db_query = db_query.ilike("entity_text", f"%{query}%")

        # Apply pagination and execute
        response = (
            await db_query.order("confidence", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        # Count relationships for each entity
        for entity in response.data:
            rel_count_response = (
                await supabase.table("kg_relationships")
                .select("*", count=CountMethod.exact)
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

        # don't return embeddings in response
        for entity in response.data:
            entity.pop("embedding", None)

        return {
            "entities": response.data,
            "total": count_response.count,
            "limit": limit,
            "skip": skip,
            "has_more": (
                (skip + limit) < count_response.count if count_response.count else 0
            ),
        }

    async def search_relationships(
        self,
        query: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        limit: int = 50,
        skip: int = 0,
        min_confidence: float = 0.0,
        verified_only: bool = False,
    ) -> Dict[str, Any]:
        """Search relationships with various filters"""

        supabase = await get_supabase()

        # Build query
        db_query = (
            supabase.table("kg_relationships")
            .select(
                "id,relationship_type,properties,confidence,is_verified,source_entity:source_entity_id(id, entity_text, entity_type),target_entity:target_entity_id(id, entity_text, entity_type),created_at"
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
            db_query = db_query.ilike("relationship_type", f"%{query}%")

        # Apply pagination and execute
        response = (
            await db_query.order("confidence", desc=True)
            .range(skip, skip + limit - 1)
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
        count_response = await count_query.execute()

        return {
            "relationships": response.data,
            "total": count_response.count,
            "limit": limit,
            "skip": skip,
            "has_more": (
                (skip + limit) < count_response.count if count_response.count else 0
            ),
        }

    async def _semantic_search(
        self, query: str, entity_types: Optional[List[str]], limit: int, skip: int
    ) -> Dict[str, Any]:
        """Perform semantic search using embeddings"""

        # Generate query embedding
        query_embedding = await get_text_embedding(query)
        if not query_embedding:
            return {
                "entities": [],
                "total": 0,
                "limit": limit,
                "skip": skip,
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
                    query_embedding, json.loads(entity["embedding"]), method="cosine"
                )
                entity["similarity_score"] = similarity
                scored_entities.append(entity)

        # Sort by similarity and apply pagination
        scored_entities.sort(key=lambda x: x["similarity_score"], reverse=True)
        paginated_entities = scored_entities[skip : skip + limit]

        # Remove embedding from response
        for entity in paginated_entities:
            entity.pop("embedding", None)

        # convert similarity_score to float
        for entity in paginated_entities:
            entity["similarity_score"] = entity["similarity_score"].item()

        print(
            f"Found {len(scored_entities)} entities, returning {len(paginated_entities)} after pagination"
        )

        print(entities)

        return {
            "entities": paginated_entities,
            "total": len(scored_entities),
            "limit": limit,
            "skip": skip,
            "has_more": (skip + limit) < len(scored_entities),
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
        skip: int = 0,
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
            .range(skip, skip + limit - 1)
            .execute()
        )

        # Get total count
        count_query = (
            supabase.table("kg_relationships")
            .select("*", count=CountMethod.exact)
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
            "skip": skip,
            "has_more": (skip + limit) < count_response.count,
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

    async def _create_entity(
        self, entity_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Create a new entity in both PostgreSQL and Neo4j"""

        supabase = await get_supabase()
        neo4j_driver = get_neo4j_driver()

        # Generate embedding for entity text
        entity_text = entity_data["entity_text"]
        # extract all properties from entity_data
        text_to_embed = entity_text
        if "properties" in entity_data:
            text_to_embed += " " + " ".join(
                f"{key}: {value}" for key, value in entity_data["properties"].items()
            )
        embedding = await get_text_embedding(text_to_embed)

        # Create entity in PostgreSQL
        postgres_data = {
            "entity_text": entity_text,
            "entity_type": entity_data["entity_type"],
            "properties": entity_data.get("properties", {}),
            "confidence": entity_data.get("confidence", 0.8),
            "embedding": embedding,
            "source_document_id": entity_data.get("source_document_id"),
            "is_verified": entity_data.get("is_verified", False),
            "created_by": user_id,
            "is_active": True,
        }

        pg_response = (
            await supabase.table("kg_entities").insert(postgres_data).execute()
        )
        entity_id = pg_response.data[0]["id"]

        properties_json = json.dumps(entity_data.get("properties", {}))

        # Create entity in Neo4j
        async with neo4j_driver.session() as session:
            neo4j_result = await session.run(
                """
                CREATE (e:Entity:{entity_type} {{
                    entity_id: $entity_id,
                    entity_text: $entity_text,
                    properties: $properties,
                    label: $entity_text,
                    type: $entity_type,
                    created_by: $created_by,
                    created_at: datetime()
                }})
                RETURN id(e) as neo4j_id
            """.format(
                    entity_type=entity_data["entity_type"]
                ),
                {
                    "entity_id": entity_id,
                    "entity_text": entity_text,
                    "entity_type": entity_data["entity_type"],
                    "properties": properties_json,
                    "created_by": user_id,
                },
            )

            record = await neo4j_result.single()
            neo4j_id = record["neo4j_id"]

            # Update PostgreSQL with Neo4j ID
            response = (
                await supabase.table("kg_entities")
                .update({"neo4j_id": str(neo4j_id)})
                .eq("id", entity_id)
                .execute()
            )

        return response.data[0]

    async def _update_entity(
        self, entity_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Update an existing entity"""

        supabase = await get_supabase()
        neo4j_driver = get_neo4j_driver()

        entity_id = entity_data["id"]

        # Get current entity data for comparison
        current_response = (
            await supabase.table("kg_entities")
            .select("*")
            .eq("id", entity_id)
            .single()
            .execute()
        )
        current_entity = current_response.data

        if not current_entity:
            raise ValueError(f"Entity {entity_id} not found")

        # Prepare updates
        updates = {}
        changes = {}

        if (
            "entity_text" in entity_data
            and entity_data["entity_text"] != current_entity["entity_text"]
        ):
            updates["entity_text"] = entity_data["entity_text"]
            changes["entity_text"] = {
                "old": current_entity["entity_text"],
                "new": entity_data["entity_text"],
            }

            # Regenerate embedding for new text
            updates["embedding"] = await get_text_embedding(entity_data["entity_text"])

        if "properties" in entity_data:
            old_props = current_entity.get("properties", {})
            new_props = entity_data["properties"]

            # Merge properties intelligently
            merged_props = {**old_props, **new_props}
            updates["properties"] = merged_props
            changes["properties"] = {"old": old_props, "new": merged_props}

        if "confidence" in entity_data:
            updates["confidence"] = entity_data["confidence"]
            changes["confidence"] = {
                "old": current_entity.get("confidence"),
                "new": entity_data["confidence"],
            }

        updates["updated_at"] = datetime.now().isoformat()
        updates["updated_by"] = user_id

        updates["is_verified"] = entity_data.get(
            "is_verified", current_entity.get("is_verified", False)
        )

        # Update PostgreSQL
        response = (
            await supabase.table("kg_entities")
            .update(updates)
            .eq("id", entity_id)
            .execute()
        )

        # Update Neo4j if neo4j_id exists
        if current_entity.get("neo4j_id"):
            async with neo4j_driver.session() as session:
                update_query = """
                    MATCH (e:Entity) WHERE id(e) = $neo4j_id
                    SET e += $properties
                """
                if "entity_text" in updates:
                    update_query += ", e.entity_text = $entity_text"

                update_query += " RETURN e"

                await session.run(
                    update_query,
                    {
                        "neo4j_id": int(current_entity["neo4j_id"]),
                        "properties": updates.get("properties", {}),
                        "entity_text": updates.get("entity_text"),
                    },
                )

        response.data[0]["changes"] = changes
        return response.data[0]

    async def _delete_entity(self, entity_id: str, user_id: str) -> Dict[str, Any]:
        """Soft delete an entity"""

        supabase = await get_supabase()
        neo4j_driver = get_neo4j_driver()

        # Get entity details
        entity_response = (
            await supabase.table("kg_entities")
            .select("*")
            .eq("id", entity_id)
            .single()
            .execute()
        )
        entity = entity_response.data

        if not entity:
            raise ValueError(f"Entity {entity_id} not found")

        # Soft delete in PostgreSQL
        await supabase.table("kg_entities").update(
            {
                "is_active": False,
                "deleted_at": datetime.now().isoformat(),
                "deleted_by": user_id,
                "deleted_reason": "Direct deletion by user",
            }
        ).eq("id", entity_id).execute()

        # Remove from Neo4j
        if entity.get("neo4j_id"):
            async with neo4j_driver.session() as session:
                await session.run(
                    """
                    MATCH (e:Entity) WHERE id(e) = $neo4j_id
                    DETACH DELETE e
                """,
                    {"neo4j_id": int(entity["neo4j_id"])},
                )

        return {"id": entity_id, "deleted": True}

    async def _create_relationship(
        self, relationship_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Create a new relationship"""

        supabase = await get_supabase()
        neo4j_driver = get_neo4j_driver()

        # Create relationship in PostgreSQL
        postgres_data = {
            "source_entity_id": relationship_data["source_entity_id"],
            "target_entity_id": relationship_data["target_entity_id"],
            "relationship_type": relationship_data["relationship_type"],
            "properties": relationship_data.get("properties", {}),
            "confidence": relationship_data.get("confidence", 0.8),
            "source_document_id": relationship_data.get("source_document_id"),
            "is_verified": relationship_data.get("is_verified", False),
            "verification_notes": relationship_data.get("verification_notes", ""),
            "created_by": user_id,
            "is_active": True,
        }

        pg_response = (
            await supabase.table("kg_relationships").insert(postgres_data).execute()
        )
        relationship_id = pg_response.data[0]["id"]

        # Get Neo4j IDs of source and target entities
        source_entity = (
            await supabase.table("kg_entities")
            .select("neo4j_id")
            .eq("id", relationship_data["source_entity_id"])
            .single()
            .execute()
        )
        target_entity = (
            await supabase.table("kg_entities")
            .select("neo4j_id")
            .eq("id", relationship_data["target_entity_id"])
            .single()
            .execute()
        )

        properties_json = json.dumps(relationship_data.get("properties", {}))

        if source_entity.data.get("neo4j_id") and target_entity.data.get("neo4j_id"):
            # Create relationship in Neo4j
            async with neo4j_driver.session() as session:
                neo4j_result = await session.run(
                    """
                    MATCH (source), (target)
                    WHERE id(source) = $source_id AND id(target) = $target_id
                    CREATE (source)-[r:{relationship_type} {{
                        relationship_id: $relationship_id,
                        properties: $properties,
                        created_by: $created_by,
                        created_at: datetime()
                    }}]->(target)
                    RETURN id(r) as neo4j_id
                """.format(
                        relationship_type=relationship_data["relationship_type"]
                    ),
                    {
                        "source_id": int(source_entity.data["neo4j_id"]),
                        "target_id": int(target_entity.data["neo4j_id"]),
                        "relationship_id": relationship_id,
                        "properties": properties_json,
                        "created_by": user_id,
                    },
                )

                record = await neo4j_result.single()
                if record:
                    neo4j_id = record["neo4j_id"]

                    # Update PostgreSQL with Neo4j ID
                    (
                        await supabase.table("kg_relationships")
                        .update({"neo4j_id": str(neo4j_id)})
                        .eq("id", relationship_id)
                        .execute()
                    )

            return pg_response.data[0]

    async def rollback_changes(self, rollback_info: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback applied changes"""

        rollback_actions = rollback_info.get("actions", [])
        rollback_results = []

        # Execute rollback actions in reverse order
        for action in reversed(rollback_actions):
            try:
                if action["type"] == "restore_entity":
                    await self._restore_entity(action["data"])
                elif action["type"] == "delete_entity":
                    await self._delete_entity(action["entity_id"], "system_rollback")
                elif action["type"] == "restore_relationship":
                    await self._restore_relationship(action["data"])
                # Add more rollback action types as needed

                rollback_results.append({"action": action, "status": "success"})

            except Exception as e:
                logger.error(f"Rollback action failed: {e}")
                rollback_results.append(
                    {"action": action, "status": "failed", "error": str(e)}
                )

        return {"rollback_results": rollback_results}

    async def _validate_edit(self, edit: KGEdit) -> List[str]:
        """Validate edit before applying"""

        errors = []

        # Validate entity data
        if edit.entity_data:
            if not edit.entity_data.get("entity_text"):
                errors.append("Entity text is required")
            if not edit.entity_data.get("entity_type"):
                errors.append("Entity type is required")

        # Validate relationship data
        if edit.relationship_data:
            if not edit.relationship_data.get("source_entity_id"):
                errors.append("Source entity ID is required")
            if not edit.relationship_data.get("target_entity_id"):
                errors.append("Target entity ID is required")
            if not edit.relationship_data.get("relationship_type"):
                errors.append("Relationship type is required")

        # Check for circular relationships
        if edit.action == KGEditAction.CREATE_RELATIONSHIP and edit.relationship_data:
            source_id = edit.relationship_data.get("source_entity_id")
            target_id = edit.relationship_data.get("target_entity_id")
            if source_id == target_id:
                errors.append("Cannot create self-referencing relationship")

        return errors

    async def _validate_edit_permissions(
        self, user_id: str, action: KGEditAction
    ) -> bool:
        """Validate user permissions for edit action"""

        from app.api.deps import get_user_permissions

        user_permissions = await get_user_permissions(user_id)

        # Admin has all permissions
        if "admin" in user_permissions.get("roles", []):
            return True

        # Expert can edit entities and relationships
        if "expert" in user_permissions.get("roles", []):
            return action in [
                KGEditAction.CREATE_ENTITY,
                KGEditAction.UPDATE_ENTITY,
                KGEditAction.CREATE_RELATIONSHIP,
                KGEditAction.UPDATE_RELATIONSHIP,
                KGEditAction.MERGE_ENTITIES,
            ]

        # Regular users cannot make direct edits
        return False

    async def _create_rollback_info(self, edit: KGEdit) -> Dict[str, Any]:
        """Create rollback information before applying changes"""

        rollback_actions = []

        if edit.action == KGEditAction.DELETE_ENTITY and edit.entity_data:
            # Store entity data for potential restoration
            supabase = await get_supabase()
            entity_response = (
                await supabase.table("kg_entities")
                .select("*")
                .eq("id", edit.entity_data["id"])
                .single()
                .execute()
            )

            if entity_response.data:
                rollback_actions.append(
                    {"type": "restore_entity", "data": entity_response.data}
                )

        return {"timestamp": datetime.now().isoformat(), "actions": rollback_actions}

    async def _log_change(
        self, edit: KGEdit, user_id: str, applied_changes: List[Dict]
    ) -> None:
        """Log the applied change for audit purposes"""

        supabase = await get_supabase()

        log_entry = {
            "user_id": user_id,
            "action": edit.action.value,
            "reason": edit.reason,
            "applied_changes": applied_changes,
            "timestamp": datetime.now().isoformat(),
        }

        await supabase.table("kg_edit_logs").insert(log_entry).execute()
