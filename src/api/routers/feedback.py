"""Feedback router for user feedback and ratings."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from src.api.auth import get_current_user, get_current_active_user
from src.database.connection import get_db
from src.database.models import User, Feedback, Task
from src.api.schemas import FeedbackCreate, FeedbackResponse
from src.agents.memory_tasks import process_task_feedback_async
from .tasks import get_task_for_user

router = APIRouter()


@router.post("/", response_model=FeedbackResponse)
async def create_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    task: Task = Depends(get_task_for_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create feedback for a task."""
    # Create feedback
    db_feedback = Feedback(
        user_id=current_user.id,
        task_id=task.id,
        rating=feedback_data.rating,
        comments=feedback_data.comments,
        feedback_type=feedback_data.feedback_type
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    # Trigger async feedback processing for learning
    background_tasks.add_task(process_task_feedback_async.delay, task.id)
    
    return db_feedback


@router.get("/", response_model=List[FeedbackResponse])
async def get_user_feedback(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's feedback entries."""
    feedback = db.query(Feedback).filter(
        Feedback.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return feedback


@router.get("/task/{task_id}", response_model=List[FeedbackResponse])
async def get_task_feedback(
    task: Task = Depends(get_task_for_user),
    db: Session = Depends(get_db)
):
    """Get feedback for a specific task."""
    return db.query(Feedback).filter(Feedback.task_id == task.id).all()
