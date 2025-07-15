from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status

from .base import BaseVisualizationService


class VisualizationDataService(BaseVisualizationService):
    """Service for fetching visualization data from various sources"""

    async def fetch_visualization_data(
        self, visualization: Dict[str, Any], params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch data based on visualization configuration"""

        try:
            if visualization.get("cypher_query"):
                return await self._fetch_cypher_data(
                    visualization["cypher_query"], params
                )
            elif visualization.get("entity_id"):
                return await self._fetch_entity_data(
                    visualization["entity_id"], visualization.get("entity_type")
                )
            elif visualization.get("query_id"):
                return await self._fetch_query_data(visualization["query_id"], params)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No data source specified for visualization",
                )

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error fetching visualization data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching visualization data: {str(e)}",
            )

    async def _fetch_cypher_data(
        self, cypher_query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute Cypher query and return data"""

        query_params = params or {}

        try:
            data = self.graph.run(cypher_query, **query_params).data()
            return data
        except Exception as e:
            self.logger.error(f"Error executing Cypher query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing Cypher query: {str(e)}",
            )

    async def _fetch_entity_data(
        self, entity_id: str, entity_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get entity and its relationships for visualization"""

        try:
            # Build Cypher query to get entity and its relationships
            cypher_query = f"""
            MATCH (n {{entity_id: '{entity_id}'}})
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN n as source, r, m as target
            UNION
            MATCH (n {{entity_id: '{entity_id}'}})
            OPTIONAL MATCH (n)<-[r]-(m)
            RETURN m as source, r, n as target
            """

            # Execute query
            data = self.graph.run(cypher_query).data()
            return data

        except Exception as e:
            self.logger.error(f"Error getting entity visualization data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting entity visualization data: {str(e)}",
            )

    async def _fetch_query_data(
        self, query_id: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get data from saved query"""

        # TODO: Implement saved query execution
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Query-based visualization not implemented yet",
        )
