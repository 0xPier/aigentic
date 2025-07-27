"""Admin-only routes for development purposes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta
import os

from src.database.connection import get_db
from src.database.models import User
from src.core.config import settings
from src.api.auth import create_token_pair
from src.services.auth_service import get_current_active_user

router = APIRouter()

@router.post("/dev-login")
async def dev_login() -> Dict[str, Any]:
    """
    Development-only endpoint to get admin access without real authentication.
    WARNING: This should be removed in production!
    """
    if os.getenv('ENVIRONMENT') != 'development':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode"
        )
    
    # Create a mock admin user
    admin_user = {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "is_active": True,
        "is_verified": True,
        "subscription_tier": "enterprise"
    }
    
    # Create tokens with admin user data
    token_data = create_token_pair({"username": "admin"})
    
    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "token_type": token_data["token_type"],
        "expires_in": token_data["expires_in"],
        "user": admin_user
    }


@router.get("/users/", response_model=list[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    users = db.query(User).offset(skip).limit(limit).all()
    return users
