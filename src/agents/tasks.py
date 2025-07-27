"""Celery tasks for async agent execution."""

from celery import current_app
from datetime import datetime
from typing import Dict, Any
import traceback

from src.core.celery_app import celery_app
from src.database.connection import get_db
from src.database.models import Task, User
from src.agents.registry import get_agent_registry
from src.agents.base import AgentContext


@celery_app.task(bind=True)
async def execute_orchestrator_task(self, task_id: int, task_request: Dict[str, Any]):
    """Execute a task using the orchestrator agent."""
    db = get_db()
    
    try:
        # Get task from database
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update task status
        task.status = "in_progress"
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Get user
        user = db.query(User).filter(User.id == task.user_id).first()
        if not user:
            raise ValueError(f"User {task.user_id} not found")
        
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
        task.status = "completed" if result.success else "failed"
        task.completed_at = datetime.utcnow()
        task.execution_time = result.execution_time
        task.result_data = result.data
        task.output_files = result.output_files
        task.error_message = result.error if not result.success else None
        
        db.commit()
        
        return {
            "task_id": task_id,
            "success": result.success,
            "message": result.message,
            "execution_time": result.execution_time
        }
        
    except Exception as e:
        # Update task with error
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)
            db.commit()
        
        # Log error
        current_app.logger.error(f"Task {task_id} failed: {e}")
        current_app.logger.error(traceback.format_exc())
        
        # Re-raise for Celery
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True)
async def execute_single_agent_task(self, task_id: int, agent_name: str, query: str, context_data: Dict[str, Any] = None):
    """Execute a task using a single specific agent."""
    db = get_db()
    
    try:
        # Get task from database
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Update task status
        task.status = "in_progress"
        task.started_at = datetime.utcnow()
        task.assigned_agent = agent_name
        db.commit()
        
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
        task.status = "completed" if result.success else "failed"
        task.completed_at = datetime.utcnow()
        task.execution_time = result.execution_time
        task.result_data = result.data
        task.output_files = result.output_files
        task.error_message = result.error if not result.success else None
        
        db.commit()
        
        return {
            "task_id": task_id,
            "agent_name": agent_name,
            "success": result.success,
            "message": result.message,
            "execution_time": result.execution_time,
            "data": result.data
        }
        
    except Exception as e:
        # Update task with error
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = "failed"
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)
            db.commit()
        
        # Log error
        current_app.logger.error(f"Single agent task {task_id} failed: {e}")
        current_app.logger.error(traceback.format_exc())
        
        # Re-raise for Celery
        raise
        
    finally:
        db.close()


@celery_app.task
def cleanup_old_tasks():
    """Cleanup old completed tasks (maintenance task)."""
    db = get_db()
    
    try:
        from datetime import timedelta
        
        # Delete tasks older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_tasks = db.query(Task).filter(
            Task.completed_at < cutoff_date,
            Task.status.in_(["completed", "failed"])
        ).all()
        
        count = len(old_tasks)
        
        for task in old_tasks:
            # TODO: Clean up associated files
            db.delete(task)
        
        db.commit()
        
        return f"Cleaned up {count} old tasks"
        
    except Exception as e:
        current_app.logger.error(f"Cleanup task failed: {e}")
        raise
        
    finally:
        db.close()


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
def generate_usage_analytics():
    """Generate usage analytics for the platform."""
    db = get_db()
    
    try:
        from sqlalchemy import func
        
        # Get basic statistics
        total_users = db.query(User).count()
        total_tasks = db.query(Task).count()
        completed_tasks = db.query(Task).filter(Task.status == "completed").count()
        
        # Get task statistics by agent
        agent_stats = db.query(
            Task.assigned_agent,
            func.count(Task.id).label("total"),
            func.count(Task.id).filter(Task.status == "completed").label("completed")
        ).filter(
            Task.assigned_agent.isnot(None)
        ).group_by(Task.assigned_agent).all()
        
        analytics = {
            "total_users": total_users,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "agent_statistics": [
                {
                    "agent": stat.assigned_agent,
                    "total_tasks": stat.total,
                    "completed_tasks": stat.completed,
                    "success_rate": (stat.completed / stat.total * 100) if stat.total > 0 else 0
                }
                for stat in agent_stats
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return analytics
        
    except Exception as e:
        current_app.logger.error(f"Analytics generation failed: {e}")
        raise
        
    finally:
        db.close()
