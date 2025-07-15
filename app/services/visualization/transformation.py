import time
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.visualization import VisualizationData, VisualizationType

from .base import BaseVisualizationService
from .configuration import VisualizationConfigService


class VisualizationTransformationService(BaseVisualizationService):
    """Service for transforming data for different visualization types"""
    
    def __init__(self):
        super().__init__()
        self.config_service = VisualizationConfigService()
    
    def transform_data_for_visualization(
        self, 
        data: List[Dict[str, Any]], 
        visualization: Dict[str, Any]
    ) -> VisualizationData:
        """Transform data based on visualization type"""
        
        visualization_type = visualization["visualization_type"]
        config = visualization["config"]
        
        result = VisualizationData()
        
        try:
            if visualization_type == VisualizationType.GRAPH:
                nodes, edges = self._transform_data_for_graph(data, config)
                result.nodes = nodes
                result.edges = edges
                
            elif visualization_type == VisualizationType.TREE:
                nodes, edges = self._transform_data_for_tree(data, config)
                result.nodes = nodes
                result.edges = edges
                
            elif visualization_type == VisualizationType.TABLE:
                rows = self._transform_data_for_table(data, config)
                result.rows = rows
                
            elif visualization_type == VisualizationType.CHART:
                chart_data = self._transform_data_for_chart(data, config)
                result.chart_data = chart_data
            
            # Add metadata
            result.metadata = {
                "record_count": len(data) if data else 0,
                "visualization_type": visualization_type,
                "visualization_name": visualization["name"],
                "timestamp": time.time(),
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error transforming data for visualization: {e}")
            # Return empty result with error info
            result.metadata = {
                "record_count": 0,
                "visualization_type": visualization_type,
                "visualization_name": visualization["name"],
                "timestamp": time.time(),
                "error": str(e)
            }
            return result
    
    def _transform_data_for_graph(
        self, 
        data: List[Dict[str, Any]], 
        config: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Transform data for graph visualization"""
        
        try:
            nodes = {}
            edges = []
            
            # Get configuration
            node_config = config.get("node_config", {})
            edge_config = config.get("edge_config", {})
            
            # Process each record
            for record in data:
                source = record.get("source")
                rel = record.get("r")
                target = record.get("target")
                
                # Process source node
                if source and source.get("id") not in nodes:
                    node = self.config_service.create_node_object(source, node_config)
                    nodes[source.get("id")] = node
                
                # Process target node
                if target and target.get("id") not in nodes:
                    node = self.config_service.create_node_object(target, node_config)
                    nodes[target.get("id")] = node
                
                # Process relationship
                if source and target and rel:
                    edge = self.config_service.create_edge_object(
                        rel, source.get("id"), target.get("id"), edge_config
                    )
                    edges.append(edge)
            
            return list(nodes.values()), edges
            
        except Exception as e:
            self.logger.error(f"Error transforming data for graph: {e}")
            return [], []
    
    def _transform_data_for_tree(
        self, 
        data: List[Dict[str, Any]], 
        config: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Transform data for tree visualization"""
        
        # For tree visualization, use the same transformation as graph
        # but ensure it forms a tree structure
        nodes, edges = self._transform_data_for_graph(data, config)
        
        # Additional processing to ensure tree structure could be added here
        # For now, return the same as graph
        return nodes, edges
    
    def _transform_data_for_table(
        self, 
        data: List[Dict[str, Any]], 
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Transform data for table visualization"""
        
        try:
            rows = []
            
            # Get configuration
            columns = config.get("config", {}).get("columns", [])
            column_fields = [col.get("field") for col in columns]
            
            # Process each record
            for record in data:
                row = {}
                
                for key, value in record.items():
                    if isinstance(value, (dict, list)):
                        # Handle nested structures (e.g., nodes, relationships)
                        if hasattr(value, "keys"):
                            # It's a dictionary-like object (e.g., a Node)
                            for prop_key, prop_value in dict(value).items():
                                if prop_key in column_fields:
                                    row[prop_key] = prop_value
                        continue
                    
                    if key in column_fields:
                        row[key] = value
                
                rows.append(row)
            
            return rows
            
        except Exception as e:
            self.logger.error(f"Error transforming data for table: {e}")
            return []
    
    def _transform_data_for_chart(
        self, 
        data: List[Dict[str, Any]], 
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Transform data for chart visualization"""
        
        try:
            chart_data = []
            
            # Get configuration
            chart_config = config.get("config", {})
            chart_type = chart_config.get("type", "bar")
            axes = chart_config.get("axes", {})
            
            x_field = axes.get("x_field")
            y_field = axes.get("y_field")
            z_field = axes.get("z_field")
            color_field = axes.get("color_field")
            size_field = axes.get("size_field")
            group_by_field = axes.get("group_by_field")
            
            if not x_field:
                raise ValueError("x_field is required for chart visualization")
            
            # For basic charts (bar, line, pie), aggregate data
            if chart_type in ["bar", "line", "pie"]:
                chart_data = self._aggregate_chart_data(
                    data, x_field, y_field, group_by_field
                )
            
            # For scatter plots, use individual points
            elif chart_type == "scatter":
                chart_data = self._create_scatter_data(
                    data, x_field, y_field, z_field, 
                    color_field, size_field, group_by_field
                )
            
            return chart_data
            
        except Exception as e:
            self.logger.error(f"Error transforming data for chart: {e}")
            return []
    
    def _aggregate_chart_data(
        self, 
        data: List[Dict[str, Any]], 
        x_field: str, 
        y_field: Optional[str], 
        group_by_field: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Aggregate data for basic chart types"""
        
        grouped_data = {}
        
        for record in data:
            x_value = self._extract_value_from_record(record, x_field)
            y_value = self._extract_value_from_record(record, y_field) if y_field else 1
            
            group = (
                self._extract_value_from_record(record, group_by_field)
                if group_by_field else "default"
            )
            
            key = (str(x_value), str(group))
            
            if key not in grouped_data:
                grouped_data[key] = {"x": x_value, "y": 0, "group": group}
            
            # Aggregate y values
            try:
                y_num = float(y_value)
                grouped_data[key]["y"] += y_num
            except (ValueError, TypeError):
                pass
        
        return list(grouped_data.values())
    
    def _create_scatter_data(
        self, 
        data: List[Dict[str, Any]], 
        x_field: str, 
        y_field: Optional[str], 
        z_field: Optional[str],
        color_field: Optional[str], 
        size_field: Optional[str], 
        group_by_field: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Create scatter plot data points"""
        
        chart_data = []
        
        for record in data:
            x_value = self._extract_value_from_record(record, x_field)
            y_value = self._extract_value_from_record(record, y_field) if y_field else 0
            z_value = self._extract_value_from_record(record, z_field) if z_field else 0
            color_value = self._extract_value_from_record(record, color_field) if color_field else None
            size_value = self._extract_value_from_record(record, size_field) if size_field else 5
            group = (
                self._extract_value_from_record(record, group_by_field)
                if group_by_field else "default"
            )
            
            point = {"x": x_value, "y": y_value, "group": group}
            
            if z_field:
                point["z"] = z_value
            
            if color_field:
                point["color"] = color_value
            
            if size_field:
                try:
                    point["size"] = float(size_value)
                except (ValueError, TypeError):
                    point["size"] = 5
            
            chart_data.append(point)
        
        return chart_data
    
    def _extract_value_from_record(
        self, 
        record: Dict[str, Any], 
        field: Optional[str]
    ) -> Any:
        """Extract a value from a record, handling nested structures"""
        
        if not field:
            return None
        
        # Handle dot notation for nested fields
        parts = field.split(".")
        value = record
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif hasattr(value, part):
                # For Neo4j Node objects
                value = getattr(value, part)
            elif (
                value is not None
                and hasattr(value, "get")
                and callable(value.get)
                and value.get(part) is not None
            ):
                # For dictionary-like objects
                value = value.get(part)
            else:
                return None
        
        return value

