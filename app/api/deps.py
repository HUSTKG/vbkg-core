from typing import Annotated, Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.api_key import APIKeyHeader

from app.services.auth import AuthService
from app.services.user import UserService

# Security schemes
security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    api_key: Optional[str] = Depends(api_key_header)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token or API key.
    Supports both authentication methods.
    """
    
    user_service = UserService()
    
    # Try API key authentication first
    if api_key:
        user = await user_service.verify_api_key(api_key)
        if user:
            # Log API usage
            await _log_api_usage(request, user, api_key_id=user.get("api_key_info", {}).get("id"))
            return user
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Try JWT token authentication
    if credentials:
        auth_service = AuthService()
        try:
            user = await auth_service.get_current_user(credentials.credentials)
            
            # Enhance user data with permissions
            enhanced_user = await user_service.get_user_by_id(user["id"])
            
            # Log API usage
            await _log_api_usage(request, enhanced_user)
            
            return enhanced_user
            
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get current active user.
    """
    if not current_user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    api_key: Optional[str] = Depends(api_key_header)
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, otherwise return None.
    Used for endpoints that work both with and without authentication.
    """
    try:
        return await get_current_user(request, credentials, api_key)
    except HTTPException:
        return None


class PermissionChecker:
    """
    Enhanced dependency to check if the user has a specific permission.
    """

    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(
        self, 
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """Check if user has required permission"""
        
        user_permissions = current_user.get("permissions", [])
        
        if self.permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {self.permission}",
            )

        return current_user


class RoleChecker:
    """
    Dependency to check if user has a specific role.
    """

    def __init__(self, required_role: str):
        self.required_role = required_role

    async def __call__(
        self, 
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """Check if user has required role"""
        
        user_roles = current_user.get("roles", [])
        
        # Admin has access to everything
        if "admin" in user_roles:
            return current_user
        
        # Expert has access to expert and user features
        if self.required_role == "expert" and "expert" in user_roles:
            return current_user
        
        # User level access
        if self.required_role == "user" and any(role in user_roles for role in ["user", "expert", "admin"]):
            return current_user
        
        # Check for exact role match
        if self.required_role in user_roles:
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient role. Required: {self.required_role}",
        )


class MultiplePermissionChecker:
    """
    Dependency to check if user has multiple permissions (ALL required).
    """
    
    def __init__(self, permissions: list[str], require_all: bool = True):
        self.permissions = permissions
        self.require_all = require_all
    
    async def __call__(
        self, 
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """Check if user has required permissions"""
        
        user_permissions = current_user.get("permissions", [])
        
        if self.require_all:
            # User must have ALL permissions
            missing_permissions = [p for p in self.permissions if p not in user_permissions]
            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(missing_permissions)}",
                )
        else:
            # User must have at least ONE permission
            if not any(p in user_permissions for p in self.permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Must have at least one of: {', '.join(self.permissions)}",
                )
        
        return current_user


# Legacy compatibility - keeping existing admin check
async def get_current_active_admin(
    current_user: Annotated[Dict[str, Any], Depends(get_current_active_user)],
) -> Dict[str, Any]:
    """
    Get current active admin (legacy compatibility).
    """
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


# Pre-defined permission checkers for common use cases
RequireAdmin = RoleChecker("admin")
RequireExpert = RoleChecker("expert") 
RequireUser = RoleChecker("user")

# Data source permissions
RequireDataSourceRead = PermissionChecker("datasource:read")
RequireDataSourceWrite = PermissionChecker("datasource:write")
RequireDataSourceDelete = PermissionChecker("datasource:delete")

# Pipeline permissions
RequirePipelineRead = PermissionChecker("pipeline:read")
RequirePipelineWrite = PermissionChecker("pipeline:write")
RequirePipelineExecute = PermissionChecker("pipeline:execute")
RequirePipelineDelete = PermissionChecker("pipeline:delete")

# Knowledge graph permissions
RequireKGRead = PermissionChecker("kg:read")
RequireKGSearch = PermissionChecker("kg:search")
RequireKGEdit = PermissionChecker("kg:edit")
RequireKGDelete = PermissionChecker("kg:delete")

# Quality management permissions
RequireQualityRead = PermissionChecker("quality:read")
RequireQualityExpert = PermissionChecker("quality:expert")
RequireQualityAdmin = PermissionChecker("quality:admin")

# System permissions
RequireUserManagement = PermissionChecker("user:management")
RequireSystemConfig = PermissionChecker("system:config")
RequireSystemMonitoring = PermissionChecker("system:monitoring")

# API permissions
RequireAPIAccess = PermissionChecker("api:access")
RequireAPIUnlimited = PermissionChecker("api:unlimited")

# Combined permission checkers
RequireDataManagement = MultiplePermissionChecker([
    "datasource:write", "pipeline:write"
], require_all=False)

RequireKGManagement = MultiplePermissionChecker([
    "kg:edit", "quality:expert"
], require_all=False)


async def validate_rate_limits(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Validate API rate limits for the current user.
    """
    from app.utils.rate_limiter import check_rate_limit
    
    user_id = current_user["id"]
    user_permissions = current_user.get("permissions", [])
    
    # Determine rate limit based on permissions
    if "api:unlimited" in user_permissions:
        return current_user  # No rate limiting for unlimited users
    
    # Get rate limit from API key info if available
    api_key_info = current_user.get("api_key_info", {})
    rate_limit = api_key_info.get("rate_limit", 1000)  # Default 1000/hour
    
    # Check rate limit
    allowed = await check_rate_limit(
        user_id=user_id,
        limit=rate_limit,
        window=3600  # 1 hour
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": "3600",
                "X-RateLimit-Limit": str(rate_limit),
                "X-RateLimit-Remaining": "0"
            }
        )
    
    return current_user


async def _log_api_usage(
    request: Request,
    user: Dict[str, Any],
    api_key_id: Optional[str] = None
):
    """Log API usage for monitoring and analytics"""
    try:
        from app.core.supabase import get_supabase
        
        supabase = await get_supabase()
        
        # Extract request info
        method = request.method
        path = str(request.url.path)
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        await supabase.table("api_usage_log").insert({
            "user_id": user["id"],
            "api_key_id": api_key_id,
            "method": method,
            "path": path,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "status_code": None,  # Will be updated by middleware
            "response_time": None  # Will be updated by middleware
        }).execute()
        
    except Exception as e:
        # Don't let logging failures affect the request
        print(f"Failed to log API usage: {e}")


# Utility function to check specific permissions programmatically
async def check_user_permission(user_id: str, permission: str) -> bool:
    """
    Utility function to check if a user has a specific permission.
    Can be used in business logic outside of FastAPI dependencies.
    """
    user_service = UserService()
    return await user_service.check_permission(user_id, permission)


async def get_user_permissions(user_id: str) -> list[str]:
    """
    Utility function to get all permissions for a user.
    Can be used in business logic outside of FastAPI dependencies.
    """
    user_service = UserService()
    return await user_service._get_user_permissions(user_id)
