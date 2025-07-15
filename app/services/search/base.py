import logging
from typing import Any, Dict, List, Optional

from py2neo import Graph, NodeMatcher, RelationshipMatcher

from app.core.config import settings
from app.core.supabase import get_supabase
from app.utils.personrank import PersonRankCalculator

logger = logging.getLogger(__name__)


class BaseSearchService:
    """Base class for all search services with common functionality"""
    
    def __init__(self):
        # Connect to Neo4j database
        self.graph = Graph(
            settings.NEO4J_URI, auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        self.node_matcher = NodeMatcher(self.graph)
        self.rel_matcher = RelationshipMatcher(self.graph)

        # Initialize OpenAI for embeddings if API key is available
        self.openai_available = False
        if settings.OPENAI_API_KEY:
            from openai import AsyncOpenAI
            self.aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.openai_available = True

        # Initialize PersonRank calculator
        self.personrank_calculator = PersonRankCalculator()

    def _validate_entity_types(self, entity_types: Optional[List[str]]) -> List[str]:
        """Validate and clean entity types list"""
        if not entity_types:
            return []

        # Filter out None, empty strings, and whitespace-only strings
        valid_types = []
        for entity_type in entity_types:
            if entity_type and isinstance(entity_type, str) and entity_type.strip():
                valid_types.append(entity_type.strip())

        return valid_types

    def _convert_neo4j_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Neo4j properties, handling DateTime objects"""
        converted = {}

        for key, value in properties.items():
            if hasattr(value, "__class__") and "DateTime" in str(value.__class__):
                # Convert Neo4j DateTime to ISO string
                if hasattr(value, "isoformat"):
                    converted[key] = value.isoformat()
                else:
                    converted[key] = str(value)
            elif hasattr(value, "strftime"):
                # Handle standard datetime
                converted[key] = value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            elif isinstance(value, (list, tuple)):
                # Handle lists that might contain DateTime
                converted[key] = [
                    (
                        item.isoformat()
                        if hasattr(item, "isoformat")
                        else (
                            str(item)
                            if hasattr(item, "__class__")
                            and "DateTime" in str(item.__class__)
                            else item
                        )
                    )
                    for item in value
                ]
            elif isinstance(value, dict):
                # Recursive for nested dicts
                converted[key] = self._convert_neo4j_properties(value)
            else:
                converted[key] = value

        return converted

    async def get_supabase_client(self):
        """Get Supabase client instance"""
        return await get_supabase()

    def _create_entity_search_result(self, node, score: float = 1.0, ontology_class=None):
        """Create EntitySearchResult from Neo4j node"""
        from app.schemas.search import EntitySearchResult

        # Extract properties
        raw_properties = dict(node)
        properties = self._convert_neo4j_properties(raw_properties)

        # Remove standard fields from properties
        for field in ["entity_id", "entity_text", "entity_type", "ontology_class"]:
            if field in properties:
                properties.pop(field)

        return EntitySearchResult(
            id=node.get("entity_id", str(node.identity)),
            text=node.get("entity_text", ""),
            type=node.get("entity_type", "Unknown"),
            properties=properties,
            ontology_class=ontology_class or node.get("ontology_class"),
            score=score,
            relationships=None,
            similar_entities=None,
        )

    def _build_entity_type_filter(self, entity_types: List[str]) -> str:
        """Build entity type filter for Cypher queries"""
        if not entity_types:
            return ""
        
        entity_type_conditions = [f"n:{entity_type}" for entity_type in entity_types]
        return f"AND ({' OR '.join(entity_type_conditions)}) "

    def _build_filter_conditions(self, filters) -> str:
        """Build filter conditions for Cypher queries"""
        if not filters:
            return ""
        
        conditions = []
        for filter_item in filters:
            field = filter_item.field
            operator = filter_item.operator
            value = filter_item.value
            
            if operator == "eq":
                conditions.append(f"n.{field} = '{value}'")
            elif operator == "gt":
                conditions.append(f"n.{field} > {value}")
            elif operator == "lt":
                conditions.append(f"n.{field} < {value}")
            elif operator == "gte":
                conditions.append(f"n.{field} >= {value}")
            elif operator == "lte":
                conditions.append(f"n.{field} <= {value}")
            elif operator == "contains":
                conditions.append(f"n.{field} CONTAINS '{value}'")
            elif operator == "in":
                values = [f"'{v}'" for v in value]
                conditions.append(f"n.{field} IN [{', '.join(values)}]")
        
        return "AND " + " AND ".join(conditions) + " " if conditions else ""

    def _build_sort_conditions(self, sort_params) -> str:
        """Build sort conditions for Cypher queries"""
        if not sort_params:
            return ""
        
        from app.schemas.search import SortOrder
        
        sort_conditions = []
        for sort_item in sort_params:
            direction = "ASC" if sort_item.order == SortOrder.ASC else "DESC"
            sort_conditions.append(f"n.{sort_item.field} {direction}")
        
        return "ORDER BY " + ", ".join(sort_conditions) + " " if sort_conditions else ""
