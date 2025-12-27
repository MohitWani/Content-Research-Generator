You are a project delivery engineer. Read the `plan.md` for the feature and create an executable task breakdown.

**Package Management:**
- This project uses `uv` as package manager (not pip or poetry)
- To add dependencies: `uv add <package>`
- Virtual environment: `.venv` (managed by uv)

**Output Structure:**

# Task Breakdown: <Feature Name>

**Total Estimated Effort:** X development days
**Test-First Approach:** All tests written before implementation

---

## Phase 1: Foundation & Setup

### T001: Database Schema & Models [P]
- **Description:** Create SQLAlchemy models and Alembic migration for <feature> tables
- **Dependencies:** None
- **Effort:** X hours
- **Files:**
  - `src/lib/<feature>/models.py`
  - `alembic/versions/xxx_create_<feature>_tables.py`
- **Quality Gate:** 
  - Migration runs successfully
  - Models can be imported
- **Status:** [ ] Not Started

### T002: Repository Layer [P]
- **Description:** Implement data access layer with CRUD operations
- **Dependencies:** T001
- **Effort:** X hours
- **Files:**
  - `src/lib/<feature>/repository.py`
- **Quality Gate:**
  - Repository methods defined
  - Ready for integration testing
- **Status:** [ ] Not Started

### T003: Integration Tests - Repository [Test-First]
- **Description:** Write integration tests for repository using real PostgreSQL
- **Dependencies:** T002
- **Effort:** X hours
- **Files:**
  - `tests/integration/test_<feature>_repository.py`
  - `tests/conftest.py` (fixtures)
- **Test Scenarios:**
  - Test create operation
  - Test read operation
  - Test update operation
  - Test delete operation
  - Test error handling
- **Quality Gate:**
  - All tests FAIL (no implementation yet)
  - Tests are comprehensive
- **Status:** [ ] Not Started

### T004: Pydantic Schemas [P]
- **Description:** Define request/response schemas for API (serves as API contract)
- **Dependencies:** T001
- **Effort:** X hours
- **Files:**
  - `src/lib/<feature>/schemas.py`
- **Quality Gate:**
  - Schemas validate correctly
  - Include field validators and descriptions
  - Cover all CRUD operations
  - FastAPI will auto-generate OpenAPI docs from these
- **Traces To:** spec.md → Functional Requirements
- **Status:** [ ] Not Started

---

## Phase 2: Core Implementation

### T005: Service Layer - Business Logic
- **Description:** Implement core business logic in service layer
- **Dependencies:** T001, T002, T004
- **Effort:** X hours
- **Files:**
  - `src/lib/<feature>/service.py`
  - `src/lib/<feature>/exceptions.py`
- **Traces To:** spec.md → User Story 1, 2
- **Quality Gate:**
  - Service methods implement all business rules
  - Error handling in place
- **Status:** [ ] Not Started

### T006: Unit Tests - Service Layer [Test-First]
- **Description:** Write unit tests for service layer logic
- **Dependencies:** T005
- **Effort:** X hours
- **Files:**
  - `tests/unit/test_<feature>_service.py`
- **Test Scenarios:**
  - Test business logic scenarios
  - Test validation rules
  - Test exception handling
- **Quality Gate:**
  - Tests cover all service methods
  - Tests initially FAIL
- **Status:** [ ] Not Started

### T007: Implement Repository Layer
- **Description:** Implement the repository methods to make integration tests pass
- **Dependencies:** T003 (tests must exist first)
- **Effort:** X hours
- **Files:**
  - `src/lib/<feature>/repository.py`
- **Quality Gate:**
  - Integration tests (T003) now PASS
  - No test mocking used
- **Status:** [ ] Not Started

### T008: Implement Service Layer
- **Description:** Implement service layer to make unit tests pass
- **Dependencies:** T006 (tests must exist first), T007
- **Effort:** X hours
- **Files:**
  - `src/lib/<feature>/service.py`
- **Quality Gate:**
  - Unit tests (T007) now PASS
  - Business logic complete
- **Status:** [ ] Not Started

### T009: FastAPI Routes
- **Description:** Create FastAPI router with all endpoints (OpenAPI docs auto-generated)
- **Dependencies:** T008
- **Effort:** X hours
- **Files:**
  - `src/api/routes/<feature>.py`
- **Traces To:** plan.md → API Design (Section 7)
- **Quality Gate:**
  - All endpoints defined with proper status codes
  - Request/response validation using Pydantic schemas
  - OpenAPI docs generated correctly (check /docs)
  - Error responses follow FastAPI standards
- **Status:** [ ] Not Started

### T010: E2E API Tests [Test-First]
- **Description:** Write end-to-end tests for API endpoints
- **Dependencies:** T009
- **Effort:** X hours
- **Files:**
  - `tests/e2e/test_<feature>_api.py`
- **Test Scenarios:**
  - Test all happy path scenarios
  - Test error responses (400, 404, 422, 500)
  - Test edge cases from spec.md
  - Verify Pydantic schema validation
- **Traces To:** spec.md → Acceptance Criteria
- **Quality Gate:**
  - Tests cover all acceptance criteria
  - Tests verify OpenAPI compliance
  - Tests initially FAIL
- **Status:** [ ] Not Started

### T011: Implement FastAPI Routes
- **Description:** Complete API implementation to make E2E tests pass
- **Dependencies:** T010 (tests must exist first)
- **Effort:** X hours
- **Files:**
  - `src/api/routes/<feature>.py`
- **Traces To:** plan.md → API Design
- **Quality Gate:**
  - E2E tests (T010) now PASS
  - OpenAPI docs are complete and accurate
  - All acceptance criteria met
- **Status:** [ ] Not Started

---

## Phase 3: CLI & Validation

### T012: CLI Commands (Typer)
- **Description:** Create Typer CLI commands for all operations
- **Dependencies:** T008
- **Effort:** X hours
- **Files:**
  - `src/cli/<feature>.py`
- **CLI Commands:**
  - `create` command
  - `list` command
  - `get` command
  - `update` command
  - `delete` command
- **Traces To:** plan.md → CLI Interface Design
- **Quality Gate:**
  - All commands work
  - Article II (CLI Mandate) satisfied
- **Status:** [ ] Not Started

### T013: CLI Tests
- **Description:** Write tests for CLI commands
- **Dependencies:** T012
- **Effort:** X hours
- **Files:**
  - `tests/cli/test_<feature>_cli.py`
- **Quality Gate:**
  - CLI commands tested
  - Tests pass
- **Status:** [ ] Not Started

### T014: Error Handling & Edge Cases
- **Description:** Implement error handling for all edge cases from spec.md
- **Dependencies:** T011
- **Effort:** X hours
- **Files:**
  - All implementation files
- **Traces To:** spec.md → Section 7 (Edge Cases)
- **Quality Gate:**
  - All edge cases handled
  - Error responses are user-friendly
- **Status:** [ ] Not Started

### T015: Performance Validation
- **Description:** Validate performance requirements from spec.md
- **Dependencies:** T014
- **Effort:** X hours
- **Tests:**
  - Response time < X ms
  - Throughput X requests/second
  - Database query optimization
- **Quality Gate:**
  - All performance metrics met
  - No N+1 query issues
- **Status:** [ ] Not Started

### T016: Documentation
- **Description:** Verify OpenAPI docs and write usage examples
- **Dependencies:** T015
- **Effort:** X hours
- **Files:**
  - `specs/<feature>/README.md`
  - FastAPI auto-generated docs
- **Quality Gate:**
  - API docs complete
  - CLI usage documented
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
- [ ] Integration tests use real services (no mocks)
- [ ] CLI interface complete
- [ ] All acceptance criteria from spec.md met
- [ ] Performance requirements satisfied
- [ ] **If Celery tasks: Must be sync (`def`) with `asyncio.run()` wrapper**
- [ ] **If Celery tasks: Return values are JSON-serializable**

---

## Progress Tracking

**Phase 1:** 0/4 tasks complete (0%)
**Phase 2:** 0/7 tasks complete (0%)
**Phase 3:** 0/5 tasks complete (0%)

**Overall:** 0/16 tasks complete (0%)

---

**Package Management:**
- Use `uv add <package>` to add dependencies (NOT `pip install` or `poetry add`)
- Virtual environment: `.venv` (managed by uv)
- Always activate: `source .venv/bin/activate` before running commands

---

Save as: `specs/<feature_name>/tasks.md`
