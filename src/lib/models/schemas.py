"""
Pydantic schemas for API request/response validation
These schemas serve as the API contract (FastAPI auto-generates OpenAPI docs from these)
Maps to: plan.md → Section 7 (API Design)
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class TopicCategoryEnum(str, Enum):
    """Topic category for research queries"""
    # AI Topics
    CORE_AI = "core_ai"
    PRACTICAL_IMPLEMENTATION = "practical_implementation"
    # Software Development Topics
    SOFTWARE_DEVELOPMENT = "software_development"
    WEB_DEVELOPMENT = "web_development"
    DEVOPS = "devops"
    GENERAL_TECH = "general_tech"


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
        default=TopicCategoryEnum.CORE_AI, 
        description="Categorized topic type"
    )
    target_audience: Optional[str] = Field(TopicCategoryEnum.CORE_AI, description="Target audience")
    status: StatusEnum = Field(..., description="Current processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# ============= Research Result Schemas =============

class SourceSchema(BaseModel):
    """Schema for research source/citation"""
    type: Optional[str] = Field("web", description="Source type (paper, web, github)")
    title: Optional[str] = Field("Unknown", description="Source title")
    url: Optional[str] = Field(None, description="Source URL")
    authors: Optional[Any] = Field(None, description="Authors (for papers)")
    published: Optional[str] = Field(None, description="Publication date")
    
    model_config = {"extra": "allow"}  # Allow extra fields from tools
    
    @field_validator("authors", mode="before")
    @classmethod
    def parse_authors(cls, v):
        """Convert authors string to list if needed"""
        if v is None:
            return None
        if isinstance(v, str):
            return [a.strip() for a in v.split(",") if a.strip()]
        if isinstance(v, list):
            return v
        return None


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
        description="LLM-generated summary of all content fetched by research tools"
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
    category: str = Field(
        ..., 
        description="Categorized topic type (core_ai, practical_implementation, software_development, etc.)"
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
        False, 
        description="Whether query is AI-related"
    )


# ============= Paper Research Schemas =============

class ArXivPaperInput(BaseModel):
    """Input for paper research - accepts ID or title search"""
    arxiv_id: Optional[str] = Field(
        None,
        description="ArXiv paper ID (e.g., '2508.07407' or 'arxiv:2508.07407v2')",
        examples=["2508.07407", "arxiv:2508.07407v2", "1706.03762"]
    )
    title_search: Optional[str] = Field(
        None,
        description="Paper title for search (if arxiv_id not provided)",
        examples=["Attention Is All You Need", "BERT: Pre-training"]
    )
    
    @field_validator("arxiv_id", "title_search", mode="after")
    @classmethod
    def validate_at_least_one(cls, v, info):
        """Validate that at least one input method is provided"""
        return v
    
    def model_post_init(self, __context):
        """Validate that at least one of arxiv_id or title_search is provided"""
        if not self.arxiv_id and not self.title_search:
            raise ValueError("Either arxiv_id or title_search must be provided")


class PaperResearchRequest(BaseModel):
    """Request schema for paper research"""
    paper: ArXivPaperInput = Field(
        ...,
        description="Paper identification (arxiv_id or title_search)"
    )
    target_audience: Optional[TargetAudienceEnum] = Field(
        default=TargetAudienceEnum.PRACTITIONER,
        description="Target audience for the research output"
    )
    generate_blog: Optional[bool] = Field(
        default=True,
        description="Whether to generate blog after research"
    )


class PaperMetadataSchema(BaseModel):
    """Paper metadata from ArXiv"""
    arxiv_id: str = Field(..., description="ArXiv paper ID")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(default=[], description="List of authors")
    abstract: str = Field(default="", description="Paper abstract")
    published: str = Field(default="", description="Publication date")
    updated: Optional[str] = Field(None, description="Last updated date")
    categories: List[str] = Field(default=[], description="ArXiv categories")
    pdf_url: Optional[str] = Field(None, description="PDF URL")
    abs_url: Optional[str] = Field(None, description="Abstract page URL")
    
    model_config = ConfigDict(from_attributes=True)


class EnhancedResearchResultSchema(BaseModel):
    """Enhanced research result with paper-specific sections"""
    # Standard research fields (from existing research)
    topic_summary: str = Field(..., description="Comprehensive summary of the topic")
    key_concepts: Dict[str, Any] = Field(
        default={},
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
    sources: List[SourceSchema] = Field(
        default=[],
        description="Sources and citations"
    )
    
    # Paper-specific enhanced sections
    paper_overview: str = Field(..., description="Structured summary of paper contribution")
    methodology_deep_dive: str = Field(..., description="Detailed methodology explanation")
    experimental_results: Optional[str] = Field(None, description="Key findings and metrics")
    practical_implications: str = Field(..., description="Real-world applications")
    limitations_future_work: Optional[str] = Field(None, description="Acknowledged limitations")
    related_work_summary: Optional[str] = Field(None, description="Related papers overview")
    citation: str = Field(..., description="Proper academic citation")
    
    # Metadata
    paper_metadata: PaperMetadataSchema = Field(..., description="Paper metadata")
    completeness_score: float = Field(..., ge=0, le=1, description="Research completeness score")
    research_data_path: Optional[str] = Field(None, description="Path to saved research data")
    
    model_config = ConfigDict(from_attributes=True)


class PaperResearchResponse(BaseModel):
    """Response for async paper research request"""
    research_id: int = Field(..., description="Research query ID")
    paper_metadata: PaperMetadataSchema = Field(..., description="Paper metadata")
    status: StatusEnum = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class PaperFullResponse(BaseModel):
    """Full response with research and blog"""
    research_id: int = Field(..., description="Research query ID")
    paper_metadata: PaperMetadataSchema = Field(..., description="Paper metadata")
    research: EnhancedResearchResultSchema = Field(..., description="Enhanced research result")
    blog: Optional[BlogGenerationResponse] = Field(None, description="Generated blog if requested")
    status: StatusEnum = Field(..., description="Processing status")
    
    model_config = ConfigDict(from_attributes=True)


class PaperSearchRequest(BaseModel):
    """Request schema for paper search"""
    query: str = Field(
        ...,
        description="Search query for papers",
        min_length=3,
        max_length=500
    )
    max_results: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results to return"
    )


class PaperBlogRequest(BaseModel):
    """Request schema for blog generation from paper research"""
    research_id: int = Field(
        ...,
        description="ID of the paper research to generate blog from"
    )
    target_audience: Optional[TargetAudienceEnum] = Field(
        default=TargetAudienceEnum.PRACTITIONER,
        description="Target audience for the blog"
    )
    tone: Optional[str] = Field(
        default="professional",
        description="Writing tone (professional, conversational, technical)"
    )


class MultiplePaperResearchRequest(BaseModel):
    """Request schema for multiple paper research"""
    arxiv_ids: List[str] = Field(
        ...,
        description="List of ArXiv paper IDs",
        min_length=1,
        max_length=5
    )
    target_audience: Optional[TargetAudienceEnum] = Field(
        default=TargetAudienceEnum.PRACTITIONER,
        description="Target audience for the research"
    )
    generate_blog: Optional[bool] = Field(
        default=False,
        description="Whether to generate a synthesis blog"
    )


# ============= Error Schemas =============

class ErrorResponse(BaseModel):
    """Standard error response schema"""
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")


class ValidationErrorResponse(BaseModel):
    """Validation error response schema"""
    detail: List[Dict[str, Any]] = Field(..., description="Validation errors")

