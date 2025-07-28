"""Integrations router for managing API keys and third-party configurations."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.auth import get_current_active_user
from src.api.schemas import IntegrationCreate, IntegrationResponse, IntegrationUpdate
from src.database.connection import get_db
from src.database.models import User, Integration

router = APIRouter()


@router.get("/", response_model=List[IntegrationResponse])
async def get_integrations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all integrations for current user."""
    integrations = db.query(Integration).filter(
        Integration.user_id == current_user.id
    ).all()
    return integrations


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific integration."""
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    return integration


@router.post("/", response_model=IntegrationResponse)
async def create_integration(
    integration_data: IntegrationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new integration."""
    # Check if integration type already exists for user
    existing = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.integration_type == integration_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integration {integration_data.name} already exists"
        )
    
    # Create new integration
    db_integration = Integration(
        user_id=current_user.id,
        integration_type=integration_data.name,
        configuration={"api_key": integration_data.api_key, **integration_data.config},
        is_active=True
    )
    
    db.add(db_integration)
    db.commit()
    db.refresh(db_integration)
    
    return db_integration


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: int,
    integration_data: IntegrationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing integration."""
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    # Update fields
    update_data = integration_data.dict(exclude_unset=True)
    if "api_key" in update_data:
        config = integration.configuration.copy()
        config["api_key"] = update_data.pop("api_key")
        integration.configuration = config
    
    for field, value in update_data.items():
        setattr(integration, field, value)
    
    db.commit()
    db.refresh(integration)
    
    return integration


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an integration."""
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found"
        )
    
    db.delete(integration)
    db.commit()
    
    return {"message": "Integration deleted successfully"}
