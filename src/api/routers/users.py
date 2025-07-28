"""Users router for user management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from src.api.auth import get_current_active_user
from src.api.schemas import UserResponse, UserUpdate, DashboardStats
from src.database.connection import get_db
from src.database.models import User, Task, Subscription

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information."""
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for current user."""
    # Optimized query for task statistics
    task_stats = db.query(
        func.count(Task.id).label("total_tasks"),
        func.sum(case((Task.status == "completed", 1), else_=0)).label("completed_tasks"),
        func.sum(case((Task.status.in_(["pending", "in_progress"]), 1), else_=0)).label("pending_tasks"),
        func.sum(case((Task.status == "failed", 1), else_=0)).label("failed_tasks"),
        func.avg(Task.execution_time).label("average_execution_time")
    ).filter(Task.user_id == current_user.id).one()

    # Get subscription info
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    tasks_this_month = subscription.monthly_tasks_used if subscription else 0
    monthly_limit = subscription.monthly_tasks_limit if subscription else 10

    return DashboardStats(
        total_tasks=task_stats.total_tasks or 0,
        completed_tasks=task_stats.completed_tasks or 0,
        pending_tasks=task_stats.pending_tasks or 0,
        failed_tasks=task_stats.failed_tasks or 0,
        average_execution_time=float(task_stats.average_execution_time or 0.0),
        tasks_this_month=tasks_this_month,
        monthly_limit=monthly_limit,
        subscription_tier=current_user.subscription_tier
    )
