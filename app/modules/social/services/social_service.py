"""
Social Service - Business logic layer for social content operations.
Handles basic operations and delegates workflow to SocialWorkflowService.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.social.schemas.social_schemas import (
    LinkedInGenerateRequest,
    LinkedInResponse,
)
from app.modules.social.services.social_workflow_service import SocialWorkflowService
from app.modules.social.services.nodes.linkedin_agent_node import LinkedInOutput


class SocialService:
    """
    Service class for social content operations.
    Delegates workflow operations to SocialWorkflowService.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.workflow_service = SocialWorkflowService(db)
        logger.debug("SocialService initialized")

    # ==================== LinkedIn Operations ====================

    async def generate_linkedin_post(
        self,
        request: LinkedInGenerateRequest,
    ) -> LinkedInOutput:
        """
        Generate LinkedIn post from content.
        
        Args:
            request: LinkedIn generation request
            
        Returns:
            LinkedInOutput with generated post
        """
        logger.info(f"[SERVICE] Starting LinkedIn post generation: '{request.topic[:50]}...'")
        
        output = await self.workflow_service.generate_linkedin_post(
            topic=request.topic,
            content=request.content,
            target_audience=request.target_audience,
            user_instructions=request.user_instructions,
        )
        
        logger.info(f"[SERVICE] LinkedIn post generation completed: {output.character_count} chars")
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
        logger.info(f"[SERVICE] Generating LinkedIn from blog: '{blog_title[:50]}...'")
        
        output = await self.workflow_service.generate_linkedin_from_blog(
            blog_title=blog_title,
            blog_content=blog_content,
            target_audience=target_audience,
            user_instructions=user_instructions,
        )
        
        logger.info(f"[SERVICE] LinkedIn from blog completed: {output.character_count} chars")
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
            user_instructions: Custom instructions from user
            
        Returns:
            LinkedInOutput with generated post
        """
        logger.info(f"[SERVICE] Generating LinkedIn from research: query_id={research_query_id}")
        
        output = await self.workflow_service.generate_linkedin_from_research(
            research_query_id=research_query_id,
            target_audience=target_audience,
            user_instructions=user_instructions,
        )
        
        logger.info(f"[SERVICE] LinkedIn from research completed: {output.character_count} chars")
        return output

    # ==================== Response Mappers ====================

    @staticmethod
    def to_linkedin_response(output: LinkedInOutput) -> LinkedInResponse:
        """Convert LinkedInOutput to LinkedInResponse schema"""
        return LinkedInResponse(
            hook=output.hook,
            content=output.content,
            hashtags=output.hashtags,
            call_to_action=output.call_to_action,
            character_count=output.character_count,
            file_path=output.file_path,
        )
