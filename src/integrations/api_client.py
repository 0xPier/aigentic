"""
Centralized API client for third-party integrations.
Handles OpenAI, Twitter/X, Telegram, and image generation APIs.
"""

import asyncio
import aiohttp
import tweepy
import openai
from typing import Dict, List, Optional, Any, Union
from telegram import Bot
from telegram.error import TelegramError
import requests
from PIL import Image
import io
import base64
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API client for LLM operations."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.openai_api_key
        if self.api_key:
            openai.api_key = self.api_key
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using OpenAI API."""
        try:
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "usage": response.usage,
                "model": response.model
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        n: int = 1
    ) -> Dict[str, Any]:
        """Generate image using DALL-E."""
        try:
            response = await openai.Image.acreate(
                prompt=prompt,
                size=size,
                quality=quality,
                n=n
            )
            return {
                "success": True,
                "images": [img.url for img in response.data],
                "prompt": prompt
            }
        except Exception as e:
            logger.error(f"DALL-E API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "images": []
            }


class TwitterClient:
    """Twitter/X API client for social media operations."""
    
    def __init__(self, api_key: str = None, api_secret: str = None, 
                 access_token: str = None, access_token_secret: str = None):
        self.api_key = api_key or settings.twitter_api_key
        self.api_secret = api_secret or settings.twitter_api_secret
        self.access_token = access_token or settings.twitter_access_token
        self.access_token_secret = access_token_secret or settings.twitter_access_token_secret
        
        if all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
        else:
            self.client = None
            logger.warning("Twitter API credentials not configured")
    
    async def post_tweet(self, text: str, media_ids: List[str] = None) -> Dict[str, Any]:
        """Post a tweet to Twitter/X."""
        if not self.client:
            return {"success": False, "error": "Twitter API not configured"}
        
        try:
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids
            )
            return {
                "success": True,
                "tweet_id": response.data['id'],
                "text": text,
                "url": f"https://twitter.com/user/status/{response.data['id']}"
            }
        except Exception as e:
            logger.error(f"Twitter API error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_media(self, media_path: str) -> Optional[str]:
        """Upload media to Twitter and return media ID."""
        if not self.client:
            return None
        
        try:
            # Use tweepy v1 API for media upload
            auth = tweepy.OAuth1UserHandler(
                self.api_key, self.api_secret,
                self.access_token, self.access_token_secret
            )
            api = tweepy.API(auth)
            
            media = api.media_upload(media_path)
            return media.media_id_string
        except Exception as e:
            logger.error(f"Twitter media upload error: {str(e)}")
            return None
    
    async def get_user_tweets(self, username: str, max_results: int = 10) -> Dict[str, Any]:
        """Get recent tweets from a user."""
        if not self.client:
            return {"success": False, "error": "Twitter API not configured"}
        
        try:
            user = self.client.get_user(username=username)
            tweets = self.client.get_users_tweets(
                id=user.data.id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            return {
                "success": True,
                "tweets": [
                    {
                        "id": tweet.id,
                        "text": tweet.text,
                        "created_at": tweet.created_at.isoformat(),
                        "metrics": tweet.public_metrics
                    }
                    for tweet in tweets.data or []
                ]
            }
        except Exception as e:
            logger.error(f"Twitter get tweets error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class TelegramClient:
    """Telegram Bot API client."""
    
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or settings.telegram_bot_token
        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
        else:
            self.bot = None
            logger.warning("Telegram bot token not configured")
    
    async def send_message(
        self, 
        chat_id: Union[int, str], 
        text: str, 
        parse_mode: str = "HTML"
    ) -> Dict[str, Any]:
        """Send a message to a Telegram chat."""
        if not self.bot:
            return {"success": False, "error": "Telegram bot not configured"}
        
        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode
            )
            return {
                "success": True,
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "text": message.text
            }
        except TelegramError as e:
            logger.error(f"Telegram API error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_photo(
        self, 
        chat_id: Union[int, str], 
        photo_path: str, 
        caption: str = None
    ) -> Dict[str, Any]:
        """Send a photo to a Telegram chat."""
        if not self.bot:
            return {"success": False, "error": "Telegram bot not configured"}
        
        try:
            with open(photo_path, 'rb') as photo:
                message = await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption
                )
            return {
                "success": True,
                "message_id": message.message_id,
                "chat_id": message.chat_id
            }
        except Exception as e:
            logger.error(f"Telegram send photo error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_updates(self) -> Dict[str, Any]:
        """Get bot updates."""
        if not self.bot:
            return {"success": False, "error": "Telegram bot not configured"}
        
        try:
            updates = await self.bot.get_updates()
            return {
                "success": True,
                "updates": [
                    {
                        "update_id": update.update_id,
                        "message": {
                            "message_id": update.message.message_id if update.message else None,
                            "text": update.message.text if update.message else None,
                            "chat_id": update.message.chat_id if update.message else None,
                            "from_user": update.message.from_user.username if update.message and update.message.from_user else None
                        }
                    }
                    for update in updates
                ]
            }
        except Exception as e:
            logger.error(f"Telegram get updates error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class ImageGenerationClient:
    """Client for various image generation APIs."""
    
    def __init__(self):
        self.openai_client = OpenAIClient()
    
    async def generate_with_dalle(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate image using DALL-E."""
        return await self.openai_client.generate_image(prompt, **kwargs)
    
    async def generate_with_stability(
        self, 
        prompt: str, 
        api_key: str = None,
        model: str = "stable-diffusion-xl-1024-v1-0"
    ) -> Dict[str, Any]:
        """Generate image using Stability AI."""
        api_key = api_key or settings.stability_api_key
        if not api_key:
            return {"success": False, "error": "Stability AI API key not configured"}
        
        try:
            url = f"https://api.stability.ai/v1/generation/{model}/text-to-image"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            body = {
                "text_prompts": [{"text": prompt}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30,
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body) as response:
                    if response.status == 200:
                        data = await response.json()
                        images = []
                        for artifact in data.get("artifacts", []):
                            if artifact.get("base64"):
                                images.append(artifact["base64"])
                        
                        return {
                            "success": True,
                            "images": images,
                            "prompt": prompt,
                            "format": "base64"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Stability AI API error: {error_text}"
                        }
        except Exception as e:
            logger.error(f"Stability AI error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class APIClientManager:
    """Centralized manager for all API clients."""
    
    def __init__(self):
        self.openai = OpenAIClient()
        self.twitter = TwitterClient()
        self.telegram = TelegramClient()
        self.image_gen = ImageGenerationClient()
    
    def get_client(self, service: str):
        """Get a specific API client."""
        clients = {
            "openai": self.openai,
            "twitter": self.twitter,
            "telegram": self.telegram,
            "image_generation": self.image_gen
        }
        return clients.get(service.lower())
    
    async def test_connections(self) -> Dict[str, bool]:
        """Test all API connections."""
        results = {}
        
        # Test OpenAI
        try:
            test_response = await self.openai.chat_completion([
                {"role": "user", "content": "Hello"}
            ])
            results["openai"] = test_response["success"]
        except:
            results["openai"] = False
        
        # Test Twitter
        try:
            if self.twitter.client:
                # Simple API test
                results["twitter"] = True
            else:
                results["twitter"] = False
        except:
            results["twitter"] = False
        
        # Test Telegram
        try:
            if self.telegram.bot:
                # Simple bot info test
                results["telegram"] = True
            else:
                results["telegram"] = False
        except:
            results["telegram"] = False
        
        return results


# Global API client manager instance
api_manager = APIClientManager()
