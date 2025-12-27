# AI Research Agent - Codebase Structure

## Overview

This document provides a comprehensive view of the existing `src/` codebase structure and the target `python-fast-api-seed/` migration structure.

---

## Current `src/` Structure (Source)

```
src/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   ├── middleware.py               # Error handling, logging, validation middleware
│   └── routes/
│       ├── __init__.py
│       ├── branding.py             # Branding API endpoints
│       ├── content.py              # Blog/content generation endpoints
│       ├── paper.py                # ArXiv paper research endpoints
│       ├── pipelines.py            # Pipeline execution endpoints
│       ├── research.py             # Research query endpoints
│       └── social.py               # LinkedIn/Twitter endpoints
│
├── cli/
│   ├── __init__.py
│   ├── main.py                     # Typer CLI entry point
│   └── commands/
│       ├── __init__.py
│       ├── content.py              # Content generation commands
│       ├── paper.py                # Paper research commands
│       ├── pipeline.py             # Pipeline commands
│       ├── research.py             # Research commands
│       └── social.py               # Social content commands
│
├── common/
│   ├── __init__.py
│   ├── config.py                   # Configuration (env-based Config class)
│   ├── database.py                 # SQLAlchemy async engine/session
│   ├── logger.py                   # Logging setup
│   ├── retry.py                    # Retry utilities
│   └── validators.py               # Validation helpers
│
└── lib/
    ├── __init__.py
    ├── agents/
    │   ├── __init__.py             # Agent exports
    │   ├── agentic_researcher.py   # LangGraph-based research agent
    │   ├── arxiv_paper_research_agent.py  # ArXiv paper agent
    │   ├── blog_writer_agent.py    # Blog generation agent
    │   ├── branding_agent.py       # Brand voice agent
    │   ├── shortform_agent.py      # LinkedIn/Twitter agent
    │   └── topic_agent.py          # Topic categorization agent
    │
    ├── llm/
    │   ├── __init__.py
    │   ├── model.py                # BedrockLLM wrapper
    │   ├── prompt_loader.py        # Prompt loading utilities
    │   └── prompts/
    │       ├── __init__.py         # PromptRegistry
    │       ├── base.py             # BasePrompt class
    │       ├── blog.py             # Blog prompts
    │       ├── branding.py         # Branding prompts
    │       ├── paper.py            # Paper research prompts
    │       ├── research.py         # Research prompts
    │       ├── social.py           # Social content prompts
    │       └── topic.py            # Topic categorization prompts
    │
    ├── models/
    │   ├── __init__.py
    │   ├── exceptions.py           # Custom exception classes
    │   ├── repository.py           # ResearchRepository CRUD
    │   ├── research.py             # SQLAlchemy models (ResearchQuery, etc.)
    │   └── schemas.py              # Pydantic schemas (Request/Response)
    │
    ├── orchestrator/
    │   ├── __init__.py
    │   ├── router.py               # Workflow routing
    │   ├── state_manager.py        # State/checkpoint management
    │   └── workflow_manager.py     # Workflow orchestration
    │
    ├── pipelines/
    │   ├── __init__.py
    │   ├── blog_pipeline.py        # Blog generation pipeline
    │   └── research_pipeline.py    # Research execution pipeline
    │
    └── services/
        ├── __init__.py
        ├── arxiv_client.py         # ArXiv API client
        ├── arxiv_id_parser.py      # ArXiv ID validation
        ├── github_trending_client.py # GitHub trending client
        ├── hackernews_client.py    # Hacker News client
        ├── tavily_client.py        # Tavily search client
        └── web_scraper.py          # Web content scraper
```

---

## Target `python-fast-api-seed/` Structure

```
python-fast-api-seed/
├── main.py                         # Uvicorn entry point
├── pyproject.toml                  # Dependencies (merged)
├── alembic.ini
│
├── app/
│   ├── __init__.py
│   ├── main_app.py                 # FastAPI app with lifecycle
│   │
│   ├── common/
│   │   ├── __init__.py
│   │   ├── constants/
│   │   │   ├── error_constant.py   # Error codes
│   │   │   └── service_constant.py # ModulesEnum
│   │   ├── decorators/             # Custom decorators
│   │   ├── exceptions/
│   │   │   ├── __init__.py
│   │   │   └── research_exceptions.py  # ← From src/lib/models/exceptions.py
│   │   ├── middleware/
│   │   │   ├── auth_middleware.py
│   │   │   ├── rate_limiter.py
│   │   │   └── request_context.py
│   │   ├── services/               # External API clients
│   │   │   ├── __init__.py
│   │   │   ├── arxiv_client.py     # ← From src/lib/services/
│   │   │   ├── github_client.py    # ← From src/lib/services/
│   │   │   ├── hackernews_client.py
│   │   │   ├── tavily_client.py    # ← From src/lib/services/
│   │   │   └── web_scraper.py      # ← From src/lib/services/
│   │   ├── utils/
│   │   └── validators/
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth/                   # JWT authentication
│   │   ├── cache/                  # Caching layer
│   │   ├── config/
│   │   │   └── environment_config.py  # ← Merged from src/common/config.py
│   │   ├── exception/
│   │   │   └── global_handlers.py  # ← From src/api/middleware.py
│   │   ├── lifecycle.py            # App startup/shutdown
│   │   ├── llm/                    # LLM integration
│   │   │   ├── __init__.py
│   │   │   ├── bedrock_llm.py      # ← From src/lib/llm/model.py
│   │   │   ├── prompt_loader.py    # ← From src/lib/llm/prompt_loader.py
│   │   │   └── prompts/            # ← From src/lib/llm/prompts/
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       ├── blog.py
│   │   │       ├── branding.py
│   │   │       ├── paper.py
│   │   │       ├── research.py
│   │   │       ├── social.py
│   │   │       └── topic.py
│   │   └── logging/                # Loguru-based logging
│   │
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── v1_router.py            # Module router registration
│   │   │
│   │   ├── auth/                   # Authentication module
│   │   │   └── routers/endpoints.py
│   │   │
│   │   ├── health/                 # Health check module
│   │   │   └── routers/endpoints.py
│   │   │
│   │   ├── user/                   # User management module
│   │   │   ├── models/
│   │   │   ├── repositories/
│   │   │   ├── routers/v1/endpoints.py
│   │   │   ├── schemas/
│   │   │   └── services/
│   │   │
│   │   ├── research/               # ← From src/api/routes/research.py
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   └── research_model.py   # ResearchQuery, ResearchResult
│   │   │   ├── repositories/
│   │   │   │   └── research_repository.py
│   │   │   ├── routers/
│   │   │   │   └── v1/endpoints.py
│   │   │   ├── schemas/
│   │   │   │   └── research_schemas.py
│   │   │   └── services/
│   │   │       ├── agentic_researcher.py  # ← From src/lib/agents/
│   │   │       ├── research_service.py
│   │   │       └── topic_agent.py         # ← From src/lib/agents/
│   │   │
│   │   ├── content/                # ← From src/api/routes/content.py
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   └── content_model.py   # ContentItem
│   │   │   ├── repositories/
│   │   │   ├── routers/
│   │   │   │   └── v1/endpoints.py
│   │   │   ├── schemas/
│   │   │   │   └── content_schemas.py
│   │   │   └── services/
│   │   │       ├── blog_pipeline.py   # ← From src/lib/pipelines/
│   │   │       └── blog_writer_agent.py # ← From src/lib/agents/
│   │   │
│   │   ├── paper/                  # ← From src/api/routes/paper.py
│   │   │   ├── __init__.py
│   │   │   ├── routers/
│   │   │   │   └── v1/endpoints.py
│   │   │   ├── schemas/
│   │   │   │   └── paper_schemas.py
│   │   │   └── services/
│   │   │       ├── arxiv_paper_agent.py  # ← From src/lib/agents/
│   │   │       └── arxiv_client.py       # (or use common/services)
│   │   │
│   │   ├── social/                 # ← From src/api/routes/social.py
│   │   │   ├── __init__.py
│   │   │   ├── routers/
│   │   │   │   └── v1/endpoints.py
│   │   │   ├── schemas/
│   │   │   │   └── social_schemas.py
│   │   │   └── services/
│   │   │       └── shortform_agent.py  # ← From src/lib/agents/
│   │   │
│   │   ├── branding/               # ← From src/api/routes/branding.py
│   │   │   ├── __init__.py
│   │   │   ├── routers/
│   │   │   │   └── v1/endpoints.py
│   │   │   ├── schemas/
│   │   │   │   └── branding_schemas.py
│   │   │   └── services/
│   │   │       └── branding_agent.py  # ← From src/lib/agents/
│   │   │
│   │   ├── pipelines/              # ← From src/api/routes/pipelines.py
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   └── pipeline_model.py   # PipelineExecution
│   │   │   ├── routers/
│   │   │   │   └── v1/endpoints.py
│   │   │   ├── schemas/
│   │   │   └── services/
│   │   │       ├── pipeline_service.py
│   │   │       └── research_pipeline.py  # ← From src/lib/pipelines/
│   │   │
│   │   └── well_known/             # JWKS endpoint
│   │
│   └── utils/                      # Shared utilities
│
├── database/
│   └── database.py                 # SQLAlchemy setup with Base
│
├── migrations/                     # Alembic migrations
│   ├── env.py
│   └── versions/
│       └── (migration files)
│
├── cli/                            # CLI (optional, at project root)
│   ├── main.py                     # ← From src/cli/main.py
│   └── commands/                   # ← From src/cli/commands/
│
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## File-by-File Migration Mapping

### Configuration

| Source | Target | Notes |
|--------|--------|-------|
| `src/common/config.py` | `app/core/config/environment_config.py` | Merged - uses pydantic-settings |
| `src/common/database.py` | `database/database.py` | Already exists in seed |
| `src/common/logger.py` | `app/core/logging/` | Replaced with Loguru |

### API Routes → Module Routers

| Source | Target Module |
|--------|--------------|
| `src/api/routes/research.py` | `app/modules/research/routers/v1/endpoints.py` |
| `src/api/routes/content.py` | `app/modules/content/routers/v1/endpoints.py` |
| `src/api/routes/paper.py` | `app/modules/paper/routers/v1/endpoints.py` |
| `src/api/routes/social.py` | `app/modules/social/routers/v1/endpoints.py` |
| `src/api/routes/branding.py` | `app/modules/branding/routers/v1/endpoints.py` |
| `src/api/routes/pipelines.py` | `app/modules/pipelines/routers/v1/endpoints.py` |

### Middleware → Global Handlers

| Source | Target | Notes |
|--------|--------|-------|
| `src/api/middleware.py` | `app/core/exception/global_handlers.py` | Merge error handling |

### Database Models

| Source | Target | Notes |
|--------|--------|-------|
| `src/lib/models/research.py` → `ResearchQuery`, `ResearchResult` | `app/modules/research/models/` | |
| `src/lib/models/research.py` → `ContentItem` | `app/modules/content/models/` | |
| `src/lib/models/research.py` → `PipelineExecution` | `app/modules/pipelines/models/` | |
| `src/lib/models/research.py` → `TopicCategory` | Shared enum or per-module | |

### Pydantic Schemas

| Source | Target |
|--------|--------|
| `src/lib/models/schemas.py` → Research* | `app/modules/research/schemas/` |
| `src/lib/models/schemas.py` → Blog*, Content* | `app/modules/content/schemas/` |
| `src/lib/models/schemas.py` → Paper* | `app/modules/paper/schemas/` |
| `src/lib/models/schemas.py` → Social* | `app/modules/social/schemas/` (inline in routes) |
| `src/lib/models/schemas.py` → Pipeline* | `app/modules/pipelines/schemas/` |

### Agents/Services

| Source | Target |
|--------|--------|
| `src/lib/agents/agentic_researcher.py` | `app/modules/research/services/agentic_researcher.py` |
| `src/lib/agents/topic_agent.py` | `app/modules/research/services/topic_agent.py` |
| `src/lib/agents/blog_writer_agent.py` | `app/modules/content/services/blog_writer_agent.py` |
| `src/lib/agents/arxiv_paper_research_agent.py` | `app/modules/paper/services/arxiv_paper_agent.py` |
| `src/lib/agents/shortform_agent.py` | `app/modules/social/services/shortform_agent.py` |
| `src/lib/agents/branding_agent.py` | `app/modules/branding/services/branding_agent.py` |

### Pipelines

| Source | Target |
|--------|--------|
| `src/lib/pipelines/research_pipeline.py` | `app/modules/pipelines/services/research_pipeline.py` |
| `src/lib/pipelines/blog_pipeline.py` | `app/modules/content/services/blog_pipeline.py` |

### External Services (Shared)

| Source | Target |
|--------|--------|
| `src/lib/services/tavily_client.py` | `app/common/services/tavily_client.py` |
| `src/lib/services/arxiv_client.py` | `app/common/services/arxiv_client.py` |
| `src/lib/services/arxiv_id_parser.py` | `app/common/services/arxiv_id_parser.py` |
| `src/lib/services/github_trending_client.py` | `app/common/services/github_client.py` |
| `src/lib/services/hackernews_client.py` | `app/common/services/hackernews_client.py` |
| `src/lib/services/web_scraper.py` | `app/common/services/web_scraper.py` |

### LLM Integration

| Source | Target |
|--------|--------|
| `src/lib/llm/model.py` | `app/core/llm/bedrock_llm.py` |
| `src/lib/llm/prompt_loader.py` | `app/core/llm/prompt_loader.py` |
| `src/lib/llm/prompts/*` | `app/core/llm/prompts/*` |

### Exceptions

| Source | Target |
|--------|--------|
| `src/lib/models/exceptions.py` | `app/common/exceptions/research_exceptions.py` |

### Orchestrator

| Source | Target |
|--------|--------|
| `src/lib/orchestrator/state_manager.py` | `app/modules/pipelines/services/state_manager.py` |
| `src/lib/orchestrator/workflow_manager.py` | `app/modules/pipelines/services/workflow_manager.py` |

### Repository

| Source | Target |
|--------|--------|
| `src/lib/models/repository.py` | Split per module (e.g., `research_repository.py`) |

---

## Key Components Summary

### Agents (6 total)

1. **TopicAgent** - Query categorization (AI vs non-AI, topic type)
2. **AgenticResearcher** - LangGraph-based research with tools (Tavily, ArXiv, Wikipedia, GitHub)
3. **ArXivPaperResearchAgent** - Paper-specific research agent
4. **BlogWriterAgent** - Blog content generation
5. **ShortformAgent** - LinkedIn posts, Twitter threads
6. **BrandingAgent** - Brand voice application

### External Services (6 total)

1. **TavilySearchClient** - AI-powered web search
2. **ArXivClient** - Academic paper search/retrieval
3. **GitHubTrendingClient** - GitHub repository search
4. **HackerNewsClient** - Tech news client
5. **WebScraper** - URL content scraping

### Pipelines (2 total)

1. **ResearchPipeline** - Topic categorization → Research → Persistence
2. **BlogGenerationPipeline** - Research → Blog → Social content

### Database Models (4 tables)

1. **research_queries** - User research queries with status
2. **research_results** - Research output (summary, concepts, sources)
3. **content_items** - Generated content (blogs, posts)
4. **pipeline_executions** - Pipeline run tracking

### LLM Prompts (9 types)

1. ResearchPrompt, SynthesisPrompt
2. TopicCategorizationPrompt
3. BlogPrompt
4. LinkedInPostPrompt, TwitterThreadPrompt
5. BrandingPrompt
6. PaperResearchPrompt, PaperBlogPrompt

---

## Migration Status

### Already in `python-fast-api-seed/`

| Component | Status |
|-----------|--------|
| `app/core/config/environment_config.py` | ✅ Merged |
| `app/core/llm/` | ✅ Migrated |
| `app/common/services/` | ✅ Migrated |
| `app/modules/research/` | ✅ Scaffolded |
| `app/modules/content/` | ✅ Scaffolded |
| `app/modules/paper/` | ✅ Scaffolded |
| `app/modules/social/` | ✅ Scaffolded |
| `app/modules/branding/` | ✅ Scaffolded |
| `app/modules/pipelines/` | ✅ Scaffolded |
| `database/database.py` | ✅ Ready |
| `app/modules/v1_router.py` | ✅ Module routing setup |

### Pending Migration

| Component | Status |
|-----------|--------|
| Agents implementation in module services | 🔄 Needs verification |
| Full endpoint implementations | 🔄 Needs verification |
| Schema migrations | 🔄 Needs copy from alembic/ |
| CLI adaptation | ❌ Pending |
| Exception handlers | 🔄 Needs integration |
| Full test suite | ❌ Pending |

---

## API Endpoints Summary

### Research Module (`/api/v1/research`)

- `POST /query` - Create research query (async)
- `GET /query/{query_id}` - Get query status
- `GET /query/{query_id}/result` - Get research result
- `GET /queries` - List research queries
- `POST /query/sync` - Synchronous research

### Content Module (`/api/v1/content`)

- `POST /blog/generate` - Generate blog from research
- `GET /blog/{content_id}` - Get blog content
- `GET /blogs` - List blog posts
- `GET /query/{query_id}/content` - Get content for query

### Paper Module (`/api/v1/paper`)

- `POST /research/sync` - Research paper synchronously
- `POST /full/sync` - Research + blog generation
- `POST /blog/sync` - Generate blog from paper
- `POST /search` - Search ArXiv papers
- `GET /info/{arxiv_id}` - Get paper metadata
- `POST /research/multiple/sync` - Research multiple papers

### Social Module (`/api/v1/social`)

- `POST /linkedin` - Generate LinkedIn post
- `POST /thread` - Generate Twitter thread
- `POST /summarize` - Summarize for social

### Branding Module (`/api/v1/branding`)

- `POST /apply` - Apply brand voice
- `POST /check` - Check voice alignment
- `POST /suggestions` - Get style suggestions
- `GET /profile` - Get voice profile
- `POST /guidelines` - Get audience guidelines

### Pipelines Module (`/api/v1/pipelines`)

- `POST /full` - Execute full pipeline
- `GET /executions` - List pipeline executions
- `GET /executions/{execution_id}` - Get execution details

---

## Dependencies

### Core Dependencies

- fastapi>=0.116.1
- sqlalchemy>=2.0.41
- asyncpg>=0.31.0
- pydantic-settings>=2.10.1
- uvicorn>=0.35.0

### LLM Dependencies

- langchain>=1.1.0
- langchain-core>=1.1.5
- langchain-aws>=1.0.0
- langchain-community>=0.4.1
- langgraph>=1.0.0
- boto3>=1.35.0

### External API Dependencies

- tavily-python>=0.5.0
- arxiv>=2.1.0
- httpx>=0.28.1
- beautifulsoup4>=4.14.2
- wikipedia>=1.4.0

### CLI Dependencies

- typer>=0.20.0
- rich>=14.2.0

---

*Generated: Dec 27, 2025*


