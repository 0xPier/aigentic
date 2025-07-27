"""Agents router for agent management and status."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime

from src.api.auth import get_current_active_user
from src.api.schemas import AgentMemoryCreate, AgentMemoryResponse
from src.database.connection import get_db
from src.database.models import User, AgentMemory, Task
from src.agents.registry import AgentRegistry

router = APIRouter()


@router.get("/available")
async def get_available_agents():
    """Get list of available agents and their capabilities."""
    registry = AgentRegistry()
    return {
        "agents": registry.get_all_agents(),
        "capabilities": registry.get_agent_capabilities()
    }


@router.get("/status/{agent_name}")
async def get_agent_status(agent_name: str):
    """Get status and performance metrics for a specific agent."""
    registry = AgentRegistry()
    agent_info = registry.get_agent_info(agent_name)
    
    if not agent_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return {
        "agent_name": agent_name,
        "status": "active",
        "info": agent_info,
        "last_execution": datetime.utcnow().isoformat()
    }


@router.post("/memory", response_model=AgentMemoryResponse)
async def create_agent_memory(
    memory_data: AgentMemoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create agent memory entry."""
    db_memory = AgentMemory(
        agent_name=memory_data.agent_name,
        memory_type=memory_data.memory_type,
        content=memory_data.content,
        context_tags=memory_data.context_tags,
        relevance_score=memory_data.relevance_score
    )
    
    db.add(db_memory)
    db.commit()
    db.refresh(db_memory)
    
    return db_memory


@router.get("/memory/{agent_name}", response_model=List[AgentMemoryResponse])
async def get_agent_memory(
    agent_name: str,
    memory_type: str = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get agent memory entries."""
    query = db.query(AgentMemory).filter(AgentMemory.agent_name == agent_name)
    
    if memory_type:
        query = query.filter(AgentMemory.memory_type == memory_type)
    
    memories = query.order_by(AgentMemory.relevance_score.desc()).limit(limit).all()
    return memories


@router.get("/performance")
async def get_agent_performance(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get performance metrics for all agents."""
    agent_stats = db.query(
        Task.assigned_agent,
        func.count(Task.id).label("total_tasks"),
        func.sum(case((Task.status == "completed", 1), else_=0)).label("completed_tasks"),
        func.sum(case((Task.status == "failed", 1), else_=0)).label("failed_tasks"),
        func.avg(Task.execution_time).label("average_execution_time")
    ).filter(
        Task.user_id == current_user.id,
        Task.assigned_agent.isnot(None)
    ).group_by(Task.assigned_agent).all()

    performance_data = [
        {
            "agent_name": stat.assigned_agent,
            "total_tasks": stat.total_tasks,
            "completed_tasks": stat.completed_tasks,
            "failed_tasks": stat.failed_tasks,
            "average_execution_time": float(stat.average_execution_time or 0.0),
            "success_rate": (stat.completed_tasks / stat.total_tasks * 100) if stat.total_tasks > 0 else 0
        }
        for stat in agent_stats
    ]

    return {"agent_performance": performance_data}
