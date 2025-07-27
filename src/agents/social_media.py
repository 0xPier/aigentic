"""Social Media Agent for X/Twitter and Telegram management."""

import tweepy
from telegram import Bot
from typing import Dict, Any, List
from datetime import datetime
import json
import asyncio
import logging

from src.agents.base import LLMAgent, AgentContext, AgentResult
from src.core.config import settings
from src.integrations.api_client import api_manager

logger = logging.getLogger(__name__)

class SocialMediaAgent(LLMAgent):
    """Agent specialized in social media management and automation."""
    
    def __init__(self):
        super().__init__(
            name="social_media",
            description="Manages X/Twitter and Telegram: posting, engagement, analytics",
            capabilities=[
                "twitter_posting",
                "telegram_management",
                "social_engagement",
                "content_scheduling",
                "analytics_tracking"
            ]
        )
        self._twitter_client = None
        self._telegram_bot = None
    
    def get_required_integrations(self) -> List[str]:
        """Social media agent requires Twitter and Telegram integrations."""
        return ["twitter", "telegram"]
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute social media task."""
        start_time = datetime.utcnow()
        
        try:
            # Parse social media requirements
            social_spec = await self._parse_social_requirements(context.query)
            
            # Initialize clients
            await self._initialize_clients()
            
            # Execute social media actions
            results = await self._execute_social_actions(social_spec, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=True,
                data={
                    "social_spec": social_spec,
                    "execution_results": results,
                    "platforms_used": list(results.keys()),
                    "posts_created": sum(len(r.get("posts", [])) for r in results.values())
                },
                message="Social media tasks completed successfully",
                execution_time=execution_time
            )
            
            # Save to memory
            self.save_memory(
                memory_type="social_media",
                content={
                    "platforms": list(results.keys()),
                    "actions": social_spec.get("actions", []),
                    "success_count": len([r for r in results.values() if r.get("success")])
                },
                context_tags=["social_media", "automation"],
                relevance_score=0.8
            )
            
            self.log_execution(context, result)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=False,
                data={},
                message=f"Social media task failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.log_execution(context, result)
            return result
    
    async def _parse_social_requirements(self, query: str) -> Dict[str, Any]:
        """Parse social media requirements from query."""
        system_prompt = """
        You are a social media expert. Parse the requirements and determine:
        1. Platforms to use (twitter, telegram)
        2. Actions to perform (post, schedule, engage, analyze)
        3. Content type (text, image, video, poll)
        4. Timing and frequency
        5. Target audience
        
        Respond in JSON format:
        {
            "platforms": ["twitter", "telegram"],
            "actions": ["post", "schedule"],
            "content_type": "text",
            "timing": "immediate",
            "audience": "general",
            "content_requirements": "engaging social media content"
        }
        """
        
        prompt = f"Parse social media requirements for: {query}"
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Social media parsing failed: {e}")
            return {
                "platforms": ["twitter"],
                "actions": ["post"],
                "content_type": "text",
                "timing": "immediate",
                "audience": "general",
                "content_requirements": query
            }
    
    async def _initialize_clients(self):
        """Initialize social media API clients."""
        try:
            # Initialize Twitter client
            if settings.twitter_api_key and settings.twitter_api_secret:
                auth = tweepy.OAuthHandler(
                    settings.twitter_api_key,
                    settings.twitter_api_secret
                )
                if settings.twitter_access_token and settings.twitter_access_token_secret:
                    auth.set_access_token(
                        settings.twitter_access_token,
                        settings.twitter_access_token_secret
                    )
                self._twitter_client = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Initialize Telegram bot
            if settings.telegram_bot_token:
                self._telegram_bot = Bot(token=settings.telegram_bot_token)
                
        except Exception as e:
            self.logger.error(f"Failed to initialize social media clients: {e}")
    
    async def _execute_social_actions(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Execute social media actions based on specification."""
        results = {}
        
        for platform in spec.get("platforms", []):
            try:
                if platform == "twitter":
                    results["twitter"] = await self._handle_twitter_actions(spec, context)
                elif platform == "telegram":
                    results["telegram"] = await self._handle_telegram_actions(spec, context)
                    
            except Exception as e:
                results[platform] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    async def _handle_twitter_actions(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Handle Twitter-specific actions."""
        if not self._twitter_client:
            return {
                "success": False,
                "error": "Twitter client not initialized - check API credentials"
            }
        
        results = {"success": True, "posts": [], "actions": []}
        
        try:
            for action in spec.get("actions", []):
                if action == "post":
                    # Generate content for posting
                    content = await self._generate_social_content(
                        platform="twitter",
                        requirements=spec.get("content_requirements", ""),
                        context=context
                    )
                    
                    # Post to Twitter using real API
                    post_result = await self._post_to_twitter(content)
                    results["posts"].append(post_result)
                    
                elif action == "analyze":
                    # Get analytics (real implementation)
                    analytics = await self._get_twitter_analytics()
                    results["analytics"] = analytics
                
                results["actions"].append(action)
                
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
        
        return results
    
    async def _handle_telegram_actions(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Handle Telegram-specific actions."""
        if not self._telegram_bot:
            return {
                "success": False,
                "error": "Telegram bot not initialized - check bot token"
            }
        
        results = {"success": True, "posts": [], "actions": []}
        
        try:
            for action in spec.get("actions", []):
                if action == "post":
                    # Generate content for Telegram
                    content = await self._generate_social_content(
                        platform="telegram",
                        requirements=spec.get("content_requirements", ""),
                        context=context
                    )
                    
                    # Post to Telegram using real API
                    post_result = await self._post_to_telegram(content)
                    results["posts"].append(post_result)
                
                results["actions"].append(action)
                
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
        
        return results
    
    async def _generate_social_content(self, platform: str, requirements: str, context: AgentContext) -> str:
        """Generate content optimized for specific social media platform."""
        char_limits = {
            "twitter": 280,
            "telegram": 4096
        }
        
        system_prompt = f"""
        You are a social media content creator. Create engaging content for {platform}.
        
        Platform guidelines:
        - Character limit: {char_limits.get(platform, 280)}
        - Use appropriate hashtags and mentions
        - Make it engaging and shareable
        - Include call-to-action if appropriate
        
        Content should be:
        - Concise and impactful
        - Relevant to the audience
        - Professional yet engaging
        """
        
        prompt = f"""
        Create {platform} content for: {requirements}
        
        Context: {context.query}
        
        Make it engaging and platform-appropriate.
        """
        
        try:
            content = await self.call_llm(prompt, system_prompt, temperature=0.7, max_tokens=200)
            
            # Ensure content fits platform limits
            max_length = char_limits.get(platform, 280)
            if len(content) > max_length:
                content = content[:max_length-3] + "..."
            
            return content.strip()
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            return f"Check out our latest update! #{platform} #automation"
    
    async def _post_to_twitter(self, content: str, media_files: List[str] = None) -> Dict[str, Any]:
        """Post content to Twitter/X using real API."""
        try:
            media_ids = []
            
            # Upload media files if provided
            if media_files:
                for media_file in media_files:
                    media_id = await api_manager.twitter.upload_media(media_file)
                    if media_id:
                        media_ids.append(media_id)
                    else:
                        logger.warning(f"Failed to upload media: {media_file}")
            
            # Post tweet
            result = await api_manager.twitter.post_tweet(
                text=content,
                media_ids=media_ids if media_ids else None
            )
            
            if result["success"]:
                return {
                    "platform": "twitter",
                    "post_id": result["tweet_id"],
                    "url": result["url"],
                    "content": content,
                    "media_count": len(media_ids),
                    "posted_at": datetime.now().isoformat(),
                    "status": "posted"
                }
            else:
                logger.error(f"Twitter posting failed: {result.get('error')}")
                return {
                    "platform": "twitter",
                    "post_id": None,
                    "url": None,
                    "content": content,
                    "media_count": 0,
                    "posted_at": datetime.now().isoformat(),
                    "status": "failed",
                    "error": result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Twitter posting error: {str(e)}")
            return {
                "platform": "twitter",
                "post_id": None,
                "url": None,
                "content": content,
                "media_count": 0,
                "posted_at": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def _post_to_telegram(self, content: str) -> Dict[str, Any]:
        """Post content to Telegram using real API."""
        try:
            # Post to Telegram
            result = await api_manager.telegram.post_message(
                chat_id="@your_channel",
                text=content
            )
            
            if result["success"]:
                return {
                    "platform": "telegram",
                    "post_id": result["message_id"],
                    "url": result["url"],
                    "content": content,
                    "posted_at": datetime.now().isoformat(),
                    "status": "posted"
                }
            else:
                logger.error(f"Telegram posting failed: {result.get('error')}")
                return {
                    "platform": "telegram",
                    "post_id": None,
                    "url": None,
                    "content": content,
                    "posted_at": datetime.now().isoformat(),
                    "status": "failed",
                    "error": result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Telegram posting error: {str(e)}")
            return {
                "platform": "telegram",
                "post_id": None,
                "url": None,
                "content": content,
                "posted_at": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def _get_twitter_analytics(self) -> Dict[str, Any]:
        """Get Twitter analytics (real implementation)."""
        # Use Twitter API v2 for analytics
        result = await api_manager.twitter.get_analytics()
        
        if result["success"]:
            return result["analytics"]
        else:
            logger.error(f"Twitter analytics failed: {result.get('error')}")
            return {
                "followers_count": 0,
                "tweets_count": 0,
                "engagement_rate": 0,
                "impressions": 0,
                "profile_visits": 0,
                "mentions": 0
            }
