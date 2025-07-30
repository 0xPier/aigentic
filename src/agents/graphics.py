"""Graphics Creation Agent for image and poster generation."""

from PIL import Image, ImageDraw, ImageFont
import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os
import base64
import io
import logging

from .base import LLMAgent, AgentContext, AgentResult
from ..integrations.api_client import api_manager
from src.core.config import app_config


class GraphicsAgent(LLMAgent):
    """Agent specialized in graphics and image creation."""
    
    def __init__(self):
        super().__init__(
            name="graphics",
            description="Generates images, posters, and visual content using AI and design tools",
            capabilities=[
                "image_generation",
                "poster_creation",
                "logo_design",
                "social_media_graphics",
                "infographic_creation"
            ]
        )
    
    def get_required_integrations(self) -> List[str]:
        """Graphics agent may use Stability AI or other image generation APIs."""
        return ["stability_ai", "huggingface"]
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute graphics creation task."""
        start_time = datetime.utcnow()
        
        try:
            # Parse graphics requirements
            graphics_spec = await self._parse_graphics_requirements(context.query)
            
            # Generate graphics based on specification
            generated_graphics = await self._generate_graphics(graphics_spec, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=True,
                data={
                    "graphics_spec": graphics_spec,
                    "generated_graphics": generated_graphics,
                    "total_images": len(generated_graphics.get("images", [])),
                    "formats": graphics_spec.get("formats", ["PNG"])
                },
                message="Graphics created successfully",
                execution_time=execution_time,
                output_files=generated_graphics.get("file_paths", [])
            )
            
            # Save to memory
            self.save_memory(
                memory_type="graphics",
                content={
                    "type": graphics_spec.get("type", "image"),
                    "style": graphics_spec.get("style", "modern"),
                    "images_created": len(generated_graphics.get("images", []))
                },
                context_tags=["graphics", "design"],
                relevance_score=0.8
            )
            
            self.log_execution(context, result)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=False,
                data={},
                message=f"Graphics creation failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.log_execution(context, result)
            return result
    
    async def _parse_graphics_requirements(self, query: str) -> Dict[str, Any]:
        """Parse graphics requirements from query."""
        system_prompt = """
        You are a graphic design expert. Parse the requirements and determine:
        1. Type of graphic (poster, logo, social media post, infographic, etc.)
        2. Style and theme (modern, vintage, minimalist, corporate, etc.)
        3. Color scheme preferences
        4. Text content to include
        5. Dimensions and format
        6. Target audience
        
        Respond in JSON format:
        {
            "type": "poster",
            "style": "modern",
            "colors": ["blue", "white"],
            "text_content": "Main headline and description",
            "dimensions": "1080x1080",
            "format": "PNG",
            "audience": "business professionals"
        }
        """
        
        prompt = f"Parse graphics requirements for: {query}"
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Graphics parsing failed: {e}")
            return {
                "type": "poster",
                "style": "modern",
                "colors": ["blue", "white"],
                "text_content": query,
                "dimensions": "1080x1080",
                "format": "PNG",
                "audience": "general"
            }
    
    async def _generate_graphics(self, spec: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Generate graphics based on specification."""
        results = {"images": [], "file_paths": []}
        
        try:
            # Create upload directory
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            graphic_type = spec.get("type", "poster")
            
            if graphic_type in ["poster", "social_media_post"]:
                image_path = await self._create_poster(spec, context)
                if image_path:
                    results["file_paths"].append(image_path)
                    results["images"].append({
                        "type": graphic_type,
                        "path": image_path,
                        "dimensions": spec.get("dimensions", "1080x1080")
                    })
            
            elif graphic_type == "logo":
                image_path = await self._create_logo(spec, context)
                if image_path:
                    results["file_paths"].append(image_path)
                    results["images"].append({
                        "type": "logo",
                        "path": image_path,
                        "dimensions": spec.get("dimensions", "512x512")
                    })
            
            elif graphic_type == "infographic":
                image_path = await self._create_infographic(spec, context)
                if image_path:
                    results["file_paths"].append(image_path)
                    results["images"].append({
                        "type": "infographic",
                        "path": image_path,
                        "dimensions": spec.get("dimensions", "800x1200")
                    })
            
            # Try AI image generation if API keys are available
            if app_config.stability_api_key or app_config.huggingface_api_key:
                ai_image_result = await self._generate_ai_image(spec.get("text_content", ""), spec.get("style", "modern"))
                if ai_image_result:
                    results["file_paths"].append(ai_image_result["filepath"])
                    results["images"].append({
                        "type": ai_image_result["type"],
                        "path": ai_image_result["filepath"],
                        "dimensions": ai_image_result["dimensions"]
                    })
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Graphics generation failed: {e}")
            results["error"] = str(e)
        
        return results
    
    async def _create_poster(self, spec: Dict[str, Any], context: AgentContext) -> str:
        """Create a poster using PIL."""
        try:
            # Parse dimensions
            dimensions = spec.get("dimensions", "1080x1080")
            width, height = map(int, dimensions.split("x"))
            
            # Create image
            colors = spec.get("colors", ["#3498db", "#ffffff"])
            bg_color = colors[0] if colors else "#3498db"
            text_color = colors[1] if len(colors) > 1 else "#ffffff"
            
            image = Image.new("RGB", (width, height), bg_color)
            draw = ImageDraw.Draw(image)
            
            # Add text content
            text_content = spec.get("text_content", "Your Content Here")
            
            try:
                # Try to use a better font
                font_size = min(width, height) // 20
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Calculate text position (centered)
            bbox = draw.textbbox((0, 0), text_content, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw text
            draw.text((x, y), text_content, fill=text_color, font=font)
            
            # Add decorative elements
            self._add_design_elements(draw, width, height, colors)
            
            # Save image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"poster_{timestamp}.png"
            filepath = os.path.join("uploads", filename)
            
            image.save(filepath, "PNG")
            return filepath
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Poster creation failed: {e}")
            return None
    
    async def _create_logo(self, spec: Dict[str, Any], context: AgentContext) -> str:
        """Create a simple logo using PIL."""
        try:
            # Parse dimensions
            dimensions = spec.get("dimensions", "512x512")
            width, height = map(int, dimensions.split("x"))
            
            # Create image with transparent background
            image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Get colors
            colors = spec.get("colors", ["#2c3e50"])
            primary_color = colors[0] if colors else "#2c3e50"
            
            # Create simple geometric logo
            center_x, center_y = width // 2, height // 2
            radius = min(width, height) // 4
            
            # Draw circle
            draw.ellipse([
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius
            ], fill=primary_color)
            
            # Add text if specified
            text_content = spec.get("text_content", "LOGO")[:4]  # Limit to 4 chars
            if text_content:
                try:
                    font_size = radius // 2
                    font = ImageFont.truetype("/System/Library/Fonts/Arial Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), text_content, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                text_x = center_x - text_width // 2
                text_y = center_y - text_height // 2
                
                draw.text((text_x, text_y), text_content, fill="white", font=font)
            
            # Save image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logo_{timestamp}.png"
            filepath = os.path.join("uploads", filename)
            
            image.save(filepath, "PNG")
            return filepath
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Logo creation failed: {e}")
            return None
    
    async def _create_infographic(self, spec: Dict[str, Any], context: AgentContext) -> str:
        """Create a simple infographic using PIL."""
        try:
            # Parse dimensions
            dimensions = spec.get("dimensions", "800x1200")
            width, height = map(int, dimensions.split("x"))
            
            # Create image
            colors = spec.get("colors", ["#ecf0f1", "#3498db"])
            bg_color = colors[0] if colors else "#ecf0f1"
            accent_color = colors[1] if len(colors) > 1 else "#3498db"
            
            image = Image.new("RGB", (width, height), bg_color)
            draw = ImageDraw.Draw(image)
            
            # Add title
            title = spec.get("text_content", "Infographic Title")
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except IOError:
                title_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
            
            # Draw title
            bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = bbox[2] - bbox[0]
            title_x = (width - title_width) // 2
            draw.text((title_x, 50), title, fill=accent_color, font=title_font)
            
            # Add some data visualization elements
            self._add_infographic_elements(draw, width, height, accent_color)
            
            # Save image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"infographic_{timestamp}.png"
            filepath = os.path.join("uploads", filename)
            
            image.save(filepath, "PNG")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Infographic creation failed: {e}")
            return None
    
    def _add_design_elements(self, draw: ImageDraw.Draw, width: int, height: int, colors: List[str]):
        """Add decorative design elements."""
        try:
            accent_color = colors[1] if len(colors) > 1 else "#ffffff"
            
            # Add corner decorations
            corner_size = min(width, height) // 20
            
            # Top-left corner
            draw.rectangle([0, 0, corner_size, corner_size], fill=accent_color)
            
            # Bottom-right corner
            draw.rectangle([
                width - corner_size, height - corner_size,
                width, height
            ], fill=accent_color)
            
        except Exception as e:
            self.logger.error(f"Design elements failed: {e}")
    
    def _add_infographic_elements(self, draw: ImageDraw.Draw, width: int, height: int, color: str):
        """Add infographic visualization elements."""
        try:
            # Add some bars for data visualization
            bar_width = width // 6
            bar_spacing = width // 8
            
            for i in range(3):
                x = bar_spacing + i * (bar_width + bar_spacing)
                bar_height = (i + 1) * 80 + 50
                y = height - 200 - bar_height
                
                # Draw bar
                draw.rectangle([x, y, x + bar_width, height - 200], fill=color)
                
                # Add percentage label
                percentage = f"{(i + 1) * 25}%"
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
                except:
                    font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), percentage, font=font)
                text_width = bbox[2] - bbox[0]
                text_x = x + (bar_width - text_width) // 2
                draw.text((text_x, height - 180), percentage, fill=color, font=font)
            
        except Exception as e:
            self.logger.error(f"Infographic elements failed: {e}")
    
    async def _generate_ai_image(self, spec: Dict[str, Any], context: AgentContext) -> str:
        """Generate image using AI (Stability AI or similar)."""
        # This is a placeholder for AI image generation
        # In production, integrate with Stability AI, DALL-E, or similar services
        
        try:
            # Create a prompt for AI image generation
            prompt = await self._create_ai_prompt(spec, context)
            
            # Mock AI generation (replace with actual API call)
            self.logger.info(f"Would generate AI image with prompt: {prompt}")
            
            # For now, return None (no AI image generated)
            return None
            
        except Exception as e:
            self.logger.error(f"AI image generation failed: {e}")
            return None
    
    async def _create_ai_prompt(self, spec: Dict[str, Any], context: AgentContext) -> str:
        """Create a prompt for AI image generation."""
        style = spec.get("style", "modern")
        colors = ", ".join(spec.get("colors", ["blue", "white"]))
        content = spec.get("text_content", "")
        
        prompt = f"Create a {style} style {spec.get('type', 'image')} with {colors} colors"
        if content:
            prompt += f" featuring {content}"
        
        prompt += ", high quality, professional design"
        
        return prompt
