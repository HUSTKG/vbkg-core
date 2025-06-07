import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from postgrest.types import CountMethod

from app.core.supabase import get_supabase
from app.services.user import UserService

logger = logging.getLogger(__name__)


class DomainService:
    """Service for managing domains, entity types, and relationship types"""

    def __init__(self):
        self.user_service = UserService()

    # =============================================
    # DOMAIN OPERATIONS
    # =============================================

    async def create_domain(
        self, domain_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Create a new domain"""

        supabase = await get_supabase()

        # Check if domain name already exists
        existing = (
            await supabase.table("domains")
            .select("id")
            .eq("name", domain_data["name"])
            .execute()
        )

        if existing.data:
            raise ValueError(f"Domain '{domain_data['name']}' already exists")

        # Create domain
        domain_data["created_by"] = user_id
        response = await supabase.table("domains").insert(domain_data).execute()

        await self.user_service._log_user_activity(
            user_id,
            "create_domain",
            f"Created domain '{domain_data['name']}'",
            resource_id=response.data[0]["id"],
        )

        return response.data[0]

    async def get_domain(
        self, domain_id: int, include_types: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get domain by ID with optional entity/relationship types"""

        supabase = await get_supabase()

        # Get domain
        response = (
            await supabase.table("domains")
            .select("*")
            .eq("id", domain_id)
            .single()
            .execute()
        )

        if not response.data:
            return None

        domain = response.data

        if include_types:
            # Get entity types for this domain
            entity_types = await self._get_domain_entity_types(domain_id)
            domain["entity_types"] = entity_types

            # Get relationship types for this domain
            relationship_types = await self._get_domain_relationship_types(domain_id)
            domain["relationship_types"] = relationship_types

            # Get domain statistics
            stats = await self.get_domain_stats(domain_id)
            domain["stats"] = stats

        return domain

    async def update_domain(
        self, domain_id: int, update_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Update domain"""

        supabase = await get_supabase()

        # Check if domain exists
        existing = await self.get_domain(domain_id)
        if not existing:
            raise ValueError("Domain not found")

        # Update domain
        response = (
            await supabase.table("domains")
            .update(update_data)
            .eq("id", domain_id)
            .execute()
        )

        await self.user_service._log_user_activity(
            user_id,
            "update_domain",
            f"Updated domain '{existing['name']}'",
            resource_id=str(domain_id),
        )

        return response.data[0]

    async def delete_domain(self, domain_id: int, user_id: str) -> bool:
        """Soft delete domain"""

        supabase = await get_supabase()

        # Check if domain has associated types
        entity_count = (
            await supabase.table("entity_type_domains")
            .select("*", count="exact")
            .eq("domain_id", domain_id)
            .execute()
        )

        relationship_count = (
            await supabase.table("relationship_type_domains")
            .select("*", count="exact")
            .eq("domain_id", domain_id)
            .execute()
        )

        if entity_count.count > 0 or relationship_count.count > 0:
            # Soft delete - mark as inactive
            await supabase.table("domains").update({"is_active": False}).eq(
                "id", domain_id
            ).execute()
        else:
            # Hard delete if no associations
            await supabase.table("domains").delete().eq("id", domain_id).execute()

        await self.user_service._log_user_activity(
            user_id,
            "delete_domain",
            f"Deleted domain with ID {domain_id}",
            resource_id=str(domain_id),
        )

        return True

    async def search_domains(
        self,
        query: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Search domains"""

        supabase = await get_supabase()

        # Build query
        db_query = supabase.table("domains").select("*")

        if is_active is not None:
            db_query = db_query.eq("is_active", is_active)

        if query:
            db_query = db_query.or_(
                f"name.ilike.%{query}%,display_name.ilike.%{query}%,description.ilike.%{query}%"
            )

        # Execute with pagination
        response = (
            await db_query.order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        # Get total count
        count_query = supabase.table("domains").select("*", count=CountMethod.exact)
        if is_active is not None:
            count_query = count_query.eq("is_active", is_active)
        if query:
            count_query = count_query.or_(
                f"name.ilike.%{query}%,display_name.ilike.%{query}%,description.ilike.%{query}%"
            )

        count_response = await count_query.execute()

        return {
            "domains": response.data,
            "total": count_response.count,
            "limit": limit,
            "skip": skip,
            "has_more": (skip + limit) < count_response.count,
        }

    # =============================================
    # ENTITY TYPE OPERATIONS
    # =============================================

    async def create_entity_type(
        self, type_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Create a new entity type"""

        supabase = await get_supabase()

        # Check if entity type name already exists
        existing = (
            await supabase.table("entity_types")
            .select("id")
            .eq("name", type_data["name"])
            .execute()
        )

        if existing.data:
            raise ValueError(f"Entity type '{type_data['name']}' already exists")

        # Extract domain mappings
        domain_ids = type_data.pop("domain_ids", [])
        primary_domain_id = type_data.pop("primary_domain_id", None)

        # Create entity type
        type_data["created_by"] = user_id
        response = await supabase.table("entity_types").insert(type_data).execute()

        entity_type = response.data[0]
        entity_type_id = entity_type["id"]

        # Create domain mappings
        if domain_ids:
            await self._create_entity_type_domain_mappings(
                entity_type_id, domain_ids, primary_domain_id
            )

        await self.user_service._log_user_activity(
            user_id,
            "create_entity_type",
            f"Created entity type '{type_data['name']}'",
            resource_id=entity_type_id,
        )

        return entity_type

    async def get_entity_type(
        self, type_id: int, include_domains: bool = False, include_usage: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get entity type by ID"""

        supabase = await get_supabase()

        response = (
            await supabase.table("entity_types")
            .select("*")
            .eq("id", type_id)
            .single()
            .execute()
        )

        if not response.data:
            return None

        entity_type = response.data

        if include_domains:
            domains = await self._get_entity_type_domains(type_id)
            entity_type["domains"] = domains

        if include_usage:
            usage_count = await self._get_entity_type_usage(type_id)
            entity_type["usage_count"] = usage_count

        return entity_type

    async def update_entity_type(
        self, type_id: int, update_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Update entity type"""

        supabase = await get_supabase()

        # Check if entity type exists
        existing = await self.get_entity_type(type_id)
        if not existing:
            raise ValueError("Entity type not found")

        # Update entity type
        response = (
            await supabase.table("entity_types")
            .update(update_data)
            .eq("id", type_id)
            .execute()
        )

        await self.user_service._log_user_activity(
            user_id,
            "update_entity_type",
            f"Updated entity type '{existing['name']}'",
            resource_id=str(type_id),
        )

        return response.data[0]

    async def delete_entity_type(self, type_id: int, user_id: str) -> bool:
        """Delete entity type"""

        supabase = await get_supabase()

        # Check usage in knowledge graph
        usage_count = await self._get_entity_type_usage(type_id)

        if usage_count > 0:
            # Soft delete - mark as inactive
            await supabase.table("entity_types").update({"is_active": False}).eq(
                "id", type_id
            ).execute()
        else:
            # Hard delete if not used
            await supabase.table("entity_types").delete().eq("id", type_id).execute()

        return True

    async def search_entity_types(
        self,
        query: Optional[str] = None,
        domain_ids: Optional[List[int]] = None,
        is_active: Optional[bool] = None,
        is_mapped: Optional[bool] = None,
        include_usage: bool = False,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Search entity types"""

        supabase = await get_supabase()

        # Build base query
        if domain_ids:
            # Join with domain mappings if filtering by domain
            db_query = (
                supabase.table("entity_types")
                .select("*, entity_type_domains!inner(domain_id)")
                .in_("entity_type_domains.domain_id", domain_ids)
            )
        else:
            db_query = supabase.table("entity_types").select("*")

        if is_active is not None:
            db_query = db_query.eq("is_active", is_active)

        if is_mapped is not None:
            # return only types that are mapped to domains
            if is_mapped:
                db_query = db_query.eq("is_mapped", True)
            else:
                db_query = db_query.eq("is_mapped", False)

        if query:
            db_query = db_query.or_(
                f"name.ilike.%{query}%,display_name.ilike.%{query}%,description.ilike.%{query}%"
            )

        # Execute with pagination
        response = (
            await db_query.order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        # Add domains and usage info
        for entity_type in response.data:
            # Get domains
            domains = await self._get_entity_type_domains(entity_type["id"])
            entity_type["domains"] = domains

            # Get usage if requested
            if include_usage:
                usage_count = await self._get_entity_type_usage(entity_type["id"])
                entity_type["usage_count"] = usage_count

        # Get total count
        count_query = supabase.table("entity_types").select("*", count="exact")
        if domain_ids:
            count_query = count_query.select(
                "*, entity_type_domains!inner(domain_id)", count="exact"
            ).in_("entity_type_domains.domain_id", domain_ids)
        if is_active is not None:
            count_query = count_query.eq("is_active", is_active)
        if query:
            count_query = count_query.or_(
                f"name.ilike.%{query}%,display_name.ilike.%{query}%,description.ilike.%{query}%"
            )

        count_response = await count_query.execute()

        return {
            "entity_types": response.data,
            "total": count_response.count,
            "limit": limit,
            "skip": skip,
            "has_more": (skip + limit) < count_response.count,
        }

    # =============================================
    # RELATIONSHIP TYPE OPERATIONS
    # =============================================

    async def create_relationship_type(
        self, type_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Create a new relationship type"""

        supabase = await get_supabase()

        # Check if relationship type name already exists
        existing = (
            await supabase.table("relationship_types")
            .select("id")
            .eq("name", type_data["name"])
            .execute()
        )

        if existing.data:
            raise ValueError(f"Relationship type '{type_data['name']}' already exists")

        # Extract domain mappings
        domain_ids = type_data.pop("domain_ids", [])
        primary_domain_id = type_data.pop("primary_domain_id", None)

        # Create relationship type
        type_data["created_by"] = user_id
        response = (
            await supabase.table("relationship_types").insert(type_data).execute()
        )

        relationship_type = response.data[0]
        relationship_type_id = relationship_type["id"]

        # Create domain mappings
        if domain_ids:
            await self._create_relationship_type_domain_mappings(
                relationship_type_id, domain_ids, primary_domain_id
            )

        await self.user_service._log_user_activity(
            user_id,
            "create_relationship_type",
            f"Created relationship type '{type_data['name']}'",
            resource_id=relationship_type_id,
        )

        return relationship_type

    async def get_relationship_type(
        self, type_id: int, include_domains: bool = False, include_usage: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get relationship type by ID"""

        supabase = await get_supabase()

        response = (
            await supabase.table("relationship_types")
            .select("*")
            .eq("id", type_id)
            .single()
            .execute()
        )

        if not response.data:
            return None

        relationship_type = response.data

        if include_domains:
            domains = await self._get_relationship_type_domains(type_id)
            relationship_type["domains"] = domains

        if include_usage:
            usage_count = await self._get_relationship_type_usage(type_id)
            relationship_type["usage_count"] = usage_count

        return relationship_type

    async def update_relationship_type(
        self, type_id: int, update_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Update relationship type"""

        supabase = await get_supabase()

        # Check if relationship type exists
        existing = await self.get_relationship_type(type_id)
        if not existing:
            raise ValueError("Relationship type not found")

        # Update relationship type
        response = (
            await supabase.table("relationship_types")
            .update(update_data)
            .eq("id", type_id)
            .execute()
        )

        await self.user_service._log_user_activity(
            user_id,
            "update_relationship_type",
            f"Updated relationship type '{existing['name']}'",
            resource_id=str(type_id),
        )

        return response.data[0]

    async def search_relationship_types(
        self,
        query: Optional[str] = None,
        domain_ids: Optional[List[int]] = None,
        source_entity_type_id: Optional[int] = None,
        target_entity_type_id: Optional[int] = None,
        is_mapped: Optional[bool] = None,
        is_bidirectional: Optional[bool] = None,
        is_active: Optional[bool] = None,
        include_usage: bool = False,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Search relationship types"""

        supabase = await get_supabase()

        # Build base query
        if domain_ids:
            db_query = (
                supabase.table("relationship_types")
                .select("*, relationship_type_domains!inner(domain_id)")
                .in_("relationship_type_domains.domain_id", domain_ids)
            )
        else:
            db_query = supabase.table("relationship_types").select("*")

        if is_active is not None:
            db_query = db_query.eq("is_active", is_active)

        if is_mapped is not None:
            # return only types that are mapped to domains
            if is_mapped:
                db_query = db_query.eq("is_mapped", True)
            else:
                db_query = db_query.eq("is_mapped", False)

        if is_bidirectional is not None:
            db_query = db_query.eq("is_bidirectional", is_bidirectional)

        if query:
            db_query = db_query.or_(
                f"name.ilike.%{query}%,display_name.ilike.%{query}%,description.ilike.%{query}%"
            )

        # Filter by source/target entity types (using array contains)
        if source_entity_type_id:
            db_query = db_query.contains("source_entity_types", [source_entity_type_id])

        if target_entity_type_id:
            db_query = db_query.contains("target_entity_types", [target_entity_type_id])

        # Execute with pagination
        response = (
            await db_query.order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        # Add domains and usage info
        for relationship_type in response.data:
            # Get domains
            domains = await self._get_relationship_type_domains(relationship_type["id"])
            relationship_type["domains"] = domains

            # Get usage if requested
            if include_usage:
                usage_count = await self._get_relationship_type_usage(
                    relationship_type["id"]
                )
                relationship_type["usage_count"] = usage_count

        # Get total count (simplified for now)
        count_response = (
            await supabase.table("relationship_types")
            .select("*", count="exact")
            .execute()
        )

        return {
            "relationship_types": response.data,
            "total": count_response.count,
            "limit": limit,
            "skip": skip,
            "has_more": (skip + limit) < count_response.count,
        }

    # =============================================
    # DOMAIN MAPPING OPERATIONS
    # =============================================

    async def add_entity_type_to_domain(
        self,
        type_id: int,
        domain_id: int,
        is_primary: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add entity type to domain"""

        supabase = await get_supabase()

        # Check if mapping already exists
        existing = (
            await supabase.table("entity_type_domains")
            .select("*")
            .eq("entity_type_id", type_id)
            .eq("domain_id", domain_id)
            .execute()
        )

        if existing.data:
            raise ValueError("Entity type already associated with this domain")

        # If this is primary, unset other primary mappings for this type
        if is_primary:
            await supabase.table("entity_type_domains").update(
                {"is_primary": False}
            ).eq("entity_type_id", type_id).execute()

        # Create mapping
        mapping_data = {
            "entity_type_id": type_id,
            "domain_id": domain_id,
            "is_primary": is_primary,
            "domain_specific_config": config or {},
        }

        response = (
            await supabase.table("entity_type_domains").insert(mapping_data).execute()
        )

        return response.data[0]

    async def remove_entity_type_from_domain(
        self, type_id: int, domain_id: int
    ) -> bool:
        """Remove entity type from domain"""

        supabase = await get_supabase()

        await supabase.table("entity_type_domains").delete().eq(
            "entity_type_id", type_id
        ).eq("domain_id", domain_id).execute()

        return True

    async def add_relationship_type_to_domain(
        self,
        type_id: int,
        domain_id: int,
        is_primary: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add relationship type to domain"""

        supabase = await get_supabase()

        # Check if mapping already exists
        existing = (
            await supabase.table("relationship_type_domains")
            .select("*")
            .eq("relationship_type_id", type_id)
            .eq("domain_id", domain_id)
            .execute()
        )

        if existing.data:
            raise ValueError("Relationship type already associated with this domain")

        # If this is primary, unset other primary mappings for this type
        if is_primary:
            await supabase.table("relationship_type_domains").update(
                {"is_primary": False}
            ).eq("relationship_type_id", type_id).execute()

        # Create mapping
        mapping_data = {
            "relationship_type_id": type_id,
            "domain_id": domain_id,
            "is_primary": is_primary,
            "domain_specific_config": config or {},
        }

        response = (
            await supabase.table("relationship_type_domains")
            .insert(mapping_data)
            .execute()
        )

        return response.data[0]

    # =============================================
    # STATISTICS & ANALYTICS
    # =============================================

    async def get_domain_stats(self, domain_id: int) -> Dict[str, Any]:
        """Get statistics for a domain"""

        supabase = await get_supabase()

        # Count entity types
        entity_types_count = (
            await supabase.table("entity_type_domains")
            .select("*", count=CountMethod.exact)
            .eq("domain_id", domain_id)
            .execute()
        ).count

        # Count relationship types
        relationship_types_count = (
            await supabase.table("relationship_type_domains")
            .select("*", count=CountMethod.exact)
            .eq("domain_id", domain_id)
            .execute()
        ).count

        # Count actual entities and relationships in KG
        # This would require complex queries joining with kg_entities/kg_relationships
        # For now, returning basic counts

        return {
            "domain_id": domain_id,
            "entity_types_count": entity_types_count,
            "relationship_types_count": relationship_types_count,
            "entities_count": 0,  # TODO: Implement KG counting
            "relationships_count": 0,  # TODO: Implement KG counting
            "last_updated": datetime.now(),
        }

    async def validate_relationship_type_constraints(
        self,
        relationship_type_id: int,
        source_entity_type_id: int,
        target_entity_type_id: int,
    ) -> Dict[str, Any]:
        """Validate if entity types are allowed for relationship type"""

        relationship_type = await self.get_relationship_type(relationship_type_id)

        if not relationship_type:
            return {"is_valid": False, "errors": ["Relationship type not found"]}

        errors = []
        warnings = []

        # Check source entity type constraints
        if relationship_type.get("source_entity_types"):
            if source_entity_type_id not in relationship_type["source_entity_types"]:
                errors.append(f"Source entity type {source_entity_type_id} not allowed")

        # Check target entity type constraints
        if relationship_type.get("target_entity_types"):
            if target_entity_type_id not in relationship_type["target_entity_types"]:
                errors.append(f"Target entity type {target_entity_type_id} not allowed")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # =============================================
    # HELPER METHODS
    # =============================================

    async def _get_domain_entity_types(self, domain_id: int) -> List[Dict[str, Any]]:
        """Get entity types for a domain"""

        supabase = await get_supabase()

        response = (
            await supabase.table("entity_types")
            .select("*, entity_type_domains!inner(is_primary, domain_specific_config)")
            .eq("entity_type_domains.domain_id", domain_id)
            .eq("is_active", True)
            .execute()
        )

        return response.data

    async def _get_domain_relationship_types(
        self, domain_id: int
    ) -> List[Dict[str, Any]]:
        """Get relationship types for a domain"""

        supabase = await get_supabase()

        response = (
            await supabase.table("relationship_types")
            .select(
                "*, relationship_type_domains!inner(is_primary, domain_specific_config)"
            )
            .eq("relationship_type_domains.domain_id", domain_id)
            .eq("is_active", True)
            .execute()
        )

        return response.data

    async def _get_entity_type_domains(self, type_id: int) -> List[Dict[str, Any]]:
        """Get domains for an entity type"""

        supabase = await get_supabase()

        response = (
            await supabase.table("domains")
            .select("*, entity_type_domains!inner(is_primary, domain_specific_config)")
            .eq("entity_type_domains.entity_type_id", type_id)
            .eq("is_active", True)
            .execute()
        )

        return response.data

    async def _get_relationship_type_domains(
        self, type_id: int
    ) -> List[Dict[str, Any]]:
        """Get domains for a relationship type"""

        supabase = await get_supabase()

        response = (
            await supabase.table("domains")
            .select(
                "*, relationship_type_domains!inner(is_primary, domain_specific_config)"
            )
            .eq("relationship_type_domains.relationship_type_id", type_id)
            .eq("is_active", True)
            .execute()
        )

        return response.data

    async def _get_entity_type_usage(self, type_id: int) -> int:
        """Get usage count of entity type in knowledge graph"""

        supabase = await get_supabase()

        response = (
            await supabase.table("kg_entities")
            .select("*", count="exact")
            .eq("entity_type_id", type_id)
            .execute()
        )

        return response.count

    async def _get_relationship_type_usage(self, type_id: int) -> int:
        """Get usage count of relationship type in knowledge graph"""

        supabase = await get_supabase()

        response = (
            await supabase.table("kg_relationships")
            .select("*", count="exact")
            .eq("relationship_type_id", type_id)
            .execute()
        )

        return response.count

    async def _create_entity_type_domain_mappings(
        self,
        type_id: int,
        domain_ids: List[int],
        primary_domain_id: Optional[int] = None,
    ) -> None:
        """Create domain mappings for entity type"""

        supabase = await get_supabase()

        mappings = []
        for domain_id in domain_ids:
            mappings.append(
                {
                    "entity_type_id": type_id,
                    "domain_id": domain_id,
                    "is_primary": domain_id == primary_domain_id,
                    "domain_specific_config": {},
                }
            )

        if mappings:
            await supabase.table("entity_type_domains").insert(mappings).execute()

    async def _create_relationship_type_domain_mappings(
        self,
        type_id: int,
        domain_ids: List[int],
        primary_domain_id: Optional[int] = None,
    ) -> None:
        """Create domain mappings for relationship type"""

        supabase = await get_supabase()

        mappings = []
        for domain_id in domain_ids:
            mappings.append(
                {
                    "relationship_type_id": type_id,
                    "domain_id": domain_id,
                    "is_primary": domain_id == primary_domain_id,
                    "domain_specific_config": {},
                }
            )

        if mappings:
            await supabase.table("relationship_type_domains").insert(mappings).execute()
