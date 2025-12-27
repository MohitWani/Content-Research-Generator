# Caching Mechanism

## Overview

This project includes a flexible and extensible caching mechanism designed to improve performance by storing frequently accessed data in memory. The caching system is built around a `CacheManager` that provides a configurable cache provider.

## Core Components

- **CacheManager**: A singleton class responsible for creating and providing a cache provider instance based on the application's configuration.
- **CacheInterface**: An abstract base class that defines the contract for all cache providers. This allows for easy extension with new caching backends.
- **AioCacheProvider**: The default implementation of the `CacheInterface`, which uses the `aiocache` library with a simple in-memory cache.
- **CustomJsonSerializer**: A custom serializer that extends `aiocache`'s `JsonSerializer` to handle Pydantic models, SQLAlchemy models, and datetime objects.

## Configuration

The caching system is configured through the following environment variables:

- `CACHE_PROVIDER`: The cache provider to use. Currently, only `aiocache` is supported.
- `CACHE_TTL_SECONDS`: The default time-to-live (TTL) for cache entries in seconds.

### Example `.env` configuration:

```bash
CACHE_PROVIDER=aiocache
CACHE_TTL_SECONDS=300
```

## How It Works

1. **Initialization**: The `CacheManager` is initialized when the application starts. It reads the `CACHE_PROVIDER` from the environment settings and creates the corresponding cache provider instance.
2. **Provider Selection**: Currently, the system only supports `aiocache` as a provider. If `CACHE_PROVIDER` is set to `aiocache`, an `AioCacheProvider` is instantiated.
3. **`aiocache` Configuration**: The `AioCacheProvider` is configured with a `SimpleMemoryCache` and the `CustomJsonSerializer`. The default TTL is set from the `CACHE_TTL_SECONDS` environment variable.
4. **Dependency Injection**: The configured cache provider is made available for dependency injection throughout the application.

## Usage

To use the cache in your services or repositories, you can inject the `cache_provider` instance from `app.core.cache.cache_manager`.

### Example:

```python
from app.core.cache.cache_manager import cache_provider

class MyService:
    async def get_data(self, user_id: int):
        cache_key = f"user_data_{user_id}"

        # Define a function to fetch the data from the database
        async def fetch_from_db():
            # Your database query logic here
            return await get_user_from_db(user_id)

        # Use the cache_and_retrieve method to get data from the cache or
        # fetch it from the database and cache it if it doesn't exist.
        user_data = await cache_provider.cache_and_retrieve(
            key=cache_key,
            func=fetch_from_db,
            ttl=600  # Optional: override the default TTL
        )

        return user_data
```

### Available Methods

The `CacheInterface` (and `AioCacheProvider`) provides the following methods:

- `get(key: str)`: Retrieve an item from the cache.
- `set(key: str, value: Any, ttl: int = None)`: Add an item to the cache with an optional TTL.
- `delete(key: str)`: Remove an item from the cache.
- `exists(key: str)`: Check if an item exists in the cache.
- `cache_and_retrieve(key: str, func: Callable[[], Coroutine[Any, Any, Any]], ttl: int = None)`: A convenient method that tries to get a key from the cache and, if it doesn't exist, calls the provided function to get the result, caches it, and returns it.
- `get_cache_client()`: Returns the underlying cache client instance (`aiocache` in this case).

## Extending the System

To add a new cache provider (e.g., Redis), you would need to:

1.  Create a new class that implements the `CacheInterface`.
2.  Implement the abstract methods defined in the interface.
3.  Update the `CacheManager` to recognize and instantiate your new provider based on the `CACHE_PROVIDER` environment variable.
