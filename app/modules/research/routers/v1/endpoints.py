"""
Research API Routes

This module contains only API endpoint definitions.
Business logic is handled by the ResearchService.
Database operations are handled by repositories.
"""
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.research.schemas.research_schemas import (
    ResearchQueryRequest,
    ResearchQueryResponse,
    ResearchResultResponse,
    ResearchStatusResponse,
)
from app.modules.research.services.background_task_service import BackgroundTaskService
from app.modules.research.services.research_service import ResearchService
from database.database import get_db

router = APIRouter()


def get_research_service(db: Session = Depends(get_db)) -> ResearchService:
    """Dependency to get ResearchService instance"""
    return ResearchService(db)


@router.post(
    "/query",
    response_model=ResearchQueryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_research_query(
    request: ResearchQueryRequest,
    background_tasks: BackgroundTasks,
    service: ResearchService = Depends(get_research_service),
):
    """
    Create a new research query and trigger background research.
    
    Returns 202 Accepted with query_id. Use GET /query/{query_id} to check status.
    """
    try:
        # Create the query record
        query_record = service.create_research_query(request)

        # Queue background task for research execution
        target_audience = (
            request.target_audience.value if request.target_audience else "practitioner"
        )
        content_type = request.content_type.value if request.content_type else "blog"

        background_tasks.add_task(
            BackgroundTaskService.run_research_task,
            query_id=query_record.id,
            query_text=request.query,
            target_audience=target_audience,
            content_type=content_type,
        )

        logger.info(f"Queued background research task for query: {query_record.id}")

        return ResearchService.to_query_response(query_record)

    except Exception as e:
        logger.error(f"Failed to create research query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/{query_id}", response_model=ResearchStatusResponse)
async def get_research_query(
    query_id: int,
    service: ResearchService = Depends(get_research_service),
):
    """Get research query by ID"""
    query = service.get_research_query(query_id)

    if not query:
        raise HTTPException(status_code=404, detail="Research query not found")

    return ResearchService.to_status_response(query)


@router.get("/query/{query_id}/result", response_model=ResearchResultResponse)
async def get_research_result(
    query_id: int,
    service: ResearchService = Depends(get_research_service),
):
    """Get research result for a query"""
    result = service.get_research_result(query_id)

    if not result:
        raise HTTPException(status_code=404, detail="Research result not found")

    return ResearchService.to_result_response(result)


@router.get("/queries", response_model=List[ResearchStatusResponse])
async def list_research_queries(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    service: ResearchService = Depends(get_research_service),
):
    """List research queries with pagination"""
    queries = service.list_research_queries(skip=skip, limit=limit, status=status)

    return [ResearchService.to_status_response(q) for q in queries]


@router.post("/query/sync", response_model=ResearchResultResponse)
async def create_research_sync(
    request: ResearchQueryRequest,
    service: ResearchService = Depends(get_research_service),
):
    """Create research query and wait for result (synchronous)"""
    try:
        result = await service.execute_sync_research(request)

        logger.info(f"Sync research completed: query_id={result.query_id}")

        return ResearchService.to_result_response(result)

    except Exception as e:
        logger.error(f"Sync research failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


research_router = router
