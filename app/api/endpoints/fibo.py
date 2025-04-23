# app/api/endpoints/fibo.py
from typing import Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, PermissionChecker 
from app.schemas.api import ApiResponse, PaginatedResponse
from app.services.fibo import FIBOService
from app.schemas.fibo import (
    FIBOClass, 
    FIBOClassCreate, 
    FIBOClassUpdate,
    FIBOPropertyUpdate,
    EntityMapping,
    FIBOProperty,
    FIBOPropertyCreate,
    RelationshipMapping,
    OntologyImportRequest,
    OntologyImportResponse
)

router = APIRouter()

check_read_permission = PermissionChecker("knowledge:read")
check_write_permission = PermissionChecker("knowledge:write")


@router.get("/classes", response_model=PaginatedResponse[FIBOClass])
async def read_fibo_classes(
    domain: Optional[str] = None,
    search: Optional[str] = None,
    is_custom: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> PaginatedResponse[FIBOClass]:
    """
    Retrieve FIBO classes with filtering options.
    """
    fibo_service = FIBOService()
    response = await fibo_service.get_fibo_classes(
        domain=domain,
        search=search,
        is_custom=is_custom,
        limit=limit,
        skip=skip
    )
    return PaginatedResponse(
        data=response.data,
        meta={
            "total": response.count,
            "limit": limit,
            "skip": skip,
        },
        message="FIBO classes retrieved successfully"
    )


@router.get("/classes/{class_id}", response_model=ApiResponse[FIBOClass])
async def read_fibo_class(
    class_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[FIBOClass]:
    """
    Get a specific FIBO class by ID.
    """
    fibo_service = FIBOService()
    response = await fibo_service.get_fibo_class(class_id=class_id)

    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="FIBO class retrieved successfully"
    )

@router.post("/classes", response_model=ApiResponse[FIBOClass], status_code=status.HTTP_201_CREATED)
async def create_fibo_class(
    fibo_class_in: FIBOClassCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[FIBOClass]:
    """
    Create a new FIBO class.
    """
    fibo_service = FIBOService()
    response = await fibo_service.create_fibo_class(fibo_class_in=fibo_class_in)
    return ApiResponse(
        data=response,
        status=status.HTTP_201_CREATED,
        message="FIBO class created successfully"
    )


@router.patch("/classes/{class_id}", response_model=ApiResponse[FIBOClass])
async def update_fibo_class(
    fibo_class_in: FIBOClassUpdate,
    class_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[FIBOClass]:
    """
    Update a FIBO class.
    """
    fibo_service = FIBOService()
    response = await fibo_service.update_fibo_class(
        class_id=class_id,
        fibo_class_in=fibo_class_in
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="FIBO class updated successfully"
    )


@router.delete("/classes/{class_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_fibo_class(
    class_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete a FIBO class.
    """
    fibo_service = FIBOService()
    response = await fibo_service.delete_fibo_class(class_id=class_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="FIBO class deleted successfully"
    )


@router.get("/properties", response_model=PaginatedResponse[FIBOProperty])
async def read_fibo_properties(
    domain_class_id: Optional[int] = None,
    property_type: Optional[str] = Query(None, enum=["object", "datatype"]),
    search: Optional[str] = None,
    is_custom: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> PaginatedResponse[FIBOProperty]:
    """
    Retrieve FIBO properties with filtering options.
    """
    fibo_service = FIBOService()
    resposne = await fibo_service.get_fibo_properties(
        domain_class_id=domain_class_id,
        property_type=property_type,
        search=search,
        is_custom=is_custom,
        limit=limit,
        skip=skip
    )
    return PaginatedResponse(
        data=resposne.data,
        meta={
            "total": resposne.count,
            "limit": limit,
            "skip": skip,
        },
        message="FIBO properties retrieved successfully"
    )


@router.get("/properties/{property_id}", response_model=ApiResponse[FIBOProperty])
async def read_fibo_property(
    property_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[FIBOProperty]:
    """
    Get a specific FIBO property by ID.
    """
    fibo_service = FIBOService()
    response = await fibo_service.get_fibo_property(property_id=property_id)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="FIBO property retrieved successfully"
    )


@router.post("/properties", response_model=ApiResponse[FIBOProperty], status_code=status.HTTP_201_CREATED)
async def create_fibo_property(
    fibo_property_in: FIBOPropertyCreate,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[FIBOProperty]:
    """
    Create a new FIBO property.
    """
    fibo_service = FIBOService()
    response = await fibo_service.create_fibo_property(fibo_property_in=fibo_property_in)
    return ApiResponse(
        data=response,
        status=status.HTTP_201_CREATED,
        message="FIBO property created successfully"
    )


@router.patch("/properties/{property_id}", response_model=FIBOProperty)
async def update_fibo_property(
    fibo_property_in: FIBOPropertyUpdate,
    property_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Update a FIBO property.
    """
    fibo_service = FIBOService()
    return await fibo_service.update_fibo_property(
        property_id=property_id,
        fibo_property_in=fibo_property_in
    )


@router.delete("/properties/{property_id}", response_model=Dict[str, Any])
async def delete_fibo_property(
    property_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Delete a FIBO property.
    """
    fibo_service = FIBOService()
    return await fibo_service.delete_fibo_property(property_id=property_id)


@router.post("/import", response_model=ApiResponse[OntologyImportResponse])
async def import_ontology(
    import_request: OntologyImportRequest,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[OntologyImportResponse]:
    """
    Import FIBO ontology from a file or URL.
    """
    fibo_service = FIBOService()
    
    if import_request.file_id:
        response = await fibo_service.import_ontology_from_file(file_id=import_request.file_id)
        return ApiResponse(
            data=response,
            status=status.HTTP_200_OK,
            message="FIBO ontology imported successfully"
        )

    elif import_request.url:
        response = await fibo_service.import_ontology_from_url(
            url=import_request.url,
            format=import_request.format
        )
        return ApiResponse(
            data=response,
            status=status.HTTP_200_OK,
            message="FIBO ontology imported successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file_id or url must be provided"
        )


@router.get("/entity-mappings", response_model=PaginatedResponse[EntityMapping])
async def read_entity_mappings(
    verified_only: bool = False,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> PaginatedResponse[EntityMapping]:
    """
    Retrieve entity mappings.
    """
    fibo_service = FIBOService()
    response = await fibo_service.get_entity_mappings(
        verified_only=verified_only,
        limit=limit,
        skip=skip
    )

    return PaginatedResponse(
        data=response.data,
        meta={
            "total": response.count,
            "limit": limit,
            "skip": skip,
        },
        message="Entity mappings retrieved successfully"
    )


@router.post("/entity-mappings", response_model=Dict[str, Any])
async def create_entity_mapping(
    mapping: EntityMapping,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> Any:
    """
    Create or update an entity mapping.
    """
    fibo_service = FIBOService()
    return await fibo_service.create_entity_mapping(
        mapping=mapping,
        user_id=current_user["id"]
    )


@router.delete("/entity-mappings/{entity_type}", response_model=ApiResponse[Dict[str, Any]])
async def delete_entity_mapping(
    entity_type: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete an entity mapping.
    """
    fibo_service = FIBOService()
    response = await fibo_service.delete_entity_mapping(entity_type=entity_type)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entity mapping deleted successfully"
    )


@router.post("/entity-mappings/{entity_type}/verify", response_model=ApiResponse[Dict[str, Any]])
async def verify_entity_mapping(
    entity_type: str = Path(...),
    verified: bool = True,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[Dict[str, Any]]:
    """
    Verify an entity mapping.
    """
    fibo_service = FIBOService()
    response = await fibo_service.verify_entity_mapping(
        entity_type=entity_type,
        verified=verified,
        user_id=current_user["id"]
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Entity mapping verified successfully"
    )


@router.get("/relationship-mappings", response_model=PaginatedResponse[RelationshipMapping])
async def read_relationship_mappings(
    verified_only: bool = False,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> PaginatedResponse[RelationshipMapping]:
    """
    Retrieve relationship mappings.
    """
    fibo_service = FIBOService()
    response = await fibo_service.get_relationship_mappings(
        verified_only=verified_only,
        limit=limit,
        skip=skip
    )
    return PaginatedResponse(
        data=response.data,
        meta={
            "total": response.count,
            "limit": limit,
            "skip": skip,
        },
        message="Relationship mappings retrieved successfully"
    )


@router.post("/relationship-mappings", response_model=ApiResponse[RelationshipMapping])
async def create_relationship_mapping(
    mapping: RelationshipMapping,
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[RelationshipMapping]:
    """
    Create or update a relationship mapping.
    """
    fibo_service = FIBOService()
    response = await fibo_service.create_relationship_mapping(
        mapping=mapping,
        user_id=current_user["id"]
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_201_CREATED,
        message="Relationship mapping created successfully"
    )


@router.delete("/relationship-mappings/{relationship_type}", response_model=ApiResponse[Dict[str, Any]])
async def delete_relationship_mapping(
    relationship_type: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission)
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete a relationship mapping.
    """
    fibo_service = FIBOService()
    response = await fibo_service.delete_relationship_mapping(relationship_type=relationship_type)
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Relationship mapping deleted successfully"
    )


@router.post("/relationship-mappings/{relationship_type}/verify", response_model=ApiResponse[Dict[str, Any]])
async def verify_relationship_mapping(
    relationship_type: str = Path(...),
    verified: bool = True,
    current_user: ApiResponse[Dict[str, Any]] = Depends(check_write_permission)
) -> Any:
    """
    Verify a relationship mapping.
    """
    fibo_service = FIBOService()
    response = await fibo_service.verify_relationship_mapping(
        relationship_type=relationship_type,
        verified=verified,
        user_id=current_user["id"]
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="Relationship mapping verified successfully"
    )


@router.get("/suggest/classes", response_model=ApiResponse[List[FIBOClass]])
async def suggest_fibo_classes(
    entity_text: str,
    entity_type: str,
    max_suggestions: int = Query(5, ge=1, le=20),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[List[FIBOClass]]:
    """
    Suggest FIBO classes for an entity.
    """
    fibo_service = FIBOService()
    response = await fibo_service.suggest_fibo_class_for_entity(
        entity_text=entity_text,
        entity_type=entity_type,
        max_suggestions=max_suggestions
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="FIBO classes suggested successfully"
    )


@router.get("/suggest/properties", response_model=ApiResponse[List[FIBOProperty]])
async def suggest_fibo_properties(
    relationship_type: str,
    source_entity_type: str,
    target_entity_type: str,
    max_suggestions: int = Query(5, ge=1, le=20),
    current_user: Dict[str, Any] = Depends(check_read_permission)
) -> ApiResponse[List[FIBOProperty]]:
    """
    Suggest FIBO properties for a relationship.
    """
    fibo_service = FIBOService()
    response = await fibo_service.suggest_fibo_property_for_relationship(
        relationship_type=relationship_type,
        source_entity_type=source_entity_type,
        target_entity_type=target_entity_type,
        max_suggestions=max_suggestions
    )
    return ApiResponse(
        data=response,
        status=status.HTTP_200_OK,
        message="FIBO properties suggested successfully"
    )
