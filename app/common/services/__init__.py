"""
External service clients for Research Agent
"""
from app.common.services.arxiv_client import ArXivClient
from app.common.services.arxiv_id_parser import (
    ArXivIdComponents,
    extract_version,
    format_arxiv_url,
    get_base_id,
    normalize_arxiv_id,
    parse_arxiv_id,
    validate_arxiv_id,
)
from app.common.services.github_client import GitHubTrendingClient
from app.common.services.hackernews_client import HackerNewsClient
from app.common.services.tavily_client import TavilySearchClient
from app.common.services.web_scraper import WebScraper

__all__ = [
    'ArXivClient',
    'TavilySearchClient',
    'GitHubTrendingClient',
    'HackerNewsClient',
    'WebScraper',
    'ArXivIdComponents',
    'parse_arxiv_id',
    'validate_arxiv_id',
    'normalize_arxiv_id',
    'extract_version',
    'get_base_id',
    'format_arxiv_url',
]


