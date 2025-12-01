# Test Suite Documentation

## Overview

This test suite follows **SDD Test-First methodology**:
- Tests are written **BEFORE** implementation
- Tests should **FAIL** initially (no implementation exists)
- Integration tests use **REAL** databases and services (no mocking)
- Each test maps to acceptance criteria in `spec.md`

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Unit tests (isolated, mocked dependencies)
│   ├── test_topic_agent.py
│   ├── test_research_agent.py
│   ├── test_blog_writer_agent.py
│   └── test_services.py
├── integration/                   # Integration tests (real DB, real LLM)
│   ├── test_models.py
│   ├── test_agent_workflows.py
│   └── test_pipelines.py
└── e2e/                          # End-to-end tests (full API stack)
    ├── test_research_flow.py
    └── test_blog_generation_flow.py
```

## Test Types

### Unit Tests
- **Location:** `tests/unit/`
- **Purpose:** Test individual components in isolation
- **Dependencies:** Mocked (LLM, external APIs)
- **Database:** Not used
- **Examples:**
  - Topic agent categorization logic
  - Research agent data processing
  - Blog writer formatting

### Integration Tests
- **Location:** `tests/integration/`
- **Purpose:** Test component interactions with real services
- **Dependencies:** Real PostgreSQL, Real AWS Bedrock (rate-limited)
- **Database:** Real PostgreSQL test database
- **Examples:**
  - Database model persistence
  - Agent workflows with real LLM
  - External API integrations

### E2E Tests
- **Location:** `tests/e2e/`
- **Purpose:** Test complete user flows via API
- **Dependencies:** Full FastAPI application, Real database
- **Database:** Real PostgreSQL test database
- **Examples:**
  - Submit research query → Get result
  - Generate blog → Retrieve content
  - Full workflow execution

## Prerequisites

### Environment Setup

1. **PostgreSQL Test Database:**
   ```bash
   # Create test database
   createdb test_research_db
   ```

2. **AWS Credentials:**
   ```bash
   # Set AWS credentials for Bedrock access
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_REGION=us-east-1
   ```

3. **Environment Variables:**
   ```bash
   export TEST_DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test_research_db"
   export BEDROCK_MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"
   ```

### Install Test Dependencies

```bash
# Activate virtual environment (uv managed)
source .venv/bin/activate

# Install test dependencies
uv add --dev pytest pytest-asyncio pytest-cov httpx
```

## Running Tests

### Run All Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/ -v
```

### Run Specific Test Types

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only (requires real DB and LLM)
pytest tests/integration/ -v -m integration

# E2E tests only
pytest tests/e2e/ -v -m e2e
```

### Run Specific Test Files

```bash
# Run topic agent tests
pytest tests/unit/test_topic_agent.py -v

# Run research workflow tests
pytest tests/integration/test_agent_workflows.py -v

# Run API endpoint tests
pytest tests/e2e/test_research_flow.py -v
```

### Run Specific Test Classes/Methods

```bash
# Run specific test class
pytest tests/unit/test_topic_agent.py::TestTopicAgentCategorization -v

# Run specific test method
pytest tests/unit/test_topic_agent.py::TestTopicAgentCategorization::test_categorize_core_ai_topic -v
```

### Run with Coverage

```bash
# Run tests with coverage report
pytest tests/ --cov=src/lib --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Run Tests in Parallel

```bash
# Install pytest-xdist
uv add --dev pytest-xdist

# Run tests in parallel
pytest tests/ -n auto
```

## Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests (requires real services)
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.asyncio` - Async tests

### Run by Marker

```bash
# Run only integration tests
pytest -m integration -v

# Run only E2E tests
pytest -m e2e -v

# Skip integration tests (faster)
pytest -m "not integration" -v
```

## Test Fixtures

### Database Fixtures

- `db_session` - Real PostgreSQL session with transaction rollback
- `db_engine` - Database engine for test database

### LLM Fixtures

- `llm` - Real AWS Bedrock LLM instance (rate-limited)
- `llm_config` - LLM configuration

### API Fixtures

- `async_client` - AsyncClient for FastAPI testing

### Test Data Fixtures

- `sample_research_query` - Sample query data
- `sample_research_result` - Sample research result
- `sample_blog_content` - Sample blog content
- `create_test_research_query` - Factory for creating test queries
- `create_test_research_result` - Factory for creating test results
- `create_test_content_item` - Factory for creating test content

## Test Execution Guidelines

### Test-First Workflow

1. **Write tests first** (they should FAIL)
2. **Implement code** to make tests PASS
3. **Refactor** if needed (tests should still PASS)

### Integration Test Guidelines

- Use **real PostgreSQL** database (no mocking)
- Use **real AWS Bedrock** LLM (with rate limiting)
- Use **real external APIs** (ArXiv, GitHub) with test fixtures
- Tests run in **transactions that rollback** after each test

### E2E Test Guidelines

- Test **full request-response cycle**
- Verify **Pydantic schema validation**
- Check **OpenAPI compliance**
- Test **error scenarios** (400, 404, 422, 500)

## Common Issues

### Database Connection Errors

```bash
# Ensure PostgreSQL is running
sudo systemctl status postgresql

# Check test database exists
psql -l | grep test_research_db
```

### AWS Bedrock Access Errors

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### Import Errors

```bash
# Ensure you're in the project root
cd /home/mohit/Mohit/research

# Ensure virtual environment is activated
source .venv/bin/activate

# Verify Python path
python -c "import sys; print(sys.path)"
```

## Test Quality Checklist

- [ ] Each test maps to acceptance criteria in `spec.md`
- [ ] Tests have descriptive names explaining expected behavior
- [ ] Tests follow Arrange-Act-Assert pattern
- [ ] Integration tests use real database (no mocks)
- [ ] E2E tests test full request-response cycle
- [ ] All edge cases covered
- [ ] Error scenarios tested
- [ ] Tests initially FAIL (no implementation exists)
- [ ] Async tests properly marked with `@pytest.mark.asyncio`

## Continuous Integration

Tests should be run in CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    source .venv/bin/activate
    pytest tests/ -v --cov=src/lib --cov-report=xml
```

## Performance Considerations

- **Integration tests** may take longer due to real LLM calls
- **Rate limiting** is implemented to prevent API overuse
- **Test database** is isolated and cleaned after each test
- **Parallel execution** can speed up test runs (use `-n auto`)

## Debugging Tests

### Run with Verbose Output

```bash
pytest tests/ -v -s  # -s shows print statements
```

### Run with PDB Debugger

```bash
pytest tests/ --pdb  # Drops into debugger on failure
```

### Show Test Coverage

```bash
pytest tests/ --cov=src/lib --cov-report=term-missing
```

## Next Steps

1. **Run tests** - They should FAIL initially (no implementation)
2. **Implement code** - Make tests pass
3. **Refactor** - Improve code while keeping tests green
4. **Add more tests** - Cover edge cases and error scenarios

---

**Note:** This project uses `uv` as package manager. Always activate `.venv` before running tests.

