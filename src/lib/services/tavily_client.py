"""
Tavily Search API client for AI-powered web search
Provides high-quality, AI-relevant search results
"""
from typing import List, Dict, Any, Optional
from tavily import TavilyClient as TavilyAPI

from src.common.config import config
from src.common.logger import setup_logger
from src.lib.models.exceptions import ExternalAPIError

logger = setup_logger(__name__)


class TavilySearchClient:
    """
    Client for Tavily AI search API
    Optimized for AI and research queries
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily client
        
        Args:
            api_key: Tavily API key (defaults to env TAVILY_API_KEY)
        """
        self.api_key = api_key or config.TAVILY_API_KEY
        if not self.api_key:
            logger.warning("Tavily API key not configured")
            self.client = None
        else:
            self.client = TavilyAPI(api_key=self.api_key)
            logger.info("Initialized Tavily search client")
    
    async def search(
        self,
        query: str,
        search_depth: str = "advanced",
        max_results: int = 10,
        include_answer: bool = True,
        include_raw_content: bool = False,
    ) -> Dict[str, Any]:
        """
        Perform AI-powered search using Tavily
        
        Args:
            query: Search query
            search_depth: "basic" or "advanced" (more thorough)
            max_results: Maximum number of results
            include_answer: Include AI-generated answer
            include_raw_content: Include raw page content
        
        Returns:
            Search results with answer and sources
        """
        if not self.client:
            raise ExternalAPIError("Tavily API key not configured")
        
        try:
            logger.debug(f"Tavily search: {query[:100]}...")
            
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
            )
            
            # Format results
            results = {
                "query": query,
                "answer": response.get("answer"),
                "results": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "content": r.get("content"),
                        "score": r.get("score"),
                        "raw_content": r.get("raw_content") if include_raw_content else None,
                    }
                    for r in response.get("results", [])
                ],
                "sources_count": len(response.get("results", [])),
            }
            
            logger.info(f"Tavily search returned {results['sources_count']} results")
            return results
            
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            raise ExternalAPIError(f"Tavily search failed: {e}")
    
    async def search_context(
        self,
        query: str,
        max_results: int = 5,
    ) -> str:
        """
        Get search context optimized for LLM consumption
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            Formatted context string for LLM
        """
        if not self.client:
            raise ExternalAPIError("Tavily API key not configured")
        
        try:
            context = self.client.get_search_context(
                query=query,
                max_results=max_results,
            )
            return context
        except Exception as e:
            logger.error(f"Tavily context search error: {e}")
            raise ExternalAPIError(f"Tavily context search failed: {e}")
    
    async def qna_search(self, query: str) -> str:
        """
        Get a direct answer to a question
        
        Args:
            query: Question to answer
        
        Returns:
            Direct answer string
        """
        if not self.client:
            raise ExternalAPIError("Tavily API key not configured")
        
        try:
            answer = self.client.qna_search(query=query)
            return answer
        except Exception as e:
            logger.error(f"Tavily QnA error: {e}")
            raise ExternalAPIError(f"Tavily QnA search failed: {e}")

