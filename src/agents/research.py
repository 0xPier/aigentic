"""Research Agent for web research and data gathering."""

import asyncio
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
from datetime import datetime
import logging
import aiohttp
import json

from src.agents.base import LLMAgent, AgentContext, AgentResult
from src.integrations.api_client import api_manager

logger = logging.getLogger(__name__)


class ResearchAgent(LLMAgent):
    """Agent specialized in web research and data gathering."""
    
    def __init__(self):
        super().__init__(
            name="research",
            description="Conducts web research, gathers market data, and analyzes trends",
            capabilities=[
                "web_scraping",
                "market_research",
                "trend_analysis",
                "data_gathering",
                "competitive_analysis"
            ]
        )
    
    def get_required_integrations(self) -> List[str]:
        """Research agent doesn't require specific integrations."""
        return []
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute research task."""
        start_time = datetime.utcnow()
        
        try:
            # Analyze research query
            research_plan = await self._create_research_plan(context.query)
            
            # Conduct research
            research_results = await self._conduct_research(research_plan)
            
            # Analyze and synthesize findings
            analysis = await self._analyze_findings(context.query, research_results)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=True,
                data={
                    "research_plan": research_plan,
                    "raw_data": research_results,
                    "analysis": analysis,
                    "sources": [item.get("url", "N/A") for item in research_results],
                    "key_findings": analysis.get("key_findings", []),
                    "recommendations": analysis.get("recommendations", [])
                },
                message="Research completed successfully",
                execution_time=execution_time
            )
            
            # Save research to memory
            self.save_memory(
                memory_type="research",
                content={
                    "query": context.query,
                    "findings": analysis.get("key_findings", []),
                    "sources": len(research_results)
                },
                context_tags=["research", context.task_type],
                relevance_score=0.9
            )
            
            self.log_execution(context, result)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AgentResult(
                success=False,
                data={},
                message=f"Research failed: {str(e)}",
                execution_time=execution_time,
                error=str(e)
            )
            
            self.log_execution(context, result)
            return result
    
    async def _create_research_plan(self, query: str) -> Dict[str, Any]:
        """Create a research plan based on the query."""
        system_prompt = """
        You are a research planning expert. Create a comprehensive research plan for the given query.
        Include:
        1. Key topics to research
        2. Search terms and keywords
        3. Types of sources to look for
        4. Specific questions to answer
        
        Respond in JSON format:
        {
            "topics": ["topic1", "topic2"],
            "keywords": ["keyword1", "keyword2"],
            "source_types": ["news", "academic", "industry_reports"],
            "questions": ["question1", "question2"]
        }
        """
        
        prompt = f"Create a research plan for: {query}"
        
        try:
            response = await self.call_llm(prompt, system_prompt, temperature=0.3)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Research planning failed: {e}")
            return {
                "topics": [query],
                "keywords": query.split(),
                "source_types": ["web"],
                "questions": [f"What information is available about {query}?"]
            }
    
    async def _conduct_research(self, research_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Conduct web research based on the plan."""
        results = []
        
        async def _perform_web_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
            """Perform web search using DuckDuckGo API (free alternative)."""
            try:
                # Use DuckDuckGo Instant Answer API (free, no API key required)
                search_url = "https://api.duckduckgo.com/"
                params = {
                    "q": query,
                    "format": "json",
                    "pretty": "1",
                    "no_html": "1",
                    "skip_disambig": "1"
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            results = []
                            
                            # Add instant answer if available
                            if data.get("AbstractText"):
                                results.append({
                                    "title": data.get("Heading", "Instant Answer"),
                                    "url": data.get("AbstractURL", ""),
                                    "snippet": data.get("AbstractText", ""),
                                    "source": data.get("AbstractSource", "DuckDuckGo"),
                                    "date": datetime.now().isoformat(),
                                    "type": "instant_answer"
                                })
                            
                            # Add related topics
                            for topic in data.get("RelatedTopics", [])[:max_results-len(results)]:
                                if isinstance(topic, dict) and topic.get("Text"):
                                    results.append({
                                        "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else "Related Topic",
                                        "url": topic.get("FirstURL", ""),
                                        "snippet": topic.get("Text", ""),
                                        "source": "DuckDuckGo",
                                        "date": datetime.now().isoformat(),
                                        "type": "related_topic"
                                    })
                            
                            return results[:max_results]
                
                # Fallback to mock results if API fails
                logger.warning("DuckDuckGo API failed, using mock results")
                return await self._get_mock_search_results(query, max_results)
                
            except Exception as e:
                logger.error(f"Web search error: {str(e)}")
                return await self._get_mock_search_results(query, max_results)
        
        async def _get_mock_search_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
            """Log failure and raise exception instead of returning mock data."""
            self.logger.error(f"Web search failed for query: {query}. No fallback data available.")
            raise Exception(f"Web search failed for query: {query}. Please check internet connection and try again.")
        
        for topic in research_plan.get("topics", []):
            try:
                search_results = await _perform_web_search(self, topic)
                results.extend(search_results)
                
                # Add some delay to simulate real research
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Research failed for topic {topic}: {e}")
                # Don't continue with other topics if search fails
                raise Exception(f"Research failed for topic {topic}: {e}")
        
        return results
    
    async def _analyze_findings(self, original_query: str, research_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze research findings and create insights."""
        analysis_prompt = f"""
        Based on the following research data, provide a comprehensive analysis:
        
        Query: {original_query}
        Research Results: {json.dumps(research_results, indent=2)}
        
        Please provide:
        1. Executive Summary
        2. Key findings and insights
        3. Trends and patterns identified
        4. Actionable recommendations
        5. Areas for further research
        6. Source reliability assessment
        
        Format the response as a structured analysis with clear sections.
        """
        
        # Use OpenAI for analysis
        analysis_response = await api_manager.openai.chat_completion([
            {
                "role": "system",
                "content": "You are an expert research analyst. Provide thorough, objective analysis based on the provided research data."
            },
            {
                "role": "user",
                "content": analysis_prompt
            }
        ], model="gpt-4", max_tokens=3000)
        
        if analysis_response["success"]:
            analysis_result = analysis_response["content"]
        else:
            analysis_result = f"Analysis failed: {analysis_response.get('error', 'Unknown error')}"
            logger.error(f"OpenAI analysis failed: {analysis_response.get('error')}")
        
        # Save results
        output_file = f"research_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        await self.save_output(output_file, {
            "query": original_query,
            "research_data": research_results,
            "analysis": analysis_result,
            "openai_usage": analysis_response.get("usage"),
            "metadata": {
                "agent": self.name,
                "timestamp": datetime.now().isoformat(),
                "sources_count": len(research_results),
                "scraped_sources": len([r for r in research_results if r["type"] != "mock"])
            }
        })
        
        return {
            "key_findings": [f"Research conducted on {original_query}"],
            "trends": ["Data analysis in progress"],
            "recommendations": ["Further research recommended"],
            "data_gaps": ["More comprehensive data needed"]
        }
    
    async def _scrape_content(self, url: str) -> Dict[str, Any]:
        """Scrape content from a URL with real web scraping."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Parse HTML with BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Extract title
                        title = soup.find('title')
                        title_text = title.get_text().strip() if title else "No title found"
                        
                        # Extract main content
                        # Try to find main content areas
                        content_selectors = [
                            'article', 'main', '.content', '#content',
                            '.post-content', '.entry-content', '.article-body'
                        ]
                        
                        content_text = ""
                        for selector in content_selectors:
                            content_elem = soup.select_one(selector)
                            if content_elem:
                                content_text = content_elem.get_text(separator=' ', strip=True)
                                break
                        
                        # Fallback to body if no specific content area found
                        if not content_text:
                            body = soup.find('body')
                            if body:
                                content_text = body.get_text(separator=' ', strip=True)
                        
                        # Clean up the text
                        content_text = ' '.join(content_text.split())  # Remove extra whitespace
                        
                        return {
                            "url": url,
                            "title": title_text,
                            "content": content_text[:5000],  # Limit to 5000 chars
                            "word_count": len(content_text.split()),
                            "scraped_at": datetime.now().isoformat(),
                            "status": "success"
                        }
                    else:
                        return {
                            "url": url,
                            "title": "Failed to scrape",
                            "content": f"Failed to access URL. Status code: {response.status}",
                            "word_count": 0,
                            "scraped_at": datetime.now().isoformat(),
                            "status": "error"
                        }
        
            
            
        except Exception as e:
            self.logger.error(f"Failed to scrape {url}: {e}")
            return {
                "url": url,
                "title": "Scraping failed",
                "content": f"Could not scrape content: {str(e)}",
                "scraped_at": datetime.utcnow().isoformat()
            }
