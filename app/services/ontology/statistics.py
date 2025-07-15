from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from fastapi import status as http_status

from .base import BaseOntologyService


class OntologyStatisticsService(BaseOntologyService):
    """Service for ontology statistics and metrics"""

    async def get_mapping_stats(
        self, domain_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Get mapping statistics"""
        try:
            supabase = await self.get_supabase()

            # Entity mapping stats
            entity_query = supabase.from_("entity_mappings").select(
                "mapping_status, is_verified, auto_mapped"
            )
            if domain_ids:
                # Join with ontology classes and their domain associations
                entity_query = entity_query.select(
                    "mapping_status, is_verified, auto_mapped, ontology_classes!inner(domain_ontology_classes!inner(domain_id))"
                ).in_("ontology_classes.domain_ontology_classes.domain_id", domain_ids)

            entity_response = await entity_query.execute()

            # Relationship mapping stats
            relationship_query = supabase.from_("relationship_mappings").select(
                "mapping_status, is_verified, auto_mapped"
            )
            if domain_ids:
                # Join with ontology properties and their domain associations
                relationship_query = relationship_query.select(
                    "mapping_status, is_verified, auto_mapped, ontology_properties!inner(domain_ontology_properties!inner(domain_id))"
                ).in_(
                    "ontology_properties.domain_ontology_properties.domain_id",
                    domain_ids,
                )

            relationship_response = await relationship_query.execute()

            # Calculate stats
            def calc_stats(data):
                total = len(data)
                verified = len([item for item in data if item["is_verified"]])
                pending = len(
                    [item for item in data if item["mapping_status"] == "pending"]
                )
                mapped = len(
                    [item for item in data if item["mapping_status"] == "mapped"]
                )
                rejected = len(
                    [item for item in data if item["mapping_status"] == "rejected"]
                )
                needs_review = len(
                    [item for item in data if item["mapping_status"] == "needs_review"]
                )
                auto_mapped = len([item for item in data if item["auto_mapped"]])

                return {
                    "total": total,
                    "verified": verified,
                    "pending": pending,
                    "mapped": mapped,
                    "rejected": rejected,
                    "needs_review": needs_review,
                    "auto_mapped": auto_mapped,
                }

            return {
                "entity_mappings": calc_stats(entity_response.data),
                "relationship_mappings": calc_stats(relationship_response.data),
            }

        except Exception as e:
            self.logger.error(f"Error getting mapping stats: {e}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting mapping stats: {str(e)}",
            )

    async def get_ontology_statistics(self) -> Dict[str, Any]:
        """Get statistics about the loaded ontology"""
        try:
            supabase = await self.get_supabase()

            # Count classes by domain
            classes_response = (
                await supabase.from_("ontology_classes")
                .select("domain, is_custom")
                .execute()
            )

            class_stats = {}
            custom_class_count = 0
            for cls in classes_response.data:
                domain = cls.get("domain", "unknown")
                class_stats[domain] = class_stats.get(domain, 0) + 1
                if cls.get("is_custom"):
                    custom_class_count += 1

            # Count properties by domain
            properties_response = (
                await supabase.from_("ontology_properties")
                .select("domain, is_custom")
                .execute()
            )

            property_stats = {}
            custom_property_count = 0
            for prop in properties_response.data:
                domain = prop.get("domain", "unknown")
                property_stats[domain] = property_stats.get(domain, 0) + 1
                if prop.get("is_custom"):
                    custom_property_count += 1

            return {
                "total_classes": len(classes_response.data),
                "total_properties": len(properties_response.data),
                "custom_classes": custom_class_count,
                "custom_properties": custom_property_count,
                "classes_by_domain": class_stats,
                "properties_by_domain": property_stats,
                "domains": list(
                    set(list(class_stats.keys()) + list(property_stats.keys()))
                ),
            }

        except Exception as e:
            self.logger.error(f"Error getting ontology statistics: {e}")
            return {}
