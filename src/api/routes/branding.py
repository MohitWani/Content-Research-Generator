"""
Branding API Routes
Endpoints for brand voice application, checking, and profile management
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from src.common.database import get_db
from src.lib.agents.branding_agent import BrandingAgent
from src.lib.models.research import ContentItem
from src.common.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


# ============= Request/Response Schemas =============

class ApplyBrandingRequest(BaseModel):
    """Request to apply branding to content"""
    content: str = Field(..., description="Content to brand")
    content_id: Optional[int] = Field(None, description="Or provide content ID to fetch")
    target_audience: str = Field(default="practitioner")
    content_type: str = Field(default="blog")


class ApplyBrandingResponse(BaseModel):
    """Response from branding application"""
    original_content: str
    branded_content: str
    changes_made: List[str]
    voice_score: float
    suggestions: List[str]


class CheckAlignmentRequest(BaseModel):
    """Request to check voice alignment"""
    content: str = Field(..., description="Content to analyze")
    target_audience: str = Field(default="practitioner")


class CheckAlignmentResponse(BaseModel):
    """Response from alignment check"""
    alignment_score: float
    tone_match: bool
    style_match: bool
    audience_appropriate: bool
    issues: List[str]
    strengths: List[str]
    recommendations: List[str]


class StyleSuggestionsRequest(BaseModel):
    """Request for style suggestions"""
    content: str = Field(..., description="Content to analyze")


class StyleSuggestionsResponse(BaseModel):
    """Response with style suggestions"""
    suggestions: List[str]


class VoiceProfileResponse(BaseModel):
    """Voice profile information"""
    brand_name: str
    tone: str
    style: str
    target_audiences: Dict[str, str]
    voice_characteristics: Dict[str, Any]
    do_list: List[str]
    dont_list: List[str]


class GuidelinesRequest(BaseModel):
    """Request for audience-specific guidelines"""
    audience: str = Field(default="practitioner")


class GuidelinesResponse(BaseModel):
    """Guidelines for specific audience"""
    audience: str
    guidelines: str


# ============= Endpoints =============

@router.post("/apply", response_model=ApplyBrandingResponse)
async def apply_branding(
    request: ApplyBrandingRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Apply brand voice and style to content
    """
    try:
        branding_agent = BrandingAgent()
        
        # Get content - either from request or database
        content = request.content
        if not content and request.content_id:
            content_item = await db.get(ContentItem, request.content_id)
            if not content_item:
                raise HTTPException(status_code=404, detail="Content not found")
            content = content_item.content
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        # Apply branding
        result = await branding_agent.apply_branding(
            content=content,
            target_audience=request.target_audience,
            content_type=request.content_type,
        )
        
        logger.info(f"Applied branding with voice score: {result.voice_score:.2f}")
        
        return ApplyBrandingResponse(
            original_content=result.original_content,
            branded_content=result.branded_content,
            changes_made=result.changes_made,
            voice_score=result.voice_score,
            suggestions=result.suggestions,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Branding application failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check", response_model=CheckAlignmentResponse)
async def check_voice_alignment(
    request: CheckAlignmentRequest,
):
    """
    Check how well content aligns with brand voice
    """
    try:
        branding_agent = BrandingAgent()
        
        result = await branding_agent.check_voice_alignment(
            content=request.content,
            target_audience=request.target_audience,
        )
        
        logger.info(f"Voice alignment check: {result.get('alignment_score', 0):.2f}")
        
        return CheckAlignmentResponse(
            alignment_score=float(result.get("alignment_score", 0.5)),
            tone_match=result.get("tone_match", False),
            style_match=result.get("style_match", False),
            audience_appropriate=result.get("audience_appropriate", False),
            issues=result.get("issues", []),
            strengths=result.get("strengths", []),
            recommendations=result.get("recommendations", []),
        )
        
    except Exception as e:
        logger.error(f"Voice alignment check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions", response_model=StyleSuggestionsResponse)
async def get_style_suggestions(
    request: StyleSuggestionsRequest,
):
    """
    Get style improvement suggestions for content
    """
    try:
        branding_agent = BrandingAgent()
        
        suggestions = await branding_agent.generate_style_suggestions(
            content=request.content,
        )
        
        return StyleSuggestionsResponse(suggestions=suggestions)
        
    except Exception as e:
        logger.error(f"Style suggestions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile", response_model=VoiceProfileResponse)
async def get_voice_profile():
    """
    Get current voice profile configuration
    """
    try:
        branding_agent = BrandingAgent()
        profile = branding_agent.voice_profile
        
        return VoiceProfileResponse(
            brand_name=profile.brand_name,
            tone=profile.tone,
            style=profile.style,
            target_audiences=profile.target_audiences,
            voice_characteristics=profile.voice_characteristics,
            do_list=profile.do_list,
            dont_list=profile.dont_list,
        )
        
    except Exception as e:
        logger.error(f"Failed to get voice profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/guidelines", response_model=GuidelinesResponse)
async def get_audience_guidelines(
    request: GuidelinesRequest,
):
    """
    Get text guidelines for a specific audience
    """
    try:
        branding_agent = BrandingAgent()
        
        guidelines = branding_agent.get_guidelines_for_audience(request.audience)
        
        return GuidelinesResponse(
            audience=request.audience,
            guidelines=guidelines,
        )
        
    except Exception as e:
        logger.error(f"Failed to get guidelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


