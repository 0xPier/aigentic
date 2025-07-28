"""Tasks router for task management and agent orchestration."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.api.auth import get_current_active_user, check_subscription_limits
from src.api.schemas import (
    TaskCreate, TaskResponse, TaskUpdate, AgentTaskRequest, AgentTaskResponse
)
from src.database.connection import get_db
from src.database.models import User, Task, Project
# from src.agents.tasks import execute_orchestrator_task

router = APIRouter()

async def get_task_for_user(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Task:
    """Dependency to get a task and verify ownership."""
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new task."""
    # Verify project ownership if project_id is provided
    if task_data.project_id:
        project = db.query(Project).filter(
            Project.id == task_data.project_id,
            Project.owner_id == current_user.id
        ).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    
    # Create task
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        query=task_data.query,
        task_type=task_data.task_type,
        priority=task_data.priority,
        user_id=current_user.id,
        project_id=task_data.project_id
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task


@router.get("/", response_model=List[TaskResponse])
async def get_user_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's tasks with optional filtering."""
    query = db.query(Task).filter(Task.user_id == current_user.id)
    
    if status:
        query = query.filter(Task.status == status)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task: Task = Depends(get_task_for_user)):
    """Get a specific task."""
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_update: TaskUpdate,
    task: Task = Depends(get_task_for_user),
    db: Session = Depends(get_db)
):
    """Update a task."""
    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task: Task = Depends(get_task_for_user),
    db: Session = Depends(get_db)
):
    """Delete a task."""
    db.delete(task)
    db.commit()
    return {"message": "Task deleted successfully"}


@router.post("/execute", response_model=TaskResponse)
async def execute_agent_task(
    task_request: AgentTaskRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute a task using the orchestrator agent with subscription checking."""
    try:
        # Check subscription limits before executing
        check_subscription_limits(current_user, db, "task_execution")
        
        # Create task record
        db_task = Task(
            title=f"Agent Task: {task_request.agent_name}",
            description=task_request.query,
            agent_name=task_request.agent_name,
            user_id=current_user.id,
            status="pending"
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        
        # Execute task asynchronously
        # task_result = execute_orchestrator_task.delay(
        #     task_id=db_task.id,
        #     query=task_request.query,
        #     context=task_request.context or {}
        # )
        
        # Update task with celery task ID
        # db_task.celery_task_id = task_result.id
        # db.commit()
        
        return db_task
        
    except HTTPException:
        # Re-raise HTTP exceptions (like subscription limits)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute task: {str(e)}"
        )
