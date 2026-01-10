"""
Research API Routes
"""
import asyncio
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.research.models.research_model import (
    ResearchQuery,
    ResearchResult,
    TopicCategory,
)
from app.modules.research.schemas.research_schemas import (
    ResearchQueryRequest,
    ResearchQueryResponse,
    ResearchResultResponse,
    ResearchStatusResponse,
)
from app.modules.research.services.agentic_researcher import AgenticResearcher
from app.modules.research.services.topic_agent import TopicAgent
from database.database import get_db, SessionLocal

router = APIRouter()


def run_research_background_task(
    query_id: int,
    query_text: str,
    target_audience: str,
    content_type: str,
):
    """
    Background task to run the agentic research flow.
    Uses asyncio.run() to execute async workflow in sync background task.
    """
    asyncio.run(
        _execute_research_workflow(query_id, query_text, target_audience, content_type)
    )


async def _execute_research_workflow(
    query_id: int,
    query_text: str,
    target_audience: str,
    content_type: str,
):
    """Execute the full research workflow asynchronously"""
    db = SessionLocal()
    try:
        # Step 1: Update status to processing
        query_record = db.get(ResearchQuery, query_id)
        if not query_record:
            logger.error(f'Query record not found: {query_id}')
            return

        query_record.status = 'processing'
        db.commit()

        # Step 2: Categorize the query
        topic_agent = TopicAgent()
        categorization = await topic_agent.categorize_query(query_text)

        category_map = {
            'core_ai': TopicCategory.CORE_AI,
            'practical_implementation': TopicCategory.PRACTICAL_IMPLEMENTATION,
            'software_development': TopicCategory.SOFTWARE_DEVELOPMENT,
            'web_development': TopicCategory.WEB_DEVELOPMENT,
            'devops': TopicCategory.DEVOPS,
            'general_tech': TopicCategory.GENERAL_TECH,
        }
        topic_category = category_map.get(
            categorization.category, TopicCategory.GENERAL_TECH
        )

        # Update query with category
        query_record.topic_category = topic_category.value
        db.commit()

        logger.info(f'Query {query_id} categorized as: {topic_category.value}')

        # Step 3: Run agentic research
        researcher = AgenticResearcher(max_iterations=5)
        research_output = await researcher.research(
            query=query_text,
            category=topic_category,
            target_audience=target_audience,
        )

        # Step 4: Persist research result
        research_result = ResearchResult(
            query_id=query_id,
            topic_summary=research_output.topic_summary,
            key_concepts=research_output.key_concepts,
            mathematical_foundations=research_output.mathematical_foundations,
            historical_context=research_output.source_descriptions,
            implementation_examples=research_output.implementation_examples,
            sources=research_output.sources,
            completeness_score=research_output.completeness_score,
            research_data_path=research_output.research_data_path,
        )
        db.add(research_result)

        # Step 5: Update query status to completed
        query_record.status = 'completed'
        db.commit()

        logger.info(f'Background research completed: query_id={query_id}')

    except Exception as e:
        logger.error(f'Background research failed for query {query_id}: {e}', exc_info=True)
        # Update status to failed
        try:
            query_record = db.get(ResearchQuery, query_id)
            if query_record:
                query_record.status = 'failed'
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post(
    '/query',
    response_model=ResearchQueryResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_research_query(
    request: ResearchQueryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new research query and trigger background research.
    
    Returns 202 Accepted with query_id. Use GET /query/{query_id} to check status.
    """
    try:
        target_audience = (
            request.target_audience.value if request.target_audience else 'practitioner'
        )
        content_type = request.content_type.value if request.content_type else 'blog'

        query_record = ResearchQuery(
            query_text=request.query,
            target_audience=target_audience,
            content_type=content_type,
            status='pending',
        )
        db.add(query_record)
        db.commit()
        db.refresh(query_record)

        logger.info(f'Created research query: {query_record.id}')

        # Add background task to execute research workflow
        background_tasks.add_task(
            run_research_background_task,
            query_id=query_record.id,
            query_text=request.query,
            target_audience=target_audience,
            content_type=content_type,
        )

        logger.info(f'Queued background research task for query: {query_record.id}')

        return ResearchQueryResponse(
            query_id=query_record.id,
            status=query_record.status,
            created_at=query_record.created_at,
        )

    except Exception as e:
        logger.error(f'Failed to create research query: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/query/{query_id}', response_model=ResearchStatusResponse)
async def get_research_query(
    query_id: int,
    db: Session = Depends(get_db),
):
    """Get research query by ID"""
    query = db.get(ResearchQuery, query_id)

    if not query:
        raise HTTPException(status_code=404, detail='Research query not found')

    return ResearchStatusResponse(
        id=query.id,
        query_text=query.query_text,
        target_audience=query.target_audience,
        topic_category=query.topic_category if query.topic_category else None,
        status=query.status,
        created_at=query.created_at,
        updated_at=query.updated_at or query.created_at,
    )


@router.get('/query/{query_id}/result', response_model=ResearchResultResponse)
async def get_research_result(
    query_id: int,
    db: Session = Depends(get_db),
):
    """Get research result for a query"""
    result = db.scalar(
        select(ResearchResult).where(ResearchResult.query_id == query_id)
    )

    if not result:
        raise HTTPException(status_code=404, detail='Research result not found')

    return ResearchResultResponse(
        query_id=result.query_id,
        topic_summary=result.topic_summary,
        key_concepts=result.key_concepts,
        mathematical_foundations=result.mathematical_foundations,
        historical_context=result.historical_context,
        implementation_examples=result.implementation_examples,
        sources=result.sources,
        completeness_score=result.completeness_score,
        created_at=result.created_at,
    )


@router.get('/queries', response_model=List[ResearchStatusResponse])
async def list_research_queries(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List research queries with pagination"""
    stmt = select(ResearchQuery).offset(skip).limit(limit)

    if status:
        stmt = stmt.where(ResearchQuery.status == status)

    stmt = stmt.order_by(ResearchQuery.created_at.desc())

    result = db.execute(stmt)
    queries = result.scalars().all()

    return [
        ResearchStatusResponse(
            id=q.id,
            query_text=q.query_text,
            target_audience=q.target_audience,
            topic_category=q.topic_category if q.topic_category else None,
            status=q.status,
            created_at=q.created_at,
            updated_at=q.updated_at or q.created_at,
        )
        for q in queries
    ]


@router.post('/query/sync', response_model=ResearchResultResponse)
async def create_research_sync(
    request: ResearchQueryRequest,
    db: Session = Depends(get_db),
):
    """Create research query and wait for result (synchronous)"""
    try:
        # Step 1: Categorize the query
        topic_agent = TopicAgent()
        categorization = await topic_agent.categorize_query(request.query)

        category_map = {
            'core_ai': TopicCategory.CORE_AI,
            'practical_implementation': TopicCategory.PRACTICAL_IMPLEMENTATION,
            'software_development': TopicCategory.SOFTWARE_DEVELOPMENT,
            'web_development': TopicCategory.WEB_DEVELOPMENT,
            'devops': TopicCategory.DEVOPS,
            'general_tech': TopicCategory.GENERAL_TECH,
        }
        topic_category = category_map.get(
            categorization.category, TopicCategory.GENERAL_TECH
        )

        logger.info(f'Query categorized as: {topic_category.value}')

        # Step 2: Create query record
        query_record = ResearchQuery(
            query_text=request.query,
            target_audience=request.target_audience.value
            if request.target_audience
            else 'practitioner',
            topic_category=topic_category.value,
            content_type=request.content_type.value
            if request.content_type
            else 'blog',
            status='processing',
        )
        db.add(query_record)
        db.flush()

        # Step 3: Run agentic research
        researcher = AgenticResearcher(max_iterations=5)
        research_output = await researcher.research(
            query=request.query,
            category=topic_category,
            target_audience=request.target_audience.value
            if request.target_audience
            else 'practitioner',
        )

        # Step 4: Persist research result
        research_result = ResearchResult(
            query_id=query_record.id,
            topic_summary=research_output.topic_summary,
            key_concepts=research_output.key_concepts,
            mathematical_foundations=research_output.mathematical_foundations,
            historical_context=research_output.source_descriptions,
            implementation_examples=research_output.implementation_examples,
            sources=research_output.sources,
            completeness_score=research_output.completeness_score,
            research_data_path=research_output.research_data_path,
        )
        db.add(research_result)

        # Step 5: Update query status
        query_record.status = 'completed'
        db.commit()
        db.refresh(research_result)

        logger.info(f'Sync research completed: query_id={query_record.id}')

        return ResearchResultResponse(
            query_id=research_result.query_id,
            topic_summary=research_result.topic_summary,
            key_concepts=research_result.key_concepts,
            mathematical_foundations=research_result.mathematical_foundations,
            historical_context=research_result.historical_context,
            implementation_examples=research_result.implementation_examples,
            sources=research_result.sources,
            completeness_score=research_result.completeness_score,
            created_at=research_result.created_at,
        )

    except Exception as e:
        logger.error(f'Sync research failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


research_router = router


