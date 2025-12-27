"""
Tests for the simplified application lifecycle management system.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI

from app.core.config.environment_config import settings
from app.core.lifecycle import ApplicationLifecycleManager


@pytest.fixture
def mock_app():
    """Create a mock FastAPI app"""
    return MagicMock(spec=FastAPI)


@pytest.mark.asyncio
async def test_run_migrations_enabled(mock_app):
    """Test that migrations run when enabled"""
    with patch('app.core.lifecycle.run_migrations') as mock_run_migrations:
        settings.ENABLE_DB_MIGRATIONS = True
        manager = ApplicationLifecycleManager()
        await manager._run_migrations(mock_app)
        mock_run_migrations.assert_called_once()


@pytest.mark.asyncio
async def test_run_migrations_disabled(mock_app):
    """Test that migrations do not run when disabled"""
    with patch('app.core.lifecycle.run_migrations') as mock_run_migrations:
        settings.ENABLE_DB_MIGRATIONS = False
        manager = ApplicationLifecycleManager()
        await manager._run_migrations(mock_app)
        mock_run_migrations.assert_not_called()


@pytest.mark.asyncio
async def test_startup_method(mock_app):
    """Test the startup method"""
    with (
        patch('app.core.lifecycle.logger') as mock_logger,
        patch.object(
            ApplicationLifecycleManager, '_run_migrations', new_callable=AsyncMock
        ) as mock_run_migrations,
    ):
        manager = ApplicationLifecycleManager()
        await manager.startup(mock_app)
        mock_logger.info.assert_called()
        mock_run_migrations.assert_called_once_with(mock_app)


@pytest.mark.asyncio
async def test_shutdown_method(mock_app):
    """Test the shutdown method"""
    with patch('app.core.lifecycle.logger') as mock_logger:
        manager = ApplicationLifecycleManager()
        await manager.shutdown(mock_app)
        mock_logger.info.assert_called_with('App is shutting down...')


@pytest.mark.asyncio
async def test_lifespan_context_manager(mock_app):
    """Test the lifespan context manager"""
    manager = ApplicationLifecycleManager()
    with (
        patch.object(manager, 'startup', new_callable=AsyncMock) as mock_startup,
        patch.object(manager, 'shutdown', new_callable=AsyncMock) as mock_shutdown,
    ):
        async with manager.lifespan(mock_app):
            mock_startup.assert_called_once_with(mock_app)
            mock_shutdown.assert_not_called()
        mock_shutdown.assert_called_once_with(mock_app)
