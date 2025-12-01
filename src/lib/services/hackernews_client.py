"""
HackerNews API client for tech news and discussions
"""
from typing import List, Dict, Any, Optional
import httpx
import asyncio

from src.common.config import config
from src.common.logger import setup_logger
from src.lib.models.exceptions import ExternalAPIError

logger = setup_logger(__name__)


class HackerNewsClient:
    """
    Client for HackerNews Firebase API
    Fetches tech news, stories, and discussions
    """
    
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        """
        Initialize HackerNews client
        
        Args:
            http_client: Optional httpx client (for testing)
        """
        self._http_client = http_client
        self.rate_limit_delay = 0.5  # HN API is relatively permissive
        logger.info("Initialized HackerNews client")
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def get_top_stories(self, limit: int = 30) -> List[int]:
        """
        Get IDs of top stories
        
        Args:
            limit: Maximum number of story IDs to return
        
        Returns:
            List of story IDs
        """
        try:
            url = f"{self.BASE_URL}/topstories.json"
            response = await self.http_client.get(url)
            
            if response.status_code != 200:
                raise ExternalAPIError(f"HN API error: {response.status_code}")
            
            story_ids = response.json()
            return story_ids[:limit]
            
        except httpx.HTTPError as e:
            logger.error(f"HN HTTP error: {e}")
            raise ExternalAPIError(f"HN API request failed: {e}")
    
    async def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific item (story, comment, etc.)
        
        Args:
            item_id: Item ID
        
        Returns:
            Item data or None if not found
        """
        try:
            url = f"{self.BASE_URL}/item/{item_id}.json"
            
            await asyncio.sleep(self.rate_limit_delay)
            response = await self.http_client.get(url)
            
            if response.status_code != 200:
                return None
            
            return response.json()
            
        except Exception as e:
            logger.error(f"HN get item error: {e}")
            return None
    
    async def get_stories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top stories with full details
        
        Args:
            limit: Maximum number of stories
        
        Returns:
            List of story data
        """
        try:
            story_ids = await self.get_top_stories(limit=limit)
            
            # Fetch story details concurrently (with rate limiting)
            stories = []
            for story_id in story_ids:
                story = await self.get_item(story_id)
                if story and story.get("type") == "story":
                    stories.append({
                        "id": story["id"],
                        "title": story.get("title"),
                        "url": story.get("url"),
                        "score": story.get("score", 0),
                        "by": story.get("by"),
                        "time": story.get("time"),
                        "descendants": story.get("descendants", 0),
                        "text": story.get("text"),  # For text posts
                        "hn_url": f"https://news.ycombinator.com/item?id={story['id']}",
                    })
            
            logger.info(f"HN fetched {len(stories)} stories")
            return stories
            
        except Exception as e:
            logger.error(f"HN get stories error: {e}")
            raise ExternalAPIError(f"HN fetch stories failed: {e}")
    
    async def search_ai_topics(
        self,
        query: str = "AI",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for AI-related stories in top stories
        
        Args:
            query: Search term to filter by
            limit: Maximum number of results
        
        Returns:
            List of matching stories
        """
        try:
            # Get more stories to filter from
            stories = await self.get_stories(limit=50)
            
            # Filter by query (simple title matching)
            query_lower = query.lower()
            ai_keywords = ["ai", "ml", "machine learning", "deep learning", 
                         "neural", "gpt", "llm", "transformer", "openai",
                         "anthropic", "claude", "gemini", "langchain"]
            
            matching = []
            for story in stories:
                title = (story.get("title") or "").lower()
                
                # Check if query matches or if it's AI-related
                if query_lower in title or any(kw in title for kw in ai_keywords):
                    matching.append(story)
                    if len(matching) >= limit:
                        break
            
            logger.info(f"HN search found {len(matching)} AI-related stories")
            return matching
            
        except Exception as e:
            logger.error(f"HN search error: {e}")
            raise ExternalAPIError(f"HN search failed: {e}")
    
    async def get_new_stories(self, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get newest stories
        
        Args:
            limit: Maximum number of stories
        
        Returns:
            List of new story data
        """
        try:
            url = f"{self.BASE_URL}/newstories.json"
            response = await self.http_client.get(url)
            
            if response.status_code != 200:
                raise ExternalAPIError(f"HN API error: {response.status_code}")
            
            story_ids = response.json()[:limit]
            
            stories = []
            for story_id in story_ids:
                story = await self.get_item(story_id)
                if story and story.get("type") == "story":
                    stories.append({
                        "id": story["id"],
                        "title": story.get("title"),
                        "url": story.get("url"),
                        "score": story.get("score", 0),
                        "by": story.get("by"),
                        "time": story.get("time"),
                        "hn_url": f"https://news.ycombinator.com/item?id={story['id']}",
                    })
            
            return stories
            
        except Exception as e:
            logger.error(f"HN new stories error: {e}")
            raise ExternalAPIError(f"HN fetch new stories failed: {e}")
    
    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()

