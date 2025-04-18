# app/api/endpoints/fibo.py
from typing import Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, check_permission
from app.services.fibo import FIBOService
from app.schemas.fibo import (
    FIBOClass, 
    FIBOClassCreate, 
    FIBOClassUpdate,
    FIBOProperty,
    FIBOPropertyCreate,
    FIBOPropertyUpdate,
    EntityMapping,
    RelationshipMapping,
    OntologyImportRequest,
    OntologyImportResponse
)

router = APIRouter()


@router.get("/classes", response_model=List[FIBOClass])
async def read_fibo_classes(
    domain: Optional[str] = None,
    search: Optional[str] = None,
    is_custom: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:read"))
) -> Any:
    """
    Retrieve FIBO classes with filtering options.
    """
    fibo_service = FIBOService()
    return await fibo_service.get_fibo_classes(
        domain=domain,
        search=search,
        is_custom=is_custom,
        limit=limit,
        offset=offset
    )


@router.get("/classes/{class_id}", response_model=FIBOClass)
async def read_fibo_class(
    class_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:read"))
) -> Any:
    """
    Get a specific FIBO class by ID.
    """
    fibo_service = FIBOService()
    return await fibo_service.get_fibo_class(class_id=class_id)


@router.post("/classes", response_model=FIBOClass, status_code=status.HTTP_201_CREATED)
async def create_fibo_class(
    fibo_class_in: FIBOClassCreate,
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Create a new FIBO class.
    """
    fibo_service = FIBOService()
    return await fibo_service.create_fibo_class(fibo_class_in=fibo_class_in)


@router.patch("/classes/{class_id}", response_model=FIBOClass)
async def update_fibo_class(
    fibo_class_in: FIBOClassUpdate,
    class_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Update a FIBO class.
    """
    fibo_service = FIBOService()
    return await fibo_service.update_fibo_class(
        class_id=class_id,
        fibo_class_in=fibo_class_in
    )


@router.delete("/classes/{class_id}", response_model=Dict[str, Any])
async def delete_fibo_class(
    class_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Delete a FIBO class.
    """
    fibo_service = FIBOService()
    return await fibo_service.delete_fibo_class(class_id=class_id)


@router.get("/properties", response_model=List[FIBOProperty])
async def read_fibo_properties(
    domain_class_id: Optional[int] = None,
    property_type: Optional[str] = Query(None, enum=["object", "datatype"]),
    search: Optional[str] = None,
    is_custom: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:read"))
) -> Any:
    """
    Retrieve FIBO properties with filtering options.
    """
    fibo_service = FIBOService()
    return await fibo_service.get_fibo_properties(
        domain_class_id=domain_class_id,
        property_type=property_type,
        search=search,
        is_custom=is_custom,
        limit=limit,
        offset=offset
    )


@router.get("/properties/{property_id}", response_model=FIBOProperty)
async def read_fibo_property(
    property_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:read"))
) -> Any:
    """
    Get a specific FIBO property by ID.
    """
    fibo_service = FIBOService()
    return await fibo_service.get_fibo_property(property_id=property_id)


@router.post("/properties", response_model=FIBOProperty, status_code=status.HTTP_201_CREATED)
async def create_fibo_property(
    fibo_property_in: FIBOPropertyCreate,
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Create a new FIBO property.
    """
    fibo_service = FIBOService()
    return await fibo_service.create_fibo_property(fibo_property_in=fibo_property_in)


@router.patch("/properties/{property_id}", response_model=FIBOProperty)
async def update_fibo_property(
    fibo_property_in: FIBOPropertyUpdate,
    property_id: int = Path(...),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
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
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Delete a FIBO property.
    """
    fibo_service = FIBOService()
    return await fibo_service.delete_fibo_property(property_id=property_id)


@router.post("/import", response_model=OntologyImportResponse)
async def import_ontology(
    import_request: OntologyImportRequest,
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Import FIBO ontology from a file or URL.
    """
    fibo_service = FIBOService()
    
    if import_request.file_id:
        return await fibo_service.import_ontology_from_file(file_id=import_request.file_id)
    elif import_request.url:
        return await fibo_service.import_ontology_from_url(
            url=import_request.url,
            format=import_request.format
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file_id or url must be provided"
        )


@router.get("/entity-mappings", response_model=List[Dict[str, Any]])
async def read_entity_mappings(
    verified_only: bool = False,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:read"))
) -> Any:
    """
    Retrieve entity mappings.
    """
    fibo_service = FIBOService()
    return await fibo_service.get_entity_mappings(
        verified_only=verified_only,
        limit=limit,
        offset=offset
    )


@router.post("/entity-mappings", response_model=Dict[str, Any])
async def create_entity_mapping(
    mapping: EntityMapping,
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Create or update an entity mapping.
    """
    fibo_service = FIBOService()
    return await fibo_service.create_entity_mapping(
        mapping=mapping,
        user_id=current_user["id"]
    )


@router.delete("/entity-mappings/{entity_type}", response_model=Dict[str, Any])
async def delete_entity_mapping(
    entity_type: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Delete an entity mapping.
    """
    fibo_service = FIBOService()
    return await fibo_service.delete_entity_mapping(entity_type=entity_type)


@router.post("/entity-mappings/{entity_type}/verify", response_model=Dict[str, Any])
async def verify_entity_mapping(
    entity_type: str = Path(...),
    verified: bool = True,
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Verify an entity mapping.
    """
    fibo_service = FIBOService()
    return await fibo_service.verify_entity_mapping(
        entity_type=entity_type,
        verified=verified,
        user_id=current_user["id"]
    )


@router.get("/relationship-mappings", response_model=List[Dict[str, Any]])
async def read_relationship_mappings(
    verified_only: bool = False,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:read"))
) -> Any:
    """
    Retrieve relationship mappings.
    """
    fibo_service = FIBOService()
    return await fibo_service.get_relationship_mappings(
        verified_only=verified_only,
        limit=limit,
        offset=offset
    )


@router.post("/relationship-mappings", response_model=Dict[str, Any])
async def create_relationship_mapping(
    mapping: RelationshipMapping,
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Create or update a relationship mapping.
    """
    fibo_service = FIBOService()
    return await fibo_service.create_relationship_mapping(
        mapping=mapping,
        user_id=current_user["id"]
    )


@router.delete("/relationship-mappings/{relationship_type}", response_model=Dict[str, Any])
async def delete_relationship_mapping(
    relationship_type: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Delete a relationship mapping.
    """
    fibo_service = FIBOService()
    return await fibo_service.delete_relationship_mapping(relationship_type=relationship_type)


@router.post("/relationship-mappings/{relationship_type}/verify", response_model=Dict[str, Any])
async def verify_relationship_mapping(
    relationship_type: str = Path(...),
    verified: bool = True,
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Verify a relationship mapping.
    """
    fibo_service = FIBOService()
    return await fibo_service.verify_relationship_mapping(
        relationship_type=relationship_type,
        verified=verified,
        user_id=current_user["id"]
    )


@router.get("/suggest/classes", response_model=List[FIBOClass])
async def suggest_fibo_classes(
    entity_text: str,
    entity_type: str,
    max_suggestions: int = Query(5, ge=1, le=20),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:read"))
) -> Any:
    """
    Suggest FIBO classes for an entity.
    """
    fibo_service = FIBOService()
    return await fibo_service.suggest_fibo_class_for_entity(
        entity_text=entity_text,
        entity_type=entity_type,
        max_suggestions=max_suggestions
    )


@router.get("/suggest/properties", response_model=List[FIBOProperty])
async def suggest_fibo_properties(
    relationship_type: str,
    source_entity_type: str,
    target_entity_type: str,
    max_suggestions: int = Query(5, ge=1, le=20),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:read"))
) -> Any:
    """
    Suggest FIBO properties for a relationship.
    """
    fibo_service = FIBOService()
    return await fibo_service.suggest_fibo_property_for_relationship(
        relationship_type=relationship_type,
        source_entity_type=source_entity_type,
        target_entity_type=target_entity_type,
        max_suggestions=max_suggestions
    )
