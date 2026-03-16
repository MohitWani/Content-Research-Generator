"""
Pydantic schemas for Social API (LinkedIn only)
"""
from typing import List, Optional

from pydantic import BaseModel, Field


# ============= Request Schemas =============

class LinkedInGenerateRequest(BaseModel):
    """Request for LinkedIn post generation"""

    topic: str = Field(
        ...,
        description='Post topic',
        min_length=5,
        max_length=500,
    )
    content: str = Field(
        ...,
        description='Source content to transform',
        min_length=50,
        max_length=8000,
    )
    target_audience: str = Field(
        default='practitioner',
        description='Target audience (beginner, practitioner, expert)',
    )
    user_instructions: str = Field(
        default='',
        description='Custom instructions on how the post should look (tone, style, length, format, etc.)',
        max_length=1000,
    )


class LinkedInFromBlogRequest(BaseModel):
    """Request to generate LinkedIn post from blog"""

    title: str = Field(
        ...,
        description='Blog title',
        min_length=5,
        max_length=500,
    )
    content: str = Field(
        ...,
        description='Blog content',
        min_length=100,
    )
    target_audience: str = Field(
        default='practitioner',
        description='Target audience',
    )
    user_instructions: str = Field(
        default='',
        description='Custom instructions on how the post should look (tone, style, length, format, etc.)',
        max_length=1000,
    )


class LinkedInFromResearchRequest(BaseModel):
    """Request to generate LinkedIn post from research"""

    research_query_id: int = Field(
        ...,
        description='Research query ID to generate LinkedIn post from',
    )
    target_audience: str = Field(
        default='practitioner',
        description='Target audience (beginner, practitioner, expert)',
    )
    user_instructions: str = Field(
        default='',
        description='Custom instructions on how the post should look (tone, style, length, format, etc.)',
        max_length=1000,
    )


# ============= Response Schemas =============

class LinkedInResponse(BaseModel):
    """Response for LinkedIn post"""

    hook: str = Field(..., description='Attention-grabbing first line')
    content: str = Field(..., description='Full post content')
    hashtags: List[str] = Field(default_factory=list, description='Relevant hashtags')
    call_to_action: str = Field(default='', description='Call-to-action text')
    character_count: int = Field(default=0, description='Post character count')
    file_path: Optional[str] = Field(None, description='Saved file path')

    class Config:
        from_attributes = True
