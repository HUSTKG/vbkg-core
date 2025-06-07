from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from app.api.deps import RequireKGEdit, RequireKGRead
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.domain import (CreateDomainRequest, CreateEntityTypeRequest,
                                CreateRelationshipTypeRequest,
                                DomainDetailResponse, DomainResponse,
                                DomainStatsResponse, EntityTypeResponse,
                                RelationshipTypeResponse,
                                TypeDomainMappingRequest,
                                TypeValidationRequest, TypeValidationResponse,
                                UpdateDomainRequest, UpdateEntityTypeRequest,
                                UpdateRelationshipTypeRequest)
from app.services.domain import DomainService
from app.utils.rate_limiter import RateLimitScope, get_rate_limiter

router = APIRouter()
security = HTTPBearer()

# =============================================
# DOMAIN ENDPOINTS
# =============================================


@router.post("/domains", response_model=DomainResponse, tags=["Domains"])
async def create_domain(
    domain_request: CreateDomainRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Create a new domain"""

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

    try:
        domain = await domain_service.create_domain(
            domain_request.dict(), current_user["id"]
        )
        return domain
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/domains", response_model=PaginatedResponse[DomainResponse], tags=["Domains"]
)
async def search_domains(
    query: Optional[str] = Query(default=None, description="Search query"),
    is_active: Optional[bool] = Query(
        default=None, description="Filter by active status"
    ),
    limit: int = Query(default=50, le=200, description="Results per page"),
    skip: int = Query(default=0, ge=0, description="Results skip"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Search domains"""

    response = await domain_service.search_domains(
        query=query, is_active=is_active, limit=limit, skip=skip
    )

    return PaginatedResponse(
        data=response["domains"],
        meta=PaginatedMeta(
            limit=limit,
            skip=skip,
            total=response["total"],
        ),
        message="Domains retrieved successfully",
        status=200,
    )


@router.get(
    "/domains/{domain_id}", response_model=DomainDetailResponse, tags=["Domains"]
)
async def get_domain(
    domain_id: int,
    include_types: bool = Query(
        default=False, description="Include entity/relationship types"
    ),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get domain by ID with optional types"""

    domain = await domain_service.get_domain(domain_id, include_types)

    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    return domain


@router.put("/domains/{domain_id}", response_model=DomainResponse, tags=["Domains"])
async def update_domain(
    domain_id: int,
    update_request: UpdateDomainRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Update domain"""

    try:
        # Filter out None values
        update_data = {k: v for k, v in update_request.dict().items() if v is not None}
        domain = await domain_service.update_domain(
            domain_id, update_data, current_user["id"]
        )
        return domain
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/domains/{domain_id}", tags=["Domains"])
async def delete_domain(
    domain_id: int,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Delete domain"""

    success = await domain_service.delete_domain(domain_id, current_user["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Domain not found")

    return {"message": "Domain deleted successfully"}


@router.get(
    "/domains/{domain_id}/stats", response_model=DomainStatsResponse, tags=["Domains"]
)
async def get_domain_stats(
    domain_id: int,
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get domain statistics"""

    stats = await domain_service.get_domain_stats(domain_id)
    return stats


# =============================================
# ENTITY TYPE ENDPOINTS
# =============================================


@router.post("/entity-types", response_model=EntityTypeResponse, tags=["Entity Types"])
async def create_entity_type(
    type_request: CreateEntityTypeRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Create a new entity type"""

    try:
        entity_type = await domain_service.create_entity_type(
            type_request.dict(), current_user["id"]
        )
        return entity_type
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/entity-types",
    response_model=PaginatedResponse[EntityTypeResponse],
    tags=["Entity Types"],
)
async def search_entity_types(
    query: Optional[str] = Query(default=None, description="Search query"),
    domain_ids: Optional[List[int]] = Query(
        default=None, description="Filter by domain IDs"
    ),
    is_mapped: Optional[bool] = Query(
        default=None, description="Filter by mapped status"
        ),
    is_active: Optional[bool] = Query(
        default=None, description="Filter by active status"
    ),
    include_usage: bool = Query(default=False, description="Include usage statistics"),
    limit: int = Query(default=50, le=200, description="Results per page"),
    skip: int = Query(default=0, ge=0, description="Results skip"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Search entity types"""

    response = await domain_service.search_entity_types(
        query=query,
        domain_ids=domain_ids,
        is_active=is_active,
        is_mapped=is_mapped,
        include_usage=include_usage,
        limit=limit,
        skip=skip,
    )

    return PaginatedResponse(
        data=response["entity_types"],
        meta=PaginatedMeta(
            limit=limit,
            skip=skip,
            total=response["total"],
        ),
        message="Entity types retrieved successfully",
        status=200,
    )


@router.get(
    "/entity-types/{type_id}", response_model=EntityTypeResponse, tags=["Entity Types"]
)
async def get_entity_type(
    type_id: int,
    include_domains: bool = Query(
        default=False, description="Include associated domains"
    ),
    include_usage: bool = Query(default=False, description="Include usage statistics"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get entity type by ID"""

    entity_type = await domain_service.get_entity_type(
        type_id, include_domains, include_usage
    )

    if not entity_type:
        raise HTTPException(status_code=404, detail="Entity type not found")

    return entity_type


@router.put(
    "/entity-types/{type_id}", response_model=EntityTypeResponse, tags=["Entity Types"]
)
async def update_entity_type(
    type_id: int,
    update_request: UpdateEntityTypeRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Update entity type"""

    try:
        # Filter out None values
        update_data = {k: v for k, v in update_request.dict().items() if v is not None}
        entity_type = await domain_service.update_entity_type(
            type_id, update_data, current_user["id"]
        )
        return entity_type
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/entity-types/{type_id}", tags=["Entity Types"])
async def delete_entity_type(
    type_id: int,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Delete entity type"""

    success = await domain_service.delete_entity_type(type_id, current_user["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Entity type not found")

    return {"message": "Entity type deleted successfully"}


# =============================================
# RELATIONSHIP TYPE ENDPOINTS
# =============================================


@router.post(
    "/relationship-types",
    response_model=RelationshipTypeResponse,
    tags=["Relationship Types"],
)
async def create_relationship_type(
    type_request: CreateRelationshipTypeRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Create a new relationship type"""

    try:
        relationship_type = await domain_service.create_relationship_type(
            type_request.dict(), current_user["id"]
        )
        return relationship_type
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/relationship-types",
    response_model=PaginatedResponse[RelationshipTypeResponse],
    tags=["Relationship Types"],
)
async def search_relationship_types(
    query: Optional[str] = Query(default=None, description="Search query"),
    domain_ids: Optional[List[int]] = Query(
        default=None, description="Filter by domain IDs"
    ),
    source_entity_type_id: Optional[int] = Query(
        default=None, description="Filter by source entity type"
    ),
    is_mapped: Optional[bool] = Query(
        default=None, description="Filter by mapped status"
        ),
    target_entity_type_id: Optional[int] = Query(
        default=None, description="Filter by target entity type"
    ),
    is_bidirectional: Optional[bool] = Query(
        default=None, description="Filter by bidirectional"
    ),
    is_active: Optional[bool] = Query(
        default=None, description="Filter by active status"
    ),
    include_usage: bool = Query(default=False, description="Include usage statistics"),
    limit: int = Query(default=50, le=200, description="Results per page"),
    skip: int = Query(default=0, ge=0, description="Results skip"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Search relationship types"""

    response = await domain_service.search_relationship_types(
        query=query,
        domain_ids=domain_ids,
        source_entity_type_id=source_entity_type_id,
        target_entity_type_id=target_entity_type_id,
        is_bidirectional=is_bidirectional,
        is_active=is_active,
        is_mapped=is_mapped,
        include_usage=include_usage,
        limit=limit,
        skip=skip,
    )

    return PaginatedResponse(
        data=response["relationship_types"],
        meta=PaginatedMeta(
            limit=limit,
            skip=skip,
            total=response["total"],
        ),
        message="Relationship types retrieved successfully",
        status=200,
    )


@router.get(
    "/relationship-types/{type_id}",
    response_model=RelationshipTypeResponse,
    tags=["Relationship Types"],
)
async def get_relationship_type(
    type_id: int,
    include_domains: bool = Query(
        default=False, description="Include associated domains"
    ),
    include_usage: bool = Query(default=False, description="Include usage statistics"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get relationship type by ID"""

    relationship_type = await domain_service.get_relationship_type(
        type_id, include_domains, include_usage
    )

    if not relationship_type:
        raise HTTPException(status_code=404, detail="Relationship type not found")

    return relationship_type


@router.put(
    "/relationship-types/{type_id}",
    response_model=RelationshipTypeResponse,
    tags=["Relationship Types"],
)
async def update_relationship_type(
    type_id: int,
    update_request: UpdateRelationshipTypeRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Update relationship type"""

    try:
        # Filter out None values
        update_data = {k: v for k, v in update_request.dict().items() if v is not None}
        relationship_type = await domain_service.update_relationship_type(
            type_id, update_data, current_user["id"]
        )
        return relationship_type
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/relationship-types/{type_id}", tags=["Relationship Types"])
async def delete_relationship_type(
    type_id: int,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Delete relationship type"""

    success = await domain_service.delete_relationship_type(type_id, current_user["id"])

    if not success:
        raise HTTPException(status_code=404, detail="Relationship type not found")

    return {"message": "Relationship type deleted successfully"}


# =============================================
# DOMAIN MAPPING ENDPOINTS
# =============================================


@router.post("/entity-types/{type_id}/domains", tags=["Domain Mappings"])
async def add_entity_type_to_domain(
    type_id: int,
    mapping_request: TypeDomainMappingRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Add entity type to domain"""

    try:
        mapping = await domain_service.add_entity_type_to_domain(
            type_id=type_id,
            domain_id=mapping_request.domain_id,
            is_primary=mapping_request.is_primary,
            config=mapping_request.domain_specific_config,
        )
        return mapping
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/entity-types/{type_id}/domains/{domain_id}", tags=["Domain Mappings"])
async def remove_entity_type_from_domain(
    type_id: int,
    domain_id: int,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Remove entity type from domain"""

    success = await domain_service.remove_entity_type_from_domain(type_id, domain_id)

    if not success:
        raise HTTPException(status_code=404, detail="Mapping not found")

    return {"message": "Entity type removed from domain successfully"}


@router.post("/relationship-types/{type_id}/domains", tags=["Domain Mappings"])
async def add_relationship_type_to_domain(
    type_id: int,
    mapping_request: TypeDomainMappingRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Add relationship type to domain"""

    try:
        mapping = await domain_service.add_relationship_type_to_domain(
            type_id=type_id,
            domain_id=mapping_request.domain_id,
            is_primary=mapping_request.is_primary,
            config=mapping_request.domain_specific_config,
        )
        return mapping
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/relationship-types/{type_id}/domains/{domain_id}", tags=["Domain Mappings"]
)
async def remove_relationship_type_from_domain(
    type_id: int,
    domain_id: int,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Remove relationship type from domain"""

    success = await domain_service.remove_relationship_type_from_domain(
        type_id, domain_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Mapping not found")

    return {"message": "Relationship type removed from domain successfully"}


# =============================================
# VALIDATION ENDPOINTS
# =============================================


@router.post("/validate", response_model=TypeValidationResponse, tags=["Validation"])
async def validate_type_constraints(
    validation_request: TypeValidationRequest,
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Validate relationship type constraints"""

    if not all(
        [
            validation_request.relationship_type_id,
            validation_request.source_entity_type_id,
            validation_request.target_entity_type_id,
        ]
    ):
        raise HTTPException(
            status_code=400,
            detail="relationship_type_id, source_entity_type_id, and target_entity_type_id are required",
        )

    validation_result = await domain_service.validate_relationship_type_constraints(
        validation_request.relationship_type_id,
        validation_request.source_entity_type_id,
        validation_request.target_entity_type_id,
    )

    return validation_result


# =============================================
# UTILITY ENDPOINTS
# =============================================


@router.get(
    "/entity-types/by-domain/{domain_name}",
    response_model=ApiResponse[List[EntityTypeResponse]],
    tags=["Utilities"],
)
async def get_entity_types_by_domain(
    domain_name: str,
    primary_only: bool = Query(default=False, description="Only primary entity types"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get entity types for a specific domain by name"""

    # This would use the database function created in migration
    from app.core.supabase import get_supabase

    supabase = await get_supabase()

    # Call the database function
    response = await supabase.rpc(
        "get_domain_entity_types", {"domain_name": domain_name}
    ).execute()

    entity_types = response.data

    if primary_only:
        entity_types = [et for et in entity_types if et.get("is_primary")]

    return ApiResponse(
        data=[EntityTypeResponse(**et) for et in entity_types],
        message="Entity types retrieved successfully",
        status=200,
    )


@router.get(
    "/relationship-types/by-domain/{domain_name}",
    response_model=List[RelationshipTypeResponse],
    tags=["Utilities"],
)
async def get_relationship_types_by_domain(
    domain_name: str,
    primary_only: bool = Query(
        default=False, description="Only primary relationship types"
    ),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get relationship types for a specific domain by name"""

    from app.core.supabase import get_supabase

    supabase = await get_supabase()

    # Call the database function
    response = await supabase.rpc(
        "get_domain_relationship_types", {"domain_name": domain_name}
    ).execute()

    relationship_types = response.data

    if primary_only:
        relationship_types = [rt for rt in relationship_types if rt.get("is_primary")]

    return relationship_types


@router.get("/compatible-relationships", tags=["Utilities"])
async def get_compatible_relationships(
    source_entity_type_id: int = Query(..., description="Source entity type ID"),
    target_entity_type_id: Optional[int] = Query(
        default=None, description="Target entity type ID"
    ),
    domain_ids: Optional[List[int]] = Query(
        default=None, description="Filter by domain IDs"
    ),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get relationship types compatible with given entity types"""

    # Search relationship types that allow the given source/target entity types
    filters = {
        "source_entity_type_id": source_entity_type_id,
        "domain_ids": domain_ids,
        "is_active": True,
        "limit": 100,
    }

    if target_entity_type_id:
        filters["target_entity_type_id"] = target_entity_type_id

    compatible_relationships = await domain_service.search_relationship_types(**filters)

    return {
        "source_entity_type_id": source_entity_type_id,
        "target_entity_type_id": target_entity_type_id,
        "compatible_relationships": compatible_relationships["relationship_types"],
    }


# =============================================
# ANALYTICS ENDPOINTS
# =============================================


@router.get("/analytics/overview", tags=["Analytics"])
async def get_domain_analytics_overview(
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get domain system analytics overview"""

    from app.core.supabase import get_supabase

    supabase = await get_supabase()

    # Get counts for overview
    domains_count = (
        await supabase.table("domains")
        .select("*", count="exact")
        .eq("is_active", True)
        .execute()
    ).count
    entity_types_count = (
        await supabase.table("entity_types")
        .select("*", count="exact")
        .eq("is_active", True)
        .execute()
    ).count
    relationship_types_count = (
        await supabase.table("relationship_types")
        .select("*", count="exact")
        .eq("is_active", True)
        .execute()
    ).count

    # Get domain distribution
    domains = await domain_service.search_domains(is_active=True, limit=100)

    domain_stats = []
    for domain in domains["domains"]:
        stats = await domain_service.get_domain_stats(domain["id"])
        stats["domain_name"] = domain["name"]
        stats["display_name"] = domain["display_name"]
        domain_stats.append(stats)

    return {
        "overview": {
            "total_domains": domains_count,
            "total_entity_types": entity_types_count,
            "total_relationship_types": relationship_types_count,
            "active_domains": len([d for d in domains["domains"] if d["is_active"]]),
        },
        "domain_stats": domain_stats,
        "generated_at": datetime.now().isoformat(),
    }


# =============================================
# BULK OPERATIONS
# =============================================


@router.post("/bulk/entity-types", tags=["Bulk Operations"])
async def bulk_create_entity_types(
    entity_types: List[CreateEntityTypeRequest],
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Bulk create entity types"""

    # Check admin permissions for bulk operations
    user_roles = current_user.get("roles", [])
    if not any(role in ["admin", "editor"] for role in user_roles):
        raise HTTPException(
            status_code=403, detail="Admin or Editor role required for bulk operations"
        )

    results = []
    errors = []

    for i, entity_type_request in enumerate(entity_types):
        try:
            entity_type = await domain_service.create_entity_type(
                entity_type_request.dict(), current_user["id"]
            )
            results.append(entity_type)
        except Exception as e:
            errors.append(
                {"index": i, "name": entity_type_request.name, "error": str(e)}
            )

    return {
        "created": results,
        "errors": errors,
        "total_attempted": len(entity_types),
        "successful": len(results),
        "failed": len(errors),
    }


@router.post("/bulk/relationship-types", tags=["Bulk Operations"])
async def bulk_create_relationship_types(
    relationship_types: List[CreateRelationshipTypeRequest],
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Bulk create relationship types"""

    # Check admin permissions for bulk operations
    user_roles = current_user.get("roles", [])
    if not any(role in ["admin", "editor"] for role in user_roles):
        raise HTTPException(
            status_code=403, detail="Admin or Editor role required for bulk operations"
        )

    results = []
    errors = []

    for i, relationship_type_request in enumerate(relationship_types):
        try:
            relationship_type = await domain_service.create_relationship_type(
                relationship_type_request.dict(), current_user["id"]
            )
            results.append(relationship_type)
        except Exception as e:
            errors.append(
                {"index": i, "name": relationship_type_request.name, "error": str(e)}
            )

    return {
        "created": results,
        "errors": errors,
        "total_attempted": len(relationship_types),
        "successful": len(results),
        "failed": len(errors),
    }
