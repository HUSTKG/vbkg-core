from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from app.api.deps import RequireKGRead
from app.schemas.knowledge_graph import (EntityResponse, EntitySearchResponse,
                                         GraphQueryRequest, PathResponse,
                                         PathSearchRequest,
                                         RelationshipResponse,
                                         RelationshipSearchResponse,
                                         StatsResponse, SubgraphResponse)
from app.services.knowledge_graph import KnowledgeGraphService
from app.utils.rate_limiter import (RateLimitConfig, RateLimitScope,
                                    get_rate_limiter)

router = APIRouter()
security = HTTPBearer()

# =============================================
# ENTITY ENDPOINTS
# =============================================


@router.get("/entities/{entity_id}", response_model=EntityResponse, tags=["Entities"])
async def get_entity(
    entity_id: str,
    include_relationships: bool = Query(
        default=False, description="Include entity relationships"
    ),
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Get entity by ID with optional relationships"""

    # Rate limiting
    rate_limiter = get_rate_limiter()
    rate_check = await rate_limiter.check_limit(
        identifier=current_user["id"],
        scope=RateLimitScope.USER,
        config_name="api_standard",
    )

    if not rate_check.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=rate_check.to_headers(),
        )

    entity = await kg_service.get_entity(entity_id, include_relationships)

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return entity


@router.get("/entities", response_model=EntitySearchResponse, tags=["Entities"])
async def search_entities(
    query: Optional[str] = Query(default=None, description="Search query"),
    entity_types: Optional[List[str]] = Query(
        default=None, description="Filter by entity types"
    ),
    limit: int = Query(default=50, le=100000, description="Results per page"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    min_confidence: float = Query(
        default=0.0, ge=0.0, le=1.0, description="Minimum confidence score"
    ),
    verified_only: bool = Query(default=False, description="Only verified entities"),
    semantic_search: bool = Query(default=False, description="Use semantic search"),
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Search entities with various filters"""

    # Rate limiting - semantic search is more expensive
    config_name = "search_heavy" if semantic_search else "api_standard"
    rate_limiter = get_rate_limiter()
    rate_check = await rate_limiter.check_limit(
        identifier=current_user["id"],
        scope=RateLimitScope.USER,
        config_name=config_name,
    )

    if not rate_check.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=rate_check.to_headers(),
        )

    return await kg_service.search_entities(
        query=query,
        entity_types=entity_types,
        limit=limit,
        offset=offset,
        min_confidence=min_confidence,
        verified_only=verified_only,
        semantic_search=semantic_search,
    )


@router.get("/entities/types", response_model=List[Dict[str, Any]], tags=["Entities"])
async def get_entity_types(
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Get all entity types with counts"""

    return await kg_service.get_entity_types()


@router.get(
    "/entities/{entity_id}/neighbors",
    response_model=Dict[str, Any],
    tags=["Graph Traversal"],
)
async def get_entity_neighbors(
    entity_id: str,
    max_depth: int = Query(default=1, le=3, description="Maximum traversal depth"),
    relationship_types: Optional[List[str]] = Query(
        default=None, description="Filter by relationship types"
    ),
    limit_per_level: int = Query(
        default=10, le=50, description="Entities per depth level"
    ),
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Get neighboring entities"""

    return await kg_service.get_entity_neighbors(
        entity_id=entity_id,
        max_depth=max_depth,
        relationship_types=relationship_types,
        limit_per_level=limit_per_level,
    )


# =============================================
# RELATIONSHIP ENDPOINTS
# =============================================

@router.get(
    "/relationships",
    response_model=RelationshipSearchResponse,
    tags=["Relationships"],
)
async def search_relationships(
    query: Optional[str] = Query(default=None, description="Search query"),
    relationship_types: Optional[List[str]] = Query(
    default=None, description="Filter by relationship types"
        ),
    limit: int = Query(default=50, le=200, description="Results per page"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    min_confidence: float = Query(
    default=0.0, ge=0.0, le=1.0, description="Minimum confidence score"
        ),
    verified_only: bool = Query(default=False, description="Only verified relationships"),
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Search relationships with various filters"""
    # Rate limiting
    rate_limiter = get_rate_limiter()
    rate_check = await rate_limiter.check_limit(
        identifier=current_user["id"],
        scope=RateLimitScope.USER,
        config_name="api_standard",
    )
    if not rate_check.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=rate_check.to_headers(),
        )
    return await kg_service.search_relationships(
        query=query,
        relationship_types=relationship_types,
        limit=limit,
        offset=offset,
        min_confidence=min_confidence,
        verified_only=verified_only,
    )



@router.get(
    "/relationships/{relationship_id}",
    response_model=RelationshipResponse,
    tags=["Relationships"],
)
async def get_relationship(
    relationship_id: str,
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Get relationship by ID"""

    relationship = await kg_service.get_relationship(relationship_id)

    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")

    return relationship


@router.get(
    "/entities/{entity_id}/relationships",
    response_model=RelationshipSearchResponse,
    tags=["Relationships"],
)
async def get_entity_relationships(
    entity_id: str,
    relationship_types: Optional[List[str]] = Query(
        default=None, description="Filter by relationship types"
    ),
    direction: str = Query(
        default="both",
        regex="^(incoming|outgoing|both)$",
        description="Relationship direction",
    ),
    limit: int = Query(default=50, le=200, description="Results per page"),
    offset: int = Query(default=0, ge=0, description="Results offset"),
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Get relationships for an entity"""

    return await kg_service.get_entity_relationships(
        entity_id=entity_id,
        relationship_types=relationship_types,
        direction=direction,
        limit=limit,
        offset=offset,
    )


# =============================================
# GRAPH TRAVERSAL ENDPOINTS
# =============================================


@router.get(
    "/entities/{entity_id}/subgraph",
    response_model=SubgraphResponse,
    tags=["Graph Traversal"],
)
async def get_subgraph(
    entity_id: str,
    radius: int = Query(default=2, le=3, description="Subgraph radius"),
    max_nodes: int = Query(default=50, le=200, description="Maximum nodes in subgraph"),
    relationship_types: Optional[List[str]] = Query(
        default=None, description="Filter by relationship types"
    ),
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Get subgraph around an entity"""

    # Rate limiting for expensive operations
    rate_limiter = get_rate_limiter()
    rate_check = await rate_limiter.check_limit(
        identifier=current_user["id"],
        scope=RateLimitScope.USER,
        config_name="search_heavy",
    )

    if not rate_check.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=rate_check.to_headers(),
        )

    return await kg_service.get_subgraph(
        entity_id=entity_id,
        radius=radius,
        max_nodes=max_nodes,
        relationship_types=relationship_types,
    )


@router.post("/paths", response_model=List[PathResponse], tags=["Graph Traversal"])
async def find_paths(
    path_request: PathSearchRequest,
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Find shortest paths between two entities"""

    # Rate limiting for expensive operations
    rate_limiter = get_rate_limiter()
    rate_check = await rate_limiter.check_limit(
        identifier=current_user["id"],
        scope=RateLimitScope.USER,
        config_name="search_heavy",
    )

    if not rate_check.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=rate_check.to_headers(),
        )

    return await kg_service.find_path(
        source_entity_id=path_request.source_entity_id,
        target_entity_id=path_request.target_entity_id,
        max_depth=path_request.max_depth,
        relationship_types=path_request.relationship_types,
    )


@router.post("/query", tags=["Graph Traversal"])
async def execute_graph_query(
    query_request: GraphQueryRequest,
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Execute custom Cypher query (Admin/Expert only)"""

    # Check admin/expert permissions
    user_roles = current_user.get("roles", [])
    if not any(role in ["admin", "expert"] for role in user_roles):
        raise HTTPException(status_code=403, detail="Admin or Expert role required")

    # Rate limiting for expensive operations
    rate_limiter = get_rate_limiter()
    rate_check = await rate_limiter.check_limit(
        identifier=current_user["id"],
        scope=RateLimitScope.USER,
        custom_config=RateLimitConfig(
            limit=10, window=3600, cost=5
        ),  # Very restrictive
    )

    if not rate_check.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=rate_check.to_headers(),
        )

    # Execute query with safety checks
    try:
        # Validate query safety (no mutations allowed)
        query_upper = query_request.cypher_query.upper()
        forbidden_keywords = [
            "CREATE",
            "DELETE",
            "SET",
            "REMOVE",
            "MERGE",
            "DROP",
            "DETACH",
        ]

        if any(keyword in query_upper for keyword in forbidden_keywords):
            raise HTTPException(status_code=400, detail="Only read queries are allowed")

        # Execute query through Neo4j service
        async with kg_service.neo4j_driver.session() as session:
            result = await session.run(
                query_request.cypher_query, query_request.parameters
            )

            records = []
            async for record in result:
                records.append(dict(record))

            return {
                "records": records[: query_request.limit],
                "query": query_request.cypher_query,
                "parameters": query_request.parameters,
                "count": len(records),
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query execution failed: {str(e)}")


# =============================================
# ANALYTICS & STATISTICS
# =============================================


@router.get("/stats", response_model=StatsResponse, tags=["Analytics"])
async def get_knowledge_graph_stats(
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Get comprehensive KG statistics"""

    # Check permissions
    return await kg_service.get_knowledge_graph_stats()


@router.get("/insights/investment", tags=["Analytics"])
async def get_investment_insights(
    entity_type: str = Query(
        default="ORGANIZATION", description="Entity type to analyze"
    ),
    limit: int = Query(default=20, le=100, description="Results limit"),
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Get investment-specific insights"""

    return await kg_service.get_investment_insights(entity_type, limit)


# =============================================
# SEARCH & DISCOVERY
# =============================================


@router.get("/search", tags=["Search"])
async def global_search(
    query: str = Query(..., min_length=2, description="Search query"),
    search_type: str = Query(
        default="mixed",
        regex="^(entities|relationships|mixed)$",
        description="Search scope",
    ),
    semantic: bool = Query(default=False, description="Use semantic search"),
    limit: int = Query(default=20, le=100, description="Results limit"),
    current_user: dict = Depends(RequireKGRead),
    kg_service: KnowledgeGraphService = Depends(),
):
    """Global search across entities and relationships"""

    # Rate limiting
    config_name = "search_heavy" if semantic else "api_standard"
    rate_limiter = get_rate_limiter()
    rate_check = await rate_limiter.check_limit(
        identifier=current_user["id"],
        scope=RateLimitScope.USER,
        config_name=config_name,
    )

    if not rate_check.allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers=rate_check.to_headers(),
        )

    results = {}

    if search_type in ["entities", "mixed"]:
        entity_results = await kg_service.search_entities(
            query=query, limit=limit, semantic_search=semantic
        )
        results["entities"] = entity_results

    if search_type in ["relationships", "mixed"]:
        # Search relationships by type or properties
        # This would need additional implementation in the service
        results["relationships"] = []

    return {
        "query": query,
        "search_type": search_type,
        "semantic": semantic,
        "results": results,
    }
