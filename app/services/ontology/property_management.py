from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.schemas.ontology import OntologyPropertyCreate, OntologyPropertyUpdate

from .base import BaseOntologyService


class OntologyPropertyService(BaseOntologyService):
    """Service for ontology property CRUD operations"""
    
    async def get_ontology_property(self, property_id: int) -> Dict[str, Any]:
        """Get a ontology property by ID"""
        try:
            supabase = await self.get_supabase()
            response = await supabase.from_("ontology_properties").select("*").eq("id", property_id).maybe_single().execute()
            
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ontology property not found"
                )
            
            return response.data
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving ontology property {property_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology property: {str(e)}"
            )
    
    async def get_ontology_property_by_uri(self, uri: str) -> Dict[str, Any]:
        """Get a ontology property by URI"""
        try:
            supabase = await self.get_supabase()
            response = await supabase.from_("ontology_properties").select("*").eq("uri", uri).maybe_single().execute()
            
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ontology property not found"
                )
            
            return response.data
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving ontology property by URI {uri}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology property: {str(e)}"
            )
    
    async def create_ontology_property(
        self,
        ontology_property_in: OntologyPropertyCreate,
        domain_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new ontology property and optionally associate with domain"""
        try:
            # Check if property already exists by URI
            try:
                existing_property = await self.get_ontology_property_by_uri(ontology_property_in.uri)
                
                # If domain_id provided, associate with domain
                if domain_id and existing_property:
                    from .domain_integration import DomainIntegrationService
                    domain_service = DomainIntegrationService()
                    await domain_service.associate_property_with_domain(existing_property["id"], domain_id)
                
                return existing_property
                
            except HTTPException as e:
                if e.status_code != status.HTTP_404_NOT_FOUND:
                    raise
            
            supabase = await self.get_supabase()
            
            # Get domain and range class IDs if provided
            domain_class_id = None
            range_class_id = None
            
            if ontology_property_in.domain_class_uri:
                try:
                    from .class_management import OntologyClassService
                    class_service = OntologyClassService()
                    domain_class = await class_service.get_ontology_class_by_uri(ontology_property_in.domain_class_uri)
                    domain_class_id = domain_class["id"]
                except HTTPException:
                    pass
            
            if ontology_property_in.range_class_uri:
                try:
                    from .class_management import OntologyClassService
                    class_service = OntologyClassService()
                    range_class = await class_service.get_ontology_class_by_uri(ontology_property_in.range_class_uri)
                    range_class_id = range_class["id"]
                except HTTPException:
                    pass
            
            # Create the property
            data = ontology_property_in.model_dump(exclude={"domain_class_uri", "range_class_uri"})
            data["domain_class_id"] = domain_class_id
            data["range_class_id"] = range_class_id
            
            response = await supabase.from_("ontology_properties").insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create ontology property"
                )
            
            created_property = response.data[0]
            
            # Associate with domain if provided
            if domain_id:
                from .domain_integration import DomainIntegrationService
                domain_service = DomainIntegrationService()
                await domain_service.associate_property_with_domain(created_property["id"], domain_id)
            
            return created_property
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error creating ontology property: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating ontology property: {str(e)}"
            )
    
    async def update_ontology_property(
        self, 
        property_id: int, 
        ontology_property_in: OntologyPropertyUpdate
    ) -> Dict[str, Any]:
        """Update a ontology property"""
        try:
            # Check if property exists
            await self.get_ontology_property(property_id)
            
            supabase = await self.get_supabase()
            
            # Prepare update data
            data = ontology_property_in.model_dump(exclude_unset=True, exclude={"domain_class_uri", "range_class_uri"})
            
            # Get domain class ID if provided
            if ontology_property_in.domain_class_uri is not None:
                if ontology_property_in.domain_class_uri:
                    try:
                        from .class_management import OntologyClassService
                        class_service = OntologyClassService()
                        domain_class = await class_service.get_ontology_class_by_uri(ontology_property_in.domain_class_uri)
                        data["domain_class_id"] = domain_class["id"]
                    except HTTPException:
                        data["domain_class_id"] = None
                else:
                    data["domain_class_id"] = None
            
            # Get range class ID if provided
            if ontology_property_in.range_class_uri is not None:
                if ontology_property_in.range_class_uri:
                    try:
                        from .class_management import OntologyClassService
                        class_service = OntologyClassService()
                        range_class = await class_service.get_ontology_class_by_uri(ontology_property_in.range_class_uri)
                        data["range_class_id"] = range_class["id"]
                    except HTTPException:
                        data["range_class_id"] = None
                else:
                    data["range_class_id"] = None
            
            # Update the property
            response = await supabase.from_("ontology_properties").update(data).eq("id", property_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update ontology property"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating ontology property {property_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating ontology property: {str(e)}"
            )
    
    async def delete_ontology_property(self, property_id: int) -> Dict[str, Any]:
        """Delete a ontology property and its domain associations"""
        try:
            # Check if property exists
            await self.get_ontology_property(property_id)
            
            supabase = await self.get_supabase()
            
            # Delete domain associations first
            await supabase.from_("domain_ontology_properties").delete().eq("ontology_property_id", property_id).execute()
            
            # Delete the property
            await supabase.from_("ontology_properties").delete().eq("id", property_id).execute()
            
            return {"success": True, "message": "Ontology property deleted"}
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting ontology property {property_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting ontology property: {str(e)}"
            )
    
    async def get_ontology_properties(
        self,
        domain_ids: Optional[List[int]] = None,
        domain_class_id: Optional[int] = None,
        range_class_id: Optional[int] = None,
        property_type: Optional[str] = None,
        search: Optional[str] = None,
        is_custom: Optional[bool] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get ontology properties with filtering and pagination"""
        try:
            supabase = await self.get_supabase()
            
            if domain_ids:
                # Join with domain associations
                query = supabase.from_("ontology_properties").select(
                    "*, domain_ontology_properties!inner(domain_id, is_primary)",
                    count=CountMethod.exact,
                ).in_("domain_ontology_properties.domain_id", domain_ids)
            else:
                query = supabase.from_("ontology_properties").select("*", count=CountMethod.exact)
            
            # Apply filters
            filters = {
                "domain_class_id": domain_class_id,
                "range_class_id": range_class_id,
                "property_type": property_type,
                "is_custom": is_custom
            }
            
            for field, value in filters.items():
                if value is not None:
                    query = query.eq(field, value)
            
            if search:
                # Search in label and URI
                query = query.or_(f"label.ilike.%{search}%,uri.ilike.%{search}%")
            
            response = await query.range(skip, skip + limit - 1).execute()
            return response
            
        except Exception as e:
            self.logger.error(f"Error retrieving ontology properties: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology properties: {str(e)}"
            )
    
    async def get_properties_by_type(
        self, 
        property_type: str, 
        domain: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get properties filtered by type (datatype or object)"""
        try:
            supabase = await self.get_supabase()
            
            query = supabase.from_("ontology_properties").select("*").eq("property_type", property_type).limit(limit)
            
            if domain:
                query = query.eq("domain", domain)
            
            response = await query.execute()
            return response.data
            
        except Exception as e:
            self.logger.error(f"Error getting {property_type} properties: {e}")
            return []

