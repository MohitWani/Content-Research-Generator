"""
ArXiv Paper Research Agent
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.common.exceptions.research_exceptions import (
    InvalidArXivIdError,
    MultiplePapersLimitError,
    PaperContentInsufficientError,
    PaperNotFoundError,
)
from app.common.services.arxiv_client import ArXivClient
from app.common.services.arxiv_id_parser import get_base_id, normalize_arxiv_id, validate_arxiv_id
from app.core.config.environment_config import settings
from app.core.llm.bedrock_llm import BedrockLLM
from app.core.llm.prompt_loader import get_audience_guidelines
from app.core.llm.prompts import prompts
from app.core.logging.logger import logger


@dataclass
class PaperMetadata:
    """Metadata for an ArXiv paper"""

    arxiv_id: str
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: str = ''
    published: str = ''
    updated: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    pdf_url: Optional[str] = None
    abs_url: Optional[str] = None

    @classmethod
    def from_arxiv_response(cls, data: Dict[str, Any]) -> 'PaperMetadata':
        """Create PaperMetadata from ArXiv API response"""
        return cls(
            arxiv_id=data.get('arxiv_id', ''),
            title=data.get('title', ''),
            authors=data.get('authors', []),
            abstract=data.get('summary', ''),
            published=data.get('published', ''),
            updated=data.get('updated'),
            categories=data.get('categories', []),
            pdf_url=data.get('pdf_url'),
            abs_url=data.get('abs_url'),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'arxiv_id': self.arxiv_id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'published': self.published,
            'updated': self.updated,
            'categories': self.categories,
            'pdf_url': self.pdf_url,
            'abs_url': self.abs_url,
        }


@dataclass
class PaperResearchOutput:
    """Enhanced research output for ArXiv paper analysis"""

    paper_metadata: PaperMetadata
    topic_summary: str = ''
    key_concepts: Dict[str, str] = field(default_factory=dict)
    mathematical_foundations: Optional[str] = None
    historical_context: Optional[str] = None
    implementation_examples: Optional[str] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
    paper_overview: str = ''
    methodology_deep_dive: str = ''
    experimental_results: Optional[str] = None
    practical_implications: str = ''
    limitations_future_work: Optional[str] = None
    related_work_summary: Optional[str] = None
    citation: str = ''
    completeness_score: float = 0.0
    research_data_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'paper_metadata': self.paper_metadata.to_dict(),
            'topic_summary': self.topic_summary,
            'key_concepts': self.key_concepts,
            'mathematical_foundations': self.mathematical_foundations,
            'historical_context': self.historical_context,
            'implementation_examples': self.implementation_examples,
            'sources': self.sources,
            'paper_overview': self.paper_overview,
            'methodology_deep_dive': self.methodology_deep_dive,
            'experimental_results': self.experimental_results,
            'practical_implications': self.practical_implications,
            'limitations_future_work': self.limitations_future_work,
            'related_work_summary': self.related_work_summary,
            'citation': self.citation,
            'completeness_score': self.completeness_score,
            'research_data_path': self.research_data_path,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class BlogOutput:
    """Output from blog generation for a paper"""

    title: str
    content: str
    meta_description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    estimated_reading_time: Optional[str] = None
    file_path: Optional[str] = None


class ArXivPaperResearchAgent:
    """Agent for deep research analysis of ArXiv papers"""

    MINIMUM_ABSTRACT_WORDS = 50
    MAX_PAPERS_PER_REQUEST = 5

    def __init__(
        self,
        llm: Optional[BedrockLLM] = None,
        arxiv_client: Optional[ArXivClient] = None,
    ):
        self.llm = llm or BedrockLLM()
        self.arxiv_client = arxiv_client or ArXivClient()
        logger.info('Initialized ArXivPaperResearchAgent')

    async def research_paper_by_id(
        self,
        arxiv_id: str,
        target_audience: str = 'practitioner',
    ) -> PaperResearchOutput:
        """Research a paper by its ArXiv ID"""
        logger.info(f'Starting paper research for: {arxiv_id}')

        if not validate_arxiv_id(arxiv_id):
            raise InvalidArXivIdError(arxiv_id)

        normalized_id = normalize_arxiv_id(arxiv_id)
        base_id = get_base_id(arxiv_id)

        paper_data = await self._fetch_paper_metadata(base_id)
        self._validate_paper_content(paper_data)

        paper_metadata = PaperMetadata.from_arxiv_response(paper_data)
        context = self._build_research_context(paper_data)

        research_output = await self._conduct_paper_research(
            context=context,
            paper_metadata=paper_metadata,
            target_audience=target_audience,
        )

        research_output.completeness_score = self._calculate_completeness_score(
            research_output
        )
        research_output.citation = self._generate_citation(paper_data)

        research_output.sources.append(
            {
                'type': 'paper',
                'title': paper_metadata.title,
                'url': paper_metadata.abs_url
                or f'https://arxiv.org/abs/{normalized_id}',
                'authors': paper_metadata.authors,
                'arxiv_id': normalized_id,
            }
        )

        research_output.research_data_path = await self._save_research_data(
            research_output
        )

        logger.info(
            f'Paper research completed with score: {research_output.completeness_score:.2f}'
        )

        return research_output

    async def research_paper_by_title(
        self,
        title: str,
        target_audience: str = 'practitioner',
    ) -> PaperResearchOutput:
        """Search for a paper by title and research it"""
        logger.info(f'Searching for paper: {title}')

        results = await self.arxiv_client.search(title, max_results=1)

        if not results:
            raise PaperNotFoundError(f'No paper found matching: {title}')

        paper_data = results[0]
        arxiv_id = paper_data.get('arxiv_id', '')

        if not arxiv_id:
            raise PaperNotFoundError(f'No valid ArXiv ID in search results for: {title}')

        logger.info(f"Found paper: {arxiv_id} - {paper_data.get('title', '')}")

        return await self.research_paper_by_id(arxiv_id, target_audience)

    async def research_multiple_papers(
        self,
        arxiv_ids: List[str],
        target_audience: str = 'practitioner',
    ) -> PaperResearchOutput:
        """Research multiple papers and synthesize findings"""
        if len(arxiv_ids) > self.MAX_PAPERS_PER_REQUEST:
            raise MultiplePapersLimitError(len(arxiv_ids), self.MAX_PAPERS_PER_REQUEST)

        logger.info(f'Researching {len(arxiv_ids)} papers')

        research_outputs = []
        for arxiv_id in arxiv_ids:
            try:
                output = await self.research_paper_by_id(arxiv_id, target_audience)
                research_outputs.append(output)
            except Exception as e:
                logger.warning(f'Failed to research paper {arxiv_id}: {e}')

        if not research_outputs:
            raise PaperNotFoundError('No papers could be researched')

        if len(research_outputs) == 1:
            return research_outputs[0]

        return await self._synthesize_papers(research_outputs, target_audience)

    async def generate_blog_from_research(
        self,
        research_output: PaperResearchOutput,
        target_audience: str = 'practitioner',
    ) -> BlogOutput:
        """Generate a blog post from paper research"""
        logger.info(f'Generating blog for: {research_output.paper_metadata.title}')

        audience_guidelines = get_audience_guidelines(target_audience)
        research_summary = self._format_for_blog(research_output)

        paper_blog_prompt = prompts.paper_blog

        user_prompt = paper_blog_prompt.user_prompt(
            paper_title=research_output.paper_metadata.title,
            paper_authors=', '.join(research_output.paper_metadata.authors[:5]),
            arxiv_id=research_output.paper_metadata.arxiv_id,
            paper_published=research_output.paper_metadata.published,
            research_summary=research_summary,
            target_audience=target_audience,
            audience_guidelines=audience_guidelines,
        )

        system_prompt = paper_blog_prompt.system_prompt(
            paper_title=research_output.paper_metadata.title,
            paper_authors=', '.join(research_output.paper_metadata.authors[:5]),
            arxiv_id=research_output.paper_metadata.arxiv_id,
            paper_published=research_output.paper_metadata.published,
        )

        response = await self.llm.ainvoke(
            prompt=user_prompt,
            system_prompt=system_prompt,
            parse_json=True,
        )

        blog_output = BlogOutput(
            title=response.get('title', research_output.paper_metadata.title),
            content=response.get('content', ''),
            meta_description=response.get('meta_description'),
            tags=response.get('tags', []),
            estimated_reading_time=response.get('estimated_reading_time'),
        )

        blog_output.file_path = await self._save_blog(
            blog_output, research_output.paper_metadata.arxiv_id
        )

        logger.info(f'Generated blog: {blog_output.title}')

        return blog_output

    async def _fetch_paper_metadata(self, arxiv_id: str) -> Dict[str, Any]:
        """Fetch paper metadata from ArXiv"""
        paper = await self.arxiv_client.get_paper(arxiv_id)

        if not paper:
            raise PaperNotFoundError(arxiv_id)

        return paper

    def _validate_paper_content(self, paper_data: Dict[str, Any]) -> None:
        """Validate that paper has sufficient content"""
        abstract = paper_data.get('summary', '')

        if not abstract:
            raise PaperContentInsufficientError(
                'Paper has no abstract',
                arxiv_id=paper_data.get('arxiv_id'),
            )

        word_count = len(abstract.split())
        if word_count < self.MINIMUM_ABSTRACT_WORDS:
            logger.warning(
                f'Paper abstract is short ({word_count} words), proceeding with limited content'
            )

    def _build_research_context(self, paper_data: Dict[str, Any]) -> str:
        """Build research context from paper metadata"""
        context_parts = []

        context_parts.append(f"Title: {paper_data.get('title', 'Unknown')}")

        authors = paper_data.get('authors', [])
        if authors:
            authors_str = ', '.join(authors[:10])
            if len(authors) > 10:
                authors_str += f', and {len(authors) - 10} more'
            context_parts.append(f'Authors: {authors_str}')

        context_parts.append(f"ArXiv ID: {paper_data.get('arxiv_id', 'Unknown')}")
        context_parts.append(f"Published: {paper_data.get('published', 'Unknown')}")

        categories = paper_data.get('categories', [])
        if categories:
            context_parts.append(f"Categories: {', '.join(categories)}")

        abstract = paper_data.get('summary', '')
        if abstract:
            context_parts.append(f'Abstract: {abstract}')

        return '\n'.join(context_parts)

    async def _conduct_paper_research(
        self,
        context: str,
        paper_metadata: PaperMetadata,
        target_audience: str,
    ) -> PaperResearchOutput:
        """Conduct deep research on the paper using LLM"""
        audience_guidelines = get_audience_guidelines(target_audience)

        paper_prompt = prompts.paper

        user_prompt = paper_prompt.user_prompt(
            paper_title=paper_metadata.title,
            paper_authors=', '.join(paper_metadata.authors[:5]),
            arxiv_id=paper_metadata.arxiv_id,
            paper_published=paper_metadata.published,
            paper_categories=', '.join(paper_metadata.categories),
            paper_abstract=paper_metadata.abstract,
            target_audience=target_audience,
            audience_guidelines=audience_guidelines,
        )

        system_prompt = paper_prompt.system_prompt()

        logger.debug('Calling LLM for paper research...')

        response = await self.llm.ainvoke(
            prompt=user_prompt,
            system_prompt=system_prompt,
            parse_json=True,
        )

        return self._parse_research_output(response, paper_metadata)

    def _parse_research_output(
        self,
        llm_response: Dict[str, Any],
        paper_metadata: PaperMetadata,
    ) -> PaperResearchOutput:
        """Parse LLM response into PaperResearchOutput"""
        return PaperResearchOutput(
            paper_metadata=paper_metadata,
            topic_summary=llm_response.get('topic_summary', ''),
            key_concepts=llm_response.get('key_concepts', {}),
            mathematical_foundations=llm_response.get('mathematical_foundations'),
            historical_context=llm_response.get('historical_context'),
            implementation_examples=llm_response.get('implementation_examples'),
            paper_overview=llm_response.get('paper_overview', ''),
            methodology_deep_dive=llm_response.get('methodology_deep_dive', ''),
            experimental_results=llm_response.get('experimental_results'),
            practical_implications=llm_response.get('practical_implications', ''),
            limitations_future_work=llm_response.get('limitations_future_work'),
            related_work_summary=llm_response.get('related_work_summary'),
            sources=[],
        )

    def _calculate_completeness_score(self, output: PaperResearchOutput) -> float:
        """Calculate research completeness score (0-1)"""
        score = 0.0
        max_score = 0.0

        required_checks = [
            (output.paper_overview, 1.5, 100),
            (output.methodology_deep_dive, 1.5, 200),
            (output.practical_implications, 1.0, 50),
            (output.topic_summary, 1.0, 200),
        ]

        for content, weight, min_len in required_checks:
            max_score += weight
            if content and len(content) >= min_len:
                score += weight
            elif content and len(content) >= min_len // 2:
                score += weight * 0.5

        optional_checks = [
            (output.experimental_results, 0.5, 50),
            (output.limitations_future_work, 0.5, 30),
            (output.related_work_summary, 0.5, 30),
            (output.mathematical_foundations, 0.5, 30),
            (output.implementation_examples, 0.5, 50),
            (output.historical_context, 0.5, 30),
        ]

        for content, weight, min_len in optional_checks:
            max_score += weight
            if content and len(content) >= min_len:
                score += weight

        max_score += 1.0
        num_concepts = len(output.key_concepts)
        if num_concepts >= 10:
            score += 1.0
        elif num_concepts >= 5:
            score += 0.5
        elif num_concepts >= 3:
            score += 0.25

        return min(score / max_score, 1.0) if max_score > 0 else 0.0

    def _generate_citation(self, paper_data: Dict[str, Any]) -> str:
        """Generate academic citation for the paper"""
        authors = paper_data.get('authors', [])
        title = paper_data.get('title', 'Unknown Title')
        arxiv_id = paper_data.get('arxiv_id', '')
        published = paper_data.get('published', '')

        if len(authors) > 3:
            author_str = f'{authors[0]} et al.'
        elif len(authors) > 0:
            author_str = ', '.join(authors)
        else:
            author_str = 'Unknown Authors'

        year = published[:4] if published and len(published) >= 4 else 'n.d.'

        citation = f'{author_str}. "{title}". arXiv:{arxiv_id}, {year}.'

        if arxiv_id:
            citation += f' https://arxiv.org/abs/{arxiv_id}'

        return citation

    def _format_for_blog(self, research_output: PaperResearchOutput) -> str:
        """Format research output for blog generation prompt"""
        sections = []

        if research_output.paper_overview:
            sections.append(f'## Paper Overview\n{research_output.paper_overview}')

        if research_output.methodology_deep_dive:
            sections.append(f'## Methodology\n{research_output.methodology_deep_dive}')

        if research_output.experimental_results:
            sections.append(f'## Key Results\n{research_output.experimental_results}')

        if research_output.practical_implications:
            sections.append(
                f'## Practical Implications\n{research_output.practical_implications}'
            )

        if research_output.key_concepts:
            concepts_text = '\n'.join(
                [
                    f'- **{k}**: {v}'
                    for k, v in list(research_output.key_concepts.items())[:10]
                ]
            )
            sections.append(f'## Key Concepts\n{concepts_text}')

        if research_output.topic_summary:
            sections.append(f'## Summary\n{research_output.topic_summary}')

        return '\n\n'.join(sections)

    async def _synthesize_papers(
        self,
        research_outputs: List[PaperResearchOutput],
        target_audience: str,
    ) -> PaperResearchOutput:
        """Synthesize research from multiple papers"""
        base = research_outputs[0]

        combined_summary = '\n\n'.join(
            [
                f'**{r.paper_metadata.title}**\n{r.topic_summary}'
                for r in research_outputs
            ]
        )

        combined_concepts = {}
        for r in research_outputs:
            combined_concepts.update(r.key_concepts)

        combined_sources = []
        for r in research_outputs:
            combined_sources.extend(r.sources)

        return PaperResearchOutput(
            paper_metadata=base.paper_metadata,
            topic_summary=combined_summary,
            key_concepts=combined_concepts,
            paper_overview=f'Analysis of {len(research_outputs)} papers on related topics',
            methodology_deep_dive='\n\n'.join(
                [
                    f'**{r.paper_metadata.title}**\n{r.methodology_deep_dive}'
                    for r in research_outputs
                    if r.methodology_deep_dive
                ]
            ),
            practical_implications='\n\n'.join(
                [r.practical_implications for r in research_outputs if r.practical_implications]
            ),
            sources=combined_sources,
            citation='; '.join([r.citation for r in research_outputs if r.citation]),
        )

    async def _save_research_data(self, research_output: PaperResearchOutput) -> str:
        """Save research data to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_id = research_output.paper_metadata.arxiv_id.replace('/', '_')
            filename = f'{timestamp}_paper_{safe_id}.json'

            research_dir = Path(settings.DATA_DIR) / 'research' / 'paper_summaries'
            research_dir.mkdir(parents=True, exist_ok=True)

            filepath = research_dir / filename
            filepath.write_text(
                json.dumps(research_output.to_dict(), indent=2, default=str)
            )

            logger.debug(f'Saved paper research to {filepath}')
            return str(filepath)

        except Exception as e:
            logger.error(f'Failed to save research data: {e}')
            return ''

    async def _save_blog(self, blog_output: BlogOutput, arxiv_id: str) -> str:
        """Save blog to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_id = arxiv_id.replace('/', '_')
            safe_title = ''.join(
                c if c.isalnum() else '_' for c in blog_output.title[:50]
            )
            filename = f'{timestamp}_{safe_id}_{safe_title}.md'

            blog_dir = Path(settings.DATA_DIR) / 'content' / 'paper_blogs'
            blog_dir.mkdir(parents=True, exist_ok=True)

            filepath = blog_dir / filename

            frontmatter = f'''---
title: "{blog_output.title}"
arxiv_id: {arxiv_id}
tags: {json.dumps(blog_output.tags)}
reading_time: "{blog_output.estimated_reading_time or 'Unknown'}"
created_at: "{datetime.now().isoformat()}"
---

'''

            filepath.write_text(frontmatter + blog_output.content)

            logger.debug(f'Saved blog to {filepath}')
            return str(filepath)

        except Exception as e:
            logger.error(f'Failed to save blog: {e}')
            return ''

    async def close(self):
        """Close resources"""
        if self.arxiv_client:
            await self.arxiv_client.close()


def get_arxiv_paper_research_agent(
    llm: Optional[BedrockLLM] = None,
) -> ArXivPaperResearchAgent:
    """Factory function to create ArXivPaperResearchAgent"""
    return ArXivPaperResearchAgent(llm=llm)


