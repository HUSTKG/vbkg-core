from .base import BaseOntologyService


class DomainIntegrationService(BaseOntologyService):
    """Service for domain integration helper methods"""

    async def associate_class_with_domain(
        self, class_id: int, domain_id: int, is_primary: bool = False
    ) -> None:
        """Associate an ontology class with a domain"""
        try:
            supabase = await self.get_supabase()

            # Check if association already exists
            existing = (
                await supabase.from_("domain_ontology_classes")
                .select("*")
                .eq("ontology_class_id", class_id)
                .eq("domain_id", domain_id)
                .execute()
            )

            if not existing.data:
                await supabase.from_("domain_ontology_classes").insert(
                    {
                        "ontology_class_id": class_id,
                        "domain_id": domain_id,
                        "is_primary": is_primary,
                        "domain_specific_config": {},
                    }
                ).execute()

        except Exception as e:
            self.logger.warning(
                f"Error associating class {class_id} with domain {domain_id}: {e}"
            )

    async def associate_property_with_domain(
        self, property_id: int, domain_id: int, is_primary: bool = False
    ) -> None:
        """Associate an ontology property with a domain"""
        try:
            supabase = await self.get_supabase()

            # Check if association already exists
            existing = (
                await supabase.from_("domain_ontology_properties")
                .select("*")
                .eq("ontology_property_id", property_id)
                .eq("domain_id", domain_id)
                .execute()
            )

            if not existing.data:
                await supabase.from_("domain_ontology_properties").insert(
                    {
                        "ontology_property_id": property_id,
                        "domain_id": domain_id,
                        "is_primary": is_primary,
                        "domain_specific_config": {},
                    }
                ).execute()

        except Exception as e:
            self.logger.warning(
                f"Error associating property {property_id} with domain {domain_id}: {e}"
            )
