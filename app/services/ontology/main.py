import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse

from app.schemas.ontology import (EntityMappingCreate, EntityMappingUpdate,
                                  OntologyClassCreate, OntologyClassUpdate,
                                  OntologyPropertyCreate,
                                  OntologyPropertyUpdate,
                                  RelationshipMappingCreate,
                                  RelationshipMappingUpdate)
from app.services.user import UserService

from .class_management import OntologyClassService
from .domain_integration import DomainIntegrationService
from .entity_mapping import EntityMappingService
from .property_management import OntologyPropertyService
from .relationship_mapping import RelationshipMappingService
from .statistics import OntologyStatisticsService
from .vietnamese_mapping import VietnameseMappingService

logger = logging.getLogger(__name__)


class OntologyService:
    """Main facade service for all ontology operations"""

    def __init__(self):
        self.class_service = OntologyClassService()
        self.property_service = OntologyPropertyService()
        self.entity_mapping_service = EntityMappingService()
        self.relationship_mapping_service = RelationshipMappingService()
        self.domain_service = DomainIntegrationService()
        self.vietnamese_service = VietnameseMappingService()
        self.statistics_service = OntologyStatisticsService()
        self.user_service = UserService()

    # Ontology Class Operations - delegate to ClassService
    async def get_ontology_class(self, class_id: int) -> Dict[str, Any]:
        return await self.class_service.get_ontology_class(class_id)

    async def get_ontology_class_by_uri(self, uri: str) -> Dict[str, Any]:
        return await self.class_service.get_ontology_class_by_uri(uri)

    async def create_ontology_class(
        self, ontology_class_in: OntologyClassCreate, domain_id: Optional[int] = None
    ) -> Dict[str, Any]:
        return await self.class_service.create_ontology_class(
            ontology_class_in, domain_id
        )

    async def update_ontology_class(
        self, class_id: int, ontology_class_in: OntologyClassUpdate
    ) -> Dict[str, Any]:
        return await self.class_service.update_ontology_class(
            class_id, ontology_class_in
        )

    async def delete_ontology_class(self, class_id: int) -> Dict[str, Any]:
        return await self.class_service.delete_ontology_class(class_id)

    async def get_ontology_classes(self, **kwargs) -> APIResponse[Dict[str, Any]]:
        return await self.class_service.get_ontology_classes(**kwargs)

    async def get_class_hierarchy(
        self, class_id: int, max_depth: int = 5
    ) -> Dict[str, Any]:
        return await self.class_service.get_class_hierarchy(class_id, max_depth)

    # Ontology Property Operations - delegate to PropertyService
    async def get_ontology_property(self, property_id: int) -> Dict[str, Any]:
        return await self.property_service.get_ontology_property(property_id)

    async def get_ontology_property_by_uri(self, uri: str) -> Dict[str, Any]:
        return await self.property_service.get_ontology_property_by_uri(uri)

    async def create_ontology_property(
        self,
        ontology_property_in: OntologyPropertyCreate,
        domain_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await self.property_service.create_ontology_property(
            ontology_property_in, domain_id
        )

    async def update_ontology_property(
        self, property_id: int, ontology_property_in: OntologyPropertyUpdate
    ) -> Dict[str, Any]:
        return await self.property_service.update_ontology_property(
            property_id, ontology_property_in
        )

    async def delete_ontology_property(self, property_id: int) -> Dict[str, Any]:
        return await self.property_service.delete_ontology_property(property_id)

    async def get_ontology_properties(self, **kwargs) -> APIResponse[Dict[str, Any]]:
        return await self.property_service.get_ontology_properties(**kwargs)

    async def get_properties_by_type(
        self, property_type: str, domain: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        return await self.property_service.get_properties_by_type(
            property_type, domain, limit
        )

    # Entity Mapping Operations - delegate to EntityMappingService
    async def get_entity_mappings(self, **kwargs) -> APIResponse[Dict[str, Any]]:
        return await self.entity_mapping_service.get_entity_mappings(**kwargs)

    async def create_entity_mapping(
        self, mapping: EntityMappingCreate, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.entity_mapping_service.create_entity_mapping(mapping, user_id)

    async def update_entity_mapping(
        self, mapping_id: str, mapping: EntityMappingUpdate
    ) -> Dict[str, Any]:
        return await self.entity_mapping_service.update_entity_mapping(
            mapping_id, mapping
        )

    async def delete_entity_mapping(self, mapping_id: str) -> Dict[str, Any]:
        return await self.entity_mapping_service.delete_entity_mapping(mapping_id)

    async def verify_entity_mapping(
        self, mapping_id: str, verified: bool, user_id: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.entity_mapping_service.verify_entity_mapping(
            mapping_id, verified, user_id, notes
        )

    # Relationship Mapping Operations - delegate to RelationshipMappingService
    async def get_relationship_mappings(self, **kwargs) -> APIResponse[Dict[str, Any]]:
        return await self.relationship_mapping_service.get_relationship_mappings(
            **kwargs
        )

    async def create_relationship_mapping(
        self, mapping: RelationshipMappingCreate, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.relationship_mapping_service.create_relationship_mapping(
            mapping, user_id
        )

    async def update_relationship_mapping(
        self, mapping_id: str, mapping: RelationshipMappingUpdate
    ) -> Dict[str, Any]:
        return await self.relationship_mapping_service.update_relationship_mapping(
            mapping_id, mapping
        )

    async def delete_relationship_mapping(self, mapping_id: str) -> Dict[str, Any]:
        return await self.relationship_mapping_service.delete_relationship_mapping(
            mapping_id
        )

    async def verify_relationship_mapping(
        self, mapping_id: str, verified: bool, user_id: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.relationship_mapping_service.verify_relationship_mapping(
            mapping_id, verified, user_id, notes
        )

    # Statistics - delegate to StatisticsService
    async def get_mapping_stats(
        self, domain_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        return await self.statistics_service.get_mapping_stats(domain_ids)

    async def get_ontology_statistics(self) -> Dict[str, Any]:
        return await self.statistics_service.get_ontology_statistics()

    # Bulk Operations
    async def bulk_create_entity_mappings(
        self, mappings: List[EntityMappingCreate], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Bulk create entity mappings"""
        try:
            success_count = 0
            failed_count = 0
            errors = []

            for mapping in mappings:
                try:
                    await self.entity_mapping_service.create_entity_mapping(
                        mapping, user_id
                    )
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(str(e))

            return {
                "success": success_count,
                "failed": failed_count,
                "errors": errors if errors else None,
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error bulk creating entity mappings: {str(e)}",
            )

    async def bulk_create_relationship_mappings(
        self, mappings: List[RelationshipMappingCreate], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Bulk create relationship mappings"""
        try:
            success_count = 0
            failed_count = 0
            errors = []

            for mapping in mappings:
                try:
                    await self.relationship_mapping_service.create_relationship_mapping(
                        mapping, user_id
                    )
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(str(e))

            return {
                "success": success_count,
                "failed": failed_count,
                "errors": errors if errors else None,
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error bulk creating relationship mappings: {str(e)}",
            )

    async def apply_entity_mapping_suggestion(
        self, mapping_id: str, suggestion_index: int, user_id: str
    ) -> Dict[str, Any]:
        """Apply AI suggestion for entity mapping"""
        try:
            from app.core.supabase import get_supabase

            # Get the entity mapping service instance
            supabase = await get_supabase()
            # Get current mapping
            current_mapping = (
                await supabase.from_("entity_mappings")
                .select("*")
                .eq("id", mapping_id)
                .maybe_single()
                .execute()
            )

            if not current_mapping:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity mapping not found",
                )

            # Get suggestions
            suggestions = current_mapping.data.get("suggestions", [])
            if suggestion_index >= len(suggestions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid suggestion index",
                )

            selected_suggestion = suggestions[suggestion_index]

            # Handle new class creation if needed
            ontology_class_id = selected_suggestion.get("suggested_class")

            if selected_suggestion.get("is_new_class", False):
                # Create new ontology class
                new_class_data = OntologyClassCreate(
                    uri=f"custom:{selected_suggestion.get('suggested_class')}",
                    label=selected_suggestion.get("suggested_class"),
                    description=f"Auto-generated class from AI suggestion: {selected_suggestion.get('reasoning', '')}",
                    is_custom=True,
                )

                # Create the new class
                new_class = await self.class_service.create_ontology_class(
                    new_class_data
                )
                ontology_class_id = new_class["id"]

                # Update the suggestion to reflect the new class ID for future reference
                selected_suggestion["suggested_class"] = ontology_class_id
                selected_suggestion["was_created"] = True

            # Apply the suggestion
            update_data = EntityMappingUpdate(
                ontology_class_id=ontology_class_id,
                mapping_status="mapped",
                confidence=selected_suggestion.get("confidence", 0.0),
                mapping_notes=f"Applied AI suggestion: {selected_suggestion.get('reasoning', '')}",
            )

            # Update the mapping
            updated_mapping = await self.entity_mapping_service.update_entity_mapping(
                mapping_id, update_data
            )

            # If high confidence, auto-verify
            if selected_suggestion.get("confidence", 0.0) >= 0.8:
                updated_mapping = (
                    await self.entity_mapping_service.verify_entity_mapping(
                        mapping_id,
                        True,
                        user_id,
                        "Auto-verified due to high confidence suggestion",
                    )
                )

            return updated_mapping

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error applying entity mapping suggestion: {str(e)}",
            )

    async def apply_relationship_mapping_suggestion(
        self, mapping_id: str, suggestion_index: int, user_id: str
    ) -> Dict[str, Any]:
        """Apply AI suggestion for relationship mapping"""
        try:
            # Get current mapping
            from app.core.supabase import get_supabase

            supabase = await get_supabase()
            current_mapping = (
                await supabase.from_("relationship_mappings")
                .select("*")
                .eq("id", mapping_id)
                .maybe_single()
                .execute()
            )

            if not current_mapping:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship mapping not found",
                )

            # Get suggestions
            suggestions = current_mapping.data.get("suggestions", [])
            if suggestion_index >= len(suggestions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid suggestion index",
                )

            selected_suggestion = suggestions[suggestion_index]

            # Handle new property creation if needed
            ontology_property_id = selected_suggestion.get("suggested_property")

            if selected_suggestion.get("is_new_property", False):
                # Create new ontology property
                new_property_data = OntologyPropertyCreate(
                    uri=f"custom:{selected_suggestion.get('suggested_property')}",
                    label=selected_suggestion.get("suggested_property"),
                    description=f"Auto-generated property from AI suggestion: {selected_suggestion.get('reasoning', '')}",
                    property_type="object",  # Default to object property, could be made configurable
                    is_custom=True,
                )

                # Create the new property
                new_property = await self.property_service.create_ontology_property(
                    new_property_data
                )
                ontology_property_id = new_property["id"]

                # Update the suggestion to reflect the new property ID for future reference
                selected_suggestion["suggested_property"] = ontology_property_id
                selected_suggestion["was_created"] = True

            # Apply the suggestion
            update_data = RelationshipMappingUpdate(
                ontology_property_id=ontology_property_id,
                mapping_status="mapped",
                confidence=selected_suggestion.get("confidence", 0.0),
                mapping_notes=f"Applied AI suggestion: {selected_suggestion.get('reasoning', '')}",
            )

            # Update the mapping
            updated_mapping = (
                await self.relationship_mapping_service.update_relationship_mapping(
                    mapping_id, update_data
                )
            )

            # If high confidence, auto-verify
            if selected_suggestion.get("confidence", 0.0) >= 0.8:
                updated_mapping = (
                    await self.relationship_mapping_service.verify_relationship_mapping(
                        mapping_id,
                        True,
                        user_id,
                        "Auto-verified due to high confidence suggestion",
                    )
                )

            return updated_mapping

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error applying relationship mapping suggestion: {str(e)}",
            )

    async def get_ontology_context_with_class_properties(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ontology context với class-specific datatype properties mapping cho entity extraction
        """
        try:
            from app.core.supabase import get_supabase

            supabase = await get_supabase()

            # Get ontology classes
            classes_query = supabase.from_("ontology_classes").select("*")
            if domain:
                classes_query = classes_query.eq("domain", domain)

            classes_response = await classes_query.execute()

            classes = {}
            class_datatype_properties = {}

            for cls in classes_response.data:
                classes[cls["id"]] = cls

                # Get datatype properties cho từng class
                datatype_props_query = (
                    supabase.from_("ontology_properties")
                    .select("*")
                    .eq("domain_class_id", cls["id"])
                    .eq("property_type", "datatype")
                )

                datatype_props_response = await datatype_props_query.execute()
                class_datatype_properties[cls["id"]] = datatype_props_response.data

            # Get all properties for general reference
            properties_query = supabase.from_("ontology_properties").select("*")
            if domain:
                properties_query = properties_query.eq("domain", domain)

            properties_response = await properties_query.execute()

            properties = {}
            for prop in properties_response.data:
                properties[prop["id"]] = prop

            return {
                "classes": classes,
                "properties": properties,
                "class_datatype_properties": class_datatype_properties,
            }

        except Exception as e:
            logger.error(f"Error getting ontology context with class properties: {e}")
            return {"classes": {}, "properties": {}, "class_datatype_properties": {}}

    async def get_object_properties_context(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ONLY object properties context cho relationship extraction
        """
        try:
            from app.core.supabase import get_supabase

            supabase = await get_supabase()

            # Get ontology classes
            classes_query = supabase.from_("ontology_classes").select("*")
            if domain:
                classes_query = classes_query.eq("domain", domain)

            classes_response = await classes_query.execute()

            classes = {}
            for cls in classes_response.data:
                classes[cls["id"]] = cls

            # Get ONLY object properties
            object_props_query = (
                supabase.from_("ontology_properties")
                .select("*")
                .eq("property_type", "object")
            )
            if domain:
                object_props_query = object_props_query.eq("domain", domain)

            object_props_response = await object_props_query.execute()

            object_properties = {}
            for prop in object_props_response.data:
                object_properties[prop["id"]] = prop

            return {"classes": classes, "object_properties": object_properties}

        except Exception as e:
            logger.error(f"Error getting object properties context: {e}")
            return {"classes": {}, "object_properties": {}}
