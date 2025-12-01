"""
Social Content API Routes
Endpoints for LinkedIn posts, Twitter threads, and social content
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from src.common.database import get_db
from src.lib.agents.shortform_agent import ShortformAgent, LinkedInPost, SocialThread
from src.lib.agents.blog_writer_agent import BlogOutput
from src.lib.models.research import ContentItem, ResearchResult
from src.common.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


# ============= Request/Response Schemas =============

class LinkedInPostRequest(BaseModel):
    """Request for LinkedIn post generation"""
    content_id: Optional[int] = Field(None, description="Blog content ID to generate from")
    research_query_id: Optional[int] = Field(None, description="Research ID to generate from")
    custom_content: Optional[str] = Field(None, description="Custom content to convert")
    target_audience: str = Field(default="practitioner")
    include_hashtags: bool = Field(default=True)
    include_cta: bool = Field(default=True)


class LinkedInPostResponse(BaseModel):
    """Response for LinkedIn post"""
    content: str
    hook: str
    call_to_action: Optional[str] = None
    hashtags: List[str] = []
    character_count: int
    target_audience: str
    file_path: Optional[str] = None


class TwitterThreadRequest(BaseModel):
    """Request for Twitter/X thread generation"""
    content_id: Optional[int] = Field(None, description="Blog content ID")
    research_query_id: Optional[int] = Field(None, description="Research ID")
    custom_content: Optional[str] = Field(None, description="Custom content")
    max_posts: int = Field(default=5, ge=2, le=15)
    platform: str = Field(default="twitter", description="twitter or threads")


class ThreadPostSchema(BaseModel):
    """A single post in a thread"""
    position: int
    content: str
    character_count: int


class TwitterThreadResponse(BaseModel):
    """Response for Twitter thread"""
    posts: List[ThreadPostSchema]
    topic: str
    total_posts: int


class SummarizeRequest(BaseModel):
    """Request for social summary"""
    content: str
    max_length: int = Field(default=280, ge=50, le=500)


class SummarizeResponse(BaseModel):
    """Response for social summary"""
    summary: str
    character_count: int


# ============= Endpoints =============

@router.post("/linkedin", response_model=LinkedInPostResponse)
async def generate_linkedin_post(
    request: LinkedInPostRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a LinkedIn post from blog content, research, or custom text
    """
    try:
        shortform_agent = ShortformAgent()
        
        # Get source content
        source_content = await _get_source_content(
            db=db,
            content_id=request.content_id,
            research_query_id=request.research_query_id,
            custom_content=request.custom_content,
        )
        
        if not source_content:
            raise HTTPException(
                status_code=400,
                detail="Provide content_id, research_query_id, or custom_content"
            )
        
        # Generate post
        post = await shortform_agent.generate_linkedin_post(
            source_content=source_content,
            target_audience=request.target_audience,
            include_hashtags=request.include_hashtags,
            include_cta=request.include_cta,
        )
        
        logger.info(f"Generated LinkedIn post: {post.character_count} chars")
        
        return LinkedInPostResponse(
            content=post.content,
            hook=post.hook,
            call_to_action=post.call_to_action,
            hashtags=post.hashtags or [],
            character_count=post.character_count,
            target_audience=post.target_audience,
            file_path=post.file_path,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LinkedIn post generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/thread", response_model=TwitterThreadResponse)
async def generate_twitter_thread(
    request: TwitterThreadRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a Twitter/X thread from content
    """
    try:
        shortform_agent = ShortformAgent()
        
        # Get source content
        source_content = await _get_source_content(
            db=db,
            content_id=request.content_id,
            research_query_id=request.research_query_id,
            custom_content=request.custom_content,
        )
        
        if not source_content:
            raise HTTPException(
                status_code=400,
                detail="Provide content_id, research_query_id, or custom_content"
            )
        
        # Generate thread
        thread = await shortform_agent.generate_thread(
            source_content=source_content,
            max_posts=request.max_posts,
            platform=request.platform,
        )
        
        logger.info(f"Generated thread with {thread.total_posts} posts")
        
        return TwitterThreadResponse(
            posts=[
                ThreadPostSchema(
                    position=p.position,
                    content=p.content,
                    character_count=p.character_count,
                )
                for p in thread.posts
            ],
            topic=thread.topic,
            total_posts=thread.total_posts,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Thread generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_for_social(
    request: SummarizeRequest,
):
    """
    Create a brief social media summary of content
    """
    try:
        shortform_agent = ShortformAgent()
        
        summary = await shortform_agent.summarize_for_social(
            content=request.content,
            max_length=request.max_length,
        )
        
        return SummarizeResponse(
            summary=summary,
            character_count=len(summary),
        )
        
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Helper Functions =============

async def _get_source_content(
    db: AsyncSession,
    content_id: Optional[int] = None,
    research_query_id: Optional[int] = None,
    custom_content: Optional[str] = None,
) -> Optional[dict]:
    """Get source content from various sources"""
    
    # Priority: custom_content > content_id > research_query_id
    if custom_content:
        return {"content": custom_content}
    
    if content_id:
        content = await db.get(ContentItem, content_id)
        if content:
            return {
                "title": content.title,
                "content": content.content,
            }
        raise HTTPException(status_code=404, detail=f"Content {content_id} not found")
    
    if research_query_id:
        result = await db.scalar(
            select(ResearchResult).where(ResearchResult.query_id == research_query_id)
        )
        if result:
            return {
                "topic_summary": result.topic_summary,
                "key_concepts": result.key_concepts or {},
            }
        raise HTTPException(
            status_code=404, 
            detail=f"Research result for query {research_query_id} not found"
        )
    
    return None


