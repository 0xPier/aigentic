"""
Agent Memory Management System for continuous learning and improvement.
Handles feedback collection, memory storage, and learning loop implementation.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import logging

from src.database.models import AgentMemory, Feedback, Task, User
from src.database.connection import mongodb
from src.integrations.api_client import api_manager

logger = logging.getLogger(__name__)


class MemoryType:
    """Memory type constants."""
    PERFORMANCE = "performance"
    FEEDBACK = "feedback"
    PATTERN = "pattern"
    OPTIMIZATION = "optimization"
    ERROR = "error"
    SUCCESS = "success"


class FeedbackProcessor:
    """Processes user feedback and converts it to actionable insights."""
    
    def __init__(self):
        self.feedback_categories = {
            "quality": ["accuracy", "relevance", "completeness"],
            "performance": ["speed", "efficiency", "reliability"],
            "usability": ["ease_of_use", "clarity", "helpfulness"],
            "content": ["creativity", "originality", "engagement"]
        }
    
    async def process_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw feedback into structured insights."""
        try:
            # Extract feedback components
            rating = feedback_data.get("rating", 0)
            comments = feedback_data.get("comments", "")
            task_id = feedback_data.get("task_id")
            agent_name = feedback_data.get("agent_name", "")
            
            # Use OpenAI to analyze feedback sentiment and extract insights
            analysis_prompt = f"""
            Analyze this user feedback for an AI agent and extract actionable insights:
            
            Agent: {agent_name}
            Rating: {rating}/5
            Comments: {comments}
            
            Please provide:
            1. Sentiment analysis (positive/negative/neutral)
            2. Key improvement areas
            3. Specific actionable recommendations
            4. Priority level (high/medium/low)
            5. Category classification (quality/performance/usability/content)
            
            Format as JSON:
            {{
                "sentiment": "positive/negative/neutral",
                "improvement_areas": ["area1", "area2"],
                "recommendations": ["rec1", "rec2"],
                "priority": "high/medium/low",
                "categories": ["category1", "category2"],
                "confidence_score": 0.8
            }}
            """
            
            analysis_response = await api_manager.openai.chat_completion([
                {
                    "role": "system",
                    "content": "You are an expert at analyzing user feedback and extracting actionable insights for AI system improvement."
                },
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ], model="gpt-4", max_tokens=1000, temperature=0.3)
            
            if analysis_response["success"]:
                try:
                    insights = json.loads(analysis_response["content"])
                except json.JSONDecodeError:
                    logger.warning("Failed to parse feedback analysis JSON")
                    insights = self._create_fallback_insights(rating, comments)
            else:
                logger.error(f"Feedback analysis failed: {analysis_response.get('error')}")
                insights = self._create_fallback_insights(rating, comments)
            
            return {
                "original_feedback": feedback_data,
                "processed_insights": insights,
                "processed_at": datetime.now().isoformat(),
                "processing_method": "openai_analysis"
            }
            
        except Exception as e:
            logger.error(f"Feedback processing error: {str(e)}")
            return {
                "original_feedback": feedback_data,
                "processed_insights": self._create_fallback_insights(
                    feedback_data.get("rating", 0), 
                    feedback_data.get("comments", "")
                ),
                "processed_at": datetime.now().isoformat(),
                "processing_method": "fallback",
                "error": str(e)
            }
    
    def _create_fallback_insights(self, rating: int, comments: str) -> Dict[str, Any]:
        """Create basic insights when AI analysis fails."""
        sentiment = "positive" if rating >= 4 else "negative" if rating <= 2 else "neutral"
        priority = "high" if rating <= 2 else "medium" if rating == 3 else "low"
        
        return {
            "sentiment": sentiment,
            "improvement_areas": ["general_improvement"] if rating < 4 else [],
            "recommendations": ["Review and improve based on user comments"],
            "priority": priority,
            "categories": ["quality"],
            "confidence_score": 0.5
        }


class MemoryManager:
    """Manages agent memory storage, retrieval, and learning patterns."""
    
    def __init__(self):
        self.feedback_processor = FeedbackProcessor()
    
    async def store_memory(
        self, 
        agent_name: str, 
        memory_type: str, 
        content: Dict[str, Any],
        context_tags: List[str] = None,
        relevance_score: float = 1.0,
    ) -> bool:
        """Store a memory entry for an agent."""
        try:
            memory_entry = AgentMemory(
                agent_name=agent_name,
                memory_type=memory_type,
                content=content,
                context_tags=context_tags or [],
                relevance_score=relevance_score,
                created_at=datetime.utcnow()
            )
            
            await mongodb.database["agent_memory"].insert_one(memory_entry.model_dump(by_alias=True, exclude_none=True))
            
            logger.info(f"Memory stored for agent {agent_name}: {memory_type}")
            return True
            
        except Exception as e:
            logger.error(f"Memory storage error: {str(e)}")
            return False
    
    async def retrieve_memories(
        self,
        agent_name: str,
        memory_type: str = None,
        context_tags: List[str] = None,
        limit: int = 10,
        min_relevance: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for an agent."""
        try:
            query_filter = {
                "agent_name": agent_name,
                "relevance_score": {"$gte": min_relevance}
            }
            
            if memory_type:
                query_filter["memory_type"] = memory_type
            
            if context_tags:
                query_filter["context_tags"] = {"$all": context_tags}
            
            memories_cursor = mongodb.database["agent_memory"].find(query_filter).sort(
                [('relevance_score', -1), ('created_at', -1)]
            ).limit(limit)
            
            memories = []
            async for doc in memories_cursor:
                memories.append({
                    "id": str(doc["_id"]),
                    "memory_type": doc["memory_type"],
                    "content": doc["content"],
                    "context_tags": doc["context_tags"],
                    "relevance_score": doc["relevance_score"],
                    "created_at": doc["created_at"].isoformat()
                })
            
            return memories
            
        except Exception as e:
            logger.error(f"Memory retrieval error: {str(e)}")
            return []
    
    async def process_task_feedback(self, task_id: str) -> Dict[str, Any]:
        """Process feedback for a completed task and update agent memory."""
        try:
            # Get task and associated feedback
            task = await mongodb.database["tasks"].find_one({"_id": task_id})
            if not task:
                return {"error": "Task not found"}
            task = Task(**task)
            
            feedback_entries_cursor = mongodb.database["feedback"].find({"task_id": task_id})
            feedback_entries = [Feedback(**doc) async for doc in feedback_entries_cursor]
            
            if not feedback_entries:
                logger.info(f"No feedback found for task {task_id}")
                return {"message": "No feedback to process"}
            
            processed_feedback = []
            
            for feedback in feedback_entries:
                # Process each feedback entry
                feedback_data = {
                    "task_id": str(task_id),
                    "agent_name": task.assigned_agent,
                    "rating": feedback.rating,
                    "comments": feedback.comments,
                    "feedback_type": feedback.feedback_type,
                    "created_at": feedback.created_at.isoformat()
                }
                
                processed = await self.feedback_processor.process_feedback(feedback_data)
                processed_feedback.append(processed)
                
                # Store processed feedback as memory
                await self.store_memory(
                    agent_name=task.assigned_agent,
                    memory_type=MemoryType.FEEDBACK,
                    content=processed,
                    context_tags=["feedback", "user_input", task.assigned_agent],
                    relevance_score=self._calculate_feedback_relevance(processed),
                )
            
            # Generate learning insights
            learning_insights = await self._generate_learning_insights(
                task.assigned_agent, processed_feedback
            )
            
            # Store learning insights
            if learning_insights:
                await self.store_memory(
                    agent_name=task.assigned_agent,
                    memory_type=MemoryType.PATTERN,
                    content=learning_insights,
                    context_tags=["learning", "insights", "improvement"],
                    relevance_score=0.9,
                )
            
            return {
                "task_id": str(task_id),
                "agent_name": task.assigned_agent,
                "processed_feedback_count": len(processed_feedback),
                "learning_insights": learning_insights,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Task feedback processing error: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_learning_insights(
        self, 
        agent_name: str, 
        processed_feedback: List[Dict[str, Any]], 
    ) -> Dict[str, Any]:
        """Generate learning insights from processed feedback."""
        try:
            # Get historical feedback for pattern analysis
            historical_memories = await self.retrieve_memories(
                agent_name=agent_name,
                memory_type=MemoryType.FEEDBACK,
                limit=50,
            )
            
            # Prepare data for analysis
            feedback_summary = {
                "recent_feedback": processed_feedback,
                "historical_patterns": historical_memories,
                "agent_name": agent_name
            }
            
            # Use OpenAI to generate insights
            insights_prompt = f"""
            Analyze feedback patterns for AI agent '{agent_name}' and generate learning insights:
            
            Recent Feedback: {json.dumps([f['processed_insights'] for f in processed_feedback], indent=2)}
            
            Historical Pattern Count: {len(historical_memories)}
            
            Please provide:
            1. Key performance trends
            2. Recurring improvement areas
            3. Specific optimization recommendations
            4. Success patterns to reinforce
            5. Priority actions for improvement
            
            Format as actionable insights for agent improvement.
            """
            
            insights_response = await api_manager.openai.chat_completion([
                {
                    "role": "system",
                    "content": "You are an AI system analyst specializing in agent performance optimization and continuous learning."
                },
                {
                    "role": "user",
                    "content": insights_prompt
                }
            ], model="gpt-4", max_tokens=2000, temperature=0.3)
            
            if insights_response["success"]:
                return {
                    "insights": insights_response["content"],
                    "feedback_count": len(processed_feedback),
                    "historical_count": len(historical_memories),
                    "generated_at": datetime.utcnow().isoformat(),
                    "confidence": "high" if len(processed_feedback) >= 3 else "medium"
                }
            else:
                logger.error(f"Learning insights generation failed: {insights_response.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Learning insights generation error: {str(e)}")
            return None
    
    def _calculate_feedback_relevance(self, processed_feedback: Dict[str, Any]) -> float:
        """Calculate relevance score for feedback memory."""
        try:
            insights = processed_feedback.get("processed_insights", {})
            
            # Base relevance on confidence and priority
            confidence = insights.get("confidence_score", 0.5)
            priority_weights = {"high": 1.0, "medium": 0.7, "low": 0.4}
            priority_weight = priority_weights.get(insights.get("priority", "medium"), 0.7)
            
            # Boost relevance for negative feedback (more important to learn from)
            sentiment_boost = 0.2 if insights.get("sentiment") == "negative" else 0.0
            
            relevance = min(1.0, confidence * priority_weight + sentiment_boost)
            return relevance
            
        except Exception as e:
            logger.error(f"Relevance calculation error: {str(e)}")
            return 0.5


class LearningLoop:
    """Implements continuous learning loop for agents."""
    
    def __init__(self):
        self.memory_manager = MemoryManager()
    
    async def run_learning_cycle(self, agent_name: str = None) -> Dict[str, Any]:
        """Run a complete learning cycle for agents."""
        try:
            results = {
                "cycle_started_at": datetime.utcnow().isoformat(),
                "agents_processed": [],
                "total_feedback_processed": 0,
                "insights_generated": 0,
                "errors": []
            }
            
            # Get agents to process
            if agent_name:
                agents_to_process = [agent_name]
            else:
                # Get all agents with recent tasks
                recent_tasks_cursor = mongodb.database["tasks"].aggregate([
                    {"$match": {"created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}}},
                    {"$group": {"_id": "$assigned_agent"}}
                ])
                agents_to_process = [doc["_id"] for doc in await recent_tasks_cursor.to_list(length=None) if doc["_id"] is not None]
            
            for agent in agents_to_process:
                try:
                    agent_result = await self._process_agent_learning(agent)
                    results["agents_processed"].append(agent_result)
                    results["total_feedback_processed"] += agent_result.get("feedback_processed", 0)
                    if agent_result.get("insights_generated"):
                        results["insights_generated"] += 1
                        
                except Exception as e:
                    error_msg = f"Error processing agent {agent}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            results["cycle_completed_at"] = datetime.utcnow().isoformat()
            results["success"] = len(results["errors"]) == 0
            
            return results
            
        except Exception as e:
            logger.error(f"Learning cycle error: {str(e)}")
            return {
                "error": str(e),
                "cycle_started_at": datetime.utcnow().isoformat(),
                "success": False
            }
    
    async def _process_agent_learning(self, agent_name: str) -> Dict[str, Any]:
        """Process learning for a specific agent."""
        try:
            # Get recent tasks with feedback for this agent
            recent_tasks_cursor = mongodb.database["tasks"].find({
                "assigned_agent": agent_name,
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)},
                "status": "completed"
            })
            recent_tasks = [Task(**doc) async for doc in recent_tasks_cursor]
            
            feedback_processed = 0
            insights_generated = False
            
            for task in recent_tasks:
                # Check if task has unprocessed feedback
                feedback_count = await mongodb.database["feedback"].count_documents({"task_id": task.id})
                memory_count = await mongodb.database["agent_memory"].count_documents({
                    "agent_name": agent_name,
                    "memory_type": MemoryType.FEEDBACK,
                    "content.original_feedback.task_id": str(task.id)
                })
                
                if feedback_count > memory_count:
                    # Process unprocessed feedback
                    result = await self.memory_manager.process_task_feedback(task.id)
                    if not result.get("error"):
                        feedback_processed += feedback_count - memory_count
                        if result.get("learning_insights"):
                            insights_generated = True
            
            return {
                "agent_name": agent_name,
                "tasks_reviewed": len(recent_tasks),
                "feedback_processed": feedback_processed,
                "insights_generated": insights_generated,
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent learning processing error for {agent_name}: {str(e)}")
            return {
                "agent_name": agent_name,
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            }


# Global instances
memory_manager = MemoryManager()
learning_loop = LearningLoop()
feedback_processor = FeedbackProcessor()
