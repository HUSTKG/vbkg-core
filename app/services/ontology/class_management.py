from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.schemas.ontology import OntologyClassCreate, OntologyClassUpdate

from .base import BaseOntologyService


class OntologyClassService(BaseOntologyService):
    """Service for ontology class CRUD operations"""
    
    async def get_ontology_class(self, class_id: int) -> Dict[str, Any]:
        """Get a ontology class by ID"""
        try:
            supabase = await self.get_supabase()
            response = await supabase.from_("ontology_classes").select("*").eq("id", class_id).maybe_single().execute()
            
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ontology class not found"
                )
            
            return response.data
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving ontology class {class_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology class: {str(e)}"
            )
    
    async def get_ontology_class_by_uri(self, uri: str) -> Dict[str, Any]:
        """Get a ontology class by URI"""
        try:
            supabase = await self.get_supabase()
            response = await supabase.from_("ontology_classes").select("*").eq("uri", uri).maybe_single().execute()
            
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ontology class not found"
                )
            
            return response.data
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving ontology class by URI {uri}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology class: {str(e)}"
            )
    
    async def create_ontology_class(
        self, 
        ontology_class_in: OntologyClassCreate, 
        domain_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new ontology class and optionally associate with domain"""
        try:
            # Check if class already exists by URI
            try:
                existing_class = await self.get_ontology_class_by_uri(ontology_class_in.uri)
                
                # If domain_id provided, associate with domain
                if domain_id and existing_class:
                    from .domain_integration import DomainIntegrationService
                    domain_service = DomainIntegrationService()
                    await domain_service.associate_class_with_domain(existing_class["id"], domain_id)
                
                return existing_class
                
            except HTTPException as e:
                if e.status_code != status.HTTP_404_NOT_FOUND:
                    raise
            
            supabase = await self.get_supabase()
            
            # Get parent class ID if provided
            parent_class_id = None
            if ontology_class_in.parent_class_uri:
                try:
                    parent = await self.get_ontology_class_by_uri(ontology_class_in.parent_class_uri)
                    parent_class_id = parent["id"]
                except HTTPException:
                    pass
            
            # Create the class
            data = ontology_class_in.model_dump(exclude={"parent_class_uri"})
            data["parent_class_id"] = parent_class_id
            
            response = await supabase.from_("ontology_classes").insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create ontology class"
                )
            
            created_class = response.data[0]
            
            # Associate with domain if provided
            if domain_id:
                from .domain_integration import DomainIntegrationService
                domain_service = DomainIntegrationService()
                await domain_service.associate_class_with_domain(created_class["id"], domain_id)
            
            return created_class
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error creating ontology class: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating ontology class: {str(e)}"
            )
    
    async def update_ontology_class(
        self, 
        class_id: int, 
        ontology_class_in: OntologyClassUpdate
    ) -> Dict[str, Any]:
        """Update a ontology class"""
        try:
            # Check if class exists
            await self.get_ontology_class(class_id)
            
            supabase = await self.get_supabase()
            
            # Prepare update data
            data = ontology_class_in.model_dump(exclude_unset=True, exclude={"parent_class_uri"})
            
            # Get parent class ID if provided
            if ontology_class_in.parent_class_uri is not None:
                if ontology_class_in.parent_class_uri:
                    try:
                        parent = await self.get_ontology_class_by_uri(ontology_class_in.parent_class_uri)
                        data["parent_class_id"] = parent["id"]
                    except HTTPException:
                        data["parent_class_id"] = None
                else:
                    data["parent_class_id"] = None
            
            # Update the class
            response = await supabase.from_("ontology_classes").update(data).eq("id", class_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update ontology class"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating ontology class {class_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating ontology class: {str(e)}"
            )
    
    async def delete_ontology_class(self, class_id: int) -> Dict[str, Any]:
        """Delete a ontology class and its domain associations"""
        try:
            # Check if class exists
            await self.get_ontology_class(class_id)
            
            supabase = await self.get_supabase()
            
            # Delete domain associations first
            await supabase.from_("domain_ontology_classes").delete().eq("ontology_class_id", class_id).execute()
            
            # Delete the class
            await supabase.from_("ontology_classes").delete().eq("id", class_id).execute()
            
            return {"success": True, "message": "Ontology class deleted"}
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting ontology class {class_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting ontology class: {str(e)}"
            )
    
    async def get_ontology_classes(
        self,
        domain_ids: Optional[List[int]] = None,
        search: Optional[str] = None,
        is_custom: Optional[bool] = None,
        parent_class_id: Optional[int] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get ontology classes with filtering and pagination"""
        try:
            supabase = await self.get_supabase()
            
            if domain_ids:
                # Join with domain associations
                query = supabase.from_("ontology_classes").select(
                    "*, domain_ontology_classes!inner(domain_id, is_primary)",
                    count=CountMethod.exact,
                ).in_("domain_ontology_classes.domain_id", domain_ids)
            else:
                query = supabase.from_("ontology_classes").select("*", count=CountMethod.exact)
            
            # Apply filters
            if is_custom is not None:
                query = query.eq("is_custom", is_custom)
            
            if parent_class_id is not None:
                query = query.eq("parent_class_id", parent_class_id)
            
            if search:
                # Search in label and URI
                query = query.or_(f"label.ilike.%{search}%,uri.ilike.%{search}%")
            
            response = await query.range(skip, skip + limit - 1).execute()
            return response
            
        except Exception as e:
            self.logger.error(f"Error retrieving ontology classes: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology classes: {str(e)}"
            )
    
    async def get_class_hierarchy(self, class_id: int, max_depth: int = 5) -> Dict[str, Any]:
        """Get the complete hierarchy (parents and children) for a class"""
        try:
            # Get the target class
            target_class = await self.get_ontology_class(class_id)
            
            # Get parent hierarchy
            parents = []
            current_class = target_class
            depth = 0
            
            while current_class.get("parent_class_id") and depth < max_depth:
                parent_class = await self.get_ontology_class(current_class["parent_class_id"])
                parents.append(parent_class)
                current_class = parent_class
                depth += 1
            
            # Get children classes
            supabase = await self.get_supabase()
            children_response = await supabase.from_("ontology_classes").select("*").eq("parent_class_id", class_id).execute()
            children = children_response.data
            
            return {
                "target_class": target_class,
                "parents": parents,
                "children": children,
                "hierarchy_depth": len(parents),
            }
            
        except Exception as e:
            self.logger.error(f"Error getting class hierarchy for {class_id}: {e}")
            return {
                "target_class": None,
                "parents": [],
                "children": [],
                "hierarchy_depth": 0,
            }

