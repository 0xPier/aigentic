"""
Unit tests for the Research Agent.
Tests web search, content scraping, and research analysis functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.agents.research import ResearchAgent
from src.agents.base import AgentContext, AgentResult


class TestResearchAgent:
    """Test Research Agent functionality."""
    
    def test_research_agent_initialization(self):
        """Test research agent initialization."""
        agent = ResearchAgent()
        
        assert agent.name == "research"
        assert "research" in agent.description.lower()
        assert agent.memory_enabled is True
    
    @pytest.mark.asyncio
    async def test_successful_research_execution(self, mock_agent_context, mock_openai_client, mock_web_search):
        """Test successful research execution with mocked APIs."""
        agent = ResearchAgent()
        mock_agent_context.query = "artificial intelligence trends 2024"
        
        # Mock the web search and OpenAI responses
        with patch.object(agent, '_perform_web_search') as mock_search, \
             patch.object(agent, '_scrape_content') as mock_scrape, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            # Setup mocks
            mock_search.return_value = [
                {
                    "title": "AI Trends 2024",
                    "url": "https://example.com/ai-trends",
                    "snippet": "Latest AI trends and developments"
                }
            ]
            
            mock_scrape.return_value = {
                "content": "Detailed AI trends content...",
                "title": "AI Trends 2024",
                "word_count": 500
            }
            
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            # Execute research
            result = await agent.execute_with_context(mock_agent_context)
            
            # Verify result
            assert result.success is True
            assert "research_results" in result.data
            assert "analysis" in result.data
            assert "sources" in result.data
            assert result.execution_time > 0
            
            # Verify methods were called
            mock_search.assert_called_once()
            mock_scrape.assert_called()
    
    @pytest.mark.asyncio
    async def test_web_search_functionality(self, mock_web_search):
        """Test web search functionality."""
        agent = ResearchAgent()
        
        # Mock DuckDuckGo API response
        mock_response_data = {
            "RelatedTopics": [
                {
                    "Text": "Artificial Intelligence - AI is transforming industries",
                    "FirstURL": "https://example.com/ai-article"
                },
                {
                    "Text": "Machine Learning trends in 2024",
                    "FirstURL": "https://example.com/ml-trends"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await agent._perform_web_search("artificial intelligence trends")
            
            # Verify search results
            assert len(results) == 2
            assert results[0]["title"] == "Artificial Intelligence"
            assert results[0]["url"] == "https://example.com/ai-article"
            assert "transforming industries" in results[0]["snippet"]
    
    @pytest.mark.asyncio
    async def test_web_search_fallback(self):
        """Test web search fallback when API fails."""
        agent = ResearchAgent()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Simulate API failure
            mock_get.side_effect = Exception("API Error")
            
            results = await agent._perform_web_search("test query")
            
            # Should return mock data as fallback
            assert len(results) > 0
            assert "mock" in results[0]["title"].lower() or "example" in results[0]["title"].lower()
    
    @pytest.mark.asyncio
    async def test_content_scraping(self):
        """Test content scraping functionality."""
        agent = ResearchAgent()
        
        mock_html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <h1>Main Heading</h1>
                <p>This is the main content of the article.</p>
                <p>Another paragraph with useful information.</p>
                <div>Some additional content in a div.</div>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            content = await agent._scrape_content("https://example.com/article")
            
            # Verify scraped content
            assert content["title"] == "Test Article"
            assert "main content" in content["content"].lower()
            assert content["word_count"] > 0
            assert len(content["content"]) > 50
    
    @pytest.mark.asyncio
    async def test_content_scraping_failure(self):
        """Test content scraping failure handling."""
        agent = ResearchAgent()
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # Simulate scraping failure
            mock_get.side_effect = Exception("Network Error")
            
            content = await agent._scrape_content("https://example.com/article")
            
            # Should return error content
            assert "error" in content["content"].lower()
            assert content["word_count"] == 0
    
    @pytest.mark.asyncio
    async def test_research_analysis_with_openai(self, mock_openai_client):
        """Test research analysis using OpenAI."""
        agent = ResearchAgent()
        
        search_results = [
            {
                "title": "AI Trends 2024",
                "url": "https://example.com/ai",
                "snippet": "AI is evolving rapidly",
                "content": "Detailed content about AI trends..."
            }
        ]
        
        with patch('src.agents.research.api_manager') as mock_api_manager:
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": True,
                "content": "Comprehensive analysis of AI trends based on research...",
                "usage": {"total_tokens": 200}
            })
            
            analysis = await agent._analyze_research_results(
                "AI trends", search_results
            )
            
            # Verify analysis
            assert "analysis" in analysis
            assert "key_findings" in analysis
            assert "sources" in analysis
            assert len(analysis["sources"]) == 1
            
            # Verify OpenAI was called
            mock_api_manager.openai.chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_research_analysis_fallback(self):
        """Test research analysis fallback when OpenAI fails."""
        agent = ResearchAgent()
        
        search_results = [
            {
                "title": "Test Article",
                "url": "https://example.com/test",
                "snippet": "Test content",
                "content": "Detailed test content"
            }
        ]
        
        with patch('src.agents.research.api_manager') as mock_api_manager:
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": False,
                "error": "API Error"
            })
            
            analysis = await agent._analyze_research_results(
                "test query", search_results
            )
            
            # Should provide basic analysis without OpenAI
            assert "analysis" in analysis
            assert "key_findings" in analysis
            assert len(analysis["sources"]) == 1
    
    @pytest.mark.asyncio
    async def test_query_parsing(self):
        """Test research query parsing and enhancement."""
        agent = ResearchAgent()
        
        test_cases = [
            {
                "input": "AI trends",
                "expected_keywords": ["AI", "trends", "artificial intelligence"]
            },
            {
                "input": "machine learning applications in healthcare",
                "expected_keywords": ["machine learning", "healthcare", "applications"]
            },
            {
                "input": "blockchain technology 2024",
                "expected_keywords": ["blockchain", "technology", "2024"]
            }
        ]
        
        for case in test_cases:
            parsed = await agent._parse_research_query(case["input"])
            
            # Verify parsing results
            assert "keywords" in parsed
            assert "search_terms" in parsed
            assert len(parsed["keywords"]) > 0
            
            # Check if expected keywords are present (case insensitive)
            keywords_lower = [k.lower() for k in parsed["keywords"]]
            for expected in case["expected_keywords"]:
                assert any(expected.lower() in keyword for keyword in keywords_lower)
    
    @pytest.mark.asyncio
    async def test_source_reliability_assessment(self):
        """Test source reliability assessment."""
        agent = ResearchAgent()
        
        test_sources = [
            {
                "url": "https://arxiv.org/abs/2024.12345",
                "title": "Academic Paper on AI",
                "expected_score": "high"
            },
            {
                "url": "https://blog.example.com/ai-thoughts",
                "title": "Personal Blog Post",
                "expected_score": "medium"
            },
            {
                "url": "https://news.bbc.com/technology/ai-news",
                "title": "BBC News Article",
                "expected_score": "high"
            },
            {
                "url": "https://random-site.com/ai-info",
                "title": "Unknown Source",
                "expected_score": "low"
            }
        ]
        
        for source in test_sources:
            reliability = await agent._assess_source_reliability(source)
            
            assert "score" in reliability
            assert "reasoning" in reliability
            assert reliability["score"] in ["high", "medium", "low"]
            
            # Verify expected reliability scores
            if source["expected_score"] == "high":
                assert reliability["score"] in ["high", "medium"]
            elif source["expected_score"] == "low":
                assert reliability["score"] in ["low", "medium"]
    
    @pytest.mark.asyncio
    async def test_research_with_memory_integration(self, mock_agent_context, db_session):
        """Test research execution with memory integration."""
        agent = ResearchAgent()
        mock_agent_context.query = "machine learning trends"
        
        # Mock previous research memory
        mock_memories = [
            {
                "id": 1,
                "memory_type": "success",
                "content": {
                    "execution_summary": {
                        "task_type": "research",
                        "summary": "Previous ML research completed"
                    }
                },
                "context_tags": ["research", "machine_learning"],
                "relevance_score": 0.8
            }
        ]
        
        with patch('src.agents.base.memory_manager') as mock_memory, \
             patch.object(agent, '_perform_web_search') as mock_search, \
             patch.object(agent, '_scrape_content') as mock_scrape:
            
            mock_memory.retrieve_memories = AsyncMock(return_value=mock_memories)
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            mock_search.return_value = [{"title": "ML Trends", "url": "https://example.com", "snippet": "ML info"}]
            mock_scrape.return_value = {"content": "ML content", "title": "ML Trends", "word_count": 100}
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Verify memory was loaded and used
            assert len(agent.learning_context) == 1
            assert result.success is True
            
            # Verify new memory was stored
            mock_memory.store_memory.assert_called()
    
    @pytest.mark.asyncio
    async def test_research_performance_tracking(self, mock_agent_context, performance_timer):
        """Test research performance tracking."""
        agent = ResearchAgent()
        mock_agent_context.query = "performance test query"
        
        with patch.object(agent, '_perform_web_search') as mock_search, \
             patch.object(agent, '_scrape_content') as mock_scrape, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            # Setup quick mocks to control timing
            mock_search.return_value = [{"title": "Test", "url": "https://example.com", "snippet": "Test"}]
            mock_scrape.return_value = {"content": "Test content", "title": "Test", "word_count": 50}
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            performance_timer.start()
            result = await agent.execute_with_context(mock_agent_context)
            performance_timer.stop()
            
            # Verify performance tracking
            assert result.execution_time > 0
            assert result.execution_time <= performance_timer.elapsed_seconds + 1  # Allow some tolerance
            assert agent.performance_metrics["total_executions"] == 1
            assert agent.performance_metrics["successful_executions"] == 1
    
    @pytest.mark.asyncio
    async def test_research_error_handling(self, mock_agent_context):
        """Test research error handling and recovery."""
        agent = ResearchAgent()
        mock_agent_context.query = "error test query"
        
        with patch.object(agent, '_perform_web_search') as mock_search, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            # Simulate search failure
            mock_search.side_effect = Exception("Search API Error")
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Should handle error gracefully
            assert result.success is False
            assert "error" in result.data
            assert result.execution_time > 0
            
            # Performance metrics should still be updated
            assert agent.performance_metrics["total_executions"] == 1
            assert agent.performance_metrics["successful_executions"] == 0


class TestResearchAgentIntegration:
    """Test Research Agent integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_research_flow(self, mock_agent_context):
        """Test complete end-to-end research flow."""
        agent = ResearchAgent()
        mock_agent_context.query = "quantum computing applications"
        
        # Mock all external dependencies
        with patch('aiohttp.ClientSession.get') as mock_get, \
             patch('src.agents.research.api_manager') as mock_api_manager, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            # Setup web search mock
            mock_search_response = AsyncMock()
            mock_search_response.status = 200
            mock_search_response.json = AsyncMock(return_value={
                "RelatedTopics": [
                    {
                        "Text": "Quantum Computing Applications - Revolutionary technology",
                        "FirstURL": "https://example.com/quantum"
                    }
                ]
            })
            
            # Setup content scraping mock
            mock_content_response = AsyncMock()
            mock_content_response.status = 200
            mock_content_response.text = AsyncMock(return_value="""
                <html>
                    <head><title>Quantum Computing Applications</title></head>
                    <body>
                        <h1>Quantum Computing in Various Industries</h1>
                        <p>Quantum computing is revolutionizing multiple sectors including finance, healthcare, and cryptography.</p>
                        <p>Key applications include optimization problems, drug discovery, and secure communications.</p>
                    </body>
                </html>
            """)
            
            # Setup mock responses
            mock_get.return_value.__aenter__.return_value = mock_search_response
            mock_get.return_value.__aenter__.return_value = mock_content_response
            
            # Setup OpenAI mock
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": True,
                "content": "Comprehensive analysis of quantum computing applications across industries...",
                "usage": {"total_tokens": 300}
            })
            
            # Setup memory mocks
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            # Execute research
            result = await agent.execute_with_context(mock_agent_context)
            
            # Verify complete flow
            assert result.success is True
            assert "research_results" in result.data
            assert "analysis" in result.data
            assert "sources" in result.data
            assert len(result.data["sources"]) > 0
            
            # Verify all components were called
            assert mock_get.call_count >= 2  # Search + scraping
            mock_api_manager.openai.chat_completion.assert_called()
            mock_memory.store_memory.assert_called()
    
    @pytest.mark.asyncio
    async def test_research_with_multiple_sources(self, mock_agent_context):
        """Test research with multiple sources and comprehensive analysis."""
        agent = ResearchAgent()
        mock_agent_context.query = "artificial intelligence ethics"
        
        with patch.object(agent, '_perform_web_search') as mock_search, \
             patch.object(agent, '_scrape_content') as mock_scrape, \
             patch('src.agents.research.api_manager') as mock_api_manager, \
             patch('src.agents.base.memory_manager') as mock_memory:
            
            # Setup multiple search results
            mock_search.return_value = [
                {
                    "title": "AI Ethics Guidelines",
                    "url": "https://example.com/ai-ethics-1",
                    "snippet": "Comprehensive AI ethics framework"
                },
                {
                    "title": "Ethical AI Development",
                    "url": "https://example.com/ai-ethics-2",
                    "snippet": "Best practices for ethical AI"
                },
                {
                    "title": "AI Bias and Fairness",
                    "url": "https://example.com/ai-bias",
                    "snippet": "Addressing bias in AI systems"
                }
            ]
            
            # Setup scraping results
            mock_scrape.side_effect = [
                {"content": "AI ethics guidelines content...", "title": "AI Ethics Guidelines", "word_count": 200},
                {"content": "Ethical AI development practices...", "title": "Ethical AI Development", "word_count": 180},
                {"content": "AI bias and fairness considerations...", "title": "AI Bias and Fairness", "word_count": 220}
            ]
            
            # Setup OpenAI analysis
            mock_api_manager.openai.chat_completion = AsyncMock(return_value={
                "success": True,
                "content": "Comprehensive analysis of AI ethics covering guidelines, development practices, and bias mitigation...",
                "usage": {"total_tokens": 400}
            })
            
            mock_memory.retrieve_memories = AsyncMock(return_value=[])
            mock_memory.store_memory = AsyncMock(return_value=True)
            
            result = await agent.execute_with_context(mock_agent_context)
            
            # Verify comprehensive research
            assert result.success is True
            assert len(result.data["sources"]) == 3
            assert "ethics" in result.data["analysis"].lower()
            
            # Verify all sources were processed
            assert mock_scrape.call_count == 3
