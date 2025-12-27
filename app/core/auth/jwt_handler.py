from datetime import datetime, timedelta
from typing import Any

import jwt
from pydantic import BaseModel

from app.common.constants.error_constant import ErrorConstant
from app.core.auth.jwks_service import jwks_service
from app.core.exception.app_exception import AppException


class TokenData(BaseModel):
    user_id: str
    exp: datetime


class JWTHandler:
    def __init__(self):
        self.algorithm = 'RS256'
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def create_access_token(self, data: dict[str, Any]) -> str:
        """Create an access token with the given data."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({'exp': expire, 'type': 'access'})

        private_key = jwks_service.getPrivateKey()
        encoded_jwt = jwt.encode(to_encode, private_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: dict[str, Any]) -> str:
        """Create a refresh token with the given data."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({'exp': expire, 'type': 'refresh'})

        private_key = jwks_service.getPrivateKey()
        encoded_jwt = jwt.encode(to_encode, private_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = 'access') -> TokenData:
        """Verify and decode a JWT token."""
        try:
            public_key = jwks_service.getPublicKey()
            payload = jwt.decode(token, public_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get('type') != token_type:
                raise AppException(ErrorConstant.UNAUTHORIZED)

            # Check if token is expired
            exp = payload.get('exp')
            if exp is None:
                raise AppException(ErrorConstant.UNAUTHORIZED)

            if datetime.utcnow() > datetime.fromtimestamp(exp):
                raise AppException(ErrorConstant.UNAUTHORIZED)

            return TokenData(
                user_id=payload.get('user_id'),
                exp=datetime.fromtimestamp(exp),
            )

        except Exception as e:
            raise AppException(ErrorConstant.UNAUTHORIZED) from e

    def refresh_access_token(self, refresh_token: str) -> str:
        """Create a new access token using a valid refresh token."""
        token_data = self.verify_token(refresh_token, 'refresh')

        # Create new access token with the same user data
        new_access_token = self.create_access_token({'user_id': token_data.user_id})

        return new_access_token


# Global instance
jwt_handler = JWTHandler()
