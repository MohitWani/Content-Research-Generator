You are a senior Python backend architect. Read the `spec.md` for the feature and create a comprehensive technical implementation plan.

**Technology Stack:**
- Backend: FastAPI (REST API)
- Database: PostgreSQL
- CLI: Typer
- Testing: pytest, pytest-asyncio
- Async: asyncio, httpx
- Cache: Redis (if needed)
- **Package Manager: uv** (use `uv add <package>` instead of `pip install` or `poetry add`)

**Output Structure:**

# Implementation Plan: <Feature Name>

## 1. Executive Summary
- Feature: [Brief technical description]
- Approach: [High-level technical strategy]
- Complexity: [Low/Medium/High]
- Estimated Effort: [X development days]

## 2. SDD Constitutional Gates (Pre-Implementation Checklist)

### ✓ Library-First Principle (Article I)
- [ ] Core logic written as independent service/library modules
- [ ] Can be imported and used without API layer
- [ ] Clear separation: `src/lib/<feature>/`, `src/api/`, `src/cli/`

### ✓ CLI Interface Mandate (Article II)
- [ ] All functionality accessible via Typer CLI commands
- [ ] Format: `python -m cli.<feature> <command> --options`

### ✓ Test-First Command (Article III)
- [ ] Tests written BEFORE implementation
- [ ] Tests should fail first, then pass after implementation
- [ ] pytest test suite prepared

### ✓ Simplicity Mandate (Article VII)
- [ ] Maximum 3 project components (lib, api, cli)
- [ ] No designing for future, only current requirements
- [ ] Complexity justified

### ✓ Anti-Abstraction Principle (Article VIII)
- [ ] Using FastAPI, SQLAlchemy, Typer DIRECTLY (no wrappers)
- [ ] No premature abstractions
- [ ] Single model throughout (no DTO/Entity separation unless proven need)

### ✓ Integration-First Testing (Article IX)
- [ ] Tests use real PostgreSQL (test database)
- [ ] Tests use real Redis (test instance)
- [ ] No mocking of databases/external services in integration tests

### ⚠️ CRITICAL: Celery Async Pattern (Lerned from Implementation)a
- [ ] **Celery tasks MUST be sync functions** (`def`, NOT `async def`)
- [ ] **Use `asyncio.run()` to execute async workflows** inside sync Celery tasks
- [ ] **Pattern:** `def celery_task(...): return asyncio.run(async_workflow(...))`
- [ ] **Why:** Celery doesn't natively support async tasks - it will return coroutine objects that can't be JSON serialized
- [ ] **Error to avoid:** `TypeError: Object of type coroutine is not JSON serializable`
- [ ] **Reference:** See `src/modules/tmap/workers/tasks.py` line 350 for correct pattern

## 3. Technical Architecture

```
┌─────────────────┐
│   FastAPI App   │
│   (REST API)    │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Service │
    │  Layer  │
    └────┬────┘
         │
    ┌────▼────────┐
    │ Repository  │
    │   Layer     │
    └────┬────────┘
         │
    ┌────▼────────┐
    │ PostgreSQL  │
    │  Database   │
    └─────────────┘
```

**⚠️ If using Celery Tasks:**
```
┌─────────────────────┐
│   Celery Task       │
│  @celery_app.task   │
│  def task(...):     │ ← SYNC (not async)
│    asyncio.run(     │
│      async_work()   │
│    )                │
└──────────┬──────────┘
           │
      ┌────▼────────┐
      │ Async Work  │
      │ async def   │
    └─────────────┘
```

**Flow:**
1. [Describe request flow]
2. [Describe data flow]
3. [Describe response flow]
4. **If Celery:** Sync task → asyncio.run() → async workflow → JSON-serializable result

## 4. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API Framework | FastAPI | [Why - maps to requirement] |
| ORM | SQLAlchemy 2.0 | [Why - maps to requirement] |
| Database | PostgreSQL | [Why - maps to requirement] |
| CLI | Typer | [Why - Article II mandate] |

## 5. Directory Structure (Library-First)

```
project_root/
├── src/
│   ├── lib/
│   │   └── <feature_name>/
│   │       ├── __init__.py
│   │       ├── service.py      # Core business logic
│   │       ├── models.py       # SQLAlchemy models
│   │       ├── repository.py   # Data access layer
│   │       ├── schemas.py      # Pydantic schemas
│   │       └── exceptions.py   # Custom exceptions
│   ├── api/
│   │   └── routes/
│   │       └── <feature_name>.py  # FastAPI router
│   └── cli/
│       └── <feature_name>.py      # Typer CLI commands
├── tests/
│   ├── unit/
│   │   └── test_<feature>_service.py
│   ├── integration/
│   │   └── test_<feature>_repository.py
│   └── e2e/
│       └── test_<feature>_api.py
├── specs/
│   └── <feature_name>/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
└── alembic/
    └── versions/
        └── xxx_create_<feature>_tables.py
```

## 6. Data Models (SQLAlchemy)

```python
# src/lib/<feature>/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime
from datetime import datetime

class <ModelName>(Base):
    __tablename__ = "<table_name>"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    # ... other fields
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Relationships:**
- [Describe foreign keys and relationships]

## 7. API Design

**OpenAPI Documentation:**
- FastAPI auto-generates complete API documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

**Endpoints:**

| Method | Endpoint | Description | Status | Request | Response |
|--------|----------|-------------|--------|---------|----------|
| POST | `/api/<feature>/` | Create entity | 201 | `<Feature>Create` | `<Feature>Response` |
| GET | `/api/<feature>/{id}` | Get by ID | 200/404 | Path: id | `<Feature>Response` |
| GET | `/api/<feature>/` | List with pagination | 200 | Query: limit, offset | `List[<Feature>Response]` |
| PUT | `/api/<feature>/{id}` | Update entity | 200/404 | `<Feature>Update` | `<Feature>Response` |
| DELETE | `/api/<feature>/{id}` | Delete entity | 204/404 | Path: id | None |

**Error Responses:**
- 400: Validation error or business rule violation
- 404: Entity not found
- 422: Pydantic validation failure
- 500: Internal server error

**Note:** Pydantic schemas in `schemas.py` serve as the API contract source of truth.

## 8. CLI Interface Design (Article II Compliance)

```bash
# Command structure
python -m cli.<feature> <command> [options]

# Examples:
python -m cli.<feature> create --name "test" --value 123
python -m cli.<feature> list --limit 10
python -m cli.<feature> get --id <uuid>
python -m cli.<feature> delete --id <uuid>
```

**CLI Module Structure:**
```python
# src/cli/<feature>.py
import typer
from src.lib.<feature>.service import <Service>

app = typer.Typer()

@app.command()
def create(name: str, value: int):
    """Create a new <feature>"""
    # Use service layer directly
    pass
```

## 9. Testing Strategy

### Test Execution Order:
1. **Unit Tests** → Test service layer logic in isolation
2. **Integration Tests** → Test repository with real PostgreSQL
3. **E2E Tests** → Test API endpoints with full stack

### Test Environment:
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
```

### Test Scenarios (From spec.md):
- [ ] Scenario 1: [Map to user story]
- [ ] Scenario 2: [Map to user story]

## 10. Implementation Phases

### Phase 1: Foundation (X days)
**Deliverables:**
- [ ] Database models and Alembic migrations
- [ ] Repository layer with CRUD operations
- [ ] Integration tests for repository
- [ ] Pydantic schemas (API contract enforcement)

**Prerequisites:** None

### Phase 2: Core Functionality (X days)
**Deliverables:**
- [ ] Service layer business logic
- [ ] FastAPI routes and endpoints
- [ ] Pydantic schemas
- [ ] Unit tests for service layer
- [ ] E2E tests for API

**Prerequisites:** Phase 1 complete

### Phase 3: CLI & Validation (X days)
**Deliverables:**
- [ ] Typer CLI commands
- [ ] Error handling and edge cases
- [ ] Performance validation
- [ ] Documentation

**Prerequisites:** Phase 2 complete

## 11. Database Migrations

```python
# alembic/versions/xxx_create_<feature>_tables.py
def upgrade():
    op.create_table(
        '<table_name>',
        sa.Column('id', sa.Integer(), primary_key=True),
        # ... columns
    )

def downgrade():
    op.drop_table('<table_name>')
```

## 12. Error Handling Strategy

```python
# src/lib/<feature>/exceptions.py
class <Feature>NotFoundError(Exception):
    pass

class <Feature>ValidationError(Exception):
    pass
```

## 13. Performance Considerations
- Database indexing strategy
- Query optimization
- Connection pooling
- Caching strategy (if applicable)

## 14. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|----------|
| [Risk 1] | High/Medium/Low | [Strategy] |
| **Celery async task serialization error** | High | Use sync function (`def`) with `asyncio.run()` wrapper. See Section 2 - Celery Async Pattern. |

## 15. Quality Gates

### Before Implementation:
- [ ] All [Needs clarification] resolved in spec.md
- [ ] SDD constitutional gates passed
- [ ] Test strategy approved
- [ ] **If using Celery: Task pattern verified (sync with asyncio.run)**

### Before Completion:
- [ ] All tests passing (unit, integration, e2e)
- [ ] All acceptance criteria met
- [ ] CLI interface complete
- [ ] No abstraction violations
- [ ] Performance requirements met
- [ ] **If using Celery: No async def tasks (all sync with asyncio.run)**
- [ ] **If using Celery: Task results are JSON-serializable**

## 16. Traceability Matrix

| Spec Requirement | Implementation Component | Test Coverage |
|------------------|-------------------------|---------------|
| Story 1 | service.py → method_x | tests/unit/test_<feature>_service.py |
| Story 2 | repository.py → method_y | tests/integration/test_<feature>_repository.py |

---

**Package Management Notes:**
- This project uses `uv` as package manager (not pip or poetry)
- To add dependencies: `uv add <package>`
- To sync environment: `uv sync`
- Virtual environment: `.venv` (managed by uv)
- Always activate: `source .venv/bin/activate` before running commands

---

Save as: `specs/<feature_name>/plan.md`
