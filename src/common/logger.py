"""
Logging configuration for AI Research Agent System
"""
import logging
import sys
from src.common.config import config


def setup_logger(name: str = None) -> logging.Logger:
    """
    Set up and return a logger instance
    
    Args:
        name: Logger name (defaults to root logger)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        # Formatter
        formatter = logging.Formatter(config.LOG_FORMAT)
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger


# Default application logger
logger = setup_logger("research_agent")

