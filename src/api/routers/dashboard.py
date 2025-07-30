"""Dashboard router for aggregated statistics."""

from fastapi import APIRouter, Depends, HTTPException, status
import logging

from src.api.dependencies import get_default_user
from src.api.schemas import DashboardStats
from src.database.connection import mongodb
from src.database.models import User, Subscription

router = APIRouter()

logger = logging.getLogger(__name__)

@router.get("/", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_default_user),
):
    """Get dashboard statistics for current user."""
    logger.info(f"Fetching dashboard stats for user: {current_user.id}")
    try:
        db = mongodb.database
        stats_collection = db.dashboard_stats
        stats = await stats_collection.find_one({"user_id": current_user.id})

        if not stats:
            # If no stats exist, create them
            await update_dashboard_stats(current_user.id)
            stats = await stats_collection.find_one({"user_id": current_user.id})

        # Get subscription info
        subscription_doc = await db.subscriptions.find_one({"user_id": current_user.id})
        subscription = Subscription(**subscription_doc) if subscription_doc else None

        tasks_this_month = subscription.monthly_tasks_used if subscription else 0
        monthly_limit = subscription.monthly_tasks_limit if subscription else 10

        # Provide default values if stats is None
        if not stats:
            stats = {
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "failed_tasks": 0,
                "average_execution_time": 0.0
            }

        dashboard_data = DashboardStats(
            total_tasks=stats.get("total_tasks", 0),
            completed_tasks=stats.get("completed_tasks", 0),
            pending_tasks=stats.get("pending_tasks", 0),
            failed_tasks=stats.get("failed_tasks", 0),
            average_execution_time=stats.get("average_execution_time", 0.0),
            tasks_this_month=tasks_this_month,
            monthly_limit=monthly_limit,
            subscription_tier=current_user.subscription_tier if hasattr(current_user, 'subscription_tier') else "free"
        )
        logger.info(f"Successfully fetched dashboard data: {dashboard_data.dict()}")
        return dashboard_data
    except Exception as e:
        logger.error(f"Error fetching dashboard stats for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics"
        )

async def update_dashboard_stats(user_id):
    """Helper function to update dashboard stats."""
    db = mongodb.database
    task_stats_pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_tasks": {"$sum": 1},
            "completed_tasks": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "pending_tasks": {"$sum": {"$cond": [{"$in": ["$status", ["pending", "in_progress"]]}, 1, 0]}},
            "failed_tasks": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}},
            "total_execution_time": {"$sum": "$execution_time"},
            "completed_task_count": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}}
        }}
    ]
    
    # Use pymongo's async aggregation with proper cursor handling
    cursor = db.tasks.aggregate(task_stats_pipeline)
    task_stats_result = []
    async for doc in cursor:
        task_stats_result.append(doc)
    
    task_stats = task_stats_result[0] if task_stats_result else {}

    total_tasks = task_stats.get("total_tasks", 0)
    completed_tasks = task_stats.get("completed_tasks", 0)
    pending_tasks = task_stats.get("pending_tasks", 0)
    failed_tasks = task_stats.get("failed_tasks", 0)
    total_execution_time = task_stats.get("total_execution_time", 0.0)
    completed_task_count = task_stats.get("completed_task_count", 0)
    
    average_execution_time = (total_execution_time / completed_task_count) if completed_task_count > 0 else 0.0

    stats_data = {
        "user_id": user_id,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "failed_tasks": failed_tasks,
        "average_execution_time": average_execution_time,
    }

    await db.dashboard_stats.update_one(
        {"user_id": user_id},
        {"$set": stats_data},
        upsert=True
    )
