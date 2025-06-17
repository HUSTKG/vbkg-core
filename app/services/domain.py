import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from postgrest.types import CountMethod

from app.core.supabase import get_supabase
from app.services.user import UserService

logger = logging.getLogger(__name__)


class DomainService:
    """Service for managing domains and their ontology class/property associations"""

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

        # Extract ontology associations
        ontology_class_ids = domain_data.pop("ontology_class_ids", [])
        ontology_property_ids = domain_data.pop("ontology_property_ids", [])
        primary_ontology_class_id = domain_data.pop("primary_ontology_class_id", None)
        primary_ontology_property_id = domain_data.pop("primary_ontology_property_id", None)

        # Create domain
        domain_data["created_by"] = user_id
        response = await supabase.table("domains").insert(domain_data).execute()

        domain = response.data[0]
        domain_id = domain["id"]

        # Create ontology class associations
        if ontology_class_ids:
            await self._create_domain_ontology_class_mappings(
                domain_id, ontology_class_ids, primary_ontology_class_id
            )

        # Create ontology property associations
        if ontology_property_ids:
            await self._create_domain_ontology_property_mappings(
                domain_id, ontology_property_ids, primary_ontology_property_id
            )

        await self.user_service._log_user_activity(
            user_id,
            "create_domain",
            f"Created domain '{domain_data['name']}'",
            resource_id=domain_id,
        )

        return domain

    async def get_domain(
        self, domain_id: int, include_ontology: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get domain by ID with optional ontology classes/properties"""

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

        if include_ontology:
            # Get ontology classes for this domain
            ontology_classes = await self._get_domain_ontology_classes(domain_id)
            domain["ontology_classes"] = ontology_classes

            # Get ontology properties for this domain
            ontology_properties = await self._get_domain_ontology_properties(domain_id)
            domain["ontology_properties"] = ontology_properties

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

        # Check if domain has associated ontology classes/properties
        class_count = (
            await supabase.table("domain_ontology_classes")
            .select("*", count="exact")
            .eq("domain_id", domain_id)
            .execute()
        )

        property_count = (
            await supabase.table("domain_ontology_properties")
            .select("*", count="exact")
            .eq("domain_id", domain_id)
            .execute()
        )

        if class_count.count > 0 or property_count.count > 0:
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
        has_ontology_classes: Optional[bool] = None,
        has_ontology_properties: Optional[bool] = None,
        ontology_namespace: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Search domains"""

        supabase = await get_supabase()

        # Build query
        db_query = supabase.table("domains").select("*")

        if is_active is not None:
            db_query = db_query.eq("is_active", is_active)

        if ontology_namespace:
            db_query = db_query.eq("ontology_namespace", ontology_namespace)

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

        # Filter by ontology associations if needed
        filtered_domains = []
        for domain in response.data:
            include_domain = True
            
            if has_ontology_classes is not None:
                class_count = await self._get_domain_ontology_class_count(domain["id"])
                if has_ontology_classes and class_count == 0:
                    include_domain = False
                elif not has_ontology_classes and class_count > 0:
                    include_domain = False
            
            if has_ontology_properties is not None and include_domain:
                property_count = await self._get_domain_ontology_property_count(domain["id"])
                if has_ontology_properties and property_count == 0:
                    include_domain = False
                elif not has_ontology_properties and property_count > 0:
                    include_domain = False
            
            if include_domain:
                filtered_domains.append(domain)

        # Get total count
        count_query = supabase.table("domains").select("*", count=CountMethod.exact)
        if is_active is not None:
            count_query = count_query.eq("is_active", is_active)
        if ontology_namespace:
            count_query = count_query.eq("ontology_namespace", ontology_namespace)
        if query:
            count_query = count_query.or_(
                f"name.ilike.%{query}%,display_name.ilike.%{query}%,description.ilike.%{query}%"
            )

        count_response = await count_query.execute()

        return {
            "domains": filtered_domains,
            "total": len(filtered_domains),
            "limit": limit,
            "skip": skip,
            "has_more": (skip + limit) < len(filtered_domains),
        }

    # =============================================
    # ONTOLOGY CLASS OPERATIONS
    # =============================================

    async def get_ontology_classes_for_domain(
        self,
        domain_id: int,
        query: Optional[str] = None,
        is_mapped: Optional[bool] = None,
        is_custom: Optional[bool] = None,
        include_usage: bool = False,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Get ontology classes associated with a domain"""

        supabase = await get_supabase()

        # Build base query
        db_query = (
            supabase.table("ontology_classes")
            .select("*, domain_ontology_classes!inner(is_primary, domain_specific_config)")
            .eq("domain_ontology_classes.domain_id", domain_id)
        )

        if is_custom is not None:
            db_query = db_query.eq("is_custom", is_custom)

        if query:
            db_query = db_query.or_(
                f"label.ilike.%{query}%,uri.ilike.%{query}%,description.ilike.%{query}%"
            )

        # Execute with pagination
        response = (
            await db_query.order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        # Add usage info
        for ontology_class in response.data:
            if include_usage:
                usage_count = await self._get_ontology_class_usage(ontology_class["id"])
                ontology_class["usage_count"] = usage_count

        # Get total count
        count_query = (
            supabase.table("ontology_classes")
            .select("*, domain_ontology_classes!inner(is_primary)", count="exact")
            .eq("domain_ontology_classes.domain_id", domain_id)
        )
        if is_custom is not None:
            count_query = count_query.eq("is_custom", is_custom)
        if query:
            count_query = count_query.or_(
                f"label.ilike.%{query}%,uri.ilike.%{query}%,description.ilike.%{query}%"
            )

        count_response = await count_query.execute()

        return {
            "ontology_classes": response.data,
            "total": count_response.count,
            "limit": limit,
            "skip": skip,
            "has_more": (skip + limit) < count_response.count,
        }

    async def search_ontology_classes(
        self,
        query: Optional[str] = None,
        domain_ids: Optional[List[int]] = None,
        is_mapped: Optional[bool] = None,
        is_custom: Optional[bool] = None,
        parent_class_id: Optional[int] = None,
        include_usage: bool = False,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Search ontology classes across domains"""

        supabase = await get_supabase()

        # Build base query
        if domain_ids:
            # Join with domain mappings if filtering by domain
            db_query = (
                supabase.table("ontology_classes")
                .select("*, domain_ontology_classes!inner(domain_id, is_primary)")
                .in_("domain_ontology_classes.domain_id", domain_ids)
            )
        else:
            db_query = supabase.table("ontology_classes").select("*")

        if is_custom is not None:
            db_query = db_query.eq("is_custom", is_custom)

        if parent_class_id is not None:
            db_query = db_query.eq("parent_class_id", parent_class_id)

        if query:
            db_query = db_query.or_(
                f"label.ilike.%{query}%,uri.ilike.%{query}%,description.ilike.%{query}%"
            )

        # Execute with pagination
        response = (
            await db_query.order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        # Add domains and usage info
        for ontology_class in response.data:
            # Get domains
            domains = await self._get_ontology_class_domains(ontology_class["id"])
            ontology_class["domains"] = domains

            # Get usage if requested
            if include_usage:
                usage_count = await self._get_ontology_class_usage(ontology_class["id"])
                ontology_class["usage_count"] = usage_count

        # Get total count
        count_query = supabase.table("ontology_classes").select("*", count="exact")
        if domain_ids:
            count_query = count_query.select(
                "*, domain_ontology_classes!inner(domain_id)", count="exact"
            ).in_("domain_ontology_classes.domain_id", domain_ids)
        if is_custom is not None:
            count_query = count_query.eq("is_custom", is_custom)
        if parent_class_id is not None:
            count_query = count_query.eq("parent_class_id", parent_class_id)
        if query:
            count_query = count_query.or_(
                f"label.ilike.%{query}%,uri.ilike.%{query}%,description.ilike.%{query}%"
            )

        count_response = await count_query.execute()

        return {
            "ontology_classes": response.data,
            "total": count_response.count,
            "limit": limit,
            "skip": skip,
            "has_more": (skip + limit) < count_response.count,
        }

    # =============================================
    # ONTOLOGY PROPERTY OPERATIONS
    # =============================================

    async def get_ontology_properties_for_domain(
        self,
        domain_id: int,
        query: Optional[str] = None,
        property_type: Optional[str] = None,
        domain_class_id: Optional[int] = None,
        range_class_id: Optional[int] = None,
        is_custom: Optional[bool] = None,
        include_usage: bool = False,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Get ontology properties associated with a domain"""

        supabase = await get_supabase()

        # Build base query
        db_query = (
            supabase.table("ontology_properties")
            .select("*, domain_ontology_properties!inner(is_primary, domain_specific_config)")
            .eq("domain_ontology_properties.domain_id", domain_id)
        )

        if property_type:
            db_query = db_query.eq("property_type", property_type)

        if domain_class_id is not None:
            db_query = db_query.eq("domain_class_id", domain_class_id)

        if range_class_id is not None:
            db_query = db_query.eq("range_class_id", range_class_id)

        if is_custom is not None:
            db_query = db_query.eq("is_custom", is_custom)

        if query:
            db_query = db_query.or_(
                f"label.ilike.%{query}%,uri.ilike.%{query}%,description.ilike.%{query}%"
            )

        # Execute with pagination
        response = (
            await db_query.order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        # Add usage info
        for ontology_property in response.data:
            if include_usage:
                usage_count = await self._get_ontology_property_usage(ontology_property["id"])
                ontology_property["usage_count"] = usage_count

        # Get total count
        count_query = (
            supabase.table("ontology_properties")
            .select("*, domain_ontology_properties!inner(is_primary)", count="exact")
            .eq("domain_ontology_properties.domain_id", domain_id)
        )
        if property_type:
            count_query = count_query.eq("property_type", property_type)
        if domain_class_id is not None:
            count_query = count_query.eq("domain_class_id", domain_class_id)
        if range_class_id is not None:
            count_query = count_query.eq("range_class_id", range_class_id)
        if is_custom is not None:
            count_query = count_query.eq("is_custom", is_custom)
        if query:
            count_query = count_query.or_(
                f"label.ilike.%{query}%,uri.ilike.%{query}%,description.ilike.%{query}%"
            )

        count_response = await count_query.execute()

        return {
            "ontology_properties": response.data,
            "total": count_response.count,
            "limit": limit,
            "skip": skip,
            "has_more": (skip + limit) < count_response.count,
        }

    async def search_ontology_properties(
        self,
        query: Optional[str] = None,
        domain_ids: Optional[List[int]] = None,
        property_type: Optional[str] = None,
        domain_class_id: Optional[int] = None,
        range_class_id: Optional[int] = None,
        is_custom: Optional[bool] = None,
        include_usage: bool = False,
        limit: int = 50,
        skip: int = 0,
    ) -> Dict[str, Any]:
        """Search ontology properties across domains"""

        supabase = await get_supabase()

        # Build base query
        if domain_ids:
            db_query = (
                supabase.table("ontology_properties")
                .select("*, domain_ontology_properties!inner(domain_id, is_primary)")
                .in_("domain_ontology_properties.domain_id", domain_ids)
            )
        else:
            db_query = supabase.table("ontology_properties").select("*")

        if property_type:
            db_query = db_query.eq("property_type", property_type)

        if domain_class_id is not None:
            db_query = db_query.eq("domain_class_id", domain_class_id)

        if range_class_id is not None:
            db_query = db_query.eq("range_class_id", range_class_id)

        if is_custom is not None:
            db_query = db_query.eq("is_custom", is_custom)

        if query:
            db_query = db_query.or_(
                f"label.ilike.%{query}%,uri.ilike.%{query}%,description.ilike.%{query}%"
            )

        # Execute with pagination
        response = (
            await db_query.order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        # Add domains and usage info
        for ontology_property in response.data:
            # Get domains
            domains = await self._get_ontology_property_domains(ontology_property["id"])
            ontology_property["domains"] = domains

            # Get usage if requested
            if include_usage:
                usage_count = await self._get_ontology_property_usage(ontology_property["id"])
                ontology_property["usage_count"] = usage_count

        # Get total count (simplified for now)
        count_response = (
            await supabase.table("ontology_properties")
            .select("*", count="exact")
            .execute()
        )

        return {
            "ontology_properties": response.data,
            "total": count_response.count,
            "limit": limit,
            "skip": skip,
            "has_more": (skip + limit) < count_response.count,
        }

    # =============================================
    # DOMAIN MAPPING OPERATIONS
    # =============================================

    async def add_ontology_class_to_domain(
        self,
        class_id: int,
        domain_id: int,
        is_primary: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add ontology class to domain"""

        supabase = await get_supabase()

        # Check if mapping already exists
        existing = (
            await supabase.table("domain_ontology_classes")
            .select("*")
            .eq("ontology_class_id", class_id)
            .eq("domain_id", domain_id)
            .execute()
        )

        if existing.data:
            raise ValueError("Ontology class already associated with this domain")

        # If this is primary, unset other primary mappings for this class
        if is_primary:
            await supabase.table("domain_ontology_classes").update(
                {"is_primary": False}
            ).eq("ontology_class_id", class_id).execute()

        # Create mapping
        mapping_data = {
            "ontology_class_id": class_id,
            "domain_id": domain_id,
            "is_primary": is_primary,
            "domain_specific_config": config or {},
        }

        response = (
            await supabase.table("domain_ontology_classes").insert(mapping_data).execute()
        )

        return response.data[0]

    async def remove_ontology_class_from_domain(
        self, class_id: int, domain_id: int
    ) -> bool:
        """Remove ontology class from domain"""

        supabase = await get_supabase()

        await supabase.table("domain_ontology_classes").delete().eq(
            "ontology_class_id", class_id
        ).eq("domain_id", domain_id).execute()

        return True

    async def add_ontology_property_to_domain(
        self,
        property_id: int,
        domain_id: int,
        is_primary: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add ontology property to domain"""

        supabase = await get_supabase()

        # Check if mapping already exists
        existing = (
            await supabase.table("domain_ontology_properties")
            .select("*")
            .eq("ontology_property_id", property_id)
            .eq("domain_id", domain_id)
            .execute()
        )

        if existing.data:
            raise ValueError("Ontology property already associated with this domain")

        # If this is primary, unset other primary mappings for this property
        if is_primary:
            await supabase.table("domain_ontology_properties").update(
                {"is_primary": False}
            ).eq("ontology_property_id", property_id).execute()

        # Create mapping
        mapping_data = {
            "ontology_property_id": property_id,
            "domain_id": domain_id,
            "is_primary": is_primary,
            "domain_specific_config": config or {},
        }

        response = (
            await supabase.table("domain_ontology_properties")
            .insert(mapping_data)
            .execute()
        )

        return response.data[0]

    async def remove_ontology_property_from_domain(
        self, property_id: int, domain_id: int
    ) -> bool:
        """Remove ontology property from domain"""

        supabase = await get_supabase()

        await supabase.table("domain_ontology_properties").delete().eq(
            "ontology_property_id", property_id
        ).eq("domain_id", domain_id).execute()

        return True

    # =============================================
    # STATISTICS & ANALYTICS
    # =============================================

    async def get_domain_stats(self, domain_id: int) -> Dict[str, Any]:
        """Get statistics for a domain"""

        supabase = await get_supabase()

        # Count ontology classes
        ontology_classes_count = (
            await supabase.table("domain_ontology_classes")
            .select("*", count=CountMethod.exact)
            .eq("domain_id", domain_id)
            .execute()
        ).count

        # Count ontology properties
        ontology_properties_count = (
            await supabase.table("domain_ontology_properties")
            .select("*", count=CountMethod.exact)
            .eq("domain_id", domain_id)
            .execute()
        ).count

        # Count actual entities and relationships in KG
        entities_count = await self._get_domain_entities_count(domain_id)
        relationships_count = await self._get_domain_relationships_count(domain_id)

        return {
            "domain_id": domain_id,
            "ontology_classes_count": ontology_classes_count,
            "ontology_properties_count": ontology_properties_count,
            "entities_count": entities_count,
            "relationships_count": relationships_count,
            "last_updated": datetime.now(),
        }

    async def validate_ontology_property_constraints(
        self,
        ontology_property_id: int,
        source_ontology_class_id: int,
        target_ontology_class_id: int,
    ) -> Dict[str, Any]:
        """Validate if ontology classes are allowed for ontology property"""

        supabase = await get_supabase()

        # Get ontology property
        property_response = (
            await supabase.table("ontology_properties")
            .select("*")
            .eq("id", ontology_property_id)
            .single()
            .execute()
        )

        if not property_response.data:
            return {"is_valid": False, "errors": ["Ontology property not found"]}

        ontology_property = property_response.data
        errors = []
        warnings = []

        # Check domain class constraints
        if ontology_property.get("domain_class_id"):
            if source_ontology_class_id != ontology_property["domain_class_id"]:
                errors.append(f"Source ontology class {source_ontology_class_id} not allowed as domain")

        # Check range class constraints
        if ontology_property.get("range_class_id"):
            if target_ontology_class_id != ontology_property["range_class_id"]:
                errors.append(f"Target ontology class {target_ontology_class_id} not allowed as range")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    # =============================================
    # SUGGESTION OPERATIONS
    # =============================================

    async def suggest_ontology_classes_for_text(
        self,
        text: str,
        domain_id: Optional[int] = None,
        max_suggestions: int = 5,
    ) -> List[Dict[str, Any]]:
        """Suggest ontology classes for text"""

        supabase = await get_supabase()

        # Build query
        query = supabase.table("ontology_classes").select("*")

        if domain_id:
            query = query.select(
                "*, domain_ontology_classes!inner(domain_id)"
            ).eq("domain_ontology_classes.domain_id", domain_id)

        # Search by label similarity
        query = query.or_(f"label.ilike.%{text}%,description.ilike.%{text}%")
        query = query.limit(max_suggestions)

        response = await query.execute()

        # Add confidence scoring
        suggestions = []
        for item in response.data:
            confidence = 0.8 if text.lower() in item.get("label", "").lower() else 0.6
            suggestions.append(
                {
                    "ontology_class": item,
                    "confidence": confidence,
                    "reason": f"Text match with '{item.get('label', item['uri'])}'",
                }
            )

        return suggestions

    async def suggest_ontology_properties_for_classes(
        self,
        source_class_id: int,
        target_class_id: Optional[int] = None,
        domain_id: Optional[int] = None,
        max_suggestions: int = 5,
    ) -> List[Dict[str, Any]]:
        """Suggest ontology properties for ontology classes"""

        supabase = await get_supabase()

        # Build query
        query = supabase.table("ontology_properties").select("*")

        if domain_id:
            query = query.select(
                "*, domain_ontology_properties!inner(domain_id)"
            ).eq("domain_ontology_properties.domain_id", domain_id)

        # Filter by domain/range constraints
        conditions = []
        if source_class_id:
            conditions.append(f"domain_class_id.eq.{source_class_id}")
        if target_class_id:
            conditions.append(f"range_class_id.eq.{target_class_id}")

        if conditions:
            query = query.or_(",".join(conditions))

        query = query.limit(max_suggestions)
        response = await query.execute()

        # Add confidence scoring
        suggestions = []
        for item in response.data:
            confidence = 0.9
            reason = "Compatible with class constraints"
            
            if item.get("domain_class_id") == source_class_id and item.get("range_class_id") == target_class_id:
                confidence = 1.0
                reason = "Perfect match for domain and range classes"
            elif item.get("domain_class_id") == source_class_id:
                confidence = 0.8
                reason = "Matches domain class"
            elif item.get("range_class_id") == target_class_id:
                confidence = 0.7
                reason = "Matches range class"

            suggestions.append(
                {
                    "ontology_property": item,
                    "confidence": confidence,
                    "reason": reason,
                }
            )

        return suggestions

    # =============================================
    # BULK OPERATIONS
    # =============================================

    async def bulk_associate_ontology_classes(
        self,
        ontology_class_ids: List[int],
        domain_id: int,
        is_primary: bool = False,
        config: Optional[Dict[str, Any]] = None,
        user_id: str = None,
    ) -> Dict[str, Any]:
        """Bulk associate ontology classes with domain"""

        results = []
        errors = []

        for class_id in ontology_class_ids:
            try:
                mapping = await self.add_ontology_class_to_domain(
                    class_id, domain_id, is_primary, config
                )
                results.append(mapping)
            except Exception as e:
                errors.append(
                    {"ontology_class_id": class_id, "error": str(e)}
                )

        if user_id:
            await self.user_service._log_user_activity(
                user_id,
                "bulk_associate_ontology_classes",
                f"Bulk associated {len(results)} ontology classes with domain {domain_id}",
                resource_id=str(domain_id),
            )

        return {
            "created": results,
            "errors": errors,
            "total_attempted": len(ontology_class_ids),
            "successful": len(results),
            "failed": len(errors),
        }

    async def bulk_associate_ontology_properties(
        self,
        ontology_property_ids: List[int],
        domain_id: int,
        is_primary: bool = False,
        config: Optional[Dict[str, Any]] = None,
        user_id: str = None,
    ) -> Dict[str, Any]:
        """Bulk associate ontology properties with domain"""

        results = []
        errors = []

        for property_id in ontology_property_ids:
            try:
                mapping = await self.add_ontology_property_to_domain(
                    property_id, domain_id, is_primary, config
                )
                results.append(mapping)
            except Exception as e:
                errors.append(
                    {"ontology_property_id": property_id, "error": str(e)}
                )

        if user_id:
            await self.user_service._log_user_activity(
                user_id,
                "bulk_associate_ontology_properties",
                f"Bulk associated {len(results)} ontology properties with domain {domain_id}",
                resource_id=str(domain_id),
            )

        return {
            "created": results,
            "errors": errors,
            "total_attempted": len(ontology_property_ids),
            "successful": len(results),
            "failed": len(errors),
        }

    # =============================================
    # ANALYTICS OVERVIEW
    # =============================================

    async def get_domain_analytics_overview(self) -> Dict[str, Any]:
        """Get domain system analytics overview"""

        supabase = await get_supabase()

        # Get counts for overview
        domains_count = (
            await supabase.table("domains")
            .select("*", count="exact")
            .eq("is_active", True)
            .execute()
        ).count

        ontology_classes_count = (
            await supabase.table("ontology_classes")
            .select("*", count="exact")
            .execute()
        ).count

        ontology_properties_count = (
            await supabase.table("ontology_properties")
            .select("*", count="exact")
            .execute()
        ).count

        # Get domain distribution
        domains = await self.search_domains(is_active=True, limit=100)

        domain_stats = []
        for domain in domains["domains"]:
            stats = await self.get_domain_stats(domain["id"])
            stats["domain_name"] = domain["name"]
            stats["display_name"] = domain["display_name"]
            domain_stats.append(stats)

        # Calculate ontology coverage
        mapped_classes = (
            await supabase.table("domain_ontology_classes")
            .select("ontology_class_id", count="exact")
            .execute()
        ).count

        mapped_properties = (
            await supabase.table("domain_ontology_properties")
            .select("ontology_property_id", count="exact")
            .execute()
        ).count

        ontology_coverage = {
            "total_classes": ontology_classes_count,
            "mapped_classes": mapped_classes,
            "unmapped_classes": ontology_classes_count - mapped_classes,
            "class_coverage_percentage": (mapped_classes / ontology_classes_count * 100) if ontology_classes_count > 0 else 0,
            "total_properties": ontology_properties_count,
            "mapped_properties": mapped_properties,
            "unmapped_properties": ontology_properties_count - mapped_properties,
            "property_coverage_percentage": (mapped_properties / ontology_properties_count * 100) if ontology_properties_count > 0 else 0,
        }

        return {
            "overview": {
                "total_domains": domains_count,
                "total_ontology_classes": ontology_classes_count,
                "total_ontology_properties": ontology_properties_count,
                "active_domains": len([d for d in domains["domains"] if d["is_active"]]),
            },
            "domain_stats": domain_stats,
            "ontology_coverage": ontology_coverage,
            "generated_at": datetime.now(),
        }

    # =============================================
    # HELPER METHODS
    # =============================================

    async def _get_domain_ontology_classes(self, domain_id: int) -> List[Dict[str, Any]]:
        """Get ontology classes for a domain"""

        supabase = await get_supabase()

        response = (
            await supabase.table("ontology_classes")
            .select("*, domain_ontology_classes!inner(is_primary, domain_specific_config)")
            .eq("domain_ontology_classes.domain_id", domain_id)
            .execute()
        )

        return response.data

    async def _get_domain_ontology_properties(self, domain_id: int) -> List[Dict[str, Any]]:
        """Get ontology properties for a domain"""

        supabase = await get_supabase()

        response = (
            await supabase.table("ontology_properties")
            .select("*, domain_ontology_properties!inner(is_primary, domain_specific_config)")
            .eq("domain_ontology_properties.domain_id", domain_id)
            .execute()
        )

        return response.data

    async def _get_ontology_class_domains(self, class_id: int) -> List[Dict[str, Any]]:
        """Get domains for an ontology class"""

        supabase = await get_supabase()

        response = (
            await supabase.table("domains")
            .select("*, domain_ontology_classes!inner(is_primary, domain_specific_config)")
            .eq("domain_ontology_classes.ontology_class_id", class_id)
            .eq("is_active", True)
            .execute()
        )

        return response.data

    async def _get_ontology_property_domains(self, property_id: int) -> List[Dict[str, Any]]:
        """Get domains for an ontology property"""

        supabase = await get_supabase()

        response = (
            await supabase.table("domains")
            .select("*, domain_ontology_properties!inner(is_primary, domain_specific_config)")
            .eq("domain_ontology_properties.ontology_property_id", property_id)
            .eq("is_active", True)
            .execute()
        )

        return response.data

    async def _get_ontology_class_usage(self, class_id: int) -> int:
        """Get usage count of ontology class in knowledge graph"""

        supabase = await get_supabase()

        response = (
            await supabase.table("kg_entities")
            .select("*", count="exact")
            .eq("ontology_class_id", class_id)
            .execute()
        )

        return response.count

    async def _get_ontology_property_usage(self, property_id: int) -> int:
        """Get usage count of ontology property in knowledge graph"""

        supabase = await get_supabase()

        response = (
            await supabase.table("kg_relationships")
            .select("*", count="exact")
            .eq("ontology_property_id", property_id)
            .execute()
        )

        return response.count

    async def _get_domain_ontology_class_count(self, domain_id: int) -> int:
        """Get count of ontology classes for a domain"""

        supabase = await get_supabase()

        response = (
            await supabase.table("domain_ontology_classes")
            .select("*", count="exact")
            .eq("domain_id", domain_id)
            .execute()
        )

        return response.count

    async def _get_domain_ontology_property_count(self, domain_id: int) -> int:
        """Get count of ontology properties for a domain"""

        supabase = await get_supabase()

        response = (
            await supabase.table("domain_ontology_properties")
            .select("*", count="exact")
            .eq("domain_id", domain_id)
            .execute()
        )

        return response.count

    async def _get_domain_entities_count(self, domain_id: int) -> int:
        """Get count of entities using ontology classes from this domain"""

        supabase = await get_supabase()

        # Get all ontology class IDs for this domain
        class_response = (
            await supabase.table("domain_ontology_classes")
            .select("ontology_class_id")
            .eq("domain_id", domain_id)
            .execute()
        )

        if not class_response.data:
            return 0

        class_ids = [item["ontology_class_id"] for item in class_response.data]

        # Count entities using these classes
        entity_response = (
            await supabase.table("kg_entities")
            .select("*", count="exact")
            .in_("ontology_class_id", class_ids)
            .execute()
        )

        return entity_response.count

    async def _get_domain_relationships_count(self, domain_id: int) -> int:
        """Get count of relationships using ontology properties from this domain"""

        supabase = await get_supabase()

        # Get all ontology property IDs for this domain
        property_response = (
            await supabase.table("domain_ontology_properties")
            .select("ontology_property_id")
            .eq("domain_id", domain_id)
            .execute()
        )

        if not property_response.data:
            return 0

        property_ids = [item["ontology_property_id"] for item in property_response.data]

        # Count relationships using these properties
        relationship_response = (
            await supabase.table("kg_relationships")
            .select("*", count="exact")
            .in_("ontology_property_id", property_ids)
            .execute()
        )

        return relationship_response.count

    async def _create_domain_ontology_class_mappings(
        self,
        domain_id: int,
        ontology_class_ids: List[int],
        primary_ontology_class_id: Optional[int] = None,
    ) -> None:
        """Create domain mappings for ontology classes"""

        supabase = await get_supabase()

        mappings = []
        for class_id in ontology_class_ids:
            mappings.append(
                {
                    "domain_id": domain_id,
                    "ontology_class_id": class_id,
                    "is_primary": class_id == primary_ontology_class_id,
                    "domain_specific_config": {},
                }
            )

        if mappings:
            await supabase.table("domain_ontology_classes").insert(mappings).execute()

    async def _create_domain_ontology_property_mappings(
        self,
        domain_id: int,
        ontology_property_ids: List[int],
        primary_ontology_property_id: Optional[int] = None,
    ) -> None:
        """Create domain mappings for ontology properties"""

        supabase = await get_supabase()

        mappings = []
        for property_id in ontology_property_ids:
            mappings.append(
                {
                    "domain_id": domain_id,
                    "ontology_property_id": property_id,
                    "is_primary": property_id == primary_ontology_property_id,
                    "domain_specific_config": {},
                }
            )

        if mappings:
            await supabase.table("domain_ontology_properties").insert(mappings).execute()
