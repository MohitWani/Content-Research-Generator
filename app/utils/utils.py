import logging
from pathlib import Path

import colorlog


def setup_logging(log_dir: str = 'logs') -> None:
    """
    Set up logging configuration with color formatting.

    Args:
        log_dir: Directory to store log files
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Create handlers
    file_handler = logging.FileHandler(
        log_path / 'marketing_review.log', encoding='utf-8'
    )
    console_handler = colorlog.StreamHandler()

    # Create formatters and add it to handlers
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_format = colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s:%(name)s:%(message)s'
    )

    file_handler.setFormatter(file_format)
    console_handler.setFormatter(console_format)

    # Add handlers to the logger
    logger = logging.getLogger()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
