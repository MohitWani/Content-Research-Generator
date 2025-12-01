# AI Research Agent System

Deep research and content generation for AI topics. Built with Python, LangChain, and AWS Bedrock.

## Features

- **Topic Categorization**: Automatically categorizes queries as Core AI or Practical Implementation
- **Deep Research**: Collects data from ArXiv, GitHub, HackerNews, Tavily, and web scraping
- **Blog Generation**: Creates Medium-ready blog posts with proper structure
- **LinkedIn Posts**: Generates engaging social media content
- **Brand Voice**: Applies consistent voice and style across content
- **Full Pipelines**: End-to-end research → blog → social workflows

## Tech Stack

- **Language**: Python 3.11+
- **Framework**: LangChain, LangGraph
- **LLM**: Claude 4.5 Sonnet (AWS Bedrock)
- **API**: FastAPI
- **CLI**: Typer + Rich
- **Database**: PostgreSQL + SQLAlchemy 2.0
- **Search**: Tavily AI Search

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd research

# Install dependencies (using uv)
uv sync

# Activate virtual environment
source .venv/bin/activate

# Copy environment template
cp .env.template .env
# Edit .env with your credentials
```

### Environment Variables

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/research_db
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
TAVILY_API_KEY=your-tavily-key
GITHUB_TOKEN=your-github-token
```

### Database Setup

```bash
# Run Alembic migrations
alembic upgrade head
```

### Usage

#### CLI Commands

```bash
# Quick research + blog generation
python -m src.cli.main quick "Explain transformers" --audience beginner

# Research only
python -m src.cli.main research run "Explain attention mechanism"

# Generate blog from topic
python -m src.cli.main content blog "Introduction to RAG"

# Generate LinkedIn post
python -m src.cli.main content linkedin "Latest in LLMs"

# Full pipeline
python -m src.cli.main pipeline full "Transformers explained" --audience practitioner

# Check system status
python -m src.cli.main status
```

#### API Server

```bash
# Start the API server
uvicorn src.api.main:app --reload --port 8000

# API docs at http://localhost:8000/docs
```

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/research/query` | POST | Create research query |
| `/api/v1/research/query/{id}` | GET | Get research query |
| `/api/v1/research/query/{id}/result` | GET | Get research result |
| `/api/v1/content/blog/generate` | POST | Generate blog post |
| `/api/v1/content/blogs` | GET | List blog posts |
| `/api/v1/pipelines/full` | POST | Execute full pipeline |

## Project Structure

```
src/
├── api/                    # FastAPI application
│   ├── main.py
│   ├── middleware.py
│   └── routes/
├── cli/                    # Typer CLI
│   ├── main.py
│   └── commands/
├── common/                 # Shared utilities
│   ├── config.py
│   ├── database.py
│   ├── logger.py
│   ├── retry.py
│   └── validators.py
└── lib/
    ├── agents/             # AI agents
    │   ├── topic_agent.py
    │   ├── research_agent.py
    │   ├── blog_writer_agent.py
    │   ├── shortform_agent.py
    │   └── branding_agent.py
    ├── llm/                # LLM integration
    │   ├── model.py
    │   ├── prompt_loader.py
    │   └── prompts/
    ├── models/             # Data models
    │   ├── research.py
    │   ├── schemas.py
    │   └── exceptions.py
    ├── orchestrator/       # Workflow orchestration
    │   ├── workflow_manager.py
    │   ├── router.py
    │   └── state_manager.py
    ├── pipelines/          # Automated pipelines
    │   ├── research_pipeline.py
    │   └── blog_pipeline.py
    └── services/           # External services
        ├── tavily_client.py
        ├── arxiv_client.py
        ├── github_trending_client.py
        ├── hackernews_client.py
        └── web_scraper.py
```

## Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/ -v

# Run E2E tests
pytest tests/e2e/ -v

# Run with coverage
pytest --cov=src tests/
```

## Development

### Adding Dependencies

```bash
uv add <package-name>
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## License

MIT

