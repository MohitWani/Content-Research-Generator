# Testing

This document outlines the testing strategy and guidelines for the project.

## Framework

We use [`pytest`](https://docs.pytest.org/) as the primary framework for writing and running tests. `pytest` provides a powerful and flexible way to write simple and scalable test suites.

## Running Tests

To run the entire test suite, execute the following command from the project root:

```bash
uv run pytest
```

This command will automatically discover and run all tests in the `tests/` directory.

### Running Specific Tests

You can run tests for a specific file or directory by providing the path:

```bash
uv run pytest tests/modules/user/services/test_user_service.py
```

## Test Structure

All tests are located in the `tests/` directory, which mirrors the structure of the `app/` directory.

-   `tests/modules/`: Contains tests for the different modules of the application.
-   `tests/conftest.py`: This file contains shared fixtures and configuration for the test suite. It also modifies the Python path to ensure that the `app` module can be imported correctly by the tests.

### Test Files

Test files are named with a `test_` prefix (e.g., `test_user_service.py`). This convention allows `pytest` to automatically discover the tests.

## Mocking

We use `unittest.mock` to mock dependencies such as database repositories and external services. This allows us to isolate the code under test and ensure that our unit tests are fast and reliable.

### Example

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def user_service():
    with patch('app.modules.user.services.user_service.UserRepository') as mock_user_repository:
        service = UserService()
        service.repository = mock_user_repository.return_value
        yield service, service.repository

def test_list_users(user_service):
    # Arrange
    service, mock_repo = user_service
    db_session = MagicMock()
    expected_users = [User(id=uuid4(), email="test1@example.com")]
    mock_repo.list_users.return_value = expected_users

    # Act
    result = service.list_users(db_session)

    # Assert
    assert result == expected_users
    mock_repo.list_users.assert_called_once_with(db=db_session)
```

## Code Coverage

We use `pytest-cov` to measure code coverage. The coverage report is configured in `pytest.ini`. To generate a coverage report, run the tests with the following command:

```bash
uv run pytest --cov=app
```

This will output a coverage summary to the console.
