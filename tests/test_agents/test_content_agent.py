"""
Unit tests for the Content Agent.
Tests content generation, SEO optimization, and content management functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import json
import os

from src.agents.content import ContentAgent
from src.agents.base import AgentContext, AgentResult


class TestContentAgent:
    """Test Content Agent functionality."""
    
    def test_content_agent_initialization(self):
        """Test content agent initialization."""
        agent = ContentAgent()
        
        assert agent.name == "content"
        assert "content" in agent.description.lower()
        assert agent.memory_enabled is True
    
    @pytest.mark.asyncio
    async def test_successful_content_generation(self, mock_agent_context, mock_openai_client):
        """Test successful content generation with OpenAI."""
        agent = ContentAgent()
        mock_agent_context.query = "Write a blog post about sustainable technology"
        mock_agent_context.parameters = {
            "content_type": "blog_post",
            "target_audience": "tech professionals",
            "tone": "professional"
        }
        
        with patch('src.agents.content.api_manager') as mock_api_manager, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            # Mock OpenAI responses
            mock_api_manager.openai.chat_completion = AsyncMock(side_effect=[
                {
                    "success": True,
                    "content": json.dumps({
                        "content_type": "blog_post",
                        "target_audience": "tech professionals",
                        "tone": "professional",
                        "keywords": ["sustainable technology", "green tech", "innovation"]
                    }),
                    "usage": {"total_tokens": 100}
                },
                {
                    "success": True,
                    "content": "# Sustainable Technology: The Future of Innovation\n\nSustainable technology represents a paradigm shift...",
                    "usage": {"total_tokens": 500}
                },
                {
                    "success": True,
                    "content": json.dumps({
                        "title_suggestions": ["Sustainable Tech Revolution", "Green Innovation Today"],
                        "meta_description": "Explore sustainable technology trends and innovations",
                        "keywords": ["sustainable technology", "green innovation"],
                        "readability_score": 85,
                        "seo_recommendations": ["Add more internal links", "Optimize images"]
                    }),
                    "usage": {"total_tokens": 200}
                }
            ])
            
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Verify result structure
            assert result.success is True
            assert "content" in result.data
            assert "seo_analysis" in result.data
            assert "metadata" in result.data
            assert result.execution_time > 0
            
            # Verify content quality
            content_data = result.data["content"]
            assert "markdown_content" in content_data
            assert "word_count" in content_data
            assert content_data["word_count"] > 0
            
            # Verify SEO analysis
            seo_data = result.data["seo_analysis"]
            assert "title_suggestions" in seo_data
            assert "meta_description" in seo_data
            assert "keywords" in seo_data
    
    @pytest.mark.asyncio
    async def test_content_parsing_and_analysis(self, mock_agent_context):
        """Test content request parsing and analysis."""
        agent = ContentAgent()
        mock_agent_context.query = "Create a technical whitepaper about blockchain security for enterprise clients"
        
        with patch('src.agents.content.api_manager') as mock_api_manager:
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": True,
                "content": json.dumps({
                    "content_type": "whitepaper",
                    "target_audience": "enterprise clients",
                    "tone": "technical",
                    "keywords": ["blockchain", "security", "enterprise"],
                    "estimated_length": "long_form"
                }),
                "usage": {"total_tokens": 150}
            })
            
            parsed = await agent._parse_content_request(mock_agent_context.query)
            
            # Verify parsing results
            assert parsed["content_type"] == "whitepaper"
            assert parsed["target_audience"] == "enterprise clients"
            assert parsed["tone"] == "technical"
            assert "blockchain" in parsed["keywords"]
            assert "security" in parsed["keywords"]
    
    @pytest.mark.asyncio
    async def test_content_generation_with_different_types(self, mock_agent_context):
        """Test content generation for different content types."""
        agent = ContentAgent()
        
        test_cases = [
            {
                "query": "Write a social media post about AI trends",
                "expected_type": "social_media",
                "expected_length": "short"
            },
            {
                "query": "Create an email newsletter about product updates",
                "expected_type": "email",
                "expected_length": "medium"
            },
            {
                "query": "Draft a comprehensive guide on machine learning",
                "expected_type": "guide",
                "expected_length": "long_form"
            }
        ]
        
        with patch('src.agents.content.api_manager') as mock_api_manager, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            for case in test_cases:
                mock_agent_context.query = case["query"]
                
                # Mock parsing response
                mock_api_manager.openai.chat_completion = AsyncMock(side_effect=[
                    {
                        "success": True,
                        "content": json.dumps({
                            "content_type": case["expected_type"],
                            "target_audience": "general",
                            "tone": "professional",
                            "keywords": ["test"],
                            "estimated_length": case["expected_length"]
                        }),
                        "usage": {"total_tokens": 100}
                    },
                    {
                        "success": True,
                        "content": f"Generated {case['expected_type']} content...",
                        "usage": {"total_tokens": 300}
                    },
                    {
                        "success": True,
                        "content": json.dumps({
                            "title_suggestions": ["Test Title"],
                            "meta_description": "Test description",
                            "keywords": ["test"],
                            "readability_score": 80,
                            "seo_recommendations": ["Test recommendation"]
                        }),
                        "usage": {"total_tokens": 150}
                    }
                ])
                
                result = await agent.execute_with_context(mock_agent_context)
                
                # Verify content type specific results
                assert result.success is True
                assert case["expected_type"] in result.data["metadata"]["content_type"]
    
    @pytest.mark.asyncio
    async def test_seo_optimization(self, mock_agent_context):
        """Test SEO optimization functionality."""
        agent = ContentAgent()
        
        test_content = """
        # Artificial Intelligence in Healthcare
        
        Artificial intelligence is transforming healthcare through innovative applications.
        Machine learning algorithms help doctors diagnose diseases more accurately.
        AI-powered systems can analyze medical images and predict patient outcomes.
        """
        
        with patch('src.agents.content.api_manager') as mock_api_manager:
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": True,
                "content": json.dumps({
                    "title_suggestions": [
                        "AI in Healthcare: Transforming Medical Diagnosis",
                        "How Artificial Intelligence is Revolutionizing Healthcare",
                        "The Future of Healthcare: AI-Powered Medical Solutions"
                    ],
                    "meta_description": "Discover how artificial intelligence is transforming healthcare through innovative applications in medical diagnosis and patient care.",
                    "keywords": ["artificial intelligence", "healthcare", "medical diagnosis", "machine learning"],
                    "readability_score": 78,
                    "seo_recommendations": [
                        "Add more subheadings for better structure",
                        "Include internal links to related content",
                        "Optimize images with alt text",
                        "Add FAQ section for better user engagement"
                    ],
                    "keyword_density": {
                        "artificial intelligence": 2.5,
                        "healthcare": 3.1,
                        "medical": 1.8
                    }
                }),
                "usage": {"total_tokens": 250}
            })
            
            seo_analysis = await agent._optimize_for_seo(test_content, ["AI", "healthcare"])
            
            # Verify SEO analysis
            assert "title_suggestions" in seo_analysis
            assert "meta_description" in seo_analysis
            assert "keywords" in seo_analysis
            assert "readability_score" in seo_analysis
            assert "seo_recommendations" in seo_analysis
            
            # Verify quality of suggestions
            assert len(seo_analysis["title_suggestions"]) >= 3
            assert len(seo_analysis["meta_description"]) > 50
            assert seo_analysis["readability_score"] > 0
    
    @pytest.mark.asyncio
    async def test_content_saving_functionality(self, mock_agent_context, tmp_path):
        """Test content saving to file system."""
        agent = ContentAgent()
        
        # Mock the uploads directory
        uploads_dir = tmp_path / "uploads"
        uploads_dir.mkdir()
        
        content_data = {
            "markdown_content": "# Test Content\n\nThis is test content.",
            "word_count": 50,
            "estimated_reading_time": 1
        }
        
        seo_data = {
            "title_suggestions": ["Test Title"],
            "meta_description": "Test description",
            "keywords": ["test"]
        }
        
        with patch('os.makedirs'), \
             patch('builtins.open', create=True) as mock_open:
            
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = await agent._save_content_output(content_data, seo_data, "blog_post")
            
            # Verify file operations
            assert mock_open.call_count == 2  # Markdown and JSON files
            assert result["markdown_file"].endswith(".md")
            assert result["json_file"].endswith(".json")
            
            # Verify content was written
            mock_file.write.assert_called()
    
    @pytest.mark.asyncio
    async def test_content_generation_fallback(self, mock_agent_context):
        """Test content generation fallback when OpenAI fails."""
        agent = ContentAgent()
        mock_agent_context.query = "Write a blog post about technology"
        
        with patch('src.agents.content.api_manager') as mock_api_manager, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            # Mock OpenAI failure
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": False,
                "error": "API Error"
            })
            
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Should provide fallback content
            assert result.success is True
            assert "content" in result.data
            assert "fallback" in result.data["content"]["markdown_content"].lower()
    
    @pytest.mark.asyncio
    async def test_content_with_memory_integration(self, mock_agent_context, db_session):
        """Test content generation with memory integration."""
        agent = ContentAgent()
        mock_agent_context.query = "Write about artificial intelligence"
        
        # Mock previous content memory
        mock_memories = [
            {
                "id": 1,
                "memory_type": "success",
                "content": {
                    "execution_summary": {
                        "task_type": "content",
                        "summary": "Previous AI content generated successfully"
                    }
                },
                "context_tags": ["content", "artificial_intelligence"],
                "relevance_score": 0.9
            }
        ]
        
        with patch('src.agents.base.memory_manager') as mock_memory, \
             patch('src.agents.content.api_manager') as mock_api_manager:
            
            mock_memory.retrieve_memories = AsyncMock(return_value=mock_memories)
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            # Mock successful content generation
            mock_api_manager.openai.chat_completion = AsyncMock(side_effect=[
                {
                    "success": True,
                    "content": json.dumps({
                        "content_type": "blog_post",
                        "target_audience": "general",
                        "tone": "professional",
                        "keywords": ["AI"]
                    }),
                    "usage": {"total_tokens": 100}
                },
                {
                    "success": True,
                    "content": "# AI Content\n\nGenerated content about AI...",
                    "usage": {"total_tokens": 300}
                },
                {
                    "success": True,
                    "content": json.dumps({
                        "title_suggestions": ["AI Title"],
                        "meta_description": "AI description",
                        "keywords": ["AI"],
                        "readability_score": 85,
                        "seo_recommendations": ["Add links"]
                    }),
                    "usage": {"total_tokens": 150}
                }
            ])
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Verify memory was loaded and used
            assert len(agent.learning_context) == 1
            assert result.success is True
            
            # Verify new memory was stored
            mock_memory.store_memory.assert_called()
    
    @pytest.mark.asyncio
    async def test_content_performance_tracking(self, mock_agent_context, performance_timer):
        """Test content generation performance tracking."""
        agent = ContentAgent()
        mock_agent_context.query = "Quick content generation test"
        
        with patch('src.agents.content.api_manager') as mock_api_manager, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            # Setup quick mocks
            mock_api_manager.openai.chat_completion = AsyncMock(side_effect=[
                {
                    "success": True,
                    "content": json.dumps({"content_type": "blog_post", "tone": "casual", "keywords": ["test"]}),
                    "usage": {"total_tokens": 50}
                },
                {
                    "success": True,
                    "content": "Quick test content",
                    "usage": {"total_tokens": 100}
                },
                {
                    "success": True,
                    "content": json.dumps({"title_suggestions": ["Test"], "meta_description": "Test", "keywords": ["test"], "readability_score": 80, "seo_recommendations": []}),
                    "usage": {"total_tokens": 75}
                }
            ])
            
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            performance_timer.start()
            result = await agent.execute_with_context(mock_agent_context)
            performance_timer.stop()
            
            # Verify performance tracking
            assert result.execution_time > 0
            assert result.execution_time <= performance_timer.elapsed_seconds + 1
            assert agent.performance_metrics["total_executions"] == 1
            assert agent.performance_metrics["successful_executions"] == 1
    
    @pytest.mark.asyncio
    async def test_content_error_handling(self, mock_agent_context):
        """Test content generation error handling."""
        agent = ContentAgent()
        mock_agent_context.query = "Generate content with error"
        
        with patch('src.agents.content.api_manager') as mock_api_manager, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            # Simulate parsing success but generation failure
            mock_api_manager.openai.chat_completion = AsyncMock(side_effect=[
                {
                    "success": True,
                    "content": json.dumps({"content_type": "blog_post", "tone": "professional", "keywords": ["test"]}),
                    "usage": {"total_tokens": 50}
                },
                {
                    "success": False,
                    "error": "Content generation failed"
                }
            ])
            
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Should handle error gracefully with fallback
            assert result.success is True  # Fallback should work
            assert "content" in result.data
            assert result.execution_time > 0


class TestContentAgentIntegration:
    """Test Content Agent integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_content_creation(self, mock_agent_context):
        """Test complete end-to-end content creation flow."""
        agent = ContentAgent()
        mock_agent_context.query = "Create a comprehensive guide about cybersecurity best practices for small businesses"
        mock_agent_context.parameters = {
            "content_type": "guide",
            "target_audience": "small business owners",
            "tone": "educational"
        }
        
        with patch('src.agents.content.api_manager') as mock_api_manager, \
             patch('src.agents.base.memory_manager') as mock_memory, \
             patch('builtins.open', create=True) as mock_open:
            
            # Mock complete flow responses
            mock_api_manager.openai.chat_completion = AsyncMock(side_effect=[
                # Parsing response
                {
                    "success": True,
                    "content": json.dumps({
                        "content_type": "guide",
                        "target_audience": "small business owners",
                        "tone": "educational",
                        "keywords": ["cybersecurity", "small business", "best practices"],
                        "estimated_length": "long_form"
                    }),
                    "usage": {"total_tokens": 120}
                },
                # Content generation response
                {
                    "success": True,
                    "content": """# Cybersecurity Best Practices for Small Businesses

## Introduction
Small businesses face increasing cybersecurity threats...

## Essential Security Measures
1. Strong password policies
2. Regular software updates
3. Employee training programs

## Conclusion
Implementing these practices will significantly improve your security posture.""",
                    "usage": {"total_tokens": 800}
                },
                # SEO optimization response
                {
                    "success": True,
                    "content": json.dumps({
                        "title_suggestions": [
                            "Cybersecurity Best Practices: A Complete Guide for Small Businesses",
                            "Small Business Cybersecurity: Essential Protection Strategies",
                            "Protect Your Small Business: Cybersecurity Best Practices Guide"
                        ],
                        "meta_description": "Comprehensive guide to cybersecurity best practices for small businesses. Learn essential security measures to protect your business from cyber threats.",
                        "keywords": ["cybersecurity", "small business security", "cyber threats", "business protection"],
                        "readability_score": 82,
                        "seo_recommendations": [
                            "Add more internal links to related security topics",
                            "Include case studies or examples",
                            "Add FAQ section for common security questions",
                            "Optimize images with descriptive alt text"
                        ],
                        "keyword_density": {
                            "cybersecurity": 3.2,
                            "small business": 2.8,
                            "security": 4.1
                        }
                    }),
                    "usage": {"total_tokens": 300}
                }
            ])
            
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            # Mock file operations
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Verify complete flow
            assert result.success is True
            assert "content" in result.data
            assert "seo_analysis" in result.data
            assert "metadata" in result.data
            assert "file_paths" in result.data
            
            # Verify content quality
            content = result.data["content"]
            assert content["word_count"] > 100
            assert "cybersecurity" in content["markdown_content"].lower()
            
            # Verify SEO analysis
            seo = result.data["seo_analysis"]
            assert len(seo["title_suggestions"]) == 3
            assert seo["readability_score"] > 80
            assert len(seo["seo_recommendations"]) > 0
            
            # Verify file operations
            assert mock_open.call_count == 2  # Markdown and JSON files
    
    @pytest.mark.asyncio
    async def test_content_with_custom_parameters(self, mock_agent_context):
        """Test content generation with custom parameters."""
        agent = ContentAgent()
        mock_agent_context.query = "Write marketing copy for a new product launch"
        mock_agent_context.parameters = {
            "content_type": "marketing_copy",
            "target_audience": "millennials",
            "tone": "exciting",
            "call_to_action": "Sign up for early access",
            "brand_voice": "innovative and friendly"
        }
        
        with patch('src.agents.content.api_manager') as mock_api_manager, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            mock_api_manager.openai.chat_completion = AsyncMock(side_effect=[
                {
                    "success": True,
                    "content": json.dumps({
                        "content_type": "marketing_copy",
                        "target_audience": "millennials",
                        "tone": "exciting",
                        "keywords": ["product launch", "innovation", "early access"],
                        "brand_voice": "innovative and friendly"
                    }),
                    "usage": {"total_tokens": 100}
                },
                {
                    "success": True,
                    "content": "🚀 Revolutionary Product Launch! Get ready for something amazing...",
                    "usage": {"total_tokens": 400}
                },
                {
                    "success": True,
                    "content": json.dumps({
                        "title_suggestions": ["Revolutionary Product Launch"],
                        "meta_description": "Be first to experience our revolutionary product",
                        "keywords": ["product launch", "innovation"],
                        "readability_score": 88,
                        "seo_recommendations": ["Add urgency elements"]
                    }),
                    "usage": {"total_tokens": 150}
                }
            ])
            
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Verify custom parameters were used
            assert result.success is True
            assert "exciting" in result.data["metadata"]["tone"]
            assert "millennials" in result.data["metadata"]["target_audience"]
            assert "🚀" in result.data["content"]["markdown_content"]  # Exciting tone indicator
