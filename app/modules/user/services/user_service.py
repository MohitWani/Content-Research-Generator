from sqlalchemy.orm import Session

from app.common.constants.error_constant import ErrorConstant
from app.core.cache.cache_manager import CacheManager
from app.core.exception.app_exception import AppException
from app.core.logging.logger import logger
from app.modules.user.models.user_model import User
from app.modules.user.repositories.user_repository import UserRepository
from app.modules.user.schemas.user_schemas import CreateUserRequest


class UserService:
    def __init__(self):
        self.repository = UserRepository()
        self.cache_provider = CacheManager.get_cache_provider()

    def create_user(self, db: Session, user_data: CreateUserRequest) -> User:
        logger.info(f'Creating user with email: {user_data.email}')

        # Check if user with email already exists
        existing_user = self.repository.get_user_by_email(db=db, email=user_data.email)
        if existing_user:
            logger.warning(f'User with email {user_data.email} already exists')
            raise AppException(ErrorConstant.CONFLICT)

        # Create new user
        user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=user_data.password,  # In production, this should be hashed
        )

        created_user = self.repository.create_user(db=db, user=user)
        logger.info(f'Created user with ID: {created_user.id}')

        return created_user

    def _get_user_from_db(self, db: Session, user_id: str) -> User | None:
        return self.repository.get_user_by_id(db=db, user_id=user_id) or None

    async def get_user_by_id(self, db: Session, user_id: str) -> User | None:
        cached_user_data = await self.cache_provider.cache_and_retrieve(
            key=f'user_{user_id}',
            func=lambda: self._get_user_from_db(db=db, user_id=user_id),
        )

        return cached_user_data or None

    def get_user_by_email(self, db: Session, email: str) -> User:
        return self.repository.get_user_by_email(db=db, email=email)
