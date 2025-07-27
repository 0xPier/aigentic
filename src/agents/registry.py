"""Agent registry for managing and discovering available agents."""

from typing import Dict, List, Optional, Type
from src.agents.base import BaseAgent


class AgentRegistry:
    """Registry for managing and discovering available agents."""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize and register all available agents."""
        # Import agents here to avoid circular imports
        from src.agents.research import ResearchAgent
        from src.agents.analysis import AnalysisAgent
        from src.agents.content import ContentAgent
        from src.agents.social_media import SocialMediaAgent
        from src.agents.graphics import GraphicsAgent
        from src.agents.presentation import PresentationAgent
        from src.agents.automation import AutomationAgent
        from src.agents.reporting import ReportingAgent
        from src.agents.customer_care import CustomerCareAgent
        from src.agents.recommendation import RecommendationAgent
        from src.agents.orchestrator import OrchestratorAgent
        
        # Register agent classes
        agent_classes = [
            ResearchAgent,
            AnalysisAgent,
            ContentAgent,
            SocialMediaAgent,
            GraphicsAgent,
            PresentationAgent,
            AutomationAgent,
            ReportingAgent,
            CustomerCareAgent,
            RecommendationAgent,
            OrchestratorAgent
        ]
        
        for agent_class in agent_classes:
            try:
                agent_instance = agent_class()
                self._agents[agent_instance.name] = agent_instance
                self._agent_classes[agent_instance.name] = agent_class
            except Exception as e:
                print(f"Failed to initialize agent {agent_class.__name__}: {e}")
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get an agent instance by name."""
        return self._agents.get(agent_name)
    
    def get_agent_class(self, agent_name: str) -> Optional[Type[BaseAgent]]:
        """Get an agent class by name."""
        return self._agent_classes.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, Dict[str, any]]:
        """Get information about all registered agents."""
        return {
            name: {
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities,
                "required_integrations": agent.get_required_integrations()
            }
            for name, agent in self._agents.items()
        }
    
    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities mapping for all agents."""
        return {
            name: agent.capabilities
            for name, agent in self._agents.items()
        }
    
    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Get all agents that have a specific capability."""
        return [
            agent for agent in self._agents.values()
            if capability in agent.capabilities
        ]
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, any]]:
        """Get detailed information about a specific agent."""
        agent = self._agents.get(agent_name)
        if not agent:
            return None
        
        return {
            "name": agent.name,
            "description": agent.description,
            "capabilities": agent.capabilities,
            "required_integrations": agent.get_required_integrations(),
            "memory_enabled": agent.memory_enabled
        }
    
    def register_agent(self, agent: BaseAgent):
        """Register a new agent instance."""
        self._agents[agent.name] = agent
        self._agent_classes[agent.name] = type(agent)
    
    def unregister_agent(self, agent_name: str):
        """Unregister an agent."""
        if agent_name in self._agents:
            del self._agents[agent_name]
        if agent_name in self._agent_classes:
            del self._agent_classes[agent_name]
    
    def list_agent_names(self) -> List[str]:
        """Get list of all registered agent names."""
        return list(self._agents.keys())


# Global registry instance
_registry = None


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
