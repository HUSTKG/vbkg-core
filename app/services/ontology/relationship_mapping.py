from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.schemas.ontology import (RelationshipMappingCreate,
                                  RelationshipMappingUpdate)
from app.services.user import UserService

from .base import BaseOntologyService


class RelationshipMappingService(BaseOntologyService):
    """Service for relationship mapping operations"""
    
    def __init__(self):
        super().__init__()
        self.user_service = UserService()
    
    async def get_relationship_mappings(
        self,
        ontology_property_id: Optional[int] = None,
        mapping_status: Optional[str] = None,
        is_verified: Optional[bool] = None,
        auto_mapped: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get relationship mappings with filtering"""
        try:
            supabase = await self.get_supabase()
            query = supabase.from_("relationship_mappings").select(
                "*, ontology_properties(uri, label, description)",
                count=CountMethod.exact,
            )
            
            # Apply filters
            filters = {
                "ontology_property_id": ontology_property_id,
                "mapping_status": mapping_status,
                "is_verified": is_verified,
                "auto_mapped": auto_mapped
            }
            
            for field, value in filters.items():
                if value is not None:
                    query = query.eq(field, value)
            
            if search:
                query = query.or_(
                    f"relationship_type.ilike.%{search}%,ontology_property_uri.ilike.%{search}%,mapping_notes.ilike.%{search}%"
                )
            
            response = await query.range(skip, skip + limit - 1).execute()
            return response
            
        except Exception as e:
            self.logger.error(f"Error retrieving relationship mappings: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving relationship mappings: {str(e)}"
            )
    
    async def create_relationship_mapping(
        self, 
        mapping: RelationshipMappingCreate, 
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update a relationship mapping"""
        try:
            supabase = await self.get_supabase()
            
            # Check if mapping already exists
            query = supabase.from_("relationship_mappings").select("*")
            
            # Build unique constraint check
            constraints = []
            if mapping.relationship_type:
                constraints.append(f"relationship_type.eq.{mapping.relationship_type}")
            if mapping.relationship_type_id:
                constraints.append(f"relationship_type_id.eq.{mapping.relationship_type_id}")
            constraints.append(f"ontology_property_id.eq.{mapping.ontology_property_id}")
            
            if constraints:
                query = query.or_(",".join(constraints))
            
            response = await query.execute()
            
            mapping_data = mapping.model_dump()
            if user_id:
                mapping_data["created_by"] = user_id
            
            # Get ontology property URI if not provided
            if not mapping_data.get("ontology_property_uri"):
                from .property_management import OntologyPropertyService
                property_service = OntologyPropertyService()
                ontology_property = await property_service.get_ontology_property(mapping.ontology_property_id)
                mapping_data["ontology_property_uri"] = ontology_property["uri"]
            
            if response.data and len(response.data) > 0:
                # Update existing mapping
                existing_id = response.data[0]["id"]
                update_response = await supabase.from_("relationship_mappings").update(mapping_data).eq("id", existing_id).execute()
                
                await self.user_service._log_user_activity(
                    user_id=user_id,
                    action="update_relationship_mapping",
                    details={
                        "mapping_id": existing_id,
                        "relationship_type": mapping.relationship_type,
                        "ontology_property_id": mapping.ontology_property_id,
                    },
                )
                
                return update_response.data[0]
            else:
                # Create new mapping
                insert_response = await supabase.from_("relationship_mappings").insert(mapping_data).execute()
                
                await self.user_service._log_user_activity(
                    user_id=user_id,
                    action="create_relationship_mapping",
                    details={
                        "relationship_type": mapping.relationship_type,
                        "ontology_property_id": mapping.ontology_property_id,
                    },
                )
                
                return insert_response.data[0]
                
        except Exception as e:
            self.logger.error(f"Error creating relationship mapping: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating relationship mapping: {str(e)}"
            )
    
    async def update_relationship_mapping(
        self, 
        mapping_id: str, 
        mapping: RelationshipMappingUpdate
    ) -> Dict[str, Any]:
        """Update a relationship mapping"""
        try:
            supabase = await self.get_supabase()
            
            data = mapping.model_dump(exclude_unset=True)
            
            # Update ontology property URI if ontology_property_id is being updated
            if data.get("ontology_property_id") and not data.get("ontology_property_uri"):
                from .property_management import OntologyPropertyService
                property_service = OntologyPropertyService()
                ontology_property = await property_service.get_ontology_property(data["ontology_property_id"])
                data["ontology_property_uri"] = ontology_property["uri"]
            
            # Update the mapping
            update_response = await supabase.from_("relationship_mappings").update(data).eq("id", mapping_id).execute()
            
            if not update_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship mapping not found"
                )
            
            return update_response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating relationship mapping {mapping_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating relationship mapping: {str(e)}"
            )
    
    async def delete_relationship_mapping(self, mapping_id: str) -> Dict[str, Any]:
        """Delete a relationship mapping"""
        try:
            supabase = await self.get_supabase()
            await supabase.from_("relationship_mappings").delete().eq("id", mapping_id).execute()
            
            return {"success": True, "message": "Relationship mapping deleted"}
            
        except Exception as e:
            self.logger.error(f"Error deleting relationship mapping {mapping_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting relationship mapping: {str(e)}"
            )
    
    async def verify_relationship_mapping(
        self, 
        mapping_id: str, 
        verified: bool, 
        user_id: str, 
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify a relationship mapping"""
        try:
            supabase = await self.get_supabase()
            
            update_data = {
                "is_verified": verified,
                "mapping_status": "mapped" if verified else "needs_review",
                "reviewed_by": user_id,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            }
            
            if notes:
                update_data["mapping_notes"] = notes
            
            update_response = await supabase.from_("relationship_mappings").update(update_data).eq("id", mapping_id).execute()
            
            if not update_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship mapping not found"
                )
            
            await self.user_service._log_user_activity(
                user_id=user_id,
                action="verify_relationship_mapping",
                details={
                    "mapping_id": mapping_id,
                    "is_verified": verified,
                    "notes": notes,
                },
            )
            
            return update_response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error verifying relationship mapping {mapping_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying relationship mapping: {str(e)}"
            )

