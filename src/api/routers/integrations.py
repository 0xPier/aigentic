from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_default_user
from src.api.schemas import IntegrationCreate, IntegrationResponse, IntegrationUpdate
from src.database.connection import mongodb
from src.database.models import User, Integration, PyObjectId

router = APIRouter()


@router.get("/", response_model=List[IntegrationResponse])
async def get_integrations(
    current_user: User = Depends(get_default_user),
):
    """Get all integrations for current user."""
    integration_collection = mongodb.database["integrations"]
    integrations_cursor = integration_collection.find({"user_id": current_user.id})
    integrations = [Integration(**doc) async for doc in integrations_cursor]
    return integrations


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: PyObjectId,
    current_user: User = Depends(get_default_user),
):
    """Get a specific integration."""
    integration_collection = mongodb.database["integrations"]
    integration_doc = integration_collection.find_one({"_id": integration_id, "user_id": current_user.id})
    
    if not integration_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    return Integration(**integration_doc)


@router.post("/", response_model=IntegrationResponse)
async def create_integration(
    integration_data: IntegrationCreate,
    current_user: User = Depends(get_default_user),
):
    """Create a new integration."""
    integration_collection = mongodb.database["integrations"]
    
    # Check if integration type already exists for user
    existing = integration_collection.find_one({
        "user_id": current_user.id,
        "integration_type": integration_data.name
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integration {integration_data.name} already exists"
        )
    
    # Create new integration
    integration_dict = integration_data.model_dump(exclude_unset=True)
    integration_dict["user_id"] = current_user.id
    integration_dict["integration_type"] = integration_data.name
    integration_dict["configuration"] = {"api_key": integration_data.api_key, **integration_data.config}
    integration_dict["is_active"] = True

    new_integration = Integration(**integration_dict)
    result = await integration_collection.insert_one(new_integration.model_dump(by_alias=True, exclude_none=True))
    new_integration.id = result.inserted_id
    
    return new_integration


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: PyObjectId,
    integration_data: IntegrationUpdate,
    current_user: User = Depends(get_default_user),
):
    """Update an existing integration."""
    integration_collection = mongodb.database["integrations"]
    
    existing_integration = integration_collection.find_one({"_id": integration_id, "user_id": current_user.id})
    
    if not existing_integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    update_data = integration_data.model_dump(exclude_unset=True)
    
    if "api_key" in update_data:
        existing_config = existing_integration.get("configuration", {})
        existing_config["api_key"] = update_data.pop("api_key")
        update_data["configuration"] = existing_config
    
    await integration_collection.update_one(
        {"_id": integration_id},
        {"$set": update_data}
    )
    
    updated_integration_doc = integration_collection.find_one({"_id": integration_id})
    return Integration(**updated_integration_doc)


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: PyObjectId,
    current_user: User = Depends(get_default_user),
):
    """Delete an integration."""
    integration_collection = mongodb.database["integrations"]
    
    result = await integration_collection.delete_one({"_id": integration_id, "user_id": current_user.id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    return {"message": "Integration deleted successfully"}