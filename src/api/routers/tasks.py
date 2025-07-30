from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from src.api.dependencies import get_default_user
from src.api.schemas import (
    TaskCreate, TaskResponse, TaskUpdate, AgentTaskRequest, AgentTaskResponse
)
from src.database.connection import mongodb
from src.database.models import User, Task, Project, PyObjectId
from src.agents.tasks import execute_orchestrator_task

router = APIRouter()

async def get_task_for_user(
    task_id: PyObjectId,
    current_user: User = Depends(get_default_user),
) -> Task:
    """Dependency to get a task and verify ownership."""
    task_collection = mongodb.database["tasks"]
    task_doc = await task_collection.find_one({"_id": task_id, "user_id": current_user.id})
    
    if not task_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return Task(**task_doc)


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_default_user),
):
    """Create a new task."""
    db = mongodb.database
    # Verify project ownership if project_id is provided
    if task_data.project_id:
        project_collection = db["projects"]
        project_doc = await project_collection.find_one({"_id": task_data.project_id, "owner_id": current_user.id})
        if not project_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    
    # Create task
    task_collection = db["tasks"]
    task_dict = task_data.model_dump(exclude_unset=True)
    task_dict["user_id"] = current_user.id
    
    new_task = Task(**task_dict)
    result = await task_collection.insert_one(new_task.model_dump(by_alias=True, exclude_none=True))
    new_task.id = result.inserted_id
    
    return new_task


@router.get("/", response_model=List[TaskResponse])
async def get_user_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    project_id: Optional[PyObjectId] = None,
    current_user: User = Depends(get_default_user),
):
    """Get user's tasks with optional filtering."""
    task_collection = mongodb.database["tasks"]
    query_filter = {"user_id": current_user.id}
    
    if status:
        query_filter["status"] = status
    if project_id:
        query_filter["project_id"] = project_id
    
    tasks_cursor = task_collection.find(query_filter).skip(skip).limit(limit)
    tasks = [Task(**doc) async for doc in tasks_cursor]
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task: Task = Depends(get_task_for_user)):
    """Get a specific task."""
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_update: TaskUpdate,
    task: Task = Depends(get_task_for_user),
):
    """Update a task."""
    task_collection = mongodb.database["tasks"]
    update_data = task_update.model_dump(exclude_unset=True)
    
    await task_collection.update_one(
        {"_id": task.id},
        {"$set": update_data}
    )
    
    updated_task_doc = await task_collection.find_one({"_id": task.id})
    return Task(**updated_task_doc)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task: Task = Depends(get_task_for_user),
):
    """Delete a task."""
    task_collection = mongodb.database["tasks"]
    await task_collection.delete_one({"_id": task.id})
    return {"message": "Task deleted successfully"}


@router.post("/execute", response_model=TaskResponse)
async def execute_agent_task(
    task_request: AgentTaskRequest,
    current_user: User = Depends(get_default_user),
):
    """Execute a task using the orchestrator agent with subscription checking."""
    try:
        db = mongodb.database
        # Check subscription limits before executing
        
        
        # Create task record
        task_collection = db["tasks"]
        task_dict = task_request.model_dump(exclude_unset=True)
        task_dict["title"] = f"Agent Task: {task_request.agent_name}"
        task_dict["description"] = task_request.query
        task_dict["user_id"] = current_user.id
        task_dict["status"] = "pending"

        new_task = Task(**task_dict)
        result = await task_collection.insert_one(new_task.model_dump(by_alias=True, exclude_none=True))
        new_task.id = result.inserted_id
        
        # Execute task asynchronously
        task_result = execute_orchestrator_task.delay(
            task_id=new_task.id,
            query=task_request.query,
            context=task_request.context or {}
        )
        
        # Update task with celery task ID
        await task_collection.update_one(
            {"_id": new_task.id},
            {"$set": {"celery_task_id": task_result.id}}
        )
        new_task.celery_task_id = task_result.id
        
        return new_task
        
    except HTTPException:
        # Re-raise HTTP exceptions (like subscription limits)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute task: {str(e)}"
        )
