from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.constants.error_constant import ErrorConstant
from app.core.exception.app_exception import AppException
from app.core.logging.logger import logger
from app.modules.user.schemas.user_schemas import CreateUserRequest, UserResponse
from app.modules.user.services.user_service import UserService
from database.database import get_db

user_router = APIRouter(tags=['User Module'])


@user_router.get('', response_model=UserResponse)
async def get_user(
    request: Request,
    user_service: UserService = Depends(UserService),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user.
    Requires Bearer JWT token in Authorization header.
    """

    # Get user ID from JWT token
    user_id = request.state.user['user_id']
    logger.info(f'User ID: {user_id}')
    logger.info(f'Request: {request}')

    # Get user by ID
    user = user_service.get_user_by_id(db=db, user_id=user_id)
    if not user:
        raise AppException(ErrorConstant.NOT_FOUND)

    return user


@user_router.post('', response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    user_service: UserService = Depends(UserService),
    db: Session = Depends(get_db),
):
    user = user_service.get_user_by_email(db=db, email=user_data.email)

    if user:
        raise AppException(ErrorConstant.BAD_REQUEST)

    user = user_service.create_user(db=db, user_data=user_data)

    return user
