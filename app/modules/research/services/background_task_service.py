"""
Background Task Service - Handles background task execution for research.
Manages its own database session lifecycle for background operations.
"""
import asyncio

from app.core.logging.logger import logger
from app.modules.research.models.research_model import TopicCategory
from app.modules.research.repositories.research_repository import (
    ResearchQueryRepository,
    ResearchResultRepository,
)
from app.modules.research.services.agentic_researcher import AgenticResearcher
from app.modules.research.services.topic_agent import TopicAgent
from database.database import SessionLocal


# Category mapping for topic categorization
CATEGORY_MAP = {
    "core_ai": TopicCategory.CORE_AI,
    "practical_implementation": TopicCategory.PRACTICAL_IMPLEMENTATION,
    "software_development": TopicCategory.SOFTWARE_DEVELOPMENT,
    "web_development": TopicCategory.WEB_DEVELOPMENT,
    "devops": TopicCategory.DEVOPS,
    "general_tech": TopicCategory.GENERAL_TECH,
}


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
        db = SessionLocal()
        query_repository = ResearchQueryRepository(db)
        result_repository = ResearchResultRepository(db)

        try:
            await BackgroundTaskService._process_research(
                query_id=query_id,
                query_text=query_text,
                target_audience=target_audience,
                query_repository=query_repository,
                result_repository=result_repository,
            )
        except Exception as e:
            logger.error(
                f"Background research failed for query {query_id}: {e}",
                exc_info=True,
            )
            await BackgroundTaskService._mark_query_failed(
                query_id=query_id,
                query_repository=query_repository,
            )
        finally:
            db.close()

    @staticmethod
    async def _process_research(
        query_id: int,
        query_text: str,
        target_audience: str,
        query_repository: ResearchQueryRepository,
        result_repository: ResearchResultRepository,
    ) -> None:
        """
        Process the research workflow steps.
        
        Args:
            query_id: The research query ID
            query_text: The query text to research
            target_audience: Target audience for the research
            query_repository: Repository for query operations
            result_repository: Repository for result operations
        """
        # Step 1: Get and validate query record
        query_record = query_repository.get_by_id(query_id)
        if not query_record:
            logger.error(f"Query record not found: {query_id}")
            return

        # Step 2: Update status to processing
        query_record.status = "processing"
        query_repository.commit()

        # Step 3: Categorize the query
        topic_agent = TopicAgent()
        categorization = await topic_agent.categorize_query(query_text)
        topic_category = CATEGORY_MAP.get(
            categorization.category, TopicCategory.GENERAL_TECH
        )

        # Step 4: Update query with category
        query_record.topic_category = topic_category.value
        query_repository.commit()
        logger.info(f"Query {query_id} categorized as: {topic_category.value}")

        # Step 5: Run agentic research
        researcher = AgenticResearcher(max_iterations=5)
        research_output = await researcher.research(
            query=query_text,
            category=topic_category,
            target_audience=target_audience,
        )

        # Step 6: Persist research result
        from app.modules.research.models.research_model import ResearchResult

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
        query_record.status = "completed"
        query_repository.commit()

        logger.info(f"Background research completed: query_id={query_id}")

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
        try:
            query_record = query_repository.get_by_id(query_id)
            if query_record:
                query_record.status = "failed"
                query_repository.commit()
        except Exception as e:
            logger.error(f"Failed to mark query {query_id} as failed: {e}")
