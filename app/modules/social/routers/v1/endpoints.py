"""
Social API Routes

This module contains only API endpoint definitions for LinkedIn.
Business logic is handled by the SocialService.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.logging.logger import logger
from sqlalchemy.orm import Session

from app.modules.social.schemas.social_schemas import (
    LinkedInFromBlogRequest,
    LinkedInFromResearchRequest,
    LinkedInGenerateRequest,
    LinkedInResponse,
)
from database.database import get_db
from app.modules.social.services.social_service import SocialService

router = APIRouter()


def get_social_service(db: Session = Depends(get_db)) -> SocialService:
    """Dependency to get SocialService instance"""
    return SocialService(db=db)


# ============= API Endpoints =============

@router.post('/linkedin', response_model=LinkedInResponse)
async def generate_linkedin_post(
    request: LinkedInGenerateRequest,
    service: SocialService = Depends(get_social_service),
):
    """
    Generate a LinkedIn post from content.
    
    This endpoint creates an engaging LinkedIn post from the provided
    topic and source content.
    """
    try:
        output = await service.generate_linkedin_post(request)

        logger.info(f"LinkedIn post generated: {output.character_count} chars")

        return SocialService.to_linkedin_response(output)

    except Exception as e:
        logger.error(f'LinkedIn generation failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/linkedin/from-blog', response_model=LinkedInResponse)
async def generate_linkedin_from_blog(
    request: LinkedInFromBlogRequest,
    service: SocialService = Depends(get_social_service),
):
    """
    Generate a LinkedIn post from a blog post.
    
    This endpoint creates an engaging LinkedIn post from blog content.
    """
    try:
        output = await service.generate_linkedin_from_blog(
            blog_title=request.title,
            blog_content=request.content,
            target_audience=request.target_audience,
            user_instructions=request.user_instructions,
        )

        logger.info(f"LinkedIn from blog generated: {output.character_count} chars")

        return SocialService.to_linkedin_response(output)

    except Exception as e:
        logger.error(f'LinkedIn from blog generation failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/linkedin/from-research', response_model=LinkedInResponse)
async def generate_linkedin_from_research(
    request: LinkedInFromResearchRequest,
    service: SocialService = Depends(get_social_service),
):
    """
    Generate a LinkedIn post from research results.
    
    This endpoint creates an engaging LinkedIn post from existing
    research data collected via the research endpoints.
    """
    try:
        output = await service.generate_linkedin_from_research(
            research_query_id=request.research_query_id,
            target_audience=request.target_audience,
            user_instructions=request.user_instructions,
        )

        logger.info(f"LinkedIn from research generated: {output.character_count} chars")

        return SocialService.to_linkedin_response(output)

    except ValueError as e:
        logger.error(f'Research data not found: {e}')
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f'LinkedIn from research generation failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


social_router = router
