# Application Lifecycle Management

This document describes the application lifecycle management system that provides expandable functions for startup and shutdown operations.

## Overview

The lifecycle management system replaces the simple `lifespan` function with a clean, simple approach that provides dedicated startup and shutdown methods. This makes the application more maintainable and expandable.

## Architecture

### Core Components

1. **`ApplicationLifecycleManager`** - Simple class with startup and shutdown methods
2. **Built-in Functions** - Default functions for common operations

### Key Features

- **Simple**: Clean, straightforward approach
- **Expandable**: Easy to add function calls in startup and shutdown methods
- **Maintainable**: Clear separation of startup and shutdown logic
- **Type Safe**: Full type hints for better IDE support

## Usage

### Basic Usage

The lifecycle manager provides two main methods:

- **`startup(app)`** - Executes startup operations:

  - Displays application banner
  - Runs database migrations (if enabled)
  - Placeholder for additional startup function calls

- **`shutdown(app)`** - Executes shutdown operations:
  - Logs shutdown information
  - Placeholder for additional shutdown function calls

### Adding Custom Functions

To add custom startup or shutdown functions, simply add the function calls directly in the `startup()` or `shutdown()` methods:

```python
# In app/core/lifecycle.py
async def startup(self, app: FastAPI) -> None:
    logger.info(banner)
    await self._run_migrations(app)
    await self._setup_database_connections(app)  # Add your function call here
    await self._warmup_caches(app)  # Add your function call here
    # add other startup function calls here

async def shutdown(self, app: FastAPI) -> None:
    logger.info('App is shutting down...')
    await self._cleanup_resources(app)  # Add your function call here
    await self._close_connections(app)  # Add your function call here
    # add other shutdown function calls here
```

### Conditional Functions

```python
async def _conditional_startup(self, app: FastAPI) -> None:
    from app.core.config.environment_config import settings

    if settings.ENABLE_DB_MIGRATIONS:
        # Execute only when feature is enabled
        logger.info("Conditional operation executed")
        await self._setup_database_connections(app)
```

### Function Dependencies

```python
async def _dependent_startup(self, app: FastAPI) -> None:
    # Ensure dependency runs first
    await self._setup_database_connections(app)
    # Your dependent logic here
    await self._warmup_caches(app)
```

## Configuration

### Adding Functions to Lifecycle Manager

You can add functions directly in the lifecycle manager:

```python
# In app/core/lifecycle.py
class ApplicationLifecycleManager:
    async def _setup_database_connections(self, app: FastAPI) -> None:
        logger.info('Setting up database connections...')
        # Add your database connection logic here

    async def _warmup_caches(self, app: FastAPI) -> None:
        logger.info('Warming up caches...')
        # Add your cache warmup logic here

    async def startup(self, app: FastAPI) -> None:
        logger.info(banner)
        await self._run_migrations(app)
        await self._setup_database_connections(app)  # Add your function call
        await self._warmup_caches(app)  # Add your function call
        # add other startup function calls here
```

### Environment-based Configuration

```python
async def _conditional_startup(self, app: FastAPI) -> None:
    from app.core.config.environment_config import settings

    if settings.ENABLE_CACHE_WARMUP:
        await self._warmup_caches(app)

    if settings.ENABLE_GRACEFUL_SHUTDOWN:
        await self._setup_graceful_shutdown(app)
```

## Error Handling

The lifecycle manager provides simple error handling:

- **Startup Errors**: If a startup function fails, the application startup is aborted
- **Shutdown Errors**: If a shutdown function fails, the shutdown process continues
- **Logging**: All operations are logged for debugging

## Best Practices

1. **Keep Functions Focused**: Each function should have a single responsibility
2. **Handle Errors Gracefully**: Implement proper error handling in your functions
3. **Use Descriptive Names**: Name your functions clearly to indicate their purpose
4. **Test Functions**: Write unit tests for your custom functions
5. **Add Functions in Order**: Add function calls in the order you want them to execute

## Migration from Old System

The old `lifespan` function has been replaced with the lifecycle manager. The functionality remains the same, but now it's more expandable:

### Before (Old System)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.ENABLE_DB_MIGRATIONS:
        run_migrations()
    display_banner()
    yield
    # Shutdown
    logger.info('App is shutting down...')
```

### After (New System)

```python
# The same functionality is now handled by the lifecycle manager
# with better separation of concerns and expandability
```

## Examples

Here's a complete example of how to extend the lifecycle manager:

```python
# In app/core/lifecycle.py
class ApplicationLifecycleManager:
    async def _setup_database_connections(self, app: FastAPI) -> None:
        logger.info('Setting up database connections...')
        # Your database connection logic here

    async def _warmup_caches(self, app: FastAPI) -> None:
        logger.info('Warming up caches...')
        # Your cache warmup logic here

    async def _cleanup_resources(self, app: FastAPI) -> None:
        logger.info('Cleaning up resources...')
        # Your cleanup logic here

    async def startup(self, app: FastAPI) -> None:
        logger.info(banner)
        await self._run_migrations(app)
        await self._setup_database_connections(app)
        await self._warmup_caches(app)
        # add other startup function calls here

    async def shutdown(self, app: FastAPI) -> None:
        logger.info('App is shutting down...')
        await self._cleanup_resources(app)
        # add other shutdown function calls here
```

## Testing

When testing your application, you can create mock functions or override methods for testing purposes:

```python
# In tests
class MockLifecycleManager(ApplicationLifecycleManager):
    async def _run_migrations(self, app: FastAPI) -> None:
        # Mock implementation for testing
        pass
```
