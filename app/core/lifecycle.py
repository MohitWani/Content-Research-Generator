from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.common.constants.app_constant import banner
from app.core.config.environment_config import settings
from app.core.logging.logger import logger
from migrations.alembic_migrarion import run_migrations


class ApplicationLifecycleManager:
    async def _run_migrations(self, app: FastAPI) -> None:
        if settings.ENABLE_DB_MIGRATIONS:
            run_migrations()
            logger.info('Database migrations completed')

    async def startup(self, app: FastAPI) -> None:
        logger.info(banner)
        await self._run_migrations(app)
        # add other startup function calls here

    async def shutdown(self, app: FastAPI) -> None:
        logger.info('App is shutting down...')
        # add other shutdown function calls here

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        await self.startup(app)
        yield
        await self.shutdown(app)


lifecycle_manager = ApplicationLifecycleManager()
