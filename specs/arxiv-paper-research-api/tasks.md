# Task Breakdown: ArXiv Paper Research & Blog Generation API

**Total Estimated Effort:** 8-10 development days  
**Test-First Approach:** All tests written before implementation  
**Phases:** 4 main phases + 1 optional database extension phase

---

## Phase 1: Foundation & Setup (2 days)

### T001: ArXiv ID Parser Service [P]
- **Description:** Create service to parse and validate ArXiv paper IDs in multiple formats
- **Dependencies:** None
- **Effort:** 3 hours
- **Files:**
  - `src/lib/services/arxiv_id_parser.py`
- **Implementation Details:**
  - Parse formats: `2508.07407`, `arxiv:2508.07407`, `arXiv:2508.07407v2`, full URLs
  - Normalize to standard format: `2508.07407` (with optional version)
  - Validate using regex pattern: `\d{4}\.\d{4,5}(v\d+)?`
  - Extract version number if present
- **Quality Gate:**
  - Parser handles all input formats from spec
  - Invalid IDs raise `InvalidArXivIdError`
- **Traces To:** spec.md → FR1, Story 1
- **Status:** [ ] Not Started

---

### T002: Unit Tests - ArXiv ID Parser [Test-First]
- **Description:** Write unit tests for ArXiv ID parsing and validation
- **Dependencies:** T001 (interface defined)
- **Effort:** 2 hours
- **Files:**
  - `tests/unit/test_arxiv_id_parser.py`
- **Test Scenarios:**
  - `test_parse_simple_id` - "2508.07407" → normalized ID
  - `test_parse_with_prefix` - "arxiv:2508.07407" → normalized ID
  - `test_parse_with_version` - "2508.07407v2" → ID with version
  - `test_parse_full_url` - "https://arxiv.org/abs/2508.07407" → normalized ID
  - `test_parse_pdf_url` - "https://arxiv.org/pdf/2508.07407.pdf" → normalized ID
  - `test_invalid_format` - "abc123" → raises `InvalidArXivIdError`
  - `test_empty_string` - "" → raises `InvalidArXivIdError`
  - `test_extract_version` - "2508.07407v3" → version=3
  - `test_case_insensitive` - "ArXiv:2508.07407" → normalized ID
- **Quality Gate:**
  - Tests FAIL initially (no implementation)
  - 100% coverage of parser functions
- **Status:** [ ] Not Started

---

### T003: Paper-Specific Prompts [P]
- **Description:** Create specialized prompts for paper research and blog generation
- **Dependencies:** None
- **Effort:** 4 hours
- **Files:**
  - `src/lib/llm/prompts/paper_research.txt`
  - `src/lib/llm/prompts/paper_blog.txt`
- **Implementation Details:**
  - Research prompt includes: paper overview, methodology, results, implications, limitations, related work
  - Blog prompt includes: hook, citation, problem, solution, findings, conclusion
  - Prompts request JSON output for parsing
  - Include audience-specific guidelines placeholders
- **Quality Gate:**
  - Prompts can be loaded via existing `load_prompt()` function
  - Prompts produce valid JSON structure when tested
- **Traces To:** spec.md → FR3, FR4, FR5, FR9
- **Status:** [ ] Not Started

---

### T004: Pydantic Schemas for Paper Research [P]
- **Description:** Define request/response schemas for paper research API
- **Dependencies:** None
- **Effort:** 3 hours
- **Files:**
  - `src/lib/models/schemas.py` (extend existing)
- **Schemas to Create:**
  - `ArXivPaperInput` - accepts arxiv_id OR title_search
  - `PaperResearchRequest` - full request with audience, generate_blog flag
  - `PaperMetadata` - paper info from ArXiv
  - `EnhancedResearchResult` - research with enhanced sections
  - `PaperResearchResponse` - async response with research_id
  - `PaperFullResponse` - research + blog combined
  - `PaperSearchRequest` - title search request
  - `PaperBlogRequest` - blog generation from research
- **Quality Gate:**
  - All schemas validate correctly
  - Field validators handle edge cases
  - Schemas documented with descriptions and examples
- **Traces To:** plan.md → Section 6.1
- **Status:** [ ] Not Started

---

### T005: Custom Exceptions for Paper Operations [P]
- **Description:** Define custom exceptions for paper research error handling
- **Dependencies:** None
- **Effort:** 1 hour
- **Files:**
  - `src/lib/models/exceptions.py` (extend existing)
- **Exceptions to Create:**
  - `ArXivPaperError` - base exception
  - `InvalidArXivIdError` - invalid ID format
  - `PaperNotFoundError` - paper doesn't exist on ArXiv
  - `PaperContentInsufficientError` - abstract too short
  - `MultiplePapersLimitError` - too many papers requested
- **Quality Gate:**
  - All exceptions include helpful error messages
  - Exceptions can be serialized for API responses
- **Traces To:** spec.md → FR10, Edge Cases
- **Status:** [ ] Not Started

---

### T006: Implement ArXiv ID Parser
- **Description:** Implement the parser to make unit tests pass
- **Dependencies:** T002 (tests must exist first)
- **Effort:** 2 hours
- **Files:**
  - `src/lib/services/arxiv_id_parser.py`
- **Quality Gate:**
  - Unit tests (T002) now PASS
  - All ID formats correctly parsed
- **Status:** [ ] Not Started

---

## Phase 2: Core Agent Implementation (3 days)

### T007: Enhanced Research Output Dataclass
- **Description:** Create dataclass for enhanced paper research output
- **Dependencies:** T004 (schemas)
- **Effort:** 2 hours
- **Files:**
  - `src/lib/agents/arxiv_paper_research_agent.py` (output classes)
- **Classes to Create:**
  - `PaperResearchOutput` - dataclass with all enhanced sections
  - Mirror `EnhancedResearchResult` schema structure
  - Include `paper_metadata`, `completeness_score`, `research_data_path`
- **Quality Gate:**
  - Dataclass can be converted to Pydantic schema
  - All fields match spec requirements
- **Traces To:** spec.md → FR3
- **Status:** [ ] Not Started

---

### T008: Unit Tests - Paper Research Agent [Test-First]
- **Description:** Write unit tests for the paper research agent
- **Dependencies:** T007, T003
- **Effort:** 4 hours
- **Files:**
  - `tests/unit/test_arxiv_paper_research_agent.py`
- **Test Scenarios:**
  - `test_build_research_context` - paper metadata → research context string
  - `test_parse_research_output` - LLM response → PaperResearchOutput
  - `test_calculate_completeness_score` - output → score 0-1
  - `test_generate_citation` - metadata → academic citation format
  - `test_validate_paper_content` - abstract < 100 words → raises error
  - `test_enhanced_sections_present` - output has all 7 enhanced sections
  - `test_format_for_blog` - research output → blog input format
- **Quality Gate:**
  - Tests FAIL initially
  - Tests cover all agent methods
- **Status:** [ ] Not Started

---

### T009: ArXiv Paper Research Agent - Core
- **Description:** Implement the main paper research agent
- **Dependencies:** T006, T003, T005, T007
- **Effort:** 8 hours
- **Files:**
  - `src/lib/agents/arxiv_paper_research_agent.py`
- **Implementation Details:**
  - Initialize with `BedrockLLM`, `ArXivClient`
  - `research_paper_by_id(arxiv_id, target_audience)` - main method
  - `research_paper_by_title(title, target_audience)` - search + research
  - `_fetch_paper_metadata(arxiv_id)` - use ArXivClient
  - `_build_research_context(metadata)` - format for prompt
  - `_conduct_paper_research(context, audience)` - LLM call with paper prompt
  - `_parse_research_output(llm_response)` - extract structured output
  - `_calculate_completeness(output)` - score based on sections present
- **Quality Gate:**
  - Unit tests (T008) now PASS
  - Agent can be imported standalone
- **Traces To:** spec.md → Story 1, Story 4, Story 5, FR3, FR4
- **Status:** [ ] Not Started

---

### T010: Integration Tests - Paper Research Workflow [Test-First]
- **Description:** Write integration tests for full paper research workflow
- **Dependencies:** T009
- **Effort:** 4 hours
- **Files:**
  - `tests/integration/test_paper_research_workflow.py`
  - `tests/conftest.py` (add fixtures)
- **Test Scenarios:**
  - `test_research_known_paper` - "1706.03762" (Attention paper) → valid research
  - `test_research_by_title_search` - "attention is all you need" → finds paper
  - `test_paper_not_found` - "9999.99999" → raises PaperNotFoundError
  - `test_research_completeness_score` - output.completeness_score > 0.8
  - `test_enhanced_sections_populated` - all 7 sections have content
  - `test_paper_metadata_extracted` - title, authors, abstract present
  - `test_citation_format` - citation matches academic format
  - `test_rate_limiting_respected` - multiple calls don't exceed rate limit
- **Note:** Uses real ArXiv API and LLM (rate-limited)
- **Quality Gate:**
  - Tests FAIL initially
  - Tests cover full workflow
- **Status:** [ ] Not Started

---

### T011: Blog Generation from Paper Research
- **Description:** Implement blog generation specifically for paper research
- **Dependencies:** T009
- **Effort:** 4 hours
- **Files:**
  - `src/lib/agents/arxiv_paper_research_agent.py` (extend)
- **Implementation Details:**
  - `generate_blog_from_research(research_output, target_audience)` method
  - Use existing `BlogWriterAgent` with paper-specific prompt
  - Include paper citation in blog
  - Format research output for blog prompt
- **Quality Gate:**
  - Blog includes proper paper citation
  - Blog follows structure from spec
- **Traces To:** spec.md → Story 3, FR5
- **Status:** [ ] Not Started

---

### T012: Multiple Paper Research Support
- **Description:** Implement support for researching multiple papers
- **Dependencies:** T009
- **Effort:** 4 hours
- **Files:**
  - `src/lib/agents/arxiv_paper_research_agent.py` (extend)
- **Implementation Details:**
  - `research_multiple_papers(arxiv_ids, target_audience)` method
  - Validate max 5 papers per request
  - Fetch all papers in parallel (respecting rate limits)
  - Synthesize findings across papers
  - Identify common themes and differences
- **Quality Gate:**
  - Handles 1-5 papers correctly
  - Raises `MultiplePapersLimitError` for > 5 papers
- **Traces To:** spec.md → Story 7, FR6
- **Status:** [ ] Not Started

---

### T013: Paper Research Pipeline
- **Description:** Create pipeline for full paper research + blog workflow
- **Dependencies:** T009, T011
- **Effort:** 3 hours
- **Files:**
  - `src/lib/pipelines/paper_research_pipeline.py`
- **Implementation Details:**
  - `PaperResearchPipeline` class
  - `execute(arxiv_id, target_audience, generate_blog)` method
  - `execute_from_search(title, target_audience, generate_blog)` method
  - Orchestrates: fetch → research → blog (optional)
  - Saves results to database and file system
- **Quality Gate:**
  - Pipeline can be used standalone
  - Results saved correctly
- **Traces To:** spec.md → FR7
- **Status:** [ ] Not Started

---

## Phase 3: API & CLI Implementation (2 days)

### T014: FastAPI Routes - Paper Research
- **Description:** Create FastAPI router with all paper research endpoints
- **Dependencies:** T009, T013, T004
- **Effort:** 4 hours
- **Files:**
  - `src/api/routes/paper.py`
- **Endpoints to Implement:**
  - `POST /research` - async paper research
  - `POST /research/sync` - sync paper research
  - `GET /research/{id}` - get research status
  - `GET /research/{id}/result` - get research result
  - `POST /blog` - generate blog from research
  - `POST /full` - research + blog async
  - `POST /full/sync` - research + blog sync
  - `POST /search` - search papers by title
  - `GET /metadata/{arxiv_id}` - get paper metadata only
- **Quality Gate:**
  - All endpoints return correct status codes
  - Request/response validation using Pydantic schemas
- **Traces To:** plan.md → Section 7 (API Design)
- **Status:** [ ] Not Started

---

### T015: Register Paper Routes in FastAPI App
- **Description:** Register paper routes in main FastAPI application
- **Dependencies:** T014
- **Effort:** 30 minutes
- **Files:**
  - `src/api/main.py`
- **Implementation:**
  - Import paper router
  - Add: `app.include_router(paper.router, prefix="/api/v1/paper", tags=["Paper Research"])`
- **Quality Gate:**
  - Routes visible in `/docs`
  - No conflicts with existing routes
- **Status:** [ ] Not Started

---

### T016: E2E Tests - Paper API [Test-First]
- **Description:** Write end-to-end tests for paper API endpoints
- **Dependencies:** T014, T015
- **Effort:** 4 hours
- **Files:**
  - `tests/e2e/test_paper_api.py`
- **Test Scenarios:**
  - `test_research_paper_sync` - POST /research/sync → 200 + result
  - `test_research_paper_async` - POST /research → 202 + research_id
  - `test_get_research_status` - GET /research/{id} → 200 + status
  - `test_get_research_result` - GET /research/{id}/result → 200 + result
  - `test_full_sync` - POST /full/sync → 200 + research + blog
  - `test_search_papers` - POST /search → 200 + list
  - `test_get_paper_metadata` - GET /metadata/{id} → 200 + metadata
  - `test_invalid_arxiv_id` - POST with invalid ID → 400
  - `test_paper_not_found` - POST with non-existent ID → 404
  - `test_validation_error` - POST with missing fields → 422
- **Quality Gate:**
  - Tests FAIL initially
  - Cover all acceptance criteria
- **Traces To:** spec.md → Acceptance Criteria, Edge Cases
- **Status:** [ ] Not Started

---

### T017: Implement API Endpoints
- **Description:** Complete API implementation to make E2E tests pass
- **Dependencies:** T016 (tests must exist first)
- **Effort:** 3 hours
- **Files:**
  - `src/api/routes/paper.py`
- **Quality Gate:**
  - E2E tests (T016) now PASS
  - OpenAPI docs complete at `/docs`
- **Status:** [ ] Not Started

---

### T018: CLI Commands - Paper Research
- **Description:** Create Typer CLI commands for paper research
- **Dependencies:** T009, T013
- **Effort:** 4 hours
- **Files:**
  - `src/cli/commands/paper.py`
- **Commands to Implement:**
  - `research --arxiv-id ID [--title TITLE] --audience AUDIENCE [--output FILE]`
  - `full --arxiv-id ID --audience AUDIENCE [--output FILE]`
  - `search --query QUERY --limit N`
  - `info --arxiv-id ID`
  - `multi-research --arxiv-ids ID1,ID2 --audience AUDIENCE`
- **Quality Gate:**
  - All commands work correctly
  - Rich output for progress and results
- **Traces To:** plan.md → Section 8 (CLI Interface Design)
- **Status:** [ ] Not Started

---

### T019: Register CLI Commands
- **Description:** Register paper commands in main CLI application
- **Dependencies:** T018
- **Effort:** 30 minutes
- **Files:**
  - `src/cli/main.py`
- **Implementation:**
  - Import paper CLI app
  - Add: `app.add_typer(paper.app, name="paper", help="ArXiv paper research commands")`
- **Quality Gate:**
  - Commands visible in `--help`
  - No conflicts with existing commands
- **Status:** [ ] Not Started

---

### T020: CLI Tests
- **Description:** Write tests for CLI commands
- **Dependencies:** T018, T019
- **Effort:** 2 hours
- **Files:**
  - `tests/cli/test_paper_cli.py`
- **Test Scenarios:**
  - `test_research_with_arxiv_id` - valid ID → success
  - `test_research_with_title` - valid title → success
  - `test_research_missing_input` - no ID or title → error
  - `test_full_command` - valid ID → research + blog
  - `test_search_command` - query → list of papers
  - `test_info_command` - ID → paper metadata
- **Quality Gate:**
  - CLI commands tested
  - Tests pass
- **Status:** [ ] Not Started

---

## Phase 4: Polish & Validation (1 day)

### T021: Error Handling & Edge Cases
- **Description:** Implement comprehensive error handling for all edge cases
- **Dependencies:** T017, T019
- **Effort:** 3 hours
- **Files:**
  - `src/api/routes/paper.py`
  - `src/cli/commands/paper.py`
  - `src/lib/agents/arxiv_paper_research_agent.py`
- **Edge Cases to Handle:**
  - Invalid ArXiv ID format → 400 with examples
  - Paper not found → 404 with clear message
  - ArXiv API rate limited → 429 with retry-after
  - ArXiv API unavailable → 503 with message
  - Abstract too short → warning, proceed with available data
  - LLM output parsing failure → retry with simplified prompt
  - Multiple papers > 5 → 400 with limit explanation
- **Quality Gate:**
  - All edge cases from spec.md handled
  - Error messages are user-friendly
- **Traces To:** spec.md → Section 7 (Edge Cases)
- **Status:** [ ] Not Started

---

### T022: Performance Validation
- **Description:** Validate performance requirements from spec
- **Dependencies:** T017
- **Effort:** 2 hours
- **Files:**
  - `tests/performance/test_paper_performance.py` (new)
- **Tests:**
  - Paper metadata retrieval < 3 seconds
  - Full research generation < 8 minutes
  - Blog generation < 3 minutes
  - API async response < 500ms
- **Quality Gate:**
  - All performance metrics met
  - No timeouts under normal load
- **Traces To:** spec.md → Section 5 (Performance Requirements)
- **Status:** [ ] Not Started

---

### T023: Integration Tests - Full Workflow
- **Description:** Final integration tests for complete workflow
- **Dependencies:** T017, T019, T021
- **Effort:** 3 hours
- **Files:**
  - `tests/integration/test_paper_research_workflow.py` (extend)
- **Test Scenarios:**
  - Full API workflow: POST /full/sync → complete response
  - Full CLI workflow: `paper full --arxiv-id X` → success
  - Database persistence: research saved correctly
  - File storage: blog saved to correct location
  - Error recovery: partial failures handled gracefully
- **Quality Gate:**
  - All integration tests pass
  - Complete workflow verified
- **Status:** [ ] Not Started

---

### T024: Documentation Update
- **Description:** Update API documentation and create usage examples
- **Dependencies:** T023
- **Effort:** 2 hours
- **Files:**
  - `specs/arxiv-paper-research-api/README.md` (new)
  - `README.md` (update if needed)
- **Content:**
  - API usage examples
  - CLI usage examples
  - Configuration notes
  - Troubleshooting guide
- **Quality Gate:**
  - Documentation complete
  - Examples tested and working
- **Status:** [ ] Not Started

---

## Phase 5: Database Extension (1 day, optional)

### T025: Database Model for Paper Research
- **Description:** Create SQLAlchemy model for paper-specific data
- **Dependencies:** T023 (only if dedicated storage needed)
- **Effort:** 2 hours
- **Files:**
  - `src/lib/models/paper.py`
- **Model:** `PaperResearch` with all enhanced fields
- **Quality Gate:**
  - Model can be imported
  - Relationships defined correctly
- **Status:** [ ] Not Started

---

### T026: Alembic Migration
- **Description:** Create database migration for paper_research table
- **Dependencies:** T025
- **Effort:** 1 hour
- **Files:**
  - `alembic/versions/xxx_add_paper_research_table.py`
- **Quality Gate:**
  - Migration runs successfully (up and down)
  - Indexes created on arxiv_id
- **Status:** [ ] Not Started

---

### T027: Update Repository Layer
- **Description:** Add repository methods for paper research
- **Dependencies:** T026
- **Effort:** 2 hours
- **Files:**
  - `src/lib/services/paper_repository.py` (new)
- **Methods:**
  - `create_paper_research()`
  - `get_paper_research_by_id()`
  - `get_paper_research_by_arxiv_id()`
  - `list_paper_research()`
- **Quality Gate:**
  - Repository methods work correctly
  - Integration tests pass
- **Status:** [ ] Not Started

---

## Task Execution Guidelines

### Test-First Workflow:
1. Write tests first (they should FAIL)
2. Implement code to make tests PASS
3. Refactor if needed (tests should still PASS)

### Parallelization:
Tasks marked with [P] can be worked on in parallel:
- T001, T003, T004, T005 can all be done in parallel
- T007, T008 can be started while T006 is in progress

### Dependency Graph:

```
Phase 1:
T001 ──┬──> T002 ──> T006
       │
T003 ──┼──> (used by T009)
       │
T004 ──┼──> T007
       │
T005 ──┘

Phase 2:
T006 ──┬──> T009 ──┬──> T010
T007 ──┤          │
T003 ──┘          ├──> T011 ──> T013
                  │
                  └──> T012

Phase 3:
T009 ──┬──> T014 ──> T015 ──> T016 ──> T017
T013 ──┤
T004 ──┘
       
T009 ──┬──> T018 ──> T019 ──> T020
T013 ──┘

Phase 4:
T017 ──┬──> T021
T019 ──┘
T017 ──> T022
T021 ──> T023 ──> T024

Phase 5 (optional):
T023 ──> T025 ──> T026 ──> T027
```

### Quality Checklist:

- [ ] All SDD constitutional principles followed
- [ ] Library-first architecture maintained (agent usable without API)
- [ ] CLI interface complete (Article II)
- [ ] Tests written before implementation (Article III)
- [ ] No abstraction layers without proven need (Article VIII)
- [ ] Integration tests use real services (Article IX)
- [ ] All acceptance criteria from spec.md met
- [ ] Performance requirements satisfied (< 8 min research)
- [ ] Error handling comprehensive (all edge cases)
- [ ] Async pattern correct (async def for FastAPI, asyncio.run() for CLI)

---

## Progress Tracking

| Phase | Tasks | Completed | Progress |
|-------|-------|-----------|----------|
| Phase 1: Foundation | 6 | 0 | 0% |
| Phase 2: Core Agent | 7 | 0 | 0% |
| Phase 3: API & CLI | 7 | 0 | 0% |
| Phase 4: Polish | 4 | 0 | 0% |
| Phase 5: Database (opt) | 3 | 0 | 0% |

**Overall Progress:** 0/27 tasks complete (0%)

---

## Summary by File

| File | Tasks | Description |
|------|-------|-------------|
| `src/lib/services/arxiv_id_parser.py` | T001, T006 | ArXiv ID parsing/validation |
| `src/lib/llm/prompts/paper_research.txt` | T003 | Paper research prompt |
| `src/lib/llm/prompts/paper_blog.txt` | T003 | Paper blog prompt |
| `src/lib/models/schemas.py` | T004 | Pydantic schemas (extend) |
| `src/lib/models/exceptions.py` | T005 | Custom exceptions (extend) |
| `src/lib/agents/arxiv_paper_research_agent.py` | T007, T009, T011, T012 | Main agent |
| `src/lib/pipelines/paper_research_pipeline.py` | T013 | Research pipeline |
| `src/api/routes/paper.py` | T014, T017 | API routes |
| `src/api/main.py` | T015 | Register routes |
| `src/cli/commands/paper.py` | T018 | CLI commands |
| `src/cli/main.py` | T019 | Register CLI |
| `tests/unit/test_arxiv_id_parser.py` | T002 | Parser tests |
| `tests/unit/test_arxiv_paper_research_agent.py` | T008 | Agent tests |
| `tests/integration/test_paper_research_workflow.py` | T010, T023 | Integration tests |
| `tests/e2e/test_paper_api.py` | T016 | API tests |
| `tests/cli/test_paper_cli.py` | T020 | CLI tests |

---

## Estimated Timeline

| Day | Tasks | Focus |
|-----|-------|-------|
| Day 1 | T001-T006 | Foundation: Parser, prompts, schemas, exceptions |
| Day 2 | T007-T009 | Core agent implementation |
| Day 3 | T010-T012 | Integration tests, blog generation, multi-paper |
| Day 4 | T013-T015 | Pipeline, API routes |
| Day 5 | T016-T017 | E2E tests, API completion |
| Day 6 | T018-T020 | CLI commands and tests |
| Day 7 | T021-T023 | Error handling, performance, integration tests |
| Day 8 | T024 | Documentation |
| Day 9-10 | T025-T027 | (Optional) Database extension |

---

**Package Management:**
- Use `uv add <package>` to add dependencies (NOT `pip install` or `poetry add`)
- Virtual environment: `.venv` (managed by uv)
- Always activate: `source .venv/bin/activate` before running commands
- No new dependencies required for this feature

---

**Document Version:** 1.0  
**Last Updated:** December 7, 2025  
**Status:** Ready for Execution

**Next Steps:**
1. Start with T001-T006 (Foundation tasks - can be parallelized)
2. Write tests first per Article III
3. Update this document as tasks complete

