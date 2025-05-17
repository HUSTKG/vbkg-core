from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EntityCreate(BaseModel):
    text: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    properties: Dict[str, Any] = Field(default_factory=dict)
    fibo_class: Optional[str] = None
    source_document_id: Optional[str] = None


class RelationshipCreate(BaseModel):
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    fibo_property: Optional[str] = None
    source_document_id: Optional[str] = None


class EntityUpdate(BaseModel):
    properties: Dict[str, Any] = Field(default_factory=dict)
    fibo_class: Optional[str] = None


class CypherQuery(BaseModel):
    query: str
    parameters: Optional[Dict[str, Any]] = None
