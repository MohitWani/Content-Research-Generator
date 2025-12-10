"""
ArXiv API client for research paper search and retrieval
"""
from typing import List, Dict, Any, Optional
import httpx
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
import asyncio

from src.common.config import config
from src.common.logger import setup_logger
from src.lib.models.exceptions import ExternalAPIError

logger = setup_logger(__name__)


class ArXivClient:
    """
    Client for ArXiv API
    Searches and retrieves academic papers
    """
    
    BASE_URL = "https://export.arxiv.org/api/query"
    NAMESPACES = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }
    
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        """
        Initialize ArXiv client
        
        Args:
            http_client: Optional httpx client (for testing)
        """
        self._http_client = http_client
        self.rate_limit_delay = 1.0 / config.EXTERNAL_API_RATE_LIMIT_RPS
        logger.info("Initialized ArXiv client")
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        return self._http_client
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
        categories: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search ArXiv for papers
        
        Args:
            query: Search query
            max_results: Maximum number of results
            sort_by: Sort field (relevance, lastUpdatedDate, submittedDate)
            sort_order: ascending or descending
            categories: Optional list of arxiv categories (e.g., ["cs.AI", "cs.LG"])
        
        Returns:
            List of paper metadata
        """
        try:
            # Build search query
            search_query = query
            if categories:
                cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
                search_query = f"({query}) AND ({cat_query})"
            
            params = {
                "search_query": f"all:{search_query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": sort_by,
                "sortOrder": sort_order,
            }
            
            url = f"{self.BASE_URL}?{urlencode(params)}"
            logger.debug(f"ArXiv search: {query[:100]}...")
            
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            response = await self.http_client.get(url)
            
            if response.status_code == 429:
                raise ExternalAPIError("ArXiv rate limit exceeded")
            
            if response.status_code != 200:
                raise ExternalAPIError(f"ArXiv API error: {response.status_code}")
            
            # Parse XML response
            papers = self._parse_response(response.text)
            logger.info(f"ArXiv search returned {len(papers)} papers")
            
            return papers
            
        except httpx.HTTPError as e:
            logger.error(f"ArXiv HTTP error: {e}")
            raise ExternalAPIError(f"ArXiv API request failed: {e}")
    
    def _parse_response(self, xml_text: str) -> List[Dict[str, Any]]:
        """Parse ArXiv API XML response"""
        papers = []
        
        try:
            root = ET.fromstring(xml_text)
            
            for entry in root.findall("atom:entry", self.NAMESPACES):
                paper = {
                    "id": self._get_text(entry, "atom:id"),
                    "title": self._get_text(entry, "atom:title", "").strip().replace("\n", " "),
                    "summary": self._get_text(entry, "atom:summary", "").strip().replace("\n", " "),
                    "published": self._get_text(entry, "atom:published"),
                    "updated": self._get_text(entry, "atom:updated"),
                    "authors": [
                        author.find("atom:name", self.NAMESPACES).text
                        for author in entry.findall("atom:author", self.NAMESPACES)
                        if author.find("atom:name", self.NAMESPACES) is not None
                    ],
                    "categories": [
                        cat.get("term")
                        for cat in entry.findall("atom:category", self.NAMESPACES)
                    ],
                    "pdf_url": None,
                    "abs_url": None,
                }
                
                # Extract links
                for link in entry.findall("atom:link", self.NAMESPACES):
                    if link.get("title") == "pdf":
                        paper["pdf_url"] = link.get("href")
                    elif link.get("type") == "text/html":
                        paper["abs_url"] = link.get("href")
                
                # Extract arxiv ID from full ID URL
                if paper["id"]:
                    paper["arxiv_id"] = paper["id"].split("/abs/")[-1]
                
                papers.append(paper)
                
        except ET.ParseError as e:
            logger.error(f"ArXiv XML parse error: {e}")
        
        return papers
    
    def _get_text(self, element: ET.Element, path: str, default: str = None) -> Optional[str]:
        """Get text content from XML element"""
        node = element.find(path, self.NAMESPACES)
        return node.text if node is not None else default
    
    async def get_paper(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by ArXiv ID
        
        Args:
            arxiv_id: ArXiv paper ID (e.g., "1706.03762")
        
        Returns:
            Paper metadata or None if not found
        """
        try:
            params = {"id_list": arxiv_id}
            url = f"{self.BASE_URL}?{urlencode(params)}"
            
            await asyncio.sleep(self.rate_limit_delay)
            response = await self.http_client.get(url)
            
            if response.status_code != 200:
                return None
            
            papers = self._parse_response(response.text)
            return papers[0] if papers else None
            
        except Exception as e:
            logger.error(f"ArXiv get paper error: {e}")
            return None
    
    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()

