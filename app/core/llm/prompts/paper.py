"""
Paper research prompts for ArXiv papers
"""
from app.core.llm.prompts.base import BasePrompt


class PaperResearchPrompt(BasePrompt):
    """Prompts for ArXiv paper research and analysis"""

    SYSTEM_TEMPLATE = """You are an expert AI Research Analyst specializing in academic paper analysis.

## Your Task
Analyze the following ArXiv paper and produce a comprehensive research report.

## Required Output Sections

### 1. Paper Overview (200-300 words)
- Main contribution and novelty
- The specific problem being solved
- Key innovation or breakthrough
- Why this paper matters

### 2. Methodology Deep-Dive (400-600 words)
- Detailed explanation of the approach
- Key algorithms, techniques, or methods
- Model architecture, training procedure (for ML papers)
- Step-by-step explanation

### 3. Experimental Results (200-400 words)
- Key findings and performance metrics
- Benchmark comparisons
- Statistical significance

### 4. Practical Implications (200-300 words)
- Real-world applications
- Industry relevance
- How practitioners can apply findings

### 5. Limitations & Future Work (100-200 words)
- Acknowledged limitations
- Suggested future directions

### 6. Related Work Summary (100-200 words)
- Key related papers
- How this differs from prior work

### 7. Key Concepts (10+ concepts)
- Extract and explain key concepts

### 8. Mathematical Foundations (if applicable)
- Key equations and formulations

### 9. Topic Summary (500-800 words)
- Comprehensive standalone summary

### 10. Implementation Examples (if applicable)
- Code snippets or pseudocode

## Output Format
Respond ONLY with valid JSON:
{
  "paper_overview": "...",
  "methodology_deep_dive": "...",
  "experimental_results": "...",
  "practical_implications": "...",
  "limitations_future_work": "...",
  "related_work_summary": "...",
  "key_concepts": {"Concept": "Explanation..."},
  "mathematical_foundations": "...",
  "topic_summary": "...",
  "implementation_examples": "...",
  "historical_context": "..."
}

IMPORTANT: Respond ONLY with the JSON object."""

    USER_TEMPLATE = """## Paper Information
- **Title:** {paper_title}
- **Authors:** {paper_authors}
- **ArXiv ID:** {arxiv_id}
- **Published:** {paper_published}
- **Categories:** {paper_categories}
- **Abstract:** {paper_abstract}

## Target Audience: {target_audience}
{audience_guidelines}"""

    def system_prompt(self, **kwargs) -> str:
        return self.SYSTEM_TEMPLATE

    def user_prompt(
        self,
        paper_title: str,
        paper_authors: str = '',
        arxiv_id: str = '',
        paper_published: str = '',
        paper_categories: str = '',
        paper_abstract: str = '',
        target_audience: str = 'practitioner',
        audience_guidelines: str = '',
        **kwargs,
    ) -> str:
        return self.format(
            self.USER_TEMPLATE,
            paper_title=paper_title,
            paper_authors=paper_authors,
            arxiv_id=arxiv_id,
            paper_published=paper_published,
            paper_categories=paper_categories,
            paper_abstract=paper_abstract,
            target_audience=target_audience,
            audience_guidelines=audience_guidelines,
        )


class PaperBlogPrompt(BasePrompt):
    """Prompts for generating blog posts from ArXiv paper research"""

    SYSTEM_TEMPLATE = """You are an expert technical writer creating a blog post about an academic research paper.

## Blog Structure Requirements

1. **Hook** - Engaging opening (1-2 paragraphs)
2. **Paper Introduction** - Context and citation (2-3 paragraphs)
3. **The Problem** - What problem is addressed (2-3 paragraphs)
4. **The Solution** - Key methodology explained accessibly (3-5 paragraphs)
5. **Key Findings** - Main results (2-3 paragraphs)
6. **Why It Matters** - Practical implications (2-3 paragraphs)
7. **Looking Forward** - Future directions (1-2 paragraphs)
8. **Conclusion** - Key takeaways and CTA (1-2 paragraphs)

## Output Format
Respond ONLY with valid JSON:
{
  "title": "Engaging blog title",
  "content": "Full markdown-formatted blog content...",
  "meta_description": "SEO-friendly description (150-160 characters)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "estimated_reading_time": "X min read"
}

IMPORTANT: Return ONLY the JSON object."""

    USER_TEMPLATE = """## Paper Information
- **Title:** {paper_title}
- **Authors:** {paper_authors}
- **ArXiv ID:** {arxiv_id}
- **Published:** {paper_published}

## Research Summary
{research_summary}

## Target Audience: {target_audience}
{audience_guidelines}"""

    def system_prompt(
        self,
        paper_title: str = '',
        paper_authors: str = '',
        arxiv_id: str = '',
        paper_published: str = '',
        **kwargs,
    ) -> str:
        return self.SYSTEM_TEMPLATE

    def user_prompt(
        self,
        paper_title: str,
        paper_authors: str = '',
        arxiv_id: str = '',
        paper_published: str = '',
        research_summary: str = '',
        target_audience: str = 'practitioner',
        audience_guidelines: str = '',
        **kwargs,
    ) -> str:
        return self.format(
            self.USER_TEMPLATE,
            paper_title=paper_title,
            paper_authors=paper_authors,
            arxiv_id=arxiv_id,
            paper_published=paper_published,
            research_summary=research_summary,
            target_audience=target_audience,
            audience_guidelines=audience_guidelines,
        )


