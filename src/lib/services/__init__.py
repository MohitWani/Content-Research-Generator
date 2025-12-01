"""
External service clients for data collection
"""
from src.lib.services.tavily_client import TavilySearchClient
from src.lib.services.arxiv_client import ArXivClient
from src.lib.services.github_trending_client import GitHubTrendingClient
from src.lib.services.hackernews_client import HackerNewsClient
from src.lib.services.web_scraper import WebScraper

__all__ = [
    "TavilySearchClient",
    "ArXivClient",
    "GitHubTrendingClient",
    "HackerNewsClient",
    "WebScraper",
]

