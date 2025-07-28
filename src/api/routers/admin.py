"""Admin-only routes for development purposes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta
import os

from src.database.connection import get_db
from src.database.models import User
from src.core.config import settings
from src.api.auth import create_token_pair, get_password_hash, authenticate_user
from src.api.auth import get_current_active_user, require_admin
from src.api.schemas import UserResponse, UserCreate, Token, LoginRequest

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
    token_data = create_token_pair({"sub": "admin"})
    
    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "token_type": token_data["token_type"],
        "expires_in": token_data["expires_in"],
        "user": admin_user
    }


@router.post("/demo-login", response_model=Token)
async def demo_login(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Demo user login endpoint for testing purposes.
    Creates a demo user if it doesn't exist and logs them in.
    """
    # Check if demo user exists
    demo_user = db.query(User).filter(User.username == "demo").first()
    
    if not demo_user:
        # Create demo user
        demo_user = User(
            email="demo@example.com",
            username="demo",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo User",
            is_active=True,
            is_verified=True,
            subscription_tier="basic",
            subscription_status="active",
            role="user"
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
    
    # Create tokens for demo user
    token_data = create_token_pair({"sub": "demo"})
    
    return {
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "token_type": token_data["token_type"],
        "expires_in": token_data["expires_in"]
    }


@router.post("/create-user", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Admin endpoint to create new users.
    Only admins can access this endpoint.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=True,
        subscription_tier="free",
        subscription_status="active",
        role="user"
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/users/", response_model=list[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get all users (admin only)."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users
