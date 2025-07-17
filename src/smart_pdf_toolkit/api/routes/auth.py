"""
Authentication endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import logging

from ..auth import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_current_admin_user,
    fake_users_db
)
from ..config import get_api_config

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    config = get_api_config()
    access_token_expires = timedelta(minutes=config.access_token_expire_minutes)
    
    # Include requested scopes that the user has access to
    token_scopes = [scope for scope in form_data.scopes if scope in user.scopes]
    
    access_token = create_access_token(
        data={"sub": user.username, "scopes": token_scopes},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User {user.username} logged in with scopes: {token_scopes}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information.
    """
    return current_user


@router.get("/users/me/scopes")
async def read_own_scopes(current_user: User = Depends(get_current_active_user)):
    """
    Get current user scopes.
    """
    return {
        "username": current_user.username,
        "scopes": current_user.scopes
    }


@router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_admin_user)):
    """
    Get all users (admin only).
    """
    return [
        {
            "username": username,
            "full_name": data["full_name"],
            "email": data["email"],
            "disabled": data["disabled"],
            "scopes": data["scopes"]
        }
        for username, data in fake_users_db.items()
    ]