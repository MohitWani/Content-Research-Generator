"""
Content API Routes

This module contains only API endpoint definitions.
Business logic is handled by the ContentService.
Database operations are handled by repositories.
"""
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.content.schemas.content_schemas import (
    BlogContentResponse,
    BlogFromResearchRequest,
    BlogGenerationResponse,
    BlogStatusResponse,
)
from app.modules.content.services.background_task_service import ContentBackgroundTaskService
from app.modules.content.services.content_service import ContentService
from database.database import get_db

router = APIRouter()


def get_content_service(db: Session = Depends(get_db)) -> ContentService:
    """Dependency to get ContentService instance"""
    return ContentService(db)


# ============= API Endpoints =============

@router.post(
    '/generate-blog',
    response_model=BlogGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_blog(
    request: BlogFromResearchRequest,
    background_tasks: BackgroundTasks,
    service: ContentService = Depends(get_content_service),
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
        query, error = service.verify_research_exists(request.research_query_id)
        if error:
            raise HTTPException(status_code=404, detail=error)

        # Create placeholder content item
        target_audience = request.target_audience or 'practitioner'
        tone = request.tone or 'professional'
        
        content_item = service.create_placeholder_content(
            research_query_id=request.research_query_id,
            query_text=query.query_text,
            target_audience=target_audience,
            tone=tone,
        )

        # Start background generation
        background_tasks.add_task(
            ContentBackgroundTaskService.run_blog_generation_task,
            research_query_id=request.research_query_id,
            target_audience=target_audience,
            tone=tone,
        )

        logger.info(f"Blog generation queued: content_id={content_item.id}")

        return BlogGenerationResponse(
            id=content_item.id,
            content_type=content_item.content_type,
            title=content_item.title,
            status=content_item.status,
            file_path=content_item.file_path,
            created_at=content_item.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue blog generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/generate-blog/sync', response_model=BlogContentResponse)
async def generate_blog_sync(
    request: BlogFromResearchRequest,
    service: ContentService = Depends(get_content_service),
):
    """
    Generate a blog post from existing research results (synchronous).
    
    This endpoint waits for the blog to be generated and returns the full content.
    Use this for real-time generation when you need the result immediately.
    """
    try:
        # Verify research exists
        _, error = service.verify_research_exists(request.research_query_id)
        if error:
            raise HTTPException(status_code=404, detail=error)

        # Generate blog synchronously
        content_item = await service.generate_blog_sync(request)

        logger.info(f"Sync blog generation completed: content_id={content_item.id}")

        return BlogContentResponse(
            id=content_item.id,
            research_query_id=content_item.research_query_id,
            content_type=content_item.content_type,
            title=content_item.title or '',
            content=content_item.content or '',
            meta_description=content_item.meta_description or '',
            tags=content_item.tags or [],
            estimated_reading_time='5 min read',
            file_path=content_item.file_path,
            target_audience=content_item.target_audience,
            tone=content_item.tone,
            status=content_item.status,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sync blog generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{content_id}', response_model=BlogContentResponse)
async def get_content(
    content_id: int,
    service: ContentService = Depends(get_content_service),
):
    """Get content item by ID with full content"""
    content = service.get_content(content_id)

    if not content:
        raise HTTPException(status_code=404, detail='Content not found')

    return BlogContentResponse(
        id=content.id,
        research_query_id=content.research_query_id,
        content_type=content.content_type,
        title=content.title or '',
        content=content.content or '',
        meta_description=content.meta_description or '',
        tags=content.tags or [],
        estimated_reading_time='5 min read',
        file_path=content.file_path,
        target_audience=content.target_audience,
        tone=content.tone,
        status=content.status,
    )


@router.get('/', response_model=List[BlogStatusResponse])
async def list_content(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    content_type: Optional[str] = Query(default=None, description='Filter by type (blog, etc.)'),
    service: ContentService = Depends(get_content_service),
):
    """List content items with pagination"""
    items = service.list_content(skip=offset, limit=limit, content_type=content_type)

    return [ContentService.to_status_response(item) for item in items]


content_router = router
