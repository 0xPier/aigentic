"""
Unit tests for the Memory Management System.
Tests feedback processing, memory storage/retrieval, and learning loops.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

from src.agents.memory_manager import (
    MemoryManager, FeedbackProcessor, LearningLoop, MemoryType,
    memory_manager, feedback_processor, learning_loop
)
from src.database.models import AgentMemory, Feedback, Task, User


class TestFeedbackProcessor:
    """Test feedback processing functionality."""
    
    def test_feedback_processor_initialization(self):
        """Test feedback processor initialization."""
        processor = FeedbackProcessor()
        
        assert hasattr(processor, 'feedback_categories')
        assert 'quality' in processor.feedback_categories
        assert 'performance' in processor.feedback_categories
        assert 'usability' in processor.feedback_categories
        assert 'content' in processor.feedback_categories
    
    @pytest.mark.asyncio
    async def test_process_feedback_with_openai(self, mock_openai_client):
        """Test feedback processing with OpenAI analysis."""
        processor = FeedbackProcessor()
        
        feedback_data = {
            "task_id": 1,
            "agent_name": "research",
            "rating": 4,
            "comments": "Great research results, very comprehensive and well-structured."
        }
        
        with patch('src.agents.memory_manager.api_manager') as mock_api_manager:
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": True,
                "content": json.dumps({
                    "sentiment": "positive",
                    "improvement_areas": ["speed"],
                    "recommendations": ["Consider caching frequent searches"],
                    "priority": "low",
                    "categories": ["quality", "performance"],
                    "confidence_score": 0.9
                }),
                "usage": {"total_tokens": 150}
            })
            
            result = await processor.process_feedback(feedback_data)
            
            # Verify processing result
            assert "original_feedback" in result
            assert "processed_insights" in result
            assert "processed_at" in result
            assert result["processing_method"] == "openai_analysis"
            
            # Verify insights structure
            insights = result["processed_insights"]
            assert insights["sentiment"] == "positive"
            assert "speed" in insights["improvement_areas"]
            assert insights["priority"] == "low"
            assert insights["confidence_score"] == 0.9
    
    @pytest.mark.asyncio
    async def test_process_feedback_fallback(self):
        """Test feedback processing fallback when OpenAI fails."""
        processor = FeedbackProcessor()
        
        feedback_data = {
            "task_id": 1,
            "agent_name": "research",
            "rating": 2,
            "comments": "Results were not accurate and took too long."
        }
        
        with patch('src.agents.memory_manager.api_manager') as mock_api_manager:
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": False,
                "error": "API Error"
            })
            
            result = await processor.process_feedback(feedback_data)
            
            # Verify fallback processing
            assert result["processing_method"] == "fallback"
            assert "error" in result
            
            # Verify fallback insights
            insights = result["processed_insights"]
            assert insights["sentiment"] == "negative"  # Rating 2 should be negative
            assert insights["priority"] == "high"  # Low rating should be high priority
            assert insights["confidence_score"] == 0.5
    
    def test_create_fallback_insights(self):
        """Test fallback insights creation."""
        processor = FeedbackProcessor()
        
        # Test positive rating
        insights = processor._create_fallback_insights(5, "Excellent work!")
        assert insights["sentiment"] == "positive"
        assert insights["priority"] == "low"
        
        # Test negative rating
        insights = processor._create_fallback_insights(1, "Poor quality")
        assert insights["sentiment"] == "negative"
        assert insights["priority"] == "high"
        
        # Test neutral rating
        insights = processor._create_fallback_insights(3, "Average results")
        assert insights["sentiment"] == "neutral"
        assert insights["priority"] == "medium"


class TestMemoryManager:
    """Test memory management functionality."""
    
    def test_memory_manager_initialization(self):
        """Test memory manager initialization."""
        manager = MemoryManager()
        
        assert hasattr(manager, 'feedback_processor')
        assert isinstance(manager.feedback_processor, FeedbackProcessor)
    
    @pytest.mark.asyncio
    async def test_store_memory(self, db_session):
        """Test memory storage functionality."""
        manager = MemoryManager()
        
        memory_content = {
            "execution_summary": {
                "task_type": "research",
                "execution_time": 15.5,
                "success": True
            }
        }
        
        result = await manager.store_memory(
            agent_name="research",
            memory_type=MemoryType.SUCCESS,
            content=memory_content,
            context_tags=["research", "web_search"],
            relevance_score=0.8,
            db=db_session
        )
        
        assert result is True
        
        # Verify memory was stored in database
        memory = db_session.query(AgentMemory).filter(
            AgentMemory.agent_name == "research"
        ).first()
        
        assert memory is not None
        assert memory.memory_type == MemoryType.SUCCESS
        assert memory.relevance_score == 0.8
        assert "research" in memory.context_tags
    
    @pytest.mark.asyncio
    async def test_retrieve_memories(self, db_session, test_memory):
        """Test memory retrieval functionality."""
        manager = MemoryManager()
        
        memories = await manager.retrieve_memories(
            agent_name="research",
            memory_type="success",
            limit=10,
            min_relevance=0.5,
            db=db_session
        )
        
        assert len(memories) >= 1
        memory = memories[0]
        assert memory["memory_type"] == "success"
        assert memory["relevance_score"] >= 0.5
        assert "id" in memory
        assert "content" in memory
        assert "context_tags" in memory
    
    @pytest.mark.asyncio
    async def test_retrieve_memories_with_context_tags(self, db_session):
        """Test memory retrieval with context tag filtering."""
        manager = MemoryManager()
        
        # Store memories with different tags
        await manager.store_memory(
            agent_name="test_agent",
            memory_type=MemoryType.SUCCESS,
            content={"test": "data1"},
            context_tags=["research", "web_search"],
            relevance_score=0.9,
            db=db_session
        )
        
        await manager.store_memory(
            agent_name="test_agent",
            memory_type=MemoryType.SUCCESS,
            content={"test": "data2"},
            context_tags=["content", "generation"],
            relevance_score=0.8,
            db=db_session
        )
        
        # Retrieve with specific context tags
        memories = await manager.retrieve_memories(
            agent_name="test_agent",
            context_tags=["research"],
            db=db_session
        )
        
        # Should only return memories with research tag
        assert len(memories) >= 1
        for memory in memories:
            assert "research" in memory["context_tags"]
    
    @pytest.mark.asyncio
    async def test_process_task_feedback(self, db_session, test_user, test_task, test_feedback):
        """Test task feedback processing."""
        manager = MemoryManager()
        
        with patch.object(manager.feedback_processor, 'process_feedback') as mock_process, \
             patch.object(manager, '_generate_learning_insights') as mock_insights:
            
            # Mock feedback processing
            mock_process.return_value = {
                "original_feedback": {"rating": 4},
                "processed_insights": {
                    "sentiment": "positive",
                    "priority": "low",
                    "confidence_score": 0.8
                },
                "processing_method": "openai_analysis"
            }
            
            # Mock learning insights
            mock_insights.return_value = {
                "insights": "Agent performance is improving",
                "confidence": "high"
            }
            
            result = await manager.process_task_feedback(test_task.id, db_session)
            
            # Verify processing result
            assert "task_id" in result
            assert "agent_name" in result
            assert "processed_feedback_count" in result
            assert "learning_insights" in result
            assert result["status"] == "completed"
            
            # Verify methods were called
            mock_process.assert_called()
            mock_insights.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_learning_insights(self, db_session):
        """Test learning insights generation."""
        manager = MemoryManager()
        
        processed_feedback = [
            {
                "processed_insights": {
                    "sentiment": "positive",
                    "improvement_areas": ["speed"],
                    "priority": "medium"
                }
            }
        ]
        
        with patch('src.agents.memory_manager.api_manager') as mock_api_manager:
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": True,
                "content": "Agent shows consistent performance with room for speed improvements...",
                "usage": {"total_tokens": 200}
            })
            
            insights = await manager._generate_learning_insights(
                "test_agent", processed_feedback, db_session
            )
            
            # Verify insights structure
            assert "insights" in insights
            assert "feedback_count" in insights
            assert "generated_at" in insights
            assert "confidence" in insights
            assert insights["feedback_count"] == 1
    
    def test_calculate_feedback_relevance(self):
        """Test feedback relevance calculation."""
        manager = MemoryManager()
        
        # Test high priority negative feedback
        processed_feedback = {
            "processed_insights": {
                "confidence_score": 0.9,
                "priority": "high",
                "sentiment": "negative"
            }
        }
        
        relevance = manager._calculate_feedback_relevance(processed_feedback)
        assert relevance > 0.8  # Should be high due to negative sentiment boost
        
        # Test low priority positive feedback
        processed_feedback = {
            "processed_insights": {
                "confidence_score": 0.6,
                "priority": "low",
                "sentiment": "positive"
            }
        }
        
        relevance = manager._calculate_feedback_relevance(processed_feedback)
        assert relevance < 0.5  # Should be lower


class TestLearningLoop:
    """Test learning loop functionality."""
    
    def test_learning_loop_initialization(self):
        """Test learning loop initialization."""
        loop = LearningLoop()
        
        assert hasattr(loop, 'memory_manager')
        assert isinstance(loop.memory_manager, MemoryManager)
    
    @pytest.mark.asyncio
    async def test_run_learning_cycle_single_agent(self, db_session, test_user, test_task):
        """Test learning cycle for a single agent."""
        loop = LearningLoop()
        
        with patch.object(loop, '_process_agent_learning') as mock_process:
            mock_process.return_value = {
                "agent_name": "research",
                "tasks_reviewed": 1,
                "feedback_processed": 1,
                "insights_generated": True,
                "processed_at": datetime.now().isoformat()
            }
            
            result = await loop.run_learning_cycle("research", db_session)
            
            # Verify cycle result
            assert "cycle_started_at" in result
            assert "cycle_completed_at" in result
            assert "agents_processed" in result
            assert "total_feedback_processed" in result
            assert "insights_generated" in result
            assert result["success"] is True
            
            # Verify agent was processed
            assert len(result["agents_processed"]) == 1
            assert result["agents_processed"][0]["agent_name"] == "research"
    
    @pytest.mark.asyncio
    async def test_run_learning_cycle_all_agents(self, db_session, test_user):
        """Test learning cycle for all agents."""
        loop = LearningLoop()
        
        # Create tasks for different agents
        task1 = Task(
            user_id=test_user.id,
            agent_name="research",
            task_type="research",
            query="Test query 1",
            status="completed",
            created_at=datetime.now()
        )
        task2 = Task(
            user_id=test_user.id,
            agent_name="content",
            task_type="content",
            query="Test query 2",
            status="completed",
            created_at=datetime.now()
        )
        
        db_session.add_all([task1, task2])
        db_session.commit()
        
        with patch.object(loop, '_process_agent_learning') as mock_process:
            mock_process.side_effect = [
                {
                    "agent_name": "research",
                    "tasks_reviewed": 1,
                    "feedback_processed": 0,
                    "insights_generated": False
                },
                {
                    "agent_name": "content",
                    "tasks_reviewed": 1,
                    "feedback_processed": 0,
                    "insights_generated": False
                }
            ]
            
            result = await loop.run_learning_cycle(None, db_session)
            
            # Verify all agents were processed
            assert len(result["agents_processed"]) == 2
            agent_names = [agent["agent_name"] for agent in result["agents_processed"]]
            assert "research" in agent_names
            assert "content" in agent_names
    
    @pytest.mark.asyncio
    async def test_process_agent_learning(self, db_session, test_user, test_task, test_feedback):
        """Test agent-specific learning processing."""
        loop = LearningLoop()
        
        with patch.object(loop.memory_manager, 'process_task_feedback') as mock_process:
            mock_process.return_value = {
                "learning_insights": {"insights": "Test insights"},
                "status": "completed"
            }
            
            result = await loop._process_agent_learning(test_task.agent_name, db_session)
            
            # Verify processing result
            assert "agent_name" in result
            assert "tasks_reviewed" in result
            assert "feedback_processed" in result
            assert "insights_generated" in result
            assert "processed_at" in result
            
            assert result["agent_name"] == test_task.agent_name
            assert result["tasks_reviewed"] >= 1
    
    @pytest.mark.asyncio
    async def test_learning_cycle_error_handling(self, db_session):
        """Test learning cycle error handling."""
        loop = LearningLoop()
        
        with patch.object(loop, '_process_agent_learning') as mock_process:
            # Simulate error in agent processing
            mock_process.side_effect = Exception("Processing error")
            
            result = await loop.run_learning_cycle("error_agent", db_session)
            
            # Should handle error gracefully
            assert "errors" in result
            assert len(result["errors"]) > 0
            assert result["success"] is False
            assert "Processing error" in result["errors"][0]


class TestMemoryIntegration:
    """Test memory system integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_feedback_processing(self, db_session, test_user, test_task):
        """Test complete end-to-end feedback processing flow."""
        # Create feedback
        feedback = Feedback(
            user_id=test_user.id,
            task_id=test_task.id,
            rating=4,
            comments="Excellent research with comprehensive results",
            feedback_type="quality"
        )
        db_session.add(feedback)
        db_session.commit()
        
        with patch('src.agents.memory_manager.api_manager') as mock_api_manager:
            # Mock OpenAI responses for feedback processing and insights
            mock_api_manager.openai.chat_completion = AsyncMock(side_effect=[
                {
                    "success": True,
                    "content": json.dumps({
                        "sentiment": "positive",
                        "improvement_areas": [],
                        "recommendations": ["Continue current approach"],
                        "priority": "low",
                        "categories": ["quality"],
                        "confidence_score": 0.9
                    }),
                    "usage": {"total_tokens": 150}
                },
                {
                    "success": True,
                    "content": "Agent demonstrates consistent high-quality performance...",
                    "usage": {"total_tokens": 200}
                }
            ])
            
            # Process feedback
            result = await memory_manager.process_task_feedback(test_task.id, db_session)
            
            # Verify complete processing
            assert result["status"] == "completed"
            assert result["processed_feedback_count"] > 0
            assert "learning_insights" in result
            
            # Verify memory was stored
            memories = db_session.query(AgentMemory).filter(
                AgentMemory.agent_name == test_task.agent_name,
                AgentMemory.memory_type == MemoryType.FEEDBACK
            ).all()
            
            assert len(memories) > 0
            memory = memories[0]
            assert "processed_insights" in memory.content
    
    @pytest.mark.asyncio
    async def test_memory_retrieval_performance(self, db_session):
        """Test memory retrieval performance with large datasets."""
        manager = MemoryManager()
        
        # Store multiple memories
        for i in range(20):
            await manager.store_memory(
                agent_name="performance_test",
                memory_type=MemoryType.SUCCESS if i % 2 == 0 else MemoryType.ERROR,
                content={"test_data": f"data_{i}"},
                context_tags=[f"tag_{i % 5}", "performance_test"],
                relevance_score=0.5 + (i % 5) * 0.1,
                db=db_session
            )
        
        # Test retrieval with various filters
        start_time = datetime.now()
        
        memories = await manager.retrieve_memories(
            agent_name="performance_test",
            memory_type=MemoryType.SUCCESS,
            limit=10,
            min_relevance=0.7,
            db=db_session
        )
        
        end_time = datetime.now()
        retrieval_time = (end_time - start_time).total_seconds()
        
        # Verify performance and results
        assert retrieval_time < 1.0  # Should be fast
        assert len(memories) <= 10  # Respects limit
        
        for memory in memories:
            assert memory["memory_type"] == MemoryType.SUCCESS
            assert memory["relevance_score"] >= 0.7
    
    @pytest.mark.asyncio
    async def test_memory_cleanup_simulation(self, db_session):
        """Test memory cleanup functionality simulation."""
        manager = MemoryManager()
        
        # Store old memories with low relevance
        old_date = datetime.now() - timedelta(days=100)
        
        for i in range(5):
            memory = AgentMemory(
                agent_name="cleanup_test",
                memory_type=MemoryType.SUCCESS,
                content={"old_data": f"data_{i}"},
                context_tags=["old", "cleanup_test"],
                relevance_score=0.2,  # Low relevance
                created_at=old_date
            )
            db_session.add(memory)
        
        # Store recent memories with high relevance
        for i in range(3):
            memory = AgentMemory(
                agent_name="cleanup_test",
                memory_type=MemoryType.SUCCESS,
                content={"new_data": f"data_{i}"},
                context_tags=["new", "cleanup_test"],
                relevance_score=0.8,  # High relevance
                created_at=datetime.now()
            )
            db_session.add(memory)
        
        db_session.commit()
        
        # Verify all memories exist
        all_memories = db_session.query(AgentMemory).filter(
            AgentMemory.agent_name == "cleanup_test"
        ).all()
        assert len(all_memories) == 8
        
        # Simulate cleanup (would normally be done by Celery task)
        cutoff_date = datetime.now() - timedelta(days=90)
        old_low_relevance = db_session.query(AgentMemory).filter(
            AgentMemory.agent_name == "cleanup_test",
            AgentMemory.created_at < cutoff_date,
            AgentMemory.relevance_score < 0.3
        )
        
        count_to_delete = old_low_relevance.count()
        assert count_to_delete == 5  # Should identify old, low-relevance memories
        
        # Verify recent high-relevance memories would be preserved
        recent_memories = db_session.query(AgentMemory).filter(
            AgentMemory.agent_name == "cleanup_test",
            AgentMemory.created_at >= cutoff_date
        ).all()
        assert len(recent_memories) == 3
