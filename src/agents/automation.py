"""Automation Agent for CRM integration and workflow automation."""

import requests
from typing import Dict, Any, List
from datetime import datetime
import json

from src.agents.base import LLMAgent, AgentContext, AgentResult


class AutomationAgent(LLMAgent):
    """Agent specialized in automation and system integrations."""
    
    def __init__(self):
        super().__init__(
            name="automation",
            description="Handles CRM integration, workflow automation, and API calls",
            capabilities=[
                "crm_integration",
                "workflow_automation",
                "api_integration",
                "data_synchronization",
                "process_automation"
            ]
        )
    
    def get_required_integrations(self) -> List[str]:
        """Automation agent may require various CRM and API integrations."""
        return ["salesforce", "hubspot", "zapier", "webhook"]
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute automation task."""
        start_time = datetime.utcnow()
        
        try:
            # Parse automation requirements
            automation_spec = await self._parse_automation_requirements(context.query)
            
            # Execute automation workflows
            automation_results = await self._execute_automation(automation_spec, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=True,
                data={
                    "automation_spec": automation_spec,
                    "execution_results": automation_results,
                    "workflows_executed": len(automation_results.get("workflows", [])),
                    "integrations_used": automation_spec.get("integrations", [])
                },
                message="Automation tasks completed successfully",
                execution_time=execution_time
            )
            
            # Save to memory
            self.save_memory(
                memory_type="automation",
                content={
                    "workflow_type": automation_spec.get("type", "general"),
                    "integrations": automation_spec.get("integrations", []),
                    "success_count": len(automation_results.get("workflows", []))
                },
                context_tags=["automation", "integration"],
                relevance_score=0.8
            )
            
            self.log_execution(context, result)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=False,
                data={},
                message=f"Automation failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.log_execution(context, result)
            return result
    
    async def _parse_automation_requirements(self, query: str) -> Dict[str, Any]:
        """Parse automation requirements from query."""
        system_prompt = """
        You are an automation expert. Parse the requirements and determine:
        1. Type of automation (CRM update, data sync, workflow trigger, etc.)
        2. Systems/platforms to integrate
        3. Data to process or transfer
        4. Triggers and conditions
        5. Actions to perform
        
        Respond in JSON format:
        {
            "type": "crm_update",
            "integrations": ["salesforce", "email"],
            "data_sources": ["customer_data", "sales_data"],
            "triggers": ["new_lead", "status_change"],
            "actions": ["update_crm", "send_notification"],
            "conditions": ["if_status_equals_qualified"]
        }
        """
        
        prompt = f"Parse automation requirements for: {query}"
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Automation parsing failed: {e}")
            return {
                "type": "general_automation",
                "integrations": ["api"],
                "data_sources": ["user_input"],
                "triggers": ["manual"],
                "actions": ["process_data"],
                "conditions": []
            }
    
    async def _execute_automation(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Execute automation workflows based on specification."""
        results = {"workflows": [], "integrations": {}}
        
        try:
            for action in spec.get("actions", []):
                workflow_result = await self._execute_workflow_action(action, spec, context)
                results["workflows"].append(workflow_result)
            
            # Handle integrations
            for integration in spec.get("integrations", []):
                integration_result = await self._handle_integration(integration, spec, context)
                results["integrations"][integration] = integration_result
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    async def _execute_workflow_action(self, action: str, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Execute a specific workflow action."""
        try:
            if action == "update_crm":
                return await self._update_crm_records(spec, context)
            elif action == "send_notification":
                return await self._send_notification(spec, context)
            elif action == "sync_data":
                return await self._sync_data(spec, context)
            elif action == "trigger_webhook":
                return await self._trigger_webhook(spec, context)
            else:
                return await self._generic_action(action, spec, context)
                
        except Exception as e:
            return {
                "action": action,
                "success": False,
                "error": str(e)
            }
    
    async def _update_crm_records(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Update CRM records (mock implementation)."""
        # In production, integrate with actual CRM APIs
        mock_data = {
            "records_updated": 5,
            "fields_modified": ["status", "last_contact", "notes"],
            "crm_system": "salesforce"
        }
        
        return {
            "action": "update_crm",
            "success": True,
            "data": mock_data,
            "message": "CRM records updated successfully"
        }
    
    async def _send_notification(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Send notifications (mock implementation)."""
        # In production, integrate with email/SMS services
        mock_data = {
            "notifications_sent": 3,
            "channels": ["email", "slack"],
            "recipients": ["team@company.com", "#sales-channel"]
        }
        
        return {
            "action": "send_notification",
            "success": True,
            "data": mock_data,
            "message": "Notifications sent successfully"
        }
    
    async def _sync_data(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Synchronize data between systems (mock implementation)."""
        mock_data = {
            "records_synced": 25,
            "source_system": "database",
            "target_system": "crm",
            "sync_timestamp": datetime.utcnow().isoformat()
        }
        
        return {
            "action": "sync_data",
            "success": True,
            "data": mock_data,
            "message": "Data synchronization completed"
        }
    
    async def _trigger_webhook(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Trigger webhook calls (mock implementation)."""
        # In production, make actual HTTP requests
        mock_data = {
            "webhooks_triggered": 2,
            "endpoints": ["https://api.example.com/webhook1", "https://api.example.com/webhook2"],
            "responses": ["200 OK", "200 OK"]
        }
        
        return {
            "action": "trigger_webhook",
            "success": True,
            "data": mock_data,
            "message": "Webhooks triggered successfully"
        }
    
    async def _generic_action(self, action: str, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Handle generic automation actions."""
        return {
            "action": action,
            "success": True,
            "data": {"processed": True},
            "message": f"Generic action '{action}' completed"
        }
    
    async def _handle_integration(self, integration: str, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Handle specific integration setup and execution."""
        try:
            if integration == "salesforce":
                return await self._handle_salesforce_integration(spec, context)
            elif integration == "hubspot":
                return await self._handle_hubspot_integration(spec, context)
            elif integration == "zapier":
                return await self._handle_zapier_integration(spec, context)
            else:
                return await self._handle_generic_integration(integration, spec, context)
                
        except Exception as e:
            return {
                "integration": integration,
                "success": False,
                "error": str(e)
            }
    
    async def _handle_salesforce_integration(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Handle Salesforce integration (mock implementation)."""
        return {
            "integration": "salesforce",
            "success": True,
            "data": {
                "connected": True,
                "api_version": "v52.0",
                "operations": ["read", "write", "update"]
            },
            "message": "Salesforce integration configured"
        }
    
    async def _handle_hubspot_integration(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Handle HubSpot integration (mock implementation)."""
        return {
            "integration": "hubspot",
            "success": True,
            "data": {
                "connected": True,
                "portal_id": "12345678",
                "scopes": ["contacts", "deals", "companies"]
            },
            "message": "HubSpot integration configured"
        }
    
    async def _handle_zapier_integration(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Handle Zapier integration (mock implementation)."""
        return {
            "integration": "zapier",
            "success": True,
            "data": {
                "webhook_url": "https://hooks.zapier.com/hooks/catch/12345/abcdef/",
                "triggers_available": True
            },
            "message": "Zapier integration configured"
        }
    
    async def _handle_generic_integration(self, integration: str, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Handle generic integration."""
        return {
            "integration": integration,
            "success": True,
            "data": {"configured": True},
            "message": f"Generic integration '{integration}' configured"
        }
