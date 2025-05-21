from typing import Annotated, Any, Dict, Optional

from fastapi import APIRouter, Depends, Path
from fastapi import status as HttpStatus

from app.api.deps import PermissionChecker
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.datasource import (DataSource, DataSourceCreate,
                                    DataSourceUpdate, SourceType)
from app.services.datasource import DataSourceService

router = APIRouter()

check_read_permission = PermissionChecker("datasource:read")
check_write_permission = PermissionChecker("datasource:write")


@router.post(
    "", response_model=ApiResponse[DataSource], status_code=HttpStatus.HTTP_201_CREATED
)
async def create_datasource(
    datasource_in: DataSourceCreate,
    current_user: Annotated[Dict[str, Any], Depends(check_write_permission)],
) -> ApiResponse[DataSource]:
    """
    Create new data source.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.create_datasource(
        datasource_in=datasource_in, user_id=current_user["id"]
    )
    return ApiResponse(
        data=DataSource(**response),
        status=HttpStatus.HTTP_201_CREATED,
        message="Data source created successfully",
    )


@router.get("", response_model=PaginatedResponse[Dict[str, Any]])
async def read_datasources(
    skip: int = 0,
    limit: int = 100,
    source_type: Optional[SourceType] = None,
    is_active: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> PaginatedResponse[Dict[str, Any]]:
    """
    Retrieve data sources with filtering options.
    """

    datasource_service = DataSourceService()

    response = await datasource_service.get_datasources(
        skip=skip,
        limit=limit,
        source_type=source_type.value if source_type else None,
        is_active=is_active,
    )

    return PaginatedResponse(
        data=response.data,
        meta=PaginatedMeta(
            total=response.count if response.count else 0,
            skip=skip,
            limit=limit,
        ),
        message="Data sources retrieved successfully",
        status=HttpStatus.HTTP_200_OK,
    )


@router.get("/{datasource_id}", response_model=ApiResponse[DataSource])
async def read_datasource(
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_read_permission),
) -> ApiResponse[DataSource]:
    """
    Get specific data source by ID.
    """
    datasource_service = DataSourceService()

    response = await datasource_service.get_datasource(datasource_id=datasource_id)

    return ApiResponse(
        data=DataSource(**response),
        status=HttpStatus.HTTP_200_OK,
        message="Data source retrieved successfully",
    )


@router.patch("/{datasource_id}", response_model=ApiResponse[DataSource])
async def update_datasource(
    datasource_in: DataSourceUpdate,
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[DataSource]:
    """
    Update a data source.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.update_datasource(
        datasource_id=datasource_id, datasource_in=datasource_in
    )
    return ApiResponse(
        data=DataSource(**response),
        status=HttpStatus.HTTP_200_OK,
        message="Data source updated successfully",
    )


@router.delete("/{datasource_id}", response_model=ApiResponse[Dict[str, Any]])
async def delete_datasource(
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(check_write_permission),
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete a data source.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.delete_datasource(datasource_id=datasource_id)

    return ApiResponse(
        data=response,
        status=HttpStatus.HTTP_200_OK,
        message="Data source deleted successfully",
    )
