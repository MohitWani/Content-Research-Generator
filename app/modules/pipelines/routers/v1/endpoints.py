"""
Pipelines API Routes
End-to-end workflow orchestration endpoints
"""
import asyncio
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.pipelines.schemas.pipeline_schemas import (
    FullPipelineRequest,
    PipelineExecutionResponse,
    PipelineStatusResponse,
)
from app.modules.pipelines.services import PipelineService, get_pipeline_service
from app.modules.research.models.research_model import PipelineExecution
from database.database import get_db, SessionLocal

router = APIRouter()


# Response Schemas
class PipelineResultResponse(BaseModel):
    """Full pipeline result response"""

    query: str
    status: str
    pipeline_id: Optional[int] = None
    research_query_id: Optional[int] = None
    category: Optional[str] = None
    steps_completed: int
    total_steps: int
    research: Optional[Dict[str, Any]] = None
    blog: Optional[Dict[str, Any]] = None
    social: Optional[Dict[str, Any]] = None
    branding: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: Optional[str] = None


class AsyncPipelineResponse(BaseModel):
    """Response for async pipeline start"""

    pipeline_id: int
    status: str
    message: str


def run_pipeline_background(
    query: str,
    target_audience: str,
    content_types: List[str],
    apply_branding: bool,
    generate_social: bool,
):
    """Background task for pipeline execution"""
    asyncio.run(
        _execute_pipeline_async(
            query, target_audience, content_types, apply_branding, generate_social
        )
    )


async def _execute_pipeline_async(
    query: str,
    target_audience: str,
    content_types: List[str],
    apply_branding: bool,
    generate_social: bool,
):
    """Execute pipeline asynchronously"""
    db = SessionLocal()
    try:
        service = get_pipeline_service()
        await service.run_full_pipeline(
            query=query,
            target_audience=target_audience,
            content_types=content_types,
            apply_branding=apply_branding,
            generate_social=generate_social,
        )
    except Exception as e:
        logger.error(f'Pipeline execution failed: {e}', exc_info=True)
    finally:
        db.close()


@router.post('/full', response_model=PipelineResultResponse)
async def run_full_pipeline(
    request: FullPipelineRequest,
    db: Session = Depends(get_db),
):
    """
    Run full research -> content generation pipeline (synchronous).
    
    This endpoint executes the complete workflow:
    1. Categorize query
    2. Research topic
    3. Generate blog (if requested)
    4. Apply branding (if enabled)
    5. Generate social content (if enabled)
    
    Returns complete results when finished.
    """
    try:
        service = get_pipeline_service()
        result = await service.run_full_pipeline(
            query=request.query,
            target_audience=request.target_audience,
            content_types=request.content_types,
            apply_branding=request.apply_branding,
            generate_social=request.generate_social,
        )

        return PipelineResultResponse(
            query=result['query'],
            status=result['status'],
            pipeline_id=result.get('pipeline_id'),
            research_query_id=result.get('research_query_id'),
            category=result.get('category'),
            steps_completed=result['steps_completed'],
            total_steps=result['total_steps'],
            research=result.get('research'),
            blog=result.get('blog'),
            social=result.get('social'),
            branding=result.get('branding'),
            error=result.get('error'),
            completed_at=result.get('completed_at'),
        )

    except Exception as e:
        logger.error(f'Pipeline failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    '/full/async',
    response_model=AsyncPipelineResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def run_full_pipeline_async(
    request: FullPipelineRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start full pipeline in background (asynchronous).
    
    Returns immediately with pipeline_id.
    Use GET /pipelines/{pipeline_id} to check status.
    """
    try:
        # Create pipeline execution record
        pipeline = PipelineExecution(
            pipeline_type='full',
            status='pending',
            execution_data={
                'query': request.query,
                'target_audience': request.target_audience,
                'content_types': request.content_types,
            },
        )
        db.add(pipeline)
        db.commit()
        db.refresh(pipeline)

        # Start background task
        background_tasks.add_task(
            run_pipeline_background,
            query=request.query,
            target_audience=request.target_audience,
            content_types=request.content_types,
            apply_branding=request.apply_branding,
            generate_social=request.generate_social,
        )

        logger.info(f'Started async pipeline: {pipeline.id}')

        return AsyncPipelineResponse(
            pipeline_id=pipeline.id,
            status='pending',
            message='Pipeline started. Use GET /pipelines/{id} to check status.',
        )

    except Exception as e:
        logger.error(f'Failed to start pipeline: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/{pipeline_id}', response_model=PipelineExecutionResponse)
async def get_pipeline_status(
    pipeline_id: int,
    db: Session = Depends(get_db),
):
    """Get pipeline execution status by ID"""
    pipeline = db.get(PipelineExecution, pipeline_id)

    if not pipeline:
        raise HTTPException(status_code=404, detail='Pipeline not found')

    return PipelineExecutionResponse(
        id=pipeline.id,
        pipeline_type=pipeline.pipeline_type,
        research_query_id=pipeline.research_query_id,
        status=pipeline.status,
        started_at=pipeline.started_at,
        completed_at=pipeline.completed_at,
        error_message=pipeline.error_message,
        execution_data=pipeline.execution_data,
    )


@router.get('/', response_model=List[PipelineExecutionResponse])
async def list_pipelines(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List pipeline executions with pagination"""
    stmt = select(PipelineExecution).offset(skip).limit(limit)

    if status_filter:
        stmt = stmt.where(PipelineExecution.status == status_filter)

    stmt = stmt.order_by(PipelineExecution.started_at.desc())

    result = db.execute(stmt)
    pipelines = result.scalars().all()

    return [
        PipelineExecutionResponse(
            id=p.id,
            pipeline_type=p.pipeline_type,
            research_query_id=p.research_query_id,
            status=p.status,
            started_at=p.started_at,
            completed_at=p.completed_at,
            error_message=p.error_message,
            execution_data=p.execution_data,
        )
        for p in pipelines
    ]


@router.post('/research-only', response_model=Dict[str, Any])
async def run_research_only(
    query: str,
    target_audience: str = 'practitioner',
):
    """
    Run research-only pipeline.
    Returns research results without content generation.
    """
    try:
        service = get_pipeline_service()
        result = await service.run_research_only(
            query=query,
            target_audience=target_audience,
        )

        return {
            'topic_summary': result.topic_summary,
            'key_concepts': result.key_concepts,
            'mathematical_foundations': result.mathematical_foundations,
            'implementation_examples': result.implementation_examples,
            'sources': result.sources,
            'completeness_score': result.completeness_score,
            'data_path': result.research_data_path,
        }

    except Exception as e:
        logger.error(f'Research pipeline failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


pipelines_router = router
