from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
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
    roles: Optional[List[str]] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: str
    is_active: bool = True
    roles: List[str] = []
    avatar_url: Optional[str] = None

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
