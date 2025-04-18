# app/schemas/fibo.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class FIBOClassBase(BaseModel):
    uri: str = Field(..., description="URI of the FIBO class")
    label: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class FIBOClassCreate(FIBOClassBase):
    parent_class_uri: Optional[str] = None
    is_custom: bool = False


class FIBOClassUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    parent_class_uri: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class FIBOClass(FIBOClassBase):
    id: int
    parent_class_id: Optional[int] = None
    is_custom: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class FIBOPropertyBase(BaseModel):
    uri: str = Field(..., description="URI of the FIBO property")
    label: Optional[str] = None
    description: Optional[str] = None
    property_type: str = Field(..., description="Type of property: 'object' or 'datatype'")


class FIBOPropertyCreate(FIBOPropertyBase):
    domain_class_uri: Optional[str] = None
    range_class_uri: Optional[str] = None
    is_custom: bool = False


class FIBOPropertyUpdate(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    domain_class_uri: Optional[str] = None
    range_class_uri: Optional[str] = None
    property_type: Optional[str] = None


class FIBOProperty(FIBOPropertyBase):
    id: int
    domain_class_id: Optional[int] = None
    range_class_id: Optional[int] = None
    is_custom: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class EntityMapping(BaseModel):
    entity_type: str
    fibo_class_uri: str
    confidence: Optional[float] = None
    is_verified: bool = False


class RelationshipMapping(BaseModel):
    relationship_type: str
    fibo_property_uri: str
    confidence: Optional[float] = None
    is_verified: bool = False


class OntologyImportRequest(BaseModel):
    file_id: Optional[str] = None
    url: Optional[str] = None
    format: str = "rdf"  # rdf, owl, ttl
    
    @validator('format')
    def validate_format(cls, v):
        valid_formats = ['rdf', 'owl', 'ttl']
        if v not in valid_formats:
            raise ValueError(f"Format must be one of {valid_formats}")
        return v
    
    @validator('file_id', 'url')
    def validate_source(cls, v, values):
        # Ensure either file_id or url is provided
        if 'file_id' not in values and 'url' not in values:
            raise ValueError("Either file_id or url must be provided")
        return v


class OntologyImportResponse(BaseModel):
    success: bool
    message: str
    classes_imported: Optional[int] = None
    properties_imported: Optional[int] = None
    errors: Optional[List[str]] = None
