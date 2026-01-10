"""
Pydantic schemas for Social API
"""
from typing import List, Optional

from pydantic import BaseModel, Field


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
        description='Target audience',
    )


class LinkedInResponse(BaseModel):
    """Response for LinkedIn post"""

    hook: str = Field(..., description='Attention-grabbing first line')
    content: str = Field(..., description='Full post content')
    hashtags: List[str] = Field(default_factory=list, description='Relevant hashtags')
    call_to_action: str = Field(default='', description='Call-to-action text')
    character_count: int = Field(default=0, description='Post character count')
    file_path: Optional[str] = Field(None, description='Saved file path')


class TwitterThreadRequest(BaseModel):
    """Request for Twitter thread generation"""

    topic: str = Field(
        ...,
        description='Thread topic',
        min_length=5,
        max_length=500,
    )
    content: str = Field(
        ...,
        description='Source content to transform',
        min_length=50,
        max_length=8000,
    )
    max_posts: int = Field(
        default=5,
        description='Maximum number of posts',
        ge=3,
        le=15,
    )


class ThreadPostResponse(BaseModel):
    """Response for single thread post"""

    position: int = Field(..., description='Post position (1-indexed)')
    content: str = Field(..., description='Post content')
    character_count: int = Field(default=0, description='Character count')


class ThreadResponse(BaseModel):
    """Response for Twitter thread"""

    posts: List[ThreadPostResponse] = Field(default_factory=list, description='Thread posts')
    topic: str = Field(..., description='Thread topic')
    total_posts: int = Field(default=0, description='Total number of posts')
    file_path: Optional[str] = Field(None, description='Saved file path')


class SocialFromBlogRequest(BaseModel):
    """Request to generate social content from blog"""

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
    platforms: List[str] = Field(
        default=['linkedin', 'twitter'],
        description='Platforms to generate for',
    )


class SocialContentResponse(BaseModel):
    """Response for combined social content"""

    linkedin: Optional[LinkedInResponse] = None
    twitter: Optional[ThreadResponse] = None
