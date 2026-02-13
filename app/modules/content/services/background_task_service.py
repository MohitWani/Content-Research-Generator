"""
Background Task Service for Content Module.
Handles background task execution with its own database session.
"""
import asyncio
from typing import Optional

from app.core.logging.logger import logger
from app.modules.content.services.content_workflow_service import ContentWorkflowService
from app.modules.research.models.research_model import ContentItem
from database.database import SessionLocal


class ContentBackgroundTaskService:
    """
    Service for handling background content generation tasks.
    Creates its own database session for background execution.
    """

    @staticmethod
    def run_blog_generation_task(
        research_query_id: int,
        target_audience: str,
        tone: str,
    ) -> None:
        """
        Background task entry point for blog generation.
        
        Args:
            research_query_id: The research query ID to generate blog from
            target_audience: Target audience for the blog
            tone: Writing tone for the blog
        """
        logger.info(f"[BACKGROUND] Starting blog generation task for query: {research_query_id}")
        asyncio.run(
            ContentBackgroundTaskService._execute_blog_generation(
                research_query_id=research_query_id,
                target_audience=target_audience,
                tone=tone,
            )
        )

    @staticmethod
    async def _execute_blog_generation(
        research_query_id: int,
        target_audience: str,
        tone: str,
    ) -> Optional[ContentItem]:
        """
        Execute blog generation from research data.
        
        Args:
            research_query_id: The research query ID
            target_audience: Target audience
            tone: Writing tone
            
        Returns:
            The created ContentItem or None if failed
        """
        db = SessionLocal()
        try:
            workflow_service = ContentWorkflowService(db)

            content_item = await workflow_service.generate_blog_from_research(
                research_query_id=research_query_id,
                target_audience=target_audience,
                tone=tone,
            )

            logger.info(f"[BACKGROUND] Blog generation completed: content_id={content_item.id}")
            return content_item

        except ValueError as e:
            logger.error(f"[BACKGROUND] Research data not found: {e}")
            return None
        except Exception as e:
            logger.error(f"[BACKGROUND] Blog generation failed: {e}", exc_info=True)
            return None
        finally:
            db.close()
