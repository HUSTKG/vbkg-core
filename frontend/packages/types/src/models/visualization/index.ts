export enum VisualizationType {
  GRAPH = "graph",
  TREE = "tree",
  TABLE = "table",
  CHART = "chart",
}

export interface NodeDisplayConfig {
  color_field?: string;
  color_mapping?: Record<string, string>;
  default_color: string;
  size_field?: string;
  size_range: number[];
  label_field: string;
  icon_field?: string;
  icon_mapping?: Record<string, string>;
  group_by_field?: string;
}

export interface EdgeDisplayConfig {
  color_field?: string;
  color_mapping?: Record<string, string>;
  default_color: string;
  width_field?: string;
  width_range: number[];
  label_field?: string;
  style_field?: string;
  style_mapping?: Record<string, string>;
}

export enum GraphLayoutType {
  FORCE = "force",
  RADIAL = "radial",
  HIERARCHICAL = "hierarchical",
  CIRCULAR = "circular",
  GRID = "grid",
  CONCENTRIC = "concentric",
}

export interface GraphLayoutConfig {
  type: GraphLayoutType;
  params: Record<string, any>;
}

export interface GraphVisualizationConfig {
  node_config: NodeDisplayConfig;
  edge_config: EdgeDisplayConfig;
  layout: GraphLayoutConfig;
  show_labels: boolean;
  show_tooltips: boolean;
  zoom_enabled: boolean;
  pan_enabled: boolean;
  clustering_enabled: boolean;
  physics_enabled: boolean;
  interactive: boolean;
  max_nodes: number;
  height: number;
  width?: number;
}

export interface TreeVisualizationConfig {
  node_config: NodeDisplayConfig;
  edge_config: EdgeDisplayConfig;
  orientation: string;
  alignment: string;
  node_separation: number;
  level_separation: number;
  show_labels: boolean;
  show_tooltips: boolean;
  interactive: boolean;
  height: number;
  width?: number;
}

export interface TableColumn {
  field: string;
  header: string;
  sortable: boolean;
  filterable: boolean;
  width?: number;
  render_template?: string;
}

export interface TableVisualizationConfig {
  columns: TableColumn[];
  pagination: boolean;
  page_size: number;
  sortable: boolean;
  filterable: boolean;
  height?: number;
  width?: number;
}

export enum ChartType {
  BAR = "bar",
  LINE = "line",
  PIE = "pie",
  SCATTER = "scatter",
  RADAR = "radar",
  HEATMAP = "heatmap",
}

export interface ChartAxes {
  x_field: string;
  y_field?: string;
  z_field?: string;
  color_field?: string;
  size_field?: string;
  group_by_field?: string;
}

export interface ChartVisualizationConfig {
  type: ChartType;
  axes: ChartAxes;
  color_scheme?: string[];
  title?: string;
  legend: boolean;
  grid: boolean;
  stacked: boolean;
  normalized: boolean;
  annotations?: Record<string, any>[];
  height: number;
  width?: number;
}

export interface VisualizationConfig {
  type: VisualizationType;
  config:
    | GraphVisualizationConfig
    | TreeVisualizationConfig
    | TableVisualizationConfig
    | ChartVisualizationConfig;
}

export interface VisualizationBase {
  name: string;
  description?: string;
  query_id?: string;
  cypher_query?: string;
  entity_id?: string;
  entity_type?: string;
  is_public: boolean;
  config: VisualizationConfig;
}

export interface VisualizationCreate extends VisualizationBase {}

export interface VisualizationUpdate {
  name?: string;
  description?: string;
  query_id?: string;
  cypher_query?: string;
  entity_id?: string;
  entity_type?: string;
  is_public?: boolean;
  config?: VisualizationConfig;
}

export interface Visualization {
  id: string;
  created_by?: string;
  created_at: Date;
  updated_at: Date;
}

export interface VisualizationData {
  nodes?: Record<string, any>[];
  edges?: Record<string, any>[];
  rows?: Record<string, any>[];
  chart_data?: Record<string, any>[];
  metadata?: Record<string, any>;
}

export interface DefaultVisualizationRequest {
  entity_id: string;
  visualization_type: VisualizationType;
  title?: string;
  description?: string;
  is_public?: boolean;
}
