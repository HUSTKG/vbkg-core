from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class ResourceType(Enum):
    """Enum for resource types."""

    USER = "user"
    DATASOURCE = "datasource"
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    PIPLEINE = "pipeline"
    VISUALIZATION = "visualization"
    ROLE = "role"
    PERMISSION = "permission"


class UserAction(Enum):
    """Enum for user actions."""

    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ENTITY_CREATE = "entity_create"
    ENTITY_UPDATE = "entity_update"
    DATASOURCE_CREATE = "datasource_create"
    DATASOURCE_UPDATE = "datasource_update"
    DATASOURCE_DELETE = "datasource_delete"
    RELATIONSHIP_CREATE = "relationship_create"
    SEARCH_QUERY = "search_query"
    VISUALIZATION_CREATE = "visualization_create"
    API_CALL = "api_call"
    FILE_UPLOAD = "file_upload"
    CHAT_MESSAGE = "chat_message"


class UserBase(BaseModel):
    """Base model for user data."""

    email: Optional[EmailStr]
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    roles: List[str] = Field(default=["viewer"])


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    """Complete user model returned from API."""

    id: str
    is_active: bool = True
    roles: List[str] = []
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
