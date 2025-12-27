from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any


class CacheInterface(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def cache_and_retrieve(
        self, key: str, func: Callable[[], Coroutine[Any, Any, Any]], ttl: int = None
    ) -> Any:
        pass

    @abstractmethod
    def get_cache_client(self) -> Any:
        pass
