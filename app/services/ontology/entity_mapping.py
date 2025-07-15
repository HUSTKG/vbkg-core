from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod

from app.schemas.ontology import EntityMappingCreate, EntityMappingUpdate
from app.services.user import UserService

from .base import BaseOntologyService


class EntityMappingService(BaseOntologyService):
    """Service for entity mapping operations"""
    
    def __init__(self):
        super().__init__()
        self.user_service = UserService()
    
    async def get_entity_mappings(
        self,
        ontology_class_id: Optional[int] = None,
        mapping_status: Optional[str] = None,
        is_verified: Optional[bool] = None,
        auto_mapped: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get entity mappings with filtering"""
        try:
            supabase = await self.get_supabase()
            query = supabase.from_("entity_mappings").select(
                "*, ontology_classes(uri, label, description)",
                count=CountMethod.exact,
            )
            
            # Apply filters
            filters = {
                "ontology_class_id": ontology_class_id,
                "mapping_status": mapping_status,
                "is_verified": is_verified,
                "auto_mapped": auto_mapped
            }
            
            for field, value in filters.items():
                if value is not None:
                    query = query.eq(field, value)
            
            if search:
                query = query.or_(
                    f"entity_type.ilike.%{search}%,ontology_class_uri.ilike.%{search}%,mapping_notes.ilike.%{search}%"
                )
            
            response = await query.range(skip, skip + limit - 1).execute()
            return response
            
        except Exception as e:
            self.logger.error(f"Error retrieving entity mappings: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving entity mappings: {str(e)}"
            )
    
    async def create_entity_mapping(
        self, 
        mapping: EntityMappingCreate, 
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update an entity mapping"""
        try:
            supabase = await self.get_supabase()
            
            # Check if mapping already exists for the same entity/ontology class combination
            query = supabase.from_("entity_mappings").select("*")
            
            # Build unique constraint check
            constraints = []
            if mapping.entity_type:
                constraints.append(f"entity_type.eq.{mapping.entity_type}")
            if mapping.entity_type_id:
                constraints.append(f"entity_type_id.eq.{mapping.entity_type_id}")
            constraints.append(f"ontology_class_id.eq.{mapping.ontology_class_id}")
            
            if constraints:
                query = query.or_(",".join(constraints))
            
            response = await query.execute()
            
            mapping_data = mapping.model_dump()
            if user_id:
                mapping_data["created_by"] = user_id
            
            # Get ontology class URI if not provided
            if not mapping_data.get("ontology_class_uri"):
                from .class_management import OntologyClassService
                class_service = OntologyClassService()
                ontology_class = await class_service.get_ontology_class(mapping.ontology_class_id)
                mapping_data["ontology_class_uri"] = ontology_class["uri"]
            
            if response.data and len(response.data) > 0:
                # Update existing mapping
                existing_id = response.data[0]["id"]
                update_response = await supabase.from_("entity_mappings").update(mapping_data).eq("id", existing_id).execute()
                
                await self.user_service._log_user_activity(
                    user_id=user_id,
                    action="update_entity_mapping",
                    details={
                        "mapping_id": existing_id,
                        "entity_type": mapping.entity_type,
                        "ontology_class_id": mapping.ontology_class_id,
                    },
                )
                return update_response.data[0]
            else:
                # Create new mapping
                insert_response = await supabase.from_("entity_mappings").insert(mapping_data).execute()
                return insert_response.data[0]
                
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error creating entity mapping: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating entity mapping: {str(e)}"
            )
    
    async def update_entity_mapping(
        self, 
        mapping_id: str, 
        mapping: EntityMappingUpdate
    ) -> Dict[str, Any]:
        """Update an entity mapping"""
        try:
            supabase = await self.get_supabase()
            
            data = mapping.model_dump(exclude_unset=True)
            
            # Update ontology class URI if ontology_class_id is being updated
            if data.get("ontology_class_id") and not data.get("ontology_class_uri"):
                from .class_management import OntologyClassService
                class_service = OntologyClassService()
                ontology_class = await class_service.get_ontology_class(data["ontology_class_id"])
                data["ontology_class_uri"] = ontology_class["uri"]
            
            response = await supabase.from_("entity_mappings").update(data).eq("id", mapping_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity mapping not found"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error updating entity mapping {mapping_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating entity mapping: {str(e)}"
            )
    
    async def delete_entity_mapping(self, mapping_id: str) -> Dict[str, Any]:
        """Delete an entity mapping"""
        try:
            supabase = await self.get_supabase()
            await supabase.from_("entity_mappings").delete().eq("id", mapping_id).execute()
            
            return {"success": True, "message": "Entity mapping deleted"}
            
        except Exception as e:
            self.logger.error(f"Error deleting entity mapping {mapping_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting entity mapping: {str(e)}"
            )
    
    async def verify_entity_mapping(
        self, 
        mapping_id: str, 
        verified: bool, 
        user_id: str, 
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify an entity mapping"""
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
            
            response = await supabase.from_("entity_mappings").update(update_data).eq("id", mapping_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity mapping not found"
                )
            
            await self.user_service._log_user_activity(
                user_id=user_id,
                action="verify_entity_mapping",
                details={
                    "mapping_id": mapping_id,
                    "is_verified": verified,
                    "notes": notes,
                },
            )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Error verifying entity mapping {mapping_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying entity mapping: {str(e)}"
            )

