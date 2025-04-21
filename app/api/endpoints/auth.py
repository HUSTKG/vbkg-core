# app/api/endpoints/auth.py
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core.config import settings
from app.schemas.user import UserCreate, UserLogin, Token, User
from app.services.auth import AuthService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """
    Login endpoint using OAuth2 password flow.
    """
    auth_service = AuthService()
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    result = await auth_service.login(login_data)
    
    return {
        "access_token": result["access_token"],
        "token_type": result["token_type"]
    }


@router.post("/login/json", response_model=Dict[str, Any])
async def login_json(login_data: UserLogin) -> Any:
    """
    Login endpoint using JSON payload instead of form data.
    """
    auth_service = AuthService()
    return await auth_service.login(login_data)


@router.post("/register", response_model=User)
async def register(user_data: UserCreate) -> Any:
    """
    Register a new user.
    """
    auth_service = AuthService()
    return await auth_service.register(user_data)


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)) -> Any:
    """
    Logout a user.
    """
    auth_service = AuthService()
    return await auth_service.logout(token)


@router.get("/me", response_model=User)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Any:
    """
    Get current user information.
    """
    auth_service = AuthService()
    return await auth_service.get_current_user(token)
