import uuid
from typing import Any, Dict, Optional

from .base import BaseVisualizationService


class VisualizationConfigService(BaseVisualizationService):
    """Service for handling visualization configuration and mapping"""
    
    def create_node_object(
        self, 
        node: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a node object for visualization"""
        
        # Get node properties
        node_props = dict(node)
        node_id = node.get(
            "id",
            str(node["identity"]) if hasattr(node, "identity") else str(uuid.uuid4()),
        )
        
        # Get label field
        label_field = config.get("label_field", "text")
        label = node_props.get(label_field, node_id)
        
        # Get node type/label
        if hasattr(node_props, "labels"):
            node_type = next(iter(node_props["labels"]), "Unknown")
        else:
            node_type = node_props.get("entity_type", "Unknown")
        
        # Determine color
        color = self._get_node_color(node_props, node_type, config)
        
        # Determine size
        size = self._get_node_size(node_props, config)
        
        # Create node object
        node_object = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "color": color,
            "size": size,
            "properties": {k: v for k, v in node_props.items() if k not in ["id"]},
        }
        
        # Add icon if configured
        icon = self._get_node_icon(node_props, node_type, config)
        if icon:
            node_object["icon"] = icon
        
        # Add group if configured
        group = self._get_node_group(node_props, config)
        if group:
            node_object["group"] = group
        
        return node_object
    
    def create_edge_object(
        self,
        rel: Dict[str, Any],
        source_id: str,
        target_id: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create an edge object for visualization"""
        
        # Get relationship properties
        rel_props = dict(rel)
        rel_id = rel.get(
            "id",
            str(rel["identity"]) if hasattr(rel, "identity") else str(uuid.uuid4()),
        )
        
        # Get relationship type
        if hasattr(rel, "__class__"):
            rel_type = rel.__class__.__name__
        else:
            rel_type = rel_props.get("type", "Unknown")
        
        # Get label field
        label_field = config.get("label_field", "type")
        label = rel_props.get(label_field, rel_type)
        
        # Determine color
        color = self._get_edge_color(rel_props, rel_type, config)
        
        # Determine width
        width = self._get_edge_width(rel_props, config)
        
        # Determine style
        style = self._get_edge_style(rel_props, rel_type, config)
        
        # Create edge object
        edge_object = {
            "id": rel_id,
            "source": source_id,
            "target": target_id,
            "label": label,
            "type": rel_type,
            "color": color,
            "width": width,
            "style": style,
            "properties": {k: v for k, v in rel_props.items() if k not in ["id"]},
        }
        
        return edge_object
    
    def _get_node_color(
        self, 
        node_props: Dict[str, Any], 
        node_type: str, 
        config: Dict[str, Any]
    ) -> str:
        """Determine node color based on configuration"""
        
        color = config.get("default_color", "#1f77b4")
        color_field = config.get("color_field")
        color_mapping = config.get("color_mapping", {}) or {}
        
        if color_field and color_field in node_props:
            field_value = str(node_props[color_field])
            if field_value in color_mapping:
                color = color_mapping[field_value]
        elif node_type in color_mapping:
            color = color_mapping[node_type]
        
        return color
    
    def _get_node_size(
        self, 
        node_props: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> float:
        """Determine node size based on configuration"""
        
        size = 50  # Default size
        size_field = config.get("size_field")
        size_range = config.get("size_range", [30, 80])
        
        if size_field and size_field in node_props:
            try:
                field_value = float(node_props[size_field])
                size = self._map_value_to_range(
                    field_value, 0, 100, size_range[0], size_range[1]
                )
            except (ValueError, TypeError):
                pass
        
        return size
    
    def _get_node_icon(
        self, 
        node_props: Dict[str, Any], 
        node_type: str, 
        config: Dict[str, Any]
    ) -> Optional[str]:
        """Determine node icon based on configuration"""
        
        icon_field = config.get("icon_field")
        icon_mapping = config.get("icon_mapping", {}) or {}
        
        if icon_field and icon_field in node_props:
            field_value = str(node_props[icon_field])
            if field_value in icon_mapping:
                return icon_mapping[field_value]
        elif node_type in icon_mapping:
            return icon_mapping[node_type]
        
        return None
    
    def _get_node_group(
        self, 
        node_props: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> Optional[str]:
        """Determine node group based on configuration"""
        
        group_by_field = config.get("group_by_field")
        if group_by_field and group_by_field in node_props:
            return str(node_props[group_by_field])
        
        return None
    
    def _get_edge_color(
        self, 
        rel_props: Dict[str, Any], 
        rel_type: str, 
        config: Dict[str, Any]
    ) -> str:
        """Determine edge color based on configuration"""
        
        color = config.get("default_color", "#aaa")
        color_field = config.get("color_field")
        color_mapping = config.get("color_mapping", {})
        
        if color_field and color_field in rel_props:
            field_value = str(rel_props[color_field])
            if field_value in color_mapping:
                color = color_mapping[field_value]
        elif rel_type in color_mapping:
            color = color_mapping[rel_type]
        
        return color
    
    def _get_edge_width(
        self, 
        rel_props: Dict[str, Any], 
        config: Dict[str, Any]
    ) -> float:
        """Determine edge width based on configuration"""
        
        width = 1  # Default width
        width_field = config.get("width_field")
        width_range = config.get("width_range", [1, 5])
        
        if width_field and width_field in rel_props:
            try:
                field_value = float(rel_props[width_field])
                width = self._map_value_to_range(
                    field_value, 0, 100, width_range[0], width_range[1]
                )
            except (ValueError, TypeError):
                pass
        
        return width
    
    def _get_edge_style(
        self, 
        rel_props: Dict[str, Any], 
        rel_type: str, 
        config: Dict[str, Any]
    ) -> str:
        """Determine edge style based on configuration"""
        
        style = "solid"  # Default style
        style_field = config.get("style_field")
        style_mapping = config.get("style_mapping", {})
        
        if style_field and style_field in rel_props:
            field_value = str(rel_props[style_field])
            if field_value in style_mapping:
                style = style_mapping[field_value]
        elif rel_type in style_mapping:
            style = style_mapping[rel_type]
        
        return style
    
    def _map_value_to_range(
        self,
        value: float,
        min_value: float,
        max_value: float,
        min_result: float,
        max_result: float,
    ) -> float:
        """Map a value from one range to another"""
        
        # Ensure value is within bounds
        value = max(min_value, min(value, max_value))
        
        # Calculate mapped value
        normalized = (
            (value - min_value) / (max_value - min_value)
            if max_value > min_value
            else 0
        )
        result = min_result + normalized * (max_result - min_result)
        
        return result

