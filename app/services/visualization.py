# app/services/visualization.py
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
import time
import uuid
import json

from postgrest.base_request_builder import APIResponse

from app.core.config import settings
from app.core.supabase import get_supabase
from app.schemas.visualization import (
    VisualizationType,
    VisualizationCreate,
    VisualizationUpdate,
    Visualization,
    VisualizationData
)


class VisualizationService:
    def __init__(self):
        # Connect to Neo4j for data querying
        from py2neo import Graph
        self.graph = Graph(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

    async def create_visualization(
        self,
        visualization_in: VisualizationCreate,
        user_id: str
    ) -> Dict[str, Any]:
        """Create a new visualization"""
        try:
            supabase = await get_supabase()
            # Validate that at least one data source is provided
            if not visualization_in.query_id and not visualization_in.cypher_query and not visualization_in.entity_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one of query_id, cypher_query, or entity_id must be provided"
                )
            
            # Prepare data
            data = visualization_in.dict()
            data["created_by"] = user_id
            
            # Insert into database
            response = await supabase.from_("visualizations").insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create visualization"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating visualization: {str(e)}"
            )

    async def get_visualization(self, visualization_id: str) -> Dict[str, Any]:
        """Get a visualization by ID"""
        try:
            supabase = await get_supabase()
            response = await supabase.from_("visualizations").select("*").eq("id", visualization_id).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Visualization not found"
                )
                
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving visualization: {str(e)}"
            )

    async def update_visualization(
        self,
        visualization_id: str,
        visualization_in: VisualizationUpdate
    ) -> Dict[str, Any]:
        """Update a visualization"""
        try:
            supabase = await get_supabase()
            # Check if visualization exists
            await self.get_visualization(visualization_id)
            
            # Update visualization
            data = visualization_in.dict(exclude_unset=True)
            
            response = await supabase.from_("visualizations").update(data).eq("id", visualization_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update visualization"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating visualization: {str(e)}"
            )
    # app/services/visualization.py (continued)

    # app/services/visualization.py (continued)
    async def delete_visualization(self, visualization_id: str) -> Dict[str, Any]:
        """Delete a visualization"""
        try:
            supabase = await get_supabase()
            # Check if visualization exists
            await self.get_visualization(visualization_id)
            
            # Delete visualization
            await supabase.from_("visualizations").delete().eq("id", visualization_id).execute()
            
            return {"success": True, "message": "Visualization deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting visualization: {str(e)}"
            )

    async def get_visualizations(
        self,
        user_id: Optional[str] = None,
        type: Optional[VisualizationType] = None,
        is_public: Optional[bool] = None,
        limit: int = 100,
        skip: int = 0
    ) -> APIResponse[Dict[str, Any]]:
        """Get visualizations with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("visualizations").select("*")
            
            # Apply filters
            if user_id:
                query = query.eq("created_by", user_id)
                
            if type:
                query = query.eq("config->>type", type.value)
                
            if is_public is not None:
                query = query.eq("is_public", is_public)
                
            # Apply pagination and order
            response = await query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
            
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving visualizations: {str(e)}"
            )

    async def get_visualization_data(
        self,
        visualization_id: str,
        params: Optional[Dict[str, Any]] = None
    ) -> VisualizationData:
        """Get data for a visualization"""
        try:
            # Get visualization configuration
            visualization = await self.get_visualization(visualization_id)
            visualization_type = visualization["config"]["type"]
            
            # Collect data based on the source
            data = None
            
            if visualization.get("cypher_query"):
                # Execute Cypher query
                cypher_query = visualization["cypher_query"]
                query_params = params or {}
                
                data = self.graph.run(cypher_query, **query_params).data()
            elif visualization.get("entity_id"):
                # Get entity and its relationships
                entity_id = visualization["entity_id"]
                entity_type = visualization.get("entity_type")
                
                data = await self._get_entity_visualization_data(entity_id, entity_type)
            elif visualization.get("query_id"):
                # Get data from saved query
                # In a real implementation, you would fetch the query definition and execute it
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="Query-based visualization not implemented yet"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No data source specified for visualization"
                )
            
            # Transform data based on visualization type
            result = VisualizationData()
            
            if visualization_type == VisualizationType.GRAPH:
                nodes, edges = self._transform_data_for_graph(data, visualization["config"])
                result.nodes = nodes
                result.edges = edges
            elif visualization_type == VisualizationType.TREE:
                nodes, edges = self._transform_data_for_tree(data, visualization["config"])
                result.nodes = nodes
                result.edges = edges
            elif visualization_type == VisualizationType.TABLE:
                rows = self._transform_data_for_table(data, visualization["config"])
                result.rows = rows
            elif visualization_type == VisualizationType.CHART:
                chart_data = self._transform_data_for_chart(data, visualization["config"])
                result.chart_data = chart_data
            
            # Add metadata
            result.metadata = {
                "record_count": len(data) if data else 0,
                "visualization_type": visualization_type,
                "visualization_name": visualization["name"],
                "timestamp": time.time()
            }
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting visualization data: {str(e)}"
            )

    async def _get_entity_visualization_data(
        self,
        entity_id: str,
        entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get entity and its relationships for visualization"""
        try:
            # Build Cypher query to get entity and its relationships
            cypher_query = f"""
            MATCH (n {{id: '{entity_id}'}})
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n as source, r, m as target
            UNION
            MATCH (n {{id: '{entity_id}'}})
            OPTIONAL MATCH (n)<-[r]-(m)
            RETURN m as source, r, n as target
            """
            
            # Execute query
            data = self.graph.run(cypher_query).data()
            
            return data
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting entity visualization data: {str(e)}"
            )

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
            node_config = config.get("config", {}).get("node_config", {})
            edge_config = config.get("config", {}).get("edge_config", {})
            
            # Process each record
            for record in data:
                source = record.get("source")
                rel = record.get("r")
                target = record.get("target")
                
                # Process source node
                if source and source.get("id") not in nodes:
                    node = self._create_node_object(source, node_config)
                    nodes[source.get("id")] = node
                
                # Process target node
                if target and target.get("id") not in nodes:
                    node = self._create_node_object(target, node_config)
                    nodes[target.get("id")] = node
                
                # Process relationship
                if source and target and rel:
                    edge = self._create_edge_object(rel, source.get("id"), target.get("id"), edge_config)
                    edges.append(edge)
            
            return list(nodes.values()), edges
        except Exception as e:
            print(f"Error transforming data for graph: {e}")
            return [], []

    def _create_node_object(
        self,
        node: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a node object for visualization"""
        # Get node properties
        node_props = dict(node)
        node_id = node.get("id", str(node['identity']) if hasattr(node, "identity") else str(uuid.uuid4()))
        
        # Get label field
        label_field = config.get("label_field", "text")
        label = node_props.get(label_field, node_id)
        
        # Get node type/label
        if hasattr(node, "labels"):
            node_type = next(iter(node['labels']), "Unknown")
        else:
            node_type = node_props.get("type", "Unknown")
        
        # Determine color
        color = config.get("default_color", "#1f77b4")
        color_field = config.get("color_field")
        color_mapping = config.get("color_mapping", {})
        
        if color_field and color_field in node_props:
            field_value = str(node_props[color_field])
            if field_value in color_mapping:
                color = color_mapping[field_value]
        elif node_type in color_mapping:
            color = color_mapping[node_type]
        
        # Determine size
        size = 50  # Default size
        size_field = config.get("size_field")
        size_range = config.get("size_range", [30, 80])
        
        if size_field and size_field in node_props:
            # Simple linear mapping from field value to size range
            try:
                field_value = float(node_props[size_field])
                size = self._map_value_to_range(field_value, 0, 100, size_range[0], size_range[1])
            except (ValueError, TypeError):
                pass
        
        # Create node object
        node_object = {
            "id": node_id,
            "label": label,
            "type": node_type,
            "color": color,
            "size": size,
            "properties": {k: v for k, v in node_props.items() if k not in ["id"]}
        }
        
        # Add icon if configured
        icon_field = config.get("icon_field")
        icon_mapping = config.get("icon_mapping", {})
        
        if icon_field and icon_field in node_props:
            field_value = str(node_props[icon_field])
            if field_value in icon_mapping:
                node_object["icon"] = icon_mapping[field_value]
        elif node_type in icon_mapping:
            node_object["icon"] = icon_mapping[node_type]
        
        # Add group if configured
        group_by_field = config.get("group_by_field")
        if group_by_field and group_by_field in node_props:
            node_object["group"] = str(node_props[group_by_field])
        
        return node_object

    def _create_edge_object(
        self,
        rel: Dict[str, Any],
        source_id: str,
        target_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create an edge object for visualization"""
        # Get relationship properties
        rel_props = dict(rel)
        rel_id = rel.get("id", str(rel['identity']) if hasattr(rel, "identity") else str(uuid.uuid4()))
        
        # Get relationship type
        if hasattr(rel, "__class__"):
            rel_type = rel.__class__.__name__
        else:
            rel_type = rel_props.get("type", "Unknown")
        
        # Get label field
        label_field = config.get("label_field", "type")
        label = rel_props.get(label_field, rel_type)
        
        # Determine color
        color = config.get("default_color", "#aaa")
        color_field = config.get("color_field")
        color_mapping = config.get("color_mapping", {})
        
        if color_field and color_field in rel_props:
            field_value = str(rel_props[color_field])
            if field_value in color_mapping:
                color = color_mapping[field_value]
        elif rel_type in color_mapping:
            color = color_mapping[rel_type]
        
        # Determine width
        width = 1  # Default width
        width_field = config.get("width_field")
        width_range = config.get("width_range", [1, 5])
        
        if width_field and width_field in rel_props:
            # Simple linear mapping from field value to width range
            try:
                field_value = float(rel_props[width_field])
                width = self._map_value_to_range(field_value, 0, 100, width_range[0], width_range[1])
            except (ValueError, TypeError):
                pass
        
        # Determine style
        style = "solid"  # Default style
        style_field = config.get("style_field")
        style_mapping = config.get("style_mapping", {})
        
        if style_field and style_field in rel_props:
            field_value = str(rel_props[style_field])
            if field_value in style_mapping:
                style = style_mapping[field_value]
        elif rel_type in style_mapping:
            style = style_mapping[rel_type]
        
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
            "properties": {k: v for k, v in rel_props.items() if k not in ["id"]}
        }
        
        return edge_object

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
            print(f"Error transforming data for table: {e}")
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
            
            # For basic charts (bar, line, pie), we can aggregate data
            if chart_type in ["bar", "line", "pie"]:
                # Group by x_field and optionally by group_by_field
                grouped_data = {}
                
                for record in data:
                    x_value = self._extract_value_from_record(record, x_field)
                    y_value = self._extract_value_from_record(record, y_field) if y_field else 1
                    
                    group = self._extract_value_from_record(record, group_by_field) if group_by_field else "default"
                    
                    key = (str(x_value), str(group))
                    
                    if key not in grouped_data:
                        grouped_data[key] = {
                            "x": x_value,
                            "y": 0,
                            "group": group
                        }
                    
                    # Aggregate y values
                    try:
                        y_num = float(y_value)
                        grouped_data[key]["y"] += y_num
                    except (ValueError, TypeError):
                        pass
                
                # Convert grouped data to list
                for _, value in grouped_data.items():
                    chart_data.append(value)
            
            # For scatter plots, we need individual points
            elif chart_type == "scatter":
                for record in data:
                    x_value = self._extract_value_from_record(record, x_field)
                    y_value = self._extract_value_from_record(record, y_field) if y_field else 0
                    z_value = self._extract_value_from_record(record, z_field) if z_field else 0
                    color_value = self._extract_value_from_record(record, color_field) if color_field else None
                    size_value = self._extract_value_from_record(record, size_field) if size_field else 5
                    group = self._extract_value_from_record(record, group_by_field) if group_by_field else "default"
                    
                    point = {
                        "x": x_value,
                        "y": y_value,
                        "group": group
                    }
                    
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
        except Exception as e:
            print(f"Error transforming data for chart: {e}")
            return []

    def _extract_value_from_record(
        self,
        record: Dict[str, Any],
        field: Optional[str]
    ) -> Any:
        """Extract a value from a record, handling nested structures"""
        if not field:
            return None
        
        # Handle dot notation for nested fields
        parts = field.split('.')
        
        value = record


        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif hasattr(value, part):
                # For Neo4j Node objects
                value = getattr(value, part)
            elif value is not None and hasattr(value, "get") and callable(value.get) and value.get(part) is not None:
                # For dictionary-like objects
                value = value.get(part)
            else:
                return None
        
        return value

    def _map_value_to_range(
        self,
        value: float,
        min_value: float,
        max_value: float,
        min_result: float,
        max_result: float
    ) -> float:
        """Map a value from one range to another"""
        # Ensure value is within bounds
        value = max(min_value, min(value, max_value))
        
        # Calculate mapped value
        normalized = (value - min_value) / (max_value - min_value) if max_value > min_value else 0
        result = min_result + normalized * (max_result - min_result)
        
        return result
