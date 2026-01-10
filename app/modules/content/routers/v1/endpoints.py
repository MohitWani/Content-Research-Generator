"""
Content API Routes
Blog generation endpoints
"""
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.content.services import BlogOutput, get_blog_writer_agent
from app.modules.research.models.research_model import ContentItem, ResearchQuery, ResearchResult
from database.database import get_db, SessionLocal

router = APIRouter()


# ============= Request Schemas =============

class BlogGenerationRequest(BaseModel):
    """Request for generating blog from existing research"""

    research_query_id: int = Field(..., description='Research query ID to generate blog from')
    target_audience: Optional[str] = Field(default='practitioner', description='Target audience')
    tone: Optional[str] = Field(default='professional', description='Writing tone')


class BlogFromQueryRequest(BaseModel):
    """Request for full pipeline: research + blog generation"""

    query: str = Field(..., min_length=5, max_length=1000, description='Research query')
    target_audience: str = Field(default='practitioner', description='Target audience')
    tone: str = Field(default='professional', description='Writing tone')


# ============= Response Schemas =============

class BlogGenerationResponse(BaseModel):
    """Response for blog generation"""

    content_id: int
    title: str
    file_path: str
    status: str


class BlogContentResponse(BaseModel):
    """Full blog content response"""

    id: int
    research_query_id: int
    content_type: str
    title: str
    content: str
    meta_description: Optional[str] = None
    tags: Optional[List[str]] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    file_path: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContentItemResponse(BaseModel):
    """Response for content listing"""

    id: int
    content_type: str
    title: Optional[str]
    status: str
    file_path: Optional[str]
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============= Background Tasks =============

def run_blog_generation_task(
    research_query_id: int,
    target_audience: str,
    tone: str,
):
    """Background task for blog generation"""
    asyncio.run(_execute_blog_from_research(research_query_id, target_audience, tone))


async def _execute_blog_from_research(
    research_query_id: int,
    target_audience: str,
    tone: str,
) -> Optional[ContentItem]:
    """Execute blog generation from research"""
    db = SessionLocal()
    try:
        # Get research result
        result = db.scalar(
            select(ResearchResult).where(ResearchResult.query_id == research_query_id)
        )
        if not result:
            logger.error(f'Research result not found: {research_query_id}')
            return None

        # Get query
        query = db.get(ResearchQuery, research_query_id)
        if not query:
            logger.error(f'Research query not found: {research_query_id}')
            return None

        # Convert to ResearchOutput
        from app.modules.research.services import ResearchOutput
        research = ResearchOutput(
            topic_summary=result.topic_summary or '',
            key_concepts=result.key_concepts or {},
            mathematical_foundations=result.mathematical_foundations,
            source_descriptions=result.historical_context,
            implementation_examples=result.implementation_examples,
            sources=result.sources or [],
            completeness_score=result.completeness_score or 0.0,
        )

        # Generate blog
        blog_writer = get_blog_writer_agent()
        blog = await blog_writer.generate_blog(
            topic=query.query_text,
            research_data=research,
            target_audience=target_audience,
            tone=tone,
        )

        # Save content item
        content_item = ContentItem(
            research_query_id=research_query_id,
            content_type='blog',
            title=blog.title,
            content=blog.content,
            file_path=blog.file_path,
            target_audience=target_audience,
            tone=tone,
            meta_description=blog.meta_description,
            tags=blog.tags,
            status='published',
        )
        db.add(content_item)
        db.commit()
        db.refresh(content_item)

        logger.info(f'Blog generation completed: content_id={content_item.id}')
        return content_item

    except Exception as e:
        logger.error(f'Blog generation failed: {e}', exc_info=True)
        return None
    finally:
        db.close()


# ============= API Endpoints =============

@router.post('/generate-blog', response_model=BlogGenerationResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_blog(
    request: BlogGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Generate a blog post from existing research results.
    
    This endpoint creates a blog post from research data that was previously
    collected via the research endpoints. Returns 202 Accepted and generates
    the blog in the background.
    
    Use GET /content/{content_id} to retrieve the generated blog.
    """
    try:
        # Verify research exists
        result = db.scalar(
            select(ResearchResult).where(ResearchResult.query_id == request.research_query_id)
        )
        if not result:
            raise HTTPException(status_code=404, detail='Research result not found')

        query = db.get(ResearchQuery, request.research_query_id)
        if not query:
            raise HTTPException(status_code=404, detail='Research query not found')

        # Create placeholder content item
        content_item = ContentItem(
            research_query_id=request.research_query_id,
            content_type='blog',
            title=f'Generating: {query.query_text[:50]}...',
            content='',
            target_audience=request.target_audience or 'practitioner',
            tone=request.tone or 'professional',
            status='generating',
        )
        db.add(content_item)
        db.commit()
        db.refresh(content_item)

        # Start background generation
        background_tasks.add_task(
            run_blog_generation_task,
            research_query_id=request.research_query_id,
            target_audience=request.target_audience or 'practitioner',
            tone=request.tone or 'professional',
        )

        logger.info(f'Blog generation queued: content_id={content_item.id}')

        return BlogGenerationResponse(
            content_id=content_item.id,
            title=content_item.title,
            file_path=content_item.file_path or '',
            status='generating',
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to queue blog generation: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/generate-blog/sync', response_model=BlogContentResponse)
async def generate_blog_sync(
    request: BlogGenerationRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a blog post from existing research results (synchronous).
    
    This endpoint waits for the blog to be generated and returns the full content.
    Use this for real-time generation when you need the result immediately.
    """
    try:
        # Get research result
        result = db.scalar(
            select(ResearchResult).where(ResearchResult.query_id == request.research_query_id)
        )
        if not result:
            raise HTTPException(status_code=404, detail='Research result not found')

        query = db.get(ResearchQuery, request.research_query_id)
        if not query:
            raise HTTPException(status_code=404, detail='Research query not found')

        # Convert to ResearchOutput
        from app.modules.research.services import ResearchOutput
        research = ResearchOutput(
            topic_summary=result.topic_summary or '',
            key_concepts=result.key_concepts or {},
            mathematical_foundations=result.mathematical_foundations,
            source_descriptions=result.historical_context,
            implementation_examples=result.implementation_examples,
            sources=result.sources or [],
            completeness_score=result.completeness_score or 0.0,
        )

        # Generate blog
        blog_writer = get_blog_writer_agent()
        blog = await blog_writer.generate_blog(
            topic=query.query_text,
            research_data=research,
            target_audience=request.target_audience or 'practitioner',
            tone=request.tone or 'professional',
        )

        # Save content item
        content_item = ContentItem(
            research_query_id=request.research_query_id,
            content_type='blog',
            title=blog.title,
            content=blog.content,
            file_path=blog.file_path,
            target_audience=request.target_audience,
            tone=request.tone,
            meta_description=blog.meta_description,
            tags=blog.tags,
            status='published',
        )
        db.add(content_item)
        db.commit()
        db.refresh(content_item)

        logger.info(f'Sync blog generation completed: content_id={content_item.id}')

        return BlogContentResponse(
            id=content_item.id,
            research_query_id=content_item.research_query_id,
            content_type=content_item.content_type,
            title=content_item.title,
            content=content_item.content,
            meta_description=content_item.meta_description,
            tags=content_item.tags,
            target_audience=content_item.target_audience,
            tone=content_item.tone,
            file_path=content_item.file_path,
            status=content_item.status,
            created_at=content_item.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Sync blog generation failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/full-pipeline', response_model=BlogContentResponse)
async def generate_blog_full_pipeline(
    request: BlogFromQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a blog post with full pipeline: research → blog generation.
    
    This endpoint runs the complete workflow:
    1. Categorize the query
    2. Conduct research
    3. Generate blog from research
    
    Returns the complete blog content when finished.
    """
    try:
        blog_writer = get_blog_writer_agent()
        blog = await blog_writer.generate_from_query(
            query=request.query,
            target_audience=request.target_audience,
            tone=request.tone,
        )

        # Create query record for tracking
        query_record = ResearchQuery(
            query_text=request.query,
            target_audience=request.target_audience,
            content_type='blog',
            status='completed',
        )
        db.add(query_record)
        db.flush()

        # Save content item
        content_item = ContentItem(
            research_query_id=query_record.id,
            content_type='blog',
            title=blog.title,
            content=blog.content,
            file_path=blog.file_path,
            target_audience=request.target_audience,
            tone=request.tone,
            meta_description=blog.meta_description,
            tags=blog.tags,
            status='published',
        )
        db.add(content_item)
        db.commit()
        db.refresh(content_item)

        return BlogContentResponse(
            id=content_item.id,
            research_query_id=content_item.research_query_id,
            content_type=content_item.content_type,
            title=content_item.title,
            content=content_item.content,
            meta_description=content_item.meta_description,
            tags=content_item.tags,
            target_audience=content_item.target_audience,
            tone=content_item.tone,
            file_path=content_item.file_path,
            status=content_item.status,
            created_at=content_item.created_at,
        )

    except Exception as e:
        logger.error(f'Full pipeline blog generation failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{content_id}', response_model=BlogContentResponse)
async def get_content(
    content_id: int,
    db: Session = Depends(get_db),
):
    """Get content item by ID with full content"""
    content = db.get(ContentItem, content_id)

    if not content:
        raise HTTPException(status_code=404, detail='Content not found')

    return BlogContentResponse(
        id=content.id,
        research_query_id=content.research_query_id,
        content_type=content.content_type,
        title=content.title,
        content=content.content or '',
        meta_description=content.meta_description,
        tags=content.tags,
        target_audience=content.target_audience,
        tone=content.tone,
        file_path=content.file_path,
        status=content.status,
        created_at=content.created_at,
    )


@router.get('/', response_model=List[ContentItemResponse])
async def list_content(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    content_type: Optional[str] = Query(default=None, description='Filter by type (blog, etc.)'),
    db: Session = Depends(get_db),
):
    """List content items with pagination"""
    stmt = select(ContentItem).offset(offset).limit(limit)

    if content_type:
        stmt = stmt.where(ContentItem.content_type == content_type)

    stmt = stmt.order_by(ContentItem.created_at.desc())

    result = db.execute(stmt)
    items = result.scalars().all()

    return [
        ContentItemResponse(
            id=item.id,
            content_type=item.content_type,
            title=item.title,
            status=item.status,
            file_path=item.file_path,
            created_at=item.created_at,
        )
        for item in items
    ]


content_router = router
