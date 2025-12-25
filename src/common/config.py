"""
Configuration management for AI Research Agent System
Loads configuration from environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    """Application configuration from environment variables"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    RESEARCH_DIR = DATA_DIR / "research"
    CONTENT_DIR = DATA_DIR / "content"
    PROFILE_DIR = DATA_DIR / "profile"
    VOICE_PROFILE_PATH = PROFILE_DIR / "voice.json"
    
    # Database configuration
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/research_db"
    )
    
    # Sync database URL for Alembic
    DATABASE_URL_SYNC = os.getenv(
        "DATABASE_URL_SYNC",
        "postgresql://postgres:postgres@localhost:5432/research_db"
    )
    
    # AWS Bedrock configuration
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    BEDROCK_MODEL_ID = os.getenv(
        "BEDROCK_MODEL_ID",
        "anthropic.claude-3-5-sonnet-20241022-v2:0"
    )
    BEDROCK_MAX_TOKENS = int(os.getenv("BEDROCK_MAX_TOKENS", "8000"))
    BEDROCK_TEMPERATURE = float(os.getenv("BEDROCK_TEMPERATURE", "0.7"))
    
    # External API configuration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    ARXIV_BASE_URL = os.getenv("ARXIV_BASE_URL", "http://export.arxiv.org/api/query")
    HN_BASE_URL = os.getenv("HN_BASE_URL", "https://hacker-news.firebaseio.com/v0")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    
    # Rate limiting
    LLM_RATE_LIMIT_RPM = int(os.getenv("LLM_RATE_LIMIT_RPM", "60"))  # Requests per minute
    EXTERNAL_API_RATE_LIMIT_RPS = float(os.getenv("EXTERNAL_API_RATE_LIMIT_RPS", "1.0"))  # Requests per second
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Application settings
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"


# Create singleton instance
config = Config()

