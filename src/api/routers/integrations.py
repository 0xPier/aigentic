"""Integrations router for third-party API management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.auth import get_current_active_user
from src.api.schemas import IntegrationCreate, IntegrationResponse, IntegrationUpdate
from src.database.connection import get_db
from src.database.models import User, Integration

router = APIRouter()


async def get_integration_for_user(
    integration_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Integration:
    """Dependency to get an integration and verify ownership."""
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
        Integration.integration_type == integration_data.integration_type
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Integration of this type already exists"
        )
    
    db_integration = Integration(
        user_id=current_user.id,
        integration_type=integration_data.integration_type,
        configuration=integration_data.configuration
    )
    
    db.add(db_integration)
    db.commit()
    db.refresh(db_integration)
    
    return db_integration


@router.get("/", response_model=List[IntegrationResponse])
async def get_user_integrations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's integrations."""
    integrations = db.query(Integration).filter(
        Integration.user_id == current_user.id
    ).all()
    
    return integrations


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(integration: Integration = Depends(get_integration_for_user)):
    """Get a specific integration."""
    return integration


@router.put("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_update: IntegrationUpdate,
    integration: Integration = Depends(get_integration_for_user),
    db: Session = Depends(get_db)
):
    """Update an integration."""
    for field, value in integration_update.dict(exclude_unset=True).items():
        setattr(integration, field, value)
    
    db.commit()
    db.refresh(integration)
    return integration


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration: Integration = Depends(get_integration_for_user),
    db: Session = Depends(get_db)
):
    """Delete an integration."""
    db.delete(integration)
    db.commit()
    return {"message": "Integration deleted successfully"}
