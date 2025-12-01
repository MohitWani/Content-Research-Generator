"""
Content API Routes
Endpoints for blog and content generation
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.common.database import get_db
from src.lib.models.research import ContentItem
from src.lib.models.schemas import (
    BlogGenerationRequest,
    BlogGenerationResponse,
    ContentItemResponse,
)
from src.lib.orchestrator.workflow_manager import WorkflowManager
from src.lib.pipelines.blog_pipeline import BlogGenerationPipeline
from src.common.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/blog/generate", response_model=BlogGenerationResponse)
async def generate_blog(
    request: BlogGenerationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a blog post from research data
    
    Requires existing research query ID
    """
    try:
        pipeline = BlogGenerationPipeline(db_session=db)
        
        result = await pipeline.execute(
            research_query_id=request.research_query_id,
            target_audience=request.target_audience,
            tone=request.tone,
            apply_branding=True,
            generate_social=request.generate_linkedin_post,
        )
        
        await db.commit()
        
        return BlogGenerationResponse(
            content_id=result.content_id,
            title=result.blog_output.title,
            content=result.blog_output.content,
            target_audience=result.blog_output.target_audience,
            status=result.status,
            file_path=result.blog_output.file_path,
            linkedin_post=result.linkedin_post.content if result.linkedin_post else None,
        )
        
    except Exception as e:
        logger.error(f"Blog generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blog/{content_id}", response_model=ContentItemResponse)
async def get_blog(
    content_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get blog content by ID"""
    content = await db.get(ContentItem, content_id)
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return ContentItemResponse(
        id=content.id,
        research_query_id=content.research_query_id,
        content_type=content.content_type,
        title=content.title,
        content=content.content,
        target_audience=content.target_audience,
        tone=content.tone,
        status=content.status,
        file_path=content.file_path,
        created_at=content.created_at,
    )


@router.get("/blogs", response_model=List[ContentItemResponse])
async def list_blogs(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List blog posts with pagination"""
    query = (
        select(ContentItem)
        .where(ContentItem.content_type == "blog")
        .offset(skip)
        .limit(limit)
    )
    
    if status:
        query = query.where(ContentItem.status == status)
    
    query = query.order_by(ContentItem.created_at.desc())
    
    result = await db.execute(query)
    contents = result.scalars().all()
    
    return [
        ContentItemResponse(
            id=c.id,
            research_query_id=c.research_query_id,
            content_type=c.content_type,
            title=c.title,
            content=c.content,
            target_audience=c.target_audience,
            tone=c.tone,
            status=c.status,
            file_path=c.file_path,
            created_at=c.created_at,
        )
        for c in contents
    ]


@router.get("/query/{query_id}/content", response_model=List[ContentItemResponse])
async def get_content_for_query(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all content generated for a research query"""
    result = await db.execute(
        select(ContentItem)
        .where(ContentItem.research_query_id == query_id)
        .order_by(ContentItem.created_at.desc())
    )
    contents = result.scalars().all()
    
    return [
        ContentItemResponse(
            id=c.id,
            research_query_id=c.research_query_id,
            content_type=c.content_type,
            title=c.title,
            content=c.content,
            target_audience=c.target_audience,
            tone=c.tone,
            status=c.status,
            file_path=c.file_path,
            created_at=c.created_at,
        )
        for c in contents
    ]

