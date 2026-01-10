"""
Pydantic schemas for Content API
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class BlogGenerateRequest(BaseModel):
    """Request schema for blog generation"""

    query: str = Field(
        ...,
        description='Research query or topic for blog generation',
        min_length=5,
        max_length=1000,
    )
    target_audience: str = Field(
        default='practitioner',
        description='Target audience (beginner, practitioner, expert)',
    )
    tone: str = Field(
        default='professional',
        description='Writing tone (professional, conversational, technical)',
    )


class BlogResponse(BaseModel):
    """Response schema for blog generation"""

    title: str = Field(..., description='Blog post title')
    content: str = Field(..., description='Full markdown content')
    meta_description: str = Field(default='', description='SEO meta description')
    tags: List[str] = Field(default_factory=list, description='Blog tags')
    estimated_reading_time: str = Field(default='5 min read', description='Reading time')
    file_path: Optional[str] = Field(None, description='Saved file path')


class BlogStatusResponse(BaseModel):
    """Response for blog status/listing"""

    id: int = Field(..., description='Content item ID')
    content_type: str = Field(..., description='Content type')
    title: Optional[str] = Field(None, description='Blog title')
    status: str = Field(..., description='Content status')
    file_path: Optional[str] = Field(None, description='File path')
    created_at: Optional[datetime] = Field(None, description='Creation timestamp')

    class Config:
        from_attributes = True


class BlogFromResearchRequest(BaseModel):
    """Request to generate blog from existing research"""

    research_query_id: int = Field(..., description='Research query ID')
    target_audience: str = Field(default='practitioner', description='Target audience')
    tone: str = Field(default='professional', description='Writing tone')
