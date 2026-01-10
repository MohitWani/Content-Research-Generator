"""
Social API Routes
LinkedIn and Twitter/X content generation endpoints
"""
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logging.logger import logger
from app.modules.social.services import (
    LinkedInOutput,
    ShortformAgent,
    ThreadOutput,
    ThreadPost,
    get_shortform_agent,
)

router = APIRouter()


# Request Schemas
class LinkedInGenerateRequest(BaseModel):
    """Request for LinkedIn post generation"""

    topic: str = Field(..., min_length=5, max_length=500)
    content: str = Field(..., min_length=50, max_length=8000)
    target_audience: str = Field(default='practitioner')


class TwitterThreadRequest(BaseModel):
    """Request for Twitter thread generation"""

    topic: str = Field(..., min_length=5, max_length=500)
    content: str = Field(..., min_length=50, max_length=8000)
    max_posts: int = Field(default=5, ge=3, le=15)


class SocialFromBlogRequest(BaseModel):
    """Request to generate social content from blog"""

    title: str = Field(..., min_length=5, max_length=500)
    content: str = Field(..., min_length=100)
    platforms: List[str] = Field(default=['linkedin', 'twitter'])


# Response Schemas
class LinkedInResponse(BaseModel):
    """Response for LinkedIn post"""

    hook: str
    content: str
    hashtags: List[str]
    call_to_action: str
    character_count: int
    file_path: Optional[str] = None


class ThreadPostResponse(BaseModel):
    """Response for single thread post"""

    position: int
    content: str
    character_count: int


class ThreadResponse(BaseModel):
    """Response for Twitter thread"""

    posts: List[ThreadPostResponse]
    topic: str
    total_posts: int
    file_path: Optional[str] = None


class SocialContentResponse(BaseModel):
    """Response for combined social content"""

    linkedin: Optional[LinkedInResponse] = None
    twitter: Optional[ThreadResponse] = None


@router.post('/linkedin', response_model=LinkedInResponse)
async def generate_linkedin_post(request: LinkedInGenerateRequest):
    """
    Generate a LinkedIn post from content.
    """
    try:
        agent = get_shortform_agent()
        result = await agent.generate_linkedin_post(
            topic=request.topic,
            content=request.content,
            target_audience=request.target_audience,
        )

        return LinkedInResponse(
            hook=result.hook,
            content=result.content,
            hashtags=result.hashtags,
            call_to_action=result.call_to_action,
            character_count=result.character_count,
            file_path=result.file_path,
        )

    except Exception as e:
        logger.error(f'LinkedIn generation failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/twitter/thread', response_model=ThreadResponse)
async def generate_twitter_thread(request: TwitterThreadRequest):
    """
    Generate a Twitter/X thread from content.
    """
    try:
        agent = get_shortform_agent()
        result = await agent.generate_twitter_thread(
            topic=request.topic,
            content=request.content,
            max_posts=request.max_posts,
        )

        return ThreadResponse(
            posts=[
                ThreadPostResponse(
                    position=p.position,
                    content=p.content,
                    character_count=p.character_count,
                )
                for p in result.posts
            ],
            topic=result.topic,
            total_posts=result.total_posts,
            file_path=result.file_path,
        )

    except Exception as e:
        logger.error(f'Twitter thread generation failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/from-blog', response_model=SocialContentResponse)
async def generate_social_from_blog(request: SocialFromBlogRequest):
    """
    Generate social media content from a blog post.
    Supports both LinkedIn and Twitter/X.
    """
    try:
        from app.modules.content.services import BlogOutput

        # Create a BlogOutput from the request
        blog = BlogOutput(
            title=request.title,
            content=request.content,
        )

        agent = get_shortform_agent()
        results = await agent.generate_from_blog(
            blog=blog,
            platforms=request.platforms,
        )

        response = SocialContentResponse()

        if 'linkedin' in results:
            li = results['linkedin']
            response.linkedin = LinkedInResponse(
                hook=li.hook,
                content=li.content,
                hashtags=li.hashtags,
                call_to_action=li.call_to_action,
                character_count=li.character_count,
                file_path=li.file_path,
            )

        if 'twitter' in results:
            tw = results['twitter']
            response.twitter = ThreadResponse(
                posts=[
                    ThreadPostResponse(
                        position=p.position,
                        content=p.content,
                        character_count=p.character_count,
                    )
                    for p in tw.posts
                ],
                topic=tw.topic,
                total_posts=tw.total_posts,
                file_path=tw.file_path,
            )

        return response

    except Exception as e:
        logger.error(f'Social content generation failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


social_router = router
