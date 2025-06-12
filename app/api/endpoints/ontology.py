from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from websockets.http11 import d

from app.api.deps import PermissionChecker, get_current_user
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.ontology import (EntityMapping, EntityMappingCreate,
                                  EntityMappingUpdate, EntityTypeSuggestion,
                                  OntologyClass, OntologyClassCreate,
                                  OntologyClassSuggestion, OntologyClassUpdate,
                                  OntologyImportRequest,
                                  OntologyImportResponse, OntologyProperty,
                                  OntologyPropertyCreate,
                                  OntologyPropertySuggestion,
                                  OntologyPropertyUpdate, RelationshipMapping,
                                  RelationshipMappingCreate,
                                  RelationshipMappingUpdate,
                                  RelationshipTypeSuggestion)
from app.services.ontology import OntologyService

router = APIRouter()

check_read_permission = PermissionChecker("kg:read")
check_write_permission = PermissionChecker("kg:edit")


@router.get("/classes", response_model=PaginatedResponse[OntologyClass])
async def read_ontology_classes(
    domain: Optional[str] = None,
    search: Optional[str] = None,
    is_custom: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[OntologyClass]:
    """Retrieve Ontology classes with filtering options."""
    ontology_service = OntologyService()
    response = await ontology_service.get_ontology_classes(
        domain=domain, search=search, is_custom=is_custom, limit=limit, skip=skip
    )
    return PaginatedResponse(
        data=[OntologyClass(**item) for item in response.data],
        meta=PaginatedMeta(
            total=response.count if response.count is not None else 0,
            limit=limit,
            skip=skip,
        ),
        message="Ontology classes retrieved successfully",
        status=status.HTTP_200_OK,
    )


@router.get("/classes/{class_id}", response_model=ApiResponse[OntologyClass])
async def read_ontology_class(
    class_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[OntologyClass]:
    """
    Get a specific Ontology class by ID.
    """
    ontology_service = OntologyService()
    response = await ontology_service.get_ontology_class(class_id=class_id)

    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Ontology class retrieved successfully",
    )


@router.post(
    "/classes",
    response_model=ApiResponse[OntologyClass],
    status_code=status.HTTP_201_CREATED,
)
async def create_ontology_class(
    ontology_class_in: OntologyClassCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[OntologyClass]:
    """
    Create a new Ontology class.
    """
    ontology_service = OntologyService()
    response = await ontology_service.create_ontology_class(ontology_class_in=ontology_class_in)
    return ApiResponse(
        data=response,
        status=status.HTTP_201_CREATED,
        message="Ontology class created successfully",
    )


@router.put("/classes/{class_id}", response_model=ApiResponse[OntologyClass])
async def update_ontology_class(
    ontology_class_in: OntologyClassUpdate,
    class_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[OntologyClass]:
    """
    Update a Ontology class.
    """
    ontology_service = OntologyService()
    response = await ontology_service.update_ontology_class(
        class_id=class_id, ontology_class_in=ontology_class_in
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Ontology class updated successfully",
    )


@router.delete("/classes/{class_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_ontology_class(
    class_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete a Ontology class.
    """
    ontology_service = OntologyService()
    response = await ontology_service.delete_ontology_class(class_id=class_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Ontology class deleted successfully",
    )


@router.get("/properties", response_model=PaginatedResponse[OntologyProperty])
async def read_ontology_properties(
    domain_class_id: Optional[int] = None,
    property_type: Optional[str] = Query(None, enum=["object", "datatype"]),
    search: Optional[str] = None,
    is_custom: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[OntologyProperty]:
    """
    Retrieve Ontology properties with filtering options.
    """
    ontology_service = OntologyService()
    response = await ontology_service.get_ontology_properties(
        domain_class_id=domain_class_id,
        property_type=property_type,
        search=search,
        is_custom=is_custom,
        limit=limit,
        skip=skip,
    )
    return PaginatedResponse(
        data=[OntologyProperty(**item) for item in response.data],
        meta=PaginatedMeta(
            total=response.count if response.count is not None else 0,
            limit=limit,
            skip=skip,
        ),
        status=status.HTTP_200_OK,
        message="Ontology properties retrieved successfully",
    )


@router.get("/properties/{property_id}", response_model=ApiResponse[OntologyProperty])
async def read_ontology_property(
    property_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[OntologyProperty]:
    """
    Get a specific Ontology property by ID.
    """
    ontology_service = OntologyService()
    response = await ontology_service.get_ontology_property(property_id=property_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Ontology property retrieved successfully",
    )


@router.post(
    "/properties",
    response_model=ApiResponse[OntologyProperty],
    status_code=status.HTTP_201_CREATED,
)
async def create_ontology_property(
    ontology_property_in: OntologyPropertyCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[OntologyProperty]:
    """
    Create a new Ontology property.
    """
    ontology_service = OntologyService()
    response = await ontology_service.create_ontology_property(
        ontology_property_in=ontology_property_in
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_201_CREATED,
        message="Ontology property created successfully",
    )


@router.patch("/properties/{property_id}", response_model=OntologyProperty)
async def update_ontology_property(
    ontology_property_in: OntologyPropertyUpdate,
    property_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> Any:
    """
    Update a Ontology property.
    """
    ontology_service = OntologyService()
    return await ontology_service.update_ontology_property(
        property_id=property_id, ontology_property_in=ontology_property_in
    )


@router.delete("/properties/{property_id}", response_model=Dict[str, Any])
async def delete_ontology_property(
    property_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> Any:
    """
    Delete a Ontology property.
    """
    ontology_service = OntologyService()
    return await ontology_service.delete_ontology_property(property_id=property_id)


@router.post("/import", response_model=ApiResponse[OntologyImportResponse])
async def import_ontology(
    import_request: OntologyImportRequest,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[OntologyImportResponse]:
    """
    Import Ontology ontology from a file or URL.
    """
    ontology_service = OntologyService()

    if import_request.file_id:
        response = await ontology_service.import_ontology_from_file(
            file_id=import_request.file_id
        )
        return ApiResponse(
            data=response,
            status=status.HTTP_200_OK,
            message="Ontology ontology imported successfully",
        )

    elif import_request.url:
        response = await ontology_service.import_ontology_from_url(
            url=import_request.url, format=import_request.format
        )
        return ApiResponse(
            data=response,
            status=status.HTTP_200_OK,
            message="Ontology ontology imported successfully",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file_id or url must be provided",
        )


@router.get("/entity-mappings", response_model=PaginatedResponse[EntityMapping])
async def read_entity_mappings(
    entity_type_id: Optional[int] = None,
    mapping_status: Optional[str] = Query(
        None, regex="^(pending|mapped|rejected|needs_review)$"
    ),
    is_verified: Optional[bool] = None,
    auto_mapped: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[EntityMapping]:
    """Retrieve entity mappings with filtering options."""
    ontology_service = OntologyService()
    response = await ontology_service.get_entity_mappings(
        entity_type_id=entity_type_id,
        mapping_status=mapping_status,
        is_verified=is_verified,
        auto_mapped=auto_mapped,
        search=search,
        limit=limit,
        skip=skip,
    )
    return PaginatedResponse(
        data=[EntityMapping(**item) for item in response.data],
        meta=PaginatedMeta(
            total=response.count if response.count is not None else 0,
            limit=limit,
            skip=skip,
        ),
        status=status.HTTP_200_OK,
        message="Entity mappings retrieved successfully",
    )


@router.post("/entity-mappings", response_model=ApiResponse[EntityMapping])
async def create_entity_mapping(
    mapping: EntityMappingCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[EntityMapping]:
    """Create or update an entity mapping."""
    ontology_service = OntologyService()
    response = await ontology_service.create_entity_mapping(
        mapping=mapping, user_id=current_user["id"]
    )
    return ApiResponse(
        data=EntityMapping(**response),
        status=status.HTTP_201_CREATED,
        message="Entity mapping created successfully",
    )


@router.patch(
    "/entity-mappings/{mapping_id}", response_model=ApiResponse[EntityMapping]
)
async def update_entity_mapping(
    mapping: EntityMappingUpdate,
    mapping_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[EntityMapping]:
    """Update an entity mapping."""
    ontology_service = OntologyService()
    response = await ontology_service.update_entity_mapping(
        mapping_id=mapping_id, mapping=mapping
    )
    return ApiResponse(
        data=EntityMapping(**response),
        status=status.HTTP_200_OK,
        message="Entity mapping updated successfully",
    )


@router.delete(
    "/entity-mappings/{mapping_id}", response_model=ApiResponse[Dict[str, Any]]
)
async def delete_entity_mapping(
    mapping_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Delete an entity mapping."""
    ontology_service = OntologyService()
    response = await ontology_service.delete_entity_mapping(mapping_id=mapping_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entity mapping deleted successfully",
    )


@router.post(
    "/entity-mappings/{mapping_id}/verify", response_model=ApiResponse[EntityMapping]
)
async def verify_entity_mapping(
    mapping_id: int = Path(...),
    verified: bool = True,
    notes: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[EntityMapping]:
    """Verify an entity mapping."""
    ontology_service = OntologyService()
    response = await ontology_service.verify_entity_mapping(
        mapping_id=mapping_id,
        verified=verified,
        user_id=current_user["id"],
        notes=notes,
    )
    return ApiResponse(
        data=EntityMapping(**response),
        status=status.HTTP_200_OK,
        message="Entity mapping verified successfully",
    )


@router.get(
    "/relationship-mappings", response_model=PaginatedResponse[RelationshipMapping]
)
async def read_relationship_mappings(
    relationship_type_id: Optional[int] = None,
    mapping_status: Optional[str] = Query(
        None, regex="^(pending|mapped|rejected|needs_review)$"
    ),
    is_verified: Optional[bool] = None,
    auto_mapped: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[RelationshipMapping]:
    """Retrieve relationship mappings with filtering options."""
    ontology_service = OntologyService()
    response = await ontology_service.get_relationship_mappings(
        relationship_type_id=relationship_type_id,
        mapping_status=mapping_status,
        is_verified=is_verified,
        auto_mapped=auto_mapped,
        search=search,
        limit=limit,
        skip=skip,
    )
    return PaginatedResponse(
        data=[RelationshipMapping(**item) for item in response.data],
        meta=PaginatedMeta(
            total=response.count if response.count is not None else 0,
            limit=limit,
            skip=skip,
        ),
        status=status.HTTP_200_OK,
        message="Relationship mappings retrieved successfully",
    )


@router.post("/relationship-mappings", response_model=ApiResponse[RelationshipMapping])
async def create_relationship_mapping(
    mapping: RelationshipMappingCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[RelationshipMapping]:
    """
    Create or update a relationship mapping.
    """
    ontology_service = OntologyService()
    response = await ontology_service.create_relationship_mapping(
        mapping=mapping, user_id=current_user["id"]
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_201_CREATED,
        message="Relationship mapping created successfully",
    )


@router.patch(
    "/relationship-mappings/{relationship_type}",
    response_model=ApiResponse[RelationshipMapping],
)
async def update_relationship_mapping(
    mapping: RelationshipMappingUpdate,
    relationship_type: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[RelationshipMapping]:
    """
    Update a relationship mapping.
    """
    ontology_service = OntologyService()
    response = await ontology_service.update_relationship_mapping(
        relationship_type=relationship_type, mapping=mapping
    )
    return ApiResponse(
        data=response,
        message="Relationship mapping updated successfully",
        status=status.HTTP_200_OK,
    )


@router.delete(
    "/relationship-mappings/{relationship_type}",
    response_model=ApiResponse[Dict[str, Any]],
)
async def delete_relationship_mapping(
    relationship_type: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete a relationship mapping.
    """
    ontology_service = OntologyService()
    response = await ontology_service.delete_relationship_mapping(
        relationship_type=relationship_type
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Relationship mapping deleted successfully",
    )


@router.post(
    "/relationship-mappings/{relationship_type}/verify",
    response_model=ApiResponse[Dict[str, Any]],
)
async def verify_relationship_mapping(
    relationship_type: str = Path(...),
    verified: bool = True,
    current_user: ApiResponse[Dict[str, Any]] = Depends(check_write_permission),
) -> Any:
    """
    Verify a relationship mapping.
    """
    ontology_service = OntologyService()
    response = await ontology_service.verify_relationship_mapping(
        relationship_type=relationship_type,
        verified=verified,
        user_id=current_user["id"],
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Relationship mapping verified successfully",
    )


@router.post("/suggest/entity-types", response_model=ApiResponse[List[EntityTypeSuggestion]])
async def suggest_entity_types(
    text: str,
    context: Optional[str] = None,
    domain_id: Optional[int] = None,
    max_suggestions: int = Query(5, ge=1, le=20),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[List[EntityTypeSuggestion]]:
    """Suggest entity types for text."""
    ontology_service = OntologyService()
    response = await ontology_service.suggest_entity_types(
        text=text,
        context=context,
        domain_id=domain_id,
        max_suggestions=max_suggestions,
    )
    return ApiResponse(
        data=[EntityTypeSuggestion(**item) for item in response],
        status=status.HTTP_200_OK,
        message="Entity types suggested successfully",
    )


@router.post("/suggest/relationship-types", response_model=ApiResponse[List[RelationshipTypeSuggestion]])
async def suggest_relationship_types(
    text: str,
    source_entity_type_id: Optional[int] = None,
    target_entity_type_id: Optional[int] = None,
    context: Optional[str] = None,
    domain_id: Optional[int] = None,
    max_suggestions: int = Query(5, ge=1, le=20),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[List[RelationshipTypeSuggestion]]:
    """Suggest relationship types for text."""
    ontology_service = OntologyService()
    response = await ontology_service.suggest_relationship_types(
        text=text,
        source_entity_type_id=source_entity_type_id,
        target_entity_type_id=target_entity_type_id,
        context=context,
        domain_id=domain_id,
        max_suggestions=max_suggestions,
    )
    return ApiResponse(
        data=[RelationshipTypeSuggestion(**item) for item in response],
        status=status.HTTP_200_OK,
        message="Relationship types suggested successfully",
    )


@router.get("/suggest/classes", response_model=ApiResponse[List[OntologyClassSuggestion]])
async def suggest_ontology_classes(
    entity_text: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_type_id: Optional[int] = None,
    context: Optional[str] = None,
    max_suggestions: int = Query(5, ge=1, le=20),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[List[OntologyClassSuggestion]]:
    """Suggest Ontology classes for an entity."""
    ontology_service = OntologyService()
    response = await ontology_service.suggest_ontology_class_for_entity(
        entity_text=entity_text or "",
        entity_type=entity_type or "",
        max_suggestions=max_suggestions,
    )
    
    # Convert to suggestion format
    suggestions = []
    for item in response:
        suggestions.append({
            "ontology_class": item,
            "confidence": 0.8,  # Default confidence
            "reason": f"Matched Ontology class: {item.get('label', item['uri'])}"
        })
    
    return ApiResponse(
        data=[OntologyClassSuggestion(**item) for item in suggestions],
        status=status.HTTP_200_OK,
        message="Ontology classes suggested successfully",
    )


@router.get("/suggest/properties", response_model=ApiResponse[List[OntologyPropertySuggestion]])
async def suggest_ontology_properties(
    relationship_type: Optional[str] = None,
    relationship_type_id: Optional[int] = None,
    source_entity_type: Optional[str] = None,
    source_entity_type_id: Optional[int] = None,
    target_entity_type: Optional[str] = None,
    target_entity_type_id: Optional[int] = None,
    context: Optional[str] = None,
    max_suggestions: int = Query(5, ge=1, le=20),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[List[OntologyPropertySuggestion]]:
    """Suggest Ontology properties for a relationship."""
    ontology_service = OntologyService()
    response = await ontology_service.suggest_ontology_property_for_relationship(
        relationship_type=relationship_type or "",
        source_entity_type=source_entity_type or "",
        target_entity_type=target_entity_type or "",
        max_suggestions=max_suggestions,
    )
    
    # Convert to suggestion format
    suggestions = []
    for item in response:
        suggestions.append({
            "ontology_property": item,
            "confidence": 0.8,  # Default confidence
            "reason": f"Matched Ontology property: {item.get('label', item['uri'])}"
        })
    
    return ApiResponse(
        data=[OntologyPropertySuggestion(**item) for item in suggestions],
        status=status.HTTP_200_OK,
        message="Ontology properties suggested successfully",
    )

# ==============================================
# BULK OPERATION ROUTES
# ==============================================

@router.post("/entity-mappings/bulk", response_model=ApiResponse[Dict[str, Any]])
async def bulk_create_entity_mappings(
    mappings: List[EntityMappingCreate],
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Bulk create entity mappings."""
    ontology_service = OntologyService()
    response = await ontology_service.bulk_create_entity_mappings(
        mappings=mappings, user_id=current_user["id"]
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entity mappings bulk created successfully",
    )


@router.post("/relationship-mappings/bulk", response_model=ApiResponse[Dict[str, Any]])
async def bulk_create_relationship_mappings(
    mappings: List[RelationshipMappingCreate],
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Bulk create relationship mappings."""
    ontology_service = OntologyService()
    response = await ontology_service.bulk_create_relationship_mappings(
        mappings=mappings, user_id=current_user["id"]
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Relationship mappings bulk created successfully",
    )

# ==============================================
# STATS ROUTES
# ==============================================

@router.get("/stats/mappings", response_model=ApiResponse[Dict[str, Any]])
async def get_mapping_stats(
    domain_id: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Get mapping statistics."""
    ontology_service = OntologyService()
    response = await ontology_service.get_mapping_stats(domain_id=domain_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Mapping statistics retrieved successfully",
    )

# ==============================================
# ONTOLOGY IMPORT ROUTE (keeping existing)
# ==============================================

@router.post("/import", response_model=ApiResponse[OntologyImportResponse])
async def import_ontology(
    import_request: OntologyImportRequest,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[OntologyImportResponse]:
    """Import Ontology ontology from a file or URL."""
    ontology_service = OntologyService()

    if import_request.file_id:
        response = await ontology_service.import_ontology_from_file(
            file_id=import_request.file_id
        )
        return ApiResponse(
            data=response,
            status=status.HTTP_200_OK,
            message="Ontology ontology imported successfully",
        )
    elif import_request.url:
        response = await ontology_service.import_ontology_from_url(
            url=import_request.url, format=import_request.format
        )
        return ApiResponse(
            data=response,
            status=status.HTTP_200_OK,
            message="Ontology ontology imported successfully",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file_id or url must be provided",
        )
