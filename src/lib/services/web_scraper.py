"""
Web scraping service for extracting content from web pages
"""
from typing import Dict, Any, Optional, List
import httpx
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urlparse

from src.common.config import config
from src.common.logger import setup_logger
from src.lib.models.exceptions import ExternalAPIError

logger = setup_logger(__name__)


class WebScraper:
    """
    Web scraping service for extracting content from URLs
    Respects robots.txt and implements rate limiting
    """
    
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        """
        Initialize web scraper
        
        Args:
            http_client: Optional httpx client (for testing)
        """
        self._http_client = http_client
        self.rate_limit_delay = 1.0 / config.EXTERNAL_API_RATE_LIMIT_RPS
        self._robots_cache: Dict[str, bool] = {}
        logger.info("Initialized WebScraper")
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "AI-Research-Agent/1.0 (Research Bot)",
                    "Accept": "text/html,application/xhtml+xml,application/xml",
                },
                follow_redirects=True,
            )
        return self._http_client
    
    async def check_robots_txt(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt
        
        Args:
            url: URL to check
        
        Returns:
            True if allowed, False if disallowed
        """
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            # Check cache
            if base_url in self._robots_cache:
                return self._robots_cache[base_url]
            
            # Fetch robots.txt
            robots_url = f"{base_url}/robots.txt"
            response = await self.http_client.get(robots_url)
            
            # If no robots.txt, assume allowed
            if response.status_code != 200:
                self._robots_cache[base_url] = True
                return True
            
            # Simple robots.txt parsing
            robots_content = response.text.lower()
            
            # Check for disallow all
            if "user-agent: *" in robots_content and "disallow: /" in robots_content:
                # Check if there's a specific allow for our user-agent
                self._robots_cache[base_url] = False
                return False
            
            self._robots_cache[base_url] = True
            return True
            
        except Exception as e:
            logger.warning(f"robots.txt check failed for {url}: {e}")
            return True  # Assume allowed if check fails
    
    async def scrape(
        self,
        url: str,
        extract_code: bool = True,
        max_content_length: int = 50000,
    ) -> Dict[str, Any]:
        """
        Scrape content from a URL
        
        Args:
            url: URL to scrape
            extract_code: Whether to extract code blocks
            max_content_length: Maximum content length to return
        
        Returns:
            Scraped content with metadata
        """
        try:
            # Check robots.txt
            if not await self.check_robots_txt(url):
                raise ExternalAPIError(f"URL disallowed by robots.txt: {url}")
            
            logger.debug(f"Scraping: {url}")
            
            await asyncio.sleep(self.rate_limit_delay)
            response = await self.http_client.get(url)
            
            if response.status_code != 200:
                raise ExternalAPIError(f"HTTP error {response.status_code} for {url}")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            
            # Extract title
            title = ""
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)
            
            # Try to find main content
            main_content = None
            for selector in ["article", "main", ".content", "#content", ".post", ".article"]:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find("body")
            
            # Extract text content
            content = ""
            if main_content:
                content = main_content.get_text(separator="\n", strip=True)
            
            # Truncate if too long
            if len(content) > max_content_length:
                content = content[:max_content_length] + "..."
            
            # Extract code blocks if requested
            code_blocks = []
            if extract_code:
                for code in soup.find_all(["code", "pre"]):
                    code_text = code.get_text(strip=True)
                    if len(code_text) > 20:  # Skip very short snippets
                        code_blocks.append(code_text[:2000])  # Limit code length
            
            # Extract meta description
            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "")
            
            result = {
                "url": url,
                "title": title,
                "content": content,
                "description": description,
                "code_blocks": code_blocks[:10],  # Limit number of code blocks
                "word_count": len(content.split()),
            }
            
            logger.info(f"Scraped {url}: {result['word_count']} words")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Scrape HTTP error: {e}")
            raise ExternalAPIError(f"Failed to scrape {url}: {e}")
    
    async def scrape_multiple(
        self,
        urls: List[str],
        max_concurrent: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs with concurrency control
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
        
        Returns:
            List of scraped content
        """
        results = []
        
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            batch_results = await asyncio.gather(
                *[self.scrape(url) for url in batch],
                return_exceptions=True,
            )
            
            for url, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to scrape {url}: {result}")
                    results.append({
                        "url": url,
                        "error": str(result),
                        "content": None,
                    })
                else:
                    results.append(result)
        
        return results
    
    async def extract_links(self, url: str, filter_domain: bool = True) -> List[str]:
        """
        Extract links from a page
        
        Args:
            url: URL to extract links from
            filter_domain: Only return links from same domain
        
        Returns:
            List of URLs
        """
        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            parsed_base = urlparse(url)
            links = []
            
            for a in soup.find_all("a", href=True):
                href = a["href"]
                
                # Handle relative URLs
                if href.startswith("/"):
                    href = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
                elif not href.startswith("http"):
                    continue
                
                # Filter by domain if requested
                if filter_domain:
                    parsed_href = urlparse(href)
                    if parsed_href.netloc != parsed_base.netloc:
                        continue
                
                links.append(href)
            
            return list(set(links))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Extract links error: {e}")
            return []
    
    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()

