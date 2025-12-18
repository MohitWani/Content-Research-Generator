"""
Research API Routes
Endpoints for research queries and results
Uses AgenticResearcher with LangGraph's create_react_agent
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.common.database import get_db, get_session
from src.lib.models.research import ResearchQuery, ResearchResult, TopicCategory
from src.lib.models.schemas import (
    ResearchQueryRequest,
    ResearchQueryResponse,
    ResearchStatusResponse,
    ResearchResultResponse,
)
from src.lib.agents import AgenticResearcher, TopicAgent
from src.lib.pipelines.research_pipeline import ResearchPipeline
from src.common.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/query", response_model=ResearchQueryResponse)
async def create_research_query(
    request: ResearchQueryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new research query
    
    Initiates research workflow in background and returns query ID
    """
    try:
        # Create query record
        query_record = ResearchQuery(
            query_text=request.query,
            target_audience=request.target_audience,
            content_type=request.content_type,
            status="pending",
        )
        db.add(query_record)
        await db.commit()
        await db.refresh(query_record)

        logger.info(f"Created research query: {query_record.id}")
        # Execute research in background
        query_id = query_record.id
        query_text = request.query
        target_audience_str = request.target_audience

        logger.info(f"Running research for query: {query_text}, {target_audience_str}, {request.content_type}")

        async def run_research():
            async with get_session() as session:
                pipeline = ResearchPipeline(db_session=session)
                await pipeline.execute_for_query(
                    query_id=query_id,
                    query=query_text,
                    target_audience=target_audience_str,
                )
        
        logger.info(f"Added background task to run research")
        background_tasks.add_task(run_research)
        
        logger.info(f"Returned research query response: {query_record.id}")
        
        return ResearchQueryResponse(
            query_id=query_record.id,
            status=query_record.status,
            created_at=query_record.created_at,
        )
        
    except Exception as e:
        logger.error(f"Failed to create research query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/{query_id}", response_model=ResearchStatusResponse)
async def get_research_query(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get research query by ID"""
    query = await db.get(ResearchQuery, query_id)
    
    if not query:
        raise HTTPException(status_code=404, detail="Research query not found")
    
    return ResearchStatusResponse(
        id=query.id,
        query_text=query.query_text,
        target_audience=query.target_audience,
        topic_category=query.topic_category if query.topic_category else None,
        status=query.status,
        created_at=query.created_at,
        updated_at=query.updated_at or query.created_at,
    )


@router.get("/query/{query_id}/result", response_model=ResearchResultResponse)
async def get_research_result(
    query_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get research result for a query"""
    result = await db.scalar(
        select(ResearchResult).where(ResearchResult.query_id == query_id)
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Research result not found")
    
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


@router.get("/queries", response_model=List[ResearchStatusResponse])
async def list_research_queries(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List research queries with pagination"""
    stmt = select(ResearchQuery).offset(skip).limit(limit)
    
    if status:
        stmt = stmt.where(ResearchQuery.status == status)
    
    stmt = stmt.order_by(ResearchQuery.created_at.desc())
    
    result = await db.execute(stmt)
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


@router.post("/query/sync", response_model=ResearchResultResponse)
async def create_research_sync(
    request: ResearchQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create research query and wait for result (synchronous)
    
    Uses AgenticResearcher with LangGraph's create_react_agent
    for modern, clean agentic workflow.
    """
    try:
        # Step 1: Categorize the query
        topic_agent = TopicAgent()
        categorization = await topic_agent.categorize_query(request.query)
        
        # Map category string to enum
        category_map = {
            "core_ai": TopicCategory.CORE_AI,
            "practical_implementation": TopicCategory.PRACTICAL_IMPLEMENTATION,
            "software_development": TopicCategory.SOFTWARE_DEVELOPMENT,
            "web_development": TopicCategory.WEB_DEVELOPMENT,
            "devops": TopicCategory.DEVOPS,
            "general_tech": TopicCategory.GENERAL_TECH,
        }
        topic_category = category_map.get(categorization.category, TopicCategory.GENERAL_TECH)
        
        logger.info(f"Query categorized as: {topic_category.value}")
        
        # Step 2: Create query record
        query_record = ResearchQuery(
            query_text=request.query,
            target_audience=request.target_audience.value if request.target_audience else "practitioner",
            topic_category=topic_category.value,
            content_type=request.content_type.value if request.content_type else "blog",
            status="processing",
        )
        db.add(query_record)
        await db.flush()
        
        # Step 3: Run agentic research
        researcher = AgenticResearcher(max_iterations=5)
        research_output = await researcher.research(
            query=request.query,
            category=topic_category,
            target_audience=request.target_audience.value if request.target_audience else "practitioner",
        )
        
        # Step 4: Persist research result
        # Note: source_descriptions maps to historical_context in DB for backward compatibility
        research_result = ResearchResult(
            query_id=query_record.id,
            topic_summary=research_output.topic_summary,
            key_concepts=research_output.key_concepts,
            mathematical_foundations=research_output.mathematical_foundations,
            historical_context=research_output.source_descriptions,  # Contains all source descriptions
            implementation_examples=research_output.implementation_examples,
            sources=research_output.sources,
            completeness_score=research_output.completeness_score,
            research_data_path=research_output.research_data_path,
        )
        db.add(research_result)
        
        # Step 5: Update query status
        query_record.status = "completed"
        await db.commit()
        await db.refresh(research_result)
        
        logger.info(f"Sync research completed: query_id={query_record.id}")
        
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
        logger.error(f"Sync research failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

