"""
Unit tests for External Service Clients
Tests ArXiv, GitHub, HackerNews, Tavily, and Web Scraper clients
Maps to: spec.md → FR8 (Data Source Integration)
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from src.lib.services.arxiv_client import ArXivClient
from src.lib.services.github_trending_client import GitHubTrendingClient
from src.lib.services.hackernews_client import HackerNewsClient
from src.lib.services.tavily_client import TavilySearchClient
from src.lib.services.web_scraper import WebScraper
from src.lib.models.exceptions import ExternalAPIError


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API testing"""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.mark.asyncio
class TestArXivClient:
    """Test ArXiv API client"""
    
    @pytest.fixture
    def arxiv_client(self, mock_httpx_client):
        """ArXiv client with mocked HTTP client"""
        client = ArXivClient(http_client=mock_httpx_client)
        return client
    
    async def test_search_papers_success(self, arxiv_client, mock_httpx_client):
        """Should search and return papers from ArXiv"""
        # Arrange
        query = "transformers"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <entry>
        <id>http://arxiv.org/abs/1706.03762v1</id>
        <title>Attention Is All You Need</title>
        <summary>We propose a new simple network architecture...</summary>
        <author><name>Vaswani, Ashish</name></author>
        <published>2017-06-12</published>
    </entry>
</feed>"""
        mock_httpx_client.get.return_value = mock_response
        
        # Act
        results = await arxiv_client.search(query)
        
        # Assert
        assert len(results) > 0
        assert results[0]["title"] == "Attention Is All You Need"
        mock_httpx_client.get.assert_called_once()
    
    async def test_search_papers_handles_rate_limit(self, arxiv_client, mock_httpx_client):
        """Should handle rate limiting"""
        # Arrange
        query = "transformers"
        mock_response = Mock()
        mock_response.status_code = 429
        mock_httpx_client.get.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(ExternalAPIError) as exc:
            await arxiv_client.search(query)
        assert "rate limit" in str(exc.value).lower()


@pytest.mark.asyncio
class TestGitHubTrendingClient:
    """Test GitHub API client"""
    
    @pytest.fixture
    def github_client(self, mock_httpx_client):
        """GitHub client with mocked HTTP client"""
        return GitHubTrendingClient(http_client=mock_httpx_client)
    
    async def test_search_repositories_success(self, github_client, mock_httpx_client):
        """Should search and return repositories from GitHub"""
        # Arrange
        query = "transformer"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": 123456,
                    "name": "awesome-transformer",
                    "full_name": "user/awesome-transformer",
                    "description": "A collection of transformer implementations",
                    "stargazers_count": 1000,
                    "forks_count": 100,
                    "html_url": "https://github.com/user/awesome-transformer",
                    "language": "Python",
                    "topics": ["transformer", "ai"],
                    "created_at": "2020-01-01",
                    "updated_at": "2024-01-01",
                    "owner": {"login": "user"},
                }
            ]
        }
        mock_httpx_client.get.return_value = mock_response
        
        # Act
        results = await github_client.search_repositories(query)
        
        # Assert
        assert len(results) > 0
        assert results[0]["name"] == "awesome-transformer"
    
    async def test_search_handles_rate_limit(self, github_client, mock_httpx_client):
        """Should handle GitHub rate limiting"""
        # Arrange
        query = "transformer"
        mock_response = Mock()
        mock_response.status_code = 403
        mock_httpx_client.get.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(ExternalAPIError) as exc:
            await github_client.search_repositories(query)
        assert "rate limit" in str(exc.value).lower()


@pytest.mark.asyncio
class TestHackerNewsClient:
    """Test HackerNews API client"""
    
    @pytest.fixture
    def hn_client(self, mock_httpx_client):
        """HackerNews client with mocked HTTP client"""
        return HackerNewsClient(http_client=mock_httpx_client)
    
    async def test_get_top_stories(self, hn_client, mock_httpx_client):
        """Should get top story IDs"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [1, 2, 3, 4, 5]
        mock_httpx_client.get.return_value = mock_response
        
        # Act
        story_ids = await hn_client.get_top_stories(limit=5)
        
        # Assert
        assert len(story_ids) == 5
    
    async def test_get_item(self, hn_client, mock_httpx_client):
        """Should get a specific item"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "title": "Test Story",
            "type": "story",
            "url": "https://example.com",
        }
        mock_httpx_client.get.return_value = mock_response
        
        # Act
        item = await hn_client.get_item(1)
        
        # Assert
        assert item["title"] == "Test Story"


@pytest.mark.asyncio
class TestTavilyClient:
    """Test Tavily Search API client"""
    
    async def test_search_without_api_key(self):
        """Should raise error when API key is not configured"""
        # Arrange
        client = TavilySearchClient(api_key="")
        
        # Act & Assert
        with pytest.raises(ExternalAPIError) as exc:
            await client.search("test query")
        assert "not configured" in str(exc.value).lower()


@pytest.mark.asyncio
class TestWebScraper:
    """Test web scraping service"""
    
    @pytest.fixture
    def web_scraper(self, mock_httpx_client):
        """Web scraper with mocked HTTP client"""
        return WebScraper(http_client=mock_httpx_client)
    
    async def test_scrape_url_success(self, web_scraper, mock_httpx_client):
        """Should scrape content from URL"""
        # Arrange
        url = "https://example.com/article"
        
        # Mock robots.txt check
        robots_response = Mock()
        robots_response.status_code = 200
        robots_response.text = "User-agent: *\nAllow: /"
        
        # Mock article response
        article_response = Mock()
        article_response.status_code = 200
        article_response.text = """
        <html>
        <head><title>Article Title</title></head>
        <body>
            <article>
                <h1>Article Title</h1>
                <p>Content here with important information.</p>
            </article>
        </body>
        </html>
        """
        
        mock_httpx_client.get.side_effect = [robots_response, article_response]
        
        # Act
        result = await web_scraper.scrape(url)
        
        # Assert
        assert result["url"] == url
        assert "Article Title" in result["title"]
        assert result["content"] is not None
    
    async def test_scrape_handles_errors(self, web_scraper, mock_httpx_client):
        """Should handle scraping errors"""
        # Arrange
        url = "https://example.com/error"
        mock_httpx_client.get.side_effect = httpx.HTTPError("Connection error")
        
        # Act & Assert
        with pytest.raises(ExternalAPIError):
            await web_scraper.scrape(url)
