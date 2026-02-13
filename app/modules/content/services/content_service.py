"""
Content Service - Business logic layer for content CRUD operations.
Handles basic CRUD operations and delegates workflow to ContentWorkflowService.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.content.repositories.content_repository import ContentItemRepository
from app.modules.content.schemas.content_schemas import (
    BlogFromResearchRequest,
    BlogResponse,
    BlogStatusResponse,
)
from app.modules.content.services.content_workflow_service import ContentWorkflowService
from app.modules.research.models.research_model import ContentItem


class ContentService:
    """
    Service class for content CRUD operations.
    Delegates workflow operations to ContentWorkflowService.
    """

    def __init__(self, db: Session):
        self.db = db
        self.content_repository = ContentItemRepository(db)
        self.workflow_service = ContentWorkflowService(db)
        logger.debug("ContentService initialized")

    # ==================== CRUD Operations ====================

    def get_content(self, content_id: int) -> Optional[ContentItem]:
        """
        Get a content item by ID.
        
        Args:
            content_id: The ID of the content to retrieve
            
        Returns:
            The ContentItem if found, None otherwise
        """
        logger.debug(f"[SERVICE] Getting content: {content_id}")
        content = self.content_repository.get_by_id(content_id)
        if content:
            logger.debug(f"[SERVICE] Found content: {content_id}")
        else:
            logger.debug(f"[SERVICE] Content not found: {content_id}")
        return content

    def list_content(
        self,
        skip: int = 0,
        limit: int = 20,
        content_type: Optional[str] = None,
    ) -> List[ContentItem]:
        """
        List content items with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            content_type: Optional content type filter
            
        Returns:
            List of ContentItem records
        """
        logger.debug(
            f"[SERVICE] Listing content: skip={skip}, limit={limit}, type={content_type}"
        )
        items = self.content_repository.list_content(
            skip=skip, limit=limit, content_type=content_type
        )
        logger.debug(f"[SERVICE] Found {len(items)} content items")
        return items

    def delete_content(self, content_id: int) -> bool:
        """
        Delete a content item by ID.
        
        Args:
            content_id: The ID of the content to delete
            
        Returns:
            True if deleted, False if not found
        """
        logger.info(f"[SERVICE] Deleting content: {content_id}")
        deleted = self.content_repository.delete(content_id)
        if deleted:
            logger.info(f"[SERVICE] Deleted content: {content_id}")
        else:
            logger.warning(f"[SERVICE] Failed to delete: content {content_id} not found")
        return deleted

    def create_placeholder_content(
        self,
        research_query_id: int,
        query_text: str,
        target_audience: str,
        tone: str,
    ) -> ContentItem:
        """
        Create a placeholder content item for async generation.
        
        Args:
            research_query_id: The research query ID
            query_text: The query text for title
            target_audience: Target audience
            tone: Writing tone
            
        Returns:
            The created placeholder ContentItem
        """
        logger.info(f"[SERVICE] Creating placeholder content for query: {research_query_id}")
        
        content_item = ContentItem(
            research_query_id=research_query_id,
            content_type='blog',
            title=f'Generating: {query_text[:50]}...',
            content='',
            target_audience=target_audience,
            tone=tone,
            status='generating',
        )
        
        created = self.content_repository.create(content_item)
        logger.info(f"[SERVICE] Created placeholder content with id: {created.id}")
        return created

    # ==================== Workflow Operations ====================

    def verify_research_exists(self, research_query_id: int):
        """
        Verify that research query and result exist.
        Delegates to workflow service.
        
        Args:
            research_query_id: The research query ID to verify
            
        Returns:
            Tuple of (ResearchQuery, error_message) - error_message is None if valid
        """
        return self.workflow_service.verify_research_exists(research_query_id)

    async def generate_blog_sync(
        self,
        request: BlogFromResearchRequest,
    ) -> ContentItem:
        """
        Generate blog synchronously from existing research.
        Delegates to workflow service.
        
        Args:
            request: Blog generation request with research_query_id
            
        Returns:
            The created ContentItem with blog content
        """
        logger.info(f"[SERVICE] Starting sync blog generation for query: {request.research_query_id}")
        
        target_audience = request.target_audience or 'practitioner'
        tone = request.tone or 'professional'
        
        content_item = await self.workflow_service.generate_blog_from_research(
            research_query_id=request.research_query_id,
            target_audience=target_audience,
            tone=tone,
        )
        
        logger.info(f"[SERVICE] Sync blog generation completed: content_id={content_item.id}")
        return content_item

    # ==================== Response Mappers ====================

    @staticmethod
    def to_blog_response(content: ContentItem) -> BlogResponse:
        """Convert ContentItem model to BlogResponse schema"""
        return BlogResponse(
            title=content.title or '',
            content=content.content or '',
            meta_description=content.meta_description or '',
            tags=content.tags or [],
            estimated_reading_time='5 min read',
            file_path=content.file_path,
        )

    @staticmethod
    def to_status_response(content: ContentItem) -> BlogStatusResponse:
        """Convert ContentItem model to BlogStatusResponse schema"""
        return BlogStatusResponse(
            id=content.id,
            content_type=content.content_type,
            title=content.title,
            status=content.status,
            file_path=content.file_path,
            created_at=content.created_at,
        )
