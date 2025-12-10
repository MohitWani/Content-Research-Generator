# Implementation Plan: ArXiv Paper Research & Blog Generation API

## 1. Executive Summary

**Feature:** ArXiv Paper Research & Blog Generation API - A comprehensive REST API and CLI that accepts ArXiv paper identifiers (ID or title search) and generates enhanced, in-depth research analysis along with publication-ready blog posts. The system extends the existing research agent to provide deeper paper-specific analysis including methodology breakdown, experimental results, and practical implications.

**Approach:** 
- Extend existing `ReActResearchAgent` with paper-specific prompts and enhanced output structure
- Create new `ArXivPaperResearchAgent` that orchestrates paper retrieval + deep research + blog generation
- Use existing `ArXivClient` for paper metadata retrieval
- Use existing `BlogWriterAgent` with paper-specific prompts
- Add new API routes under `/api/v1/paper/` and CLI commands under `ai-research paper`
- Extend database models to support paper research metadata

**Complexity:** Medium-High (extends existing infrastructure with new agent logic and specialized prompts)

**Estimated Effort:** 8-10 development days

## 2. SDD Constitutional Gates (Pre-Implementation Checklist)

### ✓ Library-First Principle (Article I)
- [ ] New agent written in `src/lib/agents/arxiv_paper_research_agent.py`
- [ ] Agent can be imported and used without API layer: `from src.lib.agents import ArXivPaperResearchAgent`
- [ ] Clear separation: agent logic in `src/lib/agents/`, API in `src/api/routes/paper.py`, CLI in `src/cli/commands/paper.py`
- [ ] Paper-specific prompts in `src/lib/llm/prompts/paper_research.txt`

### ✓ CLI Interface Mandate (Article II)
- [ ] All paper research functionality accessible via Typer CLI
- [ ] Format: `python -m cli paper research --arxiv-id 2508.07407`
- [ ] Format: `python -m cli paper search --title "attention mechanism"`
- [ ] Format: `python -m cli paper full --arxiv-id 2508.07407 --audience practitioner`

### ✓ Test-First Command (Article III)
- [ ] Tests written BEFORE implementation
- [ ] Unit tests for ArXiv ID validation, paper metadata parsing
- [ ] Integration tests for paper research workflow with real LLM
- [ ] E2E tests for API endpoints

### ✓ Simplicity Mandate (Article VII)
- [ ] Maximum 3 project components (lib, api, cli) - maintained
- [ ] No new external services - uses existing ArXiv, Bedrock
- [ ] Extends existing patterns rather than creating new abstractions

### ✓ Anti-Abstraction Principle (Article VIII)
- [ ] Using FastAPI, SQLAlchemy, LangGraph DIRECTLY
- [ ] Extends existing `ReActResearchAgent` pattern, not wrapping it
- [ ] Uses existing database models with optional extension

### ✓ Integration-First Testing (Article IX)
- [ ] Tests use real PostgreSQL (test database)
- [ ] Tests use real ArXiv API (with rate limiting in tests)
- [ ] Integration tests use real AWS Bedrock (rate-limited)

### ⚠️ CRITICAL: Async Pattern for FastAPI + LangGraph
- [ ] **FastAPI endpoints are async** (`async def`)
- [ ] **LangGraph agent workflows are async** (`async def` node functions)
- [ ] **Background tasks use FastAPI BackgroundTasks** (not Celery for this feature)
- [ ] **Pattern:** `async def api_endpoint(...): return await agent.conduct_research(...)`
- [ ] **CLI Pattern:** `def cli_command(...): asyncio.run(async_workflow(...))`

## 3. Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      User Interface Layer                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   FastAPI        │  │     CLI          │  │  Streamlit   │  │
│  │ /api/v1/paper/*  │  │  paper research  │  │   (future)   │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────────┘  │
└───────────┼─────────────────────┼────────────────────────────────┘
            │                     │
            └──────────┬──────────┘
                       │
         ┌─────────────▼─────────────┐
         │  ArXivPaperResearchAgent  │
         │   (src/lib/agents/)       │
         │  ┌─────────────────────┐  │
         │  │ 1. Parse ArXiv ID   │  │
         │  │ 2. Fetch Paper      │  │
         │  │ 3. Deep Research    │  │
         │  │ 4. Generate Blog    │  │
         │  └─────────────────────┘  │
         └─────────────┬─────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
┌───▼───────┐   ┌──────▼──────┐    ┌──────▼──────┐
│ ArXivClient│   │ReActResearch│    │BlogWriter  │
│ (existing) │   │   Agent     │    │   Agent    │
└───┬───────┘   │ (extended)  │    │ (existing) │
    │           └──────┬──────┘    └──────┬──────┘
    │                  │                  │
┌───▼──────────────────▼──────────────────▼───┐
│              AWS Bedrock (Claude)            │
│              LangChain Tools                 │
└──────────────────────────────────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │     PostgreSQL Database    │
         │  (ResearchQuery, Results)  │
         └────────────────────────────┘
```

**Flow:**

1. **Request Flow:** 
   - User submits ArXiv ID/title → API/CLI validates input
   - ArXivPaperResearchAgent orchestrates workflow

2. **Paper Retrieval Flow:**
   - Parse and normalize ArXiv ID
   - Fetch paper metadata via ArXivClient
   - Validate paper exists and has sufficient content

3. **Research Flow:**
   - Build paper-specific context from metadata
   - Execute enhanced ReAct research with paper prompts
   - Generate structured output with all enhanced sections

4. **Blog Generation Flow:**
   - Pass research output to BlogWriterAgent
   - Use paper-specific blog prompts
   - Include proper paper citation

5. **Storage Flow:**
   - Save research output to database + file system
   - Save blog to content directory
   - Link paper metadata for traceability

## 4. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Paper Research Agent | New `ArXivPaperResearchAgent` | Orchestrates paper-specific workflow, extends existing patterns |
| Paper Retrieval | Existing `ArXivClient` | Already implemented with rate limiting and parsing |
| Research Foundation | Existing `ReActResearchAgent` | Proven ReAct pattern, extend with paper prompts |
| Blog Generation | Existing `BlogWriterAgent` | Already supports audience customization |
| LLM Provider | AWS Bedrock (Claude) | Existing integration, spec requirement |
| API Framework | FastAPI | Existing pattern, async support |
| CLI Framework | Typer | Article II mandate, existing pattern |
| Database | PostgreSQL + existing models | Extend existing schema minimally |

## 5. Directory Structure (Library-First)

```
project_root/
├── src/
│   ├── lib/
│   │   ├── agents/
│   │   │   ├── __init__.py                    # Add ArXivPaperResearchAgent export
│   │   │   ├── arxiv_paper_research_agent.py  # NEW: Main paper research agent
│   │   │   ├── react_research_agent.py        # Existing (minor extension)
│   │   │   └── blog_writer_agent.py           # Existing (use as-is)
│   │   ├── services/
│   │   │   ├── arxiv_client.py                # Existing (use as-is)
│   │   │   └── arxiv_id_parser.py             # NEW: ArXiv ID parsing/validation
│   │   ├── llm/
│   │   │   └── prompts/
│   │   │       ├── paper_research.txt         # NEW: Paper-specific research prompt
│   │   │       └── paper_blog.txt             # NEW: Paper-specific blog prompt
│   │   ├── models/
│   │   │   ├── research.py                    # Extend: Add PaperResearch model
│   │   │   ├── schemas.py                     # Extend: Add paper schemas
│   │   │   └── paper.py                       # NEW: Paper-specific models
│   │   └── pipelines/
│   │       └── paper_research_pipeline.py     # NEW: Paper research pipeline
│   ├── api/
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── paper.py                       # NEW: Paper research API routes
│   └── cli/
│       └── commands/
│           └── paper.py                       # NEW: Paper research CLI commands
├── tests/
│   ├── unit/
│   │   ├── test_arxiv_id_parser.py            # NEW
│   │   └── test_arxiv_paper_research_agent.py # NEW
│   ├── integration/
│   │   └── test_paper_research_workflow.py    # NEW
│   └── e2e/
│       └── test_paper_api.py                  # NEW
├── specs/
│   └── arxiv-paper-research-api/
│       ├── spec.md                            # Created
│       ├── plan.md                            # This file
│       └── tasks.md                           # To be created
└── alembic/
    └── versions/
        └── xxx_add_paper_research_fields.py   # NEW: Optional migration
```

## 6. Data Models

### 6.1 New Pydantic Schemas (API Contract)

```python
# src/lib/models/schemas.py (extend existing file)

class ArXivPaperInput(BaseModel):
    """Input for paper research - accepts ID or title"""
    arxiv_id: Optional[str] = Field(
        None, 
        description="ArXiv paper ID (e.g., '2508.07407' or 'arxiv:2508.07407v2')",
        examples=["2508.07407", "arxiv:2508.07407v2"]
    )
    title_search: Optional[str] = Field(
        None,
        description="Paper title for search (if arxiv_id not provided)",
        examples=["Attention Is All You Need"]
    )
    
    @field_validator("arxiv_id", "title_search")
    @classmethod
    def validate_at_least_one(cls, v, info):
        # Validation: at least one of arxiv_id or title_search required
        pass


class PaperResearchRequest(BaseModel):
    """Request schema for paper research"""
    paper: ArXivPaperInput
    target_audience: Optional[TargetAudienceEnum] = TargetAudienceEnum.PRACTITIONER
    generate_blog: Optional[bool] = Field(
        default=True,
        description="Whether to generate blog after research"
    )


class PaperMetadata(BaseModel):
    """Paper metadata from ArXiv"""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    published: str
    updated: Optional[str] = None
    categories: List[str] = []
    pdf_url: Optional[str] = None
    abs_url: Optional[str] = None


class EnhancedResearchResult(BaseModel):
    """Enhanced research result with paper-specific sections"""
    # Standard research fields (from existing)
    topic_summary: str
    key_concepts: Dict[str, str]
    mathematical_foundations: Optional[str] = None
    historical_context: Optional[str] = None
    implementation_examples: Optional[str] = None
    sources: List[SourceSchema] = []
    
    # NEW: Paper-specific enhanced sections
    paper_overview: str = Field(..., description="Structured summary of paper contribution")
    methodology_deep_dive: str = Field(..., description="Detailed methodology explanation")
    experimental_results: Optional[str] = Field(None, description="Key findings and metrics")
    practical_implications: str = Field(..., description="Real-world applications")
    limitations_future_work: Optional[str] = Field(None, description="Acknowledged limitations")
    related_work_summary: Optional[str] = Field(None, description="Related papers overview")
    citation: str = Field(..., description="Proper academic citation")
    
    # Metadata
    paper_metadata: PaperMetadata
    completeness_score: float
    research_data_path: Optional[str] = None


class PaperResearchResponse(BaseModel):
    """Response for paper research request"""
    research_id: int
    paper_metadata: PaperMetadata
    status: StatusEnum
    created_at: datetime


class PaperFullResponse(BaseModel):
    """Full response with research and blog"""
    research_id: int
    paper_metadata: PaperMetadata
    research: EnhancedResearchResult
    blog: Optional[BlogGenerationResponse] = None
    status: StatusEnum
```

### 6.2 Database Model Extension (Optional)

```python
# src/lib/models/paper.py (NEW)
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

class PaperResearch(Base):
    """Extended research result for paper-specific content"""
    __tablename__ = "paper_research"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    research_result_id: Mapped[int] = mapped_column(
        ForeignKey("research_results.id"),
        nullable=False
    )
    
    # Paper metadata
    arxiv_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    paper_title: Mapped[str] = mapped_column(Text, nullable=False)
    paper_authors: Mapped[list] = mapped_column(JSON, nullable=True)
    paper_abstract: Mapped[str] = mapped_column(Text, nullable=True)
    paper_published: Mapped[str] = mapped_column(String(50), nullable=True)
    paper_categories: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Enhanced sections
    paper_overview: Mapped[str] = mapped_column(Text, nullable=True)
    methodology_deep_dive: Mapped[str] = mapped_column(Text, nullable=True)
    experimental_results: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    practical_implications: Mapped[str] = mapped_column(Text, nullable=True)
    limitations_future_work: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    related_work_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relationships
    research_result: Mapped["ResearchResult"] = relationship()
```

**Note:** The database extension is optional for V1. We can store enhanced sections in the existing `ResearchResult.key_concepts` JSON field initially and migrate to dedicated columns later if needed.

## 7. API Design

**OpenAPI Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- New endpoints under `/api/v1/paper/` tag

**Endpoints:**

| Method | Endpoint | Description | Status | Request | Response |
|--------|----------|-------------|--------|---------|----------|
| POST | `/api/v1/paper/research` | Start paper research (async) | 202 | `PaperResearchRequest` | `PaperResearchResponse` |
| POST | `/api/v1/paper/research/sync` | Paper research (sync) | 200 | `PaperResearchRequest` | `EnhancedResearchResult` |
| GET | `/api/v1/paper/research/{id}` | Get research status | 200/404 | Path: id | `PaperResearchResponse` |
| GET | `/api/v1/paper/research/{id}/result` | Get research result | 200/404 | Path: id | `EnhancedResearchResult` |
| POST | `/api/v1/paper/blog` | Generate blog from paper research | 200 | `PaperBlogRequest` | `BlogGenerationResponse` |
| POST | `/api/v1/paper/full` | Research + Blog (async) | 202 | `PaperResearchRequest` | `PaperResearchResponse` |
| POST | `/api/v1/paper/full/sync` | Research + Blog (sync) | 200 | `PaperResearchRequest` | `PaperFullResponse` |
| POST | `/api/v1/paper/search` | Search papers by title | 200 | `PaperSearchRequest` | `List[PaperMetadata]` |
| GET | `/api/v1/paper/metadata/{arxiv_id}` | Get paper metadata only | 200/404 | Path: arxiv_id | `PaperMetadata` |

**Error Responses:**
- 400: Invalid ArXiv ID format / validation error
- 404: Paper not found on ArXiv
- 422: Pydantic validation failure
- 429: Rate limit exceeded (ArXiv or LLM)
- 500: Internal server error
- 503: ArXiv API unavailable

**Example Request/Response:**

```bash
# Request
POST /api/v1/paper/full/sync
{
  "paper": {
    "arxiv_id": "2508.07407"
  },
  "target_audience": "practitioner",
  "generate_blog": true
}

# Response (200 OK)
{
  "research_id": 42,
  "paper_metadata": {
    "arxiv_id": "2508.07407",
    "title": "A Comprehensive Survey of Self-Evolving AI Agents",
    "authors": ["Jinyuan Fang", "..."],
    "abstract": "...",
    "published": "2025-08-31",
    "categories": ["cs.AI", "cs.LG"],
    "pdf_url": "https://arxiv.org/pdf/2508.07407"
  },
  "research": {
    "paper_overview": "...",
    "methodology_deep_dive": "...",
    "experimental_results": "...",
    "practical_implications": "...",
    "key_concepts": {...},
    "sources": [...],
    "completeness_score": 0.92
  },
  "blog": {
    "content_id": 123,
    "title": "Self-Evolving AI Agents: A Deep Dive",
    "file_path": "/data/content/blogs/...",
    "status": "completed"
  },
  "status": "completed"
}
```

## 8. CLI Interface Design (Article II Compliance)

```bash
# Paper research commands
python -m cli paper research --arxiv-id "2508.07407" --audience practitioner
python -m cli paper research --title "attention is all you need" --audience expert
python -m cli paper full --arxiv-id "2508.07407" --audience beginner --output ./output.md

# Paper search
python -m cli paper search --query "self-evolving agents" --limit 5

# Paper metadata only
python -m cli paper info --arxiv-id "2508.07407"

# Multiple papers
python -m cli paper multi-research --arxiv-ids "2508.07407,1706.03762" --audience practitioner
```

**CLI Module Structure:**

```python
# src/cli/commands/paper.py
import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.lib.agents.arxiv_paper_research_agent import ArXivPaperResearchAgent
from src.lib.services.arxiv_id_parser import parse_arxiv_id, validate_arxiv_id

app = typer.Typer(help="ArXiv paper research commands")
console = Console()


@app.command()
def research(
    arxiv_id: str = typer.Option(None, "--arxiv-id", "-i", help="ArXiv paper ID"),
    title: str = typer.Option(None, "--title", "-t", help="Paper title to search"),
    audience: str = typer.Option("practitioner", "--audience", "-a", help="Target audience"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Generate deep research analysis from an ArXiv paper"""
    
    if not arxiv_id and not title:
        console.print("[red]Error: Provide --arxiv-id or --title[/red]")
        raise typer.Exit(1)
    
    async def run():
        agent = ArXivPaperResearchAgent()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Fetching paper...", total=None)
            
            if arxiv_id:
                result = await agent.research_paper_by_id(
                    arxiv_id=arxiv_id,
                    target_audience=audience,
                )
            else:
                result = await agent.research_paper_by_title(
                    title=title,
                    target_audience=audience,
                )
            
            progress.update(task, description="Complete!")
        
        # Display results
        console.print(Panel(
            f"[bold]{result.paper_metadata.title}[/bold]\n\n"
            f"Authors: {', '.join(result.paper_metadata.authors[:3])}...\n"
            f"ArXiv ID: {result.paper_metadata.arxiv_id}\n"
            f"Completeness: {result.completeness_score:.0%}",
            title="Paper Research Complete",
        ))
        
        if output:
            # Save to file
            pass
        
        return result
    
    asyncio.run(run())


@app.command()
def full(
    arxiv_id: str = typer.Option(..., "--arxiv-id", "-i", help="ArXiv paper ID"),
    audience: str = typer.Option("practitioner", "--audience", "-a"),
    output: str = typer.Option(None, "--output", "-o"),
):
    """Generate research AND blog from an ArXiv paper"""
    # Implementation similar to research but also generates blog
    pass


@app.command()
def search(
    query: str = typer.Option(..., "--query", "-q", help="Search query"),
    limit: int = typer.Option(5, "--limit", "-l", help="Max results"),
):
    """Search ArXiv for papers"""
    pass


@app.command()
def info(
    arxiv_id: str = typer.Option(..., "--arxiv-id", "-i", help="ArXiv paper ID"),
):
    """Get paper metadata without research"""
    pass
```

## 9. Testing Strategy

### Test Execution Order:
1. **Unit Tests** → Test ArXiv ID parsing, validation, prompt formatting
2. **Integration Tests** → Test paper research workflow with real ArXiv + LLM
3. **E2E Tests** → Test API endpoints with full stack

### Test Environment:

```python
# tests/conftest.py (extend existing)
import pytest
from src.lib.services.arxiv_client import ArXivClient

@pytest.fixture
def arxiv_client():
    """ArXiv client for tests"""
    return ArXivClient()

@pytest.fixture
def sample_arxiv_ids():
    """Known valid ArXiv IDs for testing"""
    return [
        "1706.03762",  # Attention Is All You Need
        "2005.14165",  # GPT-3
        "2508.07407",  # Self-Evolving Agents
    ]

@pytest.fixture
def paper_research_agent(llm):
    """Paper research agent with real LLM"""
    from src.lib.agents.arxiv_paper_research_agent import ArXivPaperResearchAgent
    return ArXivPaperResearchAgent(llm=llm)
```

### Test Scenarios (From spec.md):

**Unit Tests:**
- [ ] Test ArXiv ID parsing: `2508.07407`, `arxiv:2508.07407`, `arXiv:2508.07407v2`
- [ ] Test invalid ArXiv ID detection: `abc123`, `123`, empty string
- [ ] Test paper metadata extraction from ArXiv response
- [ ] Test prompt template rendering with paper data
- [ ] Test enhanced output structure validation

**Integration Tests:**
- [ ] Test paper retrieval from real ArXiv API (rate-limited)
- [ ] Test paper research workflow with real LLM
- [ ] Test blog generation from paper research
- [ ] Test multiple paper research synthesis
- [ ] Test error handling for non-existent papers

**E2E Tests:**
- [ ] POST `/api/v1/paper/research` - async paper research
- [ ] POST `/api/v1/paper/research/sync` - sync paper research
- [ ] POST `/api/v1/paper/full/sync` - research + blog
- [ ] GET `/api/v1/paper/research/{id}/result` - get result
- [ ] Error handling: invalid ID, paper not found

## 10. Implementation Phases

### Phase 1: Foundation (2 days)
**Deliverables:**
- [ ] ArXiv ID parser and validator (`src/lib/services/arxiv_id_parser.py`)
- [ ] Paper-specific prompts (`src/lib/llm/prompts/paper_research.txt`, `paper_blog.txt`)
- [ ] Pydantic schemas for paper research (`src/lib/models/schemas.py` extension)
- [ ] Unit tests for ID parsing and validation

**Prerequisites:** None

### Phase 2: Core Agent (3 days)
**Deliverables:**
- [ ] `ArXivPaperResearchAgent` implementation
- [ ] Enhanced research output dataclass
- [ ] Integration with existing `ArXivClient`
- [ ] Integration with `ReActResearchAgent` (extended prompts)
- [ ] Integration with `BlogWriterAgent` (paper prompts)
- [ ] Unit tests for agent logic

**Prerequisites:** Phase 1 complete

### Phase 3: API Routes (2 days)
**Deliverables:**
- [ ] FastAPI routes in `src/api/routes/paper.py`
- [ ] Register routes in `src/api/main.py`
- [ ] Async and sync endpoints
- [ ] Background task handling
- [ ] E2E tests for API endpoints

**Prerequisites:** Phase 2 complete

### Phase 4: CLI & Polish (2 days)
**Deliverables:**
- [ ] CLI commands in `src/cli/commands/paper.py`
- [ ] Register CLI in `src/cli/main.py`
- [ ] Error handling and edge cases
- [ ] Integration tests for full workflow
- [ ] Documentation updates

**Prerequisites:** Phase 3 complete

### Phase 5: Database Extension (1 day, optional)
**Deliverables:**
- [ ] Alembic migration for `paper_research` table
- [ ] SQLAlchemy model for paper research
- [ ] Update repository layer
- [ ] Integration tests for database operations

**Prerequisites:** Phase 4 complete, if database extension needed

## 11. New Prompts Design

### Paper Research Prompt (`paper_research.txt`)

```text
You are an expert AI Research Analyst specializing in academic paper analysis.

## Your Task
Analyze the following ArXiv paper and produce a comprehensive research report.

## Paper Information
- **Title:** {paper_title}
- **Authors:** {paper_authors}
- **ArXiv ID:** {arxiv_id}
- **Published:** {paper_published}
- **Categories:** {paper_categories}
- **Abstract:** {paper_abstract}

## Target Audience: {target_audience}

## Required Output Sections

1. **Paper Overview** (200-300 words)
   - Main contribution and novelty
   - Problem being solved
   - Key innovation

2. **Methodology Deep-Dive** (400-600 words)
   - Detailed explanation of approach
   - Key algorithms or techniques
   - For ML papers: model architecture, training, datasets
   - For theoretical papers: key theorems, mathematical framework

3. **Experimental Results** (200-400 words)
   - Key findings and metrics
   - Benchmark comparisons
   - Statistical significance

4. **Practical Implications** (200-300 words)
   - Real-world applications
   - Industry relevance
   - Prerequisites for application

5. **Limitations & Future Work** (100-200 words)
   - Acknowledged limitations
   - Suggested future directions

6. **Related Work Summary** (100-200 words)
   - Key related papers
   - How this paper differs

7. **Key Concepts** (10+ concepts)
   - Each concept with detailed explanation

8. **Mathematical Foundations** (if applicable)
   - Key equations with explanations

## Output Format
Respond ONLY with valid JSON in the following structure:
{
  "paper_overview": "...",
  "methodology_deep_dive": "...",
  "experimental_results": "...",
  "practical_implications": "...",
  "limitations_future_work": "...",
  "related_work_summary": "...",
  "key_concepts": {"concept": "explanation", ...},
  "mathematical_foundations": "...",
  "topic_summary": "Comprehensive 500-word summary...",
  "implementation_examples": "..."
}
```

### Paper Blog Prompt (`paper_blog.txt`)

```text
You are an expert technical writer creating a blog post about an academic paper.

## Paper Information
- **Title:** {paper_title}
- **Authors:** {paper_authors}
- **ArXiv ID:** {arxiv_id}

## Research Summary
{research_summary}

## Target Audience: {target_audience}
{audience_guidelines}

## Blog Structure Requirements

1. **Hook** - Engaging opening that captures why this paper matters
2. **Paper Introduction** - Brief intro to the paper with proper citation
3. **The Problem** - What problem does this paper address?
4. **The Solution** - Key methodology and approach (accessible explanation)
5. **Key Findings** - Main results and their significance
6. **Why It Matters** - Practical implications and applications
7. **Conclusion** - Takeaways and call-to-action

## Citation Format
Include this citation in the introduction:
"{paper_title}" by {paper_authors}, arXiv:{arxiv_id}, {paper_published}

## Output Format
Respond ONLY with valid JSON:
{
  "title": "Engaging blog title",
  "content": "Full markdown blog content...",
  "meta_description": "SEO-friendly description",
  "tags": ["tag1", "tag2"],
  "estimated_reading_time": "X min read"
}
```

## 12. Error Handling Strategy

```python
# src/lib/models/exceptions.py (extend existing)

class ArXivPaperError(Exception):
    """Base exception for ArXiv paper operations"""
    pass

class InvalidArXivIdError(ArXivPaperError):
    """Invalid ArXiv ID format"""
    def __init__(self, arxiv_id: str):
        self.arxiv_id = arxiv_id
        super().__init__(
            f"Invalid ArXiv ID format: '{arxiv_id}'. "
            f"Expected format: '2508.07407' or 'arxiv:2508.07407v2'"
        )

class PaperNotFoundError(ArXivPaperError):
    """Paper not found on ArXiv"""
    def __init__(self, arxiv_id: str):
        self.arxiv_id = arxiv_id
        super().__init__(f"Paper not found on ArXiv: {arxiv_id}")

class PaperContentInsufficientError(ArXivPaperError):
    """Paper content insufficient for research"""
    pass

class MultiplePapersLimitError(ArXivPaperError):
    """Too many papers requested"""
    def __init__(self, count: int, limit: int = 5):
        super().__init__(f"Maximum {limit} papers allowed, got {count}")
```

**Error Handling Patterns:**
- Validate ArXiv ID format before API calls
- Retry with exponential backoff for ArXiv rate limits
- Clear error messages with format examples
- Graceful degradation for partial failures

## 13. Performance Considerations

**ArXiv API Rate Limiting:**
- Existing `ArXivClient` already implements 1 req/sec rate limiting
- Add request queuing for multiple paper requests
- Cache paper metadata to avoid redundant calls

**LLM Optimization:**
- Paper research uses single comprehensive prompt (reduces API calls)
- Blog generation is separate call (can be parallelized)
- Estimate: 2 LLM calls for single paper (research + blog)

**Caching Strategy:**
- Cache paper metadata for 24 hours (papers don't change frequently)
- Consider Redis for paper cache if volume increases
- For V1: use in-memory cache (simple dict with TTL)

**Database Indexing:**
- Index on `arxiv_id` for lookup
- Index on `created_at` for time-based queries

## 14. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|----------|
| ArXiv API rate limiting | Medium | Respect rate limits, queue requests, cache metadata |
| Paper abstract insufficient for deep research | Medium | Supplement with web search, flag incomplete research |
| LLM output parsing failures | Medium | Retry with simplified prompt, fallback to basic research |
| Long research times (> 8 min) | Low | Set timeout, provide progress feedback |
| Multiple paper synthesis complexity | Medium | Limit to 5 papers, clear synthesis prompts |

## 15. Quality Gates

### Before Implementation:
- [ ] All [Needs clarification] in spec.md addressed (or documented as V2)
- [ ] SDD constitutional gates passed
- [ ] Test strategy approved
- [ ] Prompt templates reviewed

### Before Completion:
- [ ] All tests passing (unit, integration, e2e)
- [ ] All acceptance criteria met
- [ ] CLI interface complete
- [ ] API endpoints documented in OpenAPI
- [ ] Performance requirements met (< 8 min single paper)
- [ ] Error handling comprehensive
- [ ] No abstraction violations

## 16. Traceability Matrix

| Spec Requirement | Implementation Component | Test Coverage |
|------------------|-------------------------|---------------|
| Story 1: Input ArXiv ID | `arxiv_id_parser.py` → `parse_arxiv_id()` | `tests/unit/test_arxiv_id_parser.py` |
| Story 2: Search by title | `arxiv_client.py` → `search()` | `tests/integration/test_paper_research_workflow.py` |
| Story 3: Blog generation | `arxiv_paper_research_agent.py` → `generate_blog()` | `tests/integration/test_paper_research_workflow.py` |
| Story 4: Methodology breakdown | `paper_research.txt` prompt + agent | `tests/unit/test_arxiv_paper_research_agent.py` |
| Story 5: Practical implications | `paper_research.txt` prompt + agent | `tests/unit/test_arxiv_paper_research_agent.py` |
| Story 6: Target audience | Agent + BlogWriterAgent | `tests/integration/test_paper_research_workflow.py` |
| Story 7: Multiple papers | Agent `research_multiple_papers()` | `tests/integration/test_paper_research_workflow.py` |
| Story 8: Related work | `paper_research.txt` prompt | `tests/unit/test_arxiv_paper_research_agent.py` |
| FR1: Input processing | `arxiv_id_parser.py` | `tests/unit/test_arxiv_id_parser.py` |
| FR2: Paper retrieval | `ArXivClient.get_paper()` | `tests/integration/test_paper_research_workflow.py` |
| FR3: Enhanced research | `ArXivPaperResearchAgent` | `tests/unit/test_arxiv_paper_research_agent.py` |
| FR8: Integration | API routes + agent | `tests/e2e/test_paper_api.py` |
| FR10: Error handling | Exceptions + API handlers | `tests/e2e/test_paper_api.py` |

---

**Package Management Notes:**
- This project uses `uv` as package manager (not pip or poetry)
- No new dependencies required (uses existing LangChain, httpx, FastAPI)
- To sync environment: `uv sync`
- Virtual environment: `.venv` (managed by uv)

**Key Dependencies (already installed):**
- `langchain`, `langgraph`, `langchain-aws` - Agent framework
- `langchain-community` - ArXiv tool
- `httpx` - Async HTTP client (ArXivClient)
- `fastapi`, `uvicorn` - API framework
- `typer`, `rich` - CLI framework
- `sqlalchemy`, `alembic` - Database

---

**Document Version:** 1.0  
**Last Updated:** December 7, 2025  
**Status:** Ready for Implementation

**Next Steps:**
1. Generate task breakdown (`tasks.md`)
2. Begin Phase 1: Foundation (ArXiv ID parser, prompts, schemas)
3. Write tests first per Article III

