"""
Repository classes for Content database operations.
Provides abstraction layer between service and database.
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.research.models.research_model import ContentItem, ResearchResult, ResearchQuery


class ContentItemRepository:
    """Repository for ContentItem database operations"""

    def __init__(self, db: Session):
        self.db = db
        logger.debug("ContentItemRepository initialized")

    def create(self, content_item: ContentItem) -> ContentItem:
        """Create a new content item record"""
        self.db.add(content_item)
        self.db.commit()
        self.db.refresh(content_item)
        logger.info(f"Created ContentItem with id: {content_item.id}")
        return content_item

    def add_without_commit(self, content_item: ContentItem) -> None:
        """Add a content item without committing (for transaction management)"""
        self.db.add(content_item)
        logger.debug(f"Added ContentItem (not committed)")

    def get_by_id(self, content_id: int) -> Optional[ContentItem]:
        """Get content item by ID"""
        content_item = self.db.get(ContentItem, content_id)
        if content_item:
            logger.debug(f"Found ContentItem with id: {content_id}")
        else:
            logger.debug(f"ContentItem not found with id: {content_id}")
        return content_item

    def get_by_research_query_id(self, research_query_id: int) -> Optional[ContentItem]:
        """Get content item by research query ID"""
        content_item = self.db.scalar(
            select(ContentItem).where(ContentItem.research_query_id == research_query_id)
        )
        if content_item:
            logger.debug(f"Found ContentItem for research_query_id: {research_query_id}")
        else:
            logger.debug(f"ContentItem not found for research_query_id: {research_query_id}")
        return content_item

    def update(self, content_item: ContentItem) -> ContentItem:
        """Update an existing content item record"""
        self.db.commit()
        self.db.refresh(content_item)
        logger.info(f"Updated ContentItem with id: {content_item.id}")
        return content_item

    def update_status(self, content_id: int, status: str) -> Optional[ContentItem]:
        """Update the status of a content item"""
        content_item = self.get_by_id(content_id)
        if content_item:
            old_status = content_item.status
            content_item.status = status
            self.db.commit()
            self.db.refresh(content_item)
            logger.info(f"Updated ContentItem {content_id} status: {old_status} -> {status}")
        else:
            logger.warning(f"Cannot update status: ContentItem {content_id} not found")
        return content_item

    def list_content(
        self,
        skip: int = 0,
        limit: int = 20,
        content_type: Optional[str] = None,
    ) -> List[ContentItem]:
        """List content items with pagination and optional type filter"""
        stmt = select(ContentItem).offset(skip).limit(limit)

        if content_type:
            stmt = stmt.where(ContentItem.content_type == content_type)

        stmt = stmt.order_by(ContentItem.created_at.desc())

        result = self.db.execute(stmt)
        items = list(result.scalars().all())
        logger.debug(
            f"Listed {len(items)} ContentItems (skip={skip}, limit={limit}, type={content_type})"
        )
        return items

    def delete(self, content_id: int) -> bool:
        """Delete a content item by ID"""
        content_item = self.get_by_id(content_id)
        if content_item:
            self.db.delete(content_item)
            self.db.commit()
            logger.info(f"Deleted ContentItem with id: {content_id}")
            return True
        logger.warning(f"Cannot delete: ContentItem {content_id} not found")
        return False

    def flush(self) -> None:
        """Flush pending changes without committing"""
        self.db.flush()
        logger.debug("Flushed pending changes")

    def commit(self) -> None:
        """Commit the current transaction"""
        self.db.commit()
        logger.debug("Committed transaction")

    def refresh(self, content_item: ContentItem) -> ContentItem:
        """Refresh a content item from the database"""
        self.db.refresh(content_item)
        logger.debug(f"Refreshed ContentItem with id: {content_item.id}")
        return content_item

    def rollback(self) -> None:
        """Rollback the current transaction"""
        self.db.rollback()
        logger.warning("Rolled back transaction")


class ResearchDataRepository:
    """Repository for accessing research data (read-only for content module)"""

    def __init__(self, db: Session):
        self.db = db
        logger.debug("ResearchDataRepository initialized")

    def get_research_query(self, query_id: int) -> Optional[ResearchQuery]:
        """Get research query by ID"""
        return self.db.get(ResearchQuery, query_id)

    def get_research_result(self, query_id: int) -> Optional[ResearchResult]:
        """Get research result by query ID"""
        return self.db.scalar(
            select(ResearchResult).where(ResearchResult.query_id == query_id)
        )
