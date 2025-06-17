from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


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
    label_field: str = "type"
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
    params: Dict[str, Any] = Field(default_factory=dict)


class GraphVisualizationConfig(BaseModel):
    node_config: NodeDisplayConfig = Field(default_factory=NodeDisplayConfig)
    edge_config: EdgeDisplayConfig = Field(default_factory=EdgeDisplayConfig)
    layout: Dict[str, Any] = Field(default_factory=lambda: {"type": "force", "params": {}})
    show_labels: bool = True
    show_tooltips: bool = True
    zoom_enabled: bool = True
    pan_enabled: bool = True
    clustering_enabled: bool = False
    physics_enabled: bool = True
    interactive: bool = True
    max_nodes: int = Field(default=500, ge=1, le=2000)
    height: int = Field(default=600, ge=300, le=2000)
    width: Optional[int] = None


class TreeVisualizationConfig(BaseModel):
    node_config: NodeDisplayConfig = Field(default_factory=NodeDisplayConfig)
    edge_config: EdgeDisplayConfig = Field(default_factory=EdgeDisplayConfig)
    orientation: str = Field(default="vertical")
    alignment: str = Field(default="center")
    node_separation: int = 150
    level_separation: int = 200
    show_labels: bool = True
    show_tooltips: bool = True
    interactive: bool = True
    height: int = Field(default=600, ge=300, le=2000)
    width: Optional[int] = None

    @field_validator("orientation")
    @classmethod
    def validate_orientation(cls, v):
        if v not in ["vertical", "horizontal"]:
            raise ValueError("orientation must be 'vertical' or 'horizontal'")
        return v

    @field_validator("alignment")
    @classmethod
    def validate_alignment(cls, v):
        if v not in ["center", "left", "right"]:
            raise ValueError("alignment must be 'center', 'left', or 'right'")
        return v


class TableColumn(BaseModel):
    field: str
    header: str
    sortable: bool = True
    filterable: bool = True
    width: Optional[int] = None
    render_template: Optional[str] = None


class TableVisualizationConfig(BaseModel):
    columns: List[TableColumn] = Field(default_factory=list)
    pagination: bool = True
    page_size: int = Field(default=10, ge=1, le=100)
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
    chart_type: ChartType = ChartType.BAR
    axes: ChartAxes
    color_scheme: Optional[str] = None
    title: Optional[str] = None
    legend: bool = True
    grid: bool = True
    stacked: bool = False
    normalized: bool = False
    annotations: Optional[List[Dict[str, Any]]] = None
    height: int = Field(default=400, ge=200, le=1000)
    width: Optional[int] = None


class GenericVisualizationConfig(BaseModel):
    """Generic config for custom visualization types"""
    custom_config: Dict[str, Any] = Field(default_factory=dict)


# Union type for all visualization configurations
VisualizationConfig = Union[
    GraphVisualizationConfig,
    TreeVisualizationConfig,
    TableVisualizationConfig,
    ChartVisualizationConfig,
    GenericVisualizationConfig,
]


class VisualizationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    visualization_type: VisualizationType = VisualizationType.GRAPH
    description: Optional[str] = None
    query_id: Optional[str] = None
    cypher_query: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    is_public: bool = False
    config: VisualizationConfig

    @model_validator(mode="after")
    def validate_data_source(self):
        """Ensure at least one data source is provided"""
        if not any([self.query_id, self.cypher_query, self.entity_id]):
            raise ValueError(
                "At least one of query_id, cypher_query, or entity_id must be provided"
            )
        return self

    @field_validator("config", mode="before")
    @classmethod
    def parse_config(cls, v, info):
        """Parse config based on visualization_type"""
        if v is None:
            return v
        
        # Get visualization_type from the model data
        visualization_type = info.data.get("visualization_type")
        
        if isinstance(v, dict):
            # Create appropriate config based on visualization_type
            if visualization_type == VisualizationType.GRAPH:
                return GraphVisualizationConfig(**v)
            elif visualization_type == VisualizationType.TREE:
                return TreeVisualizationConfig(**v)
            elif visualization_type == VisualizationType.TABLE:
                return TableVisualizationConfig(**v)
            elif visualization_type == VisualizationType.CHART:
                return ChartVisualizationConfig(**v)
            else:
                return GenericVisualizationConfig(custom_config=v)
        return v


class VisualizationCreate(VisualizationBase):
    pass


class VisualizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    visualization_type: Optional[VisualizationType] = None
    description: Optional[str] = None
    query_id: Optional[str] = None
    cypher_query: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    is_public: Optional[bool] = None
    config: Optional[VisualizationConfig] = None

    @field_validator("config", mode="before")
    @classmethod
    def parse_config(cls, v, info):
        """Parse config based on visualization_type"""
        if v is None:
            return v
        
        # Get visualization_type from the model data
        visualization_type = info.data.get("visualization_type")
        
        if isinstance(v, dict):
            # Create appropriate config based on visualization_type
            if visualization_type == VisualizationType.GRAPH:
                return GraphVisualizationConfig(**v)
            elif visualization_type == VisualizationType.TREE:
                return TreeVisualizationConfig(**v)
            elif visualization_type == VisualizationType.TABLE:
                return TableVisualizationConfig(**v)
            elif visualization_type == VisualizationType.CHART:
                return ChartVisualizationConfig(**v)
            else:
                return GenericVisualizationConfig(custom_config=v)
        return v


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
