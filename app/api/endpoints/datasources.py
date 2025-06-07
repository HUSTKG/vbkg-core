from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi import status as HttpStatus

from app.api.deps import (
    RequireDataSourceDelete,
    RequireDataSourceRead,
    RequireDataSourceWrite,
    validate_rate_limits,
)
from app.schemas.api import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.datasource import (
    CreatePipelineFromTemplate,
    DataSource,
    DataSourceCreate,
    DataSourceUpdate,
    SourceType,
)
from app.services.datasource import DataSourceService

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse[DataSource],
    status_code=HttpStatus.HTTP_201_CREATED,
    dependencies=[Depends(validate_rate_limits)],  # Add rate limiting
)
async def create_datasource(
    datasource_in: DataSourceCreate,
    current_user: Annotated[Dict[str, Any], Depends(RequireDataSourceWrite)],
) -> ApiResponse[DataSource]:
    """
    Create new data source. Requires datasource:write permission.
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
    current_user: Dict[str, Any] = Depends(RequireDataSourceRead),
) -> PaginatedResponse[Dict[str, Any]]:
    """
    Retrieve data sources with filtering options. Requires datasource:read permission.
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
    current_user: Dict[str, Any] = Depends(RequireDataSourceRead),
) -> ApiResponse[DataSource]:
    """
    Get specific data source by ID. Requires datasource:read permission.
    """
    datasource_service = DataSourceService()

    response = await datasource_service.get_datasource_with_credentials(
        datasource_id=datasource_id
    )

    return ApiResponse(
        data=DataSource(**response),
        status=HttpStatus.HTTP_200_OK,
        message="Data source retrieved successfully",
    )


@router.patch("/{datasource_id}", response_model=ApiResponse[DataSource])
async def update_datasource(
    datasource_in: DataSourceUpdate,
    datasource_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(RequireDataSourceWrite),
) -> ApiResponse[DataSource]:
    """
    Update a data source. Requires datasource:write permission.
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
    current_user: Dict[str, Any] = Depends(RequireDataSourceDelete),
) -> ApiResponse[Dict[str, Any]]:
    """
    Delete a data source. Requires datasource:delete permission.
    """
    datasource_service = DataSourceService()
    response = await datasource_service.delete_datasource(datasource_id=datasource_id)

    return ApiResponse(
        data=response,
        status=HttpStatus.HTTP_200_OK,
        message="Data source deleted successfully",
    )


@router.get("/{datasource_id}/pipeline-templates")
async def get_pipeline_templates(
    datasource_id: str,
    current_user: Dict[str, Any] = Depends(RequireDataSourceRead),
) -> ApiResponse[List[Dict[str, Any]]]:
    """Get available pipeline templates for this data source"""

    datasource_service = DataSourceService()

    try:
        templates = await datasource_service.get_pipeline_templates(datasource_id)

        return ApiResponse(
            data=templates,
            status=HttpStatus.HTTP_200_OK,
            message="Pipeline templates retrieved successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get templates: {str(e)}",
        )


@router.post("/{datasource_id}/create-pipeline")
async def create_pipeline_from_template(
    datasource_id: str,
    create_pipeline_request: CreatePipelineFromTemplate,
    current_user: Dict[str, Any] = Depends(RequireDataSourceWrite),
) -> ApiResponse[Dict[str, Any]]:
    """Create a pipeline from template for this data source"""

    # This would integrate with the pipeline factory service we discussed earlier
    from app.services.datasource import DataSourceService

    factory_service = DataSourceService()

    template_name = create_pipeline_request.template_name
    custom_options = create_pipeline_request.custom_options

    try:
        pipeline = await factory_service.create_pipeline_from_template(
            datasource_id=datasource_id,
            template_name=template_name,
            user_id=current_user["id"],
            custom_options=custom_options or {},
        )

        return ApiResponse(
            data=pipeline,
            status=HttpStatus.HTTP_201_CREATED,
            message="Pipeline created from template successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatus.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pipeline: {str(e)}",
        )
