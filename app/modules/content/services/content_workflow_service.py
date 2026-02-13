"""
Content Workflow Service - Handles blog generation workflow logic.
Orchestrates the blog generation process from research data.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.content.repositories.content_repository import (
    ContentItemRepository,
    ResearchDataRepository,
)
from app.modules.content.services.blog_writer_agent import BlogOutput, get_blog_writer_agent
from app.modules.research.models.research_model import ContentItem
from app.modules.research.services.agentic_researcher import ResearchOutput


class ContentWorkflowService:
    """
    Service class for content generation workflows.
    Handles blog generation from research data.
    """

    def __init__(self, db: Session):
        self.db = db
        self.content_repository = ContentItemRepository(db)
        self.research_repository = ResearchDataRepository(db)
        logger.debug("ContentWorkflowService initialized")

    async def generate_blog_from_research(
        self,
        research_query_id: int,
        target_audience: str = 'practitioner',
        tone: str = 'professional',
    ) -> ContentItem:
        """
        Generate blog from existing research data.
        
        Args:
            research_query_id: The research query ID to generate blog from
            target_audience: Target audience for the blog
            tone: Writing tone for the blog
            
        Returns:
            The created ContentItem with blog content
            
        Raises:
            ValueError: If research data not found
        """
        logger.info(f"[WORKFLOW] Starting blog generation for query: {research_query_id}")
        
        # Get research data
        result = self.research_repository.get_research_result(research_query_id)
        query = self.research_repository.get_research_query(research_query_id)
        
        if not result or not query:
            raise ValueError(f"Research not found for query_id: {research_query_id}")
        
        # Convert to ResearchOutput
        research = self._convert_to_research_output(result)
        
        # Generate blog
        blog_writer = get_blog_writer_agent()
        blog = await blog_writer.generate_blog(
            topic=query.query_text,
            research_data=research,
            target_audience=target_audience,
            tone=tone,
        )
        
        # Save content item
        content_item = self._create_content_from_blog(
            research_query_id=research_query_id,
            blog=blog,
            target_audience=target_audience,
            tone=tone,
        )
        
        created = self.content_repository.create(content_item)
        logger.info(f"[WORKFLOW] Blog generation completed: content_id={created.id}")
        
        return created

    def verify_research_exists(self, research_query_id: int) -> tuple[Optional[object], Optional[str]]:
        """
        Verify that research query and result exist.
        
        Args:
            research_query_id: The research query ID to verify
            
        Returns:
            Tuple of (ResearchQuery, error_message) - error_message is None if valid
        """
        result = self.research_repository.get_research_result(research_query_id)
        if not result:
            return None, 'Research result not found'

        query = self.research_repository.get_research_query(research_query_id)
        if not query:
            return None, 'Research query not found'

        return query, None

    # ==================== Helper Methods ====================

    def _convert_to_research_output(self, result) -> ResearchOutput:
        """Convert ResearchResult to ResearchOutput"""
        return ResearchOutput(
            topic_summary=result.topic_summary or '',
            key_concepts=result.key_concepts or {},
            mathematical_foundations=result.mathematical_foundations,
            source_descriptions=result.historical_context,
            implementation_examples=result.implementation_examples,
            sources=result.sources or [],
            completeness_score=result.completeness_score or 0.0,
        )

    def _create_content_from_blog(
        self,
        research_query_id: int,
        blog: BlogOutput,
        target_audience: str,
        tone: str,
    ) -> ContentItem:
        """Create ContentItem from BlogOutput"""
        return ContentItem(
            research_query_id=research_query_id,
            content_type='blog',
            title=blog.title,
            content=blog.content,
            file_path=blog.file_path,
            target_audience=target_audience,
            tone=tone,
            meta_description=blog.meta_description,
            tags=blog.tags,
            status='published',
        )
