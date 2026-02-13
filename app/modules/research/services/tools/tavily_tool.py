"""
Tavily Web Search Tool

Provides web search capabilities using the Tavily API.
"""
from typing import Optional

from langchain_core.tools import BaseTool

from app.core.config.environment_config import settings
from app.core.logging.logger import logger


def create_tavily_tool() -> Optional[BaseTool]:
    """
    Create Tavily web search tool.
    
    Returns:
        TavilySearch tool if API key is configured, None otherwise
    """
    if not settings.TAVILY_API_KEY:
        logger.warning("Tavily API key not configured, skipping web search tool")
        return None

    try:
        from langchain_tavily import TavilySearch

        tool = TavilySearch(
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            name="web_search",
            description="Search the web for current information, tutorials, docs, news.",
        )
        logger.info("Tavily web search tool initialized")
        return tool

    except Exception as e:
        logger.warning(f"Tavily initialization failed: {e}")
        return None
