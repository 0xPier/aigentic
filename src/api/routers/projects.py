from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from src.database.connection import mongodb
from src.database.models import Project, User, PyObjectId
from src.api.schemas import ProjectCreate, ProjectResponse
from src.api.dependencies import get_default_user

router = APIRouter()

async def get_project_for_user(
    project_id: PyObjectId,
    current_user: User = Depends(get_default_user),
) -> Project:
    """Dependency to get a project and verify ownership."""
    project_collection = mongodb.database["projects"]
    project_doc = project_collection.find_one({"_id": project_id, "owner_id": current_user.id})
    
    if not project_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return Project(**project_doc)


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_default_user),
):
    """Create a new project."""
    project_collection = mongodb.database["projects"]
    project_dict = project_data.model_dump(exclude_unset=True)
    project_dict["owner_id"] = current_user.id
    
    new_project = Project(**project_dict)
    result = await project_collection.insert_one(new_project.model_dump(by_alias=True, exclude_none=True))
    new_project.id = result.inserted_id
    
    return new_project


@router.get("/", response_model=List[ProjectResponse])
async def get_user_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_default_user),
):
    """Get user's projects."""
    project_collection = mongodb.database["projects"]
    projects_cursor = project_collection.find({"owner_id": current_user.id}).skip(skip).limit(limit)
    projects = [Project(**doc) async for doc in projects_cursor]
    
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project: Project = Depends(get_project_for_user)):
    """Get a specific project."""
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_update: ProjectCreate,
    project: Project = Depends(get_project_for_user),
):
    """Update a project."""
    project_collection = mongodb.database["projects"]
    update_data = project_update.model_dump(exclude_unset=True)
    
    await project_collection.update_one(
        {"_id": project.id},
        {"$set": update_data}
    )
    
    updated_project_doc = project_collection.find_one({"_id": project.id})
    return Project(**updated_project_doc)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project: Project = Depends(get_project_for_user),
):
    """Delete a project."""
    project_collection = mongodb.database["projects"]
    await project_collection.delete_one({"_id": project.id})
    return {"message": "Project deleted successfully"}