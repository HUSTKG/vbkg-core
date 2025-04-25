from datetime import datetime
from typing import Any, List, Optional, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class ApiKey(BaseModel):
    id: str
    name: str
    key: str
    created_at: datetime 
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    permissions: List[str]
    class Config:
        from_attributes = True

class PaginatedMeta(BaseModel):
    total: int
    skip: int
    limit: int

class ApiResponse(BaseModel, Generic[T]):
    data: T  
    status: int
    message: str
    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    meta: PaginatedMeta 
    status: int
    message: str
    class Config:
        from_attributes = True

