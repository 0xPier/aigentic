"""Projects router for project management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import Project, User
from src.schemas.project import ProjectCreate, ProjectRead
from src.services.auth_service import get_current_active_user

router = APIRouter()

async def get_project_for_user(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Project:
    """Dependency to get a project and verify ownership."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


@router.post("/", response_model=ProjectRead)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new project."""
    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project


@router.get("/", response_model=List[ProjectRead])
async def get_user_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's projects."""
    projects = db.query(Project).filter(
        Project.owner_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return projects


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project: Project = Depends(get_project_for_user)):
    """Get a specific project."""
    return project


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_update: ProjectCreate,
    project: Project = Depends(get_project_for_user),
    db: Session = Depends(get_db)
):
    """Update a project."""
    for field, value in project_update.dict(exclude_unset=True).items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project: Project = Depends(get_project_for_user),
    db: Session = Depends(get_db)
):
    """Delete a project."""
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}
