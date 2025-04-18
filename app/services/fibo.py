# app/services/fibo.py
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status, UploadFile
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
import requests
import tempfile
import os
import uuid
from datetime import datetime

from app.core.supabase import get_supabase
from app.schemas.fibo import (
    FIBOClassCreate, 
    FIBOClassUpdate, 
    FIBOPropertyCreate, 
    FIBOPropertyUpdate,
    EntityMapping,
    RelationshipMapping
)
from app.services.datasource import DataSourceService


class FIBOService:
    def __init__(self):
        self.supabase = get_supabase()
        
        # Common namespaces for FIBO
        self.fibo = Namespace("https://spec.edmcouncil.org/fibo/ontology/")
        self.fibo_fbc = Namespace("https://spec.edmcouncil.org/fibo/ontology/FBC/")
        self.fibo_loan = Namespace("https://spec.edmcouncil.org/fibo/ontology/LOAN/")
        self.fibo_fnd = Namespace("https://spec.edmcouncil.org/fibo/ontology/FND/")

    async def get_fibo_class(self, class_id: int) -> Dict[str, Any]:
        """Get a FIBO class by ID"""
        try:
            response = self.supabase.from_("fibo_classes").select("*").eq("id", class_id).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="FIBO class not found"
                )
                
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving FIBO class: {str(e)}"
            )

    async def get_fibo_class_by_uri(self, uri: str) -> Dict[str, Any]:
        """Get a FIBO class by URI"""
        try:
            response = self.supabase.from_("fibo_classes").select("*").eq("uri", uri).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="FIBO class not found"
                )
                
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving FIBO class: {str(e)}"
            )

    async def create_fibo_class(self, fibo_class_in: FIBOClassCreate) -> Dict[str, Any]:
        """Create a new FIBO class"""
        try:
            # Check if class already exists by URI
            try:
                existing_class = await self.get_fibo_class_by_uri(fibo_class_in.uri)
                return existing_class
            except HTTPException as e:
                if e.status_code != status.HTTP_404_NOT_FOUND:
                    raise
            
            # Get parent class ID if provided
            parent_class_id = None
            if fibo_class_in.parent_class_uri:
                try:
                    parent = await self.get_fibo_class_by_uri(fibo_class_in.parent_class_uri)
                    parent_class_id = parent["id"]
                except HTTPException:
                    pass
            
            # Create the class
            data = fibo_class_in.dict(exclude={"parent_class_uri"})
            data["parent_class_id"] = parent_class_id
            
            response = self.supabase.from_("fibo_classes").insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create FIBO class"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating FIBO class: {str(e)}"
            )

    async def update_fibo_class(
        self, 
        class_id: int, 
        fibo_class_in: FIBOClassUpdate
    ) -> Dict[str, Any]:
        """Update a FIBO class"""
        try:
            # Check if class exists
            await self.get_fibo_class(class_id)
            
            # Prepare update data
            data = fibo_class_in.dict(exclude_unset=True, exclude={"parent_class_uri"})
            
            # Get parent class ID if provided
            if fibo_class_in.parent_class_uri is not None:
                if fibo_class_in.parent_class_uri:
                    try:
                        parent = await self.get_fibo_class_by_uri(fibo_class_in.parent_class_uri)
                        data["parent_class_id"] = parent["id"]
                    except HTTPException:
                        data["parent_class_id"] = None
                else:
                    data["parent_class_id"] = None
            
            # Update the class
            response = self.supabase.from_("fibo_classes").update(data).eq("id", class_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update FIBO class"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating FIBO class: {str(e)}"
            )

    async def delete_fibo_class(self, class_id: int) -> Dict[str, Any]:
        """Delete a FIBO class"""
        try:
            # Check if class exists
            await self.get_fibo_class(class_id)
            
            # Delete the class
            self.supabase.from_("fibo_classes").delete().eq("id", class_id).execute()
            
            return {"success": True, "message": "FIBO class deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting FIBO class: {str(e)}"
            )

    async def get_fibo_classes(
        self,
        domain: Optional[str] = None,
        search: Optional[str] = None,
        is_custom: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get FIBO classes with filtering and pagination"""
        try:
            query = self.supabase.from_("fibo_classes").select("*")
            
            if domain:
                query = query.eq("domain", domain)
                
            if is_custom is not None:
                query = query.eq("is_custom", is_custom)
                
            if search:
                # Search in label and URI
                query = query.or_(f"label.ilike.%{search}%,uri.ilike.%{search}%")
            
            response = query.range(offset, offset + limit - 1).execute()
            
            return response.data or []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving FIBO classes: {str(e)}"
            )

    async def get_fibo_property(self, property_id: int) -> Dict[str, Any]:
        """Get a FIBO property by ID"""
        try:
            response = self.supabase.from_("fibo_properties").select("*").eq("id", property_id).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="FIBO property not found"
                )
                
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving FIBO property: {str(e)}"
            )

    async def get_fibo_property_by_uri(self, uri: str) -> Dict[str, Any]:
        """Get a FIBO property by URI"""
        try:
            response = self.supabase.from_("fibo_properties").select("*").eq("uri", uri).single().execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="FIBO property not found"
                )
                
            return response.data
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving FIBO property: {str(e)}"
            )

    async def create_fibo_property(self, fibo_property_in: FIBOPropertyCreate) -> Dict[str, Any]:
        """Create a new FIBO property"""
        try:
            # Check if property already exists by URI
            try:
                existing_property = await self.get_fibo_property_by_uri(fibo_property_in.uri)
                return existing_property
            except HTTPException as e:
                if e.status_code != status.HTTP_404_NOT_FOUND:
                    raise
            
            # Get domain and range class IDs if provided
            domain_class_id = None
            range_class_id = None
            
            if fibo_property_in.domain_class_uri:
                try:
                    domain_class = await self.get_fibo_class_by_uri(fibo_property_in.domain_class_uri)
                    domain_class_id = domain_class["id"]
                except HTTPException:
                    pass
            
            if fibo_property_in.range_class_uri:
                try:
                    range_class = await self.get_fibo_class_by_uri(fibo_property_in.range_class_uri)
                    range_class_id = range_class["id"]
                except HTTPException:
                    pass
            
            # Create the property
            data = fibo_property_in.dict(exclude={"domain_class_uri", "range_class_uri"})
            data["domain_class_id"] = domain_class_id
            data["range_class_id"] = range_class_id
            
            response = self.supabase.from_("fibo_properties").insert(data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create FIBO property"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating FIBO property: {str(e)}"
            )

    async def update_fibo_property(
        self, 
        property_id: int, 
        fibo_property_in: FIBOPropertyUpdate
    ) -> Dict[str, Any]:
        """Update a FIBO property"""
        try:
            # Check if property exists
            await self.get_fibo_property(property_id)
            
            # Prepare update data
            data = fibo_property_in.dict(exclude_unset=True, exclude={"domain_class_uri", "range_class_uri"})
            
            # Get domain class ID if provided
            if fibo_property_in.domain_class_uri is not None:
                if fibo_property_in.domain_class_uri:
                    try:
                        domain_class = await self.get_fibo_class_by_uri(fibo_property_in.domain_class_uri)
                        data["domain_class_id"] = domain_class["id"]
                    except HTTPException:
                        data["domain_class_id"] = None
                else:
                    data["domain_class_id"] = None
            
            # Get range class ID if provided
            if fibo_property_in.range_class_uri is not None:
                if fibo_property_in.range_class_uri:
                    try:
                        range_class = await self.get_fibo_class_by_uri(fibo_property_in.range_class_uri)
                        data["range_class_id"] = range_class["id"]
                    except HTTPException:
                        data["range_class_id"] = None
                else:
                    data["range_class_id"] = None
            
            # Update the property
            response = self.supabase.from_("fibo_properties").update(data).eq("id", property_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update FIBO property"
                )
                
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating FIBO property: {str(e)}"
            )

    async def delete_fibo_property(self, property_id: int) -> Dict[str, Any]:
        """Delete a FIBO property"""
        try:
            # Check if property exists
            await self.get_fibo_property(property_id)
            
            # Delete the property
            self.supabase.from_("fibo_properties").delete().eq("id", property_id).execute()
            
            return {"success": True, "message": "FIBO property deleted"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting FIBO property: {str(e)}"
            )

    async def get_fibo_properties(
        self,
        domain_class_id: Optional[int] = None,
        property_type: Optional[str] = None,
        search: Optional[str] = None,
        is_custom: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get FIBO properties with filtering and pagination"""
        try:
            query = self.supabase.from_("fibo_properties").select("*")
            
            if domain_class_id:
                query = query.eq("domain_class_id", domain_class_id)
                
            if property_type:
                query = query.eq("property_type", property_type)
                
            if is_custom is not None:
                query = query.eq("is_custom", is_custom)
                
            if search:
                # Search in label and URI
                query = query.or_(f"label.ilike.%{search}%,uri.ilike.%{search}%")
            
            response = query.range(offset, offset + limit - 1).execute()
            
            return response.data or []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving FIBO properties: {str(e)}"
            )

    async def import_ontology_from_file(self, file_id: str) -> Dict[str, Any]:
        """Import FIBO ontology from an uploaded file"""
        try:
            # Get file content
            datasource_service = DataSourceService()
            file_info = await datasource_service.get_file_upload(file_upload_id=file_id)
            file_content = await datasource_service.get_file_content(file_upload_id=file_id)
            
            # Determine format based on file type
            file_format = "rdf"  # Default
            if file_info["file_name"].endswith(".ttl"):
                file_format = "turtle"
            elif file_info["file_name"].endswith(".owl"):
                file_format = "xml"
            
            # Process the ontology
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                import_result = await self._process_ontology_file(temp_file_path, file_format)
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
                detail=f"Error importing ontology: {str(e)}"
            )

    async def import_ontology_from_url(self, url: str, format: str = "rdf") -> Dict[str, Any]:
        """Import FIBO ontology from a URL"""
        try:
            # Download the ontology file
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            try:
                # Process the ontology
                file_format = "xml" if format == "rdf" else format
                if format == "owl":
                    file_format = "xml"
                elif format == "ttl":
                    file_format = "turtle"
                
                import_result = await self._process_ontology_file(temp_file_path, file_format)
            finally:
                # Clean up temp file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
            return import_result
        except HTTPException:
            raise
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error downloading ontology: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error importing ontology: {str(e)}"
            )

    async def _process_ontology_file(self, file_path: str, format: str) -> Dict[str, Any]:
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
                    if "fibo/ontology/" in uri:
                        parts = uri.split("fibo/ontology/")[1].split("/")
                        if len(parts) > 0:
                            domain = parts[0]
                    
                    # Get parent class
                    parent_class_uri = None
                    for _, _, parent in g.triples((s, RDFS.subClassOf, None)):
                        if isinstance(parent, URIRef):
                            parent_class_uri = str(parent)
                            break
                    
                    # Create or update the class
                    class_data = FIBOClassCreate(
                        uri=uri,
                        label=label,
                        description=description,
                        domain=domain,
                        parent_class_uri=parent_class_uri,
                        is_custom=False
                    )
                    
                    await self.create_fibo_class(class_data)
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
                        property_data = FIBOPropertyCreate(
                            uri=uri,
                            label=label,
                            description=description,
                            domain_class_uri=domain_class_uri,
                            range_class_uri=range_class_uri,
                            property_type="object" if property_type == OWL.ObjectProperty else "datatype",
                            is_custom=False
                        )
                        
                        await self.create_fibo_property(property_data)
                        properties_imported += 1
                        
                    except Exception as e:
                        errors.append(f"Error processing property {s}: {str(e)}")
            
            return {
                "success": True,
                "message": f"Imported {classes_imported} classes and {properties_imported} properties",
                "classes_imported": classes_imported,
                "properties_imported": properties_imported,
                "errors": errors if errors else None
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing ontology file: {str(e)}"
            )

    async def get_entity_mappings(
        self,
        verified_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get entity mappings"""
        try:
            query = self.supabase.from_("entity_mappings").select("*")
            
            if verified_only:
                query = query.eq("is_verified", True)
            
            response = query.range(offset, offset + limit - 1).execute()
            
            return response.data or []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving entity mappings: {str(e)}"
            )

    async def create_entity_mapping(
        self,
        mapping: EntityMapping,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update an entity mapping"""
        try:
            # Check if mapping already exists
            response = self.supabase.from_("entity_mappings").select("*").eq("entity_type", mapping.entity_type).execute()
            
            if response.data and len(response.data) > 0:
                # Update existing mapping
                mapping_data = mapping.dict()
                if user_id:
                    mapping_data["created_by"] = user_id
                
                update_response = self.supabase.from_("entity_mappings").update(mapping_data).eq("entity_type", mapping.entity_type).execute()
                
                return update_response.data[0]
            else:
                # Create new mapping
                mapping_data = mapping.dict()
                if user_id:
                    mapping_data["created_by"] = user_id
                
                insert_response = self.supabase.from_("entity_mappings").insert(mapping_data).execute()
                
                return insert_response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating entity mapping: {str(e)}"
            )

    async def delete_entity_mapping(self, entity_type: str) -> Dict[str, Any]:
        """Delete an entity mapping"""
        try:
            self.supabase.from_("entity_mappings").delete().eq("entity_type", entity_type).execute()
            
            return {"success": True, "message": "Entity mapping deleted"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting entity mapping: {str(e)}"
            )

    async def get_relationship_mappings(
        self,
        verified_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get relationship mappings"""
        try:
            query = self.supabase.from_("relationship_mappings").select("*")
            
            if verified_only:
                query = query.eq("is_verified", True)
            
            response = query.range(offset, offset + limit - 1).execute()
            
            return response.data or []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving relationship mappings: {str(e)}"
            )

    async def create_relationship_mapping(
        self,
        mapping: RelationshipMapping,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create or update a relationship mapping"""
        try:
            # Check if mapping already exists
            response = self.supabase.from_("relationship_mappings").select("*").eq("relationship_type", mapping.relationship_type).execute()
            
            if response.data and len(response.data) > 0:
                # Update existing mapping
                mapping_data = mapping.dict()
                if user_id:
                    mapping_data["created_by"] = user_id
                
                update_response = self.supabase.from_("relationship_mappings").update(mapping_data).eq("relationship_type", mapping.relationship_type).execute()
                
                return update_response.data[0]
            else:
                # Create new mapping
                mapping_data = mapping.dict()
                if user_id:
                    mapping_data["created_by"] = user_id
                
                insert_response = self.supabase.from_("relationship_mappings").insert(mapping_data).execute()
                
                return insert_response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating relationship mapping: {str(e)}"
            )

    async def delete_relationship_mapping(self, relationship_type: str) -> Dict[str, Any]:
        """Delete a relationship mapping"""
        try:
            self.supabase.from_("relationship_mappings").delete().eq("relationship_type", relationship_type).execute()
            
            return {"success": True, "message": "Relationship mapping deleted"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting relationship mapping: {str(e)}"
            )

    async def get_entity_fibo_class(self, entity_type: str) -> Optional[Dict[str, Any]]:
        """Get FIBO class for an entity type using mappings"""
        try:
            # First check mapping table
            response = self.supabase.from_("entity_mappings").select("*").eq("entity_type", entity_type).execute()
            
            if response.data and len(response.data) > 0:
                mapping = response.data[0]
                fibo_class_uri = mapping.get("fibo_class_uri")
                
                if fibo_class_uri:
                    try:
                        return await self.get_fibo_class_by_uri(fibo_class_uri)
                    except HTTPException:
                        pass
            
            # If no mapping found or class not found, try to find by similarity
            classes = await self.get_fibo_classes(search=entity_type, limit=1)
            
            if classes:
                return classes[0]
            
            return None
        except Exception as e:
            print(f"Error getting entity FIBO class: {e}")
            return None

    async def get_relationship_fibo_property(self, relationship_type: str) -> Optional[Dict[str, Any]]:
        """Get FIBO property for a relationship type using mappings"""
        try:
            # First check mapping table
            response = self.supabase.from_("relationship_mappings").select("*").eq("relationship_type", relationship_type).execute()
            
            if response.data and len(response.data) > 0:
                mapping = response.data[0]
                fibo_property_uri = mapping.get("fibo_property_uri")
                
                if fibo_property_uri:
                    try:
                        return await self.get_fibo_property_by_uri(fibo_property_uri)
                    except HTTPException:
                        pass
            
            # If no mapping found or property not found, try to find by similarity
            properties = await self.get_fibo_properties(search=relationship_type, limit=1)
            
            if properties:
                return properties[0]
            
            return None
        except Exception as e:
            print(f"Error getting relationship FIBO property: {e}")
            return None

    async def suggest_fibo_class_for_entity(
        self, 
        entity_text: str, 
        entity_type: str,
        properties: Optional[Dict[str, Any]] = None,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """Suggest FIBO classes for an entity based on text similarity"""
        try:
            # First try to get from mapping
            mapped_class = await self.get_entity_fibo_class(entity_type)
            
            if mapped_class:
                return [mapped_class]
            
            # Search for similar classes
            suggestions = []
            
            # Try to find by entity type
            type_results = await self.get_fibo_classes(search=entity_type, limit=max_suggestions)
            suggestions.extend(type_results)
            
            # Try to find by text
            if entity_text and len(suggestions) < max_suggestions:
                remaining = max_suggestions - len(suggestions)
                
                # Extract keywords from entity text
                keywords = entity_text.split()
                for keyword in keywords:
                    if len(keyword) > 3:  # Only use longer keywords
                        text_results = await self.get_fibo_classes(search=keyword, limit=remaining)
                        
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
                banking_classes = await self.get_fibo_classes(domain="FBC", limit=max_suggestions)
                suggestions.extend(banking_classes)
            
            return suggestions
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error suggesting FIBO classes: {str(e)}"
            )

    async def suggest_fibo_property_for_relationship(
        self,
        relationship_type: str,
        source_entity_type: str,
        target_entity_type: str,
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """Suggest FIBO properties for a relationship based on entity types and relationship type"""
        try:
            # First try to get from mapping
            mapped_property = await self.get_relationship_fibo_property(relationship_type)
            
            if mapped_property:
                return [mapped_property]
            
            suggestions = []
            
            # Get FIBO classes for source and target entity types
            source_class = await self.get_entity_fibo_class(source_entity_type)
            target_class = await self.get_entity_fibo_class(target_entity_type)
            
            # If we have both classes, look for properties that connect them
            if source_class and target_class:
                query = f"""
                SELECT p.*
                FROM fibo_properties p
                WHERE 
                    (p.domain_class_id = '{source_class["id"]}' AND p.range_class_id = '{target_class["id"]}')
                    OR p.label ILIKE '%{relationship_type}%'
                    OR p.uri ILIKE '%{relationship_type}%'
                LIMIT {max_suggestions}
                """
                
                response = self.supabase.rpc("exec_sql", {"sql_query": query}).execute()
                
                if response.data:
                    suggestions.extend(response.data)
            
            # If we don't have enough suggestions, search by relationship type
            if len(suggestions) < max_suggestions:
                remaining = max_suggestions - len(suggestions)
                type_results = await self.get_fibo_properties(search=relationship_type, limit=remaining)
                
                # Add only new suggestions
                for result in type_results:
                    if result["id"] not in [s["id"] for s in suggestions]:
                        suggestions.append(result)
            
            # If still no suggestions, get object properties
            if not suggestions:
                default_properties = await self.get_fibo_properties(property_type="object", limit=max_suggestions)
                suggestions.extend(default_properties)
            
            return suggestions
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error suggesting FIBO properties: {str(e)}"
            )

    async def verify_entity_mapping(
        self, 
        entity_type: str, 
        verified: bool, 
        user_id: str
    ) -> Dict[str, Any]:
        """Verify an entity mapping"""
        try:
            # Check if mapping exists
            response = self.supabase.from_("entity_mappings").select("*").eq("entity_type", entity_type).execute()
            
            if not response.data or len(response.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Entity mapping not found"
                )
            
            # Update verification status
            update_data = {
                "is_verified": verified,
                "verified_by": user_id if verified else None,
                "verified_at": datetime.utcnow().isoformat() if verified else None
            }
            
            update_response = self.supabase.from_("entity_mappings").update(update_data).eq("entity_type", entity_type).execute()
            
            return update_response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying entity mapping: {str(e)}"
            )

    async def verify_relationship_mapping(
        self, 
        relationship_type: str, 
        verified: bool, 
        user_id: str
    ) -> Dict[str, Any]:
        """Verify a relationship mapping"""
        try:
            # Check if mapping exists
            response = self.supabase.from_("relationship_mappings").select("*").eq("relationship_type", relationship_type).execute()
            
            if not response.data or len(response.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Relationship mapping not found"
                )
            
            # Update verification status
            update_data = {
                "is_verified": verified,
                "verified_by": user_id if verified else None,
                "verified_at": datetime.utcnow().isoformat() if verified else None
            }
            
            update_response = self.supabase.from_("relationship_mappings").update(update_data).eq("relationship_type", relationship_type).execute()
            
            return update_response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying relationship mapping: {str(e)}"
            )
