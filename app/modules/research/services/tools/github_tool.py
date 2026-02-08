"""
GitHub Search Tool

Provides GitHub repository search capabilities.
"""
from typing import Optional

from langchain_core.tools import BaseTool, tool

from app.core.config.environment_config import settings
from app.core.logging.logger import logger


def create_github_tool() -> Optional[BaseTool]:
    """
    Create GitHub search tool.
    
    Returns:
        GitHub search tool if initialization succeeds, None otherwise
    """
    try:

        @tool
        def github_search(query: str, language: str = "python") -> str:
            """Search GitHub for code repositories."""
            import httpx

            try:
                headers = {
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "Research-Agent",
                }

                if settings.GITHUB_TOKEN:
                    headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        "https://api.github.com/search/repositories",
                        params={
                            "q": f"{query} language:{language}",
                            "sort": "stars",
                            "per_page": 5,
                        },
                        headers=headers,
                    )

                    if response.status_code != 200:
                        return f"GitHub API error: {response.status_code}"

                    repos = response.json().get("items", [])
                    if not repos:
                        return "No repositories found."

                    results = []
                    for i, repo in enumerate(repos, 1):
                        stars = repo["stargazers_count"]
                        description = repo.get("description", "")[:100]
                        results.append(
                            f"{i}. {repo['full_name']} (⭐{stars:,}) - {description}"
                        )

                    return "\n".join(results)

            except Exception as e:
                return f"Error searching GitHub: {e}"

        logger.info("GitHub search tool initialized")
        return github_search

    except Exception as e:
        logger.warning(f"GitHub tool initialization failed: {e}")
        return None
