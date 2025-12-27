from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.modules.auth.schemas.requests import LoginRequest, RefreshTokenRequest
from app.modules.auth.schemas.responses import LoginResponse, RefreshTokenResponse
from app.modules.auth.services.auth_service import AuthService
from database.database import get_db

auth_router = APIRouter(tags=['Authentication'])


@auth_router.post(
    '/login', response_model=LoginResponse, status_code=status.HTTP_200_OK
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(AuthService),
    db: Session = Depends(get_db),
):
    return auth_service.login(request.email, request.password, db)


@auth_router.post(
    '/refresh', response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(AuthService),
):
    return auth_service.refresh_token(request.refresh_token)
