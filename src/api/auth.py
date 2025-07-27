"""Authentication utilities for JWT token management."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_
from dotenv import load_dotenv

from src.core.config import settings
from src.database.connection import get_db
from src.database.models import User, Subscription
from src.schemas.auth import TokenData
from src.schemas.user import User as UserSchema

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TOKEN_TYPE_ACCESS
    })
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TOKEN_TYPE_REFRESH
    })
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def verify_token(token: str, expected_type: str = TOKEN_TYPE_ACCESS) -> str:
    """Verify JWT token and return username."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def refresh_access_token(refresh_token: str, db: Session) -> Dict[str, Any]:
    """Generate new access token from refresh token."""
    username = verify_token(refresh_token, TOKEN_TYPE_REFRESH)
    
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": username})
    
    return {
        "access_token": access_token,
        "refresh_token": create_refresh_token(data={"sub": username}),
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the current user is an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation forbidden: Not an administrator"
        )
    return current_user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user with subscription check"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def check_subscription_limits(user: User, db: Session, action: str = "task_execution") -> bool:
    """Check if user has not exceeded subscription limits"""
    # Get user's current subscription
    subscription = db.query(Subscription).filter(
        and_(
            Subscription.user_id == user.id,
            Subscription.is_active == True,
            Subscription.end_date > datetime.utcnow()
        )
    ).first()
    
    if not subscription:
        # Free tier limits
        if action == "task_execution":
            # Count tasks this month
            current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            from src.database.models import Task
            monthly_tasks = db.query(Task).filter(
                and_(
                    Task.user_id == user.id,
                    Task.created_at >= current_month_start
                )
            ).count()
            
            if monthly_tasks >= settings.free_tier_monthly_tasks:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Monthly task limit exceeded. Please upgrade your subscription."
                )
    
    return True

def require_subscription(tier: str = "basic"):
    """Decorator to require specific subscription tier"""
    def subscription_dependency(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        subscription = db.query(Subscription).filter(
            and_(
                Subscription.user_id == current_user.id,
                Subscription.is_active == True,
                Subscription.end_date > datetime.utcnow()
            )
        ).first()
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"This feature requires a {tier} subscription or higher."
            )
        
        # Check subscription tier hierarchy
        tier_hierarchy = {"basic": 1, "pro": 2, "enterprise": 3}
        required_level = tier_hierarchy.get(tier, 1)
        user_level = tier_hierarchy.get(subscription.tier, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"This feature requires a {tier} subscription or higher. Current: {subscription.tier}"
            )
        
        return current_user
    
    return subscription_dependency


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
