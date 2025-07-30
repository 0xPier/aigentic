import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from src.database.connection import mongodb
from src.database.models import User
from src.core.config import app_config

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, 
            app_config.secret_key, 
            algorithms=[app_config.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user_collection = mongodb.database["users"]
    user_doc = await user_collection.find_one({"_id": user_id})
    
    if user_doc is None:
        raise credentials_exception
    
    user = User(**user_doc)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Temporary fallback for development - creates a default user if none exists
async def get_default_user() -> User:
    """TEMPORARY: Returns a default user for development. Should be replaced with proper auth."""
    logger.warning("Using default user - this should only be used in development!")
    
    user_collection = mongodb.database["users"]
    default_email = "dev@example.com"
    user_doc = await user_collection.find_one({"email": default_email})

    if not user_doc:
        # Create default development user
        user = User(
            email=default_email,
            username="devuser",
            full_name="Development User",
            is_active=True,
            is_verified=True,
            subscription_tier="free"
        )
        result = await user_collection.insert_one(user.model_dump(by_alias=True, exclude_none=True))
        user.id = result.inserted_id
        logger.info("Created default development user")
    else:
        user = User(**user_doc)
    
    return user
