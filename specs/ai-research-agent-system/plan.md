# Implementation Plan: AI Research Agent System

## 1. Executive Summary

**Feature:** Multi-agent AI research and content generation system using LangChain/LangGraph for autonomous research on AI topics and Medium blog post generation.

**Approach:** 
- Library-first architecture with core agent logic in `src/lib/agents/`
- LangGraph for workflow orchestration and agent coordination
- FastAPI wrapper for REST API access
- PostgreSQL for metadata and state management
- CLI interface for direct agent execution
- Background task processing for pipelines

**Complexity:** High (multi-agent orchestration, LLM integration, multiple data sources, complex workflows)

**Estimated Effort:** 25-30 development days

## 2. SDD Constitutional Gates (Pre-Implementation Checklist)

### ✓ Library-First Principle (Article I)
- [ ] Core agent logic written as independent library modules in `src/lib/agents/`
- [ ] Agents can be imported and used without API layer
- [ ] Clear separation: `src/lib/agents/`, `src/lib/services/`, `src/lib/llm/`, `src/api/`, `src/cli/`
- [ ] LangGraph workflows defined in library layer, reusable across CLI and API

### ✓ CLI Interface Mandate (Article II)
- [ ] All agent functionality accessible via Typer CLI commands
- [ ] Format: `python -m cli.research <query> --audience <audience>`
- [ ] Pipeline execution via CLI: `python -m cli.pipelines daily-research`
- [ ] Direct agent invocation: `python -m cli.agents research --query "transformers"`

### ✓ Test-First Command (Article III)
- [ ] Tests written BEFORE implementation
- [ ] Tests should fail first, then pass after implementation
- [ ] pytest test suite prepared with async support
- [ ] Mock LLM responses for unit tests, real LLM for integration tests (with rate limiting)

### ✓ Simplicity Mandate (Article VII)
- [ ] Maximum 3 project components (lib, api, cli)
- [ ] No designing for future, only current requirements
- [ ] Complexity justified: Multi-agent orchestration requires LangGraph complexity

### ✓ Anti-Abstraction Principle (Article VIII)
- [ ] Using LangChain, LangGraph, FastAPI, SQLAlchemy DIRECTLY (no wrappers)
- [ ] No premature abstractions over LangChain agents
- [ ] Single model throughout (no DTO/Entity separation unless proven need)
- [ ] Direct AWS Bedrock integration via boto3 (no abstraction layer)

### ✓ Integration-First Testing (Article IX)
- [ ] Tests use real PostgreSQL (test database)
- [ ] Tests use real AWS Bedrock (with rate limiting and cost controls)
- [ ] Tests use real external APIs (ArXiv, GitHub) with test fixtures
- [ ] No mocking of databases/external services in integration tests

### ⚠️ CRITICAL: Async Pattern for Agent Workflows
- [ ] **LangGraph workflows are async** (`async def` for node functions)
- [ ] **CLI commands use `asyncio.run()`** to execute async workflows
- [ ] **FastAPI endpoints are async** and await LangGraph execution
- [ ] **Background tasks:** Use FastAPI BackgroundTasks or Celery (if needed) with sync wrapper pattern
- [ ] **Pattern:** `def cli_command(...): return asyncio.run(async_workflow(...))`
- [ ] **Pattern:** `async def api_endpoint(...): return await graph.ainvoke(...)`
- [ ] **Why:** LangGraph requires async execution, but CLI needs sync entry point

## 3. Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   FastAPI    │  │     CLI      │  │  Background  │    │
│  │   REST API   │  │   (Typer)    │  │   Tasks      │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼──────────────────┼──────────────────┼────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │      Orchestrator Layer              │
          │  ┌──────────────┐  ┌──────────────┐│
          │  │   Router     │  │   Workflow   ││
          │  │              │  │   Manager   ││
          │  └──────┬───────┘  └──────┬───────┘│
          └─────────┼──────────────────┼────────┘
                    │                  │
          ┌─────────▼──────────────────▼────────┐
          │      LangGraph Workflow              │
          │  ┌──────────────────────────────┐   │
          │  │  Topic Agent → Research      │   │
          │  │  Agent → Blog Writer Agent  │   │
          │  │  → Shortform Agent → ...    │   │
          │  └──────────────────────────────┘   │
          └─────────┬────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───▼────┐    ┌─────▼─────┐   ┌─────▼─────┐
│ Agents │    │ Services  │   │   LLM     │
│ Layer  │    │  Layer    │   │  Layer    │
└───┬────┘    └─────┬─────┘   └─────┬─────┘
    │               │               │
    │    ┌──────────▼───────────────┘
    │    │  AWS Bedrock (Claude 4.5) │
    │    └──────────┬────────────────┘
    │               │
┌───▼───────────────▼───────────────────┐
│      External Data Sources             │
│  ArXiv │ GitHub │ HN │ Web Scraping   │
└────────────────────────────────────────┘
                    │
          ┌─────────▼─────────┐
          │   PostgreSQL      │
          │  (Metadata/State)  │
          └───────────────────┘
```

**Flow:**
1. **Request Flow:** User submits query → Router categorizes → Workflow Manager creates LangGraph workflow → Agents execute sequentially/parallel → Results stored
2. **Data Flow:** Query → Topic Agent (categorization) → Research Agent (data collection) → Blog Writer Agent (content generation) → Output
3. **Response Flow:** Agent outputs → Formatted → Stored in PostgreSQL + file system → Returned to user
4. **Pipeline Flow:** Scheduled trigger → Pipeline executor → LangGraph workflow → Results stored → Notifications

## 4. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent Framework | LangChain + LangGraph | Industry standard for multi-agent systems, supports complex workflows |
| LLM Provider | AWS Bedrock (Claude 4.5 Sonnet) | Spec requirement, enterprise-grade, cost-effective |
| API Framework | FastAPI | Async support, auto-documentation, modern Python framework |
| ORM | SQLAlchemy 2.0 | Mature, async support, PostgreSQL integration |
| Database | PostgreSQL | Metadata storage, state management, query history |
| CLI Framework | Typer | Article II mandate, modern CLI framework |
| Workflow Engine | LangGraph | Native support for agent orchestration, state management |
| HTTP Client | httpx | Async HTTP client for external API calls |
| Web Scraping | BeautifulSoup4 + httpx | Reliable parsing, async support |
| Testing | pytest + pytest-asyncio | Standard Python testing, async test support |
| Task Queue | FastAPI BackgroundTasks (or Celery if needed) | Simple async tasks, Celery for complex scheduling |
| Package Manager | uv | Project requirement, fast dependency management |

## 5. Directory Structure (Library-First)

```
project_root/
├── src/
│   ├── lib/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── research_agent.py      # Deep research agent
│   │   │   ├── topic_agent.py         # Topic categorization agent
│   │   │   ├── blog_writer_agent.py   # Blog generation agent
│   │   │   ├── shortform_agent.py     # Short-form content agent
│   │   │   ├── branding_agent.py      # Brand voice agent
│   │   │   ├── distribution_agent.py  # Distribution strategy agent
│   │   │   └── analytics_agent.py     # Analytics and reporting agent
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── web_scraper.py         # Web scraping service
│   │   │   ├── arxiv_client.py        # ArXiv API client
│   │   │   ├── github_trending_client.py  # GitHub API client
│   │   │   ├── hackernews_client.py   # HackerNews API client
│   │   │   ├── linkedin_api.py        # LinkedIn API integration
│   │   │   └── medium_api.py          # Medium API integration
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── model.py               # AWS Bedrock LLM wrapper
│   │   │   └── prompts/
│   │   │       ├── research_prompt.txt
│   │   │       ├── blog_prompt.txt
│   │   │       ├── post_prompt.txt
│   │   │       ├── branding_prompt.txt
│   │   │       └── style_guidelines.txt
│   │   ├── orchestrator/
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # Query routing logic
│   │   │   └── workflow_manager.py    # LangGraph workflow builder
│   │   ├── pipelines/
│   │   │   ├── __init__.py
│   │   │   ├── daily_research_pipeline.py
│   │   │   ├── blog_generation_pipeline.py
│   │   │   ├── post_generation_pipeline.py
│   │   │   └── weekly_report_pipeline.py
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── research.py            # Research data models
│   │       ├── content.py             # Content models
│   │       └── schemas.py             # Pydantic schemas
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── research.py            # Research endpoints
│   │       ├── content.py             # Content endpoints
│   │       └── pipelines.py           # Pipeline endpoints
│   └── cli/
│       ├── __init__.py
│       ├── research.py                # Research CLI commands
│       ├── agents.py                  # Agent CLI commands
│       └── pipelines.py               # Pipeline CLI commands
├── tests/
│   ├── unit/
│   │   ├── test_research_agent.py
│   │   ├── test_topic_agent.py
│   │   ├── test_blog_writer_agent.py
│   │   └── test_services.py
│   ├── integration/
│   │   ├── test_agent_workflows.py
│   │   ├── test_pipelines.py
│   │   └── test_external_apis.py
│   └── e2e/
│       ├── test_research_flow.py
│       └── test_blog_generation_flow.py
├── data/
│   ├── research/
│   │   ├── papers/
│   │   ├── summaries/
│   │   └── tools/
│   ├── content/
│   │   ├── blogs/
│   │   ├── linkedin_posts/
│   │   └── ideas/
│   └── profile/
│       └── voice.json
├── specs/
│   └── ai-research-agent-system/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── alembic/
│   └── versions/
│       └── xxx_create_research_tables.py
├── app.py                            # Application entry point
└── requirements.txt                   # Dependencies (managed by uv)
```

## 6. Data Models (SQLAlchemy)

```python
# src/lib/models/research.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Text, JSON, ForeignKey, Enum
from datetime import datetime
import enum

class Base(DeclarativeBase):
    pass

class TopicCategory(str, enum.Enum):
    CORE_AI = "core_ai"
    PRACTICAL_IMPLEMENTATION = "practical_implementation"

class ResearchQuery(Base):
    __tablename__ = "research_queries"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    topic_category: Mapped[TopicCategory] = mapped_column(Enum(TopicCategory))
    target_audience: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    research_results: Mapped[list["ResearchResult"]] = relationship(back_populates="query")
    content_items: Mapped[list["ContentItem"]] = relationship(back_populates="research_query")

class ResearchResult(Base):
    __tablename__ = "research_results"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("research_queries.id"))
    topic_summary: Mapped[str] = mapped_column(Text)
    key_concepts: Mapped[dict] = mapped_column(JSON)
    mathematical_foundations: Mapped[str] = mapped_column(Text, nullable=True)
    historical_context: Mapped[str] = mapped_column(Text, nullable=True)
    implementation_examples: Mapped[str] = mapped_column(Text, nullable=True)
    sources: Mapped[list[dict]] = mapped_column(JSON)
    research_data_path: Mapped[str] = mapped_column(String(500))
    completeness_score: Mapped[float] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    query: Mapped["ResearchQuery"] = relationship(back_populates="research_results")

class ContentItem(Base):
    __tablename__ = "content_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    research_query_id: Mapped[int] = mapped_column(ForeignKey("research_queries.id"))
    content_type: Mapped[str] = mapped_column(String(50))  # blog, linkedin_post, etc.
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(String(500))
    target_audience: Mapped[str] = mapped_column(String(50))
    tone: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    research_query: Mapped["ResearchQuery"] = relationship(back_populates="content_items")

class PipelineExecution(Base):
    __tablename__ = "pipeline_executions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    execution_data: Mapped[dict] = mapped_column(JSON, nullable=True)
```

**Relationships:**
- `ResearchQuery` → `ResearchResult` (one-to-many)
- `ResearchQuery` → `ContentItem` (one-to-many)
- Content items reference research queries for traceability

## 7. API Design

**OpenAPI Documentation:**
- FastAPI auto-generates complete API documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

**Endpoints:**

| Method | Endpoint | Description | Status | Request | Response |
|--------|----------|-------------|--------|---------|----------|
| POST | `/api/research/query` | Submit research query | 202 | `ResearchQueryRequest` | `ResearchQueryResponse` |
| GET | `/api/research/{query_id}` | Get research status | 200/404 | Path: query_id | `ResearchStatusResponse` |
| GET | `/api/research/{query_id}/result` | Get research result | 200/404 | Path: query_id | `ResearchResultResponse` |
| POST | `/api/content/generate-blog` | Generate blog from research | 202 | `BlogGenerationRequest` | `BlogGenerationResponse` |
| GET | `/api/content/{content_id}` | Get content item | 200/404 | Path: content_id | `ContentItemResponse` |
| GET | `/api/content/` | List content items | 200 | Query: limit, offset, type | `List[ContentItemResponse]` |
| POST | `/api/pipelines/daily-research` | Trigger daily research | 202 | None | `PipelineExecutionResponse` |
| POST | `/api/pipelines/blog-generation` | Trigger blog generation | 202 | `BlogPipelineRequest` | `PipelineExecutionResponse` |
| GET | `/api/pipelines/{execution_id}` | Get pipeline status | 200/404 | Path: execution_id | `PipelineStatusResponse` |

**Request/Response Schemas:**

```python
# src/lib/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ResearchQueryRequest(BaseModel):
    query: str = Field(..., description="Research query text")
    target_audience: Optional[str] = Field("practitioner", description="Target audience")
    content_type: Optional[str] = Field("blog", description="Desired content type")

class ResearchQueryResponse(BaseModel):
    query_id: int
    status: str
    created_at: datetime

class ResearchResultResponse(BaseModel):
    query_id: int
    topic_summary: str
    key_concepts: dict
    sources: List[dict]
    research_data_path: str
    completeness_score: Optional[float]

class BlogGenerationRequest(BaseModel):
    research_query_id: int
    target_audience: Optional[str] = "practitioner"
    tone: Optional[str] = "professional"

class BlogGenerationResponse(BaseModel):
    content_id: int
    title: str
    file_path: str
    status: str
```

**Error Responses:**
- 400: Validation error or business rule violation
- 404: Entity not found
- 422: Pydantic validation failure
- 429: Rate limit exceeded (LLM API)
- 500: Internal server error
- 503: External service unavailable

## 8. CLI Interface Design (Article II Compliance)

```bash
# Research commands
python -m cli.research query "transformers architecture" --audience "expert"
python -m cli.research status --query-id <id>
python -m cli.research result --query-id <id>

# Agent commands (direct invocation)
python -m cli.agents research --query "attention mechanism" --category "core_ai"
python -m cli.agents topic --query "LangChain framework"
python -m cli.agents blog-writer --research-id <id> --audience "beginner"

# Pipeline commands
python -m cli.pipelines daily-research
python -m cli.pipelines blog-generation --research-id <id>
python -m cli.pipelines weekly-report

# Content commands
python -m cli.content list --type blog --limit 10
python -m cli.content get --id <id>
python -m cli.content generate-shortform --blog-id <id>
```

**CLI Module Structure:**

```python
# src/cli/research.py
import typer
import asyncio
from src.lib.orchestrator.workflow_manager import WorkflowManager

app = typer.Typer()

@app.command()
def query(
    query_text: str = typer.Argument(..., help="Research query"),
    audience: str = typer.Option("practitioner", "--audience", "-a"),
):
    """Submit a research query"""
    async def run():
        manager = WorkflowManager()
        result = await manager.execute_research_workflow(query_text, audience)
        typer.echo(f"Research query submitted: {result.query_id}")
    
    asyncio.run(run())

@app.command()
def status(query_id: int = typer.Option(..., "--query-id", "-q")):
    """Get research query status"""
    # Implementation
    pass
```

## 9. Testing Strategy

### Test Execution Order:
1. **Unit Tests** → Test agent logic, services, utilities in isolation
2. **Integration Tests** → Test agent workflows with real LLM (rate-limited), real PostgreSQL
3. **E2E Tests** → Test full research → blog generation flow

### Test Environment:

```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.lib.llm.model import BedrockLLM

@pytest.fixture(scope="session")
def db_engine():
    # Real PostgreSQL test database
    engine = create_engine("postgresql://test:test@localhost/test_db")
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    # Transaction rollback after each test
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def llm():
    # Real AWS Bedrock LLM (with rate limiting)
    return BedrockLLM(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0")

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### Test Scenarios (From spec.md):

**Unit Tests:**
- [ ] Test topic agent categorization (core AI vs practical)
- [ ] Test research agent data collection logic
- [ ] Test blog writer agent formatting
- [ ] Test web scraper parsing
- [ ] Test ArXiv client API calls
- [ ] Test prompt loading and formatting

**Integration Tests:**
- [ ] Test research workflow end-to-end (with real LLM)
- [ ] Test blog generation workflow (with real LLM)
- [ ] Test pipeline execution
- [ ] Test external API integrations (ArXiv, GitHub, HN)
- [ ] Test database persistence

**E2E Tests:**
- [ ] Test full flow: Query → Research → Blog Generation
- [ ] Test pipeline: Daily Research → Blog Generation
- [ ] Test error handling: API failures, rate limits
- [ ] Test concurrent query handling

## 10. Implementation Phases

### Phase 1: Foundation & Infrastructure (5 days)
**Deliverables:**
- [ ] Project structure setup with uv
- [ ] PostgreSQL database setup and Alembic migrations
- [ ] AWS Bedrock LLM integration (`src/lib/llm/model.py`)
- [ ] Basic LangChain agent setup
- [ ] Prompt templates loading system
- [ ] Database models and schemas
- [ ] Basic logging and configuration

**Prerequisites:** AWS credentials, PostgreSQL instance

### Phase 2: Core Agents (8 days)
**Deliverables:**
- [ ] Topic Agent (categorization)
- [ ] Research Agent (data collection and synthesis)
- [ ] Blog Writer Agent (content generation)
- [ ] Unit tests for each agent
- [ ] Integration with external services (ArXiv, GitHub, web scraping)

**Prerequisites:** Phase 1 complete

### Phase 3: Orchestration & Workflows (5 days)
**Deliverables:**
- [ ] Router implementation
- [ ] Workflow Manager with LangGraph
- [ ] Research workflow (Topic → Research → Blog)
- [ ] State management and persistence
- [ ] Integration tests for workflows

**Prerequisites:** Phase 2 complete

### Phase 4: Additional Agents & Pipelines (5 days)
**Deliverables:**
- [ ] Short-form Agent
- [ ] Branding Agent
- [ ] Distribution Agent
- [ ] Analytics Agent
- [ ] Pipeline implementations (daily research, blog generation, weekly report)
- [ ] Pipeline scheduling and execution

**Prerequisites:** Phase 3 complete

### Phase 5: API & CLI (4 days)
**Deliverables:**
- [ ] FastAPI routes and endpoints
- [ ] Typer CLI commands
- [ ] Error handling and validation
- [ ] API documentation
- [ ] E2E tests

**Prerequisites:** Phase 4 complete

### Phase 6: Polish & Optimization (3 days)
**Deliverables:**
- [ ] Performance optimization
- [ ] Rate limiting and retry logic
- [ ] Error recovery mechanisms
- [ ] Documentation
- [ ] Final testing and bug fixes

**Prerequisites:** Phase 5 complete

## 11. Database Migrations

```python
# alembic/versions/001_create_research_tables.py
"""Create research and content tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'research_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('topic_category', sa.Enum('CORE_AI', 'PRACTICAL_IMPLEMENTATION', name='topiccategory'), nullable=True),
        sa.Column('target_audience', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'research_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=True),
        sa.Column('topic_summary', sa.Text(), nullable=True),
        sa.Column('key_concepts', sa.JSON(), nullable=True),
        sa.Column('mathematical_foundations', sa.Text(), nullable=True),
        sa.Column('historical_context', sa.Text(), nullable=True),
        sa.Column('implementation_examples', sa.Text(), nullable=True),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('research_data_path', sa.String(500), nullable=True),
        sa.Column('completeness_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['query_id'], ['research_queries.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table(
        'content_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('research_query_id', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(50), nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('target_audience', sa.String(50), nullable=True),
        sa.Column('tone', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['research_query_id'], ['research_queries.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_research_queries_status', 'research_queries', ['status'])
    op.create_index('idx_research_queries_created_at', 'research_queries', ['created_at'])

def downgrade():
    op.drop_table('content_items')
    op.drop_table('research_results')
    op.drop_table('research_queries')
    op.execute('DROP TYPE topiccategory')
```

## 12. Error Handling Strategy

```python
# src/lib/models/exceptions.py
class ResearchAgentError(Exception):
    """Base exception for research agent errors"""
    pass

class QueryCategorizationError(ResearchAgentError):
    """Failed to categorize query"""
    pass

class ResearchDataInsufficientError(ResearchAgentError):
    """Insufficient research data for content generation"""
    pass

class LLMRateLimitError(ResearchAgentError):
    """LLM API rate limit exceeded"""
    pass

class ExternalAPIError(ResearchAgentError):
    """External API call failed"""
    pass

class ContentGenerationError(Exception):
    """Base exception for content generation errors"""
    pass

class BlogGenerationError(ContentGenerationError):
    """Failed to generate blog post"""
    pass
```

**Error Handling Patterns:**
- Retry with exponential backoff for transient errors (API failures, rate limits)
- Graceful degradation (use cached data if available)
- Detailed logging for debugging
- User-friendly error messages in API responses

## 13. Performance Considerations

**Database Indexing:**
- Index on `research_queries.status` for pipeline queries
- Index on `research_queries.created_at` for time-based queries
- Index on `content_items.research_query_id` for joins

**Query Optimization:**
- Use SQLAlchemy eager loading for relationships
- Pagination for list endpoints
- Connection pooling (SQLAlchemy default)

**Caching Strategy:**
- Cache LLM responses for identical queries (optional, consider cost vs. freshness)
- Cache external API responses (ArXiv papers, GitHub repos) with TTL
- Redis for session state (if needed for long-running workflows)

**Rate Limiting:**
- AWS Bedrock: Implement token bucket or queue-based rate limiting
- External APIs: Respect rate limits, implement backoff
- Per-user rate limiting for API endpoints

**Async Optimization:**
- Parallel agent execution where possible (LangGraph parallel nodes)
- Concurrent external API calls (httpx async client)
- Background task processing for long-running operations

## 14. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|----------|
| **AWS Bedrock rate limits** | High | Implement queue system, retry with exponential backoff, monitor usage |
| **LLM API costs** | High | Monitor token usage, implement cost tracking, set budget alerts |
| **External API failures** | Medium | Graceful degradation, cached data fallback, multiple source redundancy |
| **LangGraph workflow complexity** | Medium | Start with simple workflows, iterate, comprehensive testing |
| **Research data quality** | Medium | Validation checks, completeness scoring, manual review flags |
| **Content quality issues** | Medium | Post-generation validation, readability scoring, user feedback loop |
| **Database performance** | Low | Proper indexing, connection pooling, query optimization |
| **Concurrent query handling** | Medium | Queue system, rate limiting, resource monitoring |
| **Pipeline execution failures** | Medium | Checkpoint/resume capability, error logging, alerting |
| **Async task serialization error** | High | Use sync functions with `asyncio.run()` wrapper for Celery (if used) |

## 15. Quality Gates

### Before Implementation:
- [ ] All [Needs clarification] resolved in spec.md
- [ ] SDD constitutional gates passed
- [ ] Test strategy approved
- [ ] AWS Bedrock access configured
- [ ] PostgreSQL instance available
- [ ] External API credentials obtained (ArXiv, GitHub, etc.)

### Before Completion:
- [ ] All tests passing (unit, integration, e2e)
- [ ] All acceptance criteria met
- [ ] CLI interface complete
- [ ] No abstraction violations
- [ ] Performance requirements met (< 5 min research, < 3 min blog generation)
- [ ] Error handling comprehensive
- [ ] Documentation complete
- [ ] Rate limiting implemented
- [ ] Cost monitoring in place

## 16. Traceability Matrix

| Spec Requirement | Implementation Component | Test Coverage |
|------------------|-------------------------|---------------|
| Story 1: Research Query | `src/lib/agents/research_agent.py` → `conduct_research()` | `tests/unit/test_research_agent.py` |
| Story 2: Topic Categorization | `src/lib/agents/topic_agent.py` → `categorize_query()` | `tests/unit/test_topic_agent.py` |
| Story 3: Blog Generation | `src/lib/agents/blog_writer_agent.py` → `generate_blog()` | `tests/unit/test_blog_writer_agent.py` |
| Story 4: Audience Customization | `src/lib/agents/blog_writer_agent.py` → tone adaptation | `tests/integration/test_blog_generation.py` |
| Story 5: Branded Content | `src/lib/agents/branding_agent.py` → `apply_brand_voice()` | `tests/unit/test_branding_agent.py` |
| Story 6: Daily Pipeline | `src/lib/pipelines/daily_research_pipeline.py` | `tests/integration/test_pipelines.py` |
| Story 7: Weekly Reports | `src/lib/agents/analytics_agent.py` → `generate_report()` | `tests/unit/test_analytics_agent.py` |
| Story 8: Implementation Guidance | `src/lib/agents/research_agent.py` → practical topic handling | `tests/integration/test_research_workflow.py` |
| Story 9: Core AI Research | `src/lib/agents/research_agent.py` → core AI topic handling | `tests/integration/test_research_workflow.py` |
| Story 10: Query Routing | `src/lib/orchestrator/router.py` → `route_query()` | `tests/unit/test_router.py` |
| FR1: Query Processing | `src/lib/orchestrator/router.py` | `tests/unit/test_router.py` |
| FR2: Deep Research | `src/lib/agents/research_agent.py` | `tests/integration/test_research_agent.py` |
| FR3: Data Structure | `src/lib/models/research.py` | `tests/integration/test_models.py` |
| FR4: Blog Generation | `src/lib/agents/blog_writer_agent.py` | `tests/integration/test_blog_generation.py` |
| FR5: Personalization | `src/lib/agents/branding_agent.py` | `tests/unit/test_branding_agent.py` |
| FR6: Orchestration | `src/lib/orchestrator/workflow_manager.py` | `tests/integration/test_workflows.py` |
| FR7: Pipelines | `src/lib/pipelines/*.py` | `tests/integration/test_pipelines.py` |
| FR8: Data Sources | `src/lib/services/*.py` | `tests/integration/test_external_apis.py` |
| FR9: Storage | `src/lib/models/research.py` + file system | `tests/integration/test_storage.py` |
| FR10: Error Handling | `src/lib/models/exceptions.py` | `tests/unit/test_error_handling.py` |
| FR11: Formatting | `src/lib/agents/blog_writer_agent.py` | `tests/unit/test_formatting.py` |
| FR12: Analytics | `src/lib/agents/analytics_agent.py` | `tests/unit/test_analytics_agent.py` |

---

**Package Management Notes:**
- This project uses `uv` as package manager (not pip or poetry)
- To add dependencies: `uv add <package>`
- To sync environment: `uv sync`
- Virtual environment: `.venv` (managed by uv)
- Always activate: `source .venv/bin/activate` before running commands

**Key Dependencies:**
```bash
uv add langchain langgraph langchain-aws
uv add fastapi uvicorn
uv add sqlalchemy alembic psycopg2-binary
uv add typer
uv add httpx beautifulsoup4
uv add pydantic
uv add pytest pytest-asyncio
uv add boto3  # AWS Bedrock
```

---

**Document Version:** 1.0  
**Last Updated:** [Current Date]  
**Status:** Ready for Implementation

