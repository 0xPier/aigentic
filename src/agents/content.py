"""Content Creation Agent for blog writing and long-form content."""

import os
from typing import Dict, Any, List
from datetime import datetime
import json
import logging

from src.agents.base import LLMAgent, AgentContext, AgentResult
from src.integrations.api_client import api_manager

logger = logging.getLogger(__name__)


class ContentAgent(LLMAgent):
    """Agent specialized in content creation and writing."""
    
    def __init__(self):
        super().__init__(
            name="content",
            description="Creates blogs, articles, and long-form content with SEO optimization",
            capabilities=[
                "blog_writing",
                "article_creation",
                "copywriting",
                "seo_optimization",
                "content_strategy"
            ]
        )
    
    def get_required_integrations(self) -> List[str]:
        """Content agent doesn't require specific integrations."""
        return []
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute content creation task."""
        start_time = datetime.utcnow()
        
        try:
            # Analyze content requirements
            content_brief = await self._create_content_brief(context.query)
            
            # Generate content using OpenAI
            content_type = content_brief.get("type", "article")
            topic = content_brief.get("topic", "")
            target_audience = content_brief.get("audience", "general")
            requirements = content_brief.get("requirements", "")
            keywords = content_brief.get("keywords", [])
            
            content_prompt = f"""
            Create {content_type} content based on the following requirements:
            
            Topic: {topic}
            Target Audience: {target_audience}
            Content Requirements: {requirements}
            
            Please create engaging, informative content that:
            1. Captures attention with a compelling headline
            2. Provides valuable information
            3. Is optimized for SEO with relevant keywords
            4. Includes a clear call-to-action
            5. Matches the tone for the target audience
            6. Is well-structured with proper headings and subheadings
            
            Format the response as structured content with clear sections including:
            - Headline
            - Introduction
            - Main content with subheadings
            - Conclusion
            - Call-to-action
            - SEO keywords
            """
            
            # Use OpenAI for content generation
            content_response = await api_manager.openai.chat_completion([
                {
                    "role": "system",
                    "content": f"You are an expert content writer specializing in {content_type} creation. Create high-quality, engaging content that resonates with the target audience and achieves business objectives."
                },
                {
                    "role": "user",
                    "content": content_prompt
                }
            ], model="gpt-4", max_tokens=3000, temperature=0.7)
            
            if content_response["success"]:
                content_result = content_response["content"]
            else:
                content_result = f"Content generation failed: {content_response.get('error', 'Unknown error')}"
                logger.error(f"OpenAI content generation failed: {content_response.get('error')}")
            
            # Generate SEO optimization suggestions using OpenAI
            seo_prompt = f"""
            Analyze the following content and provide comprehensive SEO optimization suggestions:
            
            Content: {content_result}
            Target Keywords: {', '.join(keywords)}
            
            Provide detailed recommendations for:
            1. Title tag suggestions (under 60 characters, include primary keyword)
            2. Meta description suggestions (under 160 characters, compelling and keyword-rich)
            3. Header structure recommendations (H1, H2, H3 hierarchy)
            4. Keyword density analysis and optimization
            5. Internal linking opportunities
            6. Content improvements for better search rankings
            7. Featured snippet optimization
            8. Schema markup suggestions
            
            Format as actionable SEO recommendations.
            """
            
            # Use OpenAI for SEO analysis
            seo_response = await api_manager.openai.chat_completion([
                {
                    "role": "system",
                    "content": "You are an SEO expert. Analyze content and provide specific, actionable SEO optimization recommendations that will improve search engine rankings."
                },
                {
                    "role": "user",
                    "content": seo_prompt
                }
            ], model="gpt-4", max_tokens=2000, temperature=0.3)
            
            if seo_response["success"]:
                seo_suggestions = seo_response["content"]
            else:
                seo_suggestions = f"SEO analysis failed: {seo_response.get('error', 'Unknown error')}"
                logger.error(f"OpenAI SEO analysis failed: {seo_response.get('error')}")
            
            # Save content to file with comprehensive metadata
            content_file = f"content_{content_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            # Create comprehensive content package
            content_package = {
                "content": content_result,
                "seo_suggestions": seo_suggestions,
                "metadata": {
                    "topic": topic,
                    "content_type": content_type,
                    "target_audience": target_audience,
                    "keywords": keywords,
                    "requirements": requirements,
                    "created_at": datetime.now().isoformat(),
                    "agent": self.name,
                    "openai_usage": {
                        "content_generation": content_response.get("usage"),
                        "seo_analysis": seo_response.get("usage")
                    }
                }
            }
            
            # Save as both markdown and JSON
            await self.save_output(content_file, f"# {topic}\n\n{content_result}\n\n## SEO Recommendations\n\n{seo_suggestions}")
            
            json_file = content_file.replace('.md', '.json')
            await self.save_output(json_file, content_package)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=True,
                data={
                    "content_brief": content_brief,
                    "content": content_result,
                    "word_count": len(content_result.split()),
                    "seo_keywords": keywords,
                    "content_type": content_type
                },
                message="Content created successfully",
                execution_time=execution_time,
                output_files=[content_file, json_file]
            )
            
            # Save to memory
            self.save_memory(
                memory_type="content",
                content={
                    "topic": topic,
                    "type": content_type,
                    "word_count": len(content_result.split())
                },
                context_tags=["content", "writing"],
                relevance_score=0.8
            )
            
            self.log_execution(context, result)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=False,
                data={},
                message=f"Content creation failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.log_execution(context, result)
            return result
    
    async def _create_content_brief(self, query: str) -> Dict[str, Any]:
        """Create a content brief based on the query."""
        system_prompt = """
        You are a content strategist. Create a comprehensive content brief including:
        1. Content type (blog, article, guide, etc.)
        2. Target audience
        3. Main topic and subtopics
        4. SEO keywords
        5. Content structure outline
        6. Tone and style
        
        Respond in JSON format:
        {
            "type": "blog_post",
            "topic": "main topic",
            "audience": "target audience",
            "keywords": ["keyword1", "keyword2"],
            "outline": ["section1", "section2"],
            "tone": "professional",
            "word_count_target": 1000
        }
        """
        
        prompt = f"Create a content brief for: {query}"
        
        try:
            response = await api_manager.openai.chat_completion([
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ], model="gpt-4", max_tokens=2000, temperature=0.3)
            
            if response["success"]:
                return json.loads(response["content"])
            else:
                logger.error(f"Content brief creation failed: {response.get('error')}")
                return {
                    "type": "article",
                    "topic": query,
                    "audience": "general",
                    "keywords": query.split(),
                    "outline": ["Introduction", "Main Content", "Conclusion"],
                    "tone": "professional",
                    "word_count_target": 800
                }
        except Exception as e:
            self.logger.error(f"Content brief creation failed: {e}")
            return {
                "type": "article",
                "topic": query,
                "audience": "general",
                "keywords": query.split(),
                "outline": ["Introduction", "Main Content", "Conclusion"],
                "tone": "professional",
                "word_count_target": 800
            }
    
    async def save_output(self, filename: str, content):
        """Save content to file."""
        try:
            # Create uploads directory if it doesn't exist
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            filepath = os.path.join(upload_dir, filename)
            
            # Handle different content types
            if isinstance(content, dict):
                # Save as JSON
                import json
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
            else:
                # Save as text/markdown
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            
            logger.info(f"Content saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save content to {filename}: {str(e)}")
            json_filename = f"content_data_task_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            json_filepath = os.path.join(upload_dir, json_filename)
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            output_files.append(json_filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save content: {e}")
        
        return output_files
