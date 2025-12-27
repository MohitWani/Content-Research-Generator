import json
from datetime import datetime

from aiocache.serializers import JsonSerializer
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

from app.common.constants.error_constant import ErrorConstant
from app.core.cache.aiocache_provider import AioCacheProvider
from app.core.cache.cache_interface import CacheInterface
from app.core.config.environment_config import settings
from app.core.exception.app_exception import AppException


class CustomJsonSerializer(JsonSerializer):
    def default_encoder(self, o):
        if isinstance(o, dict):
            return o
        if isinstance(o, BaseModel):
            return o.model_dump()
        if isinstance(o, DeclarativeBase):
            # Handle SQLAlchemy models
            return {
                column.name: getattr(o, column.name) for column in o.__table__.columns
            }
        if isinstance(o, datetime):
            return o.isoformat()
        raise AppException(
            ErrorConstant.INTERNAL_SERVER_ERROR,
            f'Object of type {o.__class__.__name__} is not JSON serializable',
        )

    def dumps(self, value):
        return json.dumps(value, default=self.default_encoder)


class CacheManager:
    _cache_provider: CacheInterface = None

    @classmethod
    def get_cache_provider(cls) -> CacheInterface:
        if cls._cache_provider is None and settings.CACHE_PROVIDER == 'aiocache':
            config = {
                'default': {
                    'cache': 'aiocache.SimpleMemoryCache',
                    'serializer': {
                        'class': 'app.core.cache.cache_manager.CustomJsonSerializer',
                    },
                    'ttl': settings.CACHE_TTL_SECONDS,
                }
            }
            cls._cache_provider = AioCacheProvider(config)
            return cls._cache_provider
        raise AppException(
            ErrorConstant.INTERNAL_SERVER_ERROR,
            f'Unsupported cache provider: {settings.CACHE_PROVIDER}',
        )
