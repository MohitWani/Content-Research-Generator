"""
Pydantic schemas for API request/response validation
These schemas serve as the API contract (FastAPI auto-generates OpenAPI docs from these)
Maps to: plan.md → Section 7 (API Design)
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class TopicCategoryEnum(str, Enum):
    """Topic category for research queries"""
    CORE_AI = "core_ai"
    PRACTICAL_IMPLEMENTATION = "practical_implementation"


class TargetAudienceEnum(str, Enum):
    """Target audience for content generation"""
    BEGINNER = "beginner"
    PRACTITIONER = "practitioner"
    EXPERT = "expert"


class ContentTypeEnum(str, Enum):
    """Type of content to generate"""
    BLOG = "blog"
    LINKEDIN_POST = "linkedin_post"
    SHORT_FORM = "short_form"


class StatusEnum(str, Enum):
    """Status of query/content processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============= Research Query Schemas =============

class ResearchQueryRequest(BaseModel):
    """Request schema for submitting a research query"""
    query: str = Field(
        ...,
        description="The research query/topic to investigate",
        min_length=5,
        max_length=1000,
        examples=["Explain the attention mechanism in transformers"]
    )
    target_audience: Optional[TargetAudienceEnum] = Field(
        default=TargetAudienceEnum.PRACTITIONER,
        description="Target audience for the research output"
    )
    content_type: Optional[ContentTypeEnum] = Field(
        default=ContentTypeEnum.BLOG,
        description="Type of content to eventually generate"
    )


class ResearchQueryResponse(BaseModel):
    """Response schema for research query submission"""
    query_id: int = Field(..., description="Unique identifier for the query")
    status: StatusEnum = Field(..., description="Current status of the query")
    created_at: datetime = Field(..., description="Timestamp when query was created")
    
    model_config = ConfigDict(from_attributes=True)


class ResearchStatusResponse(BaseModel):
    """Response schema for research query status check"""
    id: int = Field(..., description="Query ID")
    query_text: str = Field(..., description="Original query text")
    topic_category: Optional[TopicCategoryEnum] = Field(
        None, 
        description="Categorized topic type"
    )
    target_audience: Optional[str] = Field(None, description="Target audience")
    status: StatusEnum = Field(..., description="Current processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# ============= Research Result Schemas =============

class SourceSchema(BaseModel):
    """Schema for research source/citation"""
    type: str = Field(..., description="Source type (paper, web, github)")
    title: str = Field(..., description="Source title")
    url: Optional[str] = Field(None, description="Source URL")
    authors: Optional[List[str]] = Field(None, description="Authors (for papers)")
    published: Optional[str] = Field(None, description="Publication date")


class ResearchResultResponse(BaseModel):
    """Response schema for research results"""
    query_id: int = Field(..., description="Associated query ID")
    topic_summary: Optional[str] = Field(None, description="Summary of the topic")
    key_concepts: Optional[Dict[str, Any]] = Field(
        None, 
        description="Key concepts with explanations"
    )
    mathematical_foundations: Optional[str] = Field(
        None, 
        description="Mathematical formulas and explanations"
    )
    historical_context: Optional[str] = Field(
        None, 
        description="Historical background"
    )
    implementation_examples: Optional[str] = Field(
        None, 
        description="Code examples"
    )
    sources: Optional[List[SourceSchema]] = Field(
        None, 
        description="Sources and citations"
    )
    research_data_path: Optional[str] = Field(
        None, 
        description="Path to full research data file"
    )
    completeness_score: Optional[float] = Field(
        None, 
        ge=0, 
        le=1, 
        description="Research completeness score (0-1)"
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# ============= Content Generation Schemas =============

class BlogGenerationRequest(BaseModel):
    """Request schema for blog generation"""
    research_query_id: int = Field(
        ..., 
        description="ID of the research query to generate blog from"
    )
    target_audience: Optional[TargetAudienceEnum] = Field(
        default=TargetAudienceEnum.PRACTITIONER,
        description="Target audience for the blog"
    )
    tone: Optional[str] = Field(
        default="professional",
        description="Writing tone (professional, conversational, technical)"
    )
    generate_linkedin_post: Optional[bool] = Field(
        default=False,
        description="Whether to also generate a LinkedIn post"
    )


class BlogGenerationResponse(BaseModel):
    """Response schema for blog generation"""
    content_id: int = Field(..., description="Generated content ID")
    title: Optional[str] = Field(None, description="Blog post title")
    content: Optional[str] = Field(None, description="Full blog content")
    target_audience: Optional[str] = Field(None, description="Target audience")
    file_path: Optional[str] = Field(None, description="Path to generated blog file")
    status: StatusEnum = Field(..., description="Generation status")
    linkedin_post: Optional[str] = Field(None, description="LinkedIn post if generated")
    
    model_config = ConfigDict(from_attributes=True)


class ContentItemResponse(BaseModel):
    """Response schema for content item retrieval"""
    id: int = Field(..., description="Content item ID")
    research_query_id: int = Field(..., description="Associated research query ID")
    content_type: str = Field(..., description="Type of content")
    title: Optional[str] = Field(None, description="Content title")
    content: Optional[str] = Field(None, description="Full content text")
    file_path: Optional[str] = Field(None, description="File path if saved to disk")
    target_audience: Optional[str] = Field(None, description="Target audience")
    tone: Optional[str] = Field(None, description="Content tone")
    status: Optional[str] = Field(None, description="Content status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ContentListResponse(BaseModel):
    """Response schema for paginated content list"""
    items: List[ContentItemResponse] = Field(..., description="List of content items")
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Starting offset")


# ============= Pipeline Schemas =============

class PipelineExecutionResponse(BaseModel):
    """Response schema for pipeline execution"""
    execution_id: int = Field(..., description="Pipeline execution ID")
    pipeline_name: str = Field(..., description="Name of the pipeline")
    status: StatusEnum = Field(..., description="Execution status")
    started_at: datetime = Field(..., description="Start timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class PipelineStatusResponse(BaseModel):
    """Response schema for pipeline status check"""
    id: int = Field(..., description="Execution ID")
    pipeline_name: str = Field(..., description="Pipeline name")
    status: StatusEnum = Field(..., description="Current status")
    started_at: datetime = Field(..., description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    execution_data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Pipeline execution data"
    )
    
    model_config = ConfigDict(from_attributes=True)


class BlogPipelineRequest(BaseModel):
    """Request schema for blog generation pipeline"""
    research_ids: List[int] = Field(
        ..., 
        description="List of research query IDs to generate blogs for"
    )
    target_audience: Optional[TargetAudienceEnum] = Field(
        default=TargetAudienceEnum.PRACTITIONER,
        description="Target audience for all blogs"
    )


# ============= Topic Agent Schemas =============

class TopicCategorizationResult(BaseModel):
    """Result from topic categorization agent"""
    category: Optional[TopicCategoryEnum] = Field(
        None, 
        description="Categorized topic type"
    )
    confidence: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="Confidence score"
    )
    reasoning: Optional[str] = Field(
        None, 
        description="Explanation for categorization"
    )
    is_ai_related: bool = Field(
        True, 
        description="Whether query is AI-related"
    )


# ============= Error Schemas =============

class ErrorResponse(BaseModel):
    """Standard error response schema"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


class ValidationErrorResponse(BaseModel):
    """Validation error response schema"""
    detail: List[Dict[str, Any]] = Field(..., description="Validation errors")

