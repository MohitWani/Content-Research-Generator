"""
Paper research schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.research.schemas.research_schemas import (
    SourceSchema,
    StatusEnum,
    TargetAudienceEnum,
)


class ArXivPaperInput(BaseModel):
    """Input for paper research"""

    arxiv_id: Optional[str] = Field(
        None,
        description="ArXiv paper ID (e.g., '2508.07407' or 'arxiv:2508.07407v2')",
        examples=['2508.07407', 'arxiv:2508.07407v2', '1706.03762'],
    )
    title_search: Optional[str] = Field(
        None,
        description='Paper title for search (if arxiv_id not provided)',
        examples=['Attention Is All You Need', 'BERT: Pre-training'],
    )

    def model_post_init(self, __context):
        """Validate that at least one of arxiv_id or title_search is provided"""
        if not self.arxiv_id and not self.title_search:
            raise ValueError('Either arxiv_id or title_search must be provided')


class PaperResearchRequest(BaseModel):
    """Request schema for paper research"""

    paper: ArXivPaperInput = Field(
        ..., description='Paper identification (arxiv_id or title_search)'
    )
    target_audience: Optional[TargetAudienceEnum] = Field(
        default=TargetAudienceEnum.PRACTITIONER,
        description='Target audience for the research output',
    )
    generate_blog: Optional[bool] = Field(
        default=True, description='Whether to generate blog after research'
    )


class PaperMetadataSchema(BaseModel):
    """Paper metadata from ArXiv"""

    arxiv_id: str = Field(..., description='ArXiv paper ID')
    title: str = Field(..., description='Paper title')
    authors: List[str] = Field(default=[], description='List of authors')
    abstract: str = Field(default='', description='Paper abstract')
    published: str = Field(default='', description='Publication date')
    updated: Optional[str] = Field(None, description='Last updated date')
    categories: List[str] = Field(default=[], description='ArXiv categories')
    pdf_url: Optional[str] = Field(None, description='PDF URL')
    abs_url: Optional[str] = Field(None, description='Abstract page URL')

    model_config = ConfigDict(from_attributes=True)


class EnhancedResearchResultSchema(BaseModel):
    """Enhanced research result with paper-specific sections"""

    topic_summary: str = Field(..., description='Comprehensive summary of the topic')
    key_concepts: Dict[str, Any] = Field(
        default={}, description='Key concepts with explanations'
    )
    mathematical_foundations: Optional[str] = Field(
        None, description='Mathematical formulas and explanations'
    )
    historical_context: Optional[str] = Field(None, description='Historical background')
    implementation_examples: Optional[str] = Field(None, description='Code examples')
    sources: List[SourceSchema] = Field(default=[], description='Sources and citations')

    paper_overview: str = Field(
        ..., description='Structured summary of paper contribution'
    )
    methodology_deep_dive: str = Field(
        ..., description='Detailed methodology explanation'
    )
    experimental_results: Optional[str] = Field(
        None, description='Key findings and metrics'
    )
    practical_implications: str = Field(..., description='Real-world applications')
    limitations_future_work: Optional[str] = Field(
        None, description='Acknowledged limitations'
    )
    related_work_summary: Optional[str] = Field(
        None, description='Related papers overview'
    )
    citation: str = Field(..., description='Proper academic citation')

    paper_metadata: PaperMetadataSchema = Field(..., description='Paper metadata')
    completeness_score: float = Field(
        ..., ge=0, le=1, description='Research completeness score'
    )
    research_data_path: Optional[str] = Field(
        None, description='Path to saved research data'
    )

    model_config = ConfigDict(from_attributes=True)


class PaperResearchResponse(BaseModel):
    """Response for async paper research request"""

    research_id: int = Field(..., description='Research query ID')
    paper_metadata: PaperMetadataSchema = Field(..., description='Paper metadata')
    status: StatusEnum = Field(..., description='Current status')
    created_at: datetime = Field(..., description='Creation timestamp')

    model_config = ConfigDict(from_attributes=True)


class BlogGenerationResponse(BaseModel):
    """Response schema for blog generation"""

    content_id: int = Field(..., description='Generated content ID')
    title: Optional[str] = Field(None, description='Blog post title')
    content: Optional[str] = Field(None, description='Full blog content')
    target_audience: Optional[str] = Field(None, description='Target audience')
    file_path: Optional[str] = Field(None, description='Path to generated blog file')
    status: StatusEnum = Field(..., description='Generation status')
    linkedin_post: Optional[str] = Field(
        None, description='LinkedIn post if generated'
    )

    model_config = ConfigDict(from_attributes=True)


class PaperFullResponse(BaseModel):
    """Full response with research and blog"""

    research_id: int = Field(..., description='Research query ID')
    paper_metadata: PaperMetadataSchema = Field(..., description='Paper metadata')
    research: EnhancedResearchResultSchema = Field(
        ..., description='Enhanced research result'
    )
    blog: Optional[BlogGenerationResponse] = Field(
        None, description='Generated blog if requested'
    )
    status: StatusEnum = Field(..., description='Processing status')

    model_config = ConfigDict(from_attributes=True)


class PaperSearchRequest(BaseModel):
    """Request schema for paper search"""

    query: str = Field(
        ..., description='Search query for papers', min_length=3, max_length=500
    )
    max_results: Optional[int] = Field(
        default=5, ge=1, le=20, description='Maximum number of results to return'
    )


class PaperBlogRequest(BaseModel):
    """Request schema for blog generation from paper research"""

    research_id: int = Field(
        ..., description='ID of the paper research to generate blog from'
    )
    target_audience: Optional[TargetAudienceEnum] = Field(
        default=TargetAudienceEnum.PRACTITIONER,
        description='Target audience for the blog',
    )
    tone: Optional[str] = Field(
        default='professional',
        description='Writing tone (professional, conversational, technical)',
    )


class MultiplePaperResearchRequest(BaseModel):
    """Request schema for multiple paper research"""

    arxiv_ids: List[str] = Field(
        ..., description='List of ArXiv paper IDs', min_length=1, max_length=5
    )
    target_audience: Optional[TargetAudienceEnum] = Field(
        default=TargetAudienceEnum.PRACTITIONER,
        description='Target audience for the research',
    )
    generate_blog: Optional[bool] = Field(
        default=False, description='Whether to generate a synthesis blog'
    )


