# app/api/endpoints/visualization.py
from typing import Any, List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, check_permission
from app.services.visualization import VisualizationService
from app.schemas.visualization import (
    Visualization,
    VisualizationCreate,
    VisualizationUpdate,
    VisualizationType,
    VisualizationData
)

router = APIRouter()


@router.post("/", response_model=Visualization, status_code=status.HTTP_201_CREATED)
async def create_visualization(
    visualization_in: VisualizationCreate,
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Create a new visualization.
    """
    visualization_service = VisualizationService()
    return await visualization_service.create_visualization(
        visualization_in=visualization_in,
        user_id=current_user["id"]
    )


@router.get("/", response_model=List[Visualization])
async def read_visualizations(
    type: Optional[VisualizationType] = None,
    is_public: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:read"))
) -> Any:
    """
    Retrieve visualizations with filtering options.
    """
    visualization_service = VisualizationService()
    
    # Get visualizations for the current user or public ones
    return await visualization_service.get_visualizations(
        user_id=current_user["id"],
        type=type,
        is_public=is_public,
        limit=limit,
        offset=offset
    )


@router.get("/public", response_model=List[Visualization])
async def read_public_visualizations(
    type: Optional[VisualizationType] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> Any:
    """
    Retrieve public visualizations.
    """
    visualization_service = VisualizationService()
    return await visualization_service.get_visualizations(
        is_public=True,
        type=type,
        limit=limit,
        offset=offset
    )


@router.get("/{visualization_id}", response_model=Visualization)
async def read_visualization(
    visualization_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get a specific visualization by ID.
    """
    visualization_service = VisualizationService()
    visualization = await visualization_service.get_visualization(visualization_id=visualization_id)
    
    # Check if visualization is public or if user is the creator
    if not visualization["is_public"] and visualization["created_by"] != current_user["id"]:
        # Check if user has admin permission
        has_admin_perm = "admin" in current_user.get("roles", [])
        
        if not has_admin_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this visualization"
            )
    
    return visualization


@router.patch("/{visualization_id}", response_model=Visualization)
async def update_visualization(
    visualization_in: VisualizationUpdate,
    visualization_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Update a visualization.
    """
    visualization_service = VisualizationService()
    
    # Check if user has permission to update
    visualization = await visualization_service.get_visualization(visualization_id=visualization_id)
    
    if visualization["created_by"] != current_user["id"]:
        # Check if user has admin permission
        has_admin_perm = "admin" in current_user.get("roles", [])
        
        if not has_admin_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this visualization"
            )
    
    return await visualization_service.update_visualization(
        visualization_id=visualization_id,
        visualization_in=visualization_in
    )


@router.delete("/{visualization_id}", response_model=Dict[str, Any])
async def delete_visualization(
    visualization_id: str = Path(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Delete a visualization.
    """
    visualization_service = VisualizationService()
    
    # Check if user has permission to delete
    visualization = await visualization_service.get_visualization(visualization_id=visualization_id)
    
    if visualization["created_by"] != current_user["id"]:
        # Check if user has admin permission
        has_admin_perm = "admin" in current_user.get("roles", [])
        
        if not has_admin_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this visualization"
            )
    
    return await visualization_service.delete_visualization(visualization_id=visualization_id)


@router.get("/{visualization_id}/data", response_model=VisualizationData)
async def get_visualization_data(
    visualization_id: str = Path(...),
    params: Dict[str, Any] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Any:
    """
    Get data for a visualization.
    """
    visualization_service = VisualizationService()
    
    # Check if visualization is public or if user is the creator
    visualization = await visualization_service.get_visualization(visualization_id=visualization_id)
    
    if not visualization["is_public"] and visualization["created_by"] != current_user["id"]:
        # Check if user has read permission
        has_read_perm = await check_permission("knowledge:read", current_user)
        
        if not has_read_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this visualization data"
            )
    
    return await visualization_service.get_visualization_data(
        visualization_id=visualization_id,
        params=params
    )


class DefaultVisualizationRequest(BaseModel):
    entity_id: str
    visualization_type: VisualizationType = VisualizationType.GRAPH
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = False


@router.post("/default", response_model=Visualization)
async def create_default_visualization(
    request: DefaultVisualizationRequest,
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:write"))
) -> Any:
    """
    Create a default visualization for an entity.
    """
    visualization_service = VisualizationService()
    
    # Generate title if not provided
    title = request.title or f"{request.visualization_type.capitalize()} visualization for entity {request.entity_id}"
    
    # Create configuration based on visualization type
    config = None
    
    if request.visualization_type == VisualizationType.GRAPH:
        config = {
            "type": VisualizationType.GRAPH,
            "config": {
                "node_config": {
                    "color_field": "type",
                    "color_mapping": {
                        "Customer": "#4CAF50",
                        "BankAccount": "#2196F3",
                        "Transaction": "#FFC107",
                        "Loan": "#F44336",
                        "Branch": "#9C27B0",
                        "Employee": "#FF9800"
                    },
                    "size_field": None,
                    "label_field": "text"
                },
                "edge_config": {
                    "color_field": "type",
                    "color_mapping": {},
                    "width_field": None,
                    "label_field": "type"
                },
                "layout": {
                    "type": "force",
                    "params": {
                        "linkDistance": 150,
                        "charge": -500
                    }
                },
                "show_labels": True,
                "show_tooltips": True,
                "zoom_enabled": True,
                "pan_enabled": True,
                "physics_enabled": True,
                "interactive": True,
                "height": 600
            }
        }
    elif request.visualization_type == VisualizationType.TREE:
        config = {
            "type": VisualizationType.TREE,
            "config": {
                "node_config": {
                    "color_field": "type",
                    "color_mapping": {
                        "Customer": "#4CAF50",
                        "BankAccount": "#2196F3",
                        "Transaction": "#FFC107",
                        "Loan": "#F44336",
                        "Branch": "#9C27B0",
                        "Employee": "#FF9800"
                    },
                    "label_field": "text"
                },
                "edge_config": {
                    "color_field": "type",
                    "label_field": "type"
                },
                "orientation": "vertical",
                "alignment": "center",
                "node_separation": 150,
                "level_separation": 200,
                "show_labels": True,
                "show_tooltips": True,
                "interactive": True,
                "height": 600
            }
        }
    elif request.visualization_type == VisualizationType.TABLE:
        config = {
            "type": VisualizationType.TABLE,
            "config": {
                "columns": [
                    {"field": "id", "header": "ID", "sortable": True},
                    {"field": "text", "header": "Text", "sortable": True},
                    {"field": "type", "header": "Type", "sortable": True}
                ],
                "pagination": True,
                "page_size": 10,
                "sortable": True,
                "filterable": True
            }
        }
    elif request.visualization_type == VisualizationType.CHART:
        config = {
            "type": VisualizationType.CHART,
            "config": {
                "type": "bar",
                # app/api/endpoints/visualization.py (continued)
                "axes": {
                    "x_field": "type",
                    "y_field": "count",
                    "group_by_field": "type"
                },
                "color_scheme": ["#4CAF50", "#2196F3", "#FFC107", "#F44336", "#9C27B0", "#FF9800"],
                "title": title,
                "legend": True,
                "grid": True,
                "height": 400
            }
        }
    
    # Create visualization
    visualization_in = VisualizationCreate(
        name=title,
        description=request.description or f"Default {request.visualization_type} visualization",
        entity_id=request.entity_id,
        is_public=request.is_public,
        config=config
    )
    
    return await visualization_service.create_visualization(
        visualization_in=visualization_in,
        user_id=current_user["id"]
    )


@router.get("/templates", response_model=List[Dict[str, Any]])
async def get_visualization_templates(
    current_user: Dict[str, Any] = Depends(check_permission("knowledge:read"))
) -> Any:
    """
    Get visualization templates.
    """
    # Return predefined visualization templates
    templates = [
        {
            "id": "graph-default",
            "name": "Default Graph Visualization",
            "type": VisualizationType.GRAPH,
            "description": "Basic force-directed graph visualization",
            "preview_image": "/static/templates/graph-default.png",
            "config": {
                "type": VisualizationType.GRAPH,
                "config": {
                    "node_config": {
                        "color_field": "type",
                        "color_mapping": {
                            "Customer": "#4CAF50",
                            "BankAccount": "#2196F3",
                            "Transaction": "#FFC107",
                            "Loan": "#F44336",
                            "Branch": "#9C27B0",
                            "Employee": "#FF9800"
                        },
                        "size_field": None,
                        "label_field": "text"
                    },
                    "edge_config": {
                        "color_field": "type",
                        "width_field": None,
                        "label_field": "type"
                    },
                    "layout": {
                        "type": "force",
                        "params": {}
                    },
                    "show_labels": True,
                    "show_tooltips": True,
                    "zoom_enabled": True,
                    "pan_enabled": True,
                    "physics_enabled": True,
                    "interactive": True,
                    "height": 600
                }
            }
        },
        {
            "id": "tree-hierarchical",
            "name": "Hierarchical Tree Visualization",
            "type": VisualizationType.TREE,
            "description": "Tree visualization with hierarchical layout",
            "preview_image": "/static/templates/tree-hierarchical.png",
            "config": {
                "type": VisualizationType.TREE,
                "config": {
                    "node_config": {
                        "color_field": "type",
                        "color_mapping": {},
                        "label_field": "text"
                    },
                    "edge_config": {
                        "color_field": "type",
                        "label_field": "type"
                    },
                    "orientation": "vertical",
                    "alignment": "center",
                    "node_separation": 150,
                    "level_separation": 200,
                    "show_labels": True,
                    "show_tooltips": True,
                    "interactive": True,
                    "height": 600
                }
            }
        },
        {
            "id": "bar-chart",
            "name": "Bar Chart",
            "type": VisualizationType.CHART,
            "description": "Basic bar chart visualization",
            "preview_image": "/static/templates/bar-chart.png",
            "config": {
                "type": VisualizationType.CHART,
                "config": {
                    "type": "bar",
                    "axes": {
                        "x_field": "type",
                        "y_field": "count",
                        "group_by_field": "type"
                    },
                    "color_scheme": ["#4CAF50", "#2196F3", "#FFC107", "#F44336", "#9C27B0", "#FF9800"],
                    "title": "Bar Chart",
                    "legend": True,
                    "grid": True,
                    "height": 400
                }
            }
        },
        {
            "id": "data-table",
            "name": "Data Table",
            "type": VisualizationType.TABLE,
            "description": "Tabular data visualization",
            "preview_image": "/static/templates/data-table.png",
            "config": {
                "type": VisualizationType.TABLE,
                "config": {
                    "columns": [
                        {"field": "id", "header": "ID", "sortable": True},
                        {"field": "text", "header": "Text", "sortable": True},
                        {"field": "type", "header": "Type", "sortable": True}
                    ],
                    "pagination": True,
                    "page_size": 10,
                    "sortable": True,
                    "filterable": True
                }
            }
        }
    ]
    
    return templates
