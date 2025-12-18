"""
ArXiv Paper Research Agent
Deep research agent specialized for ArXiv paper analysis
Generates enhanced research with paper-specific sections and blog generation
Maps to: spec.md → Stories 1-8, FR1-FR10 | plan.md → T007, T009, T011, T012
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from src.lib.llm.model import BedrockLLM
from src.lib.llm.prompts import prompts
from src.lib.llm.prompt_loader import get_audience_guidelines
from src.lib.services.arxiv_client import ArXivClient
from src.lib.services.arxiv_id_parser import (
    parse_arxiv_id,
    validate_arxiv_id,
    normalize_arxiv_id,
    get_base_id,
)
from src.lib.models.exceptions import (
    PaperNotFoundError,
    PaperContentInsufficientError,
    MultiplePapersLimitError,
    InvalidArXivIdError,
)
from src.common.config import config
from src.common.logger import setup_logger

logger = setup_logger(__name__)


# ============= Data Classes =============

@dataclass
class PaperMetadata:
    """Metadata for an ArXiv paper"""
    arxiv_id: str
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    published: str = ""
    updated: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    pdf_url: Optional[str] = None
    abs_url: Optional[str] = None
    
    @classmethod
    def from_arxiv_response(cls, data: Dict[str, Any]) -> "PaperMetadata":
        """Create PaperMetadata from ArXiv API response"""
        return cls(
            arxiv_id=data.get("arxiv_id", ""),
            title=data.get("title", ""),
            authors=data.get("authors", []),
            abstract=data.get("summary", ""),
            published=data.get("published", ""),
            updated=data.get("updated"),
            categories=data.get("categories", []),
            pdf_url=data.get("pdf_url"),
            abs_url=data.get("abs_url"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "published": self.published,
            "updated": self.updated,
            "categories": self.categories,
            "pdf_url": self.pdf_url,
            "abs_url": self.abs_url,
        }


@dataclass
class PaperResearchOutput:
    """Enhanced research output for ArXiv paper analysis"""
    # Paper metadata
    paper_metadata: PaperMetadata
    
    # Standard research sections
    topic_summary: str = ""
    key_concepts: Dict[str, str] = field(default_factory=dict)
    mathematical_foundations: Optional[str] = None
    historical_context: Optional[str] = None
    implementation_examples: Optional[str] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
    
    # Enhanced paper-specific sections
    paper_overview: str = ""
    methodology_deep_dive: str = ""
    experimental_results: Optional[str] = None
    practical_implications: str = ""
    limitations_future_work: Optional[str] = None
    related_work_summary: Optional[str] = None
    citation: str = ""
    
    # Metadata
    completeness_score: float = 0.0
    research_data_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "paper_metadata": self.paper_metadata.to_dict(),
            "topic_summary": self.topic_summary,
            "key_concepts": self.key_concepts,
            "mathematical_foundations": self.mathematical_foundations,
            "historical_context": self.historical_context,
            "implementation_examples": self.implementation_examples,
            "sources": self.sources,
            "paper_overview": self.paper_overview,
            "methodology_deep_dive": self.methodology_deep_dive,
            "experimental_results": self.experimental_results,
            "practical_implications": self.practical_implications,
            "limitations_future_work": self.limitations_future_work,
            "related_work_summary": self.related_work_summary,
            "citation": self.citation,
            "completeness_score": self.completeness_score,
            "research_data_path": self.research_data_path,
            "created_at": self.created_at.isoformat(),
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


# ============= ArXiv Paper Research Agent =============

class ArXivPaperResearchAgent:
    """
    Agent for deep research analysis of ArXiv papers
    Generates comprehensive research with enhanced paper-specific sections
    """
    
    MINIMUM_ABSTRACT_WORDS = 50  # Reduced from 100 for more flexibility
    MAX_PAPERS_PER_REQUEST = 5
    
    def __init__(
        self,
        llm: Optional[BedrockLLM] = None,
        arxiv_client: Optional[ArXivClient] = None,
    ):
        """
        Initialize the paper research agent
        
        Args:
            llm: LLM instance for research generation
            arxiv_client: ArXiv client for paper retrieval
        """
        self.llm = llm or BedrockLLM()
        self.arxiv_client = arxiv_client or ArXivClient()
        logger.info("Initialized ArXivPaperResearchAgent")
    
    async def research_paper_by_id(
        self,
        arxiv_id: str,
        target_audience: str = "practitioner",
    ) -> PaperResearchOutput:
        """
        Research a paper by its ArXiv ID
        
        Args:
            arxiv_id: ArXiv paper ID (supports various formats)
            target_audience: Target audience (beginner, practitioner, expert)
            
        Returns:
            PaperResearchOutput with comprehensive research
            
        Raises:
            InvalidArXivIdError: If arxiv_id format is invalid
            PaperNotFoundError: If paper not found on ArXiv
            PaperContentInsufficientError: If paper content is too short
        """
        logger.info(f"Starting paper research for: {arxiv_id}")
        
        # Parse and validate ArXiv ID
        if not validate_arxiv_id(arxiv_id):
            raise InvalidArXivIdError(arxiv_id)
        
        normalized_id = normalize_arxiv_id(arxiv_id)
        # Use base ID (without version) for ArXiv API - it handles versions internally
        base_id = get_base_id(arxiv_id)
        
        # Fetch paper metadata using base ID
        paper_data = await self._fetch_paper_metadata(base_id)
        
        # Validate paper content
        self._validate_paper_content(paper_data)
        
        # Create paper metadata object
        paper_metadata = PaperMetadata.from_arxiv_response(paper_data)
        
        # Build research context
        context = self._build_research_context(paper_data)
        
        # Conduct research using LLM
        research_output = await self._conduct_paper_research(
            context=context,
            paper_metadata=paper_metadata,
            target_audience=target_audience,
        )
        
        # Calculate completeness score
        research_output.completeness_score = self._calculate_completeness_score(research_output)
        
        # Generate citation
        research_output.citation = self._generate_citation(paper_data)
        
        # Add paper as source
        research_output.sources.append({
            "type": "paper",
            "title": paper_metadata.title,
            "url": paper_metadata.abs_url or f"https://arxiv.org/abs/{normalized_id}",
            "authors": paper_metadata.authors,
            "arxiv_id": normalized_id,
        })
        
        # Save research data
        research_output.research_data_path = await self._save_research_data(research_output)
        
        logger.info(f"Paper research completed with score: {research_output.completeness_score:.2f}")
        
        return research_output
    
    async def research_paper_by_title(
        self,
        title: str,
        target_audience: str = "practitioner",
    ) -> PaperResearchOutput:
        """
        Search for a paper by title and research it
        
        Args:
            title: Paper title to search for
            target_audience: Target audience level
            
        Returns:
            PaperResearchOutput for the found paper
            
        Raises:
            PaperNotFoundError: If no matching paper found
        """
        logger.info(f"Searching for paper: {title}")
        
        # Search ArXiv
        results = await self.arxiv_client.search(title, max_results=1)
        
        if not results:
            raise PaperNotFoundError(f"No paper found matching: {title}")
        
        # Get the first result's ArXiv ID
        paper_data = results[0]
        arxiv_id = paper_data.get("arxiv_id", "")
        
        if not arxiv_id:
            raise PaperNotFoundError(f"No valid ArXiv ID in search results for: {title}")
        
        logger.info(f"Found paper: {arxiv_id} - {paper_data.get('title', '')}")
        
        # Research the found paper
        return await self.research_paper_by_id(arxiv_id, target_audience)
    
    async def research_multiple_papers(
        self,
        arxiv_ids: List[str],
        target_audience: str = "practitioner",
    ) -> PaperResearchOutput:
        """
        Research multiple papers and synthesize findings
        
        Args:
            arxiv_ids: List of ArXiv paper IDs
            target_audience: Target audience level
            
        Returns:
            Synthesized PaperResearchOutput
            
        Raises:
            MultiplePapersLimitError: If more than 5 papers requested
        """
        if len(arxiv_ids) > self.MAX_PAPERS_PER_REQUEST:
            raise MultiplePapersLimitError(len(arxiv_ids), self.MAX_PAPERS_PER_REQUEST)
        
        logger.info(f"Researching {len(arxiv_ids)} papers")
        
        # Research each paper
        research_outputs = []
        for arxiv_id in arxiv_ids:
            try:
                output = await self.research_paper_by_id(arxiv_id, target_audience)
                research_outputs.append(output)
            except Exception as e:
                logger.warning(f"Failed to research paper {arxiv_id}: {e}")
        
        if not research_outputs:
            raise PaperNotFoundError("No papers could be researched")
        
        # If only one paper, return it directly
        if len(research_outputs) == 1:
            return research_outputs[0]
        
        # Synthesize multiple papers
        return await self._synthesize_papers(research_outputs, target_audience)
    
    async def generate_blog_from_research(
        self,
        research_output: PaperResearchOutput,
        target_audience: str = "practitioner",
    ) -> BlogOutput:
        """
        Generate a blog post from paper research
        
        Args:
            research_output: Completed paper research
            target_audience: Target audience for the blog
            
        Returns:
            BlogOutput with generated blog content
        """
        logger.info(f"Generating blog for: {research_output.paper_metadata.title}")
        
        # Get audience guidelines
        audience_guidelines = get_audience_guidelines(target_audience)
        
        # Build research summary for blog prompt
        research_summary = self._format_for_blog(research_output)
        
        # Get paper blog prompt
        paper_blog_prompt = prompts.paper_blog
        
        # Build user prompt
        user_prompt = paper_blog_prompt.user_prompt(
            paper_title=research_output.paper_metadata.title,
            paper_authors=", ".join(research_output.paper_metadata.authors[:5]),
            arxiv_id=research_output.paper_metadata.arxiv_id,
            paper_published=research_output.paper_metadata.published,
            research_summary=research_summary,
            target_audience=target_audience,
            audience_guidelines=audience_guidelines,
        )
        
        # Get system prompt with paper details
        system_prompt = paper_blog_prompt.system_prompt(
            paper_title=research_output.paper_metadata.title,
            paper_authors=", ".join(research_output.paper_metadata.authors[:5]),
            arxiv_id=research_output.paper_metadata.arxiv_id,
            paper_published=research_output.paper_metadata.published,
        )
        
        # Generate blog content
        response = await self.llm.ainvoke(
            prompt=user_prompt,
            system_prompt=system_prompt,
            parse_json=True,
        )
        
        # Create blog output
        blog_output = BlogOutput(
            title=response.get("title", research_output.paper_metadata.title),
            content=response.get("content", ""),
            meta_description=response.get("meta_description"),
            tags=response.get("tags", []),
            estimated_reading_time=response.get("estimated_reading_time"),
        )
        
        # Save blog to file
        blog_output.file_path = await self._save_blog(blog_output, research_output.paper_metadata.arxiv_id)
        
        logger.info(f"Generated blog: {blog_output.title}")
        
        return blog_output
    
    async def _fetch_paper_metadata(self, arxiv_id: str) -> Dict[str, Any]:
        """Fetch paper metadata from ArXiv"""
        paper = await self.arxiv_client.get_paper(arxiv_id)
        
        if not paper:
            raise PaperNotFoundError(arxiv_id)
        
        return paper
    
    def _validate_paper_content(self, paper_data: Dict[str, Any]) -> None:
        """Validate that paper has sufficient content for research"""
        abstract = paper_data.get("summary", "")
        
        if not abstract:
            raise PaperContentInsufficientError(
                "Paper has no abstract",
                arxiv_id=paper_data.get("arxiv_id"),
            )
        
        word_count = len(abstract.split())
        if word_count < self.MINIMUM_ABSTRACT_WORDS:
            logger.warning(f"Paper abstract is short ({word_count} words), proceeding with limited content")
    
    def _build_research_context(self, paper_data: Dict[str, Any]) -> str:
        """Build research context from paper metadata"""
        context_parts = []
        
        context_parts.append(f"Title: {paper_data.get('title', 'Unknown')}")
        
        authors = paper_data.get("authors", [])
        if authors:
            authors_str = ", ".join(authors[:10])  # Limit to first 10 authors
            if len(authors) > 10:
                authors_str += f", and {len(authors) - 10} more"
            context_parts.append(f"Authors: {authors_str}")
        
        context_parts.append(f"ArXiv ID: {paper_data.get('arxiv_id', 'Unknown')}")
        context_parts.append(f"Published: {paper_data.get('published', 'Unknown')}")
        
        categories = paper_data.get("categories", [])
        if categories:
            context_parts.append(f"Categories: {', '.join(categories)}")
        
        abstract = paper_data.get("summary", "")
        if abstract:
            context_parts.append(f"Abstract: {abstract}")
        
        return "\n".join(context_parts)
    
    async def _conduct_paper_research(
        self,
        context: str,
        paper_metadata: PaperMetadata,
        target_audience: str,
    ) -> PaperResearchOutput:
        """Conduct deep research on the paper using LLM"""
        # Get audience guidelines
        audience_guidelines = get_audience_guidelines(target_audience)
        
        # Get paper research prompt
        paper_prompt = prompts.paper
        
        # Build user prompt
        user_prompt = paper_prompt.user_prompt(
            paper_title=paper_metadata.title,
            paper_authors=", ".join(paper_metadata.authors[:5]),
            arxiv_id=paper_metadata.arxiv_id,
            paper_published=paper_metadata.published,
            paper_categories=", ".join(paper_metadata.categories),
            paper_abstract=paper_metadata.abstract,
            target_audience=target_audience,
            audience_guidelines=audience_guidelines,
        )
        
        # Get system prompt
        system_prompt = paper_prompt.system_prompt()
        
        logger.debug("Calling LLM for paper research...")
        
        # Call LLM
        response = await self.llm.ainvoke(
            prompt=user_prompt,
            system_prompt=system_prompt,
            parse_json=True,
        )
        
        # Parse response into output
        return self._parse_research_output(response, paper_metadata)
    
    def _parse_research_output(
        self,
        llm_response: Dict[str, Any],
        paper_metadata: PaperMetadata,
    ) -> PaperResearchOutput:
        """Parse LLM response into PaperResearchOutput"""
        return PaperResearchOutput(
            paper_metadata=paper_metadata,
            topic_summary=llm_response.get("topic_summary", ""),
            key_concepts=llm_response.get("key_concepts", {}),
            mathematical_foundations=llm_response.get("mathematical_foundations"),
            historical_context=llm_response.get("historical_context"),
            implementation_examples=llm_response.get("implementation_examples"),
            paper_overview=llm_response.get("paper_overview", ""),
            methodology_deep_dive=llm_response.get("methodology_deep_dive", ""),
            experimental_results=llm_response.get("experimental_results"),
            practical_implications=llm_response.get("practical_implications", ""),
            limitations_future_work=llm_response.get("limitations_future_work"),
            related_work_summary=llm_response.get("related_work_summary"),
            sources=[],
        )
    
    def _calculate_completeness_score(self, output: PaperResearchOutput) -> float:
        """Calculate research completeness score (0-1)"""
        score = 0.0
        max_score = 0.0
        
        # Required sections (weighted higher)
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
        
        # Optional sections
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
        
        # Key concepts (check for 10+ concepts)
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
        authors = paper_data.get("authors", [])
        title = paper_data.get("title", "Unknown Title")
        arxiv_id = paper_data.get("arxiv_id", "")
        published = paper_data.get("published", "")
        
        # Format authors
        if len(authors) > 3:
            author_str = f"{authors[0]} et al."
        elif len(authors) > 0:
            author_str = ", ".join(authors)
        else:
            author_str = "Unknown Authors"
        
        # Extract year from published date
        year = published[:4] if published and len(published) >= 4 else "n.d."
        
        # Format citation
        citation = f'{author_str}. "{title}". arXiv:{arxiv_id}, {year}.'
        
        if arxiv_id:
            citation += f" https://arxiv.org/abs/{arxiv_id}"
        
        return citation
    
    def _format_for_blog(self, research_output: PaperResearchOutput) -> str:
        """Format research output for blog generation prompt"""
        sections = []
        
        if research_output.paper_overview:
            sections.append(f"## Paper Overview\n{research_output.paper_overview}")
        
        if research_output.methodology_deep_dive:
            sections.append(f"## Methodology\n{research_output.methodology_deep_dive}")
        
        if research_output.experimental_results:
            sections.append(f"## Key Results\n{research_output.experimental_results}")
        
        if research_output.practical_implications:
            sections.append(f"## Practical Implications\n{research_output.practical_implications}")
        
        if research_output.key_concepts:
            concepts_text = "\n".join([
                f"- **{k}**: {v}"
                for k, v in list(research_output.key_concepts.items())[:10]
            ])
            sections.append(f"## Key Concepts\n{concepts_text}")
        
        if research_output.topic_summary:
            sections.append(f"## Summary\n{research_output.topic_summary}")
        
        return "\n\n".join(sections)
    
    async def _synthesize_papers(
        self,
        research_outputs: List[PaperResearchOutput],
        target_audience: str,
    ) -> PaperResearchOutput:
        """Synthesize research from multiple papers"""
        # Use the first paper as the base
        base = research_outputs[0]
        
        # Combine summaries
        combined_summary = "\n\n".join([
            f"**{r.paper_metadata.title}**\n{r.topic_summary}"
            for r in research_outputs
        ])
        
        # Combine key concepts
        combined_concepts = {}
        for r in research_outputs:
            combined_concepts.update(r.key_concepts)
        
        # Combine sources
        combined_sources = []
        for r in research_outputs:
            combined_sources.extend(r.sources)
        
        # Create synthesized output
        return PaperResearchOutput(
            paper_metadata=base.paper_metadata,  # Use first paper as primary
            topic_summary=combined_summary,
            key_concepts=combined_concepts,
            paper_overview=f"Analysis of {len(research_outputs)} papers on related topics",
            methodology_deep_dive="\n\n".join([
                f"**{r.paper_metadata.title}**\n{r.methodology_deep_dive}"
                for r in research_outputs if r.methodology_deep_dive
            ]),
            practical_implications="\n\n".join([
                r.practical_implications
                for r in research_outputs if r.practical_implications
            ]),
            sources=combined_sources,
            citation="; ".join([r.citation for r in research_outputs if r.citation]),
        )
    
    async def _save_research_data(self, research_output: PaperResearchOutput) -> str:
        """Save research data to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_id = research_output.paper_metadata.arxiv_id.replace("/", "_")
            filename = f"{timestamp}_paper_{safe_id}.json"
            
            research_dir = config.RESEARCH_DIR / "paper_summaries"
            research_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = research_dir / filename
            filepath.write_text(json.dumps(research_output.to_dict(), indent=2, default=str))
            
            logger.debug(f"Saved paper research to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save research data: {e}")
            return ""
    
    async def _save_blog(self, blog_output: BlogOutput, arxiv_id: str) -> str:
        """Save blog to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_id = arxiv_id.replace("/", "_")
            safe_title = "".join(c if c.isalnum() else "_" for c in blog_output.title[:50])
            filename = f"{timestamp}_{safe_id}_{safe_title}.md"
            
            blog_dir = config.CONTENT_DIR / "paper_blogs"
            blog_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = blog_dir / filename
            
            # Add frontmatter
            frontmatter = f"""---
title: "{blog_output.title}"
arxiv_id: {arxiv_id}
tags: {json.dumps(blog_output.tags)}
reading_time: "{blog_output.estimated_reading_time or 'Unknown'}"
created_at: "{datetime.now().isoformat()}"
---

"""
            
            filepath.write_text(frontmatter + blog_output.content)
            
            logger.debug(f"Saved blog to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save blog: {e}")
            return ""
    
    async def close(self):
        """Close resources"""
        if self.arxiv_client:
            await self.arxiv_client.close()


def get_arxiv_paper_research_agent(
    llm: Optional[BedrockLLM] = None,
) -> ArXivPaperResearchAgent:
    """Factory function to create ArXivPaperResearchAgent"""
    return ArXivPaperResearchAgent(llm=llm)
