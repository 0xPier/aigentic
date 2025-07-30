from fastapi import Depends, HTTPException, status
from src.database.connection import mongodb
from src.database.models import User

# This is a placeholder for a default user. In a real application, this would
# be replaced with a proper authentication system.
DEFAULT_USER_EMAIL = "defaultuser@example.com"

async def get_default_user() -> User:
    """Returns a default user. Creates one if it doesn't exist."""
    user_collection = mongodb.database["users"]
    user_doc = await user_collection.find_one({"email": DEFAULT_USER_EMAIL})

    if not user_doc:
        user = User(
            email=DEFAULT_USER_EMAIL,
            username="defaultuser",
            full_name="Default User",
            is_active=True,
            is_verified=True
        )
        result = await user_collection.insert_one(user.model_dump(by_alias=True, exclude_none=True))
        user.id = result.inserted_id
    else:
        user = User(**user_doc)
    return user
