"""
Agentic Research Agent using LangGraph's create_react_agent
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain.agents import create_agent
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.arxiv import ArxivAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from app.core.config.environment_config import settings
from app.core.llm.bedrock_llm import BedrockLLM
from app.core.llm.prompt_loader import get_react_category_guidelines
from app.core.llm.prompts import prompts
from app.core.logging.logger import logger
from app.modules.research.models.research_model import TopicCategory


# ============= Output Model =============


class ResearchOutput(BaseModel):
    """Structured output from research agent"""

    topic_summary: str = Field(default='', description='Comprehensive topic summary')
    key_concepts: Dict[str, str] = Field(default_factory=dict, description='Key concepts')
    mathematical_foundations: Optional[str] = Field(
        None, description='Math foundations'
    )
    source_descriptions: Optional[str] = Field(
        None, description='Synthesized summary of sources'
    )
    implementation_examples: Optional[str] = Field(None, description='Code examples')
    sources: List[Dict[str, Any]] = Field(default_factory=list, description='Sources')
    research_data_path: Optional[str] = Field(None, description='Data file path')
    completeness_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description='Score'
    )


# ============= Tool Definitions =============


def create_research_tools() -> List[BaseTool]:
    """Create research tools for the agentic researcher."""
    tools: List[BaseTool] = []

    # 1. Tavily Search
    if settings.TAVILY_API_KEY:
        try:
            tools.append(
                TavilySearchResults(
                    max_results=5,
                    search_depth='advanced',
                    include_answer=True,
                    name='web_search',
                    description='Search the web for current information, tutorials, docs, news.',
                )
            )
        except Exception as e:
            logger.warning(f'Tavily init failed: {e}')

    # 2. ArXiv Search
    try:
        tools.append(
            ArxivQueryRun(
                api_wrapper=ArxivAPIWrapper(
                    top_k_results=5,
                    doc_content_chars_max=4000,
                    load_all_available_meta=True,
                ),
                name='arxiv_search',
                description='Search ArXiv for academic papers and research.',
            )
        )
    except Exception as e:
        logger.warning(f'ArXiv init failed: {e}')

    # 3. Wikipedia
    try:
        tools.append(
            WikipediaQueryRun(
                api_wrapper=WikipediaAPIWrapper(
                    top_k_results=3, doc_content_chars_max=4000
                ),
                name='wikipedia',
                description='Search Wikipedia for background info and definitions.',
            )
        )
    except Exception as e:
        logger.warning(f'Wikipedia init failed: {e}')

    # 4. Web Scraper
    @tool
    def scrape_url(url: str) -> str:
        """Scrape content from a URL to get detailed information."""
        try:
            loader = WebBaseLoader(web_paths=[url], requests_kwargs={'timeout': 10})
            docs = loader.load()
            return docs[0].page_content[:6000] if docs else f'No content at {url}'
        except Exception as e:
            return f'Error: {e}'

    tools.append(scrape_url)

    # 5. GitHub Search
    @tool
    def github_search(query: str, language: str = 'python') -> str:
        """Search GitHub for code repositories."""
        import httpx

        try:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Research-Agent',
            }
            if settings.GITHUB_TOKEN:
                headers['Authorization'] = f'token {settings.GITHUB_TOKEN}'

            with httpx.Client(timeout=30.0) as client:
                resp = client.get(
                    'https://api.github.com/search/repositories',
                    params={
                        'q': f'{query} language:{language}',
                        'sort': 'stars',
                        'per_page': 5,
                    },
                    headers=headers,
                )
                if resp.status_code != 200:
                    return f'GitHub API error: {resp.status_code}'

                repos = resp.json().get('items', [])
                if not repos:
                    return 'No repositories found.'

                return '\n'.join(
                    [
                        f"{i}. {r['full_name']} (⭐{r['stargazers_count']:,}) - "
                        f"{r.get('description', '')[:100]}"
                        for i, r in enumerate(repos, 1)
                    ]
                )
        except Exception as e:
            return f'Error: {e}'

    tools.append(github_search)

    logger.info(f'Created {len(tools)} research tools')
    return tools


# ============= Source Type Mapping =============

SOURCE_TYPES = {
    'web_search': 'web',
    'arxiv_search': 'paper',
    'wikipedia': 'encyclopedia',
    'github_search': 'github',
    'scrape_url': 'web',
}


# ============= Agentic Researcher =============


class AgenticResearcher:
    """LangChain v1.1.0 Agent for research."""

    def __init__(
        self, llm: Optional[BedrockLLM] = None, max_iterations: int = 10
    ):
        self.llm = llm or BedrockLLM()
        self.max_iterations = max_iterations
        self.tools = create_research_tools()

        # Create agent using LangChain v1.0+ API
        self.agent = create_agent(
            model=self.llm.llm,
            tools=self.tools,
        )

        logger.info(f'AgenticResearcher initialized: {len(self.tools)} tools')

    async def research(
        self,
        query: str,
        category: TopicCategory,
        target_audience: str = 'practitioner',
    ) -> ResearchOutput:
        """Execute research using LangChain v1.1.0 agent with ainvoke."""
        logger.info(
            f"[RESEARCH] Query: '{query[:60]}...' | Category: {category.value}"
        )

        # Build messages
        messages = [
            SystemMessage(content=prompts.research.system_prompt()),
            HumanMessage(
                content=prompts.research.user_prompt(
                    query=query,
                    category=category.value,
                    category_guidelines=get_react_category_guidelines(category.value),
                    target_audience=target_audience,
                    max_iterations=self.max_iterations,
                )
            ),
        ]

        agent_config = {
            'recursion_limit': self.max_iterations * 2 + 5,
        }

        try:
            logger.info(
                f"[AGENT] Starting (recursion_limit={agent_config['recursion_limit']})"
            )

            result = await self.agent.ainvoke(
                {'messages': messages},
                config=agent_config,
            )
            logger.info(f"[AGENT] result: {result['messages']}")

            tool_calls, tool_results, final_content = self._extract_from_messages(
                result['messages']
            )

            logger.info(
                f'[AGENT] Done: {len(tool_calls)} tool calls, {len(tool_results)} results'
            )

            output = self._parse_output(
                final_content, tool_calls, tool_results, query, category
            )

            output.research_data_path = await self._save(query, output)

            logger.info(f'[RESEARCH] Complete: score={output.completeness_score:.2f}')
            return output

        except Exception as e:
            logger.error(f'[RESEARCH] Failed: {e}', exc_info=True)
            return ResearchOutput(
                topic_summary=f'Research failed: {str(e)}',
                key_concepts={'error': str(e)},
            )

    def _extract_from_messages(
        self, messages: List[BaseMessage]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
        """Extract tool calls, results, and final content from messages."""
        tool_calls: List[Dict[str, Any]] = []
        tool_results: List[Dict[str, Any]] = []
        final_content = ''

        logger.info(f'[MESSAGES] messages length: {len(messages)}')

        for msg in messages:
            logger.info(f'[MESSAGES] message type: {type(msg)} : {msg}')
            if isinstance(msg, AIMessage):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        name = tc.get('name', 'unknown')
                        args = tc.get('args', {})
                        logger.info(f'[TOOL] {name}: {str(args)[:60]}')
                        tool_calls.append(
                            {
                                'tool': name,
                                'query': str(args)[:100],
                                'type': SOURCE_TYPES.get(name, 'web'),
                            }
                        )

                if msg.content:
                    final_content = msg.content

            elif isinstance(msg, ToolMessage) and msg.content:
                name = getattr(msg, 'name', 'unknown')
                logger.info(f'[TOOL] Result: {name} ({len(msg.content)} chars)')
                tool_results.append(
                    {
                        'tool': name,
                        'content': msg.content[:4000],
                    }
                )

        return tool_calls, tool_results, final_content

    def _parse_output(
        self,
        content: str,
        tool_calls: List[Dict],
        tool_results: List[Dict],
        query: str,
        category: TopicCategory,
    ) -> ResearchOutput:
        """Parse agent's JSON output into ResearchOutput."""
        data = {}

        if content:
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    data = json.loads(content[start:end])
                    logger.info(f'[PARSE] JSON keys: {list(data.keys())}')
            except json.JSONDecodeError as e:
                logger.warning(f'[PARSE] JSON error: {e}')

        # Deduplicate sources
        sources = []
        seen = set()
        for tc in tool_calls:
            key = f"{tc['tool']}:{tc['query'][:40]}"
            if key not in seen:
                seen.add(key)
                sources.append(tc)

        source_summary = self._build_source_summary(tool_results)

        if not data.get('topic_summary') or len(data.get('topic_summary', '')) < 100:
            logger.warning('[PARSE] Using fallback')
            data = {
                'topic_summary': f'Research on: {query}. Collected {len(sources)} sources.',
                'key_concepts': {'query': query},
            }

        output = ResearchOutput(
            topic_summary=data.get('topic_summary', ''),
            key_concepts=data.get('key_concepts', {}),
            mathematical_foundations=data.get('mathematical_foundations'),
            source_descriptions=source_summary,
            implementation_examples=data.get('implementation_examples'),
            sources=sources,
        )

        output.completeness_score = self._calculate_score(output, category)
        logger.info(
            f'[PARSE] Output: {len(output.topic_summary)} chars, {len(sources)} sources'
        )

        return output

    def _build_source_summary(self, tool_results: List[Dict]) -> str:
        """Build source summary from tool results."""
        if not tool_results:
            return ''

        grouped = {}
        for r in tool_results:
            tool = r.get('tool', 'unknown')
            grouped.setdefault(tool, []).append(1)

        labels = {
            'web_search': 'Web Search',
            'arxiv_search': 'Academic Papers',
            'wikipedia': 'Wikipedia',
            'github_search': 'GitHub',
            'scrape_url': 'Web Content',
        }

        parts = [
            f"**{labels.get(t, t)}** ({len(c)} results)" for t, c in grouped.items()
        ]
        return 'Sources: ' + ', '.join(parts) if parts else ''

    def _calculate_score(
        self, output: ResearchOutput, category: TopicCategory
    ) -> float:
        """Calculate completeness score (0-1)."""
        score = 0.0

        if len(output.topic_summary) > 1000:
            score += 2.0
        elif len(output.topic_summary) > 500:
            score += 1.5
        elif len(output.topic_summary) > 200:
            score += 1.0

        concepts = len(output.key_concepts)
        if concepts >= 5:
            score += 1.0
        elif concepts >= 3:
            score += 0.7
        elif concepts >= 1:
            score += 0.3

        sources = len(output.sources)
        if sources >= 8:
            score += 1.0
        elif sources >= 5:
            score += 0.7
        elif sources >= 3:
            score += 0.4

        if category == TopicCategory.CORE_AI:
            if (
                output.mathematical_foundations
                and len(output.mathematical_foundations) > 50
            ):
                score += 1.0
        else:
            if (
                output.implementation_examples
                and len(output.implementation_examples) > 50
            ):
                score += 1.0

        return min(score / 5.0, 1.0)

    async def _save(self, query: str, output: ResearchOutput) -> str:
        """Save research to JSON file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_query = ''.join(c if c.isalnum() else '_' for c in query[:50])
            filename = f'{timestamp}_{safe_query}.json'

            research_dir = Path(settings.DATA_DIR) / 'research' / 'summaries'
            research_dir.mkdir(parents=True, exist_ok=True)

            filepath = research_dir / filename
            filepath.write_text(
                json.dumps(
                    {
                        'query': query,
                        'agent_type': 'agentic_researcher',
                        'topic_summary': output.topic_summary,
                        'key_concepts': output.key_concepts,
                        'mathematical_foundations': output.mathematical_foundations,
                        'source_summary': output.source_descriptions,
                        'implementation_examples': output.implementation_examples,
                        'sources': output.sources,
                        'completeness_score': output.completeness_score,
                        'created_at': datetime.now().isoformat(),
                    },
                    indent=2,
                    default=str,
                )
            )

            logger.info(f'[SAVE] {filepath}')
            return str(filepath)
        except Exception as e:
            logger.error(f'[SAVE] Failed: {e}')
            return ''


# ============= Factory =============


def get_agentic_researcher(
    llm: Optional[BedrockLLM] = None,
    max_iterations: int = 10,
) -> AgenticResearcher:
    """Create AgenticResearcher instance."""
    return AgenticResearcher(llm=llm, max_iterations=max_iterations)


