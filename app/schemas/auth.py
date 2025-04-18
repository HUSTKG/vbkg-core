from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID
from datetime import datetime

# Token models
class Token(BaseModel):
    """Model for authentication token."""
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    """Model for token payload."""
    sub: Optional[str] = None
    exp: Optional[int] = None

# User models
class UserBase(BaseModel):
    """Base model for user data."""
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    """Model for creating a new user."""
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserUpdate(BaseModel):
    """Model for updating an existing user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength if provided."""
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one digit')
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least one uppercase letter')
        return v

class UserLogin(BaseModel):
    """Model for user login."""
    email: EmailStr
    password: str

class User(UserBase):
    """Complete user model returned from API."""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class UserWithRoles(User):
    """User model with roles included."""
    roles: List['Role'] = []

# Role models
class RoleBase(BaseModel):
    """Base model for role data."""
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    """Model for creating a new role."""
    pass

class RoleUpdate(BaseModel):
    """Model for updating an existing role."""
    name: Optional[str] = None
    description: Optional[str] = None

class Role(RoleBase):
    """Complete role model returned from API."""
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class RoleWithPermissions(Role):
    """Role model with permissions included."""
    permissions: List['Permission'] = []

# Permission models
class PermissionBase(BaseModel):
    """Base model for permission data."""
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    """Model for creating a new permission."""
    pass

class PermissionUpdate(BaseModel):
    """Model for updating an existing permission."""
    name: Optional[str] = None
    description: Optional[str] = None

class Permission(PermissionBase):
    """Complete permission model returned from API."""
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# Update forward references
UserWithRoles.update_forward_refs()
RoleWithPermissions.update_forward_refs()
