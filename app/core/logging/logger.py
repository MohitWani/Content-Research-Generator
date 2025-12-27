import sys
from datetime import datetime
from pathlib import Path

from loguru import logger as loguru_logger

from app.core.config.environment_config import settings

LOG_PATH = Path(settings.LOG_PATH_PREFIX)
LOG_PATH.mkdir(parents=True, exist_ok=True)


def setup_logger():
    # Remove the default Loguru handler
    loguru_logger.remove()

    # Console logger for development with pretty formatting
    loguru_logger.add(
        sys.stdout,
        format=(
            '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
            '<level>{level: <8}</level> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - '
            '<level>{message}</level>'
        ),
        level=settings.LOG_LEVEL,
        colorize=True,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # File logger with rotation and retention for production
    # Get current date string, e.g., 2025-07-16
    current_date = datetime.now().strftime('%Y-%m-%d')
    loguru_logger.add(
        f'{settings.LOG_PATH_PREFIX}/{settings.ENV_NAME}/application-{current_date}.log',
        rotation=settings.LOG_ROTATION,  # Rotate after 10 MB
        retention=settings.LOG_RETENTION,  # Keep logs for 7 days
        compression=settings.LOG_COMPRESSION_TYPE,  # Compress rotated logs
        level=settings.LOG_LEVEL,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    return loguru_logger


logger = setup_logger()
