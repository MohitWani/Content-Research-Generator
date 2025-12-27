from collections.abc import Callable, Coroutine
from typing import Any

from aiocache import caches

from app.core.cache.cache_interface import CacheInterface


class AioCacheProvider(CacheInterface):
    def __init__(self, config: dict[str, Any]):
        caches.set_config(config)
        self.cache = caches.get('default')

    async def get(self, key: str) -> Any:
        return await self.cache.get(key)

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        await self.cache.set(key, value, ttl=ttl)

    async def delete(self, key: str) -> None:
        await self.cache.delete(key)

    async def exists(self, key: str) -> bool:
        return await self.cache.exists(key)

    async def cache_and_retrieve(
        self, key: str, func: Callable[[], Coroutine[Any, Any, Any]], ttl: int = None
    ) -> Any:
        if await self.exists(key):
            return await self.get(key)

        result = await func()
        await self.set(key, result, ttl=ttl)
        return result

    def get_cache_client(self) -> Any:
        return self.cache
