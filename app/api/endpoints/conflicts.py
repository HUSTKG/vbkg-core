from typing import Annotated, Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi import status as HttpStatus
from pydantic import parse_obj_as

from app.api.deps import PermissionChecker, get_current_user
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.entity import EntityConflict, EntityResolution
from app.services.entity_resolution import (batch_detect_conflicts,
                                            create_entity_conflict,
                                            delete_entity,
                                            find_entity_conflicts,
                                            get_conflict_statistics,
                                            get_entity_conflicts,
                                            merge_entities,
                                            resolve_entity_conflict)

router = APIRouter()

check_read_permission = PermissionChecker("conflict:read")
check_write_permission = PermissionChecker("conflict:write")


@router.get("/", response_model=PaginatedResponse[EntityConflict])
async def list_conflicts(
    status: Optional[str] = Query(
        None, description="Filter by conflict status (pending/resolved/ignored)"
    ),
    conflict_type: Optional[str] = Query(None, description="Filter by conflict type"),
    entity_id: Optional[UUID] = Query(None, description="Filter by entity ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[EntityConflict]:
    """
    List entity conflicts with filtering options.
    """
    conflicts = await get_entity_conflicts(
        status=status,
        conflict_type=conflict_type,
        entity_id=entity_id,
        limit=limit,
        skip=skip,
    )

    return PaginatedResponse(
        data=[EntityConflict(**conflict) for conflict in conflicts.data],
        meta=PaginatedMeta(
            skip=skip,
            limit=limit,
            total=conflicts.count if conflicts.count else 0,  # In a real implementation, you'd want to get the total count
        ),
        message="Conflicts retrieved successfully",
        status=HttpStatus.HTTP_200_OK,
    )


@router.get("/statistics", response_model=ApiResponse[Dict[str, Any]])
async def get_statistics(
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Get statistics about entity conflicts.
    """
    stats = await get_conflict_statistics()

    return ApiResponse(
        data=stats,
        message="Conflict statistics retrieved successfully",
        status=HttpStatus.HTTP_200_OK,
    )


@router.post("/detect", response_model=ApiResponse[Dict[str, Any]])
async def detect_conflicts(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    threshold: float = Query(0.8, ge=0.0, le=1.0, description="Similarity threshold"),
    batch_size: int = Query(
        100, ge=1, le=1000, description="Number of entities to process"
    ),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Run batch conflict detection for entities.
    """
    result = await batch_detect_conflicts(
        entity_type=entity_type, threshold=threshold, batch_size=batch_size
    )

    return ApiResponse(
        data=result,
        message="Conflict detection completed successfully",
        status=HttpStatus.HTTP_200_OK,
    )


@router.get("/{entity_id}/potential", response_model=ApiResponse[List[Dict[str, Any]]])
async def find_potential_conflicts(
    entity_id: UUID = Path(..., description="Entity ID to check for conflicts"),
    threshold: float = Query(0.8, ge=0.0, le=1.0, description="Similarity threshold"),
    max_conflicts: int = Query(
        5, ge=1, le=100, description="Maximum number of conflicts to return"
    ),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[List[Dict[str, Any]]]:
    """
    Find potential conflicts for a specific entity.
    """
    conflicts = await find_entity_conflicts(
        entity_id=entity_id, threshold=threshold, max_conflicts=max_conflicts
    )

    return ApiResponse(
        data=conflicts,
        message="Potential conflicts found successfully",
        status=HttpStatus.HTTP_200_OK,
    )


@router.post("/{conflict_id}/resolve", response_model=ApiResponse[EntityConflict])
async def resolve_conflict(
    resolution: EntityResolution,
    conflict_id: UUID = Path(..., description="Conflict ID to resolve"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[EntityConflict]:
    """
    Resolve an entity conflict.
    """
    result = await resolve_entity_conflict(
        conflict_id=conflict_id,
        resolution=resolution,
        resolved_by=UUID(current_user["id"]),
    )

    if not result:
        raise HTTPException(
            status_code=HttpStatus.HTTP_404_NOT_FOUND,
            detail="Conflict not found or could not be resolved",
        )

    return ApiResponse(
        data=result,
        message="Conflict resolved successfully",
        status=HttpStatus.HTTP_200_OK,
    )


@router.post("/merge", response_model=ApiResponse[Dict[str, Any]])
async def merge_entity_pair(
    entity1_id: UUID = Query(..., description="First entity ID"),
    entity2_id: UUID = Query(..., description="Second entity ID"),
    keep_id: Optional[UUID] = Query(
        None, description="ID of the entity to keep (optional)"
    ),
    properties: Optional[Dict[str, Any]] = None,
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Merge two entities into one.
    """
    result = await merge_entities(
        entity1_id=entity1_id,
        entity2_id=entity2_id,
        keep_id=keep_id,
        merged_properties=properties,
    )

    if not result:
        raise HTTPException(
            status_code=HttpStatus.HTTP_404_NOT_FOUND,
            detail="One or both entities not found or could not be merged",
        )

    return ApiResponse(
        data=result,
        message="Entities merged successfully",
        status=HttpStatus.HTTP_200_OK,
    )


@router.delete("/{entity_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_entity_endpoint(
    entity_id: UUID = Path(..., description="Entity ID to delete"),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete an entity.
    """
    success = await delete_entity(entity_id=entity_id)

    if not success:
        raise HTTPException(
            status_code=HttpStatus.HTTP_404_NOT_FOUND,
            detail="Entity not found or could not be deleted",
        )

    return ApiResponse(
        data={"success": True},
        message="Entity deleted successfully",
        status=HttpStatus.HTTP_200_OK,
    )
