import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.deps import PermissionChecker
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.ontology import (BulkEntityMappingRequest,
                                  BulkMappingResponse,
                                  BulkRelationshipMappingRequest,
                                  EntityMapping, EntityMappingCreate,
                                  EntityMappingUpdate, MappingStatistics,
                                  OntologyClass, OntologyClassCreate,
                                  OntologyClassUpdate, OntologyImportRequest,
                                  OntologyImportResponse, OntologyProperty,
                                  OntologyPropertyCreate,
                                  OntologyPropertyUpdate, RelationshipMapping,
                                  RelationshipMappingCreate,
                                  RelationshipMappingUpdate)
from app.services.ontology import OntologyService

router = APIRouter()

check_read_permission = PermissionChecker("ontology:read")
check_write_permission = PermissionChecker("ontology:write")


# =============================================
# ONTOLOGY CLASS ROUTES
# =============================================


@router.get("/classes", response_model=PaginatedResponse[OntologyClass])
async def read_ontology_classes(
    domain_ids: Optional[List[int]] = Query(None, description="Filter by domain IDs"),
    search: Optional[str] = Query(None, description="Search in label and URI"),
    is_custom: Optional[bool] = Query(None, description="Filter by custom classes"),
    parent_class_id: Optional[int] = Query(None, description="Filter by parent class"),
    limit: int = Query(100, ge=1, le=100000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[OntologyClass]:
    """Retrieve ontology classes with filtering options."""
    ontology_service = OntologyService()
    response = await ontology_service.get_ontology_classes(
        domain_ids=domain_ids,
        search=search,
        is_custom=is_custom,
        parent_class_id=parent_class_id,
        limit=limit,
        skip=skip,
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
    class_id: int = Path(..., description="Ontology class ID"),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[OntologyClass]:
    """Get a specific ontology class by ID."""
    ontology_service = OntologyService()
    response = await ontology_service.get_ontology_class(class_id=class_id)

    return ApiResponse(
        data=OntologyClass(**response),
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
    domain_id: Optional[int] = Query(None, description="Domain to associate with"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[OntologyClass]:
    """Create a new ontology class."""
    ontology_service = OntologyService()
    response = await ontology_service.create_ontology_class(
        ontology_class_in=ontology_class_in, domain_id=domain_id
    )
    return ApiResponse(
        data=OntologyClass(**response),
        status=status.HTTP_201_CREATED,
        message="Ontology class created successfully",
    )


@router.put("/classes/{class_id}", response_model=ApiResponse[OntologyClass])
async def update_ontology_class(
    ontology_class_in: OntologyClassUpdate,
    class_id: int = Path(..., description="Ontology class ID"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[OntologyClass]:
    """Update an ontology class."""
    ontology_service = OntologyService()
    response = await ontology_service.update_ontology_class(
        class_id=class_id, ontology_class_in=ontology_class_in
    )
    return ApiResponse(
        data=OntologyClass(**response),
        status=status.HTTP_200_OK,
        message="Ontology class updated successfully",
    )


@router.delete("/classes/{class_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_ontology_class(
    class_id: int = Path(..., description="Ontology class ID"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Delete an ontology class."""
    ontology_service = OntologyService()
    response = await ontology_service.delete_ontology_class(class_id=class_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Ontology class deleted successfully",
    )


# =============================================
# ONTOLOGY PROPERTY ROUTES
# =============================================


@router.get("/properties", response_model=PaginatedResponse[OntologyProperty])
async def read_ontology_properties(
    domain_ids: Optional[List[int]] = Query(None, description="Filter by domain IDs"),
    domain_class_id: Optional[int] = Query(None, description="Filter by domain class"),
    range_class_id: Optional[int] = Query(None, description="Filter by range class"),
    property_type: Optional[str] = Query(None, enum=["object", "datatype"]),
    search: Optional[str] = Query(None, description="Search in label and URI"),
    is_custom: Optional[bool] = Query(None, description="Filter by custom properties"),
    limit: int = Query(100, ge=1, le=100000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[OntologyProperty]:
    """Retrieve ontology properties with filtering options."""
    ontology_service = OntologyService()
    response = await ontology_service.get_ontology_properties(
        domain_ids=domain_ids,
        domain_class_id=domain_class_id,
        range_class_id=range_class_id,
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
    property_id: int = Path(..., description="Ontology property ID"),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[OntologyProperty]:
    """Get a specific ontology property by ID."""
    ontology_service = OntologyService()
    response = await ontology_service.get_ontology_property(property_id=property_id)
    return ApiResponse(
        data=OntologyProperty(**response),
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
    domain_id: Optional[int] = Query(None, description="Domain to associate with"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[OntologyProperty]:
    """Create a new ontology property."""
    ontology_service = OntologyService()
    response = await ontology_service.create_ontology_property(
        ontology_property_in=ontology_property_in, domain_id=domain_id
    )
    return ApiResponse(
        data=OntologyProperty(**response),
        status=status.HTTP_201_CREATED,
        message="Ontology property created successfully",
    )


@router.put("/properties/{property_id}", response_model=ApiResponse[OntologyProperty])
async def update_ontology_property(
    ontology_property_in: OntologyPropertyUpdate,
    property_id: int = Path(..., description="Ontology property ID"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[OntologyProperty]:
    """Update an ontology property."""
    ontology_service = OntologyService()
    response = await ontology_service.update_ontology_property(
        property_id=property_id, ontology_property_in=ontology_property_in
    )
    return ApiResponse(
        data=OntologyProperty(**response),
        status=status.HTTP_200_OK,
        message="Ontology property updated successfully",
    )


@router.delete("/properties/{property_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_ontology_property(
    property_id: int = Path(..., description="Ontology property ID"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Delete an ontology property."""
    ontology_service = OntologyService()
    response = await ontology_service.delete_ontology_property(property_id=property_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Ontology property deleted successfully",
    )


# =============================================
# ENTITY MAPPING ROUTES
# =============================================


@router.get("/entity-mappings", response_model=PaginatedResponse[EntityMapping])
async def read_entity_mappings(
    ontology_class_id: Optional[int] = Query(
        None, description="Filter by ontology class"
    ),
    mapping_status: Optional[str] = Query(
        None, regex="^(pending|mapped|rejected|needs_review)$"
    ),
    is_verified: Optional[bool] = Query(
        None, description="Filter by verification status"
    ),
    auto_mapped: Optional[bool] = Query(
        None, description="Filter by auto-mapped status"
    ),
    search: Optional[str] = Query(None, description="Search in entity type and notes"),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[EntityMapping]:
    """Retrieve entity mappings with filtering options."""
    ontology_service = OntologyService()
    response = await ontology_service.get_entity_mappings(
        ontology_class_id=ontology_class_id,
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


@router.put("/entity-mappings/{mapping_id}", response_model=ApiResponse[EntityMapping])
async def update_entity_mapping(
    mapping: EntityMappingUpdate,
    mapping_id: str = Path(..., description="Entity mapping ID"),
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
    mapping_id: str = Path(..., description="Entity mapping ID"),
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
    mapping_id: str = Path(..., description="Entity mapping ID"),
    verified: bool = Query(True, description="Verification status"),
    notes: Optional[str] = Query(None, description="Verification notes"),
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


# =============================================
# RELATIONSHIP MAPPING ROUTES
# =============================================


@router.get(
    "/relationship-mappings", response_model=PaginatedResponse[RelationshipMapping]
)
async def read_relationship_mappings(
    ontology_property_id: Optional[int] = Query(
        None, description="Filter by ontology property"
    ),
    mapping_status: Optional[str] = Query(
        None, regex="^(pending|mapped|rejected|needs_review)$"
    ),
    is_verified: Optional[bool] = Query(
        None, description="Filter by verification status"
    ),
    auto_mapped: Optional[bool] = Query(
        None, description="Filter by auto-mapped status"
    ),
    search: Optional[str] = Query(
        None, description="Search in relationship type and notes"
    ),
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[RelationshipMapping]:
    """Retrieve relationship mappings with filtering options."""
    ontology_service = OntologyService()
    response = await ontology_service.get_relationship_mappings(
        ontology_property_id=ontology_property_id,
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
    """Create or update a relationship mapping."""
    ontology_service = OntologyService()
    response = await ontology_service.create_relationship_mapping(
        mapping=mapping, user_id=current_user["id"]
    )
    return ApiResponse(
        data=RelationshipMapping(**response),
        status=status.HTTP_201_CREATED,
        message="Relationship mapping created successfully",
    )


@router.put(
    "/relationship-mappings/{mapping_id}",
    response_model=ApiResponse[RelationshipMapping],
)
async def update_relationship_mapping(
    mapping: RelationshipMappingUpdate,
    mapping_id: str = Path(..., description="Relationship mapping ID"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[RelationshipMapping]:
    """Update a relationship mapping."""
    ontology_service = OntologyService()
    response = await ontology_service.update_relationship_mapping(
        mapping_id=mapping_id, mapping=mapping
    )
    return ApiResponse(
        data=RelationshipMapping(**response),
        message="Relationship mapping updated successfully",
        status=status.HTTP_200_OK,
    )


@router.delete(
    "/relationship-mappings/{mapping_id}", response_model=ApiResponse[Dict[str, Any]]
)
async def delete_relationship_mapping(
    mapping_id: str = Path(..., description="Relationship mapping ID"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """Delete a relationship mapping."""
    ontology_service = OntologyService()
    response = await ontology_service.delete_relationship_mapping(mapping_id=mapping_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Relationship mapping deleted successfully",
    )


@router.post(
    "/relationship-mappings/{mapping_id}/verify",
    response_model=ApiResponse[RelationshipMapping],
)
async def verify_relationship_mapping(
    mapping_id: str = Path(..., description="Relationship mapping ID"),
    verified: bool = Query(True, description="Verification status"),
    notes: Optional[str] = Query(None, description="Verification notes"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[RelationshipMapping]:
    """Verify a relationship mapping."""
    ontology_service = OntologyService()
    response = await ontology_service.verify_relationship_mapping(
        mapping_id=mapping_id,
        verified=verified,
        user_id=current_user["id"],
        notes=notes,
    )
    return ApiResponse(
        data=RelationshipMapping(**response),
        status=status.HTTP_200_OK,
        message="Relationship mapping verified successfully",
    )


# =============================================
# BULK OPERATION ROUTES
# =============================================


@router.post("/entity-mappings/bulk", response_model=ApiResponse[BulkMappingResponse])
async def bulk_create_entity_mappings(
    request: BulkEntityMappingRequest,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[BulkMappingResponse]:
    """Bulk create entity mappings."""
    ontology_service = OntologyService()
    response = await ontology_service.bulk_create_entity_mappings(
        mappings=request.mappings, user_id=current_user["id"]
    )
    return ApiResponse(
        data=BulkMappingResponse(**response),
        status=status.HTTP_200_OK,
        message="Entity mappings bulk created successfully",
    )


@router.post(
    "/relationship-mappings/bulk", response_model=ApiResponse[BulkMappingResponse]
)
async def bulk_create_relationship_mappings(
    request: BulkRelationshipMappingRequest,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[BulkMappingResponse]:
    """Bulk create relationship mappings."""
    ontology_service = OntologyService()
    response = await ontology_service.bulk_create_relationship_mappings(
        mappings=request.mappings, user_id=current_user["id"]
    )
    return ApiResponse(
        data=BulkMappingResponse(**response),
        status=status.HTTP_200_OK,
        message="Relationship mappings bulk created successfully",
    )


@router.get("/stats/mappings", response_model=ApiResponse[MappingStatistics])
async def get_mapping_statistics(
    domain_ids: Optional[List[int]] = Query(None, description="Filter by domain IDs"),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[MappingStatistics]:
    """Get mapping statistics."""
    ontology_service = OntologyService()
    response = await ontology_service.get_mapping_stats(domain_ids=domain_ids)
    return ApiResponse(
        data=MappingStatistics(**response),
        status=status.HTTP_200_OK,
        message="Mapping statistics retrieved successfully",
    )


# =============================================
# IMPORT AND EXPORT ROUTES
# =============================================


@router.post("/import", response_model=ApiResponse[OntologyImportResponse])
async def import_ontology(
    import_request: OntologyImportRequest,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[OntologyImportResponse]:
    """Import ontology from a file or URL."""
    ontology_service = OntologyService()

    if import_request.file_id:
        response = await ontology_service.import_ontology_from_file(
            file_id=import_request.file_id,
            target_domain_id=import_request.target_domain_id,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file_id or url must be provided",
        )

    return ApiResponse(
        data=OntologyImportResponse(**response),
        status=status.HTTP_200_OK,
        message="Ontology imported successfully",
    )


@router.post(
    "/entity-mappings/{mapping_id}/apply-suggestion",
    response_model=ApiResponse[EntityMapping],
)
async def apply_entity_mapping_suggestion(
    mapping_id: str = Path(..., description="Entity mapping ID"),
    suggestion_index: int = Query(
        ..., description="Index of suggestion to apply", ge=0
    ),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[EntityMapping]:
    """Apply AI suggestion for entity mapping."""
    ontology_service = OntologyService()
    response = await ontology_service.apply_entity_mapping_suggestion(
        mapping_id=mapping_id,
        suggestion_index=suggestion_index,
        user_id=current_user["id"],
    )
    return ApiResponse(
        data=EntityMapping(**response),
        status=status.HTTP_200_OK,
        message="Entity mapping suggestion applied successfully",
    )


@router.post(
    "/relationship-mappings/{mapping_id}/apply-suggestion",
    response_model=ApiResponse[RelationshipMapping],
)
async def apply_relationship_mapping_suggestion(
    mapping_id: str = Path(..., description="Relationship mapping ID"),
    suggestion_index: int = Query(
        ..., description="Index of suggestion to apply", ge=0
    ),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[RelationshipMapping]:
    """Apply AI suggestion for relationship mapping."""
    ontology_service = OntologyService()
    response = await ontology_service.apply_relationship_mapping_suggestion(
        mapping_id=mapping_id,
        suggestion_index=suggestion_index,
        user_id=current_user["id"],
    )
    return ApiResponse(
        data=RelationshipMapping(**response),
        status=status.HTTP_200_OK,
        message="Relationship mapping suggestion applied successfully",
    )
