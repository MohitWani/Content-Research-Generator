You are an expert Python/FastAPI developer implementing tasks using Specification-Driven Development (SDD) methodology.

**Context:**
- Read the feature's `spec.md`, `plan.md`, and `tasks.md` from `specs/<feature_name>/`
- Implement ONE task at a time
- Follow Test-First approach strictly
- **Package Manager: uv** (use `uv add <package>`, NOT `pip install` or `poetry add`)
- **Virtual Environment: `.venv`** (managed by uv, activate with `source .venv/bin/activate`)

---

## Implementation Command

**Feature:** <feature_name>
**Task ID:** <Task_ID> (e.g., T005)
**Task Description:** <Copy from tasks.md>

---

## SDD Constitutional Constraints

### ✅ Article I: Library-First Principle
- Write core logic as independent library module first
- Location: `src/lib/<feature>/`
- Must be usable without API/CLI layer
- No framework coupling in business logic

### ✅ Article II: CLI Interface Mandate
- All functionality must be accessible via CLI
- Use Typer for CLI implementation
- Location: `src/cli/<feature>.py`

### ✅ Article III: Test-First Command
- If this is a TEST task (marked [Test-First]):
  - Write comprehensive tests first
  - Tests MUST FAIL (no implementation exists yet)
  - Verify test failure before proceeding
- If this is an IMPLEMENTATION task:
  - Tests already exist from previous task
  - Implement code to make tests PASS
  - Do not modify tests unless they have bugs

### ✅ Article VII: Simplicity Mandate
- Maximum 3 project components: lib, api, cli
- No designing for future requirements
- Implement only what spec.md requires
- No speculative features

### ✅ Article VIII: Anti-Abstraction Principle
- Use FastAPI, SQLAlchemy, Typer DIRECTLY
- No wrapper classes or helper abstractions
- No DTO/Entity separation unless proven necessary
- No "manager", "handler", "processor" classes without clear need

### ✅ Article IX: Integration-First Testing
- Integration tests use real PostgreSQL database
- Integration tests use real Redis instance
- No mocking of databases or external services
- Use test database with transaction rollback

---

## Implementation Steps

### Step 1: Review Context
- [ ] Read `specs/<feature>/spec.md` - understand WHAT and WHY
- [ ] Read `specs/<feature>/plan.md` - understand HOW (includes API design)
- [ ] Read `specs/<feature>/tasks.md` - find current task
- [ ] Check task dependencies (all must be complete)

### Step 2: Locate Related Files
- [ ] Identify which files this task modifies/creates
- [ ] Read existing code in those files
- [ ] Understand the surrounding context

### Step 3: Check Test-First Status

**If this task is [Test-First]:**
```python
# Write tests FIRST
# Tests should comprehensively cover:
# - Happy path scenarios
# - Edge cases
# - Error conditions
# - Validation rules

# After writing tests:
# 1. Run tests - they should FAIL
# 2. Verify failure messages make sense
# 3. Stop here - implementation comes in next task
```

**If this task is IMPLEMENTATION:**
```python
# Tests already exist from previous [Test-First] task
# 1. Read the test file
# 2. Understand what tests expect
# 3. Implement minimal code to make tests PASS
# 4. Run tests - they should now PASS
# 5. Refactor if needed (tests still PASS)
```

### Step 4: Implement

**⚠️ CRITICAL CHECK: If implementing Celery tasks, ensure:**
- [ ] Task function is `def` (sync), NOT `async def`
- [ ] Use `asyncio.run()` to execute async workflows inside
- [ ] Return value is JSON-serializable (dict, list, str, int, etc.)
- [ ] Reference: `src/modules/tmap/workers/tasks.py` line 350 for correct pattern

**For Database/Repository Tasks:**
```python
# Use SQLAlchemy 2.0+ style with async
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class <Feature>Repository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, data: dict) -> Model:
        obj = Model(**data)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def get_by_id(self, id: int) -> Model | None:
        result = await self.session.execute(
            select(Model).where(Model.id == id)
        )
        return result.scalar_one_or_none()
```

**For Service Layer Tasks:**
```python
# Pure business logic, no framework dependencies
from src.lib.<feature>.repository import <Feature>Repository
from src.lib.<feature>.exceptions import <Feature>NotFoundError

class <Feature>Service:
    def __init__(self, repository: <Feature>Repository):
        self.repository = repository
    
    async def create_<entity>(self, data: dict) -> Model:
        # Business validation
        if not data.get('field'):
            raise ValueError("Field is required")
        
        # Use repository
        return await self.repository.create(data)
    
    async def get_<entity>(self, id: int) -> Model:
        obj = await self.repository.get_by_id(id)
        if not obj:
            raise <Feature>NotFoundError(f"Entity {id} not found")
        return obj
```

**For FastAPI Routes:**
```python
# API layer - thin wrapper around service
# Pydantic schemas define the API contract (FastAPI auto-generates OpenAPI docs)
from fastapi import APIRouter, Depends, HTTPException, status
from src.lib.<feature>.service import <Feature>Service
from src.lib.<feature>.schemas import <Feature>Create, <Feature>Response

router = APIRouter(prefix="/api/<feature>", tags=["<feature>"])

@router.post("/", response_model=<Feature>Response, status_code=status.HTTP_201_CREATED)
async def create_<entity>(
    data: <Feature>Create,
    service: <Feature>Service = Depends(get_<feature>_service)
):
    """Create new <entity>
    
    OpenAPI docs auto-generated at /docs
    """
    try:
        result = await service.create_<entity>(data.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{id}", response_model=<Feature>Response)
async def get_<entity>(
    id: int,
    service: <Feature>Service = Depends(get_<feature>_service)
):
    """Get <entity> by ID
    
    Returns 404 if not found
    """
    try:
        result = await service.get_<entity>(id)
        return result
    except <Feature>NotFoundError:
        raise HTTPException(status_code=404, detail="Entity not found")
```

**For CLI Commands:**
```python
# CLI layer using Typer
import typer
from src.lib.<feature>.service import <Feature>Service
from src.lib.<feature>.repository import <Feature>Repository
from src.common.database import get_session

app = typer.Typer()

@app.command()
def create(
    name: str = typer.Option(..., help="Entity name"),
    value: int = typer.Option(..., help="Entity value")
):
    """Create a new <entity>"""
    async def _create():
        async with get_session() as session:
            repo = <Feature>Repository(session)
            service = <Feature>Service(repo)
            result = await service.create_<entity>({
                "name": name,
                "value": value
            })
            typer.echo(f"Created <entity> with ID: {result.id}")
    
    import asyncio
    asyncio.run(_create())

@app.command()
def get(id: int = typer.Argument(..., help="Entity ID")):
    """Get <entity> by ID"""
    async def _get():
        async with get_session() as session:
            repo = <Feature>Repository(session)
            service = <Feature>Service(repo)
            result = await service.get_<entity>(id)
            typer.echo(f"ID: {result.id}, Name: {result.name}, Value: {result.value}")
    
    import asyncio
    asyncio.run(_get())
```

**For Celery Tasks (CRITICAL PATTERN):**
```python
# ⚠️ CRITICAL: Celery tasks MUST be sync (def, not async def)
# Use asyncio.run() to execute async workflows inside
import asyncio
from src.workers.celery_app import celery_app

@celery_app.task(bind=True, name="<feature>_task")
def <feature>_task(self, ...):  # ← SYNC function (def, NOT async def)
    """
    Celery task MUST be sync function.
    Use asyncio.run() to execute async workflows inside.
    """
    # Execute async workflow in sync context
    result = asyncio.run(async_workflow_function(...))
    
    # Return JSON-serializable result
    return {
        'status': 'success',
        'data': result
    }

# ❌ WRONG - Will cause serialization error:
# @celery_app.task(bind=True)
# async def celery_task(...):  # ← DON'T DO THIS
#     return await async_function(...)

# ✅ CORRECT - Use sync wrapper:
# @celery_app.task(bind=True)
# def celery_task(...):  # ← SYNC function
#     return asyncio.run(async_function(...))
```

**For Tests:**
```python
# Unit tests (service layer)
import pytest
from src.lib.<feature>.service import <Feature>Service
from src.lib.<feature>.exceptions import <Feature>NotFoundError

@pytest.mark.asyncio
async def test_create_<entity>_success(mock_repository):
    service = <Feature>Service(mock_repository)
    result = await service.create_<entity>({"name": "test", "value": 123})
    assert result.name == "test"
    assert result.value == 123

# Integration tests (repository layer with real DB)
@pytest.mark.asyncio
async def test_repository_create(db_session):
    repo = <Feature>Repository(db_session)
    result = await repo.create({"name": "test", "value": 123})
    assert result.id is not None
    assert result.name == "test"

# E2E tests (FastAPI with real DB)
@pytest.mark.asyncio
async def test_api_create_<entity>(async_client, db_session):
    response = await async_client.post(
        "/api/<feature>/",
        json={"name": "test", "value": 123}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test"
```

### Step 5: Verify

**Run Tests:**
```bash
# Activate virtual environment (uv managed)
source .venv/bin/activate

# Run specific test file
pytest tests/unit/test_<feature>_service.py -v

# Run integration tests (requires DB)
pytest tests/integration/test_<feature>_repository.py -v

# Run E2E tests
pytest tests/e2e/test_<feature>_api.py -v

# Run all tests for this feature
pytest tests/ -k "<feature>" -v
```

**Verify CLI:**
```bash
# Activate virtual environment first
source .venv/bin/activate

# Test CLI commands
python -m src.cli.<feature> create --name "test" --value 123
python -m src.cli.<feature> get 1
python -m src.cli.<feature> list
```

**Add Dependencies (if needed):**
```bash
# Use uv to add packages (NOT pip install or poetry add)
uv add <package-name>
uv add --dev pytest-asyncio  # For dev dependencies
```

### Step 6: Update Task Status
- [ ] Mark task as complete in `tasks.md`
- [ ] Update progress percentage
- [ ] Check if any dependent tasks are now unblocked

---

## Expected Output

### For Test-First Tasks:
- Comprehensive test file created
- Tests cover all scenarios from acceptance criteria
- Tests FAIL when run (no implementation exists)
- Clear test failure messages

### For Implementation Tasks:
- Code file(s) created/modified
- Minimal implementation (no unnecessary code)
- Previously written tests now PASS
- Code follows SDD principles
- No abstraction violations
- Ready to commit

### Quality Checklist:
- [ ] Code implements only what task requires (no extras)
- [ ] Tests pass (for implementation tasks)
- [ ] Tests fail appropriately (for test-first tasks)
- [ ] No wrapper classes or abstractions
- [ ] Integration tests use real services
- [ ] CLI works if this task involved CLI
- [ ] Follows existing project conventions
- [ ] Type hints included
- [ ] Docstrings for public methods
- [ ] No hardcoded values (use config/env)
- [ ] **If Celery task: Must be sync (`def`) with `asyncio.run()` wrapper**
- [ ] **If Celery task: Return value is JSON-serializable**

---

## Next Steps

After completing this task:
1. Verify all tests pass
2. Check next task in `tasks.md`
3. Verify dependencies are met
4. Execute `/sdd.implement` for next task

If all tasks complete:
- Run full test suite
- Verify all acceptance criteria met
- Update documentation
- Ready for code review

---

**Remember:**
- One task at a time
- Test-first always
- No premature optimization
- No unnecessary abstractions
- Use frameworks directly
- Keep it simple
- **⚠️ CRITICAL: Celery tasks must be sync (`def`) with `asyncio.run()` wrapper**

---

**Package Management:**
- Use `uv add <package>` to add dependencies (NOT `pip install` or `poetry add`)
- Virtual environment: `.venv` (managed by uv)
- Always activate: `source .venv/bin/activate` before running commands or tests

---

Save implementation results to appropriate files as per task definition.