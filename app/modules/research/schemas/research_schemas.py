"""
Pydantic schemas for Research API
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TopicCategoryEnum(str, Enum):
    """Topic category for research queries"""

    CORE_AI = 'core_ai'
    PRACTICAL_IMPLEMENTATION = 'practical_implementation'
    SOFTWARE_DEVELOPMENT = 'software_development'
    WEB_DEVELOPMENT = 'web_development'
    DEVOPS = 'devops'
    GENERAL_TECH = 'general_tech'


class TargetAudienceEnum(str, Enum):
    """Target audience for content generation"""

    BEGINNER = 'beginner'
    PRACTITIONER = 'practitioner'
    EXPERT = 'expert'


class ContentTypeEnum(str, Enum):
    """Type of content to generate"""

    BLOG = 'blog'
    LINKEDIN_POST = 'linkedin_post'
    SHORT_FORM = 'short_form'


class StatusEnum(str, Enum):
    """Status of query/content processing"""

    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


# ============= Research Query Schemas =============


class ResearchQueryRequest(BaseModel):
    """Request schema for submitting a research query"""

    query: str = Field(
        ...,
        description='The research query/topic to investigate',
        min_length=5,
        max_length=1000,
        examples=['Explain the attention mechanism in transformers'],
    )
    target_audience: Optional[TargetAudienceEnum] = Field(
        default=TargetAudienceEnum.PRACTITIONER,
        description='Target audience for the research output',
    )
    content_type: Optional[ContentTypeEnum] = Field(
        default=ContentTypeEnum.BLOG,
        description='Type of content to eventually generate',
    )


class ResearchQueryResponse(BaseModel):
    """Response schema for research query submission"""

    query_id: int = Field(..., description='Unique identifier for the query')
    status: StatusEnum = Field(..., description='Current status of the query')
    created_at: datetime = Field(..., description='Timestamp when query was created')

    model_config = ConfigDict(from_attributes=True)


class ResearchStatusResponse(BaseModel):
    """Response schema for research query status check"""

    id: int = Field(..., description='Query ID')
    query_text: str = Field(..., description='Original query text')
    topic_category: Optional[TopicCategoryEnum] = Field(
        default=TopicCategoryEnum.CORE_AI, description='Categorized topic type'
    )
    target_audience: Optional[str] = Field(
        TopicCategoryEnum.CORE_AI, description='Target audience'
    )
    status: StatusEnum = Field(..., description='Current processing status')
    created_at: datetime = Field(..., description='Creation timestamp')
    updated_at: datetime = Field(..., description='Last update timestamp')

    model_config = ConfigDict(from_attributes=True)


# ============= Research Result Schemas =============


class SourceSchema(BaseModel):
    """Schema for research source/citation"""

    type: Optional[str] = Field('web', description='Source type (paper, web, github)')
    title: Optional[str] = Field('Unknown', description='Source title')
    url: Optional[str] = Field(None, description='Source URL')
    authors: Optional[Any] = Field(None, description='Authors (for papers)')
    published: Optional[str] = Field(None, description='Publication date')

    model_config = {'extra': 'allow'}

    @field_validator('authors', mode='before')
    @classmethod
    def parse_authors(cls, v):
        """Convert authors string to list if needed"""
        if v is None:
            return None
        if isinstance(v, str):
            return [a.strip() for a in v.split(',') if a.strip()]
        if isinstance(v, list):
            return v
        return None


class ResearchResultResponse(BaseModel):
    """Response schema for research results"""

    query_id: int = Field(..., description='Associated query ID')
    topic_summary: Optional[str] = Field(None, description='Summary of the topic')
    key_concepts: Optional[Dict[str, Any]] = Field(
        None, description='Key concepts with explanations'
    )
    mathematical_foundations: Optional[str] = Field(
        None, description='Mathematical formulas and explanations'
    )
    historical_context: Optional[str] = Field(
        None, description='LLM-generated summary of all content fetched by research tools'
    )
    implementation_examples: Optional[str] = Field(None, description='Code examples')
    sources: Optional[List[SourceSchema]] = Field(
        None, description='Sources and citations'
    )
    research_data_path: Optional[str] = Field(
        None, description='Path to full research data file'
    )
    completeness_score: Optional[float] = Field(
        None, ge=0, le=1, description='Research completeness score (0-1)'
    )
    created_at: Optional[datetime] = Field(None, description='Creation timestamp')

    model_config = ConfigDict(from_attributes=True)


# ============= Topic Agent Schemas =============


class TopicCategorizationResult(BaseModel):
    """Result from topic categorization agent"""

    category: str = Field(
        ...,
        description='Categorized topic type (core_ai, practical_implementation, etc.)',
    )
    confidence: float = Field(..., ge=0, le=1, description='Confidence score')
    reasoning: Optional[str] = Field(None, description='Explanation for categorization')
    is_ai_related: bool = Field(False, description='Whether query is AI-related')


# ============= Error Schemas =============


class ErrorResponse(BaseModel):
    """Standard error response schema"""

    detail: str = Field(..., description='Error message')
    error_code: Optional[str] = Field(None, description='Error code')


