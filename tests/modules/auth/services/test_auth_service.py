from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.common.constants.error_constant import ErrorConstant
from app.core.exception.app_exception import AppException
from app.modules.auth.schemas.responses import LoginResponse, RefreshTokenResponse
from app.modules.auth.services.auth_service import AuthService
from app.modules.user.models.user_model import User


@pytest.fixture
def auth_service():
    with (
        patch(
            'app.modules.auth.services.auth_service.UserService'
        ) as mock_user_service,
        patch('app.modules.auth.services.auth_service.jwt_handler') as mock_jwt_handler,
    ):
        service = AuthService()
        service.user_service = mock_user_service.return_value
        yield service, service.user_service, mock_jwt_handler


def test_authenticate_user_success(auth_service):
    # Arrange
    service, mock_user_service, _ = auth_service
    db_session = MagicMock()
    user = User(id=uuid4(), email='test@example.com', password='password')
    mock_user_service.get_user_by_email.return_value = user

    # Act
    result = service.authenticate_user('test@example.com', 'password', db_session)

    # Assert
    assert result.email == user.email
    mock_user_service.get_user_by_email.assert_called_once_with(
        db=db_session, email='test@example.com'
    )


def test_authenticate_user_not_found(auth_service):
    # Arrange
    service, mock_user_service, _ = auth_service
    db_session = MagicMock()
    mock_user_service.get_user_by_email.return_value = None

    # Act & Assert
    with pytest.raises(AppException) as exc_info:
        service.authenticate_user('test@example.com', 'password', db_session)

    assert exc_info.value.error_constant == ErrorConstant.NOT_FOUND


def test_authenticate_user_wrong_password(auth_service):
    # Arrange
    service, mock_user_service, _ = auth_service
    db_session = MagicMock()
    user = User(id=uuid4(), email='test@example.com', password='wrong_password')
    mock_user_service.get_user_by_email.return_value = user

    # Act & Assert
    with pytest.raises(AppException) as exc_info:
        service.authenticate_user('test@example.com', 'password', db_session)

    assert exc_info.value.error_constant == ErrorConstant.UNAUTHORIZED


def test_login(auth_service):
    # Arrange
    service, mock_user_service, mock_jwt_handler = auth_service
    db_session = MagicMock()
    user = User(
        id=uuid4(),
        email='test@example.com',
        first_name='Test',
        last_name='User',
        password='password',
    )

    # Mock authenticate_user to return the user
    service.authenticate_user = MagicMock(return_value=user)

    mock_jwt_handler.create_access_token.return_value = 'access_token'
    mock_jwt_handler.create_refresh_token.return_value = 'refresh_token'
    mock_jwt_handler.access_token_expire_minutes = 30

    # Act
    result = service.login('test@example.com', 'password', db_session)

    # Assert
    assert isinstance(result, LoginResponse)
    assert result.access_token == 'access_token'
    assert result.refresh_token == 'refresh_token'
    service.authenticate_user.assert_called_once_with(
        email='test@example.com', password='password', db=db_session
    )


def test_refresh_token(auth_service):
    # Arrange
    service, _, mock_jwt_handler = auth_service
    mock_jwt_handler.refresh_access_token.return_value = 'new_access_token'
    mock_jwt_handler.access_token_expire_minutes = 30

    # Act
    result = service.refresh_token('refresh_token')

    # Assert
    assert isinstance(result, RefreshTokenResponse)
    assert result.access_token == 'new_access_token'
    mock_jwt_handler.refresh_access_token.assert_called_once_with('refresh_token')
