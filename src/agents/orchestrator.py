"""Orchestrator Agent for task decomposition and delegation."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from src.agents.base import BaseAgent, AgentContext, AgentResult, LLMAgent
from src.agents.registry import AgentRegistry
from src.agents.baby_agi import baby_agi
from src.agents.tools.file import get_file_tools
from src.agents.tools.process import get_process_tools
from src.agents.tools.search import get_search_tools
from src.core.config import settings
from src.database.connection import get_db
from src.database.models import Task, Agent, Step
from src.services.task_service import TaskService


class OrchestratorAgent(LLMAgent):
    """
    Orchestrator Agent that breaks down complex queries into subtasks
    and delegates them to specialized agents.
    """
    
    def __init__(self):
        super().__init__(
            name="orchestrator",
            description="Coordinates and delegates tasks to specialized agents",
            capabilities=[
                "task_decomposition",
                "agent_delegation",
                "result_compilation",
                "workflow_management"
            ]
        )
        self.agent_registry = AgentRegistry()
    
    def get_required_integrations(self) -> List[str]:
        """Orchestrator doesn't require specific integrations."""
        return []
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute orchestration workflow."""
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Analyze the query and determine task type
            task_analysis = await self._analyze_query(context)
            
            # Step 2: Decompose into subtasks
            subtasks = await self._decompose_task(context, task_analysis)
            
            # Step 3: Create subtask records in database
            await self._create_subtask_records(context.task_id, subtasks)
            
            # Step 4: Execute subtasks in order
            results = await self._execute_subtasks(context, subtasks)
            
            # Step 5: Compile final results
            final_result = await self._compile_results(context, results)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=True,
                data=final_result,
                message="Task orchestration completed successfully",
                execution_time=execution_time,
                output_files=final_result.get("output_files", [])
            )
            
            self.log_execution(context, result)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=False,
                data={},
                message=f"Orchestration failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.log_execution(context, result)
            return result
    
    async def _analyze_query(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze the user query to understand intent and requirements."""
        system_prompt = """
        You are an AI task analyzer. Analyze the user query and determine:
        1. Primary task type (research, analysis, content_creation, automation, etc.)
        2. Required capabilities and tools
        3. Complexity level (simple, moderate, complex)
        4. Estimated execution time
        5. Required integrations or external APIs
        
        Respond in JSON format with these fields:
        - task_type: string
        - capabilities: list of strings
        - complexity: string
        - estimated_time: string
        - integrations: list of strings
        - subtask_types: list of strings (what types of subtasks are needed)
        """
        
        prompt = f"""
        Query: {context.query}
        Task Type: {context.task_type}
        Priority: {context.priority}
        
        Analyze this query and provide the requested information.
        """
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Query analysis failed: {e}")
            # Fallback analysis
            return {
                "task_type": context.task_type or "general",
                "capabilities": ["general"],
                "complexity": "moderate",
                "estimated_time": "5-10 minutes",
                "integrations": [],
                "subtask_types": [context.task_type or "general"]
            }
    
    async def _decompose_task(self, context: AgentContext, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Decompose the main task into subtasks."""
        system_prompt = """
        You are a task decomposition expert. Break down the user query into specific subtasks
        that can be executed by specialized agents. Each subtask should be:
        1. Specific and actionable
        2. Assigned to the most appropriate agent type
        3. Have clear dependencies if any
        4. Include expected outputs
        
        Available agent types:
        - research: Web research, data gathering, market analysis
        - analysis: Data processing, statistical analysis, insights generation
        - content: Blog writing, article creation, copywriting
        - social_media: Twitter/X posting, Telegram management, social engagement
        - graphics: Image generation, poster creation, visual content
        - presentation: PowerPoint/PDF creation, slide design
        - automation: CRM integration, workflow automation, API calls
        - reporting: Dashboard creation, report generation, data visualization
        - customer_care: Chatbot creation, customer service automation
        - recommendation: Strategic advice, decision support, planning
        
        Respond in JSON format with a list of subtasks:
        [
            {
                "agent_type": "string",
                "description": "string",
                "dependencies": ["subtask_id"],
                "expected_output": "string",
                "priority": "high|medium|low"
            }
        ]
        """
        
        prompt = f"""
        Original Query: {context.query}
        Task Analysis: {json.dumps(analysis, indent=2)}
        
        Break this down into specific subtasks for execution.
        """
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            subtasks = json.loads(response)
            
            # Add execution order and IDs
            for i, subtask in enumerate(subtasks):
                subtask["subtask_id"] = f"subtask_{i+1}"
                subtask["execution_order"] = i + 1
            
            return subtasks
            
        except Exception as e:
            self.logger.error(f"Task decomposition failed: {e}")
            # Fallback: create a single subtask
            return [{
                "subtask_id": "subtask_1",
                "agent_type": analysis.get("task_type", "general"),
                "description": context.query,
                "dependencies": [],
                "expected_output": "Task completion",
                "priority": context.priority,
                "execution_order": 1
            }]
    
    async def _create_subtask_records(self, task_id: int, subtasks: List[Dict[str, Any]]):
        """Create subtask records in the database."""
        try:
            db = get_db()
            
            for subtask in subtasks:
                db_subtask = SubTask(
                    parent_task_id=task_id,
                    agent_name=subtask["agent_type"],
                    task_description=subtask["description"],
                    execution_order=subtask["execution_order"],
                    dependencies=subtask.get("dependencies", [])
                )
                db.add(db_subtask)
            
            db.commit()
            db.close()
            
        except Exception as e:
            self.logger.error(f"Failed to create subtask records: {e}")
    
    async def _execute_subtasks(self, context: AgentContext, subtasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute subtasks in the correct order."""
        results = {}
        
        # Sort subtasks by execution order
        sorted_subtasks = sorted(subtasks, key=lambda x: x["execution_order"])
        
        for subtask in sorted_subtasks:
            try:
                # Get the appropriate agent
                agent = self.agent_registry.get_agent(subtask["agent_type"])
                
                if not agent:
                    self.logger.warning(f"Agent {subtask['agent_type']} not found, skipping subtask")
                    results[subtask["subtask_id"]] = {
                        "success": False,
                        "error": f"Agent {subtask['agent_type']} not available"
                    }
                    continue
                
                # Create subtask context
                subtask_context = AgentContext(
                    user_id=context.user_id,
                    task_id=context.task_id,
                    query=subtask["description"],
                    task_type=subtask["agent_type"],
                    priority=subtask.get("priority", context.priority),
                    project_id=context.project_id,
                    previous_results=results,
                    integrations=context.integrations
                )
                
                # Execute subtask
                result = await agent.execute(subtask_context)
                results[subtask["subtask_id"]] = {
                    "success": result.success,
                    "data": result.data,
                    "message": result.message,
                    "output_files": result.output_files or [],
                    "error": result.error
                }
                
                # Update subtask status in database
                await self._update_subtask_status(context.task_id, subtask["subtask_id"], result)
                
            except Exception as e:
                self.logger.error(f"Subtask execution failed: {e}")
                results[subtask["subtask_id"]] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    async def _update_subtask_status(self, task_id: int, subtask_id: str, result: AgentResult):
        """Update subtask status in database."""
        try:
            db = get_db()
            
            subtask = db.query(SubTask).filter(
                SubTask.parent_task_id == task_id,
                SubTask.task_description.contains(subtask_id)  # Simple matching
            ).first()
            
            if subtask:
                subtask.status = "completed" if result.success else "failed"
                subtask.result_data = result.data
                subtask.completed_at = datetime.utcnow()
                db.commit()
            
            db.close()
            
        except Exception as e:
            self.logger.error(f"Failed to update subtask status: {e}")
    
    async def _compile_results(self, context: AgentContext, results: Dict[str, Any]) -> Dict[str, Any]:
        """Compile subtask results into final output."""
        successful_results = {k: v for k, v in results.items() if v.get("success", False)}
        failed_results = {k: v for k, v in results.items() if not v.get("success", False)}
        
        # Collect all output files
        all_output_files = []
        for result in successful_results.values():
            if result.get("output_files"):
                all_output_files.extend(result["output_files"])
        
        # Create summary
        system_prompt = """
        You are a results compiler. Create a comprehensive summary of the task execution results.
        Include key findings, generated content, and actionable insights.
        Be concise but thorough.
        """
        
        prompt = f"""
        Original Query: {context.query}
        
        Successful Results:
        {json.dumps(successful_results, indent=2)}
        
        Failed Results:
        {json.dumps(failed_results, indent=2)}
        
        Create a comprehensive summary of what was accomplished.
        """
        
        try:
            summary = await self.call_llm(prompt, system_prompt, temperature=0.3)
        except Exception as e:
            summary = f"Task execution completed with {len(successful_results)} successful subtasks and {len(failed_results)} failed subtasks."
        
        return {
            "summary": summary,
            "successful_subtasks": len(successful_results),
            "failed_subtasks": len(failed_results),
            "total_subtasks": len(results),
            "output_files": all_output_files,
            "detailed_results": results,
            "execution_timestamp": datetime.utcnow().isoformat()
        }
