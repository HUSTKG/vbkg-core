import logging
from abc import ABC

from app.core.config import settings
from app.core.supabase import get_supabase


class BaseVisualizationService(ABC):
    """Base service for all visualization operations"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._graph = None

    async def get_supabase(self):
        return await get_supabase()

    @property
    def graph(self):
        """Lazy initialization of Neo4j connection"""
        if self._graph is None:
            from py2neo import Graph

            self._graph = Graph(
                settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
        return self._graph
