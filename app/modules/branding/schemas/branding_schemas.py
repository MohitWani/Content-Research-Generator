"""
Pydantic schemas for Branding API
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ApplyBrandingRequest(BaseModel):
    """Request for applying branding to content"""

    content: str = Field(
        ...,
        description='Content to apply branding to',
        min_length=50,
        max_length=15000,
    )
    target_audience: str = Field(
        default='practitioner',
        description='Target audience',
    )
    content_type: str = Field(
        default='blog',
        description='Type of content (blog, linkedin, twitter)',
    )


class BrandingResponse(BaseModel):
    """Response for branding application"""

    original_content: str = Field(..., description='Original content')
    branded_content: str = Field(..., description='Branded content')
    changes_made: List[str] = Field(default_factory=list, description='Changes made')
    voice_score: float = Field(default=0.0, ge=0.0, le=1.0, description='Voice alignment score')
    suggestions: List[str] = Field(default_factory=list, description='Improvement suggestions')
    file_path: Optional[str] = Field(None, description='Saved file path')


class CheckAlignmentRequest(BaseModel):
    """Request for checking brand alignment"""

    content: str = Field(
        ...,
        description='Content to check',
        min_length=50,
        max_length=15000,
    )
    target_audience: str = Field(
        default='practitioner',
        description='Target audience',
    )


class AlignmentResponse(BaseModel):
    """Response for alignment check"""

    alignment_score: float = Field(..., ge=0.0, le=1.0, description='Alignment score')
    is_aligned: bool = Field(..., description='Whether content is aligned')
    issues: List[str] = Field(default_factory=list, description='Issues found')
    strengths: List[str] = Field(default_factory=list, description='Strengths found')
    suggestions: List[str] = Field(default_factory=list, description='Improvement suggestions')
    changes_needed: List[str] = Field(default_factory=list, description='Changes needed')


class VoiceProfileUpdate(BaseModel):
    """Request for updating voice profile"""

    brand_name: Optional[str] = Field(None, description='Brand name')
    tone: Optional[str] = Field(None, description='Primary tone')
    style: Optional[str] = Field(None, description='Writing style')
    do_list: Optional[List[str]] = Field(None, description='Things to do')
    dont_list: Optional[List[str]] = Field(None, description='Things to avoid')


class VoiceProfileResponse(BaseModel):
    """Response for voice profile"""

    brand_name: str = Field(..., description='Brand name')
    tone: str = Field(..., description='Primary tone')
    style: str = Field(..., description='Writing style')
    target_audiences: Dict[str, str] = Field(default_factory=dict, description='Audience guidelines')
    voice_characteristics: Dict[str, str] = Field(default_factory=dict, description='Voice characteristics')
    do_list: List[str] = Field(default_factory=list, description='Things to do')
    dont_list: List[str] = Field(default_factory=list, description='Things to avoid')
