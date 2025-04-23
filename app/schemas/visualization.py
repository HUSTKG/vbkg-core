from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, validator


class VisualizationType(str, Enum):
    GRAPH = "graph"
    TREE = "tree"
    TABLE = "table"
    CHART = "chart"


class NodeDisplayConfig(BaseModel):
    color_field: Optional[str] = None
    color_mapping: Optional[Dict[str, str]] = None
    default_color: str = "#1f77b4"
    size_field: Optional[str] = None
    size_range: Optional[List[int]] = Field(default=[30, 80])
    label_field: str = "text"
    icon_field: Optional[str] = None
    icon_mapping: Optional[Dict[str, str]] = None
    group_by_field: Optional[str] = None


class EdgeDisplayConfig(BaseModel):
    color_field: Optional[str] = None
    color_mapping: Optional[Dict[str, str]] = None
    default_color: str = "#aaa"
    width_field: Optional[str] = None
    width_range: Optional[List[int]] = Field(default=[1, 5])
    label_field: Optional[str] = "type"
    style_field: Optional[str] = None
    style_mapping: Optional[Dict[str, str]] = None


class GraphLayoutType(str, Enum):
    FORCE = "force"
    RADIAL = "radial"
    HIERARCHICAL = "hierarchical"
    CIRCULAR = "circular"
    GRID = "grid"
    CONCENTRIC = "concentric"


class GraphLayoutConfig(BaseModel):
    type: GraphLayoutType = GraphLayoutType.FORCE
    params: Dict[str, Any] = Field(default_factory=dict)


class GraphVisualizationConfig(BaseModel):
    node_config: NodeDisplayConfig = Field(default_factory=NodeDisplayConfig)
    edge_config: EdgeDisplayConfig = Field(default_factory=EdgeDisplayConfig)
    layout: GraphLayoutConfig = Field(default_factory=GraphLayoutConfig)
    show_labels: bool = True
    show_tooltips: bool = True
    zoom_enabled: bool = True
    pan_enabled: bool = True
    clustering_enabled: bool = False
    physics_enabled: bool = True
    interactive: bool = True
    max_nodes: int = Field(500, ge=1, le=2000)
    height: int = Field(600, ge=300, le=2000)
    width: Optional[int] = None


class TreeVisualizationConfig(BaseModel):
    node_config: NodeDisplayConfig = Field(default_factory=NodeDisplayConfig)
    edge_config: EdgeDisplayConfig = Field(default_factory=EdgeDisplayConfig)
    orientation: str = "vertical"  # vertical, horizontal
    alignment: str = "center"  # center, left, right
    node_separation: int = 150
    level_separation: int = 200
    show_labels: bool = True
    show_tooltips: bool = True
    interactive: bool = True
    height: int = Field(600, ge=300, le=2000)
    width: Optional[int] = None


class TableColumn(BaseModel):
    field: str
    header: str
    sortable: bool = True
    filterable: bool = True
    width: Optional[int] = None
    render_template: Optional[str] = None


class TableVisualizationConfig(BaseModel):
    columns: List[TableColumn]
    pagination: bool = True
    page_size: int = Field(10, ge=1, le=100)
    sortable: bool = True
    filterable: bool = True
    height: Optional[int] = None
    width: Optional[int] = None


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    RADAR = "radar"
    HEATMAP = "heatmap"


class ChartAxes(BaseModel):
    x_field: str
    y_field: Optional[str] = None
    z_field: Optional[str] = None
    color_field: Optional[str] = None
    size_field: Optional[str] = None
    group_by_field: Optional[str] = None


class ChartVisualizationConfig(BaseModel):
    type: ChartType
    axes: ChartAxes
    color_scheme: Optional[List[str]] = None
    title: Optional[str] = None
    legend: bool = True
    grid: bool = True
    stacked: bool = False
    normalized: bool = False
    annotations: Optional[List[Dict[str, Any]]] = None
    height: int = Field(400, ge=200, le=1000)
    width: Optional[int] = None


class VisualizationConfig(BaseModel):
    type: VisualizationType
    config: Union[
        GraphVisualizationConfig,
        TreeVisualizationConfig,
        TableVisualizationConfig,
        ChartVisualizationConfig
    ] = Field(...)
    
    @validator('config', pre=True)
    def validate_config(cls, v, values):
        if 'type' not in values:
            raise ValueError("Visualization type is required")
        
        if values['type'] == VisualizationType.GRAPH:
            if not isinstance(v, GraphVisualizationConfig):
                return GraphVisualizationConfig(**v)
        elif values['type'] == VisualizationType.TREE:
            if not isinstance(v, TreeVisualizationConfig):
                return TreeVisualizationConfig(**v)
        elif values['type'] == VisualizationType.TABLE:
            if not isinstance(v, TableVisualizationConfig):
                return TableVisualizationConfig(**v)
        elif values['type'] == VisualizationType.CHART:
            if not isinstance(v, ChartVisualizationConfig):
                return ChartVisualizationConfig(**v)
        
        return v


class VisualizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    query_id: Optional[str] = None
    cypher_query: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    is_public: bool = False
    config: VisualizationConfig
    
    @validator('query_id', 'cypher_query', 'entity_id', 'entity_type')
    def validate_data_source(cls, v, values):
        # Ensure at least one data source is provided
        if not any(key in values and values[key] is not None for key in ['query_id', 'cypher_query', 'entity_id']):
            if v is None:
                raise ValueError("At least one of query_id, cypher_query, or entity_id must be provided")
        return v


class VisualizationCreate(VisualizationBase):
    pass


class VisualizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    query_id: Optional[str] = None
    cypher_query: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    is_public: Optional[bool] = None
    config: Optional[VisualizationConfig] = None


class Visualization(VisualizationBase):
    id: str
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VisualizationData(BaseModel):
    nodes: Optional[List[Dict[str, Any]]] = None
    edges: Optional[List[Dict[str, Any]]] = None
    rows: Optional[List[Dict[str, Any]]] = None
    chart_data: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

class DefaultVisualizationRequest(BaseModel):
    entity_id: str
    visualization_type: VisualizationType = VisualizationType.GRAPH
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: bool = False

