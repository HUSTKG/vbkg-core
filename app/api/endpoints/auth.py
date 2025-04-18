from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.services.auth import get_user_by_email, create_user
from app.schemas.auth import Token, UserCreate, UserLogin
from app.api.deps import get_current_user, get_supabase

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_access_token(form_data: UserLogin) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await get_user_by_email(email=form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=Token)
async def register_user(user_in: UserCreate) -> Any:
    """
    Register new user
    """
    user = await get_user_by_email(email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists",
        )
    
    user = await create_user(user_in)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/logout")
async def logout(supabase=Depends(get_supabase)):
    """
    Logout user by invalidating access token
    """
    # For Supabase auth, we don't need to explicitly invalidate token
    # Client should discard the token
    return {"message": "Successfully logged out"}
