from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.common.constants.error_constant import ErrorConstant
from app.core.exception.app_exception import AppException
from app.modules.user.models.user_model import User
from app.modules.user.schemas.user_schemas import CreateUserRequest
from app.modules.user.services.user_service import UserService


@pytest.fixture
def user_service():
    with (
        patch(
            'app.modules.user.services.user_service.UserRepository'
        ) as mock_user_repository,
        patch(
            'app.modules.user.services.user_service.CacheManager'
        ) as mock_cache_manager,
    ):
        service = UserService()
        service.repository = mock_user_repository.return_value
        service.cache_provider = mock_cache_manager.get_cache_provider.return_value
        yield service, service.repository, service.cache_provider


def test_create_user_success(user_service):
    # Arrange
    service, mock_repo, _ = user_service
    db_session = MagicMock()
    user_data = CreateUserRequest(
        email='new@example.com',
        first_name='Test',
        last_name='User',
        password='password',
    )
    mock_repo.get_user_by_email.return_value = None
    created_user = User(id=uuid4(), **user_data.model_dump())
    mock_repo.create_user.return_value = created_user

    # Act
    result = service.create_user(db_session, user_data)

    # Assert
    assert result.email == user_data.email
    mock_repo.get_user_by_email.assert_called_once_with(
        db=db_session, email=user_data.email
    )
    mock_repo.create_user.assert_called_once()


def test_create_user_conflict(user_service):
    # Arrange
    service, mock_repo, _ = user_service
    db_session = MagicMock()
    user_data = CreateUserRequest(
        email='existing@example.com',
        first_name='Test',
        last_name='User',
        password='password',
    )
    mock_repo.get_user_by_email.return_value = User(id=uuid4(), email=user_data.email)

    # Act & Assert
    with pytest.raises(AppException) as exc_info:
        service.create_user(db_session, user_data)

    assert exc_info.value.error_constant == ErrorConstant.CONFLICT
    mock_repo.get_user_by_email.assert_called_once_with(
        db=db_session, email=user_data.email
    )


@pytest.mark.asyncio
async def test_get_user_by_id_found_in_cache(user_service):
    # Arrange
    service, _, mock_cache = user_service
    db_session = MagicMock()
    user_id = str(uuid4())
    user = User(id=user_id, email='test@example.com')
    cached_user = {'id': user.id, 'email': user.email}
    # Make cache_and_retrieve an async mock
    mock_cache.cache_and_retrieve = AsyncMock(return_value=user)

    # Act
    result = await service.get_user_by_id(db_session, user_id)

    # Assert
    assert result.id == cached_user['id']
    mock_cache.cache_and_retrieve.assert_called_once()


def test_get_user_by_email(user_service):
    # Arrange
    service, mock_repo, _ = user_service
    db_session = MagicMock()
    email = 'test@example.com'
    expected_user = User(id=uuid4(), email=email)
    mock_repo.get_user_by_email.return_value = expected_user

    # Act
    result = service.get_user_by_email(db_session, email)

    # Assert
    assert result == expected_user
    mock_repo.get_user_by_email.assert_called_once_with(db=db_session, email=email)
