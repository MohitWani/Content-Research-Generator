"""
Branding API Routes
Brand voice application endpoints
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logging.logger import logger
from app.modules.branding.services import (
    BrandingAgent,
    BrandingOutput,
    VoiceProfile,
    get_branding_agent,
)

router = APIRouter()


# Request Schemas
class ApplyBrandingRequest(BaseModel):
    """Request for applying branding to content"""

    content: str = Field(..., min_length=50, max_length=15000)
    target_audience: str = Field(default='practitioner')
    content_type: str = Field(default='blog')


class CheckAlignmentRequest(BaseModel):
    """Request for checking brand alignment"""

    content: str = Field(..., min_length=50, max_length=15000)
    target_audience: str = Field(default='practitioner')


class VoiceProfileUpdate(BaseModel):
    """Request for updating voice profile"""

    brand_name: Optional[str] = None
    tone: Optional[str] = None
    style: Optional[str] = None
    do_list: Optional[List[str]] = None
    dont_list: Optional[List[str]] = None


# Response Schemas
class BrandingResponse(BaseModel):
    """Response for branding application"""

    original_content: str
    branded_content: str
    changes_made: List[str]
    voice_score: float
    suggestions: List[str]
    file_path: Optional[str] = None


class AlignmentResponse(BaseModel):
    """Response for alignment check"""

    alignment_score: float
    is_aligned: bool
    issues: List[str]
    strengths: List[str]
    suggestions: List[str]
    changes_needed: List[str]


class VoiceProfileResponse(BaseModel):
    """Response for voice profile"""

    brand_name: str
    tone: str
    style: str
    target_audiences: Dict[str, str]
    voice_characteristics: Dict[str, str]
    do_list: List[str]
    dont_list: List[str]


@router.post('/apply', response_model=BrandingResponse)
async def apply_branding(request: ApplyBrandingRequest):
    """
    Apply brand voice to content.
    Returns branded content with changes made.
    """
    try:
        agent = get_branding_agent()
        result = await agent.apply_branding(
            content=request.content,
            target_audience=request.target_audience,
            content_type=request.content_type,
        )

        return BrandingResponse(
            original_content=result.original_content,
            branded_content=result.branded_content,
            changes_made=result.changes_made,
            voice_score=result.voice_score,
            suggestions=result.suggestions,
            file_path=result.file_path,
        )

    except Exception as e:
        logger.error(f'Branding application failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/check-alignment', response_model=AlignmentResponse)
async def check_alignment(request: CheckAlignmentRequest):
    """
    Check if content aligns with brand voice.
    Returns alignment score and issues without modifying content.
    """
    try:
        agent = get_branding_agent()
        result = await agent.check_alignment(
            content=request.content,
            target_audience=request.target_audience,
        )

        return AlignmentResponse(
            alignment_score=result['alignment_score'],
            is_aligned=result['is_aligned'],
            issues=result['issues'],
            strengths=result['strengths'],
            suggestions=result['suggestions'],
            changes_needed=result['changes_needed'],
        )

    except Exception as e:
        logger.error(f'Alignment check failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/voice-profile', response_model=VoiceProfileResponse)
async def get_voice_profile():
    """
    Get current voice profile settings.
    """
    try:
        agent = get_branding_agent()
        vp = agent.voice_profile

        return VoiceProfileResponse(
            brand_name=vp.brand_name,
            tone=vp.tone,
            style=vp.style,
            target_audiences=vp.target_audiences,
            voice_characteristics=vp.voice_characteristics,
            do_list=vp.do_list,
            dont_list=vp.dont_list,
        )

    except Exception as e:
        logger.error(f'Failed to get voice profile: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/voice-profile', response_model=VoiceProfileResponse)
async def update_voice_profile(update: VoiceProfileUpdate):
    """
    Update voice profile settings.
    Only provided fields will be updated.
    """
    try:
        agent = get_branding_agent()
        vp = agent.voice_profile

        # Update only provided fields
        if update.brand_name is not None:
            vp.brand_name = update.brand_name
        if update.tone is not None:
            vp.tone = update.tone
        if update.style is not None:
            vp.style = update.style
        if update.do_list is not None:
            vp.do_list = update.do_list
        if update.dont_list is not None:
            vp.dont_list = update.dont_list

        # Save updated profile
        if not agent.save_voice_profile():
            raise HTTPException(status_code=500, detail='Failed to save voice profile')

        return VoiceProfileResponse(
            brand_name=vp.brand_name,
            tone=vp.tone,
            style=vp.style,
            target_audiences=vp.target_audiences,
            voice_characteristics=vp.voice_characteristics,
            do_list=vp.do_list,
            dont_list=vp.dont_list,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Failed to update voice profile: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/guidelines')
async def get_brand_guidelines(target_audience: str = 'practitioner'):
    """
    Get formatted brand guidelines for a target audience.
    """
    try:
        agent = get_branding_agent()
        guidelines = agent.get_guidelines(target_audience)

        return {'guidelines': guidelines, 'target_audience': target_audience}

    except Exception as e:
        logger.error(f'Failed to get guidelines: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


branding_router = router
