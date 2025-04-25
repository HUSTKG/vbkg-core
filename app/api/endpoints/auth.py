# app/api/endpoints/auth.py
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core.config import settings
from app.schemas.user import UserCreate, UserLogin, Token, User
from app.schemas.api import ApiResponse

from app.services.auth import AuthService

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """
    Login endpoint using OAuth2 password flow.
    """
    auth_service = AuthService()
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    result = await auth_service.login(login_data)
    
    return Token(
        access_token=result["access_token"],
        token_type=result["token_type"],
    )

@router.post("/login/json", response_model=ApiResponse[Dict[str, Any]])
async def login_json(login_data: UserLogin) -> ApiResponse[Dict[str, Any]]:
    """
    Login endpoint using JSON payload instead of form data.
    """
    auth_service = AuthService()
    result = await auth_service.login(login_data)
    return ApiResponse(
        data=result,
        status=status.HTTP_200_OK,
        message="Login successful"
    )


@router.post("/register", response_model=ApiResponse[User])
async def register(user_data: UserCreate) -> ApiResponse[User]:
    """
    Register a new user.
    """
    auth_service = AuthService()
    user = await auth_service.register(user_data)
    return ApiResponse(
        data=user,
        status=status.HTTP_201_CREATED,
        message="User registered successfully"
    )


@router.post("/logout", response_model=ApiResponse[None])
async def logout(token: str = Depends(oauth2_scheme)) -> ApiResponse[None]:
    """
    Logout a user.
    """
    auth_service = AuthService()
    await auth_service.logout(token)
    return ApiResponse(
        data=None,
        status=status.HTTP_200_OK,
        message="Logged out successfully"
    )

