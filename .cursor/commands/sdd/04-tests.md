You are a test-first Python backend developer. Read the `spec.md` and `plan.md` for the feature and generate comprehensive test suites following SDD Test-First methodology.

**Testing Philosophy:**
- Write tests BEFORE implementation
- Tests should FAIL first (no implementation exists)
- Integration tests use REAL databases (no mocking)
- Each test maps to acceptance criteria in spec.md

**Package Management:**
- This project uses `uv` as package manager
- To add test dependencies: `uv add --dev pytest pytest-asyncio`
- Virtual environment: `.venv` (managed by uv)
- Activate: `source .venv/bin/activate`

---

## Test Generation Command

**Feature:** <feature_name>
**Based On:** 
- `specs/<feature>/spec.md` (acceptance criteria)
- `specs/<feature>/plan.md` (technical design + API design)

---

## Output Structure

Generate 3 types of test files:

### 1. Unit Tests (Service Layer Logic)
**Location:** `tests/unit/test_<feature>_service.py`

```python
"""
Unit tests for <Feature> Service Layer
Tests business logic in isolation using mocks for repository
"""
import pytest
from unittest.mock import AsyncMock, Mock
from src.lib.<feature>.service import <Feature>Service
from src.lib.<feature>.exceptions import <Feature>NotFoundError, <Feature>ValidationError
from src.lib.<feature>.models import <Model>


@pytest.fixture
def mock_repository():
    """Mock repository for service testing"""
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repository):
    """Service instance with mocked repository"""
    return <Feature>Service(mock_repository)


class TestCreate<Entity>:
    """Test create <entity> functionality"""
    
    @pytest.mark.asyncio
    async def test_create_success(self, service, mock_repository):
        """Should create <entity> with valid data"""
        # Arrange
        input_data = {"name": "test", "value": 123}
        expected = <Model>(id=1, name="test", value=123)
        mock_repository.create.return_value = expected
        
        # Act
        result = await service.create_<entity>(input_data)
        
        # Assert
        assert result.name == "test"
        assert result.value == 123
        mock_repository.create.assert_called_once_with(input_data)
    
    @pytest.mark.asyncio
    async def test_create_validation_error(self, service):
        """Should raise error when required field missing"""
        # Arrange
        invalid_data = {"value": 123}  # missing 'name'
        
        # Act & Assert
        with pytest.raises(<Feature>ValidationError) as exc:
            await service.create_<entity>(invalid_data)
        assert "name is required" in str(exc.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_with_invalid_value(self, service):
        """Should raise error when value is negative"""
        # Arrange
        invalid_data = {"name": "test", "value": -1}
        
        # Act & Assert
        with pytest.raises(<Feature>ValidationError) as exc:
            await service.create_<entity>(invalid_data)
        assert "value must be positive" in str(exc.value).lower()


class TestGet<Entity>:
    """Test get <entity> functionality"""
    
    @pytest.mark.asyncio
    async def test_get_success(self, service, mock_repository):
        """Should return <entity> when found"""
        # Arrange
        expected = <Model>(id=1, name="test", value=123)
        mock_repository.get_by_id.return_value = expected
        
        # Act
        result = await service.get_<entity>(1)
        
        # Assert
        assert result.id == 1
        assert result.name == "test"
        mock_repository.get_by_id.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_get_not_found(self, service, mock_repository):
        """Should raise error when <entity> not found"""
        # Arrange
        mock_repository.get_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(<Feature>NotFoundError) as exc:
            await service.get_<entity>(999)
        assert "not found" in str(exc.value).lower()


class TestUpdate<Entity>:
    """Test update <entity> functionality"""
    
    @pytest.mark.asyncio
    async def test_update_success(self, service, mock_repository):
        """Should update existing <entity>"""
        # Arrange
        existing = <Model>(id=1, name="old", value=100)
        updated = <Model>(id=1, name="new", value=200)
        mock_repository.get_by_id.return_value = existing
        mock_repository.update.return_value = updated
        
        # Act
        result = await service.update_<entity>(1, {"name": "new", "value": 200})
        
        # Assert
        assert result.name == "new"
        assert result.value == 200


class TestDelete<Entity>:
    """Test delete <entity> functionality"""
    
    @pytest.mark.asyncio
    async def test_delete_success(self, service, mock_repository):
        """Should delete existing <entity>"""
        # Arrange
        mock_repository.get_by_id.return_value = <Model>(id=1)
        mock_repository.delete.return_value = True
        
        # Act
        result = await service.delete_<entity>(1)
        
        # Assert
        assert result is True
        mock_repository.delete.assert_called_once_with(1)
```

---

### 2. Integration Tests (Repository Layer with Real DB)
**Location:** `tests/integration/test_<feature>_repository.py`

```python
"""
Integration tests for <Feature> Repository
Uses REAL PostgreSQL database (no mocking)
Tests run in transactions that rollback after each test
"""
import pytest
from sqlalchemy import select
from src.lib.<feature>.repository import <Feature>Repository
from src.lib.<feature>.models import <Model>


@pytest.mark.integration
class TestRepositoryCreate:
    """Test repository create operations with real database"""
    
    @pytest.mark.asyncio
    async def test_create_persists_to_database(self, db_session):
        """Should persist <entity> to database"""
        # Arrange
        repo = <Feature>Repository(db_session)
        data = {"name": "test", "value": 123}
        
        # Act
        result = await repo.create(data)
        await db_session.commit()
        
        # Assert - verify in database
        assert result.id is not None
        assert result.name == "test"
        assert result.value == 123
        
        # Verify can be retrieved
        retrieved = await db_session.get(<Model>, result.id)
        assert retrieved is not None
        assert retrieved.name == "test"
    
    @pytest.mark.asyncio
    async def test_create_with_all_fields(self, db_session):
        """Should create with all optional fields"""
        # Arrange
        repo = <Feature>Repository(db_session)
        data = {
            "name": "test",
            "value": 123,
            "description": "test description",
            "is_active": True
        }
        
        # Act
        result = await repo.create(data)
        await db_session.commit()
        
        # Assert
        assert result.description == "test description"
        assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_create_sets_timestamps(self, db_session):
        """Should automatically set created_at and updated_at"""
        # Arrange
        repo = <Feature>Repository(db_session)
        data = {"name": "test", "value": 123}
        
        # Act
        result = await repo.create(data)
        await db_session.commit()
        
        # Assert
        assert result.created_at is not None
        assert result.updated_at is not None


@pytest.mark.integration
class TestRepositoryRead:
    """Test repository read operations"""
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, db_session):
        """Should retrieve <entity> by ID"""
        # Arrange - create test data
        repo = <Feature>Repository(db_session)
        created = await repo.create({"name": "test", "value": 123})
        await db_session.commit()
        
        # Act
        result = await repo.get_by_id(created.id)
        
        # Assert
        assert result is not None
        assert result.id == created.id
        assert result.name == "test"
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session):
        """Should return None when ID not found"""
        # Arrange
        repo = <Feature>Repository(db_session)
        
        # Act
        result = await repo.get_by_id(99999)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_all(self, db_session):
        """Should list all <entities>"""
        # Arrange - create multiple entities
        repo = <Feature>Repository(db_session)
        await repo.create({"name": "test1", "value": 100})
        await repo.create({"name": "test2", "value": 200})
        await db_session.commit()
        
        # Act
        results = await repo.list_all(limit=10)
        
        # Assert
        assert len(results) >= 2
    
    @pytest.mark.asyncio
    async def test_list_with_pagination(self, db_session):
        """Should support pagination"""
        # Arrange - create test data
        repo = <Feature>Repository(db_session)
        for i in range(5):
            await repo.create({"name": f"test{i}", "value": i * 100})
        await db_session.commit()
        
        # Act
        results = await repo.list_all(limit=2, offset=2)
        
        # Assert
        assert len(results) == 2


@pytest.mark.integration
class TestRepositoryUpdate:
    """Test repository update operations"""
    
    @pytest.mark.asyncio
    async def test_update_modifies_record(self, db_session):
        """Should update existing record"""
        # Arrange
        repo = <Feature>Repository(db_session)
        created = await repo.create({"name": "original", "value": 100})
        await db_session.commit()
        
        # Act
        updated = await repo.update(created.id, {"name": "updated", "value": 200})
        await db_session.commit()
        
        # Assert
        assert updated.name == "updated"
        assert updated.value == 200
        assert updated.updated_at > created.updated_at


@pytest.mark.integration
class TestRepositoryDelete:
    """Test repository delete operations"""
    
    @pytest.mark.asyncio
    async def test_delete_removes_record(self, db_session):
        """Should delete record from database"""
        # Arrange
        repo = <Feature>Repository(db_session)
        created = await repo.create({"name": "test", "value": 123})
        await db_session.commit()
        
        # Act
        result = await repo.delete(created.id)
        await db_session.commit()
        
        # Assert
        assert result is True
        deleted = await db_session.get(<Model>, created.id)
        assert deleted is None
```

---

### 3. End-to-End Tests (FastAPI with Real DB)
**Location:** `tests/e2e/test_<feature>_api.py`

```python
"""
E2E tests for <Feature> API endpoints
Tests full request-response cycle with real database
Maps to acceptance criteria from spec.md
Verifies Pydantic schema validation and OpenAPI compliance
"""
import pytest
from httpx import AsyncClient
from src.main import app


@pytest.mark.e2e
class TestCreate<Entity>API:
    """Test POST /api/<feature>/ endpoint"""
    
    @pytest.mark.asyncio
    async def test_create_returns_201(self, async_client: AsyncClient):
        """Should create <entity> and return 201 Created"""
        # Arrange
        payload = {"name": "test", "value": 123}
        
        # Act
        response = await async_client.post("/api/<feature>/", json=payload)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test"
        assert data["value"] == 123
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_validation_error_returns_400(self, async_client):
        """Should return 400 when validation fails"""
        # Arrange - missing required field
        payload = {"value": 123}  # missing 'name'
        
        # Act
        response = await async_client.post("/api/<feature>/", json=payload)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_create_with_invalid_type_returns_422(self, async_client):
        """Should return 422 when field type is wrong"""
        # Arrange
        payload = {"name": "test", "value": "not_a_number"}
        
        # Act
        response = await async_client.post("/api/<feature>/", json=payload)
        
        # Assert
        assert response.status_code == 422


@pytest.mark.e2e
class TestGet<Entity>API:
    """Test GET /api/<feature>/{id} endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_returns_200(self, async_client: AsyncClient, create_test_<entity>):
        """Should return <entity> when found"""
        # Arrange
        created = await create_test_<entity>({"name": "test", "value": 123})
        
        # Act
        response = await async_client.get(f"/api/<feature>/{created.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created.id
        assert data["name"] == "test"
    
    @pytest.mark.asyncio
    async def test_get_not_found_returns_404(self, async_client):
        """Should return 404 when <entity> not found"""
        # Act
        response = await async_client.get("/api/<feature>/99999")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


@pytest.mark.e2e
class TestList<Entity>API:
    """Test GET /api/<feature>/ endpoint"""
    
    @pytest.mark.asyncio
    async def test_list_returns_200(self, async_client, create_test_<entity>):
        """Should list all <entities>"""
        # Arrange - create test data
        await create_test_<entity>({"name": "test1", "value": 100})
        await create_test_<entity>({"name": "test2", "value": 200})
        
        # Act
        response = await async_client.get("/api/<feature>/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    @pytest.mark.asyncio
    async def test_list_with_pagination(self, async_client):
        """Should support pagination parameters"""
        # Act
        response = await async_client.get("/api/<feature>/?limit=10&offset=0")
        
        # Assert
        assert response.status_code == 200


@pytest.mark.e2e
class TestUpdate<Entity>API:
    """Test PUT /api/<feature>/{id} endpoint"""
    
    @pytest.mark.asyncio
    async def test_update_returns_200(self, async_client, create_test_<entity>):
        """Should update <entity> and return 200 OK"""
        # Arrange
        created = await create_test_<entity>({"name": "original", "value": 100})
        payload = {"name": "updated", "value": 200}
        
        # Act
        response = await async_client.put(f"/api/<feature>/{created.id}", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated"
        assert data["value"] == 200


@pytest.mark.e2e
class TestDelete<Entity>API:
    """Test DELETE /api/<feature>/{id} endpoint"""
    
    @pytest.mark.asyncio
    async def test_delete_returns_204(self, async_client, create_test_<entity>):
        """Should delete <entity> and return 204 No Content"""
        # Arrange
        created = await create_test_<entity>({"name": "test", "value": 123})
        
        # Act
        response = await async_client.delete(f"/api/<feature>/{created.id}")
        
        # Assert
        assert response.status_code == 204
        
        # Verify deleted
        get_response = await async_client.get(f"/api/<feature>/{created.id}")
        assert get_response.status_code == 404
```

---

### 4. Test Fixtures (Shared Configuration)
**Location:** `tests/conftest.py`

```python
"""
Shared test fixtures for all test types
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient
from src.main import app
from src.common.database import Base, get_db
from src.lib.<feature>.repository import <Feature>Repository
from src.lib.<feature>.models import <Model>


# Database fixtures
@pytest.fixture(scope="session")
def db_url():
    """Test database URL - uses real PostgreSQL"""
    return "postgresql+asyncpg://test:test@localhost:5432/test_db"


@pytest_asyncio.fixture(scope="session")
async def engine(db_url):
    """Create test database engine"""
    engine = create_async_engine(db_url, poolclass=NullPool)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Create test database session with transaction rollback"""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


# API client fixtures
@pytest_asyncio.fixture
async def async_client(db_session):
    """AsyncClient for API testing with database override"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


# Helper fixtures
@pytest_asyncio.fixture
def create_test_<entity>(db_session):
    """Factory fixture for creating test <entities>"""
    async def _create(data: dict) -> <Model>:
        repo = <Feature>Repository(db_session)
        entity = await repo.create(data)
        await db_session.commit()
        return entity
    return _create
```

---

## Test Execution Commands

```bash
# Activate virtual environment (uv managed)
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test type
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v -m integration  # Integration tests
pytest tests/e2e/ -v -m e2e             # E2E tests only

# Run tests for specific feature
pytest tests/ -k "<feature>" -v

# Run with coverage
pytest tests/ --cov=src/lib/<feature> --cov-report=html

# Run tests in parallel
pytest tests/ -n auto
```

**Note:** This project uses `uv` as package manager. Always activate `.venv` before running tests.

---

## Test Quality Checklist

- [ ] Each test maps to acceptance criteria in spec.md
- [ ] Tests have descriptive names explaining expected behavior
- [ ] Tests follow Arrange-Act-Assert pattern
- [ ] Integration tests use real database (no mocks)
- [ ] E2E tests test full request-response cycle
- [ ] All edge cases covered
- [ ] Error scenarios tested
- [ ] Tests initially FAIL (no implementation exists)
- [ ] **If testing Celery tasks: Verify sync function pattern (not async def)**
- [ ] **If testing Celery tasks: Verify asyncio.run() wrapper usage**

---

**Package Management:**
- Use `uv add --dev pytest pytest-asyncio` to add test dependencies
- Virtual environment: `.venv` (managed by uv)
- Always activate: `source .venv/bin/activate` before running tests

---

Save all test files to appropriate locations as specified above.
