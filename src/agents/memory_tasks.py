"""
Celery tasks for agent memory management and learning loops.
Handles automated feedback processing and continuous learning cycles.
"""

import asyncio
from celery import Celery
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from src.core.celery_app import celery_app
from src.database.connection import get_db
from src.database.models import Task, Feedback, AgentMemory, User
from src.agents.memory_manager import memory_manager, learning_loop, feedback_processor

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_task_feedback_async(self, task_id: int):
    """
    Asynchronously process feedback for a completed task.
    
    Args:
        task_id: ID of the task to process feedback for
    
    Returns:
        Dict with processing results
    """
    try:
        logger.info(f"Starting feedback processing for task {task_id}")
        
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            db = next(get_db())
            result = loop.run_until_complete(
                memory_manager.process_task_feedback(task_id, db)
            )
            
            logger.info(f"Feedback processing completed for task {task_id}: {result}")
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Feedback processing failed for task {task_id}: {str(e)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 2 ** self.request.retries * 60  # 1, 2, 4 minutes
            logger.info(f"Retrying feedback processing for task {task_id} in {retry_delay} seconds")
            raise self.retry(countdown=retry_delay, exc=e)
        
        return {
            "error": str(e),
            "task_id": task_id,
            "status": "failed",
            "retries_exhausted": True
        }


@celery_app.task(bind=True, max_retries=2)
def run_learning_cycle_async(self, agent_name: str = None):
    """
    Run automated learning cycle for agents.
    
    Args:
        agent_name: Specific agent to process, or None for all agents
    
    Returns:
        Dict with learning cycle results
    """
    try:
        logger.info(f"Starting learning cycle for agent: {agent_name or 'all agents'}")
        
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            db = next(get_db())
            result = loop.run_until_complete(
                learning_loop.run_learning_cycle(agent_name, db)
            )
            
            logger.info(f"Learning cycle completed: {result}")
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Learning cycle failed: {str(e)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 5 ** self.request.retries * 60  # 5, 25 minutes
            logger.info(f"Retrying learning cycle in {retry_delay} seconds")
            raise self.retry(countdown=retry_delay, exc=e)
        
        return {
            "error": str(e),
            "agent_name": agent_name,
            "status": "failed",
            "retries_exhausted": True
        }


@celery_app.task
def cleanup_old_memories():
    """
    Clean up old, low-relevance memories to maintain performance.
    Runs periodically to prevent memory table from growing too large.
    """
    try:
        logger.info("Starting memory cleanup task")
        
        db = next(get_db())
        
        # Delete memories older than 90 days with low relevance
        cutoff_date = datetime.now() - timedelta(days=90)
        
        old_memories = db.query(AgentMemory).filter(
            AgentMemory.created_at < cutoff_date,
            AgentMemory.relevance_score < 0.3
        )
        
        count_before = old_memories.count()
        old_memories.delete()
        db.commit()
        
        logger.info(f"Cleaned up {count_before} old memories")
        
        # Update relevance scores based on recent usage patterns
        recent_memories = db.query(AgentMemory).filter(
            AgentMemory.created_at >= datetime.now() - timedelta(days=30)
        ).all()
        
        updated_count = 0
        for memory in recent_memories:
            # Decay relevance score over time
            days_old = (datetime.now() - memory.created_at).days
            decay_factor = max(0.1, 1.0 - (days_old * 0.01))  # 1% decay per day
            
            new_score = memory.relevance_score * decay_factor
            if abs(new_score - memory.relevance_score) > 0.05:  # Only update if significant change
                memory.relevance_score = new_score
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
            logger.info(f"Updated relevance scores for {updated_count} memories")
        
        return {
            "memories_deleted": count_before,
            "relevance_scores_updated": updated_count,
            "cleanup_completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Memory cleanup failed: {str(e)}")
        return {
            "error": str(e),
            "cleanup_completed_at": datetime.now().isoformat()
        }


@celery_app.task
def generate_performance_insights():
    """
    Generate performance insights across all agents.
    Analyzes patterns and generates recommendations for system optimization.
    """
    try:
        logger.info("Starting performance insights generation")
        
        db = next(get_db())
        
        # Get performance data for all agents
        agents_data = {}
        
        # Query recent tasks and feedback
        recent_tasks = db.query(Task).filter(
            Task.created_at >= datetime.now() - timedelta(days=30)
        ).all()
        
        for task in recent_tasks:
            agent_name = task.agent_name
            if agent_name not in agents_data:
                agents_data[agent_name] = {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "avg_execution_time": 0,
                    "feedback_ratings": [],
                    "memory_entries": 0
                }
            
            agents_data[agent_name]["total_tasks"] += 1
            
            if task.status == "completed":
                agents_data[agent_name]["completed_tasks"] += 1
                if task.execution_time:
                    agents_data[agent_name]["avg_execution_time"] += task.execution_time
            elif task.status == "failed":
                agents_data[agent_name]["failed_tasks"] += 1
            
            # Get feedback for this task
            feedback_entries = db.query(Feedback).filter(Feedback.task_id == task.id).all()
            for feedback in feedback_entries:
                if feedback.rating:
                    agents_data[agent_name]["feedback_ratings"].append(feedback.rating)
        
        # Calculate averages and get memory counts
        for agent_name, data in agents_data.items():
            if data["completed_tasks"] > 0:
                data["avg_execution_time"] = data["avg_execution_time"] / data["completed_tasks"]
                data["success_rate"] = data["completed_tasks"] / data["total_tasks"]
            else:
                data["success_rate"] = 0
            
            if data["feedback_ratings"]:
                data["avg_rating"] = sum(data["feedback_ratings"]) / len(data["feedback_ratings"])
            else:
                data["avg_rating"] = 0
            
            # Get memory count
            memory_count = db.query(AgentMemory).filter(
                AgentMemory.agent_name == agent_name
            ).count()
            data["memory_entries"] = memory_count
        
        # Generate insights using the data
        insights = {
            "generated_at": datetime.now().isoformat(),
            "period_days": 30,
            "agents_analyzed": len(agents_data),
            "top_performers": [],
            "improvement_needed": [],
            "system_recommendations": []
        }
        
        # Identify top performers and those needing improvement
        for agent_name, data in agents_data.items():
            performance_score = (
                data["success_rate"] * 0.4 +
                (data["avg_rating"] / 5.0) * 0.4 +
                (1.0 if data["avg_execution_time"] < 30 else 0.5) * 0.2
            )
            
            agent_summary = {
                "agent_name": agent_name,
                "performance_score": performance_score,
                "success_rate": data["success_rate"],
                "avg_rating": data["avg_rating"],
                "total_tasks": data["total_tasks"]
            }
            
            if performance_score >= 0.8:
                insights["top_performers"].append(agent_summary)
            elif performance_score < 0.6:
                insights["improvement_needed"].append(agent_summary)
        
        # Generate system recommendations
        total_tasks = sum(data["total_tasks"] for data in agents_data.values())
        total_failed = sum(data["failed_tasks"] for data in agents_data.values())
        
        if total_tasks > 0:
            system_failure_rate = total_failed / total_tasks
            if system_failure_rate > 0.1:
                insights["system_recommendations"].append(
                    f"High system failure rate ({system_failure_rate:.1%}). Review error handling and API reliability."
                )
        
        avg_ratings = [data["avg_rating"] for data in agents_data.values() if data["avg_rating"] > 0]
        if avg_ratings and sum(avg_ratings) / len(avg_ratings) < 3.5:
            insights["system_recommendations"].append(
                "Overall user satisfaction is below target. Focus on quality improvements."
            )
        
        logger.info(f"Performance insights generated for {len(agents_data)} agents")
        return insights
        
    except Exception as e:
        logger.error(f"Performance insights generation failed: {str(e)}")
        return {
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        }


@celery_app.task
def schedule_learning_cycles():
    """
    Schedule regular learning cycles for all agents.
    This task runs daily and triggers learning cycles for active agents.
    """
    try:
        logger.info("Scheduling learning cycles for active agents")
        
        db = next(get_db())
        
        # Get agents that have had activity in the last 7 days
        active_agents = db.query(Task.agent_name).filter(
            Task.created_at >= datetime.now() - timedelta(days=7)
        ).distinct().all()
        
        scheduled_tasks = []
        
        for agent_tuple in active_agents:
            agent_name = agent_tuple[0]
            
            # Schedule learning cycle with delay to spread load
            task_result = run_learning_cycle_async.apply_async(
                args=[agent_name],
                countdown=len(scheduled_tasks) * 60  # 1 minute delay between each
            )
            
            scheduled_tasks.append({
                "agent_name": agent_name,
                "task_id": task_result.id,
                "scheduled_at": datetime.now().isoformat()
            })
        
        logger.info(f"Scheduled learning cycles for {len(scheduled_tasks)} agents")
        
        return {
            "scheduled_count": len(scheduled_tasks),
            "scheduled_tasks": scheduled_tasks,
            "scheduled_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Learning cycle scheduling failed: {str(e)}")
        return {
            "error": str(e),
            "scheduled_at": datetime.now().isoformat()
        }


# Periodic task scheduling
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic tasks for memory management and learning."""
    
    # Run learning cycles daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        schedule_learning_cycles.s(),
        name='daily-learning-cycles'
    )
    
    # Clean up old memories weekly on Sunday at 3 AM
    sender.add_periodic_task(
        crontab(hour=3, minute=0, day_of_week=0),
        cleanup_old_memories.s(),
        name='weekly-memory-cleanup'
    )
    
    # Generate performance insights weekly on Monday at 1 AM
    sender.add_periodic_task(
        crontab(hour=1, minute=0, day_of_week=1),
        generate_performance_insights.s(),
        name='weekly-performance-insights'
    )
