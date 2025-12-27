"""
GitHub API client for repository search and trending repos
"""
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.common.exceptions.research_exceptions import ExternalAPIError
from app.core.config.environment_config import settings
from app.core.logging.logger import logger


class GitHubTrendingClient:
    """Client for GitHub API"""

    BASE_URL = 'https://api.github.com'

    def __init__(
        self,
        token: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.token = token or settings.GITHUB_TOKEN
        self._http_client = http_client
        self.rate_limit_delay = 1.0 / settings.EXTERNAL_API_RATE_LIMIT_RPS
        logger.info('Initialized GitHub client')

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'AI-Research-Agent',
            }
            if self.token:
                headers['Authorization'] = f'token {self.token}'

            self._http_client = httpx.AsyncClient(
                headers=headers,
                timeout=30.0,
            )
        return self._http_client

    async def search_repositories(
        self,
        query: str,
        sort: str = 'stars',
        order: str = 'desc',
        max_results: int = 10,
        language: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search GitHub repositories"""
        try:
            search_query = query
            if language:
                search_query += f' language:{language}'

            params = {
                'q': search_query,
                'sort': sort,
                'order': order,
                'per_page': min(max_results, 100),
            }

            url = f'{self.BASE_URL}/search/repositories'
            logger.debug(f'GitHub search: {query[:100]}...')

            await asyncio.sleep(self.rate_limit_delay)
            response = await self.http_client.get(url, params=params)

            if response.status_code == 403:
                raise ExternalAPIError('GitHub rate limit exceeded')

            if response.status_code != 200:
                raise ExternalAPIError(f'GitHub API error: {response.status_code}')

            data = response.json()
            repos = [
                {
                    'id': repo['id'],
                    'name': repo['name'],
                    'full_name': repo['full_name'],
                    'description': repo.get('description'),
                    'url': repo['html_url'],
                    'stars': repo['stargazers_count'],
                    'forks': repo['forks_count'],
                    'language': repo.get('language'),
                    'topics': repo.get('topics', []),
                    'created_at': repo['created_at'],
                    'updated_at': repo['updated_at'],
                    'owner': repo['owner']['login'],
                }
                for repo in data.get('items', [])
            ]

            logger.info(f'GitHub search returned {len(repos)} repositories')
            return repos

        except httpx.HTTPError as e:
            logger.error(f'GitHub HTTP error: {e}')
            raise ExternalAPIError(f'GitHub API request failed: {e}')

    async def get_trending(
        self,
        language: Optional[str] = 'python',
        since: str = 'weekly',
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get trending repositories"""
        try:
            days_map = {'daily': 1, 'weekly': 7, 'monthly': 30}
            days = days_map.get(since, 7)
            date_threshold = (datetime.now() - timedelta(days=days)).strftime(
                '%Y-%m-%d'
            )

            query = f'created:>{date_threshold} stars:>10'
            if language:
                query += f' language:{language}'

            ai_query = (
                f'{query} (machine-learning OR deep-learning OR AI OR transformer OR LLM)'
            )

            repos = await self.search_repositories(
                query=ai_query,
                sort='stars',
                order='desc',
                max_results=max_results,
            )

            return repos

        except Exception as e:
            logger.error(f'GitHub trending error: {e}')
            raise ExternalAPIError(f'GitHub trending fetch failed: {e}')

    async def get_repository(
        self, owner: str, repo: str
    ) -> Optional[Dict[str, Any]]:
        """Get details for a specific repository"""
        try:
            url = f'{self.BASE_URL}/repos/{owner}/{repo}'

            await asyncio.sleep(self.rate_limit_delay)
            response = await self.http_client.get(url)

            if response.status_code == 404:
                return None

            if response.status_code != 200:
                raise ExternalAPIError(f'GitHub API error: {response.status_code}')

            repo_data = response.json()
            return {
                'id': repo_data['id'],
                'name': repo_data['name'],
                'full_name': repo_data['full_name'],
                'description': repo_data.get('description'),
                'url': repo_data['html_url'],
                'stars': repo_data['stargazers_count'],
                'forks': repo_data['forks_count'],
                'language': repo_data.get('language'),
                'topics': repo_data.get('topics', []),
                'readme_url': f"{repo_data['html_url']}/blob/main/README.md",
            }

        except Exception as e:
            logger.error(f'GitHub get repository error: {e}')
            return None

    async def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """Get repository README content"""
        try:
            url = f'{self.BASE_URL}/repos/{owner}/{repo}/readme'

            await asyncio.sleep(self.rate_limit_delay)
            response = await self.http_client.get(
                url,
                headers={'Accept': 'application/vnd.github.raw'},
            )

            if response.status_code == 200:
                return response.text
            return None

        except Exception as e:
            logger.error(f'GitHub get README error: {e}')
            return None

    async def close(self):
        """Close HTTP client"""
        if self._http_client:
            await self._http_client.aclose()


