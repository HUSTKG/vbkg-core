from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer

from app.api.deps import RequireKGEdit, RequireKGRead, validate_rate_limits
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.domain import (BulkOntologyClassAssociationRequest,
                                BulkOntologyPropertyAssociationRequest,
                                BulkOperationResponse, CreateDomainRequest,
                                DomainDetailResponse, DomainResponse,
                                DomainStatsResponse,
                                OntologyClassDomainMappingRequest,
                                OntologyClassResponse,
                                OntologyPropertyDomainMappingRequest,
                                OntologyPropertyResponse,
                                OntologyValidationRequest,
                                OntologyValidationResponse,
                                UpdateDomainRequest)
from app.services.domain import DomainService
from app.utils.rate_limiter import RateLimitScope, get_rate_limiter

router = APIRouter(
    dependencies=[Depends(validate_rate_limits)],  # Add rate limiting
        )

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


@router.get("/domains", response_model=PaginatedResponse[DomainResponse], tags=["Domains"])
async def search_domains(
    query: Optional[str] = Query(default=None, description="Search query"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    has_ontology_classes: Optional[bool] = Query(default=None, description="Filter by having ontology classes"),
    has_ontology_properties: Optional[bool] = Query(default=None, description="Filter by having ontology properties"),
    ontology_namespace: Optional[str] = Query(default=None, description="Filter by ontology namespace"),
    limit: int = Query(default=50, le=200, description="Results per page"),
    skip: int = Query(default=0, ge=0, description="Results skip"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Search domains"""

    response = await domain_service.search_domains(
        query=query, 
        is_active=is_active,
        has_ontology_classes=has_ontology_classes,
        has_ontology_properties=has_ontology_properties,
        ontology_namespace=ontology_namespace,
        limit=limit, 
        skip=skip
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


@router.get("/domains/{domain_id}", response_model=DomainDetailResponse, tags=["Domains"])
async def get_domain(
    domain_id: int,
    include_ontology: bool = Query(default=False, description="Include ontology classes/properties"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get domain by ID with optional ontology classes/properties"""

    domain = await domain_service.get_domain(domain_id, include_ontology)

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


@router.get("/domains/{domain_id}/stats", response_model=ApiResponse[DomainStatsResponse], tags=["Domains"])
async def get_domain_stats(
    domain_id: int,
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get domain statistics"""

    stats = await domain_service.get_domain_stats(domain_id)
    return ApiResponse(
        data=stats,
        message="Domain statistics retrieved successfully",
        status=200,
    )

# =============================================
# ONTOLOGY CLASS ENDPOINTS
# =============================================

@router.get("/domains/{domain_id}/ontology-classes", response_model=PaginatedResponse[OntologyClassResponse], tags=["Ontology Classes"])
async def get_domain_ontology_classes(
    domain_id: int,
    query: Optional[str] = Query(default=None, description="Search query"),
    is_custom: Optional[bool] = Query(default=None, description="Filter by custom classes"),
    include_usage: bool = Query(default=False, description="Include usage statistics"),
    limit: int = Query(default=50, le=200, description="Results per page"),
    skip: int = Query(default=0, ge=0, description="Results skip"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get ontology classes for a domain"""

    response = await domain_service.get_ontology_classes_for_domain(
        domain_id=domain_id,
        query=query,
        is_custom=is_custom,
        include_usage=include_usage,
        limit=limit,
        skip=skip,
    )

    return PaginatedResponse(
        data=response["ontology_classes"],
        meta=PaginatedMeta(
            limit=limit,
            skip=skip,
            total=response["total"],
        ),
        message="Ontology classes retrieved successfully",
        status=200,
    )


@router.get("/ontology-classes", response_model=PaginatedResponse[OntologyClassResponse], tags=["Ontology Classes"])
async def search_ontology_classes(
    query: Optional[str] = Query(default=None, description="Search query"),
    domain_ids: Optional[List[int]] = Query(default=None, description="Filter by domain IDs"),
    is_custom: Optional[bool] = Query(default=None, description="Filter by custom classes"),
    parent_class_id: Optional[int] = Query(default=None, description="Filter by parent class"),
    include_usage: bool = Query(default=False, description="Include usage statistics"),
    limit: int = Query(default=50, le=200, description="Results per page"),
    skip: int = Query(default=0, ge=0, description="Results skip"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Search ontology classes"""

    response = await domain_service.search_ontology_classes(
        query=query,
        domain_ids=domain_ids,
        is_custom=is_custom,
        parent_class_id=parent_class_id,
        include_usage=include_usage,
        limit=limit,
        skip=skip,
    )

    return PaginatedResponse(
        data=response["ontology_classes"],
        meta=PaginatedMeta(
            limit=limit,
            skip=skip,
            total=response["total"],
        ),
        message="Ontology classes retrieved successfully",
        status=200,
    )

# =============================================
# ONTOLOGY PROPERTY ENDPOINTS
# =============================================

@router.get("/domains/{domain_id}/ontology-properties", response_model=PaginatedResponse[OntologyPropertyResponse], tags=["Ontology Properties"])
async def get_domain_ontology_properties(
    domain_id: int,
    query: Optional[str] = Query(default=None, description="Search query"),
    property_type: Optional[str] = Query(default=None, description="Filter by property type"),
    domain_class_id: Optional[int] = Query(default=None, description="Filter by domain class"),
    range_class_id: Optional[int] = Query(default=None, description="Filter by range class"),
    is_custom: Optional[bool] = Query(default=None, description="Filter by custom properties"),
    include_usage: bool = Query(default=False, description="Include usage statistics"),
    limit: int = Query(default=50, le=200, description="Results per page"),
    skip: int = Query(default=0, ge=0, description="Results skip"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get ontology properties for a domain"""

    response = await domain_service.get_ontology_properties_for_domain(
        domain_id=domain_id,
        query=query,
        property_type=property_type,
        domain_class_id=domain_class_id,
        range_class_id=range_class_id,
        is_custom=is_custom,
        include_usage=include_usage,
        limit=limit,
        skip=skip,
    )

    return PaginatedResponse(
        data=response["ontology_properties"],
        meta=PaginatedMeta(
            limit=limit,
            skip=skip,
            total=response["total"],
        ),
        message="Ontology properties retrieved successfully",
        status=200,
    )


@router.get("/ontology-properties", response_model=PaginatedResponse[OntologyPropertyResponse], tags=["Ontology Properties"])
async def search_ontology_properties(
    query: Optional[str] = Query(default=None, description="Search query"),
    domain_ids: Optional[List[int]] = Query(default=None, description="Filter by domain IDs"),
    property_type: Optional[str] = Query(default=None, description="Filter by property type"),
    domain_class_id: Optional[int] = Query(default=None, description="Filter by domain class"),
    range_class_id: Optional[int] = Query(default=None, description="Filter by range class"),
    is_custom: Optional[bool] = Query(default=None, description="Filter by custom properties"),
    include_usage: bool = Query(default=False, description="Include usage statistics"),
    limit: int = Query(default=50, le=200, description="Results per page"),
    skip: int = Query(default=0, ge=0, description="Results skip"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Search ontology properties"""

    response = await domain_service.search_ontology_properties(
        query=query,
        domain_ids=domain_ids,
        property_type=property_type,
        domain_class_id=domain_class_id,
        range_class_id=range_class_id,
        is_custom=is_custom,
        include_usage=include_usage,
        limit=limit,
        skip=skip,
    )

    return PaginatedResponse(
        data=response["ontology_properties"],
        meta=PaginatedMeta(
            limit=limit,
            skip=skip,
            total=response["total"],
        ),
        message="Ontology properties retrieved successfully",
        status=200,
    )

# =============================================
# DOMAIN MAPPING ENDPOINTS
# =============================================

@router.post("/ontology-classes/{class_id}/domains", tags=["Domain Mappings"])
async def add_ontology_class_to_domain(
    class_id: int,
    mapping_request: OntologyClassDomainMappingRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Add ontology class to domain"""

    try:
        mapping = await domain_service.add_ontology_class_to_domain(
            class_id=class_id,
            domain_id=mapping_request.domain_id,
            is_primary=mapping_request.is_primary,
            config=mapping_request.domain_specific_config,
        )
        return mapping
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/ontology-classes/{class_id}/domains/{domain_id}", tags=["Domain Mappings"])
async def remove_ontology_class_from_domain(
    class_id: int,
    domain_id: int,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Remove ontology class from domain"""

    success = await domain_service.remove_ontology_class_from_domain(class_id, domain_id)

    if not success:
        raise HTTPException(status_code=404, detail="Mapping not found")

    return {"message": "Ontology class removed from domain successfully"}


@router.post("/ontology-properties/{property_id}/domains", tags=["Domain Mappings"])
async def add_ontology_property_to_domain(
    property_id: int,
    mapping_request: OntologyPropertyDomainMappingRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Add ontology property to domain"""

    try:
        mapping = await domain_service.add_ontology_property_to_domain(
            property_id=property_id,
            domain_id=mapping_request.domain_id,
            is_primary=mapping_request.is_primary,
            config=mapping_request.domain_specific_config,
        )
        return mapping
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/ontology-properties/{property_id}/domains/{domain_id}", tags=["Domain Mappings"])
async def remove_ontology_property_from_domain(
    property_id: int,
    domain_id: int,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Remove ontology property from domain"""

    success = await domain_service.remove_ontology_property_from_domain(property_id, domain_id)

    if not success:
        raise HTTPException(status_code=404, detail="Mapping not found")

    return {"message": "Ontology property removed from domain successfully"}

# =============================================
# VALIDATION ENDPOINTS
# =============================================

@router.post("/validate-ontology", response_model=OntologyValidationResponse, tags=["Validation"])
async def validate_ontology_constraints(
    validation_request: OntologyValidationRequest,
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Validate ontology property constraints"""

    if not all([
        validation_request.ontology_property_id,
        validation_request.source_ontology_class_id,
        validation_request.target_ontology_class_id,
    ]):
        raise HTTPException(
            status_code=400,
            detail="ontology_property_id, source_ontology_class_id, and target_ontology_class_id are required",
        )

    validation_result = await domain_service.validate_ontology_property_constraints(
        validation_request.ontology_property_id,
        validation_request.source_ontology_class_id,
        validation_request.target_ontology_class_id,
    )

    return validation_result

# =============================================
# SUGGESTION ENDPOINTS
# =============================================

@router.post("/suggest/ontology-classes", response_model=ApiResponse[List[Dict]], tags=["Suggestions"])
async def suggest_ontology_classes(
    text: str,
    domain_id: Optional[int] = Query(default=None, description="Domain ID filter"),
    max_suggestions: int = Query(default=5, ge=1, le=20, description="Maximum suggestions"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Suggest ontology classes for text"""

    suggestions = await domain_service.suggest_ontology_classes_for_text(
        text=text,
        domain_id=domain_id,
        max_suggestions=max_suggestions,
    )

    return ApiResponse(
        data=suggestions,
        message="Ontology class suggestions retrieved successfully",
        status=200,
    )


@router.post("/suggest/ontology-properties", response_model=ApiResponse[List[Dict]], tags=["Suggestions"])
async def suggest_ontology_properties(
    source_class_id: int,
    target_class_id: Optional[int] = Query(default=None, description="Target class ID"),
    domain_id: Optional[int] = Query(default=None, description="Domain ID filter"),
    max_suggestions: int = Query(default=5, ge=1, le=20, description="Maximum suggestions"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Suggest ontology properties for classes"""

    suggestions = await domain_service.suggest_ontology_properties_for_classes(
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        domain_id=domain_id,
        max_suggestions=max_suggestions,
    )

    return ApiResponse(
        data=suggestions,
        message="Ontology property suggestions retrieved successfully",
        status=200,
    )

# =============================================
# UTILITY ENDPOINTS
# =============================================

@router.get("/domains/by-name/{domain_name}/ontology-classes", response_model=ApiResponse[List[OntologyClassResponse]], tags=["Utilities"])
async def get_ontology_classes_by_domain_name(
    domain_name: str,
    primary_only: bool = Query(default=False, description="Only primary ontology classes"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get ontology classes for a specific domain by name"""

    from app.core.supabase import get_supabase

    supabase = await get_supabase()

    # Call the database function
    response = await supabase.rpc(
        "get_domain_ontology_classes", {"domain_name": domain_name}
    ).execute()

    ontology_classes = response.data

    if primary_only:
        ontology_classes = [oc for oc in ontology_classes if oc.get("is_primary")]

    return ApiResponse(
        data=[OntologyClassResponse(**oc) for oc in ontology_classes],
        message="Ontology classes retrieved successfully",
        status=200,
    )


@router.get("/domains/by-name/{domain_name}/ontology-properties", response_model=ApiResponse[List[OntologyPropertyResponse]], tags=["Utilities"])
async def get_ontology_properties_by_domain_name(
    domain_name: str,
    primary_only: bool = Query(default=False, description="Only primary ontology properties"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get ontology properties for a specific domain by name"""

    from app.core.supabase import get_supabase

    supabase = await get_supabase()

    # Call the database function
    response = await supabase.rpc(
        "get_domain_ontology_properties", {"domain_name": domain_name}
    ).execute()

    ontology_properties = response.data

    if primary_only:
        ontology_properties = [op for op in ontology_properties if op.get("is_primary")]

    return ApiResponse(
        data=[OntologyPropertyResponse(**op) for op in ontology_properties],
        message="Ontology properties retrieved successfully",
        status=200,
    )


@router.get("/compatible-ontology-properties", tags=["Utilities"])
async def get_compatible_ontology_properties(
    source_class_id: int = Query(..., description="Source ontology class ID"),
    target_class_id: Optional[int] = Query(default=None, description="Target ontology class ID"),
    domain_ids: Optional[List[int]] = Query(default=None, description="Filter by domain IDs"),
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get ontology properties compatible with given classes"""

    # Search ontology properties that allow the given source/target classes
    filters = {
        "domain_class_id": source_class_id,
        "domain_ids": domain_ids,
        "limit": 100,
    }

    if target_class_id:
        filters["range_class_id"] = target_class_id

    compatible_properties = await domain_service.search_ontology_properties(**filters)

    return {
        "source_class_id": source_class_id,
        "target_class_id": target_class_id,
        "compatible_properties": compatible_properties["ontology_properties"],
    }

# =============================================
# BULK OPERATIONS
# =============================================

@router.post("/bulk/ontology-classes/associate", response_model=BulkOperationResponse, tags=["Bulk Operations"])
async def bulk_associate_ontology_classes(
    request: BulkOntologyClassAssociationRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Bulk associate ontology classes with domain"""

    # Check admin permissions for bulk operations
    user_roles = current_user.get("roles", [])
    if not any(role in ["admin", "editor"] for role in user_roles):
        raise HTTPException(
            status_code=403, detail="Admin or Editor role required for bulk operations"
        )

    result = await domain_service.bulk_associate_ontology_classes(
        ontology_class_ids=request.ontology_classes,
        domain_id=request.domain_id,
        is_primary=request.is_primary,
        config=request.config,
        user_id=current_user["id"],
    )

    return result


@router.post("/bulk/ontology-properties/associate", response_model=BulkOperationResponse, tags=["Bulk Operations"])
async def bulk_associate_ontology_properties(
    request: BulkOntologyPropertyAssociationRequest,
    current_user: dict = Depends(RequireKGEdit),
    domain_service: DomainService = Depends(),
):
    """Bulk associate ontology properties with domain"""

    # Check admin permissions for bulk operations
    user_roles = current_user.get("roles", [])
    if not any(role in ["admin", "editor"] for role in user_roles):
        raise HTTPException(
            status_code=403, detail="Admin or Editor role required for bulk operations"
        )

    result = await domain_service.bulk_associate_ontology_properties(
        ontology_property_ids=request.ontology_properties,
        domain_id=request.domain_id,
        is_primary=request.is_primary,
        config=request.config,
        user_id=current_user["id"],
    )

    return result

# =============================================
# ANALYTICS ENDPOINTS
# =============================================

@router.get("/analytics/overview", response_model=Dict[str, Any], tags=["Analytics"])
async def get_domain_analytics_overview(
    current_user: dict = Depends(RequireKGRead),
    domain_service: DomainService = Depends(),
):
    """Get domain system analytics overview"""

    analytics = await domain_service.get_domain_analytics_overview()
    return analytics
