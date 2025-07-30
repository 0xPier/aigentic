"""Celery tasks for async agent execution."""

from celery import current_app
from datetime import datetime
from typing import Dict, Any
import traceback

from src.core.celery_app import celery_app
from src.database.connection import mongodb
from src.database.models import Task, User, PyObjectId
from src.agents.registry import get_agent_registry
from src.agents.base import AgentContext


@celery_app.task(bind=True)
async def execute_orchestrator_task(self, task_id: int, task_request: Dict[str, Any]):
    """Execute a task using the orchestrator agent."""
    try:
        # Get task from database
        task_doc = await mongodb.database["tasks"].find_one({"_id": task_id})
        if not task_doc:
            raise ValueError(f"Task {task_id} not found")
        task = Task(**task_doc)
        
        # Update task status
        await mongodb.database["tasks"].update_one(
            {"_id": task_id},
            {"$set": {"status": "in_progress", "started_at": datetime.utcnow()}}
        )
        task.status = "in_progress"
        task.started_at = datetime.utcnow()
        
        # Get user
        user_doc = await mongodb.database["users"].find_one({"_id": task.user_id})
        if not user_doc:
            raise ValueError(f"User {task.user_id} not found")
        user = User(**user_doc)
        
        # Get orchestrator agent
        registry = get_agent_registry()
        orchestrator = registry.get_agent("orchestrator")
        
        if not orchestrator:
            raise ValueError("Orchestrator agent not available")
        
        # Create agent context
        context = AgentContext(
            user_id=task.user_id,
            task_id=task.id,
            query=task.query,
            task_type=task.task_type or "general",
            priority=task.priority,
            project_id=task.project_id,
            previous_results=None,
            integrations=None  # TODO: Load user integrations
        )
        
        # Execute orchestrator
        result = orchestrator.execute(context)
        
        # Update task with results
        update_data = {
            "status": "completed" if result.success else "failed",
            "completed_at": datetime.utcnow(),
            "execution_time": result.execution_time,
            "result_data": result.data,
            "output_files": result.output_files,
            "error_message": result.error if not result.success else None
        }
        await mongodb.database["tasks"].update_one(
            {"_id": task_id},
            {"$set": update_data}
        )
        
        return {
            "task_id": str(task_id),
            "success": result.success,
            "message": result.message,
            "execution_time": result.execution_time
        }
        
    except Exception as e:
        # Update task with error
        task_doc = await mongodb.database["tasks"].find_one({"_id": task_id})
        if task_doc:
            await mongodb.database["tasks"].update_one(
                {"_id": task_id},
                {"$set": {"status": "failed", "completed_at": datetime.utcnow(), "error_message": str(e)}}
            )
        
        # Log error
        current_app.logger.error(f"Task {task_id} failed: {e}")
        current_app.logger.error(traceback.format_exc())
        
        # Re-raise for Celery
        raise


@celery_app.task(bind=True)
async def execute_single_agent_task(self, task_id: PyObjectId, agent_name: str, query: str, context_data: Dict[str, Any] = None):
    """Execute a task using a single specific agent."""
    try:
        # Get task from database
        task_doc = await mongodb.database["tasks"].find_one({"_id": task_id})
        if not task_doc:
            raise ValueError(f"Task {task_id} not found")
        task = Task(**task_doc)
        
        # Update task status
        await mongodb.database["tasks"].update_one(
            {"_id": task_id},
            {"$set": {"status": "in_progress", "started_at": datetime.utcnow(), "assigned_agent": agent_name}}
        )
        task.status = "in_progress"
        task.started_at = datetime.utcnow()
        task.assigned_agent = agent_name
        
        # Get agent
        registry = get_agent_registry()
        agent = registry.get_agent(agent_name)
        
        if not agent:
            raise ValueError(f"Agent {agent_name} not available")
        
        # Create agent context
        context = AgentContext(
            user_id=task.user_id,
            task_id=task.id,
            query=query,
            task_type=agent_name,
            priority=task.priority,
            project_id=task.project_id,
            previous_results=context_data.get("previous_results") if context_data else None,
            integrations=context_data.get("integrations") if context_data else None
        )
        
        # Execute agent
        result = await agent.execute(context)
        
        # Update task with results
        update_data = {
            "status": "completed" if result.success else "failed",
            "completed_at": datetime.utcnow(),
            "execution_time": result.execution_time,
            "result_data": result.data,
            "output_files": result.output_files,
            "error_message": result.error if not result.success else None
        }
        await mongodb.database["tasks"].update_one(
            {"_id": task_id},
            {"$set": update_data}
        )
        
        return {
            "task_id": str(task_id),
            "agent_name": agent_name,
            "success": result.success,
            "message": result.message,
            "execution_time": result.execution_time,
            "data": result.data
        }
        
    except Exception as e:
        # Update task with error
        task_doc = await mongodb.database["tasks"].find_one({"_id": task_id})
        if task_doc:
            await mongodb.database["tasks"].update_one(
                {"_id": task_id},
                {"$set": {"status": "failed", "completed_at": datetime.utcnow(), "error_message": str(e)}}
            )
        
        # Log error
        current_app.logger.error(f"Single agent task {task_id} failed: {e}")
        current_app.logger.error(traceback.format_exc())
        
        # Re-raise for Celery
        raise


@celery_app.task
async def cleanup_old_tasks():
    """Cleanup old completed tasks (maintenance task)."""
    try:
        from datetime import timedelta
        
        # Delete tasks older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        result = await mongodb.database["tasks"].delete_many({
            "completed_at": {"$lt": cutoff_date},
            "status": {"$in": ["completed", "failed"]}
        })
        
        count = result.deleted_count
        
        return f"Cleaned up {count} old tasks"
        
    except Exception as e:
        current_app.logger.error(f"Cleanup task failed: {e}")
        raise


@celery_app.task
def update_agent_memory():
    """Update agent memory and learning (maintenance task)."""
    try:
        # TODO: Implement memory consolidation and learning updates
        # This could include:
        # - Analyzing successful vs failed tasks
        # - Updating agent performance metrics
        # - Consolidating similar memories
        # - Removing outdated or irrelevant memories
        
        return "Agent memory updated successfully"
        
    except Exception as e:
        current_app.logger.error(f"Memory update task failed: {e}")
        raise


@celery_app.task
async def generate_usage_analytics():
    """Generate usage analytics for the platform."""
    try:
        # Get basic statistics
        total_users = await mongodb.database["users"].count_documents({})
        total_tasks = await mongodb.database["tasks"].count_documents({})
        completed_tasks = await mongodb.database["tasks"].count_documents({"status": "completed"})
        
        # Get task statistics by agent
        agent_stats_pipeline = [
            {"$match": {"assigned_agent": {"$ne": None}}},
            {"$group": {
                "_id": "$assigned_agent",
                "total": {"$sum": 1},
                "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}}
            }}
        ]
        agent_stats_cursor = mongodb.database["tasks"].aggregate(agent_stats_pipeline)
        agent_stats = []
        async for stat in agent_stats_cursor:
            agent_stats.append({
                "assigned_agent": stat["_id"],
                "total": stat["total"],
                "completed": stat["completed"]
            })
        
        analytics = {
            "total_users": total_users,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "agent_statistics": [
                {
                    "agent": stat["assigned_agent"],
                    "total_tasks": stat["total"],
                    "completed_tasks": stat["completed"],
                    "success_rate": (stat["completed"] / stat["total"] * 100) if stat["total"] > 0 else 0
                }
                for stat in agent_stats
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return analytics
        
    except Exception as e:
        current_app.logger.error(f"Analytics generation failed: {e}")
        raise
