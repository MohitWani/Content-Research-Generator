from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    # Application Configurations
    APP_NAME: str = 'ai-research-agent'
    ENV_NAME: str = 'local'
    APP_VERSION: str = '0.1.0'
    APP_HOST: str = '127.0.0.1'
    APP_PORT: int = 8000

    # Logging Configuration
    LOG_LEVEL: str = 'INFO'
    LOG_PATH_PREFIX: str = './logs'
    LOG_ROTATION: str = '10 MB'
    LOG_RETENTION: str = '7 days'
    LOG_COMPRESSION_TYPE: str = 'zip'

    # Database Configuration
    DATABASE_URL: str = 'postgresql://postgres:postgres@localhost:5432/research_db'
    DATABASE_URL_SYNC: str = 'postgresql://postgres:postgres@localhost:5432/research_db'

    # Module enable
    MODULE_NAMES: str = "['health', 'user', 'auth', 'research', 'paper', 'content', 'social', 'branding', 'pipelines']"

    # DB Migration
    ENABLE_DB_MIGRATIONS: bool = True

    # Rate Limiter
    RATE_LIMIT_CONFIG: str = '{"global": {"counts": 60, "time": 60}}'

    # Public Paths (includes all research, paper, content endpoints for testing)
    PUBLIC_ENDPOINTS: str = '[{"endpoint":"/docs","method":"GET"},{"endpoint":"/redoc","method":"GET"},{"endpoint":"/openapi.json","method":"GET"},{"endpoint":"/api/v1/user","method":"POST"},{"endpoint":"/api/v1/auth/login","method":"POST"},{"endpoint":"/api/v1/auth/refresh","method":"POST"},{"endpoint":"/.well-known/jwks.json","method":"GET"},{"endpoint":"/api/health","method":"GET"},{"endpoint":"/api/v1/research/query","method":"POST"},{"endpoint":"/api/v1/research/query/sync","method":"POST"},{"endpoint":"/api/v1/research/queries","method":"GET"},{"endpoint":"/api/v1/paper/search","method":"POST"},{"endpoint":"/api/v1/paper/research/sync","method":"POST"},{"endpoint":"/api/v1/paper/full/sync","method":"POST"},{"endpoint":"/api/v1/paper/research/multiple/sync","method":"POST"},{"endpoint":"/api/v1/content/generate-blog","method":"POST"},{"endpoint":"/api/v1/content/generate-blog/sync","method":"POST"},{"endpoint":"/api/v1/content/full-pipeline","method":"POST"},{"endpoint":"/api/v1/content/","method":"GET"},{"endpoint":"/api/v1/social/linkedin","method":"POST"},{"endpoint":"/api/v1/social/twitter/thread","method":"POST"},{"endpoint":"/api/v1/social/from-blog","method":"POST"},{"endpoint":"/api/v1/branding/apply","method":"POST"},{"endpoint":"/api/v1/branding/check-alignment","method":"POST"},{"endpoint":"/api/v1/branding/voice-profile","method":"GET"},{"endpoint":"/api/v1/branding/guidelines","method":"GET"},{"endpoint":"/api/v1/pipelines/full","method":"POST"},{"endpoint":"/api/v1/pipelines/full/async","method":"POST"},{"endpoint":"/api/v1/pipelines/research-only","method":"POST"}]'

    # Public and Private Keys
    PRIVATE_KEY: str = ''
    PUBLIC_KEY: str = ''

    # Cache Configuration
    CACHE_PROVIDER: str = 'aiocache'
    CACHE_TTL_SECONDS: int = 3600

    # AWS Bedrock Configuration
    AWS_REGION: str = 'us-east-1'
    AWS_ACCESS_KEY_ID: str = ''
    AWS_SECRET_ACCESS_KEY: str = ''
    BEDROCK_MODEL_ID: str = ''
    BEDROCK_MAX_TOKENS: int = 8000
    BEDROCK_TEMPERATURE: float = 0.7

    # External API Configuration
    GITHUB_TOKEN: str = ''
    ARXIV_BASE_URL: str = 'http://export.arxiv.org/api/query'
    HN_BASE_URL: str = 'https://hacker-news.firebaseio.com/v0'
    TAVILY_API_KEY: str = ''

    # Rate Limiting
    LLM_RATE_LIMIT_RPM: int = 60
    EXTERNAL_API_RATE_LIMIT_RPS: float = 1.0

    # Project Paths
    @property
    def PROJECT_ROOT(self) -> Path:
        return Path(__file__).parent.parent.parent.parent

    @property
    def DATA_DIR(self) -> Path:
        return self.PROJECT_ROOT / 'data'

    @property
    def RESEARCH_DIR(self) -> Path:
        return self.DATA_DIR / 'research'

    @property
    def CONTENT_DIR(self) -> Path:
        return self.DATA_DIR / 'content'

    @property
    def PROFILE_DIR(self) -> Path:
        return self.DATA_DIR / 'profile'

    @property
    def VOICE_PROFILE_PATH(self) -> Path:
        return self.PROFILE_DIR / 'voice.json'


settings = Settings()
