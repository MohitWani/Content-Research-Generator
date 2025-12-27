"""
Tavily Search API client for AI-powered web search
"""
from typing import Any, Dict, Optional

from tavily import TavilyClient as TavilyAPI

from app.common.exceptions.research_exceptions import ExternalAPIError
from app.core.config.environment_config import settings
from app.core.logging.logger import logger


class TavilySearchClient:
    """Client for Tavily AI search API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.TAVILY_API_KEY
        if not self.api_key:
            logger.warning('Tavily API key not configured')
            self.client = None
        else:
            self.client = TavilyAPI(api_key=self.api_key)
            logger.info('Initialized Tavily search client')

    async def search(
        self,
        query: str,
        search_depth: str = 'advanced',
        max_results: int = 10,
        include_answer: bool = True,
        include_raw_content: bool = False,
    ) -> Dict[str, Any]:
        """Perform AI-powered search using Tavily"""
        if not self.client:
            raise ExternalAPIError('Tavily API key not configured')

        try:
            logger.debug(f'Tavily search: {query[:100]}...')

            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
            )

            results = {
                'query': query,
                'answer': response.get('answer'),
                'results': [
                    {
                        'title': r.get('title'),
                        'url': r.get('url'),
                        'content': r.get('content'),
                        'score': r.get('score'),
                        'raw_content': r.get('raw_content')
                        if include_raw_content
                        else None,
                    }
                    for r in response.get('results', [])
                ],
                'sources_count': len(response.get('results', [])),
            }

            logger.info(f"Tavily search returned {results['sources_count']} results")
            return results

        except Exception as e:
            logger.error(f'Tavily search error: {e}')
            raise ExternalAPIError(f'Tavily search failed: {e}')

    async def search_context(
        self,
        query: str,
        max_results: int = 5,
    ) -> str:
        """Get search context optimized for LLM consumption"""
        if not self.client:
            raise ExternalAPIError('Tavily API key not configured')

        try:
            context = self.client.get_search_context(
                query=query,
                max_results=max_results,
            )
            return context
        except Exception as e:
            logger.error(f'Tavily context search error: {e}')
            raise ExternalAPIError(f'Tavily context search failed: {e}')

    async def qna_search(self, query: str) -> str:
        """Get a direct answer to a question"""
        if not self.client:
            raise ExternalAPIError('Tavily API key not configured')

        try:
            answer = self.client.qna_search(query=query)
            return answer
        except Exception as e:
            logger.error(f'Tavily QnA error: {e}')
            raise ExternalAPIError(f'Tavily QnA search failed: {e}')


