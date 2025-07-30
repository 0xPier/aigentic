from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_default_user
from src.api.schemas import UserSettingsResponse, UserSettingsUpdate, UserSettingsCreate
from src.database.connection import mongodb
from src.database.models import User, UserSettings, PyObjectId

router = APIRouter()


@router.get("/", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_default_user),
):
    """Get current user's settings."""
    settings_collection = mongodb.database["user_settings"]
    settings_doc = settings_collection.find_one({"user_id": current_user.id})
    
    if not settings_doc:
        # Create default settings if none exist
        settings = UserSettings(
            user_id=current_user.id,
            llm_provider="openai",
            llm_model="gpt-3.5-turbo",
            theme="light",
            language="en",
            timezone="UTC",
            email_notifications=True,
            task_completion_notifications=True,
            project_updates_notifications=True,
            auto_save_interval=30,
            max_concurrent_tasks=3
        )
        result = await settings_collection.insert_one(settings.model_dump(by_alias=True, exclude_none=True))
        settings.id = result.inserted_id
    else:
        settings = UserSettings(**settings_doc)
    
    return settings


@router.put("/", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_default_user),
):
    """Update current user's settings."""
    settings_collection = mongodb.database["user_settings"]
    
    existing_settings = settings_collection.find_one({"user_id": current_user.id})
    
    if not existing_settings:
        # Create new settings if none exist
        settings = UserSettings(user_id=current_user.id, **settings_data.model_dump(exclude_unset=True))
        result = await settings_collection.insert_one(settings.model_dump(by_alias=True, exclude_none=True))
        settings.id = result.inserted_id
        return settings
    
    # Update only provided fields
    update_data = settings_data.model_dump(exclude_unset=True)
    
    await settings_collection.update_one(
        {"user_id": current_user.id},
        {"$set": update_data}
    )
    
    updated_settings_doc = settings_collection.find_one({"user_id": current_user.id})
    return UserSettings(**updated_settings_doc)


@router.post("/", response_model=UserSettingsResponse)
async def create_user_settings(
    settings_data: UserSettingsCreate,
    current_user: User = Depends(get_default_user),
):
    """Create user settings (if they don't exist)."""
    settings_collection = mongodb.database["user_settings"]
    existing_settings = settings_collection.find_one({"user_id": current_user.id})
    
    if existing_settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User settings already exist. Use PUT to update."
        )
    
    settings_dict = settings_data.model_dump(exclude_unset=True)
    settings_dict["user_id"] = current_user.id
    
    settings = UserSettings(**settings_dict)
    result = await settings_collection.insert_one(settings.model_dump(by_alias=True, exclude_none=True))
    settings.id = result.inserted_id
    
    return settings


@router.delete("/")
async def delete_user_settings(
    current_user: User = Depends(get_default_user),
):
    """Delete user settings (will be recreated with defaults on next get)."""
    settings_collection = mongodb.database["user_settings"]
    result = await settings_collection.delete_one({"user_id": current_user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User settings not found"
        )
    
    return {"message": "User settings deleted successfully"}


@router.get("/llm-config")
async def get_llm_config(
    current_user: User = Depends(get_default_user),
):
    """Get LLM configuration for the current user."""
    settings_collection = mongodb.database["user_settings"]
    settings_doc = settings_collection.find_one({"user_id": current_user.id})
    
    if not settings_doc:
        # Return default configuration
        return {
            "provider": "openai",
            "api_key": None,
            "api_base": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo"
        }
    
    settings = UserSettings(**settings_doc)
    
    return {
        "provider": settings.llm_provider or "openai",
        "api_key": settings.llm_api_key,
        "api_base": settings.llm_api_base,
        "model": settings.llm_model or "gpt-3.5-turbo"
    }


@router.post("/test-llm-connection")
async def test_llm_connection(
    current_user: User = Depends(get_default_user),
):
    """Test the LLM connection with current settings."""
    settings_collection = mongodb.database["user_settings"]
    settings_doc = settings_collection.find_one({"user_id": current_user.id})
    
    if not settings_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM settings not found for user"
        )
    
    settings = UserSettings(**settings_doc)

    if not settings.llm_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LLM API key not configured"
        )
    
    try:
        # Test connection based on provider
        if settings.llm_provider == "openai":
            import openai
            client = openai.OpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_api_base or "https://api.openai.com/v1"
            )
            response = client.chat.completions.create(
                model=settings.llm_model or "gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return {"status": "success", "message": "Connection successful"}
        
        elif settings.llm_provider == "ollama":
            import requests
            base_url = settings.llm_api_base or "http://localhost:11434"
            response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": settings.llm_model or "llama2",
                    "prompt": "Hello",
                    "stream": False
                },
                timeout=10
            )
            if response.status_code == 200:
                return {"status": "success", "message": "Connection successful"}
            else:
                raise Exception(f"Ollama API returned status {response.status_code}")
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported LLM provider: {settings.llm_provider}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Connection failed: {str(e)}"
        )