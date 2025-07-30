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

from src.core.config import app_config

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API client for LLM operations."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or app_config.openai_api_key
        if not self.api_key:
            logger.warning("OpenAI API key not configured. OpenAI features may not work.")
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
        self.api_key = api_key or app_config.twitter_api_key
        self.api_secret = api_secret or app_config.twitter_api_secret
        self.access_token = access_token or app_config.twitter_access_token
        self.access_token_secret = access_token_secret or app_config.twitter_access_token_secret
        
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
        self.bot_token = bot_token or app_config.telegram_bot_token
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
        api_key = api_key or app_config.stability_api_key
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


class OllamaClient:
    """Ollama API client for local LLM operations."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or app_config.ollama_base_url
        if not self.base_url:
            logger.warning("Ollama base URL not configured. Ollama features may not work.")
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion using Ollama API."""
        try:
            if not self.base_url:
                raise ValueError("Ollama base URL not configured")
            
            model = model or app_config.ollama_model
            
            # Convert messages to Ollama format (single prompt)
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "content": data.get("response", ""),
                            "model": model,
                            "done": data.get("done", False)
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API returned status {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models in Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "models": data.get("models", [])
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to list models: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "models": []
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Ollama connection."""
        try:
            # First try to list models
            models_result = await self.list_models()
            if not models_result["success"]:
                return {"success": False, "error": "Failed to connect to Ollama"}
            
            # If models available, try a simple chat completion
            if models_result["models"]:
                test_response = await self.chat_completion(
                    [{"role": "user", "content": "Hello"}],
                    max_tokens=10
                )
                return {
                    "success": test_response["success"],
                    "error": test_response.get("error"),
                    "models_available": len(models_result["models"])
                }
            else:
                return {
                    "success": True,
                    "error": "No models available in Ollama",
                    "models_available": 0
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class APIClientManager:
    """Centralized manager for all API clients."""
    
    def __init__(self):
        self.openai = OpenAIClient()
        self.ollama = OllamaClient()
        self.twitter = TwitterClient()
        self.telegram = TelegramClient()
        self.image_gen = ImageGenerationClient()
    
    def get_client(self, service: str):
        """Get a specific API client."""
        clients = {
            "openai": self.openai,
            "ollama": self.ollama,
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
            if self.openai.api_key:
                test_response = await self.openai.chat_completion([
                    {"role": "user", "content": "Hello"}
                ], model="gpt-3.5-turbo", max_tokens=10)
                results["openai"] = test_response["success"]
            else:
                results["openai"] = False
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            results["openai"] = False
        
        # Test Ollama
        try:
            ollama_result = await self.ollama.test_connection()
            results["ollama"] = ollama_result["success"]
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            results["ollama"] = False
        
        # Test Twitter
        try:
            if self.twitter.client:
                # Attempt to get user info (non-destructive)
                user_info = await self.twitter.get_user_tweets(username="twitterdev", max_results=1)
                results["twitter"] = user_info["success"]
            else:
                results["twitter"] = False
        except Exception as e:
            logger.error(f"Twitter connection test failed: {e}")
            results["twitter"] = False
        
        # Test Telegram
        try:
            if self.telegram.bot:
                # Attempt to get bot info (non-destructive)
                bot_info = await self.telegram.bot.get_me()
                results["telegram"] = True
            else:
                results["telegram"] = False
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            results["telegram"] = False
        
        return results


# Global API client manager instance
api_manager = APIClientManager()
