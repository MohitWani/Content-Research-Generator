"""
Background Task Service - Handles background task execution for research.
Manages its own database session lifecycle for background operations.
"""
import asyncio

from app.core.logging.logger import logger
from app.modules.research.models.research_model import ResearchResult, TopicCategory
from app.modules.research.repositories.research_repository import (
    ResearchQueryRepository,
    ResearchResultRepository,
)
from app.modules.research.services.agentic_researcher import AgenticResearcher
from app.modules.research.services.nodes import TopicAgentNode
from database.database import SessionLocal


class BackgroundTaskService:
    """
    Service for handling background task execution.
    Creates and manages its own database session for background operations.
    """

    @staticmethod
    def run_research_task(
        query_id: int,
        query_text: str,
        target_audience: str,
        content_type: str,
    ) -> None:
        """
        Entry point for background research task.
        Uses asyncio.run() to execute async workflow in sync background task.
        
        Args:
            query_id: The research query ID
            query_text: The query text to research
            target_audience: Target audience for the research
            content_type: Type of content to generate
        """
        logger.info(
            f"[BACKGROUND] Starting research task for query_id: {query_id}"
        )
        asyncio.run(
            BackgroundTaskService._execute_workflow(
                query_id, query_text, target_audience, content_type
            )
        )

    @staticmethod
    async def _execute_workflow(
        query_id: int,
        query_text: str,
        target_audience: str,
        content_type: str,
    ) -> None:
        """
        Execute the research workflow asynchronously.
        
        Args:
            query_id: The research query ID
            query_text: The query text to research
            target_audience: Target audience for the research
            content_type: Type of content to generate
        """
        logger.info(f"[BACKGROUND] Initializing workflow for query_id: {query_id}")
        db = SessionLocal()
        query_repository = ResearchQueryRepository(db)
        result_repository = ResearchResultRepository(db)

        try:
            await BackgroundTaskService._process_research(
                query_id=query_id,
                query_text=query_text,
                target_audience=target_audience,
                content_type=content_type,
                query_repository=query_repository,
                result_repository=result_repository,
            )
        except Exception as e:
            logger.error(
                f"[BACKGROUND] Research failed for query {query_id}: {e}",
                exc_info=True,
            )
            await BackgroundTaskService._mark_query_failed(
                query_id=query_id,
                query_repository=query_repository,
            )
        finally:
            db.close()
            logger.debug(f"[BACKGROUND] Database session closed for query_id: {query_id}")

    @staticmethod
    async def _process_research(
        query_id: int,
        query_text: str,
        target_audience: str,
        content_type: str,
        query_repository: ResearchQueryRepository,
        result_repository: ResearchResultRepository,
    ) -> None:
        """
        Process the research workflow steps.
        
        Args:
            query_id: The research query ID
            query_text: The query text to research
            target_audience: Target audience for the research
            content_type: Type of content (blog or linkedin)
            query_repository: Repository for query operations
            result_repository: Repository for result operations
        """
        # Step 1: Get and validate query record
        logger.info(f"[BACKGROUND] Step 1: Fetching query record for id: {query_id}")
        query_record = query_repository.get_by_id(query_id)
        if not query_record:
            logger.error(f"[BACKGROUND] Query record not found: {query_id}")
            return

        # Step 2: Update status to processing
        logger.info(f"[BACKGROUND] Step 2: Updating status to 'processing' for query_id: {query_id}")
        query_record.status = "processing"
        query_repository.commit()

        # Step 3: Categorize the query using TopicAgentNode
        logger.info(f"[BACKGROUND] Step 3: Categorizing query for query_id: {query_id}")
        topic_agent_node = TopicAgentNode()
        topic_category = await topic_agent_node.categorize(query_text)
        logger.info(f"[BACKGROUND] Query {query_id} categorized as: {topic_category.value}")

        # Step 4: Update query with category
        logger.info(f"[BACKGROUND] Step 4: Updating category for query_id: {query_id}")
        query_record.topic_category = topic_category.value
        query_repository.commit()

        # Step 5: Run agentic research
        logger.info(f"[BACKGROUND] Step 5: Starting agentic research for query_id: {query_id}")
        researcher = AgenticResearcher(max_iterations=5)
        research_output = await researcher.research(
            query=query_text,
            category=topic_category,
            target_audience=target_audience,
            content_type=content_type,
        )
        logger.info(
            f"[BACKGROUND] Research completed for query_id: {query_id}, "
            f"score: {research_output.completeness_score:.2f}"
        )

        # Step 6: Persist research result
        logger.info(f"[BACKGROUND] Step 6: Persisting research result for query_id: {query_id}")
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
        result_repository.add_without_commit(research_result)

        # Step 7: Update query status to completed
        logger.info(f"[BACKGROUND] Step 7: Marking query as completed for query_id: {query_id}")
        query_record.status = "completed"
        query_repository.commit()

        logger.info(f"[BACKGROUND] Research workflow completed successfully for query_id: {query_id}")

    @staticmethod
    async def _mark_query_failed(
        query_id: int,
        query_repository: ResearchQueryRepository,
    ) -> None:
        """
        Mark a query as failed.
        
        Args:
            query_id: The research query ID
            query_repository: Repository for query operations
        """
        logger.warning(f"[BACKGROUND] Marking query as failed: {query_id}")
        try:
            query_record = query_repository.get_by_id(query_id)
            if query_record:
                query_record.status = "failed"
                query_repository.commit()
                logger.info(f"[BACKGROUND] Query {query_id} marked as failed")
            else:
                logger.error(f"[BACKGROUND] Cannot mark as failed: query {query_id} not found")
        except Exception as e:
            logger.error(f"[BACKGROUND] Failed to mark query {query_id} as failed: {e}")
