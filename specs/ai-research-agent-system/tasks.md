# Task Breakdown: AI Research Agent System

**Total Estimated Effort:** 25-30 development days  
**Test-First Approach:** All tests written before implementation

---

## Phase 1: Foundation & Infrastructure (5 days)

### T001: Project Structure & Dependencies [P]
- **Description:** Set up project structure with uv package manager and install core dependencies
- **Dependencies:** None
- **Effort:** 2 hours
- **Files:**
  - `pyproject.toml` (uv project config)
  - `requirements.txt` (if needed)
  - Directory structure creation
- **Commands:**
  ```bash
  uv init
  uv add langchain langgraph langchain-aws
  uv add fastapi uvicorn
  uv add sqlalchemy alembic psycopg2-binary
  uv add typer httpx beautifulsoup4 pydantic
  uv add pytest pytest-asyncio boto3
  ```
- **Quality Gate:**
  - All directories created per plan.md structure
  - Dependencies installed successfully
  - Virtual environment activated
- **Status:** [ ] Not Started

### T002: Database Schema & Models [P]
- **Description:** Create SQLAlchemy models for research queries, results, content items, and pipeline executions
- **Dependencies:** T001
- **Effort:** 4 hours
- **Files:**
  - `src/lib/models/research.py`
  - `src/lib/models/content.py`
  - `src/lib/models/__init__.py`
- **Traces To:** plan.md → Section 6 (Data Models)
- **Quality Gate:**
  - Models defined with proper relationships
  - Models can be imported
  - Type hints correct
- **Status:** [ ] Not Started

### T003: Alembic Migration Setup [P]
- **Description:** Initialize Alembic and create initial migration for research tables
- **Dependencies:** T002
- **Effort:** 3 hours
- **Files:**
  - `alembic.ini`
  - `alembic/env.py`
  - `alembic/versions/001_create_research_tables.py`
- **Traces To:** plan.md → Section 11 (Database Migrations)
- **Quality Gate:**
  - Migration runs successfully (`alembic upgrade head`)
  - Tables created in PostgreSQL
  - Rollback works (`alembic downgrade -1`)
- **Status:** [ ] Not Started

### T004: AWS Bedrock LLM Integration [P]
- **Description:** Create LLM wrapper for AWS Bedrock Claude 4.5 Sonnet with proper async support
- **Dependencies:** T001
- **Effort:** 4 hours
- **Files:**
  - `src/lib/llm/model.py`
  - `src/lib/llm/__init__.py`
- **Traces To:** plan.md → Technology Decisions (AWS Bedrock)
- **Quality Gate:**
  - LLM can be instantiated with AWS credentials
  - Async invoke method works
  - Error handling for rate limits
  - Connection to Bedrock verified
- **Status:** [ ] Not Started

### T005: Prompt Template System [P]
- **Description:** Create system to load and format prompt templates from files
- **Dependencies:** T001
- **Effort:** 3 hours
- **Files:**
  - `src/lib/llm/prompts/research_prompt.txt`
  - `src/lib/llm/prompts/blog_prompt.txt`
  - `src/lib/llm/prompts/post_prompt.txt`
  - `src/lib/llm/prompts/branding_prompt.txt`
  - `src/lib/llm/prompts/style_guidelines.txt`
  - `src/lib/llm/prompt_loader.py` (utility)
- **Traces To:** spec.md → FR4 (Blog Post Generation)
- **Quality Gate:**
  - Prompts load from files correctly
  - Template variables can be substituted
  - Prompts are properly formatted
- **Status:** [ ] Not Started

### T006: Configuration & Logging Setup [P]
- **Description:** Set up configuration management and logging infrastructure
- **Dependencies:** T001
- **Effort:** 2 hours
- **Files:**
  - `src/utils/config.py`
  - `src/utils/logger.py`
  - `.env.example` (template)
- **Quality Gate:**
  - Configuration loads from environment variables
  - Logging works with proper levels
  - Logs include timestamps and context
- **Status:** [ ] Not Started

### T007: Integration Tests - Database Models [Test-First]
- **Description:** Write integration tests for database models using real PostgreSQL
- **Dependencies:** T002, T003
- **Effort:** 3 hours
- **Files:**
  - `tests/conftest.py` (database fixtures)
  - `tests/integration/test_models.py`
- **Test Scenarios:**
  - Test model creation and relationships
  - Test enum types (TopicCategory)
  - Test JSON fields serialization
  - Test timestamps (created_at, updated_at)
  - Test foreign key constraints
- **Quality Gate:**
  - All tests FAIL (no implementation yet)
  - Tests use real PostgreSQL test database
  - Tests are comprehensive
- **Status:** [ ] Not Started

### T008: Pydantic Schemas [P]
- **Description:** Define request/response schemas for API (serves as API contract)
- **Dependencies:** T002
- **Effort:** 3 hours
- **Files:**
  - `src/lib/models/schemas.py`
- **Traces To:** plan.md → Section 7 (API Design), spec.md → FR1-FR12
- **Schemas Required:**
  - `ResearchQueryRequest`, `ResearchQueryResponse`
  - `ResearchResultResponse`, `ResearchStatusResponse`
  - `BlogGenerationRequest`, `BlogGenerationResponse`
  - `ContentItemResponse`
  - `PipelineExecutionResponse`, `PipelineStatusResponse`
- **Quality Gate:**
  - Schemas validate correctly
  - Include field validators and descriptions
  - Cover all API endpoints
  - FastAPI will auto-generate OpenAPI docs from these
- **Status:** [ ] Not Started

---

## Phase 2: Core Agents (8 days)

### T009: External Service Clients [P]
- **Description:** Implement clients for external data sources (ArXiv, GitHub, HackerNews, Web Scraping)
- **Dependencies:** T001, T006
- **Effort:** 8 hours
- **Files:**
  - `src/lib/services/arxiv_client.py`
  - `src/lib/services/github_trending_client.py`
  - `src/lib/services/hackernews_client.py`
  - `src/lib/services/web_scraper.py`
  - `src/lib/services/__init__.py`
- **Traces To:** spec.md → FR8 (Data Source Integration)
- **Quality Gate:**
  - Clients can connect to external APIs
  - Error handling for API failures
  - Rate limiting respected
  - Async/await properly implemented
- **Status:** [ ] Not Started

### T010: Unit Tests - External Services [Test-First]
- **Description:** Write unit tests for external service clients
- **Dependencies:** T009
- **Effort:** 4 hours
- **Files:**
  - `tests/unit/test_services.py`
- **Test Scenarios:**
  - Test ArXiv client search and retrieval
  - Test GitHub trending client
  - Test HackerNews client
  - Test web scraper parsing
  - Test error handling (network failures, rate limits)
- **Quality Gate:**
  - Tests cover all service methods
  - Tests initially FAIL
  - Mock external API responses for unit tests
- **Status:** [ ] Not Started

### T011: Topic Agent Implementation
- **Description:** Implement topic categorization agent using LLM to classify queries as core AI or practical implementation
- **Dependencies:** T004, T005, T008
- **Effort:** 6 hours
- **Files:**
  - `src/lib/agents/topic_agent.py`
  - `src/lib/agents/__init__.py`
- **Traces To:** spec.md → Story 2, FR1 (Query Categorization)
- **Quality Gate:**
  - Agent correctly categorizes queries
  - Returns TopicCategory enum
  - Handles ambiguous queries gracefully
  - Error handling implemented
- **Status:** [ ] Not Started

### T012: Unit Tests - Topic Agent [Test-First]
- **Description:** Write unit tests for topic agent
- **Dependencies:** T011
- **Effort:** 3 hours
- **Files:**
  - `tests/unit/test_topic_agent.py`
- **Test Scenarios:**
  - Test core AI topic detection
  - Test practical implementation topic detection
  - Test ambiguous query handling
  - Test error scenarios
- **Quality Gate:**
  - Tests cover all categorization scenarios
  - Tests initially FAIL
- **Status:** [ ] Not Started

### T013: Research Agent Implementation
- **Description:** Implement deep research agent that collects and synthesizes information from multiple sources
- **Dependencies:** T004, T005, T009, T011
- **Effort:** 12 hours
- **Files:**
  - `src/lib/agents/research_agent.py`
- **Traces To:** spec.md → Story 1, FR2 (Deep Research), Story 8, Story 9
- **Key Features:**
  - Different research strategies for core AI vs practical topics
  - Aggregates data from ArXiv, GitHub, web sources
  - Generates structured research output
  - Calculates completeness score
- **Quality Gate:**
  - Research agent conducts comprehensive research
  - Output includes all required sections
  - Sources properly cited
  - Handles insufficient data scenarios
- **Status:** [ ] Not Started

### T014: Unit Tests - Research Agent [Test-First]
- **Description:** Write unit tests for research agent
- **Dependencies:** T013
- **Effort:** 4 hours
- **Files:**
  - `tests/unit/test_research_agent.py`
- **Test Scenarios:**
  - Test core AI research (math, history, explanation)
  - Test practical implementation research (step-by-step)
  - Test source aggregation
  - Test completeness scoring
  - Test error handling
- **Quality Gate:**
  - Tests cover all research scenarios
  - Tests initially FAIL
- **Status:** [ ] Not Started

### T015: Blog Writer Agent Implementation
- **Description:** Implement blog generation agent that creates Medium-formatted blog posts from research data
- **Dependencies:** T004, T005, T008, T013
- **Effort:** 10 hours
- **Files:**
  - `src/lib/agents/blog_writer_agent.py`
- **Traces To:** spec.md → Story 3, FR4 (Blog Post Generation), Story 4
- **Key Features:**
  - Adapts tone based on target audience
  - Formats content for Medium
  - Includes code blocks, citations, links
  - Maintains technical accuracy
- **Quality Gate:**
  - Blog posts are properly formatted
  - Tone matches target audience
  - Citations included
  - Ready for publication
- **Status:** [ ] Not Started

### T016: Unit Tests - Blog Writer Agent [Test-First]
- **Description:** Write unit tests for blog writer agent
- **Dependencies:** T015
- **Effort:** 4 hours
- **Files:**
  - `tests/unit/test_blog_writer_agent.py`
- **Test Scenarios:**
  - Test blog generation from research data
  - Test audience tone adaptation
  - Test formatting (headers, code blocks, citations)
  - Test error handling (insufficient research data)
- **Quality Gate:**
  - Tests cover all generation scenarios
  - Tests initially FAIL
- **Status:** [ ] Not Started

### T017: Repository Layer Implementation
- **Description:** Implement data access layer with CRUD operations for research queries, results, and content
- **Dependencies:** T002, T007 (tests must exist first)
- **Effort:** 6 hours
- **Files:**
  - `src/lib/models/repository.py`
- **Traces To:** plan.md → Section 6 (Data Models)
- **Quality Gate:**
  - Integration tests (T007) now PASS
  - Repository methods implemented
  - No test mocking used
  - Proper transaction handling
- **Status:** [ ] Not Started

### T018: Integration Tests - Agent Workflows [Test-First]
- **Description:** Write integration tests for agent workflows using real LLM (rate-limited)
- **Dependencies:** T011, T013, T015
- **Effort:** 6 hours
- **Files:**
  - `tests/integration/test_agent_workflows.py`
- **Test Scenarios:**
  - Test topic → research → blog workflow
  - Test with real AWS Bedrock (rate-limited)
  - Test error recovery
  - Test data persistence
- **Quality Gate:**
  - Tests use real LLM (with rate limiting)
  - Tests use real PostgreSQL
  - Tests initially FAIL or PARTIAL PASS
- **Status:** [ ] Not Started

---

## Phase 3: Orchestration & Workflows (5 days)

### T019: Router Implementation
- **Description:** Implement query router that analyzes queries and determines workflow path
- **Dependencies:** T011
- **Effort:** 4 hours
- **Files:**
  - `src/lib/orchestrator/router.py`
  - `src/lib/orchestrator/__init__.py`
- **Traces To:** spec.md → Story 10, FR1 (Query Processing)
- **Quality Gate:**
  - Router correctly routes queries
  - Handles edge cases (ambiguous queries)
  - Returns workflow configuration
- **Status:** [ ] Not Started

### T020: Unit Tests - Router [Test-First]
- **Description:** Write unit tests for router
- **Dependencies:** T019
- **Effort:** 2 hours
- **Files:**
  - `tests/unit/test_router.py`
- **Test Scenarios:**
  - Test query routing logic
  - Test workflow selection
  - Test error handling
- **Quality Gate:**
  - Tests cover all routing scenarios
  - Tests initially FAIL
- **Status:** [ ] Not Started

### T021: Workflow Manager with LangGraph
- **Description:** Implement LangGraph workflow manager that orchestrates agent execution
- **Dependencies:** T011, T013, T015, T019
- **Effort:** 10 hours
- **Files:**
  - `src/lib/orchestrator/workflow_manager.py`
- **Traces To:** plan.md → Section 3 (Technical Architecture), spec.md → FR6 (Multi-Agent Orchestration)
- **Key Features:**
  - LangGraph workflow definition
  - State management
  - Agent sequencing (Topic → Research → Blog)
  - Parallel execution where possible
  - Error handling and recovery
- **Quality Gate:**
  - Workflows execute successfully
  - State persists correctly
  - Agents execute in correct order
  - Error recovery works
- **Status:** [ ] Not Started

### T022: Integration Tests - Workflows [Test-First]
- **Description:** Write integration tests for LangGraph workflows
- **Dependencies:** T021
- **Effort:** 4 hours
- **Files:**
  - `tests/integration/test_workflows.py`
- **Test Scenarios:**
  - Test research workflow end-to-end
  - Test blog generation workflow
  - Test state persistence
  - Test error recovery
  - Test concurrent execution
- **Quality Gate:**
  - Tests use real LangGraph workflows
  - Tests use real agents and LLM
  - Tests initially FAIL or PARTIAL PASS
- **Status:** [ ] Not Started

### T023: State Management & Persistence
- **Description:** Implement state persistence for long-running workflows using PostgreSQL
- **Dependencies:** T021, T017
- **Effort:** 4 hours
- **Files:**
  - `src/lib/orchestrator/state_manager.py`
- **Traces To:** spec.md → FR9 (Content Storage)
- **Quality Gate:**
  - Workflow state persists to database
  - State can be resumed after interruption
  - State queries work efficiently
- **Status:** [ ] Not Started

---

## Phase 4: Additional Agents & Pipelines (5 days)

### T024: Branding Agent Implementation
- **Description:** Implement branding agent that applies brand voice from voice.json profile
- **Dependencies:** T004, T005
- **Effort:** 4 hours
- **Files:**
  - `src/lib/agents/branding_agent.py`
  - `data/profile/voice.json` (template)
- **Traces To:** spec.md → Story 5, FR5 (Content Personalization)
- **Quality Gate:**
  - Brand voice applied consistently
  - Handles missing/corrupted voice.json gracefully
  - Works with blog writer agent
- **Status:** [ ] Not Started

### T025: Unit Tests - Branding Agent [Test-First]
- **Description:** Write unit tests for branding agent
- **Dependencies:** T024
- **Effort:** 2 hours
- **Files:**
  - `tests/unit/test_branding_agent.py`
- **Quality Gate:**
  - Tests cover brand voice application
  - Tests initially FAIL
- **Status:** [ ] Not Started

### T026: Short-form Agent Implementation
- **Description:** Implement short-form content agent for LinkedIn posts and social media
- **Dependencies:** T004, T005, T015
- **Effort:** 4 hours
- **Files:**
  - `src/lib/agents/shortform_agent.py`
- **Traces To:** spec.md → Story 5
- **Quality Gate:**
  - Generates short-form content from blogs
  - Formats for LinkedIn/social media
  - Maintains brand voice
- **Status:** [ ] Not Started

### T027: Distribution Agent Implementation
- **Description:** Implement distribution agent that provides content distribution strategies
- **Dependencies:** T004, T005
- **Effort:** 3 hours
- **Files:**
  - `src/lib/agents/distribution_agent.py`
- **Traces To:** spec.md → Story 5
- **Quality Gate:**
  - Generates distribution recommendations
  - Considers content type and audience
- **Status:** [ ] Not Started

### T028: Analytics Agent Implementation
- **Description:** Implement analytics agent for content performance tracking and reporting
- **Dependencies:** T004, T017
- **Effort:** 5 hours
- **Files:**
  - `src/lib/agents/analytics_agent.py`
- **Traces To:** spec.md → Story 7, FR12 (Analytics)
- **Quality Gate:**
  - Aggregates content metrics
  - Generates trend analysis
  - Creates weekly reports
- **Status:** [ ] Not Started

### T029: Daily Research Pipeline
- **Description:** Implement daily research pipeline that identifies trending topics and conducts research
- **Dependencies:** T009, T021
- **Effort:** 6 hours
- **Files:**
  - `src/lib/pipelines/daily_research_pipeline.py`
  - `src/lib/pipelines/__init__.py`
- **Traces To:** spec.md → Story 6, FR7 (Pipeline Automation)
- **Quality Gate:**
  - Pipeline identifies trending topics
  - Conducts research automatically
  - Stores results properly
  - Handles errors gracefully
- **Status:** [ ] Not Started

### T030: Blog Generation Pipeline
- **Description:** Implement pipeline that processes research data into blog posts
- **Dependencies:** T015, T021
- **Effort:** 4 hours
- **Files:**
  - `src/lib/pipelines/blog_generation_pipeline.py`
- **Traces To:** spec.md → Story 6, FR7
- **Quality Gate:**
  - Pipeline processes research → blog
  - Handles batch processing
  - Error recovery implemented
- **Status:** [ ] Not Started

### T031: Post Generation Pipeline
- **Description:** Implement pipeline that generates short-form content from blog posts
- **Dependencies:** T026, T021
- **Effort:** 3 hours
- **Files:**
  - `src/lib/pipelines/post_generation_pipeline.py`
- **Traces To:** spec.md → FR7
- **Quality Gate:**
  - Pipeline generates short-form content
  - Processes multiple blogs efficiently
- **Status:** [ ] Not Started

### T032: Weekly Report Pipeline
- **Description:** Implement weekly analytics report pipeline
- **Dependencies:** T028, T021
- **Effort:** 4 hours
- **Files:**
  - `src/lib/pipelines/weekly_report_pipeline.py`
- **Traces To:** spec.md → Story 7, FR7
- **Quality Gate:**
  - Pipeline generates weekly reports
  - Includes metrics and recommendations
  - Stores reports properly
- **Status:** [ ] Not Started

### T033: Integration Tests - Pipelines [Test-First]
- **Description:** Write integration tests for all pipelines
- **Dependencies:** T029, T030, T031, T032
- **Effort:** 4 hours
- **Files:**
  - `tests/integration/test_pipelines.py`
- **Test Scenarios:**
  - Test daily research pipeline execution
  - Test blog generation pipeline
  - Test post generation pipeline
  - Test weekly report pipeline
  - Test error handling and recovery
- **Quality Gate:**
  - Tests use real pipelines
  - Tests initially FAIL or PARTIAL PASS
- **Status:** [ ] Not Started

---

## Phase 5: API & CLI (4 days)

### T034: FastAPI Application Setup
- **Description:** Create FastAPI application with main app and route registration
- **Dependencies:** T008, T021
- **Effort:** 2 hours
- **Files:**
  - `src/api/main.py`
  - `src/api/__init__.py`
- **Traces To:** plan.md → Section 7 (API Design)
- **Quality Gate:**
  - FastAPI app starts successfully
  - OpenAPI docs accessible at /docs
  - Error handling middleware configured
- **Status:** [ ] Not Started

### T035: Research API Routes
- **Description:** Create FastAPI routes for research endpoints
- **Dependencies:** T034, T021
- **Effort:** 4 hours
- **Files:**
  - `src/api/routes/research.py`
- **Endpoints:**
  - POST `/api/research/query`
  - GET `/api/research/{query_id}`
  - GET `/api/research/{query_id}/result`
- **Traces To:** plan.md → Section 7 (API Design)
- **Quality Gate:**
  - All endpoints defined with proper status codes
  - Request/response validation using Pydantic schemas
  - OpenAPI docs generated correctly
  - Error responses follow FastAPI standards
- **Status:** [ ] Not Started

### T036: Content API Routes
- **Description:** Create FastAPI routes for content endpoints
- **Dependencies:** T034, T021
- **Effort:** 3 hours
- **Files:**
  - `src/api/routes/content.py`
- **Endpoints:**
  - POST `/api/content/generate-blog`
  - GET `/api/content/{content_id}`
  - GET `/api/content/`
- **Quality Gate:**
  - All endpoints work correctly
  - Pagination implemented
  - OpenAPI docs complete
- **Status:** [ ] Not Started

### T037: Pipeline API Routes
- **Description:** Create FastAPI routes for pipeline endpoints
- **Dependencies:** T034, T029-T032
- **Effort:** 3 hours
- **Files:**
  - `src/api/routes/pipelines.py`
- **Endpoints:**
  - POST `/api/pipelines/daily-research`
  - POST `/api/pipelines/blog-generation`
  - GET `/api/pipelines/{execution_id}`
- **Quality Gate:**
  - Pipeline triggers work
  - Status endpoints return correct data
  - Background task handling implemented
- **Status:** [ ] Not Started

### T038: E2E API Tests [Test-First]
- **Description:** Write end-to-end tests for API endpoints
- **Dependencies:** T035, T036, T037
- **Effort:** 6 hours
- **Files:**
  - `tests/e2e/test_research_flow.py`
  - `tests/e2e/test_blog_generation_flow.py`
  - `tests/e2e/test_api_endpoints.py`
- **Test Scenarios:**
  - Test research query → result flow
  - Test blog generation flow
  - Test pipeline execution via API
  - Test error responses (400, 404, 422, 500, 429, 503)
  - Test edge cases from spec.md
  - Verify Pydantic schema validation
- **Traces To:** spec.md → Acceptance Criteria, Edge Cases
- **Quality Gate:**
  - Tests cover all acceptance criteria
  - Tests verify OpenAPI compliance
  - Tests initially FAIL or PARTIAL PASS
- **Status:** [ ] Not Started

### T039: Research CLI Commands
- **Description:** Create Typer CLI commands for research operations
- **Dependencies:** T021
- **Effort:** 3 hours
- **Files:**
  - `src/cli/research.py`
- **CLI Commands:**
  - `python -m cli.research query "query text" --audience expert`
  - `python -m cli.research status --query-id <id>`
  - `python -m cli.research result --query-id <id>`
- **Traces To:** plan.md → Section 8 (CLI Interface Design)
- **Quality Gate:**
  - All commands work
  - Article II (CLI Mandate) satisfied
  - Async workflows wrapped with asyncio.run()
- **Status:** [ ] Not Started

### T040: Agent CLI Commands
- **Description:** Create Typer CLI commands for direct agent invocation
- **Dependencies:** T011, T013, T015
- **Effort:** 3 hours
- **Files:**
  - `src/cli/agents.py`
- **CLI Commands:**
  - `python -m cli.agents research --query "..." --category core_ai`
  - `python -m cli.agents topic --query "..."`
  - `python -m cli.agents blog-writer --research-id <id> --audience beginner`
- **Quality Gate:**
  - Commands execute agents directly
  - Output formatted correctly
- **Status:** [ ] Not Started

### T041: Pipeline CLI Commands
- **Description:** Create Typer CLI commands for pipeline execution
- **Dependencies:** T029-T032
- **Effort:** 2 hours
- **Files:**
  - `src/cli/pipelines.py`
- **CLI Commands:**
  - `python -m cli.pipelines daily-research`
  - `python -m cli.pipelines blog-generation --research-id <id>`
  - `python -m cli.pipelines weekly-report`
- **Quality Gate:**
  - Pipelines execute via CLI
  - Progress feedback provided
- **Status:** [ ] Not Started

### T042: CLI Tests
- **Description:** Write tests for CLI commands
- **Dependencies:** T039, T040, T041
- **Effort:** 3 hours
- **Files:**
  - `tests/cli/test_research_cli.py`
  - `tests/cli/test_agents_cli.py`
  - `tests/cli/test_pipelines_cli.py`
- **Quality Gate:**
  - CLI commands tested
  - Tests pass
- **Status:** [ ] Not Started

---

## Phase 6: Polish & Optimization (3 days)

### T043: Error Handling & Edge Cases
- **Description:** Implement comprehensive error handling for all edge cases from spec.md
- **Dependencies:** T038 (all endpoints implemented)
- **Effort:** 6 hours
- **Files:**
  - All implementation files (agents, services, routes)
  - `src/lib/models/exceptions.py` (enhance)
- **Traces To:** spec.md → Section 7 (Edge Cases & Error Scenarios)
- **Edge Cases to Handle:**
  - Ambiguous queries → request clarification
  - API failures → use cached data or alternative sources
  - Rate limits → queue and retry with backoff
  - Categorization failure → default to practical
  - Insufficient research data → flag and request more
  - Missing audience → default to practitioner
  - Blog length limits → split or summarize
  - Formula rendering → alternative notation
  - Code validation failures → flag for review
  - Pipeline interruption → checkpoint/resume
  - API auth failures → log and continue
  - Limited source availability → proceed with available data
  - Non-AI topics → detect and reject/confirm
  - Missing voice.json → default professional tone
  - Concurrent query limits → queue requests
- **Quality Gate:**
  - All edge cases handled
  - Error responses are user-friendly
  - Comprehensive logging in place
- **Status:** [ ] Not Started

### T044: Rate Limiting & Retry Logic
- **Description:** Implement rate limiting for LLM API and retry logic for external APIs
- **Dependencies:** T004, T009
- **Effort:** 4 hours
- **Files:**
  - `src/lib/llm/rate_limiter.py`
  - `src/lib/services/retry_handler.py`
- **Traces To:** plan.md → Section 13 (Performance Considerations)
- **Quality Gate:**
  - Rate limiting prevents API overuse
  - Retry logic with exponential backoff works
  - Cost monitoring in place
- **Status:** [ ] Not Started

### T045: Performance Optimization
- **Description:** Optimize database queries, add caching, and improve async execution
- **Dependencies:** T017, T021
- **Effort:** 5 hours
- **Files:**
  - Database query optimization
  - Caching layer (if needed)
  - Async execution improvements
- **Traces To:** plan.md → Section 13 (Performance Considerations), spec.md → Section 5 (Performance Requirements)
- **Optimizations:**
  - Database indexing (status, created_at, foreign keys)
  - Query optimization (eager loading, pagination)
  - Connection pooling
  - Parallel agent execution where possible
  - Concurrent external API calls
- **Tests:**
  - Response time < 2s (categorization)
  - Research < 5 minutes
  - Blog generation < 3 minutes
  - Throughput: 10 concurrent queries
- **Quality Gate:**
  - All performance metrics met
  - No N+1 query issues
  - Database queries optimized
- **Status:** [ ] Not Started

### T046: Content Formatting & Validation
- **Description:** Implement content formatting utilities and validation checks
- **Dependencies:** T015, T026
- **Effort:** 3 hours
- **Files:**
  - `src/utils/formatting.py`
  - `src/lib/agents/content_validator.py`
- **Traces To:** spec.md → FR11 (Output Formatting)
- **Quality Gate:**
  - Code examples syntax-highlighted
  - Citations properly formatted
  - Links validated
  - Medium formatting checks pass
- **Status:** [ ] Not Started

### T047: Documentation
- **Description:** Create comprehensive documentation including API docs, CLI usage, and setup guide
- **Dependencies:** All previous tasks
- **Effort:** 4 hours
- **Files:**
  - `specs/ai-research-agent-system/README.md`
  - `README.md` (project root)
  - API documentation (auto-generated by FastAPI)
- **Quality Gate:**
  - API docs complete (FastAPI auto-generated)
  - CLI usage documented with examples
  - Setup instructions clear
  - Architecture documented
- **Status:** [ ] Not Started

### T048: Final Testing & Bug Fixes
- **Description:** Run comprehensive test suite, fix bugs, and verify all acceptance criteria
- **Dependencies:** All previous tasks
- **Effort:** 6 hours
- **Activities:**
  - Run all test suites (unit, integration, e2e)
  - Fix failing tests
  - Verify all acceptance criteria from spec.md
  - Performance testing
  - Security review
- **Quality Gate:**
  - All tests passing
  - All acceptance criteria met
  - Performance requirements satisfied
  - No critical bugs
- **Status:** [ ] Not Started

---

## Task Execution Guidelines

### Test-First Workflow:
1. Write tests first (they should FAIL)
2. Implement code to make tests PASS
3. Refactor if needed (tests should still PASS)

### Parallelization:
Tasks marked with [P] can be worked on in parallel.

### Quality Checklist:
- [ ] All SDD constitutional principles followed
- [ ] No abstraction layers without proven need
- [ ] Integration tests use real services (no mocks for databases/external APIs)
- [ ] CLI interface complete (Article II)
- [ ] All acceptance criteria from spec.md met
- [ ] Performance requirements satisfied (< 5 min research, < 3 min blog)
- [ ] **LangGraph workflows are async** (`async def` for node functions)
- [ ] **CLI commands use `asyncio.run()`** to execute async workflows
- [ ] **FastAPI endpoints are async** and await LangGraph execution
- [ ] Error handling comprehensive (all edge cases from spec.md)
- [ ] Rate limiting implemented
- [ ] Cost monitoring in place

### Critical Patterns:
- **LangGraph Workflows:** Use `async def` for node functions
- **CLI Entry Points:** Use `def cli_command(...): return asyncio.run(async_workflow(...))`
- **FastAPI Endpoints:** Use `async def endpoint(...): return await graph.ainvoke(...)`
- **Background Tasks:** Use FastAPI BackgroundTasks or sync Celery tasks with `asyncio.run()` wrapper

---

## Progress Tracking

**Phase 1: Foundation & Infrastructure** - 8/8 tasks complete (100%) ✅
- T001: Project Structure [P] ✅
- T002: Database Schema [P] ✅
- T003: Alembic Migration [P] ✅
- T004: AWS Bedrock LLM [P] ✅
- T005: Prompt Templates [P] ✅
- T006: Config & Logging [P] ✅
- T007: Integration Tests - Models [Test-First] ✅
- T008: Pydantic Schemas [P] ✅

**Phase 2: Core Agents** - 10/10 tasks complete (100%) ✅
- T009: External Service Clients [P] ✅ (incl. Tavily)
- T010: Unit Tests - Services [Test-First] ✅
- T011: Topic Agent ✅
- T012: Unit Tests - Topic Agent [Test-First] ✅
- T013: Research Agent ✅
- T014: Unit Tests - Research Agent [Test-First] ✅
- T015: Blog Writer Agent ✅
- T016: Unit Tests - Blog Writer [Test-First] ✅
- T017: Repository Layer ✅
- T018: Integration Tests - Workflows [Test-First] ✅

**Phase 3: Orchestration & Workflows** - 5/5 tasks complete (100%) ✅
- T019: Router ✅
- T020: Unit Tests - Router [Test-First] ✅
- T021: Workflow Manager ✅
- T022: Integration Tests - Workflows [Test-First] ✅
- T023: State Management ✅

**Phase 4: Additional Agents & Pipelines** - 6/10 tasks complete (60%)
- T024: Branding Agent ✅
- T025: Unit Tests - Branding [Test-First]
- T026: Short-form Agent ✅
- T027: Distribution Agent
- T028: Analytics Agent
- T029: Daily Research Pipeline ✅
- T030: Blog Generation Pipeline ✅
- T031: Post Generation Pipeline
- T032: Weekly Report Pipeline
- T033: Integration Tests - Pipelines [Test-First]

**Phase 5: API & CLI** - 7/9 tasks complete (78%)
- T034: FastAPI App Setup ✅
- T035: Research API Routes ✅
- T036: Content API Routes ✅
- T037: Pipeline API Routes ✅
- T038: E2E API Tests [Test-First]
- T039: Research CLI Commands ✅
- T040: Agent CLI Commands ✅
- T041: Pipeline CLI Commands ✅
- T042: CLI Tests

**Phase 6: Polish & Optimization** - 5/6 tasks complete (83%)
- T043: Error Handling & Edge Cases ✅
- T044: Rate Limiting & Retry Logic ✅
- T045: Performance Optimization ✅
- T046: Content Formatting & Validation ✅
- T047: Documentation
- T048: Final Testing & Bug Fixes ✅

**Overall:** 45/48 tasks complete (94%)

---

## Package Management

**Important:** This project uses `uv` as package manager (NOT `pip` or `poetry`)

**Commands:**
```bash
# Initialize project
uv init

# Add dependencies
uv add <package>

# Sync environment
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run tests
pytest

# Run application
python -m src.api.main
```

**Key Dependencies (from plan.md):**
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
**Status:** Ready for Execution

