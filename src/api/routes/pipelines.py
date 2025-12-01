"""
Pipeline API Routes
Endpoints for running and monitoring pipelines
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from src.common.database import get_db
from src.lib.models.research import PipelineExecution
from src.lib.pipelines.research_pipeline import ResearchPipeline
from src.lib.pipelines.blog_pipeline import BlogGenerationPipeline
from src.common.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


class FullPipelineRequest(BaseModel):
    """Request for full pipeline execution"""
    query_text: str
    target_audience: str = "practitioner"
    tone: str = "professional"
    generate_social: bool = True


class FullPipelineResponse(BaseModel):
    """Response from full pipeline execution"""
    research_query_id: int
    content_id: int
    blog_title: str
    completeness_score: float
    execution_time_seconds: float
    status: str


class PipelineExecutionResponse(BaseModel):
    """Pipeline execution status"""
    id: int
    pipeline_type: str
    status: str
    research_query_id: Optional[int]
    started_at: str
    completed_at: Optional[str]
    error_message: Optional[str]


@router.post("/full", response_model=FullPipelineResponse)
async def execute_full_pipeline(
    request: FullPipelineRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute full pipeline: Research → Blog → Social
    
    Complete end-to-end content generation from query
    """
    try:
        # Execute research pipeline
        research_pipeline = ResearchPipeline(db_session=db)
        research_result = await research_pipeline.execute(
            query=request.query_text,
            target_audience=request.target_audience,
        )
        
        await db.commit()
        
        # Execute blog pipeline
        blog_pipeline = BlogGenerationPipeline(db_session=db)
        blog_result = await blog_pipeline.execute(
            research_query_id=research_result.query_id,
            target_audience=request.target_audience,
            tone=request.tone,
            generate_social=request.generate_social,
        )
        
        await db.commit()
        
        total_time = (
            research_result.execution_time_seconds + 
            blog_result.execution_time_seconds
        )
        
        logger.info(
            f"Full pipeline completed in {total_time:.2f}s "
            f"(query_id={research_result.query_id})"
        )
        
        return FullPipelineResponse(
            research_query_id=research_result.query_id,
            content_id=blog_result.content_id,
            blog_title=blog_result.blog_output.title,
            completeness_score=research_result.completeness_score,
            execution_time_seconds=total_time,
            status="completed",
        )
        
    except Exception as e:
        logger.error(f"Full pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions", response_model=List[PipelineExecutionResponse])
async def list_pipeline_executions(
    skip: int = 0,
    limit: int = 20,
    pipeline_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List pipeline executions with filtering"""
    query = select(PipelineExecution).offset(skip).limit(limit)
    
    if pipeline_type:
        query = query.where(PipelineExecution.pipeline_type == pipeline_type)
    
    if status:
        query = query.where(PipelineExecution.status == status)
    
    query = query.order_by(PipelineExecution.started_at.desc())
    
    result = await db.execute(query)
    executions = result.scalars().all()
    
    return [
        PipelineExecutionResponse(
            id=e.id,
            pipeline_type=e.pipeline_type,
            status=e.status,
            research_query_id=e.research_query_id,
            started_at=e.started_at.isoformat() if e.started_at else None,
            completed_at=e.completed_at.isoformat() if e.completed_at else None,
            error_message=e.error_message,
        )
        for e in executions
    ]


@router.get("/executions/{execution_id}", response_model=PipelineExecutionResponse)
async def get_pipeline_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get pipeline execution by ID"""
    execution = await db.get(PipelineExecution, execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Pipeline execution not found")
    
    return PipelineExecutionResponse(
        id=execution.id,
        pipeline_type=execution.pipeline_type,
        status=execution.status,
        research_query_id=execution.research_query_id,
        started_at=execution.started_at.isoformat() if execution.started_at else None,
        completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
        error_message=execution.error_message,
    )

