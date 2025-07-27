"""Customer Care Agent for chatbot creation and deployment."""

import os
from typing import Dict, Any, List
from datetime import datetime
import json

from src.agents.base import LLMAgent, AgentContext, AgentResult


class CustomerCareAgent(LLMAgent):
    """Agent specialized in creating and deploying customer care chatbots."""
    
    def __init__(self):
        super().__init__(
            name="customer_care",
            description="Creates and deploys customer service chatbots and automated support systems",
            capabilities=[
                "chatbot_creation",
                "customer_support_automation",
                "faq_generation",
                "conversation_flow_design",
                "support_ticket_automation"
            ]
        )
    
    def get_required_integrations(self) -> List[str]:
        """Customer care agent may require chat platform integrations."""
        return ["rasa", "dialogflow", "telegram", "slack"]
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute customer care task."""
        start_time = datetime.utcnow()
        
        try:
            # Parse customer care requirements
            care_spec = await self._parse_care_requirements(context.query)
            
            # Generate chatbot configuration
            chatbot_config = await self._generate_chatbot_config(care_spec, context)
            
            # Create conversation flows
            conversation_flows = await self._create_conversation_flows(care_spec, context)
            
            # Generate deployment files
            deployment_files = await self._generate_deployment_files(chatbot_config, conversation_flows)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=True,
                data={
                    "care_spec": care_spec,
                    "chatbot_config": chatbot_config,
                    "conversation_flows": conversation_flows,
                    "intents_count": len(conversation_flows.get("intents", [])),
                    "responses_count": len(conversation_flows.get("responses", []))
                },
                message="Customer care chatbot created successfully",
                execution_time=execution_time,
                output_files=deployment_files
            )
            
            # Save to memory
            self.save_memory(
                memory_type="customer_care",
                content={
                    "chatbot_type": care_spec.get("type", "general"),
                    "platform": care_spec.get("platform", "web"),
                    "intents_created": len(conversation_flows.get("intents", []))
                },
                context_tags=["customer_care", "chatbot"],
                relevance_score=0.8
            )
            
            self.log_execution(context, result)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=False,
                data={},
                message=f"Customer care creation failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.log_execution(context, result)
            return result
    
    async def _parse_care_requirements(self, query: str) -> Dict[str, Any]:
        """Parse customer care requirements from query."""
        system_prompt = """
        You are a customer service expert. Parse the requirements and determine:
        1. Type of customer service needed (chatbot, FAQ, support automation)
        2. Target platform (web, mobile, telegram, slack)
        3. Business domain and use cases
        4. Common customer queries and issues
        5. Integration requirements
        6. Response style and tone
        
        Respond in JSON format:
        {
            "type": "chatbot",
            "platform": "web",
            "domain": "e-commerce",
            "use_cases": ["order_status", "returns", "product_info"],
            "common_queries": ["Where is my order?", "How to return?"],
            "tone": "friendly_professional",
            "languages": ["english"]
        }
        """
        
        prompt = f"Parse customer care requirements for: {query}"
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Customer care parsing failed: {e}")
            return {
                "type": "chatbot",
                "platform": "web",
                "domain": "general",
                "use_cases": ["general_inquiry", "support"],
                "common_queries": ["How can I help you?", "What do you need?"],
                "tone": "friendly_professional",
                "languages": ["english"]
            }
    
    async def _generate_chatbot_config(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Generate chatbot configuration."""
        return {
            "name": f"{spec.get('domain', 'general')}_support_bot",
            "description": f"Customer support chatbot for {spec.get('domain', 'general')} domain",
            "platform": spec.get("platform", "web"),
            "language": spec.get("languages", ["english"])[0],
            "tone": spec.get("tone", "friendly_professional"),
            "fallback_message": "I'm sorry, I didn't understand that. Could you please rephrase your question?",
            "greeting_message": "Hello! I'm here to help you. How can I assist you today?",
            "goodbye_message": "Thank you for contacting us. Have a great day!",
            "escalation_trigger": "human_agent",
            "confidence_threshold": 0.7,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _create_conversation_flows(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Create conversation flows and intents."""
        system_prompt = """
        You are a conversation design expert. Create comprehensive conversation flows including:
        1. Intents (user intentions)
        2. Entities (key information to extract)
        3. Responses for each intent
        4. Follow-up questions
        5. Escalation paths
        
        Respond in JSON format:
        {
            "intents": [
                {
                    "name": "order_status",
                    "examples": ["Where is my order?", "Track my order"],
                    "entities": ["order_number"],
                    "responses": ["I can help you track your order. Please provide your order number."],
                    "follow_up": ["Is there anything else I can help you with?"]
                }
            ],
            "entities": [
                {
                    "name": "order_number",
                    "type": "text",
                    "patterns": ["[A-Z]{2}[0-9]{6}"]
                }
            ],
            "responses": {
                "greeting": ["Hello! How can I help you today?"],
                "goodbye": ["Thank you! Have a great day!"],
                "fallback": ["I didn't understand. Can you rephrase?"]
            }
        }
        """
        
        prompt = f"""
        Customer care specification:
        {json.dumps(spec, indent=2)}
        
        Create comprehensive conversation flows for the chatbot.
        """
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.4)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Conversation flow creation failed: {e}")
            return {
                "intents": [
                    {
                        "name": "greeting",
                        "examples": ["Hello", "Hi", "Hey"],
                        "entities": [],
                        "responses": ["Hello! How can I help you today?"],
                        "follow_up": []
                    },
                    {
                        "name": "help",
                        "examples": ["I need help", "Can you help me?"],
                        "entities": [],
                        "responses": ["I'm here to help! What do you need assistance with?"],
                        "follow_up": ["What specific issue are you facing?"]
                    }
                ],
                "entities": [],
                "responses": {
                    "greeting": ["Hello! How can I help you today?"],
                    "goodbye": ["Thank you! Have a great day!"],
                    "fallback": ["I didn't understand. Can you rephrase that?"]
                }
            }
    
    async def _generate_deployment_files(self, config: Dict[str, Any], flows: Dict[str, Any]) -> List[str]:
        """Generate deployment files for the chatbot."""
        output_files = []
        
        try:
            # Create uploads directory
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Generate Rasa NLU training data
            nlu_file = await self._generate_rasa_nlu_file(flows, timestamp)
            if nlu_file:
                output_files.append(nlu_file)
            
            # Generate Rasa domain file
            domain_file = await self._generate_rasa_domain_file(config, flows, timestamp)
            if domain_file:
                output_files.append(domain_file)
            
            # Generate stories file
            stories_file = await self._generate_rasa_stories_file(flows, timestamp)
            if stories_file:
                output_files.append(stories_file)
            
            # Generate configuration file
            config_file = await self._generate_rasa_config_file(config, timestamp)
            if config_file:
                output_files.append(config_file)
            
            # Generate deployment README
            readme_file = await self._generate_deployment_readme(config, timestamp)
            if readme_file:
                output_files.append(readme_file)
            
        except Exception as e:
            self.logger.error(f"Deployment file generation failed: {e}")
        
        return output_files
    
    async def _generate_rasa_nlu_file(self, flows: Dict[str, Any], timestamp: str) -> str:
        """Generate Rasa NLU training data file."""
        try:
            nlu_data = {
                "version": "3.1",
                "nlu": []
            }
            
            # Add intents
            for intent in flows.get("intents", []):
                intent_data = {
                    "intent": intent["name"],
                    "examples": "\n".join([f"- {example}" for example in intent["examples"]])
                }
                nlu_data["nlu"].append(intent_data)
            
            filename = f"nlu_{timestamp}.yml"
            filepath = os.path.join("uploads", filename)
            
            import yaml
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(nlu_data, f, default_flow_style=False, allow_unicode=True)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"NLU file generation failed: {e}")
            return None
    
    async def _generate_rasa_domain_file(self, config: Dict[str, Any], flows: Dict[str, Any], timestamp: str) -> str:
        """Generate Rasa domain file."""
        try:
            domain_data = {
                "version": "3.1",
                "intents": [intent["name"] for intent in flows.get("intents", [])],
                "entities": [entity["name"] for entity in flows.get("entities", [])],
                "responses": {}
            }
            
            # Add responses
            for intent in flows.get("intents", []):
                response_key = f"utter_{intent['name']}"
                domain_data["responses"][response_key] = [
                    {"text": response} for response in intent["responses"]
                ]
            
            # Add default responses
            for key, responses in flows.get("responses", {}).items():
                domain_data["responses"][f"utter_{key}"] = [
                    {"text": response} for response in responses
                ]
            
            filename = f"domain_{timestamp}.yml"
            filepath = os.path.join("uploads", filename)
            
            import yaml
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(domain_data, f, default_flow_style=False, allow_unicode=True)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Domain file generation failed: {e}")
            return None
    
    async def _generate_rasa_stories_file(self, flows: Dict[str, Any], timestamp: str) -> str:
        """Generate Rasa stories file."""
        try:
            stories_content = "version: \"3.1\"\n\nstories:\n"
            
            for intent in flows.get("intents", []):
                story = f"""
- story: {intent['name']}_story
  steps:
  - intent: {intent['name']}
  - action: utter_{intent['name']}
"""
                stories_content += story
            
            filename = f"stories_{timestamp}.yml"
            filepath = os.path.join("uploads", filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(stories_content)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Stories file generation failed: {e}")
            return None
    
    async def _generate_rasa_config_file(self, config: Dict[str, Any], timestamp: str) -> str:
        """Generate Rasa configuration file."""
        try:
            config_content = """# Configuration for Rasa NLU.
language: en

pipeline:
  - name: WhitespaceTokenizer
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: CountVectorsFeaturizer
    analyzer: char_wb
    min_ngram: 1
    max_ngram: 4
  - name: DIETClassifier
    epochs: 100
    constrain_similarities: true
  - name: EntitySynonymMapper
  - name: ResponseSelector
    epochs: 100
    constrain_similarities: true
  - name: FallbackClassifier
    threshold: 0.3
    ambiguity_threshold: 0.1

policies:
  - name: MemoizationPolicy
  - name: RulePolicy
  - name: UnexpecTEDIntentPolicy
    max_history: 5
    epochs: 100
  - name: TEDPolicy
    max_history: 5
    epochs: 100
    constrain_similarities: true
"""
            
            filename = f"config_{timestamp}.yml"
            filepath = os.path.join("uploads", filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Config file generation failed: {e}")
            return None
    
    async def _generate_deployment_readme(self, config: Dict[str, Any], timestamp: str) -> str:
        """Generate deployment README file."""
        try:
            readme_content = f"""# {config.get('name', 'Customer Support Bot')}

## Overview

This is a customer support chatbot created for the {config.get('domain', 'general')} domain.

**Platform:** {config.get('platform', 'web')}
**Language:** {config.get('language', 'english')}
**Tone:** {config.get('tone', 'friendly_professional')}

## Setup Instructions

### Prerequisites
- Python 3.8+
- Rasa 3.1+

### Installation

1. Install Rasa:
```bash
pip install rasa
```

2. Train the model:
```bash
rasa train
```

3. Test the chatbot:
```bash
rasa shell
```

4. Run the action server (if using custom actions):
```bash
rasa run actions
```

5. Start the Rasa server:
```bash
rasa run --enable-api --cors "*"
```

## Configuration

- **Confidence Threshold:** {config.get('confidence_threshold', 0.7)}
- **Fallback Message:** "{config.get('fallback_message', 'I did not understand.')}"
- **Greeting:** "{config.get('greeting_message', 'Hello!')}"

## Deployment

### Web Integration
```html
<script src="https://cdn.jsdelivr.net/npm/rasa-webchat/lib/index.js"></script>
<script>
  WebChat.default.init({{
    selector: "#webchat",
    initPayload: "/get_started",
    customData: {{"language": "en"}},
    socketUrl: "http://localhost:5005",
    title: "Customer Support",
    subtitle: "How can I help you today?"
  }})
</script>
```

### API Usage
```bash
curl -X POST http://localhost:5005/webhooks/rest/webhook \\
  -H "Content-Type: application/json" \\
  -d '{{"sender": "user", "message": "Hello"}}'
```

## Customization

1. **Add New Intents:** Update the NLU training data
2. **Modify Responses:** Edit the domain file
3. **Create Stories:** Add new conversation flows
4. **Custom Actions:** Implement in actions.py

## Support

For technical support or customization requests, please contact the development team.

---
*Generated by AI Consultancy Platform on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            
            filename = f"chatbot_readme_{timestamp}.md"
            filepath = os.path.join("uploads", filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"README generation failed: {e}")
            return None
