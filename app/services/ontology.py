import logging
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from fastapi import HTTPException, status
from numpy import info
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
                "domain": "banking"
            },
            "Account": {
                "vietnamese_labels": ["tài khoản", "tk"],
                "domain": "banking"
            },
            "LegalPerson": {
                "vietnamese_labels": ["pháp nhân", "tổ chức"],
                "domain": "banking"
            },
            "NaturalPerson": {
                "vietnamese_labels": ["cá nhân", "khách hàng cá nhân"],
                "domain": "banking"
            },
            "Bank": {
                "vietnamese_labels": ["ngân hàng", "nh"],
                "domain": "banking"
            },
            "Loan": {
                "vietnamese_labels": ["khoản vay", "vay"],
                "domain": "banking"
            },
            "Deposit": {
                "vietnamese_labels": ["tiền gửi", "gửi tiết kiệm"],
                "domain": "banking"
            },
            "CreditCard": {
                "vietnamese_labels": ["thẻ tín dụng"],
                "domain": "banking"
            },
            "DebitCard": {
                "vietnamese_labels": ["thẻ ghi nợ", "thẻ atm"],
                "domain": "banking"
            },
            "Transaction": {
                "vietnamese_labels": ["giao dịch", "gd"],
                "domain": "banking"
            },
            "Transfer": {
                "vietnamese_labels": ["chuyển khoản", "chuyển tiền"],
                "domain": "banking"
            },
            "InterestRate": {
                "vietnamese_labels": ["lãi suất", "lãi"],
                "domain": "banking"
            },
            "Currency": {
                "vietnamese_labels": ["tiền tệ", "đồng tiền"],
                "domain": "banking"
            },
            "MonetaryAmount": {
                "vietnamese_labels": ["số tiền", "giá trị tiền tệ"],
                "domain": "banking"
            }
        }
        
        # Vietnamese banking relationship mappings
        self.vietnamese_relationship_mappings = {
            "hasAccount": {
                "vietnamese_labels": ["có tài khoản", "sở hữu tài khoản"],
                "domain": "banking"
            },
            "isCustomerOf": {
                "vietnamese_labels": ["là khách hàng của", "giao dịch tại"],
                "domain": "banking"
            },
            "providesService": {
                "vietnamese_labels": ["cung cấp dịch vụ", "phục vụ"],
                "domain": "banking"
            },
            "manages": {
                "vietnamese_labels": ["quản lý", "điều hành"],
                "domain": "banking"
            },
            "transfersTo": {
                "vietnamese_labels": ["chuyển đến", "gửi cho"],
                "domain": "banking"
            },
            "borrowsFrom": {
                "vietnamese_labels": ["vay từ", "đi vay tại"],
                "domain": "banking"
            },
            "depositsIn": {
                "vietnamese_labels": ["gửi vào", "gửi tiết kiệm tại"],
                "domain": "banking"
            },
            "appliesFor": {
                "vietnamese_labels": ["đăng ký", "mở"],
                "domain": "banking"
            }
        }

    async def get_ontology_class(self, class_id: int) -> Dict[str, Any]:
        """Get a Ontology class by ID"""
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
                detail=f"Error retrieving Ontology class: {str(e)}",
            )

    async def get_ontology_class_by_uri(self, uri: str) -> Dict[str, Any]:
        """Get a Ontology class by URI"""
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
                detail=f"Error retrieving Ontology class: {str(e)}",
            )

    async def create_ontology_class(
        self, ontology_class_in: OntologyClassCreate
    ) -> Dict[str, Any]:
        """Create a new Ontology class"""
        try:
            supabase = await get_supabase()
            # Check if class already exists by URI
            try:
                existing_class = await self.get_ontology_class_by_uri(
                    ontology_class_in.uri
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
                    detail="Failed to create Ontology class",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating Ontology class: {str(e)}",
            )

    async def update_ontology_class(
        self, class_id: int, ontology_class_in: OntologyClassUpdate
    ) -> Dict[str, Any]:
        """Update a Ontology class"""
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
                    detail="Failed to update Ontology class",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating Ontology class: {str(e)}",
            )

    async def delete_ontology_class(self, class_id: int) -> Dict[str, Any]:
        """Delete a Ontology class"""
        try:
            supabase = await get_supabase()
            # Check if class exists
            await self.get_ontology_class(class_id)

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
                detail=f"Error deleting Ontology class: {str(e)}",
            )

    async def get_ontology_classes(
        self,
        domain: Optional[str] = None,
        search: Optional[str] = None,
        is_custom: Optional[bool] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get Ontology classes with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("ontology_classes").select(
                "*", count=CountMethod.exact
            )

            if domain:
                query = query.eq("domain", domain)

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
                detail=f"Error retrieving Ontology classes: {str(e)}",
            )

    async def get_ontology_property(self, property_id: int) -> Dict[str, Any]:
        """Get a Ontology property by ID"""
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
                detail=f"Error retrieving Ontology property: {str(e)}",
            )

    async def get_ontology_property_by_uri(self, uri: str) -> Dict[str, Any]:
        """Get a Ontology property by URI"""
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
                detail=f"Error retrieving Ontology property: {str(e)}",
            )

    async def create_ontology_property(
        self, ontology_property_in: OntologyPropertyCreate
    ) -> Dict[str, Any]:
        """Create a new Ontology property"""
        try:
            supabase = await get_supabase()
            # Check if property already exists by URI
            try:
                existing_property = await self.get_ontology_property_by_uri(
                    ontology_property_in.uri
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
                    detail="Failed to create Ontology property",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating Ontology property: {str(e)}",
            )

    async def update_ontology_property(
        self, property_id: int, ontology_property_in: OntologyPropertyUpdate
    ) -> Dict[str, Any]:
        """Update a Ontology property"""
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
                    detail="Failed to update Ontology property",
                )

            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating Ontology property: {str(e)}",
            )

    async def delete_ontology_property(self, property_id: int) -> Dict[str, Any]:
        """Delete a Ontology property"""
        try:
            supabase = await get_supabase()
            # Check if property exists
            await self.get_ontology_property(property_id)

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
                detail=f"Error deleting Ontology property: {str(e)}",
            )

    async def get_ontology_properties(
        self,
        domain_class_id: Optional[int] = None,
        property_type: Optional[str] = None,
        search: Optional[str] = None,
        is_custom: Optional[bool] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> APIResponse[Dict[str, Any]]:
        """Get Ontology properties with filtering and pagination"""
        try:
            supabase = await get_supabase()
            query = supabase.from_("ontology_properties").select(
                "*", count=CountMethod.exact
            )

            if domain_class_id:
                query = query.eq("domain_class_id", domain_class_id)

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
                detail=f"Error retrieving Ontology properties: {str(e)}",
            )

    async def import_ontology_from_file(self, file_id: str) -> Dict[str, Any]:
        """Import Ontology ontology from an uploaded file"""
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
                    include_vietnamese_mappings=True
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

    async def _process_ontology_file(
        self, file_path: str, format: str
    ) -> Dict[str, Any]:
        """Process an ontology file and import classes and properties"""
        try:
            # Create RDF graph and parse the file
            g = Graph()
            g.parse(file_path, format=format)

            # Extract classes
            classes_imported = 0
            properties_imported = 0
            errors = []

            # Process classes (owl:Class)
            for s, p, o in g.triples((None, RDF.type, OWL.Class)):
                try:
                    uri = str(s)
                    label = None
                    description = None

                    # Get label
                    for _, _, label_literal in g.triples((s, RDFS.label, None)):
                        label = str(label_literal)
                        break

                    # Get description/comment
                    for _, _, desc_literal in g.triples((s, RDFS.comment, None)):
                        description = str(desc_literal)
                        break

                    # Get domain (extract from URI)
                    domain = None
                    if "ontology/ontology/" in uri:
                        parts = uri.split("ontology/ontology/")[1].split("/")
                        if len(parts) > 0:
                            domain = parts[0]

                    # Get parent class
                    parent_class_uri = None
                    for _, _, parent in g.triples((s, RDFS.subClassOf, None)):
                        if isinstance(parent, URIRef):
                            parent_class_uri = str(parent)
                            break

                    # Create or update the class
                    class_data = OntologyClassCreate(
                        uri=uri,
                        label=label,
                        description=description,
                        domain=domain,
                        parent_class_uri=parent_class_uri,
                        is_custom=False,
                    )

                    await self.create_ontology_class(class_data)
                    classes_imported += 1

                except Exception as e:
                    errors.append(f"Error processing class {s}: {str(e)}")

            # Process properties (owl:ObjectProperty and owl:DatatypeProperty)
            for property_type in [OWL.ObjectProperty, OWL.DatatypeProperty]:
                for s, p, o in g.triples((None, RDF.type, property_type)):
                    try:
                        uri = str(s)
                        label = None
                        description = None

                        # Get label
                        for _, _, label_literal in g.triples((s, RDFS.label, None)):
                            label = str(label_literal)
                            break

                        # Get description/comment
                        for _, _, desc_literal in g.triples((s, RDFS.comment, None)):
                            description = str(desc_literal)
                            break

                        # Get domain class
                        domain_class_uri = None
                        for _, _, domain in g.triples((s, RDFS.domain, None)):
                            if isinstance(domain, URIRef):
                                domain_class_uri = str(domain)
                                break

                        # Get range class
                        range_class_uri = None
                        for _, _, range_class in g.triples((s, RDFS.range, None)):
                            if isinstance(range_class, URIRef):
                                range_class_uri = str(range_class)
                                break

                        # Create or update the property
                        property_data = OntologyPropertyCreate(
                            uri=uri,
                            label=label,
                            description=description,
                            domain_class_uri=domain_class_uri,
                            range_class_uri=range_class_uri,
                            property_type=(
                                "object"
                                if property_type == OWL.ObjectProperty
                                else "datatype"
                            ),
                            is_custom=False,
                        )

                        await self.create_ontology_property(property_data)
                        properties_imported += 1

                    except Exception as e:
                        errors.append(f"Error processing property {s}: {str(e)}")

            return {
                "success": True,
                "message": f"Imported {classes_imported} classes and {properties_imported} properties",
                "classes_imported": classes_imported,
                "properties_imported": properties_imported,
                "errors": errors if errors else None,
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing ontology file: {str(e)}",
            )

    async def get_entity_mappings(
        self,
        entity_type_id: Optional[int] = None,
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
                "*, entity_types(name, display_name, color, icon)",
                count=CountMethod.exact,
            )

            if entity_type_id:
                query = query.eq("entity_type_id", entity_type_id)

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

            # Check if mapping already exists
            query = supabase.from_("entity_mappings").select("*")

            if mapping.entity_type_id:
                query = query.eq("entity_type_id", mapping.entity_type_id)
            elif mapping.entity_type:
                query = query.eq("entity_type", mapping.entity_type)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either entity_type or entity_type_id must be provided",
                )

            response = await query.execute()

            mapping_data = mapping.model_dump()
            if user_id:
                mapping_data["created_by"] = user_id

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
                        "ontology_class_uri": mapping.ontology_class_uri,
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
                # update entity.is_mapped
                await supabase.from_("entities").update({"is_mapped": True}).eq(
                    "id", mapping_data["entity_type_id"]
                ).execute()
                return insert_response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating entity mapping: {str(e)}",
            )

    async def update_entity_mapping(
        self, mapping_id: int, mapping: EntityMappingUpdate
    ) -> Dict[str, Any]:
        """Update an entity mapping"""
        try:
            supabase = await get_supabase()

            data = mapping.dict(exclude_unset=True)
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

    async def delete_entity_mapping(self, mapping_id: int) -> Dict[str, Any]:
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
        self, mapping_id: int, verified: bool, user_id: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify an entity mapping"""
        try:
            supabase = await get_supabase()

            update_data = {
                "is_verified": verified,
                "mapping_status": "mapped" if verified else "needs_review",
                "reviewed_by": user_id,
                "reviewed_at": datetime.utcnow().isoformat(),
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

    async def get_relationship_mappings(
        self,
        relationship_type_id: Optional[int] = None,
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
                "*, relationship_types(name, display_name, color), ontology_properties(uri, label)",
                count=CountMethod.exact,
            )

            if relationship_type_id:
                query = query.eq("relationship_type_id", relationship_type_id)

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
            response = (
                await supabase.from_("relationship_mappings")
                .select("*")
                .eq("relationship_type", mapping.relationship_type)
                .execute()
            )

            if response.data and len(response.data) > 0:
                # Update existing mapping
                mapping_data = mapping.dict()
                if user_id:
                    mapping_data["created_by"] = user_id

                update_response = (
                    await supabase.from_("relationship_mappings")
                    .update(mapping_data)
                    .eq("relationship_type", mapping.relationship_type)
                    .execute()
                )

                await self.user_service._log_user_activity(
                    user_id=user_id,
                    action="update_relationship_mapping",
                    details={
                        "relationship_type": mapping.relationship_type,
                        "ontology_property_uri": mapping.ontology_property_uri,
                    },
                )

                return update_response.data[0]
            else:
                # Create new mapping
                mapping_data = mapping.dict()
                if user_id:
                    mapping_data["created_by"] = user_id

                insert_response = (
                    await supabase.from_("relationship_mappings")
                    .insert(mapping_data)
                    .execute()
                )

                await supabase.from_("relationship_types").update(
                    {"is_mapped": True}
                ).eq("id", mapping.relationship_type_id).execute()

                await self.user_service._log_user_activity(
                    user_id=user_id,
                    action="create_relationship_mapping",
                    details={
                        "relationship_type": mapping.relationship_type,
                        "ontology_property_uri": mapping.ontology_property_uri,
                    },
                )

                return insert_response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating relationship mapping: {str(e)}",
            )

    async def update_relationship_mapping(
        self, relationship_type: str, mapping: RelationshipMappingUpdate
    ) -> Dict[str, Any]:
        """Update a relationship mapping"""
        try:
            supabase = await get_supabase()
            # Check if mapping exists
            response = (
                await supabase.from_("relationship_mappings")
                .select("*")
                .eq("relationship_type", relationship_type)
                .maybe_single()
                .execute()
            )
            if not response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship mapping not found",
                )
            # Prepare update data
            data = mapping.model_dump(exclude_unset=True)
            # Update the mapping
            update_response = (
                await supabase.from_("relationship_mappings")
                .update(data)
                .eq("relationship_type", relationship_type)
                .execute()
            )
            return update_response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating relationship mapping: {str(e)}",
            )

    async def delete_relationship_mapping(
        self, relationship_type: str
    ) -> Dict[str, Any]:
        """Delete a relationship mapping"""
        try:
            supabase = await get_supabase()
            await supabase.from_("relationship_mappings").delete().eq(
                "relationship_type", relationship_type
            ).execute()

            return {"success": True, "message": "Relationship mapping deleted"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting relationship mapping: {str(e)}",
            )

    async def get_entity_ontology_class(
        self, entity_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get Ontology class for an entity type using mappings"""
        try:
            supabase = await get_supabase()
            # First check mapping table
            response = (
                await supabase.from_("entity_mappings")
                .select("*")
                .eq("entity_type", entity_type)
                .execute()
            )

            if response.data and len(response.data) > 0:
                mapping = response.data[0]
                ontology_class_uri = mapping.get("ontology_class_uri")

                if ontology_class_uri:
                    try:
                        return await self.get_ontology_class_by_uri(ontology_class_uri)
                    except HTTPException:
                        pass

            # If no mapping found or class not found, try to find by similarity
            classes = await self.get_ontology_classes(search=entity_type, limit=1)

            if classes:
                return classes.data[0]

            return None
        except Exception as e:
            print(f"Error getting entity Ontology class: {e}")
            return None

    async def get_relationship_ontology_property(
        self, relationship_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get Ontology property for a relationship type using mappings"""
        try:
            supabase = await get_supabase()
            # First check mapping table
            response = (
                await supabase.from_("relationship_mappings")
                .select("*")
                .eq("relationship_type", relationship_type)
                .execute()
            )

            if response.data and len(response.data) > 0:
                mapping = response.data[0]
                ontology_property_uri = mapping.get("ontology_property_uri")

                if ontology_property_uri:
                    try:
                        return await self.get_ontology_property_by_uri(
                            ontology_property_uri
                        )
                    except HTTPException:
                        pass

            # If no mapping found or property not found, try to find by similarity
            properties = await self.get_ontology_properties(
                search=relationship_type, limit=1
            )

            if properties:
                return properties.data[0]

            return None
        except Exception as e:
            print(f"Error getting relationship Ontology property: {e}")
            return None

    async def suggest_ontology_class_for_entity(
        self,
        entity_text: str,
        entity_type: str,
        properties: Optional[Dict[str, Any]] = None,
        max_suggestions: int = 5,
    ) -> List[Dict[str, Any]]:
        """Suggest Ontology classes for an entity based on text similarity"""
        try:
            # First try to get from mapping
            mapped_class = await self.get_entity_ontology_class(entity_type)

            if mapped_class:
                return [mapped_class]

            # Search for similar classes
            suggestions = []

            # Try to find by entity type
            type_results = await self.get_ontology_classes(
                search=entity_type, limit=max_suggestions
            )
            suggestions.extend(type_results)

            # Try to find by text
            if entity_text and len(suggestions) < max_suggestions:
                remaining = max_suggestions - len(suggestions)

                # Extract keywords from entity text
                keywords = entity_text.split()
                for keyword in keywords:
                    if len(keyword) > 3:  # Only use longer keywords
                        text_results = await self.get_ontology_classes(
                            search=keyword, limit=remaining
                        )

                        # Add only new suggestions
                        for result in text_results:
                            if result["id"] not in [s["id"] for s in suggestions]:
                                suggestions.append(result)

                                if len(suggestions) >= max_suggestions:
                                    break

                    if len(suggestions) >= max_suggestions:
                        break

            # If no suggestions found, get top classes for relevant domains
            if not suggestions:
                banking_classes = await self.get_ontology_classes(
                    domain="FBC", limit=max_suggestions
                )
                suggestions.extend(banking_classes)

            return suggestions
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error suggesting Ontology classes: {str(e)}",
            )

    async def suggest_ontology_property_for_relationship(
        self,
        relationship_type: str,
        source_entity_type: str,
        target_entity_type: str,
        max_suggestions: int = 5,
    ) -> List[Dict[str, Any]]:
        """Suggest Ontology properties for a relationship based on entity types and relationship type"""
        try:
            supabase = await get_supabase()
            # First try to get from mapping
            mapped_property = await self.get_relationship_ontology_property(
                relationship_type
            )

            if mapped_property:
                return [mapped_property]

            suggestions = []

            # Get Ontology classes for source and target entity types
            source_class = await self.get_entity_ontology_class(source_entity_type)
            target_class = await self.get_entity_ontology_class(target_entity_type)

            # If we have both classes, look for properties that connect them
            if source_class and target_class:
                query = f"""
                SELECT p.*
                FROM ontology_properties p
                WHERE 
                    (p.domain_class_id = '{source_class["id"]}' AND p.range_class_id = '{target_class["id"]}')
                    OR p.label ILIKE '%{relationship_type}%'
                    OR p.uri ILIKE '%{relationship_type}%'
                LIMIT {max_suggestions}
                """

                response = await supabase.rpc(
                    "exec_sql", {"sql_query": query}
                ).execute()

                if response.data:
                    suggestions.extend(response.data)

            # If we don't have enough suggestions, search by relationship type
            if len(suggestions) < max_suggestions:
                remaining = max_suggestions - len(suggestions)
                type_results = await self.get_ontology_properties(
                    search=relationship_type, limit=remaining
                )

                # Add only new suggestions
                for result in type_results:
                    if result["id"] not in [s["id"] for s in suggestions]:
                        suggestions.append(result)

            # If still no suggestions, get object properties
            if not suggestions:
                default_properties = await self.get_ontology_properties(
                    property_type="object", limit=max_suggestions
                )
                suggestions.extend(default_properties)

            return suggestions
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error suggesting Ontology properties: {str(e)}",
            )

    async def verify_relationship_mapping(
        self, relationship_type: str, verified: bool, user_id: str
    ) -> Dict[str, Any]:
        """Verify a relationship mapping"""
        try:
            supabase = await get_supabase()
            # Check if mapping exists
            response = (
                await supabase.from_("relationship_mappings")
                .select("*")
                .eq("relationship_type", relationship_type)
                .execute()
            )

            if not response.data or len(response.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship mapping not found",
                )

            # Update verification status
            update_data = {
                "is_verified": verified,
                "verified_by": user_id if verified else None,
                "verified_at": datetime.utcnow().isoformat() if verified else None,
            }

            update_response = (
                await supabase.from_("relationship_mappings")
                .update(update_data)
                .eq("relationship_type", relationship_type)
                .execute()
            )

            await self.user_service._log_user_activity(
                user_id=user_id,
                action="verify_relationship_mapping",
                details={
                    "relationship_type": relationship_type,
                    "is_verified": verified,
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

    async def suggest_entity_types(
        self,
        text: str,
        context: Optional[str] = None,
        domain_id: Optional[int] = None,
        max_suggestions: int = 5,
    ) -> List[Dict[str, Any]]:
        """Suggest entity types based on text"""
        try:
            supabase = await get_supabase()

            # Simple text-based matching for now
            query = supabase.from_("entity_types").select("*").eq("is_active", True)

            if domain_id:
                query = query.eq("entity_type_domains.domain_id", domain_id)

            # Search by name similarity
            query = query.or_(f"name.ilike.%{text}%,display_name.ilike.%{text}%")
            query = query.limit(max_suggestions)

            response = await query.execute()

            # Add confidence scoring
            suggestions = []
            for item in response.data:
                confidence = 0.8 if text.lower() in item["name"].lower() else 0.6
                suggestions.append(
                    {
                        "entity_type": item,
                        "confidence": confidence,
                        "reason": f"Text match with '{item['name']}'",
                    }
                )

            return suggestions
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error suggesting entity types: {str(e)}",
            )

    async def suggest_relationship_types(
        self,
        text: str,
        source_entity_type_id: Optional[int] = None,
        target_entity_type_id: Optional[int] = None,
        context: Optional[str] = None,
        domain_id: Optional[int] = None,
        max_suggestions: int = 5,
    ) -> List[Dict[str, Any]]:
        """Suggest relationship types based on text and entity types"""
        try:
            supabase = await get_supabase()

            query = (
                supabase.from_("relationship_types").select("*").eq("is_active", True)
            )

            if domain_id:
                query = query.eq("relationship_type_domains.domain_id", domain_id)

            # Search by name similarity
            query = query.or_(f"name.ilike.%{text}%,display_name.ilike.%{text}%")
            query = query.limit(max_suggestions)

            response = await query.execute()

            # Add confidence scoring and constraint checking
            suggestions = []
            for item in response.data:
                confidence = 0.8 if text.lower() in item["name"].lower() else 0.6

                # Check entity type constraints
                source_valid = True
                target_valid = True

                if source_entity_type_id and item.get("source_entity_types"):
                    source_valid = source_entity_type_id in item["source_entity_types"]

                if target_entity_type_id and item.get("target_entity_types"):
                    target_valid = target_entity_type_id in item["target_entity_types"]

                if source_valid and target_valid:
                    suggestions.append(
                        {
                            "relationship_type": item,
                            "confidence": confidence,
                            "reason": f"Text match with '{item['name']}'",
                        }
                    )

            return suggestions
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error suggesting relationship types: {str(e)}",
            )

    # ==============================================
    # BULK OPERATIONS
    # ==============================================

    async def bulk_create_entity_mappings(
        self, mappings: List[EntityMappingCreate], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Bulk create entity mappings"""
        try:
            supabase = await get_supabase()

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

    # ==============================================
    # STATS OPERATIONS
    # ==============================================

    async def get_mapping_stats(
        self, domain_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get mapping statistics"""
        try:
            supabase = await get_supabase()

            # Entity mapping stats
            entity_query = supabase.from_("entity_mappings").select(
                "mapping_status, is_verified, auto_mapped"
            )
            if domain_id:
                entity_query = entity_query.eq(
                    "entity_types.entity_type_domains.domain_id", domain_id
                )

            entity_response = await entity_query.execute()

            # Relationship mapping stats
            relationship_query = supabase.from_("relationship_mappings").select(
                "mapping_status, is_verified, auto_mapped"
            )
            if domain_id:
                relationship_query = relationship_query.eq(
                    "relationship_types.relationship_type_domains.domain_id", domain_id
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

    async def load_fibo_ontology(
        self, 
        fibo_file_path: str, 
        domain_filter: Optional[str] = None,
        include_vietnamese_mappings: bool = True
    ) -> Dict[str, Any]:
        """
        Load FIBO ontology from RDF file into database
        
        Args:
            fibo_file_path: Path to FIBO RDF/OWL file
            domain_filter: Filter by specific domain (e.g., 'banking', 'securities')
            include_vietnamese_mappings: Whether to add Vietnamese language mappings
            
        Returns:
            Loading results with statistics
        """
        if not RDFLIB_AVAILABLE:
            raise ValueError("rdflib is required for FIBO ontology loading. Install with: pip install rdflib")
        
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
                properties = await self._add_vietnamese_mappings_to_properties(properties)
            
            # Save to database
            results = await self._save_ontology_to_database(classes, properties)
            
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
            '.owl': 'xml',
            '.rdf': 'xml', 
            '.xml': 'xml',
            '.ttl': 'turtle',
            '.n3': 'n3',
            '.nt': 'nt',
            '.jsonld': 'json-ld'
        }
        
        return format_map.get(extension, 'xml')  # Default to XML

    async def _extract_fibo_classes(
        self, 
        graph: Graph, 
        domain_filter: Optional[str] = None
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
        self, 
        graph: Graph, 
        class_uri: URIRef,
        domain_filter: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Extract information for a single class"""
        try:
            uri_str = str(class_uri)
            
            # Apply domain filter
            if domain_filter and not self._matches_domain_filter(uri_str, domain_filter):
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
                    "namespace": self._extract_namespace(uri_str)
                }
            }
            
            return class_info
            
        except Exception as e:
            logger.warning(f"Error extracting class info for {class_uri}: {e}")
            return None

    async def _extract_fibo_properties(
        self, 
        graph: Graph, 
        domain_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract properties from FIBO ontology"""
        properties = []
        
        # Query for object properties
        for subj in graph.subjects(RDF.type, OWL.ObjectProperty):
            prop_info = await self._extract_property_info(graph, subj, "object", domain_filter)
            if prop_info:
                properties.append(prop_info)
        
        # Query for datatype properties
        for subj in graph.subjects(RDF.type, OWL.DatatypeProperty):
            prop_info = await self._extract_property_info(graph, subj, "datatype", domain_filter)
            if prop_info:
                properties.append(prop_info)
        
        logger.info(f"Extracted {len(properties)} properties from FIBO")
        return properties

    async def _extract_property_info(
        self, 
        graph: Graph, 
        property_uri: URIRef,
        property_type: str,
        domain_filter: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Extract information for a single property"""
        try:
            uri_str = str(property_uri)
            
            # Apply domain filter
            if domain_filter and not self._matches_domain_filter(uri_str, domain_filter):
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
                "is_custom": False
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
        name = uri.split('#')[-1] if '#' in uri else uri.split('/')[-1]
        
        # Convert CamelCase to readable format
        name = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
        
        return name

    def _extract_namespace(self, uri: str) -> str:
        """Extract namespace from URI"""
        if '#' in uri:
            return uri.split('#')[0] + '#'
        else:
            parts = uri.split('/')
            return '/'.join(parts[:-1]) + '/'

    def _determine_fibo_domain(self, uri: str) -> str:
        """Determine FIBO domain based on URI structure"""
        uri_lower = uri.lower()
        
        if 'fnd' in uri_lower:
            return 'foundations'
        elif 'sec' in uri_lower:
            return 'securities'
        elif 'loan' in uri_lower:
            return 'loans'
        elif 'der' in uri_lower:
            return 'derivatives'
        elif 'ins' in uri_lower:
            return 'insurance'
        elif any(banking_term in uri_lower for banking_term in ['bank', 'account', 'deposit', 'payment']):
            return 'banking'
        else:
            return 'general'

    def _matches_domain_filter(self, uri: str, domain_filter: str) -> bool:
        """Check if URI matches domain filter"""
        determined_domain = self._determine_fibo_domain(uri)
        return determined_domain == domain_filter or domain_filter == 'general'

    async def _add_vietnamese_mappings_to_classes(
        self, 
        classes: List[Dict[str, Any]]
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
                
                class_info["properties"]["vietnamese_labels"] = mapping["vietnamese_labels"]
                class_info["domain"] = mapping.get("domain", class_info.get("domain"))
                
                # Update description to include Vietnamese context
                if mapping["vietnamese_labels"]:
                    vietnamese_desc = f"Tiếng Việt: {', '.join(mapping['vietnamese_labels'])}"
                    if class_info.get("description"):
                        class_info["description"] += f" ({vietnamese_desc})"
                    else:
                        class_info["description"] = vietnamese_desc
        
        return classes

    async def _add_vietnamese_mappings_to_properties(
        self, 
        properties: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Add Vietnamese language mappings to properties"""
        for prop_info in properties:
            label = prop_info.get("label", "")
            
            # Check if we have Vietnamese mappings for this property
            if label in self.vietnamese_relationship_mappings:
                mapping = self.vietnamese_relationship_mappings[label]
                
                # Add Vietnamese labels to description
                if mapping["vietnamese_labels"]:
                    vietnamese_desc = f"Tiếng Việt: {', '.join(mapping['vietnamese_labels'])}"
                    if prop_info.get("description"):
                        prop_info["description"] += f" ({vietnamese_desc})"
                    else:
                        prop_info["description"] = vietnamese_desc
                
                prop_info["domain"] = mapping.get("domain", prop_info.get("domain"))
        
        return properties

    async def _save_ontology_to_database(
        self, 
        classes: List[Dict[str, Any]], 
        properties: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Save extracted ontology to database"""
        try:
            supabase = await get_supabase()
            
            results = {
                "classes_added": 0,
                "properties_added": 0,
                "classes_updated": 0,
                "properties_updated": 0,
                "errors": []
            }
            
            # Create URI to ID mapping for parent class resolution
            uri_to_id_map = {}
            
            # First pass: Insert/update classes
            for class_info in classes:
                try:
                    # Check if class already exists
                    existing_response = await supabase.from_("ontology_classes").select("id").eq("uri", class_info["uri"]).execute()
                    
                    class_data = {
                        "uri": class_info["uri"],
                        "label": class_info["label"],
                        "description": class_info["description"],
                        "domain": class_info["domain"],
                        "is_custom": class_info["is_custom"],
                        "properties": class_info.get("properties", {})
                    }
                    
                    if existing_response.data:
                        # Update existing class
                        class_id = existing_response.data[0]["id"]
                        await supabase.from_("ontology_classes").update(class_data).eq("id", class_id).execute()
                        results["classes_updated"] += 1
                        uri_to_id_map[class_info["uri"]] = class_id
                    else:
                        # Insert new class
                        response = await supabase.from_("ontology_classes").insert(class_data).execute()
                        if response.data:
                            class_id = response.data[0]["id"]
                            results["classes_added"] += 1
                            uri_to_id_map[class_info["uri"]] = class_id
                            
                except Exception as e:
                    error_msg = f"Error saving class {class_info.get('label', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # Second pass: Update parent class relationships
            for class_info in classes:
                if class_info.get("parent_class_uri") and class_info["uri"] in uri_to_id_map:
                    parent_class_uri = class_info["parent_class_uri"]
                    if parent_class_uri in uri_to_id_map:
                        try:
                            class_id = uri_to_id_map[class_info["uri"]]
                            parent_id = uri_to_id_map[parent_class_uri]
                            
                            await supabase.from_("ontology_classes").update(
                                {"parent_class_id": parent_id}
                            ).eq("id", class_id).execute()
                            
                        except Exception as e:
                            logger.warning(f"Error updating parent class relationship: {e}")
            
            # Third pass: Insert/update properties
            for prop_info in properties:
                try:
                    # Check if property already exists
                    existing_response = await supabase.from_("ontology_properties").select("id").eq("uri", prop_info["uri"]).execute()
                    
                    # Resolve domain and range class IDs
                    domain_class_id = None
                    range_class_id = None
                    
                    if prop_info.get("domain_class_uri"):
                        domain_class_id = uri_to_id_map.get(prop_info["domain_class_uri"])
                    
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
                        "is_custom": prop_info.get("is_custom", False)
                    }
                    
                    if existing_response.data:
                        # Update existing property
                        property_id = existing_response.data[0]["id"]
                        await supabase.from_("ontology_properties").update(property_data).eq("id", property_id).execute()
                        results["properties_updated"] += 1
                    else:
                        # Insert new property
                        response = await supabase.from_("ontology_properties").insert(property_data).execute()
                        if response.data:
                            results["properties_added"] += 1
                            
                except Exception as e:
                    error_msg = f"Error saving property {prop_info.get('label', 'unknown')}: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"FIBO ontology save completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error saving ontology to database: {e}")
            raise

    async def create_vietnamese_banking_extensions(self) -> Dict[str, Any]:
        """
        Create Vietnamese-specific banking extensions to FIBO ontology
        """
        try:
            logger.info("Creating Vietnamese banking extensions")
            
            # Vietnamese-specific banking classes
            vietnamese_classes = [
                {
                    "uri": "http://vietnamese.banking.ontology/VietnamBank",
                    "label": "Ngân hàng Việt Nam",
                    "description": "Ngân hàng hoạt động tại Việt Nam theo quy định của Ngân hàng Nhà nước Việt Nam",
                    "domain": "banking",
                    "is_custom": True,
                    "properties": {
                        "vietnamese_labels": ["ngân hàng", "nh", "ngân hàng việt nam"],
                        "country": "Vietnam",
                        "regulatory_authority": "State Bank of Vietnam"
                    }
                },
                {
                    "uri": "http://vietnamese.banking.ontology/VNDCurrency",
                    "label": "Đồng Việt Nam",
                    "description": "Đơn vị tiền tệ chính thức của Việt Nam",
                    "domain": "banking",
                    "is_custom": True,
                    "properties": {
                        "vietnamese_labels": ["vnd", "đồng", "việt nam đồng"],
                        "currency_code": "VND",
                        "country": "Vietnam"
                    }
                },
                {
                    "uri": "http://vietnamese.banking.ontology/InterBankTransfer",
                    "label": "Chuyển khoản liên ngân hàng",
                    "description": "Giao dịch chuyển tiền giữa các ngân hàng khác nhau tại Việt Nam",
                    "domain": "banking",
                    "is_custom": True,
                    "properties": {
                        "vietnamese_labels": ["chuyển khoản liên ngân hàng", "chuyển khoản ln"],
                        "transaction_type": "inter_bank"
                    }
                },
                {
                    "uri": "http://vietnamese.banking.ontology/VietQR",
                    "label": "VietQR",
                    "description": "Hệ thống thanh toán QR Code của Việt Nam",
                    "domain": "banking",
                    "is_custom": True,
                    "properties": {
                        "vietnamese_labels": ["vietqr", "qr pay", "thanh toán qr"],
                        "payment_method": "QR_code"
                    }
                },
                {
                    "uri": "http://vietnamese.banking.ontology/CITADAccount",
                    "label": "Tài khoản thanh toán CITAD",
                    "description": "Tài khoản tham gia hệ thống thanh toán điện tử liên ngân hàng CITAD",
                    "domain": "banking",
                    "is_custom": True,
                    "properties": {
                        "vietnamese_labels": ["tài khoản citad", "tk citad"],
                        "system": "CITAD"
                    }
                }
            ]
            
            # Vietnamese-specific banking properties
            vietnamese_properties = [
                {
                    "uri": "http://vietnamese.banking.ontology/hasVietQRCode",
                    "label": "Có mã VietQR",
                    "description": "Mối quan hệ giữa tài khoản và mã VietQR tương ứng",
                    "property_type": "object",
                    "domain": "banking",
                    "is_custom": True
                },
                {
                    "uri": "http://vietnamese.banking.ontology/regulatedBy",
                    "label": "Được quản lý bởi",
                    "description": "Mối quan hệ giữa ngân hàng và cơ quan quản lý",
                    "property_type": "object",
                    "domain": "banking",
                    "is_custom": True
                },
                {
                    "uri": "http://vietnamese.banking.ontology/participatesInCITAD",
                    "label": "Tham gia CITAD",
                    "description": "Ngân hàng tham gia hệ thống thanh toán CITAD",
                    "property_type": "object",
                    "domain": "banking",
                    "is_custom": True
                },
                {
                    "uri": "http://vietnamese.banking.ontology/usesVNDCurrency",
                    "label": "Sử dụng tiền Việt Nam",
                    "description": "Giao dịch sử dụng đồng Việt Nam",
                    "property_type": "object",
                    "domain": "banking",
                    "is_custom": True
                }
            ]
            
            # Save Vietnamese extensions to database
            results = await self._save_ontology_to_database(vietnamese_classes, vietnamese_properties)
            
            logger.info(f"Created Vietnamese banking extensions: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error creating Vietnamese banking extensions: {e}")
            raise


    async def get_ontology_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded ontology
        """
        try:
            supabase = await get_supabase()
            
            # Count classes by domain
            classes_response = await supabase.from_("ontology_classes").select("domain, is_custom").execute()
            
            class_stats = {}
            custom_class_count = 0
            for cls in classes_response.data:
                domain = cls.get("domain", "unknown")
                class_stats[domain] = class_stats.get(domain, 0) + 1
                if cls.get("is_custom"):
                    custom_class_count += 1
            
            # Count properties by domain
            properties_response = await supabase.from_("ontology_properties").select("domain, is_custom").execute()
            
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
                "domains": list(set(list(class_stats.keys()) + list(property_stats.keys())))
            }
            
        except Exception as e:
            logger.error(f"Error getting ontology statistics: {e}")
            return {}
