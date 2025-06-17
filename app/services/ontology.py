import json
import logging
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from postgrest.base_request_builder import APIResponse
from postgrest.types import CountMethod
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from app.core.supabase import get_supabase
from app.schemas.ontology import (EntityMappingCreate, EntityMappingUpdate,
                                  OntologyClassCreate, OntologyClassUpdate,
                                  OntologyPropertyCreate,
                                  OntologyPropertyUpdate,
                                  RelationshipMappingCreate,
                                  RelationshipMappingUpdate)
from app.services.user import UserService

logger = logging.getLogger(__name__)


class OntologyService:
    def __init__(self):
        self.user_service = UserService()
        # Standard ontology namespaces
        self.FIBO_FND = Namespace("https://spec.edmcouncil.org/fibo/ontology/FND/")
        self.FIBO_SEC = Namespace("https://spec.edmcouncil.org/fibo/ontology/SEC/")
        self.FIBO_LOAN = Namespace("https://spec.edmcouncil.org/fibo/ontology/LOAN/")
        self.FIBO_DER = Namespace("https://spec.edmcouncil.org/fibo/ontology/DER/")
        self.FIBO_INS = Namespace("https://spec.edmcouncil.org/fibo/ontology/INS/")

        # Vietnamese banking adaptations
        self.vietnamese_banking_mappings = {
            # Common FIBO concepts with Vietnamese equivalents
            "FinancialInstrument": {
                "vietnamese_labels": ["công cụ tài chính", "sản phẩm tài chính"],
                "domain": "banking",
            },
            "Account": {"vietnamese_labels": ["tài khoản", "tk"], "domain": "banking"},
            "LegalPerson": {
                "vietnamese_labels": ["pháp nhân", "tổ chức"],
                "domain": "banking",
            },
            "NaturalPerson": {
                "vietnamese_labels": ["cá nhân", "khách hàng cá nhân"],
                "domain": "banking",
            },
            "Bank": {"vietnamese_labels": ["ngân hàng", "nh"], "domain": "banking"},
            "Loan": {"vietnamese_labels": ["khoản vay", "vay"], "domain": "banking"},
            "Deposit": {
                "vietnamese_labels": ["tiền gửi", "gửi tiết kiệm"],
                "domain": "banking",
            },
            "CreditCard": {"vietnamese_labels": ["thẻ tín dụng"], "domain": "banking"},
            "DebitCard": {
                "vietnamese_labels": ["thẻ ghi nợ", "thẻ atm"],
                "domain": "banking",
            },
            "Transaction": {
                "vietnamese_labels": ["giao dịch", "gd"],
                "domain": "banking",
            },
            "Transfer": {
                "vietnamese_labels": ["chuyển khoản", "chuyển tiền"],
                "domain": "banking",
            },
            "InterestRate": {
                "vietnamese_labels": ["lãi suất", "lãi"],
                "domain": "banking",
            },
            "Currency": {
                "vietnamese_labels": ["tiền tệ", "đồng tiền"],
                "domain": "banking",
            },
            "MonetaryAmount": {
                "vietnamese_labels": ["số tiền", "giá trị tiền tệ"],
                "domain": "banking",
            },
        }

        # Vietnamese banking relationship mappings
        self.vietnamese_relationship_mappings = {
            "hasAccount": {
                "vietnamese_labels": ["có tài khoản", "sở hữu tài khoản"],
                "domain": "banking",
            },
            "isCustomerOf": {
                "vietnamese_labels": ["là khách hàng của", "giao dịch tại"],
                "domain": "banking",
            },
            "providesService": {
                "vietnamese_labels": ["cung cấp dịch vụ", "phục vụ"],
                "domain": "banking",
            },
            "manages": {
                "vietnamese_labels": ["quản lý", "điều hành"],
                "domain": "banking",
            },
            "transfersTo": {
                "vietnamese_labels": ["chuyển đến", "gửi cho"],
                "domain": "banking",
            },
            "borrowsFrom": {
                "vietnamese_labels": ["vay từ", "đi vay tại"],
                "domain": "banking",
            },
            "depositsIn": {
                "vietnamese_labels": ["gửi vào", "gửi tiết kiệm tại"],
                "domain": "banking",
            },
            "appliesFor": {"vietnamese_labels": ["đăng ký", "mở"], "domain": "banking"},
        }

    # =============================================
    # ONTOLOGY CLASS OPERATIONS (Domain-aware)
    # =============================================

    async def get_ontology_class(self, class_id: int) -> Dict[str, Any]:
        """Get a ontology class by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("ontology_classes")
                .select("*")
                .eq("id", class_id)
                .maybe_single()
                .execute()
            )

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ontology class not found",
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology class: {str(e)}",
            )

    async def get_ontology_class_by_uri(self, uri: str) -> Dict[str, Any]:
        """Get a ontology class by URI"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("ontology_classes")
                .select("*")
                .eq("uri", uri)
                .maybe_single()
                .execute()
            )

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ontology class not found",
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology class: {str(e)}",
            )

    async def create_ontology_class(
        self, ontology_class_in: OntologyClassCreate, domain_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new ontology class and optionally associate with domain"""
        try:
            supabase = await get_supabase()

            # Check if class already exists by URI
            try:
                existing_class = await self.get_ontology_class_by_uri(
                    ontology_class_in.uri
                )

                # If domain_id provided, associate with domain
                if domain_id and existing_class:
                    await self._associate_class_with_domain(
                        existing_class["id"], domain_id
                    )

                return existing_class
            except HTTPException as e:
                if e.status_code != status.HTTP_404_NOT_FOUND:
                    raise

            # Get parent class ID if provided
            parent_class_id = None
            if ontology_class_in.parent_class_uri:
                try:
                    parent = await self.get_ontology_class_by_uri(
                        ontology_class_in.parent_class_uri
                    )
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
                    detail="Failed to create ontology class",
                )

            created_class = response.data[0]

            # Associate with domain if provided
            if domain_id:
                await self._associate_class_with_domain(created_class["id"], domain_id)

            return created_class
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating ontology class: {str(e)}",
            )

    async def update_ontology_class(
        self, class_id: int, ontology_class_in: OntologyClassUpdate
    ) -> Dict[str, Any]:
        """Update a ontology class"""
        try:
            supabase = await get_supabase()
            # Check if class exists
            await self.get_ontology_class(class_id)

            # Prepare update data
            data = ontology_class_in.model_dump(
                exclude_unset=True, exclude={"parent_class_uri"}
            )

            # Get parent class ID if provided
            if ontology_class_in.parent_class_uri is not None:
                if ontology_class_in.parent_class_uri:
                    try:
                        parent = await self.get_ontology_class_by_uri(
                            ontology_class_in.parent_class_uri
                        )
                        data["parent_class_id"] = parent["id"]
                    except HTTPException:
                        data["parent_class_id"] = None
                else:
                    data["parent_class_id"] = None

            # Update the class
            response = (
                await supabase.from_("ontology_classes")
                .update(data)
                .eq("id", class_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update ontology class",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating ontology class: {str(e)}",
            )

    async def delete_ontology_class(self, class_id: int) -> Dict[str, Any]:
        """Delete a ontology class and its domain associations"""
        try:
            supabase = await get_supabase()
            # Check if class exists
            await self.get_ontology_class(class_id)

            # Delete domain associations first
            await supabase.from_("domain_ontology_classes").delete().eq(
                "ontology_class_id", class_id
            ).execute()

            # Delete the class
            await supabase.from_("ontology_classes").delete().eq(
                "id", class_id
            ).execute()

            return {"success": True, "message": "Ontology class deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting ontology class: {str(e)}",
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
            supabase = await get_supabase()

            if domain_ids:
                # Join with domain associations
                query = (
                    supabase.from_("ontology_classes")
                    .select(
                        "*, domain_ontology_classes!inner(domain_id, is_primary)",
                        count=CountMethod.exact,
                    )
                    .in_("domain_ontology_classes.domain_id", domain_ids)
                )
            else:
                query = supabase.from_("ontology_classes").select(
                    "*", count=CountMethod.exact
                )

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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology classes: {str(e)}",
            )

    # =============================================
    # ONTOLOGY PROPERTY OPERATIONS (Domain-aware)
    # =============================================

    async def get_ontology_property(self, property_id: int) -> Dict[str, Any]:
        """Get a ontology property by ID"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("ontology_properties")
                .select("*")
                .eq("id", property_id)
                .maybe_single()
                .execute()
            )

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ontology property not found",
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology property: {str(e)}",
            )

    async def get_ontology_property_by_uri(self, uri: str) -> Dict[str, Any]:
        """Get a ontology property by URI"""
        try:
            supabase = await get_supabase()
            response = (
                await supabase.from_("ontology_properties")
                .select("*")
                .eq("uri", uri)
                .maybe_single()
                .execute()
            )

            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Ontology property not found",
                )

            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology property: {str(e)}",
            )

    async def create_ontology_property(
        self,
        ontology_property_in: OntologyPropertyCreate,
        domain_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new ontology property and optionally associate with domain"""
        try:
            supabase = await get_supabase()

            # Check if property already exists by URI
            try:
                existing_property = await self.get_ontology_property_by_uri(
                    ontology_property_in.uri
                )

                # If domain_id provided, associate with domain
                if domain_id and existing_property:
                    await self._associate_property_with_domain(
                        existing_property["id"], domain_id
                    )

                return existing_property
            except HTTPException as e:
                if e.status_code != status.HTTP_404_NOT_FOUND:
                    raise

            # Get domain and range class IDs if provided
            domain_class_id = None
            range_class_id = None

            if ontology_property_in.domain_class_uri:
                try:
                    domain_class = await self.get_ontology_class_by_uri(
                        ontology_property_in.domain_class_uri
                    )
                    domain_class_id = domain_class["id"]
                except HTTPException:
                    pass

            if ontology_property_in.range_class_uri:
                try:
                    range_class = await self.get_ontology_class_by_uri(
                        ontology_property_in.range_class_uri
                    )
                    range_class_id = range_class["id"]
                except HTTPException:
                    pass

            # Create the property
            data = ontology_property_in.model_dump(
                exclude={"domain_class_uri", "range_class_uri"}
            )
            data["domain_class_id"] = domain_class_id
            data["range_class_id"] = range_class_id

            response = (
                await supabase.from_("ontology_properties").insert(data).execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create ontology property",
                )

            created_property = response.data[0]

            # Associate with domain if provided
            if domain_id:
                await self._associate_property_with_domain(
                    created_property["id"], domain_id
                )

            return created_property
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating ontology property: {str(e)}",
            )

    async def update_ontology_property(
        self, property_id: int, ontology_property_in: OntologyPropertyUpdate
    ) -> Dict[str, Any]:
        """Update a ontology property"""
        try:
            supabase = await get_supabase()
            # Check if property exists
            await self.get_ontology_property(property_id)

            # Prepare update data
            data = ontology_property_in.model_dump(
                exclude_unset=True, exclude={"domain_class_uri", "range_class_uri"}
            )

            # Get domain class ID if provided
            if ontology_property_in.domain_class_uri is not None:
                if ontology_property_in.domain_class_uri:
                    try:
                        domain_class = await self.get_ontology_class_by_uri(
                            ontology_property_in.domain_class_uri
                        )
                        data["domain_class_id"] = domain_class["id"]
                    except HTTPException:
                        data["domain_class_id"] = None
                else:
                    data["domain_class_id"] = None

            # Get range class ID if provided
            if ontology_property_in.range_class_uri is not None:
                if ontology_property_in.range_class_uri:
                    try:
                        range_class = await self.get_ontology_class_by_uri(
                            ontology_property_in.range_class_uri
                        )
                        data["range_class_id"] = range_class["id"]
                    except HTTPException:
                        data["range_class_id"] = None
                else:
                    data["range_class_id"] = None

            # Update the property
            response = (
                await supabase.from_("ontology_properties")
                .update(data)
                .eq("id", property_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update ontology property",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating ontology property: {str(e)}",
            )

    async def delete_ontology_property(self, property_id: int) -> Dict[str, Any]:
        """Delete a ontology property and its domain associations"""
        try:
            supabase = await get_supabase()
            # Check if property exists
            await self.get_ontology_property(property_id)

            # Delete domain associations first
            await supabase.from_("domain_ontology_properties").delete().eq(
                "ontology_property_id", property_id
            ).execute()

            # Delete the property
            await supabase.from_("ontology_properties").delete().eq(
                "id", property_id
            ).execute()

            return {"success": True, "message": "Ontology property deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting ontology property: {str(e)}",
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
            supabase = await get_supabase()

            if domain_ids:
                # Join with domain associations
                query = (
                    supabase.from_("ontology_properties")
                    .select(
                        "*, domain_ontology_properties!inner(domain_id, is_primary)",
                        count=CountMethod.exact,
                    )
                    .in_("domain_ontology_properties.domain_id", domain_ids)
                )
            else:
                query = supabase.from_("ontology_properties").select(
                    "*", count=CountMethod.exact
                )

            if domain_class_id:
                query = query.eq("domain_class_id", domain_class_id)

            if range_class_id:
                query = query.eq("range_class_id", range_class_id)

            if property_type:
                query = query.eq("property_type", property_type)

            if is_custom is not None:
                query = query.eq("is_custom", is_custom)

            if search:
                # Search in label and URI
                query = query.or_(f"label.ilike.%{search}%,uri.ilike.%{search}%")

            response = await query.range(skip, skip + limit - 1).execute()

            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving ontology properties: {str(e)}",
            )

    # =============================================
    # ENTITY MAPPING OPERATIONS (Updated for ontology classes)
    # =============================================

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
            supabase = await get_supabase()
            query = supabase.from_("entity_mappings").select(
                "*, ontology_classes(uri, label, description)",
                count=CountMethod.exact,
            )

            if ontology_class_id:
                query = query.eq("ontology_class_id", ontology_class_id)

            if mapping_status:
                query = query.eq("mapping_status", mapping_status)

            if is_verified is not None:
                query = query.eq("is_verified", is_verified)

            if auto_mapped is not None:
                query = query.eq("auto_mapped", auto_mapped)

            if search:
                query = query.or_(
                    f"entity_type.ilike.%{search}%,ontology_class_uri.ilike.%{search}%,mapping_notes.ilike.%{search}%"
                )

            response = await query.range(skip, skip + limit - 1).execute()
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving entity mappings: {str(e)}",
            )

    async def create_entity_mapping(
        self, mapping: EntityMappingCreate, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update an entity mapping"""
        try:
            supabase = await get_supabase()

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
                ontology_class = await self.get_ontology_class(
                    mapping.ontology_class_id
                )
                mapping_data["ontology_class_uri"] = ontology_class["uri"]

            if response.data and len(response.data) > 0:
                # Update existing mapping
                existing_id = response.data[0]["id"]
                update_response = (
                    await supabase.from_("entity_mappings")
                    .update(mapping_data)
                    .eq("id", existing_id)
                    .execute()
                )
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
                insert_response = (
                    await supabase.from_("entity_mappings")
                    .insert(mapping_data)
                    .execute()
                )
                return insert_response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating entity mapping: {str(e)}",
            )

    async def update_entity_mapping(
        self, mapping_id: str, mapping: EntityMappingUpdate
    ) -> Dict[str, Any]:
        """Update an entity mapping"""
        try:
            supabase = await get_supabase()

            data = mapping.model_dump(exclude_unset=True)

            # Update ontology class URI if ontology_class_id is being updated
            if data.get("ontology_class_id") and not data.get("ontology_class_uri"):
                ontology_class = await self.get_ontology_class(
                    data["ontology_class_id"]
                )
                data["ontology_class_uri"] = ontology_class["uri"]

            response = (
                await supabase.from_("entity_mappings")
                .update(data)
                .eq("id", mapping_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity mapping not found",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating entity mapping: {str(e)}",
            )

    async def delete_entity_mapping(self, mapping_id: str) -> Dict[str, Any]:
        """Delete an entity mapping"""
        try:
            supabase = await get_supabase()
            await supabase.from_("entity_mappings").delete().eq(
                "id", mapping_id
            ).execute()
            return {"success": True, "message": "Entity mapping deleted"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting entity mapping: {str(e)}",
            )

    async def verify_entity_mapping(
        self, mapping_id: str, verified: bool, user_id: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify an entity mapping"""
        try:
            supabase = await get_supabase()

            update_data = {
                "is_verified": verified,
                "mapping_status": "mapped" if verified else "needs_review",
                "reviewed_by": user_id,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            }

            if notes:
                update_data["mapping_notes"] = notes

            response = (
                await supabase.from_("entity_mappings")
                .update(update_data)
                .eq("id", mapping_id)
                .execute()
            )

            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity mapping not found",
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying entity mapping: {str(e)}",
            )

    # =============================================
    # RELATIONSHIP MAPPING OPERATIONS (Updated for ontology properties)
    # =============================================

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
            supabase = await get_supabase()
            query = supabase.from_("relationship_mappings").select(
                "*, ontology_properties(uri, label, description)",
                count=CountMethod.exact,
            )

            if ontology_property_id:
                query = query.eq("ontology_property_id", ontology_property_id)

            if mapping_status:
                query = query.eq("mapping_status", mapping_status)

            if is_verified is not None:
                query = query.eq("is_verified", is_verified)

            if auto_mapped is not None:
                query = query.eq("auto_mapped", auto_mapped)

            if search:
                query = query.or_(
                    f"relationship_type.ilike.%{search}%,ontology_property_uri.ilike.%{search}%,mapping_notes.ilike.%{search}%"
                )

            response = await query.range(skip, skip + limit - 1).execute()
            return response
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving relationship mappings: {str(e)}",
            )

    async def create_relationship_mapping(
        self, mapping: RelationshipMappingCreate, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update a relationship mapping"""
        try:
            supabase = await get_supabase()

            # Check if mapping already exists
            query = supabase.from_("relationship_mappings").select("*")

            # Build unique constraint check
            constraints = []
            if mapping.relationship_type:
                constraints.append(f"relationship_type.eq.{mapping.relationship_type}")
            if mapping.relationship_type_id:
                constraints.append(
                    f"relationship_type_id.eq.{mapping.relationship_type_id}"
                )
            constraints.append(
                f"ontology_property_id.eq.{mapping.ontology_property_id}"
            )

            if constraints:
                query = query.or_(",".join(constraints))

            response = await query.execute()

            mapping_data = mapping.model_dump()
            if user_id:
                mapping_data["created_by"] = user_id

            # Get ontology property URI if not provided
            if not mapping_data.get("ontology_property_uri"):
                ontology_property = await self.get_ontology_property(
                    mapping.ontology_property_id
                )
                mapping_data["ontology_property_uri"] = ontology_property["uri"]

            if response.data and len(response.data) > 0:
                # Update existing mapping
                existing_id = response.data[0]["id"]
                update_response = (
                    await supabase.from_("relationship_mappings")
                    .update(mapping_data)
                    .eq("id", existing_id)
                    .execute()
                )

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
                insert_response = (
                    await supabase.from_("relationship_mappings")
                    .insert(mapping_data)
                    .execute()
                )

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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating relationship mapping: {str(e)}",
            )

    async def update_relationship_mapping(
        self, mapping_id: str, mapping: RelationshipMappingUpdate
    ) -> Dict[str, Any]:
        """Update a relationship mapping"""
        try:
            supabase = await get_supabase()

            data = mapping.model_dump(exclude_unset=True)

            # Update ontology property URI if ontology_property_id is being updated
            if data.get("ontology_property_id") and not data.get(
                "ontology_property_uri"
            ):
                ontology_property = await self.get_ontology_property(
                    data["ontology_property_id"]
                )
                data["ontology_property_uri"] = ontology_property["uri"]

            # Update the mapping
            update_response = (
                await supabase.from_("relationship_mappings")
                .update(data)
                .eq("id", mapping_id)
                .execute()
            )

            if not update_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship mapping not found",
                )

            return update_response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating relationship mapping: {str(e)}",
            )

    async def delete_relationship_mapping(self, mapping_id: str) -> Dict[str, Any]:
        """Delete a relationship mapping"""
        try:
            supabase = await get_supabase()
            await supabase.from_("relationship_mappings").delete().eq(
                "id", mapping_id
            ).execute()

            return {"success": True, "message": "Relationship mapping deleted"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting relationship mapping: {str(e)}",
            )

    async def verify_relationship_mapping(
        self, mapping_id: str, verified: bool, user_id: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify a relationship mapping"""
        try:
            supabase = await get_supabase()

            update_data = {
                "is_verified": verified,
                "mapping_status": "mapped" if verified else "needs_review",
                "reviewed_by": user_id,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
            }

            if notes:
                update_data["mapping_notes"] = notes

            update_response = (
                await supabase.from_("relationship_mappings")
                .update(update_data)
                .eq("id", mapping_id)
                .execute()
            )

            if not update_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship mapping not found",
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying relationship mapping: {str(e)}",
            )

    # =============================================
    # DOMAIN INTEGRATION HELPER METHODS
    # =============================================

    async def _associate_class_with_domain(
        self, class_id: int, domain_id: int, is_primary: bool = False
    ) -> None:
        """Associate an ontology class with a domain"""
        try:
            supabase = await get_supabase()

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
            logger.warning(
                f"Error associating class {class_id} with domain {domain_id}: {e}"
            )

    async def _associate_property_with_domain(
        self, property_id: int, domain_id: int, is_primary: bool = False
    ) -> None:
        """Associate an ontology property with a domain"""
        try:
            supabase = await get_supabase()

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
            logger.warning(
                f"Error associating property {property_id} with domain {domain_id}: {e}"
            )

    # =============================================
    # IMPORT AND ENRICHMENT OPERATIONS
    # =============================================

    async def import_ontology_from_file(
        self, file_id: str, target_domain_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Import ontology from an uploaded file and associate with domain"""
        from app.services.file_upload import UploadService

        try:
            # Get file content
            upload_service = UploadService()
            file_content = await upload_service.get_file_content(file_upload_id=file_id)

            # Process the ontology
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            try:
                import_result = await self.load_fibo_ontology(
                    fibo_file_path=temp_file_path,
                    include_vietnamese_mappings=True,
                    target_domain_id=target_domain_id,
                )

            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)

            return import_result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error importing ontology: {str(e)}",
            )

    async def load_fibo_ontology(
        self,
        fibo_file_path: str,
        domain_filter: Optional[str] = None,
        include_vietnamese_mappings: bool = True,
        target_domain_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Load FIBO ontology from RDF file into database and associate with domain

        Args:
            fibo_file_path: Path to FIBO RDF/OWL file
            domain_filter: Filter by specific domain (e.g., 'banking', 'securities')
            include_vietnamese_mappings: Whether to add Vietnamese language mappings
            target_domain_id: Domain ID to associate imported ontology with

        Returns:
            Loading results with statistics
        """

        try:
            logger.info(f"Loading FIBO ontology from: {fibo_file_path}")

            # Load RDF graph
            graph = Graph()
            graph.parse(fibo_file_path, format=self._detect_rdf_format(fibo_file_path))

            logger.info(f"Loaded RDF graph with {len(graph)} triples")

            # Extract classes and properties
            classes = await self._extract_fibo_classes(graph, domain_filter)
            properties = await self._extract_fibo_properties(graph, domain_filter)

            # Add Vietnamese mappings if requested
            if include_vietnamese_mappings:
                classes = await self._add_vietnamese_mappings_to_classes(classes)
                properties = await self._add_vietnamese_mappings_to_properties(
                    properties
                )

            # Save to database and associate with domain
            results = await self._save_ontology_to_database(
                classes, properties, target_domain_id
            )

            logger.info(f"Successfully loaded FIBO ontology: {results}")
            return results

        except Exception as e:
            logger.error(f"Error loading FIBO ontology: {e}")
            raise

    def _detect_rdf_format(self, file_path: str) -> str:
        """Detect RDF file format based on extension"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        format_map = {
            ".owl": "xml",
            ".rdf": "xml",
            ".xml": "xml",
            ".ttl": "turtle",
            ".n3": "n3",
            ".nt": "nt",
            ".jsonld": "json-ld",
        }

        return format_map.get(extension, "xml")  # Default to XML

    async def _extract_fibo_classes(
        self, graph: Graph, domain_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract classes from FIBO ontology"""
        classes = []

        # Query for all OWL classes
        for subj in graph.subjects(RDF.type, OWL.Class):
            class_info = await self._extract_class_info(graph, subj, domain_filter)
            if class_info:
                classes.append(class_info)

        logger.info(f"Extracted {len(classes)} classes from FIBO")
        return classes

    async def _extract_class_info(
        self, graph: Graph, class_uri: URIRef, domain_filter: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Extract information for a single class"""
        try:
            uri_str = str(class_uri)

            # Apply domain filter
            if domain_filter and not self._matches_domain_filter(
                uri_str, domain_filter
            ):
                return None

            # Get class label
            label = self._get_rdf_label(graph, class_uri)
            if not label:
                label = self._extract_name_from_uri(uri_str)

            # Get class description/comment
            description = self._get_rdf_comment(graph, class_uri)

            # Get parent classes
            parent_classes = list(graph.objects(class_uri, RDFS.subClassOf))
            parent_class_uri = str(parent_classes[0]) if parent_classes else None

            # Determine domain based on URI structure
            domain = self._determine_fibo_domain(uri_str)

            class_info = {
                "uri": uri_str,
                "label": label,
                "description": description,
                "domain": domain,
                "parent_class_uri": parent_class_uri,
                "is_custom": False,
                "properties": {
                    "fibo_source": True,
                    "namespace": self._extract_namespace(uri_str),
                },
            }

            return class_info

        except Exception as e:
            logger.warning(f"Error extracting class info for {class_uri}: {e}")
            return None

    async def _extract_fibo_properties(
        self, graph: Graph, domain_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract properties from FIBO ontology"""
        properties = []

        # Query for object properties
        for subj in graph.subjects(RDF.type, OWL.ObjectProperty):
            prop_info = await self._extract_property_info(
                graph, subj, "object", domain_filter
            )
            if prop_info:
                properties.append(prop_info)

        # Query for datatype properties
        for subj in graph.subjects(RDF.type, OWL.DatatypeProperty):
            prop_info = await self._extract_property_info(
                graph, subj, "datatype", domain_filter
            )
            if prop_info:
                properties.append(prop_info)

        logger.info(f"Extracted {len(properties)} properties from FIBO")
        return properties

    async def _extract_property_info(
        self,
        graph: Graph,
        property_uri: URIRef,
        property_type: str,
        domain_filter: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Extract information for a single property"""
        try:
            uri_str = str(property_uri)

            # Apply domain filter
            if domain_filter and not self._matches_domain_filter(
                uri_str, domain_filter
            ):
                return None

            # Get property label
            label = self._get_rdf_label(graph, property_uri)
            if not label:
                label = self._extract_name_from_uri(uri_str)

            # Get property description/comment
            description = self._get_rdf_comment(graph, property_uri)

            # Get domain and range
            domains = list(graph.objects(property_uri, RDFS.domain))
            ranges = list(graph.objects(property_uri, RDFS.range))

            domain_class_uri = str(domains[0]) if domains else None
            range_class_uri = str(ranges[0]) if ranges else None

            # Determine domain based on URI structure
            domain = self._determine_fibo_domain(uri_str)

            property_info = {
                "uri": uri_str,
                "label": label,
                "description": description,
                "property_type": property_type,
                "domain": domain,
                "domain_class_uri": domain_class_uri,
                "range_class_uri": range_class_uri,
                "is_custom": False,
            }

            return property_info

        except Exception as e:
            logger.warning(f"Error extracting property info for {property_uri}: {e}")
            return None

    def _get_rdf_label(self, graph: Graph, uri: URIRef) -> Optional[str]:
        """Get rdfs:label for a URI"""
        labels = list(graph.objects(uri, RDFS.label))
        return str(labels[0]) if labels else None

    def _get_rdf_comment(self, graph: Graph, uri: URIRef) -> Optional[str]:
        """Get rdfs:comment for a URI"""
        comments = list(graph.objects(uri, RDFS.comment))
        return str(comments[0]) if comments else None

    def _extract_name_from_uri(self, uri: str) -> str:
        """Extract class/property name from URI"""
        # Get the last part after # or /
        name = uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]

        # Convert CamelCase to readable format
        name = re.sub(r"(?<!^)(?=[A-Z])", " ", name)

        return name

    def _extract_namespace(self, uri: str) -> str:
        """Extract namespace from URI"""
        if "#" in uri:
            return uri.split("#")[0] + "#"
        else:
            parts = uri.split("/")
            return "/".join(parts[:-1]) + "/"

    def _determine_fibo_domain(self, uri: str) -> str:
        """Determine FIBO domain based on URI structure"""
        uri_lower = uri.lower()

        if "fnd" in uri_lower:
            return "foundations"
        elif "sec" in uri_lower:
            return "securities"
        elif "loan" in uri_lower:
            return "loans"
        elif "der" in uri_lower:
            return "derivatives"
        elif "ins" in uri_lower:
            return "insurance"
        elif any(
            banking_term in uri_lower
            for banking_term in ["bank", "account", "deposit", "payment"]
        ):
            return "banking"
        else:
            return "general"

    def _matches_domain_filter(self, uri: str, domain_filter: str) -> bool:
        """Check if URI matches domain filter"""
        determined_domain = self._determine_fibo_domain(uri)
        return determined_domain == domain_filter or domain_filter == "general"

    async def _add_vietnamese_mappings_to_classes(
        self, classes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add Vietnamese language mappings to classes"""
        for class_info in classes:
            label = class_info.get("label", "")

            # Check if we have Vietnamese mappings for this class
            if label in self.vietnamese_banking_mappings:
                mapping = self.vietnamese_banking_mappings[label]

                # Add Vietnamese labels to properties
                if "properties" not in class_info:
                    class_info["properties"] = {}

                class_info["properties"]["vietnamese_labels"] = mapping[
                    "vietnamese_labels"
                ]
                class_info["domain"] = mapping.get("domain", class_info.get("domain"))

                # Update description to include Vietnamese context
                if mapping["vietnamese_labels"]:
                    vietnamese_desc = (
                        f"Tiếng Việt: {', '.join(mapping['vietnamese_labels'])}"
                    )
                    if class_info.get("description"):
                        class_info["description"] += f" ({vietnamese_desc})"
                    else:
                        class_info["description"] = vietnamese_desc

        return classes

    async def _add_vietnamese_mappings_to_properties(
        self, properties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add Vietnamese language mappings to properties"""
        for prop_info in properties:
            label = prop_info.get("label", "")

            # Check if we have Vietnamese mappings for this property
            if label in self.vietnamese_relationship_mappings:
                mapping = self.vietnamese_relationship_mappings[label]

                # Add Vietnamese labels to description
                if mapping["vietnamese_labels"]:
                    vietnamese_desc = (
                        f"Tiếng Việt: {', '.join(mapping['vietnamese_labels'])}"
                    )
                    if prop_info.get("description"):
                        prop_info["description"] += f" ({vietnamese_desc})"
                    else:
                        prop_info["description"] = vietnamese_desc

                prop_info["domain"] = mapping.get("domain", prop_info.get("domain"))

        return properties

    async def _save_ontology_to_database(
        self,
        classes: List[Dict[str, Any]],
        properties: List[Dict[str, Any]],
        target_domain_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Save extracted ontology to database and associate with domain"""
        try:
            supabase = await get_supabase()

            results = {
                "classes_added": 0,
                "properties_added": 0,
                "classes_updated": 0,
                "properties_updated": 0,
                "domain_associations_created": 0,
                "errors": [],
            }

            # Create URI to ID mapping for parent class resolution
            uri_to_id_map = {}

            # First pass: Insert/update classes
            for class_info in classes:
                try:
                    # Check if class already exists
                    existing_response = (
                        await supabase.from_("ontology_classes")
                        .select("id")
                        .eq("uri", class_info["uri"])
                        .execute()
                    )

                    class_data = {
                        "uri": class_info["uri"],
                        "label": class_info["label"],
                        "description": class_info["description"],
                        "domain": class_info["domain"],
                        "is_custom": class_info["is_custom"],
                        "properties": class_info.get("properties", {}),
                    }

                    if existing_response.data:
                        # Update existing class
                        class_id = existing_response.data[0]["id"]
                        await supabase.from_("ontology_classes").update(class_data).eq(
                            "id", class_id
                        ).execute()
                        results["classes_updated"] += 1
                        uri_to_id_map[class_info["uri"]] = class_id
                    else:
                        # Insert new class
                        response = (
                            await supabase.from_("ontology_classes")
                            .insert(class_data)
                            .execute()
                        )
                        if response.data:
                            class_id = response.data[0]["id"]
                            results["classes_added"] += 1
                            uri_to_id_map[class_info["uri"]] = class_id

                    # Associate with target domain if provided
                    if target_domain_id and class_id:
                        await self._associate_class_with_domain(
                            class_id, target_domain_id
                        )
                        results["domain_associations_created"] += 1

                except Exception as e:
                    error_msg = f"Error saving class {class_info.get('label', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            # Second pass: Update parent class relationships
            for class_info in classes:
                if (
                    class_info.get("parent_class_uri")
                    and class_info["uri"] in uri_to_id_map
                ):
                    parent_class_uri = class_info["parent_class_uri"]
                    if parent_class_uri in uri_to_id_map:
                        try:
                            class_id = uri_to_id_map[class_info["uri"]]
                            parent_id = uri_to_id_map[parent_class_uri]

                            await supabase.from_("ontology_classes").update(
                                {"parent_class_id": parent_id}
                            ).eq("id", class_id).execute()

                        except Exception as e:
                            logger.warning(
                                f"Error updating parent class relationship: {e}"
                            )

            # Third pass: Insert/update properties
            for prop_info in properties:
                try:
                    # Check if property already exists
                    existing_response = (
                        await supabase.from_("ontology_properties")
                        .select("id")
                        .eq("uri", prop_info["uri"])
                        .execute()
                    )

                    # Resolve domain and range class IDs
                    domain_class_id = None
                    range_class_id = None

                    if prop_info.get("domain_class_uri"):
                        domain_class_id = uri_to_id_map.get(
                            prop_info["domain_class_uri"]
                        )

                    if prop_info.get("range_class_uri"):
                        range_class_id = uri_to_id_map.get(prop_info["range_class_uri"])

                    property_data = {
                        "uri": prop_info["uri"],
                        "label": prop_info["label"],
                        "description": prop_info["description"],
                        "property_type": prop_info["property_type"],
                        "domain": prop_info["domain"],
                        "domain_class_id": domain_class_id,
                        "range_class_id": range_class_id,
                        "is_custom": prop_info.get("is_custom", False),
                    }

                    if existing_response.data:
                        # Update existing property
                        property_id = existing_response.data[0]["id"]
                        await supabase.from_("ontology_properties").update(
                            property_data
                        ).eq("id", property_id).execute()
                        results["properties_updated"] += 1
                    else:
                        # Insert new property
                        response = (
                            await supabase.from_("ontology_properties")
                            .insert(property_data)
                            .execute()
                        )
                        if response.data:
                            property_id = response.data[0]["id"]
                            results["properties_added"] += 1

                            # Associate with target domain if provided
                            if target_domain_id:
                                await self._associate_property_with_domain(
                                    property_id, target_domain_id
                                )
                                results["domain_associations_created"] += 1

                except Exception as e:
                    error_msg = f"Error saving property {prop_info.get('label', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)

            logger.info(f"FIBO ontology save completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Error saving ontology to database: {e}")
            raise

    # =============================================
    # BULK OPERATIONS
    # =============================================

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
                    await self.create_entity_mapping(mapping, user_id)
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
                    await self.create_relationship_mapping(mapping, user_id)
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

    # =============================================
    # STATS OPERATIONS
    # =============================================

    async def get_mapping_stats(
        self, domain_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Get mapping statistics"""
        try:
            supabase = await get_supabase()

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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting mapping stats: {str(e)}",
            )

    async def get_ontology_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded ontology
        """
        try:
            supabase = await get_supabase()

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
            logger.error(f"Error getting ontology statistics: {e}")
            return {}

    async def get_datatype_properties_for_class(
        self, class_id: int, domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all datatype properties that have this class as domain
        """
        try:
            supabase = await get_supabase()

            query = (
                supabase.from_("ontology_properties")
                .select("*")
                .eq("domain_class_id", class_id)
                .eq("property_type", "datatype")
            )

            if domain:
                query = query.eq("domain", domain)

            response = await query.execute()
            return response.data

        except Exception as e:
            logger.error(f"Error getting datatype properties for class {class_id}: {e}")
            return []

    async def get_object_properties_for_domain_range(
        self,
        domain_class_id: Optional[int] = None,
        range_class_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get object properties filtered by domain and/or range classes
        """
        try:
            supabase = await get_supabase()

            query = (
                supabase.from_("ontology_properties")
                .select("*")
                .eq("property_type", "object")
            )

            if domain_class_id:
                query = query.eq("domain_class_id", domain_class_id)

            if range_class_id:
                query = query.eq("range_class_id", range_class_id)

            if domain:
                query = query.eq("domain", domain)

            response = await query.execute()
            return response.data

        except Exception as e:
            logger.error(f"Error getting object properties: {e}")
            return []

    async def get_properties_by_type(
        self, property_type: str, domain: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get properties filtered by type (datatype or object)
        """
        try:
            supabase = await get_supabase()

            query = (
                supabase.from_("ontology_properties")
                .select("*")
                .eq("property_type", property_type)
                .limit(limit)
            )

            if domain:
                query = query.eq("domain", domain)

            response = await query.execute()
            return response.data

        except Exception as e:
            logger.error(f"Error getting {property_type} properties: {e}")
            return []

    async def suggest_datatype_properties_for_entity(
        self, entity_type: str, entity_text: str, domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Suggest relevant datatype properties for an entity based on its type and content
        """
        try:
            # First find the ontology class for this entity type
            supabase = await get_supabase()

            class_query = (
                supabase.from_("ontology_classes")
                .select("*")
                .ilike("label", f"%{entity_type}%")
            )
            if domain:
                class_query = class_query.eq("domain", domain)

            class_response = await class_query.execute()

            suggestions = []

            for cls in class_response.data:
                # Get datatype properties for this class
                datatype_props = await self.get_datatype_properties_for_class(
                    cls["id"], domain
                )

                for prop in datatype_props:
                    # Simple relevance scoring based on entity text content
                    relevance_score = self._calculate_property_relevance(
                        prop, entity_text
                    )

                    if relevance_score > 0.3:  # Threshold for relevance
                        suggestions.append(
                            {
                                "property": prop,
                                "relevance_score": relevance_score,
                                "suggested_extraction_pattern": self._suggest_extraction_pattern(
                                    prop, entity_text
                                ),
                            }
                        )

            # Sort by relevance score
            suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
            return suggestions[:10]  # Return top 10 suggestions

        except Exception as e:
            logger.error(f"Error suggesting datatype properties: {e}")
            return []

    def _calculate_property_relevance(
        self, property_info: Dict[str, Any], entity_text: str
    ) -> float:
        """
        Calculate how relevant a property is to an entity based on text content
        """
        score = 0.0

        property_label = property_info.get("label", "").lower()
        property_desc = property_info.get("description", "").lower()
        entity_text_lower = entity_text.lower()

        # Keyword matching
        relevance_keywords = {
            "account": ["tài khoản", "account", "số", "tk"],
            "amount": ["số tiền", "tiền", "amount", "triệu", "tỷ", "vnd", "usd"],
            "date": ["ngày", "date", "time", "thời gian"],
            "name": ["tên", "name", "họ"],
            "address": ["địa chỉ", "address", "phường", "quận", "thành phố"],
            "phone": ["số điện thoại", "phone", "sdt", "mobile"],
            "email": ["email", "mail", "@"],
            "id": ["id", "mã", "code", "số"],
        }

        # Check if property label contains relevant keywords
        for category, keywords in relevance_keywords.items():
            if any(keyword in property_label for keyword in keywords):
                if any(keyword in entity_text_lower for keyword in keywords):
                    score += 0.3

        # Check description matching
        if property_desc and any(
            word in entity_text_lower for word in property_desc.split()
        ):
            score += 0.2

        # Vietnamese banking specific patterns
        banking_patterns = {
            "số tài khoản": r"\d{10,16}",
            "số tiền": r"\d+(?:[.,]\d+)*\s*(?:vnd|vnđ|đồng|triệu|tỷ|usd)",
            "ngày": r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "số điện thoại": r"(?:\+84|0)[1-9]\d{8,9}",
        }

        for pattern_name, pattern in banking_patterns.items():
            if pattern_name in property_label and re.search(pattern, entity_text):
                score += 0.4

        return min(score, 1.0)  # Cap at 1.0

    def _suggest_extraction_pattern(
        self, property_info: Dict[str, Any], entity_text: str
    ) -> Optional[str]:
        """
        Suggest regex pattern for extracting this property from entity text
        """
        property_label = property_info.get("label", "").lower()

        # Common extraction patterns
        extraction_patterns = {
            "account": r"\d{10,16}",
            "amount": r"\d+(?:[.,]\d+)*\s*(?:vnd|vnđ|đồng|triệu|tỷ|usd)",
            "date": r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone": r"(?:\+84|0)[1-9]\d{8,9}",
            "name": r"[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]+",
            "id": r"[A-Z0-9]{6,20}",
        }

        for pattern_type, pattern in extraction_patterns.items():
            if pattern_type in property_label:
                return pattern

        return None

    async def validate_property_domain_range(
        self, property_id: int, source_entity_type: str, target_entity_type: str
    ) -> Dict[str, Any]:
        """
        Validate if a property can be used between two entity types
        """
        try:
            # Get property details
            property_info = await self.get_ontology_property(property_id)

            # Get domain and range class information
            domain_class_id = property_info.get("domain_class_id")
            range_class_id = property_info.get("range_class_id")

            validation_result = {
                "is_valid": True,
                "domain_match": True,
                "range_match": True,
                "warnings": [],
            }

            # Check domain class
            if domain_class_id:
                domain_class = await self.get_ontology_class(domain_class_id)
                if domain_class["label"].lower() != source_entity_type.lower():
                    validation_result["domain_match"] = False
                    validation_result["warnings"].append(
                        f"Source entity type '{source_entity_type}' doesn't match property domain '{domain_class['label']}'"
                    )

            # Check range class (for object properties)
            if range_class_id and property_info.get("property_type") == "object":
                range_class = await self.get_ontology_class(range_class_id)
                if range_class["label"].lower() != target_entity_type.lower():
                    validation_result["range_match"] = False
                    validation_result["warnings"].append(
                        f"Target entity type '{target_entity_type}' doesn't match property range '{range_class['label']}'"
                    )

            # Overall validation
            validation_result["is_valid"] = (
                validation_result["domain_match"] and validation_result["range_match"]
            )

            if not validation_result["is_valid"]:
                logger.warning(
                    f"Property {property_info['label']} validation failed: {validation_result['warnings']}"
                )
            return validation_result
        except Exception as e:
            logger.error(f"Error validating property domain/range: {e}")
            return {
                "is_valid": False,
                "domain_match": False,
                "range_match": False,
                "warnings": [str(e)],
            }

    async def get_ontology_context_with_class_properties(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ontology context với class-specific datatype properties mapping cho entity extraction
        """
        try:
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

    async def suggest_object_property_mapping(
        self,
        relationship_type: str,
        source_entity_type: str,
        target_entity_type: str,
        max_suggestions: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Suggest ONLY object property mappings for a relationship
        """
        try:
            supabase = await get_supabase()

            suggestions = []

            # First try exact label match for object properties only
            response = (
                await supabase.from_("ontology_properties")
                .select("*")
                .eq("property_type", "object")
                .ilike("label", f"%{relationship_type}%")
                .limit(max_suggestions)
                .execute()
            )

            for prop in response.data:
                # Additional validation for domain/range compatibility
                compatibility_score = (
                    await self._calculate_object_property_compatibility(
                        prop, source_entity_type, target_entity_type
                    )
                )

                suggestions.append(
                    {
                        "ontology_property_id": prop["id"],
                        "label": prop["label"],
                        "uri": prop["uri"],
                        "description": prop.get("description"),
                        "property_type": "object",
                        "similarity_score": 0.9,
                        "compatibility_score": compatibility_score,
                        "match_type": "label_match",
                        "domain_class_id": prop.get("domain_class_id"),
                        "range_class_id": prop.get("range_class_id"),
                    }
                )

            # If not enough suggestions, try description search for object properties
            if len(suggestions) < max_suggestions:
                remaining = max_suggestions - len(suggestions)
                response = (
                    await supabase.from_("ontology_properties")
                    .select("*")
                    .eq("property_type", "object")
                    .ilike("description", f"%{relationship_type}%")
                    .limit(remaining)
                    .execute()
                )

                for prop in response.data:
                    # Avoid duplicates
                    if not any(
                        s["ontology_property_id"] == prop["id"] for s in suggestions
                    ):
                        compatibility_score = (
                            await self._calculate_object_property_compatibility(
                                prop, source_entity_type, target_entity_type
                            )
                        )

                        suggestions.append(
                            {
                                "ontology_property_id": prop["id"],
                                "label": prop["label"],
                                "uri": prop["uri"],
                                "description": prop.get("description"),
                                "property_type": "object",
                                "similarity_score": 0.7,
                                "compatibility_score": compatibility_score,
                                "match_type": "description_match",
                                "domain_class_id": prop.get("domain_class_id"),
                                "range_class_id": prop.get("range_class_id"),
                            }
                        )

            # Sort by combined score (similarity + compatibility)
            for suggestion in suggestions:
                suggestion["combined_score"] = (
                    suggestion["similarity_score"] * 0.4
                    + suggestion["compatibility_score"] * 0.6
                )

            suggestions.sort(key=lambda x: x["combined_score"], reverse=True)
            return suggestions

        except Exception as e:
            logger.error(f"Error suggesting object property mapping: {e}")
            return []

    async def _calculate_object_property_compatibility(
        self,
        property_info: Dict[str, Any],
        source_entity_type: str,
        target_entity_type: str,
    ) -> float:
        """
        Calculate compatibility score for object property với entity types
        """
        try:
            compatibility_score = 0.5  # Base score

            # Check domain compatibility
            domain_class_id = property_info.get("domain_class_id")
            if domain_class_id:
                domain_class = await self.get_ontology_class(domain_class_id)
                if domain_class["label"].lower() == source_entity_type.lower():
                    compatibility_score += 0.3
                elif source_entity_type.lower() in domain_class["label"].lower():
                    compatibility_score += 0.15

            # Check range compatibility
            range_class_id = property_info.get("range_class_id")
            if range_class_id:
                range_class = await self.get_ontology_class(range_class_id)
                if range_class["label"].lower() == target_entity_type.lower():
                    compatibility_score += 0.3
                elif target_entity_type.lower() in range_class["label"].lower():
                    compatibility_score += 0.15

            return min(compatibility_score, 1.0)

        except Exception as e:
            logger.warning(f"Error calculating property compatibility: {e}")
            return 0.3  # Default low score

    async def suggest_ontology_class_mapping(
        self, entity_text: str, entity_type: str, max_suggestions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest ontology class mappings for an entity using database
        """
        try:
            supabase = await get_supabase()

            suggestions = []

            # First try exact label match
            response = (
                await supabase.from_("ontology_classes")
                .select("*")
                .ilike("label", f"%{entity_type}%")
                .limit(max_suggestions)
                .execute()
            )

            for cls in response.data:
                suggestions.append(
                    {
                        "ontology_class_id": cls["id"],
                        "label": cls["label"],
                        "uri": cls["uri"],
                        "description": cls.get("description"),
                        "similarity_score": 0.9,
                        "match_type": "label_match",
                    }
                )

            # If not enough suggestions, try description search
            if len(suggestions) < max_suggestions:
                remaining = max_suggestions - len(suggestions)
                response = (
                    await supabase.from_("ontology_classes")
                    .select("*")
                    .ilike("description", f"%{entity_text}%")
                    .limit(remaining)
                    .execute()
                )

                for cls in response.data:
                    # Avoid duplicates
                    if not any(
                        s["ontology_class_id"] == cls["id"] for s in suggestions
                    ):
                        suggestions.append(
                            {
                                "ontology_class_id": cls["id"],
                                "label": cls["label"],
                                "uri": cls["uri"],
                                "description": cls.get("description"),
                                "similarity_score": 0.7,
                                "match_type": "description_match",
                            }
                        )

            return suggestions

        except Exception as e:
            logger.error(f"Error suggesting ontology class mapping: {e}")
            return []

    async def get_ontology_context_for_extraction(
        self,
        domain: Optional[str] = None,
        include_datatype: bool = True,
        include_object: bool = True,
    ) -> Dict[str, Any]:
        """
        Unified method để get ontology context cho cả entity và relationship extraction
        """
        try:
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

                # Get datatype properties cho từng class nếu cần
                if include_datatype:
                    datatype_props_query = (
                        supabase.from_("ontology_properties")
                        .select("*")
                        .eq("domain_class_id", cls["id"])
                        .eq("property_type", "datatype")
                    )

                    datatype_props_response = await datatype_props_query.execute()
                    class_datatype_properties[cls["id"]] = datatype_props_response.data

            # Get properties by type
            context = {
                "classes": classes,
                "class_datatype_properties": (
                    class_datatype_properties if include_datatype else {}
                ),
            }

            if include_datatype:
                datatype_props = await self.get_properties_by_type("datatype", domain)
                context["datatype_properties"] = {
                    prop["id"]: prop for prop in datatype_props
                }

            if include_object:
                object_props = await self.get_properties_by_type("object", domain)
                context["object_properties"] = {
                    prop["id"]: prop for prop in object_props
                }

            return context

        except Exception as e:
            logger.error(f"Error getting unified ontology context: {e}")
            return {
                "classes": {},
                "class_datatype_properties": {},
                "datatype_properties": {},
                "object_properties": {},
            }

    async def get_class_hierarchy(
        self, class_id: int, max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Get the complete hierarchy (parents and children) for a class
        """
        try:
            supabase = await get_supabase()

            # Get the target class
            target_class = await self.get_ontology_class(class_id)

            # Get parent hierarchy
            parents = []
            current_class = target_class
            depth = 0

            while current_class.get("parent_class_id") and depth < max_depth:
                parent_class = await self.get_ontology_class(
                    current_class["parent_class_id"]
                )
                parents.append(parent_class)
                current_class = parent_class
                depth += 1

            # Get children classes
            children_response = (
                await supabase.from_("ontology_classes")
                .select("*")
                .eq("parent_class_id", class_id)
                .execute()
            )
            children = children_response.data

            return {
                "target_class": target_class,
                "parents": parents,
                "children": children,
                "hierarchy_depth": len(parents),
            }

        except Exception as e:
            logger.error(f"Error getting class hierarchy: {e}")
            return {
                "target_class": None,
                "parents": [],
                "children": [],
                "hierarchy_depth": 0,
            }

    async def find_compatible_properties(
        self, source_class_id: int, target_class_id: int, property_type: str = "object"
    ) -> List[Dict[str, Any]]:
        """
        Find properties that can connect two specific classes
        """
        try:
            supabase = await get_supabase()

            # Direct match
            direct_match_query = (
                supabase.from_("ontology_properties")
                .select("*")
                .eq("domain_class_id", source_class_id)
                .eq("property_type", property_type)
            )

            if property_type == "object":
                direct_match_query = direct_match_query.eq(
                    "range_class_id", target_class_id
                )

            direct_matches = await direct_match_query.execute()

            compatible_properties = []

            # Add direct matches
            for prop in direct_matches.data:
                compatible_properties.append(
                    {
                        "property": prop,
                        "compatibility_type": "direct",
                        "confidence": 1.0,
                    }
                )

            # Check for inherited compatibility (via class hierarchy)
            source_hierarchy = await self.get_class_hierarchy(source_class_id)
            target_hierarchy = await self.get_class_hierarchy(target_class_id)

            # Check if any parent classes have compatible properties
            for parent_class in source_hierarchy["parents"]:
                parent_props_query = (
                    supabase.from_("ontology_properties")
                    .select("*")
                    .eq("domain_class_id", parent_class["id"])
                    .eq("property_type", property_type)
                )

                if property_type == "object":
                    # Check against target class and its parents
                    target_class_ids = [target_class_id] + [
                        p["id"] for p in target_hierarchy["parents"]
                    ]
                    parent_props_query = parent_props_query.in_(
                        "range_class_id", target_class_ids
                    )

                parent_props = await parent_props_query.execute()

                for prop in parent_props.data:
                    # Avoid duplicates
                    if not any(
                        cp["property"]["id"] == prop["id"]
                        for cp in compatible_properties
                    ):
                        compatible_properties.append(
                            {
                                "property": prop,
                                "compatibility_type": "inherited",
                                "confidence": 0.8,
                                "inherited_from": parent_class["label"],
                            }
                        )

            return compatible_properties

        except Exception as e:
            logger.error(f"Error finding compatible properties: {e}")
            return []

    async def suggest_missing_ontology_elements(
        self,
        extracted_entities: List[Dict[str, Any]],
        extracted_relationships: List[Dict[str, Any]],
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze extraction results and suggest missing ontology classes/properties
        """
        try:
            supabase = await get_supabase()

            # Get existing ontology elements
            existing_classes_query = supabase.from_("ontology_classes").select(
                "label, uri"
            )
            existing_props_query = supabase.from_("ontology_properties").select(
                "label, uri"
            )

            if domain:
                existing_classes_query = existing_classes_query.eq("domain", domain)
                existing_props_query = existing_props_query.eq("domain", domain)

            existing_classes = await existing_classes_query.execute()
            existing_props = await existing_props_query.execute()

            existing_class_labels = {
                cls["label"].lower() for cls in existing_classes.data
            }
            existing_prop_labels = {
                prop["label"].lower() for prop in existing_props.data
            }

            # Analyze unmapped entities
            unmapped_entity_types = set()
            for entity in extracted_entities:
                if not entity.get("is_mapped", False):
                    entity_type = entity.get("entity_type", "").lower()
                    if entity_type and entity_type not in existing_class_labels:
                        unmapped_entity_types.add(entity_type)

            # Analyze unmapped relationships
            unmapped_relationship_types = set()
            for relationship in extracted_relationships:
                if not relationship.get("is_mapped", False):
                    rel_type = relationship.get("relationship_type", "").lower()
                    if rel_type and rel_type not in existing_prop_labels:
                        unmapped_relationship_types.add(rel_type)

            # Generate suggestions
            class_suggestions = []
            for entity_type in unmapped_entity_types:
                suggestion = await self._generate_class_suggestion(entity_type, domain)
                if suggestion:
                    class_suggestions.append(suggestion)

            property_suggestions = []
            for rel_type in unmapped_relationship_types:
                suggestion = await self._generate_property_suggestion(rel_type, domain)
                if suggestion:
                    property_suggestions.append(suggestion)

            return {
                "missing_classes": list(unmapped_entity_types),
                "missing_properties": list(unmapped_relationship_types),
                "class_suggestions": class_suggestions,
                "property_suggestions": property_suggestions,
                "suggested_domain": domain or "banking",
            }

        except Exception as e:
            logger.error(f"Error suggesting missing ontology elements: {e}")
            return {
                "missing_classes": [],
                "missing_properties": [],
                "class_suggestions": [],
                "property_suggestions": [],
            }

    async def _generate_class_suggestion(
        self, entity_type: str, domain: Optional[str]
    ) -> Dict[str, Any]:
        """Generate suggestion for a missing ontology class"""
        # Vietnamese to English mapping for banking domain
        vietnamese_to_english = {
            "ngân hàng": "Bank",
            "khách hàng": "Customer",
            "tài khoản": "Account",
            "thẻ tín dụng": "CreditCard",
            "thẻ ghi nợ": "DebitCard",
            "giao dịch": "Transaction",
            "chi nhánh": "Branch",
            "sản phẩm": "Product",
            "khoản vay": "Loan",
            "tiền gửi": "Deposit",
        }

        # Generate URI
        english_label = vietnamese_to_english.get(
            entity_type.lower(), entity_type.title().replace(" ", "")
        )
        domain_prefix = domain or "banking"
        suggested_uri = f"https://ontology.example.com/{domain_prefix}#{english_label}"

        # Determine parent class
        parent_mappings = {
            "ngân hàng": "FinancialInstitution",
            "khách hàng": "Person",
            "tài khoản": "FinancialInstrument",
            "thẻ tín dụng": "PaymentInstrument",
            "thẻ ghi nợ": "PaymentInstrument",
            "giao dịch": "FinancialTransaction",
            "chi nhánh": "Location",
            "khoản vay": "FinancialInstrument",
            "tiền gửi": "FinancialInstrument",
        }

        return {
            "suggested_label": english_label,
            "suggested_uri": suggested_uri,
            "original_entity_type": entity_type,
            "suggested_domain": domain_prefix,
            "suggested_parent_class": parent_mappings.get(entity_type.lower()),
            "description": f"Auto-generated class for {entity_type} entities",
            "vietnamese_labels": [entity_type],
        }

    async def _generate_property_suggestion(
        self, relationship_type: str, domain: Optional[str]
    ) -> Dict[str, Any]:
        """Generate suggestion for a missing ontology property"""
        # Vietnamese to English relationship mapping
        vietnamese_to_english_props = {
            "có tài khoản": "hasAccount",
            "là khách hàng của": "isCustomerOf",
            "chuyển tiền cho": "transfersTo",
            "vay từ": "borrowsFrom",
            "gửi tiết kiệm tại": "depositsAt",
            "quản lý": "manages",
            "cung cấp dịch vụ": "providesService",
            "thuộc về": "belongsTo",
            "giao dịch tại": "transactsAt",
        }

        english_label = vietnamese_to_english_props.get(
            relationship_type.lower(), relationship_type.title().replace(" ", "")
        )
        domain_prefix = domain or "banking"
        suggested_uri = f"https://ontology.example.com/{domain_prefix}#{english_label}"

        # Determine property type and domain/range
        property_type_mapping = {
            "có tài khoản": ("object", "Person", "Account"),
            "là khách hàng của": ("object", "Person", "Bank"),
            "chuyển tiền cho": ("object", "Person", "Person"),
            "vay từ": ("object", "Person", "Bank"),
            "quản lý": ("object", "Person", "Account"),
            "cung cấp dịch vụ": ("object", "Bank", "Person"),
            "thuộc về": ("object", "Account", "Person"),
            "giao dịch tại": ("object", "Person", "Bank"),
        }

        prop_type, domain_class, range_class = property_type_mapping.get(
            relationship_type.lower(), ("object", None, None)
        )

        return {
            "suggested_label": english_label,
            "suggested_uri": suggested_uri,
            "original_relationship_type": relationship_type,
            "suggested_domain": domain_prefix,
            "property_type": prop_type,
            "suggested_domain_class": domain_class,
            "suggested_range_class": range_class,
            "description": f"Auto-generated property for {relationship_type} relationships",
            "vietnamese_labels": [relationship_type],
        }

    async def apply_entity_mapping_suggestion(
        self, mapping_id: str, suggestion_index: int, user_id: str
    ) -> Dict[str, Any]:
        """Apply AI suggestion for entity mapping"""
        try:
            supabase = await get_supabase()

            # Get current mapping
            mapping_response = (
                await supabase.table("entity_mappings")
                .select("*")
                .eq("id", mapping_id)
                .single()
                .execute()
            )

            if not mapping_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity mapping not found",
                )

            mapping = mapping_response.data

            # Parse suggestions from mapping_notes
            suggestions = []
            if mapping.get("suggestions"):
                try:
                    suggestions = json.loads(mapping["suggestions"])
                except json.JSONDecodeError:
                    suggestions = []

            if suggestion_index >= len(suggestions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid suggestion index",
                )

            suggestion = suggestions[suggestion_index]
            suggested_class = suggestion.get("suggested_class", "")

            # Find ontology class by label
            class_response = (
                await supabase.table("ontology_classes")
                .select("*")
                .eq("label", suggested_class)
                .execute()
            )

            if not class_response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ontology class '{suggested_class}' not found",
                )

            ontology_class = class_response.data[0]

            # Update mapping with applied suggestion
            update_data = {
                "ontology_class_id": ontology_class["id"],
                "mapping_status": "mapped",
                "confidence": suggestion.get("confidence", 0.8),
                "is_verified": False,  # Still needs admin verification
                "mapping_notes": f"Applied AI suggestion: {suggestion.get('reasoning', '')}",
                "reviewed_by": user_id,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            response = (
                await supabase.table("entity_mappings")
                .update(update_data)
                .eq("id", mapping_id)
                .execute()
            )

            # Log activity
            await self.user_service._log_user_activity(
                user_id=user_id,
                action="apply_entity_mapping_suggestion",
                details={
                    "mapping_id": mapping_id,
                    "applied_suggestion": suggestion,
                    "ontology_class_id": ontology_class["id"],
                },
            )

            return response.data[0]

        except HTTPException:
            raise
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
            supabase = await get_supabase()

            # Get current mapping
            mapping_response = (
                await supabase.table("relationship_mappings")
                .select("*")
                .eq("id", mapping_id)
                .single()
                .execute()
            )

            if not mapping_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship mapping not found",
                )

            mapping = mapping_response.data

            # Parse suggestions from mapping_notes
            suggestions = []
            if mapping.get("suggestions"):
                try:
                    suggestions = json.loads(mapping["suggestions"])
                except json.JSONDecodeError:
                    suggestions = []

            if suggestion_index >= len(suggestions):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid suggestion index",
                )

            suggestion = suggestions[suggestion_index]
            suggested_property = suggestion.get("suggested_property", "")

            # Find ontology property by label
            property_response = (
                await supabase.table("ontology_properties")
                .select("*")
                .eq("label", suggested_property)
                .execute()
            )

            if not property_response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ontology property '{suggested_property}' not found",
                )

            ontology_property = property_response.data[0]

            # Update mapping with applied suggestion
            update_data = {
                "ontology_property_id": ontology_property["id"],
                "mapping_status": "mapped",
                "confidence": suggestion.get("confidence", 0.8),
                "is_verified": False,  # Still needs admin verification
                "mapping_notes": f"Applied AI suggestion: {suggestion.get('reasoning', '')}",
                "reviewed_by": user_id,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            response = (
                await supabase.table("relationship_mappings")
                .update(update_data)
                .eq("id", mapping_id)
                .execute()
            )

            # Log activity
            await self.user_service._log_user_activity(
                user_id=user_id,
                action="apply_relationship_mapping_suggestion",
                details={
                    "mapping_id": mapping_id,
                    "applied_suggestion": suggestion,
                    "ontology_property_id": ontology_property["id"],
                },
            )

            return response.data[0]

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error applying relationship mapping suggestion: {str(e)}",
            )
