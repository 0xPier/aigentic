"""Recommendation Agent for strategic advice and decision support."""

from typing import Dict, Any, List
from datetime import datetime
import json

from src.agents.base import LLMAgent, AgentContext, AgentResult


class RecommendationAgent(LLMAgent):
    """Agent specialized in providing strategic recommendations and decision support."""
    
    def __init__(self):
        super().__init__(
            name="recommendation",
            description="Provides strategic recommendations, decision support, and business planning",
            capabilities=[
                "strategic_planning",
                "decision_support",
                "business_analysis",
                "risk_assessment",
                "opportunity_identification"
            ]
        )
    
    def get_required_integrations(self) -> List[str]:
        """Recommendation agent doesn't require specific integrations."""
        return []
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute recommendation task."""
        start_time = datetime.utcnow()
        
        try:
            # Analyze the situation and requirements
            situation_analysis = await self._analyze_situation(context)
            
            # Generate strategic recommendations
            recommendations = await self._generate_recommendations(situation_analysis, context)
            
            # Assess risks and opportunities
            risk_assessment = await self._assess_risks_opportunities(recommendations, context)
            
            # Create implementation plan
            implementation_plan = await self._create_implementation_plan(recommendations, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=True,
                data={
                    "situation_analysis": situation_analysis,
                    "recommendations": recommendations,
                    "risk_assessment": risk_assessment,
                    "implementation_plan": implementation_plan,
                    "priority_actions": recommendations.get("priority_actions", []),
                    "success_metrics": implementation_plan.get("success_metrics", [])
                },
                message="Strategic recommendations generated successfully",
                execution_time=execution_time
            )
            
            # Save to memory
            self.save_memory(
                memory_type="recommendation",
                content={
                    "domain": situation_analysis.get("domain", "business"),
                    "recommendations_count": len(recommendations.get("recommendations", [])),
                    "priority_level": recommendations.get("priority", "medium")
                },
                context_tags=["strategy", "recommendations"],
                relevance_score=0.9
            )
            
            self.log_execution(context, result)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=False,
                data={},
                message=f"Recommendation generation failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.log_execution(context, result)
            return result
    
    async def _analyze_situation(self, context: AgentContext) -> Dict[str, Any]:
        """Analyze the current situation and context."""
        system_prompt = """
        You are a strategic business analyst. Analyze the situation and provide:
        1. Current state assessment
        2. Key challenges and pain points
        3. Available resources and constraints
        4. Market context and competitive landscape
        5. Stakeholder considerations
        
        Respond in JSON format:
        {
            "domain": "business area",
            "current_state": "description of current situation",
            "challenges": ["challenge1", "challenge2"],
            "resources": ["resource1", "resource2"],
            "constraints": ["constraint1", "constraint2"],
            "stakeholders": ["stakeholder1", "stakeholder2"],
            "market_context": "market analysis"
        }
        """
        
        # Include previous results context if available
        context_info = ""
        if context.previous_results:
            context_info = f"\nPrevious analysis results: {json.dumps(context.previous_results, indent=2)}"
        
        prompt = f"""
        Situation to analyze: {context.query}
        Task type: {context.task_type}
        Priority: {context.priority}
        {context_info}
        
        Provide a comprehensive situation analysis.
        """
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Situation analysis failed: {e}")
            return {
                "domain": "general",
                "current_state": "Analysis in progress",
                "challenges": ["Need more information"],
                "resources": ["Available team", "Budget allocation"],
                "constraints": ["Time limitations", "Resource constraints"],
                "stakeholders": ["Management", "Team members"],
                "market_context": "Competitive market environment"
            }
    
    async def _generate_recommendations(self, situation: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Generate strategic recommendations based on situation analysis."""
        system_prompt = """
        You are a strategic consultant. Based on the situation analysis, provide:
        1. Strategic recommendations (3-5 key recommendations)
        2. Priority actions (immediate next steps)
        3. Long-term strategic initiatives
        4. Resource requirements
        5. Expected outcomes and benefits
        
        Respond in JSON format:
        {
            "recommendations": [
                {
                    "title": "Recommendation title",
                    "description": "Detailed description",
                    "priority": "high|medium|low",
                    "timeline": "timeframe",
                    "resources_needed": ["resource1", "resource2"],
                    "expected_outcome": "expected result"
                }
            ],
            "priority_actions": ["action1", "action2"],
            "long_term_initiatives": ["initiative1", "initiative2"],
            "success_factors": ["factor1", "factor2"]
        }
        """
        
        prompt = f"""
        Situation Analysis:
        {json.dumps(situation, indent=2)}
        
        Original Query: {context.query}
        
        Generate strategic recommendations to address the situation.
        """
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.4)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Recommendation generation failed: {e}")
            return {
                "recommendations": [
                    {
                        "title": "Immediate Assessment",
                        "description": "Conduct thorough assessment of current situation",
                        "priority": "high",
                        "timeline": "1-2 weeks",
                        "resources_needed": ["Analysis team", "Data access"],
                        "expected_outcome": "Clear understanding of current state"
                    }
                ],
                "priority_actions": ["Gather more data", "Stakeholder consultation"],
                "long_term_initiatives": ["Strategic planning", "Process improvement"],
                "success_factors": ["Clear communication", "Stakeholder buy-in"]
            }
    
    async def _assess_risks_opportunities(self, recommendations: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Assess risks and opportunities for the recommendations."""
        system_prompt = """
        You are a risk assessment expert. Analyze the recommendations and identify:
        1. Key risks and mitigation strategies
        2. Opportunities for additional value
        3. Dependencies and critical success factors
        4. Potential obstacles and solutions
        
        Respond in JSON format:
        {
            "risks": [
                {
                    "risk": "risk description",
                    "impact": "high|medium|low",
                    "probability": "high|medium|low",
                    "mitigation": "mitigation strategy"
                }
            ],
            "opportunities": [
                {
                    "opportunity": "opportunity description",
                    "potential_value": "value description",
                    "requirements": ["requirement1", "requirement2"]
                }
            ],
            "dependencies": ["dependency1", "dependency2"],
            "critical_success_factors": ["factor1", "factor2"]
        }
        """
        
        prompt = f"""
        Recommendations to assess:
        {json.dumps(recommendations, indent=2)}
        
        Context: {context.query}
        
        Provide comprehensive risk and opportunity assessment.
        """
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Risk assessment failed: {e}")
            return {
                "risks": [
                    {
                        "risk": "Implementation challenges",
                        "impact": "medium",
                        "probability": "medium",
                        "mitigation": "Careful planning and stakeholder engagement"
                    }
                ],
                "opportunities": [
                    {
                        "opportunity": "Process improvement",
                        "potential_value": "Increased efficiency",
                        "requirements": ["Team training", "Tool implementation"]
                    }
                ],
                "dependencies": ["Management support", "Resource availability"],
                "critical_success_factors": ["Clear communication", "Proper execution"]
            }
    
    async def _create_implementation_plan(self, recommendations: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Create an implementation plan for the recommendations."""
        system_prompt = """
        You are a project management expert. Create an implementation plan including:
        1. Phased approach with timelines
        2. Resource allocation
        3. Milestones and deliverables
        4. Success metrics and KPIs
        5. Communication and governance structure
        
        Respond in JSON format:
        {
            "phases": [
                {
                    "phase": "Phase name",
                    "duration": "timeframe",
                    "objectives": ["objective1", "objective2"],
                    "deliverables": ["deliverable1", "deliverable2"],
                    "resources": ["resource1", "resource2"]
                }
            ],
            "milestones": [
                {
                    "milestone": "milestone name",
                    "target_date": "relative timeframe",
                    "success_criteria": ["criteria1", "criteria2"]
                }
            ],
            "success_metrics": ["metric1", "metric2"],
            "governance": {
                "steering_committee": ["role1", "role2"],
                "reporting_frequency": "frequency",
                "review_points": ["point1", "point2"]
            }
        }
        """
        
        prompt = f"""
        Recommendations to implement:
        {json.dumps(recommendations, indent=2)}
        
        Context: {context.query}
        Priority: {context.priority}
        
        Create a detailed implementation plan.
        """
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Implementation planning failed: {e}")
            return {
                "phases": [
                    {
                        "phase": "Planning Phase",
                        "duration": "2-4 weeks",
                        "objectives": ["Define scope", "Allocate resources"],
                        "deliverables": ["Project plan", "Resource allocation"],
                        "resources": ["Project manager", "Core team"]
                    },
                    {
                        "phase": "Execution Phase",
                        "duration": "4-8 weeks",
                        "objectives": ["Implement recommendations", "Monitor progress"],
                        "deliverables": ["Implementation results", "Progress reports"],
                        "resources": ["Implementation team", "Subject matter experts"]
                    }
                ],
                "milestones": [
                    {
                        "milestone": "Planning Complete",
                        "target_date": "Week 4",
                        "success_criteria": ["Approved plan", "Team ready"]
                    },
                    {
                        "milestone": "Implementation Complete",
                        "target_date": "Week 12",
                        "success_criteria": ["All recommendations implemented", "Success metrics met"]
                    }
                ],
                "success_metrics": ["Implementation completion rate", "Stakeholder satisfaction", "ROI achievement"],
                "governance": {
                    "steering_committee": ["Project sponsor", "Key stakeholders"],
                    "reporting_frequency": "Weekly",
                    "review_points": ["Phase gates", "Milestone reviews"]
                }
            }
