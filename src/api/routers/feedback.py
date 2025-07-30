"""Feedback router for user feedback and ratings."""

from typing import List
from fastapi import APIRouter, Depends, BackgroundTasks

from src.api.dependencies import get_default_user
from src.database.connection import mongodb
from src.database.models import User, Feedback, Task
from src.api.schemas import FeedbackCreate, FeedbackResponse
from src.agents.memory_tasks import process_task_feedback_async
from .tasks import get_task_for_user

router = APIRouter()


@router.post("/", response_model=FeedbackResponse)
async def create_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_default_user),
    task: Task = Depends(get_task_for_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create feedback for a task."""
    feedback_collection = mongodb.database["feedback"]
    
    db_feedback = Feedback(
        user_id=current_user.id,
        task_id=task.id,
        rating=feedback_data.rating,
        comments=feedback_data.comments,
        feedback_type=feedback_data.feedback_type
    )
    
    result = await feedback_collection.insert_one(db_feedback.model_dump(by_alias=True, exclude_none=True))
    db_feedback.id = result.inserted_id
    
    # Trigger async feedback processing for learning
    background_tasks.add_task(process_task_feedback_async.delay, task.id)
    
    return db_feedback


@router.get("/", response_model=List[FeedbackResponse])
async def get_user_feedback(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_default_user),
):
    """Get user's feedback entries."""
    feedback_collection = mongodb.database["feedback"]
    feedback_cursor = feedback_collection.find({"user_id": current_user.id}).skip(skip).limit(limit)
    feedback = [Feedback(**doc) async for doc in feedback_cursor]
    
    return feedback


@router.get("/task/{task_id}", response_model=List[FeedbackResponse])
async def get_task_feedback(
    task: Task = Depends(get_task_for_user),
):
    """Get feedback for a specific task."""
    feedback_collection = mongodb.database["feedback"]
    feedback_cursor = feedback_collection.find({"task_id": task.id})
    feedback = [Feedback(**doc) async for doc in feedback_cursor]
    return feedback
