"""
Database models and Pydantic schemas for AI Research Agent System
"""
from src.lib.models.research import (
    TopicCategory,
    ResearchQuery,
    ResearchResult,
    ContentItem,
    PipelineExecution,
)
from src.lib.models.exceptions import (
    AIResearchAgentError,
    QueryCategorizationError,
    ResearchDataInsufficientError,
    RateLimitExceededError,
    ExternalAPIError,
    ContentGenerationError,
    BlogGenerationError,
    PipelineError,
    ConfigurationError,
    LLMError,
)
from src.lib.models.schemas import (
    TopicCategoryEnum,
    TargetAudienceEnum,
    ContentTypeEnum,
    StatusEnum,
    ResearchQueryRequest,
    ResearchQueryResponse,
    ResearchStatusResponse,
    SourceSchema,
    ResearchResultResponse,
    BlogGenerationRequest,
    BlogGenerationResponse,
    ContentItemResponse,
    ContentListResponse,
    PipelineExecutionResponse,
    PipelineStatusResponse,
    BlogPipelineRequest,
    TopicCategorizationResult,
    ErrorResponse,
    ValidationErrorResponse,
)
from src.lib.models.repository import ResearchRepository

__all__ = [
    # SQLAlchemy Models
    "TopicCategory",
    "ResearchQuery",
    "ResearchResult",
    "ContentItem",
    "PipelineExecution",
    # Exceptions
    "AIResearchAgentError",
    "QueryCategorizationError",
    "ResearchDataInsufficientError",
    "RateLimitExceededError",
    "ExternalAPIError",
    "ContentGenerationError",
    "BlogGenerationError",
    "PipelineError",
    "ConfigurationError",
    "LLMError",
    # Pydantic Schemas - Enums
    "TopicCategoryEnum",
    "TargetAudienceEnum",
    "ContentTypeEnum",
    "StatusEnum",
    # Pydantic Schemas - Research
    "ResearchQueryRequest",
    "ResearchQueryResponse",
    "ResearchStatusResponse",
    "SourceSchema",
    "ResearchResultResponse",
    # Pydantic Schemas - Content
    "BlogGenerationRequest",
    "BlogGenerationResponse",
    "ContentItemResponse",
    "ContentListResponse",
    # Pydantic Schemas - Pipeline
    "PipelineExecutionResponse",
    "PipelineStatusResponse",
    "BlogPipelineRequest",
    # Pydantic Schemas - Agent Results
    "TopicCategorizationResult",
    # Pydantic Schemas - Errors
    "ErrorResponse",
    "ValidationErrorResponse",
    # Repository
    "ResearchRepository",
]
