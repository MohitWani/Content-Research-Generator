from sqlalchemy.orm import Session

from app.common.constants.error_constant import ErrorConstant
from app.core.auth.jwt_handler import jwt_handler
from app.core.exception.app_exception import AppException
from app.modules.auth.schemas.responses import LoginResponse, RefreshTokenResponse
from app.modules.user.models.user_model import User
from app.modules.user.services.user_service import UserService


class AuthService:
    def __init__(self):
        self.user_service = UserService()

    def authenticate_user(self, email: str, password: str, db: Session) -> User:
        user = self.user_service.get_user_by_email(db=db, email=email)

        if not user:
            raise AppException(ErrorConstant.NOT_FOUND)

        if user.password != password:
            raise AppException(ErrorConstant.UNAUTHORIZED)

        return user

    def login(self, email: str, password: str, db: Session) -> LoginResponse:
        user = self.authenticate_user(email=email, password=password, db=db)

        access_token = jwt_handler.create_access_token(
            {'user_id': str(user.id), 'email': user.email}
        )

        refresh_token = jwt_handler.create_refresh_token(
            {'user_id': str(user.id), 'email': user.email}
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer',
            expires_in=jwt_handler.access_token_expire_minutes * 60,
            user_id=str(user.id),
        )

    def refresh_token(self, refresh_token: str) -> RefreshTokenResponse:
        new_access_token = jwt_handler.refresh_access_token(refresh_token)

        return RefreshTokenResponse(
            access_token=new_access_token,
            token_type='bearer',
            expires_in=jwt_handler.access_token_expire_minutes * 60,
        )


# Global instance
auth_service = AuthService()
