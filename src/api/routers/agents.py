from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from src.api.dependencies import get_default_user
from src.api.schemas import AgentMemoryCreate, AgentMemoryResponse
from src.database.connection import mongodb
from src.database.models import User, AgentMemory, Task, PyObjectId
from src.agents.registry import AgentRegistry

router = APIRouter()


@router.get("/")
async def get_agents(
    current_user: User = Depends(get_default_user),
):
    """Get list of all agents and their basic information."""
    registry = AgentRegistry()
    agents = registry.get_all_agents()
    
    # Get performance data for each agent
    task_collection = mongodb.database["tasks"]
    agent_stats_pipeline = [
        {"$match": {"user_id": current_user.id, "assigned_agent": {"$ne": None}}},
        {"$group": {
            "_id": "$assigned_agent",
            "total_tasks": {"$sum": 1},
            "completed_tasks": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "failed_tasks": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}},
        }}
    ]
    
    agent_stats_cursor = task_collection.aggregate(agent_stats_pipeline)
    performance_data = {}
    async for stat in agent_stats_cursor:
        agent_name = stat["_id"]
        performance_data[agent_name] = {
            "total_tasks": stat["total_tasks"],
            "completed_tasks": stat["completed_tasks"],
            "failed_tasks": stat["failed_tasks"],
            "success_rate": (stat["completed_tasks"] / stat["total_tasks"] * 100) if stat["total_tasks"] > 0 else 0
        }
    
    # Combine agent info with performance data
    result = []
    for agent_name, agent_info in agents.items():
        agent_data = {
            "name": agent_name,
            "info": agent_info,
            "performance": performance_data.get(agent_name, {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "success_rate": 0
            })
        }
        result.append(agent_data)
    
    return result


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
    current_user: User = Depends(get_default_user),
):
    """Create agent memory entry."""
    agent_memory_collection = mongodb.database["agent_memory"]
    memory_dict = memory_data.model_dump(exclude_unset=True)
    
    new_memory = AgentMemory(**memory_dict)
    result = await agent_memory_collection.insert_one(new_memory.model_dump(by_alias=True, exclude_none=True))
    new_memory.id = result.inserted_id
    
    return new_memory


@router.get("/memory/{agent_name}", response_model=List[AgentMemoryResponse])
async def get_agent_memory(
    agent_name: str,
    memory_type: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_default_user),
):
    """Get agent memory entries."""
    agent_memory_collection = mongodb.database["agent_memory"]
    query_filter = {"agent_name": agent_name}
    
    if memory_type:
        query_filter["memory_type"] = memory_type
    
    memories_cursor = agent_memory_collection.find(query_filter).sort("relevance_score", -1).limit(limit)
    memories = [AgentMemory(**doc) async for doc in memories_cursor]
    return memories


@router.get("/performance")
async def get_agent_performance(
    current_user: User = Depends(get_default_user),
):
    """Get performance metrics for all agents."""
    task_collection = mongodb.database["tasks"]
    
    agent_stats_pipeline = [
        {"$match": {"user_id": current_user.id, "assigned_agent": {"$ne": None}}},
        {"$group": {
            "_id": "$assigned_agent",
            "total_tasks": {"$sum": 1},
            "completed_tasks": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "failed_tasks": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}},
            "total_execution_time": {"$sum": "$execution_time"},
        }}
    ]
    
    agent_stats_cursor = task_collection.aggregate(agent_stats_pipeline)
    performance_data = []
    async for stat in agent_stats_cursor:
        agent_name = stat["_id"]
        total_tasks = stat.get("total_tasks", 0)
        completed_tasks = stat.get("completed_tasks", 0)
        failed_tasks = stat.get("failed_tasks", 0)
        total_execution_time = stat.get("total_execution_time", 0.0)
        
        average_execution_time = (total_execution_time / completed_tasks) if completed_tasks > 0 else 0.0
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        performance_data.append({
            "agent_name": agent_name,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "average_execution_time": average_execution_time,
            "success_rate": success_rate
        })

    return performance_data