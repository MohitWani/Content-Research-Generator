"""
Wikipedia Search Tool

Provides Wikipedia search capabilities for background information.
"""
from typing import Optional

from langchain_core.tools import BaseTool

from app.core.logging.logger import logger


def create_wikipedia_tool() -> Optional[BaseTool]:
    """
    Create Wikipedia search tool.
    
    Returns:
        WikipediaQueryRun tool if initialization succeeds, None otherwise
    """
    try:
        from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
        from langchain_community.utilities.wikipedia import WikipediaAPIWrapper

        tool = WikipediaQueryRun(
            api_wrapper=WikipediaAPIWrapper(
                top_k_results=3,
                doc_content_chars_max=4000,
            ),
            name="wikipedia",
            description="Search Wikipedia for background info and definitions.",
        )
        logger.info("Wikipedia search tool initialized")
        return tool

    except Exception as e:
        logger.warning(f"Wikipedia initialization failed: {e}")
        return None
