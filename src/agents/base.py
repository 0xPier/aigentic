"""Base agent interface and utilities for the multi-agent system."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.core.config import app_config
from .memory_manager import memory_manager, MemoryType
from ..database.models import AgentMemory
from src.database.connection import mongodb

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result object returned by agent execution."""
    success: bool
    data: Dict[str, Any]
    message: str
    execution_time: float
    output_files: List[str] = None
    error: Optional[str] = None


@dataclass
class AgentContext:
    """Context object passed to agents during execution."""
    user_id: int
    task_id: int
    query: str
    task_type: str
    priority: str
    project_id: Optional[int] = None
    previous_results: Dict[str, Any] = None
    integrations: Dict[str, Any] = None


class BaseAgent(ABC):
    """Base class for all AI agents in the system."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"agent.{name}")
        self.execution_history = []
        self.performance_metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time": 0,
            "last_execution": None
        }
        self.memory_enabled = True
        self.learning_context = []
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent's main functionality."""
        pass
    
    @abstractmethod
    def get_required_integrations(self) -> List[str]:
        """Return list of required third-party integrations."""
        pass
    
    def validate_context(self, context: AgentContext) -> bool:
        """Validate that the context contains required information."""
        return True
    
    def _update_average_execution_time(self, execution_time: float):
        """Update the rolling average execution time."""
        current_avg = self.performance_metrics["average_execution_time"]
        total_executions = self.performance_metrics["total_executions"]
        
        if total_executions == 1:
            self.performance_metrics["average_execution_time"] = execution_time
        else:
            # Calculate rolling average
            new_avg = ((current_avg * (total_executions - 1)) + execution_time) / total_executions
            self.performance_metrics["average_execution_time"] = new_avg
    
    async def _load_relevant_memories(self, context: AgentContext):
        """Load relevant memories to inform execution."""
        try:
            # Generate context tags from the current request
            context_tags = self._extract_context_tags(context)
            
            # Retrieve relevant memories
            memories = await memory_manager.retrieve_memories(
                agent_name=self.name,
                context_tags=context_tags,
                limit=5,
                min_relevance=0.6
            )
            
            # Store memories in learning context for use during execution
            self.learning_context = memories
            
            if memories:
                self.logger.info(f"Loaded {len(memories)} relevant memories for execution")
            
        except Exception as e:
            self.logger.error(f"Failed to load memories: {str(e)}")
            self.learning_context = []
    
    async def _store_execution_memory(self, context: AgentContext, result: AgentResult, execution_time: float):
        """Store successful execution as memory for future learning."""
        try:
            memory_content = {
                "execution_summary": {
                    "task_type": context.task_type,
                    "parameters": context.parameters,
                    "execution_time": execution_time,
                    "success": result.success,
                    "summary": result.summary
                },
                "performance_data": {
                    "execution_time": execution_time,
                    "data_size": len(str(result.data)) if result.data else 0,
                    "timestamp": datetime.now().isoformat()
                },
                "context_tags": self._extract_context_tags(context)
            }
            
            # Calculate relevance based on execution success and performance
            relevance_score = self._calculate_execution_relevance(execution_time, result)
            
            await memory_manager.store_memory(
                agent_name=self.name,
                memory_type=MemoryType.SUCCESS,
                content=memory_content,
                context_tags=self._extract_context_tags(context),
                relevance_score=relevance_score
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store execution memory: {str(e)}")
    
    async def _store_error_memory(self, context: AgentContext, error_message: str, execution_time: float):
        """Store execution error as memory for future learning."""
        try:
            memory_content = {
                "error_details": {
                    "task_type": context.task_type,
                    "parameters": context.parameters,
                    "error_message": error_message,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                },
                "context_tags": self._extract_context_tags(context),
                "learning_notes": f"Error occurred during {context.task_type} execution"
            }
            
            await memory_manager.store_memory(
                agent_name=self.name,
                memory_type=MemoryType.ERROR,
                content=memory_content,
                context_tags=self._extract_context_tags(context) + ["error", "failure"],
                relevance_score=0.8  # Errors are highly relevant for learning
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store error memory: {str(e)}")
    
    def _extract_context_tags(self, context: AgentContext) -> List[str]:
        """Extract relevant tags from execution context."""
        tags = [self.name.lower(), context.task_type]
        
        # Add parameter-based tags
        if context.parameters:
            for key, value in context.parameters.items():
                if isinstance(value, str) and len(value) < 50:
                    tags.append(f"{key}_{value}".lower())
                else:
                    tags.append(key.lower())
        
        # Add user-based tags if available
        if hasattr(context, 'user_id') and context.user_id:
            tags.append(f"user_{context.user_id}")
        
        return list(set(tags))  # Remove duplicates
    
    def _calculate_execution_relevance(self, execution_time: float, result: AgentResult) -> float:
        """Calculate relevance score for execution memory."""
        base_relevance = 0.7
        
        # Boost relevance for fast executions
        if execution_time < self.performance_metrics["average_execution_time"]:
            base_relevance += 0.2
        
        # Boost relevance for successful executions with substantial output
        if result.success and result.data:
            data_size = len(str(result.data))
            if data_size > 1000:  # Substantial output
                base_relevance += 0.1
        
        return min(1.0, base_relevance)
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get learning insights from stored memories."""
        try:
            memories = await memory_manager.retrieve_memories(
                agent_name=self.name,
                limit=20,
                min_relevance=0.5
            )
            
            insights = {
                "agent_name": self.name,
                "total_memories": len(memories),
                "memory_types": {},
                "performance_trends": self._analyze_performance_trends(memories),
                "common_patterns": self._identify_common_patterns(memories),
                "improvement_suggestions": []
            }
            
            # Analyze memory types
            for memory in memories:
                memory_type = memory.get("memory_type", "unknown")
                insights["memory_types"][memory_type] = insights["memory_types"].get(memory_type, 0) + 1
            
            # Generate improvement suggestions based on error patterns
            error_memories = [m for m in memories if m.get("memory_type") == MemoryType.ERROR]
            if error_memories:
                insights["improvement_suggestions"].append(
                    f"Found {len(error_memories)} error patterns. Review error handling for common failure modes."
                )
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Failed to get learning insights: {str(e)}")
            return {"error": str(e), "agent_name": self.name}
    
    def _analyze_performance_trends(self, memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance trends from memory data."""
        execution_times = []
        success_count = 0
        total_count = 0
        
        for memory in memories:
            if memory.get("memory_type") in [MemoryType.SUCCESS, MemoryType.ERROR]:
                content = memory.get("content", {})
                if "execution_summary" in content:
                    exec_time = content["execution_summary"].get("execution_time")
                    if exec_time:
                        execution_times.append(exec_time)
                    
                    if content["execution_summary"].get("success"):
                        success_count += 1
                    total_count += 1
        
        trends = {
            "avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "total_executions_analyzed": total_count
        }
        
        return trends
    
    def _identify_common_patterns(self, memories: List[Dict[str, Any]]) -> List[str]:
        """Identify common patterns from memory data."""
        patterns = []
        
        # Analyze context tags for common patterns
        all_tags = []
        for memory in memories:
            tags = memory.get("context_tags", [])
            all_tags.extend(tags)
        
        # Find most common tags
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for tag, count in common_tags:
            if count > 2:  # Only include tags that appear multiple times
                patterns.append(f"Frequent context: {tag} ({count} occurrences)")
        
        return patterns
    
    def log_execution(self, context: AgentContext, result: AgentResult):
        """Log agent execution for monitoring and debugging."""
        self.logger.info(
            f"Agent {self.name} executed for task {context.task_id}: "
            f"Success={result.success}, Time={result.execution_time:.2f}s"
        )
        
        # Save execution to memory for learning
        if self.memory_enabled:
            execution_memory = {
                "task_id": context.task_id,
                "query": context.query,
                "task_type": context.task_type,
                "success": result.success,
                "execution_time": result.execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if result.error:
                execution_memory["error"] = result.error
            
            self.save_memory(
                memory_type="execution",
                content=execution_memory,
                context_tags=[context.task_type, "execution"],
                relevance_score=1.0 if result.success else 0.5
            )
    
    def save_memory(self, memory_type: str, content: Dict[str, Any], 
                   context_tags: List[str] = None, relevance_score: float = 1.0):
        """Save information to agent memory."""
        if not self.memory_enabled:
            return
        
        try:
            memory = AgentMemory(
                agent_name=self.name,
                memory_type=memory_type,
                content=content,
                context_tags=context_tags or [],
                relevance_score=relevance_score
            )
            mongodb.database["agent_memory"].insert_one(memory.model_dump(by_alias=True, exclude_none=True))
        except Exception as e:
            self.logger.error(f"Failed to save memory: {e}")
    
    async def retrieve_memory(self, memory_type: str = None, 
                       context_tags: List[str] = None, 
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve relevant memories."""
        try:
            query_filter = {"agent_name": self.name}
            
            if memory_type:
                query_filter["memory_type"] = memory_type
            
            if context_tags:
                query_filter["context_tags"] = {"$all": context_tags}
            
            memories_cursor = mongodb.database["agent_memory"].find(query_filter).sort(
                [('relevance_score', -1)]
            ).limit(limit)
            
            memories = []
            async for doc in memories_cursor:
                memories.append(AgentMemory(**doc).model_dump())
            
            return memories
        except Exception as e:
            self.logger.error(f"Failed to retrieve memory: {e}")
            return []


class LLMAgent(BaseAgent):
    """Base class for LLM-powered agents."""
    
    def __init__(self, name: str, description: str = "", capabilities: List[str] = None):
        super().__init__(name, description)
        self.capabilities = capabilities or []
        self.openai_api_key = app_config.openai_api_key
        
        if not self.openai_api_key:
            self.logger.warning("OpenAI API key not configured")
    
    async def get_user_llm_settings(self, user_id) -> Dict[str, Any]:
        """Get LLM settings for a specific user."""
        try:
            from src.database.connection import mongodb
            settings_collection = mongodb.database["user_settings"]
            settings_doc = await settings_collection.find_one({"user_id": user_id})
            
            if settings_doc:
                return {
                    "provider": settings_doc.get("llm_provider", "openai"),
                    "model": settings_doc.get("llm_model", "gpt-3.5-turbo"),
                    "api_key": settings_doc.get("llm_api_key"),
                    "api_base": settings_doc.get("llm_api_base")
                }
            else:
                # Return default settings
                return {
                    "provider": app_config.llm_provider,
                    "model": "gpt-3.5-turbo",
                    "api_key": self.openai_api_key,
                    "api_base": app_config.openai_api_base
                }
        except Exception as e:
            self.logger.error(f"Failed to get user LLM settings: {e}")
            return {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "api_key": self.openai_api_key,
                "api_base": app_config.openai_api_base
            }
    
    async def call_llm(self, prompt: str, system_prompt: str = None, 
                      temperature: float = 0.7, max_tokens: int = 1000,
                      user_id=None) -> str:
        """Make a call to the LLM with provider selection."""
        try:
            # Get user-specific LLM settings
            llm_settings = await self.get_user_llm_settings(user_id) if user_id else {}
            provider = llm_settings.get("provider", "openai")
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            if provider == "openai":
                return await self._call_openai(
                    messages, llm_settings, temperature, max_tokens
                )
            elif provider == "ollama":
                return await self._call_ollama(
                    messages, llm_settings, temperature, max_tokens
                )
            else:
                # Fallback to OpenAI
                return await self._call_openai(
                    messages, llm_settings, temperature, max_tokens
                )
            
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            raise
    
    async def _call_openai(self, messages: List[Dict], settings: Dict, 
                          temperature: float, max_tokens: int) -> str:
        """Call OpenAI API."""
        import openai
        
        api_key = settings.get("api_key") or self.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        client = openai.OpenAI(
            api_key=api_key,
            base_url=settings.get("api_base", app_config.openai_api_base)
        )
        
        response = client.chat.completions.create(
            model=settings.get("model", "gpt-3.5-turbo"),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    async def _call_ollama(self, messages: List[Dict], settings: Dict,
                          temperature: float, max_tokens: int) -> str:
        """Call Ollama API."""
        from src.integrations.api_client import api_manager
        
        response = await api_manager.ollama.chat_completion(
            messages=messages,
            model=settings.get("model", app_config.ollama_model),
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if not response["success"]:
            raise Exception(f"Ollama API error: {response.get('error')}")
        
        return response["content"]


class AgentError(Exception):
    """Custom exception for agent-related errors."""
    pass


class AgentValidationError(AgentError):
    """Exception raised when agent validation fails."""
    pass


class AgentExecutionError(AgentError):
    """Exception raised during agent execution."""
    pass
