"""
ArXiv Search Tool

Provides academic paper search capabilities using the ArXiv API.
"""
from typing import Optional

from langchain_core.tools import BaseTool

from app.core.logging.logger import logger


def create_arxiv_tool() -> Optional[BaseTool]:
    """
    Create ArXiv search tool.
    
    Returns:
        ArxivQueryRun tool if initialization succeeds, None otherwise
    """
    try:
        from langchain_community.tools.arxiv.tool import ArxivQueryRun
        from langchain_community.utilities.arxiv import ArxivAPIWrapper

        tool = ArxivQueryRun(
            api_wrapper=ArxivAPIWrapper(
                top_k_results=5,
                doc_content_chars_max=4000,
                load_all_available_meta=True,
            ),
            name="arxiv_search",
            description="Search ArXiv for academic papers and research.",
        )
        logger.info("ArXiv search tool initialized")
        return tool

    except Exception as e:
        logger.warning(f"ArXiv initialization failed: {e}")
        return None
