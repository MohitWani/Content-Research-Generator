"""
Pydantic schemas for Pipeline API
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PipelineTypeEnum(str, Enum):
    """Pipeline type enumeration"""
    
    RESEARCH = 'research'
    BLOG = 'blog'
    FULL = 'full'
    PAPER = 'paper'
    SOCIAL = 'social'


class PipelineStatusEnum(str, Enum):
    """Pipeline status enumeration"""
    
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class FullPipelineRequest(BaseModel):
    """Request for full pipeline execution"""

    query: str = Field(
        ...,
        description='Research query to process',
        min_length=5,
        max_length=1000,
    )
    target_audience: str = Field(
        default='practitioner',
        description='Target audience (beginner, practitioner, expert)',
    )
    content_types: List[str] = Field(
        default=['blog'],
        description='Content types to generate',
    )
    apply_branding: bool = Field(
        default=True,
        description='Whether to apply brand voice',
    )
    generate_social: bool = Field(
        default=False,
        description='Whether to generate social media content',
    )


class PipelineExecutionResponse(BaseModel):
    """Response for pipeline execution status"""

    id: int = Field(..., description='Pipeline execution ID')
    pipeline_type: str = Field(..., description='Type of pipeline')
    research_query_id: Optional[int] = Field(None, description='Associated research query ID')
    status: str = Field(..., description='Current status')
    started_at: datetime = Field(..., description='Start timestamp')
    completed_at: Optional[datetime] = Field(None, description='Completion timestamp')
    error_message: Optional[str] = Field(None, description='Error message if failed')
    execution_data: Optional[Dict[str, Any]] = Field(None, description='Execution data')

    class Config:
        from_attributes = True


class PipelineStatusResponse(BaseModel):
    """Simplified pipeline status response"""

    id: int
    status: str
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    current_step: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
    error_message: Optional[str] = None
