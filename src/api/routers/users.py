from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from src.api.dependencies import get_default_user
from src.api.schemas import UserResponse, UserUpdate
from src.database.connection import mongodb
from src.database.models import User, PyObjectId

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_default_user)):
    """Get current user's profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_default_user),
):
    """Update current user's profile."""
    user_collection = mongodb.database["users"]
    update_data = user_update.model_dump(exclude_unset=True)
    
    await user_collection.update_one(
        {"_id": current_user.id},
        {"$set": update_data}
    )
    
    updated_user_doc = await user_collection.find_one({"_id": current_user.id})
    if not updated_user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = User(**updated_user_doc)
    
    return UserResponse(
        id=str(updated_user.id),
        email=updated_user.email,
        username=updated_user.username,
        full_name=updated_user.full_name,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at
    )


