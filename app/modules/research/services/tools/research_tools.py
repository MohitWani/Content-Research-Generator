"""
Research Tools - Tools for gathering research information.

This module contains all the tools used by the research agent:
- Web Search (Tavily)
- ArXiv Search
- Wikipedia Search
- GitHub Search
- URL Scraper
"""
from typing import List

from langchain_core.tools import BaseTool

from app.core.config.environment_config import settings
from app.core.logging.logger import logger
from app.modules.research.services.tools.arxiv_tool import create_arxiv_tool
from app.modules.research.services.tools.github_tool import create_github_tool
from app.modules.research.services.tools.scraper_tool import create_scraper_tool
from app.modules.research.services.tools.tavily_tool import create_tavily_tool
from app.modules.research.services.tools.wikipedia_tool import create_wikipedia_tool


# Source type mapping for categorizing tool outputs
SOURCE_TYPE_MAPPING = {
    "web_search": "web",
    "arxiv_search": "paper",
    "wikipedia": "encyclopedia",
    "github_search": "github",
    "scrape_url": "web",
}


def create_research_tools() -> List[BaseTool]:
    """
    Create and return all research tools for the agent.
    
    Returns:
        List of initialized research tools
    """
    tools: List[BaseTool] = []

    # 1. Tavily Web Search
    tavily_tool = create_tavily_tool()
    if tavily_tool:
        tools.append(tavily_tool)

    # 2. ArXiv Search
    arxiv_tool = create_arxiv_tool()
    if arxiv_tool:
        tools.append(arxiv_tool)

    # 3. Wikipedia Search
    wikipedia_tool = create_wikipedia_tool()
    if wikipedia_tool:
        tools.append(wikipedia_tool)

    # 4. URL Scraper
    scraper_tool = create_scraper_tool()
    if scraper_tool:
        tools.append(scraper_tool)

    # 5. GitHub Search
    github_tool = create_github_tool()
    if github_tool:
        tools.append(github_tool)

    logger.info(f"Created {len(tools)} research tools")
    return tools
