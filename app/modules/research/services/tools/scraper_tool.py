"""
URL Scraper Tool

Provides web scraping capabilities to extract content from URLs.
"""
from typing import Optional

from langchain_core.tools import BaseTool, tool

from app.core.logging.logger import logger


def create_scraper_tool() -> Optional[BaseTool]:
    """
    Create URL scraper tool.
    
    Returns:
        Scraper tool if initialization succeeds, None otherwise
    """
    try:

        @tool
        def scrape_url(url: str) -> str:
            """Scrape content from a URL to get detailed information."""
            try:
                from langchain_community.document_loaders import WebBaseLoader

                loader = WebBaseLoader(
                    web_paths=[url],
                    requests_kwargs={"timeout": 10},
                )
                docs = loader.load()

                if docs:
                    return docs[0].page_content[:6000]
                return f"No content found at {url}"

            except Exception as e:
                return f"Error scraping URL: {e}"

        logger.info("URL scraper tool initialized")
        return scrape_url

    except Exception as e:
        logger.warning(f"Scraper tool initialization failed: {e}")
        return None
