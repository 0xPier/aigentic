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
from src.database.connection import mongodb
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
            result = loop.run_until_complete(
                memory_manager.process_task_feedback(task_id, mongodb.database)
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
            result = loop.run_until_complete(
                learning_loop.run_learning_cycle(agent_name, mongodb.database)
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
        
        # Delete memories older than 90 days with low relevance
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                memory_manager.cleanup_old_memories(cutoff_date, mongodb.database)
            )
            
            logger.info(f"Memory cleanup completed: {result}")
            return result
            
        finally:
            loop.close()
        
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
        
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                memory_manager.generate_performance_insights(mongodb.database)
            )
            
            logger.info(f"Performance insights generated: {result}")
            return result
            
        finally:
            loop.close()
        
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
        
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                learning_loop.schedule_learning_cycles(mongodb.database)
            )
            
            logger.info(f"Learning cycles scheduled: {result}")
            return result
            
        finally:
            loop.close()
        
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
