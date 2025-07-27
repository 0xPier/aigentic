"""
Unit tests for the base agent functionality.
Tests memory integration, performance tracking, and core agent behavior.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.agents.base import BaseAgent, LLMAgent, AgentContext, AgentResult
from src.agents.memory_manager import MemoryType
from src.database.models import AgentMemory


class TestBaseAgent(BaseAgent):
    """Test implementation of BaseAgent for testing."""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Simple test execution."""
        await asyncio.sleep(0.1)  # Simulate work
        return AgentResult(
            success=True,
            data={"test": "result"},
            summary="Test execution completed",
            agent_name=self.name,
            execution_time=0.1
        )


class TestFailingAgent(BaseAgent):
    """Test agent that always fails for error testing."""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Always fails for testing error handling."""
        raise Exception("Test error")


class TestBaseAgentCore:
    """Test core BaseAgent functionality."""
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = TestBaseAgent("test_agent", "Test agent description")
        
        assert agent.name == "test_agent"
        assert agent.description == "Test agent description"
        assert agent.memory_enabled is True
        assert agent.learning_context == []
        assert agent.performance_metrics["total_executions"] == 0
        assert agent.performance_metrics["successful_executions"] == 0
        assert agent.performance_metrics["average_execution_time"] == 0
    
    def test_performance_metrics_update(self):
        """Test performance metrics updating."""
        agent = TestBaseAgent("test_agent")
        
        # Test first execution time update
        agent.performance_metrics["total_executions"] = 1
        agent._update_average_execution_time(10.0)
        assert agent.performance_metrics["average_execution_time"] == 10.0
        
        # Test second execution time update
        agent.performance_metrics["total_executions"] = 2
        agent._update_average_execution_time(20.0)
        assert agent.performance_metrics["average_execution_time"] == 15.0
        
        # Test third execution time update
        agent.performance_metrics["total_executions"] = 3
        agent._update_average_execution_time(30.0)
        assert agent.performance_metrics["average_execution_time"] == 20.0
    
    def test_context_tag_extraction(self, mock_agent_context):
        """Test context tag extraction."""
        agent = TestBaseAgent("test_agent")
        
        tags = agent._extract_context_tags(mock_agent_context)
        
        assert "test_agent" in tags
        assert "research" in tags  # task_type
        assert len(tags) >= 2
    
    def test_execution_relevance_calculation(self, mock_agent_result):
        """Test execution relevance score calculation."""
        agent = TestBaseAgent("test_agent")
        agent.performance_metrics["average_execution_time"] = 15.0
        
        # Test fast execution (should boost relevance)
        relevance = agent._calculate_execution_relevance(10.0, mock_agent_result)
        assert relevance > 0.7
        
        # Test slow execution
        relevance = agent._calculate_execution_relevance(20.0, mock_agent_result)
        assert relevance >= 0.7
        
        # Test with substantial data
        mock_agent_result.data = {"large_data": "x" * 2000}
        relevance = agent._calculate_execution_relevance(10.0, mock_agent_result)
        assert relevance > 0.8


class TestBaseAgentExecution:
    """Test agent execution with context and memory integration."""
    
    @pytest.mark.asyncio
    async def test_successful_execution(self, mock_agent_context, db_session):
        """Test successful agent execution."""
        agent = TestBaseAgent("test_agent")
        
        with patch.object(agent, '_load_relevant_memories') as mock_load, \
             patch.object(agent, '_store_execution_memory') as mock_store:
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Verify result
            assert result.success is True
            assert result.data == {"test": "result"}
            assert result.summary == "Test execution completed"
            assert result.execution_time > 0
            
            # Verify performance metrics updated
            assert agent.performance_metrics["total_executions"] == 1
            assert agent.performance_metrics["successful_executions"] == 1
            assert agent.performance_metrics["average_execution_time"] > 0
            
            # Verify memory operations called
            mock_load.assert_called_once()
            mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_failed_execution(self, mock_agent_context, db_session):
        """Test failed agent execution."""
        agent = TestFailingAgent("failing_agent")
        
        with patch.object(agent, '_load_relevant_memories') as mock_load, \
             patch.object(agent, '_store_error_memory') as mock_store_error:
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Verify error result
            assert result.success is False
            assert "Test error" in result.data["error"]
            assert result.execution_time > 0
            
            # Verify performance metrics updated
            assert agent.performance_metrics["total_executions"] == 1
            assert agent.performance_metrics["successful_executions"] == 0
            
            # Verify memory operations called
            mock_load.assert_called_once()
            mock_store_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_memory_loading(self, mock_agent_context, db_session):
        """Test memory loading before execution."""
        agent = TestBaseAgent("test_agent")
        
        # Mock memory manager
        with patch('src.agents.base.memory_manager') as mock_memory_manager:
            mock_memory_manager.retrieve_memories = AsyncMock(return_value=[
                {
                    "id": 1,
                    "memory_type": "success",
                    "content": {"test": "memory"},
                    "context_tags": ["test"],
                    "relevance_score": 0.8
                }
            ])
            
            await agent._load_relevant_memories(mock_agent_context)
            
            # Verify memories loaded
            assert len(agent.learning_context) == 1
            assert agent.learning_context[0]["content"]["test"] == "memory"
            
            # Verify memory manager called correctly
            mock_memory_manager.retrieve_memories.assert_called_once_with(
                agent_name="test_agent",
                context_tags=agent._extract_context_tags(mock_agent_context),
                limit=5,
                min_relevance=0.6
            )
    
    @pytest.mark.asyncio
    async def test_execution_memory_storage(self, mock_agent_context, mock_agent_result, db_session):
        """Test execution memory storage."""
        agent = TestBaseAgent("test_agent")
        
        with patch('src.agents.base.memory_manager') as mock_memory_manager:
            mock_memory_manager.store_memory = AsyncMock(return_value=True)
            
            await agent._store_execution_memory(mock_agent_context, mock_agent_result, 10.5)
            
            # Verify memory storage called
            mock_memory_manager.store_memory.assert_called_once()
            call_args = mock_memory_manager.store_memory.call_args
            
            assert call_args[1]["agent_name"] == "test_agent"
            assert call_args[1]["memory_type"] == MemoryType.SUCCESS
            assert "execution_summary" in call_args[1]["content"]
            assert call_args[1]["relevance_score"] > 0
    
    @pytest.mark.asyncio
    async def test_error_memory_storage(self, mock_agent_context, db_session):
        """Test error memory storage."""
        agent = TestBaseAgent("test_agent")
        error_message = "Test error occurred"
        
        with patch('src.agents.base.memory_manager') as mock_memory_manager:
            mock_memory_manager.store_memory = AsyncMock(return_value=True)
            
            await agent._store_error_memory(mock_agent_context, error_message, 5.0)
            
            # Verify error memory storage called
            mock_memory_manager.store_memory.assert_called_once()
            call_args = mock_memory_manager.store_memory.call_args
            
            assert call_args[1]["agent_name"] == "test_agent"
            assert call_args[1]["memory_type"] == MemoryType.ERROR
            assert "error_details" in call_args[1]["content"]
            assert call_args[1]["content"]["error_details"]["error_message"] == error_message
            assert call_args[1]["relevance_score"] == 0.8


class TestBaseAgentLearning:
    """Test agent learning and insights functionality."""
    
    @pytest.mark.asyncio
    async def test_learning_insights_generation(self, db_session):
        """Test learning insights generation."""
        agent = TestBaseAgent("test_agent")
        
        mock_memories = [
            {
                "id": 1,
                "memory_type": "success",
                "content": {
                    "execution_summary": {
                        "execution_time": 10.0,
                        "success": True
                    }
                },
                "context_tags": ["research", "web_search"]
            },
            {
                "id": 2,
                "memory_type": "error",
                "content": {
                    "execution_summary": {
                        "execution_time": 15.0,
                        "success": False
                    }
                },
                "context_tags": ["research", "api_error"]
            }
        ]
        
        with patch('src.agents.base.memory_manager') as mock_memory_manager:
            mock_memory_manager.retrieve_memories = AsyncMock(return_value=mock_memories)
            
            insights = await agent.get_learning_insights()
            
            # Verify insights structure
            assert insights["agent_name"] == "test_agent"
            assert insights["total_memories"] == 2
            assert "memory_types" in insights
            assert "performance_trends" in insights
            assert "common_patterns" in insights
            assert "improvement_suggestions" in insights
            
            # Verify memory type analysis
            assert insights["memory_types"]["success"] == 1
            assert insights["memory_types"]["error"] == 1
            
            # Verify improvement suggestions for errors
            assert len(insights["improvement_suggestions"]) > 0
    
    def test_performance_trends_analysis(self):
        """Test performance trends analysis from memories."""
        agent = TestBaseAgent("test_agent")
        
        memories = [
            {
                "memory_type": "success",
                "content": {
                    "execution_summary": {
                        "execution_time": 10.0,
                        "success": True
                    }
                }
            },
            {
                "memory_type": "success",
                "content": {
                    "execution_summary": {
                        "execution_time": 20.0,
                        "success": True
                    }
                }
            },
            {
                "memory_type": "error",
                "content": {
                    "execution_summary": {
                        "execution_time": 5.0,
                        "success": False
                    }
                }
            }
        ]
        
        trends = agent._analyze_performance_trends(memories)
        
        assert trends["avg_execution_time"] == 11.67  # (10+20+5)/3, rounded
        assert trends["success_rate"] == 2/3  # 2 successes out of 3 total
        assert trends["total_executions_analyzed"] == 3
    
    def test_common_patterns_identification(self):
        """Test common patterns identification from memories."""
        agent = TestBaseAgent("test_agent")
        
        memories = [
            {"context_tags": ["research", "web_search", "success"]},
            {"context_tags": ["research", "api_call", "success"]},
            {"context_tags": ["research", "web_search", "error"]},
            {"context_tags": ["content", "generation"]}
        ]
        
        patterns = agent._identify_common_patterns(memories)
        
        # Should identify "research" as most common pattern
        research_pattern = next((p for p in patterns if "research" in p), None)
        assert research_pattern is not None
        assert "3 occurrences" in research_pattern


class TestLLMAgent:
    """Test LLM-specific agent functionality."""
    
    def test_llm_agent_initialization(self):
        """Test LLM agent initialization."""
        agent = LLMAgent("llm_test", "LLM test agent")
        
        assert agent.name == "llm_test"
        assert agent.description == "LLM test agent"
        assert hasattr(agent, 'openai_api_key')
    
    @pytest.mark.asyncio
    async def test_llm_call(self, mock_openai_client):
        """Test LLM API call functionality."""
        agent = LLMAgent("llm_test", "LLM test agent")
        
        # Mock the API manager
        with patch('src.agents.base.api_manager') as mock_api_manager:
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": True,
                "content": "Mock LLM response",
                "usage": {"total_tokens": 50}
            })
            
            response = await agent.call_llm(
                prompt="Test prompt",
                system_prompt="Test system prompt",
                temperature=0.7
            )
            
            assert response == "Mock LLM response"
            mock_api_manager.openai.chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_llm_call_failure(self):
        """Test LLM API call failure handling."""
        agent = LLMAgent("llm_test", "LLM test agent")
        
        with patch('src.agents.base.api_manager') as mock_api_manager:
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": False,
                "error": "API error"
            })
            
            response = await agent.call_llm("Test prompt")
            
            # Should return empty string on failure
            assert response == ""


class TestAgentPerformance:
    """Test agent performance and timing."""
    
    @pytest.mark.asyncio
    async def test_execution_timing(self, mock_agent_context, performance_timer):
        """Test that execution timing is accurate."""
        agent = TestBaseAgent("test_agent")
        
        performance_timer.start()
        result = await agent.execute_with_context(mock_agent_context)
        performance_timer.stop()
        
        # Execution time should be close to actual elapsed time
        assert abs(result.execution_time - performance_timer.elapsed_seconds) < 0.1
        assert result.execution_time > 0
    
    @pytest.mark.asyncio
    async def test_memory_disabled_execution(self, mock_agent_context):
        """Test execution with memory disabled."""
        agent = TestBaseAgent("test_agent")
        agent.memory_enabled = False
        
        with patch.object(agent, '_load_relevant_memories') as mock_load, \
             patch.object(agent, '_store_execution_memory') as mock_store:
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Memory operations should not be called
            mock_load.assert_not_called()
            mock_store.assert_not_called()
            
            # But execution should still succeed
            assert result.success is True
