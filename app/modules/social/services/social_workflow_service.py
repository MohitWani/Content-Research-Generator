"""
Social Workflow Service - Handles LinkedIn post generation workflow logic.
Orchestrates the LinkedIn post generation process from content.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.research.models.research_model import ResearchQuery, ResearchResult
from app.modules.social.services.linkedin_agent import LinkedInAgent, LinkedInOutput, get_linkedin_agent


class SocialWorkflowService:
    """
    Service class for social content generation workflows.
    Handles LinkedIn post generation from content.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.linkedin_agent = get_linkedin_agent()
        logger.debug("SocialWorkflowService initialized")

    async def generate_linkedin_post(
        self,
        topic: str,
        content: str,
        target_audience: str = 'practitioner',
        user_instructions: str = '',
    ) -> LinkedInOutput:
        """
        Generate LinkedIn post from content.
        
        Args:
            topic: Post topic
            content: Source content to transform
            target_audience: Target audience
            user_instructions: Custom instructions from user
            
        Returns:
            LinkedInOutput with generated post
        """
        logger.info(f"[WORKFLOW] Starting LinkedIn post generation for: '{topic[:50]}...'")
        
        output = await self.linkedin_agent.generate_post(
            topic=topic,
            content=content,
            target_audience=target_audience,
            user_instructions=user_instructions,
        )
        
        logger.info(f"[WORKFLOW] LinkedIn post generation completed: {output.character_count} chars")
        return output

    async def generate_linkedin_from_blog(
        self,
        blog_title: str,
        blog_content: str,
        target_audience: str = 'practitioner',
        user_instructions: str = '',
    ) -> LinkedInOutput:
        """
        Generate LinkedIn post from a blog post.
        
        Args:
            blog_title: Blog title
            blog_content: Blog content
            target_audience: Target audience
            user_instructions: Custom instructions from user
            
        Returns:
            LinkedInOutput with generated post
        """
        logger.info(f"[WORKFLOW] Generating LinkedIn from blog: '{blog_title[:50]}...'")
        
        output = await self.linkedin_agent.generate_from_blog(
            blog_title=blog_title,
            blog_content=blog_content,
            target_audience=target_audience,
            user_instructions=user_instructions,
        )
        
        logger.info(f"[WORKFLOW] LinkedIn from blog completed: {output.character_count} chars")
        return output

    async def generate_linkedin_from_research(
        self,
        research_query_id: int,
        target_audience: str = 'practitioner',
        user_instructions: str = '',
    ) -> LinkedInOutput:
        """
        Generate LinkedIn post from research data.
        
        Args:
            research_query_id: Research query ID
            target_audience: Target audience
            
        Returns:
            LinkedInOutput with generated post
            
        Raises:
            ValueError: If research data not found
        """
        if not self.db:
            raise ValueError("Database session required for research lookup")

        logger.info(f"[WORKFLOW] Generating LinkedIn from research: query_id={research_query_id}")

        # Get research query
        query = self.db.get(ResearchQuery, research_query_id)
        if not query:
            raise ValueError(f"Research query not found: {research_query_id}")

        # Get research result
        result = self.db.scalar(
            select(ResearchResult).where(ResearchResult.query_id == research_query_id)
        )
        if not result:
            raise ValueError(f"Research result not found for query: {research_query_id}")

        # Format research content for LinkedIn
        content = self._format_research_for_linkedin(result)

        output = await self.linkedin_agent.generate_post(
            topic=query.query_text,
            content=content,
            target_audience=target_audience,
            user_instructions=user_instructions,
        )

        logger.info(f"[WORKFLOW] LinkedIn from research completed: {output.character_count} chars")
        return output

    def _format_research_for_linkedin(self, result: ResearchResult) -> str:
        """Format research result for LinkedIn post generation"""
        parts = []

        if result.topic_summary:
            parts.append(f"Summary:\n{result.topic_summary}")

        if result.key_concepts:
            concepts = ', '.join(result.key_concepts.keys())
            parts.append(f"Key Concepts: {concepts}")

        if result.implementation_examples:
            parts.append(f"Implementation:\n{result.implementation_examples[:500]}")

        return '\n\n'.join(parts) if parts else 'Research data available'
