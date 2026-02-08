"""
Research schemas for API request/response validation and agent data structures.
"""
# API Schemas
from app.modules.research.schemas.research_schemas import (
    ContentTypeEnum,
    ErrorResponse,
    ResearchQueryRequest,
    ResearchQueryResponse,
    ResearchResultResponse,
    ResearchStatusResponse,
    SourceSchema,
    StatusEnum,
    TargetAudienceEnum,
    TopicCategorizationResult,
    TopicCategoryEnum,
)

# Agent Schemas
from app.modules.research.schemas.agent_schemas import (
    AgentConfig,
    ParsedAgentResponse,
    ResearchOutput,
    ResearchRequest,
    ToolCallSchema,
    ToolResultSchema,
)

__all__ = [
    # API Enums
    "TopicCategoryEnum",
    "TargetAudienceEnum",
    "ContentTypeEnum",
    "StatusEnum",
    # API Request/Response
    "ResearchQueryRequest",
    "ResearchQueryResponse",
    "ResearchStatusResponse",
    "SourceSchema",
    "ResearchResultResponse",
    "TopicCategorizationResult",
    "ErrorResponse",
    # Agent Schemas
    "ResearchOutput",
    "ToolCallSchema",
    "ToolResultSchema",
    "ParsedAgentResponse",
    "AgentConfig",
    "ResearchRequest",
]
