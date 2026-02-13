"""
Repository classes for Research database operations.
Provides abstraction layer between service and database.
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.research.models.research_model import ResearchQuery, ResearchResult


class ResearchQueryRepository:
    """Repository for ResearchQuery database operations"""

    def __init__(self, db: Session):
        self.db = db
        logger.debug("ResearchQueryRepository initialized")

    def create(self, query_record: ResearchQuery) -> ResearchQuery:
        """Create a new research query record"""
        self.db.add(query_record)
        self.db.commit()
        self.db.refresh(query_record)
        logger.info(f"Created ResearchQuery with id: {query_record.id}")
        return query_record

    def get_by_id(self, query_id: int) -> Optional[ResearchQuery]:
        """Get research query by ID"""
        query_record = self.db.get(ResearchQuery, query_id)
        if query_record:
            logger.debug(f"Found ResearchQuery with id: {query_id}")
        else:
            logger.debug(f"ResearchQuery not found with id: {query_id}")
        return query_record

    def update(self, query_record: ResearchQuery) -> ResearchQuery:
        """Update an existing research query record"""
        self.db.commit()
        self.db.refresh(query_record)
        logger.info(f"Updated ResearchQuery with id: {query_record.id}")
        return query_record

    def update_status(self, query_id: int, status: str) -> Optional[ResearchQuery]:
        """Update the status of a research query"""
        query_record = self.get_by_id(query_id)
        if query_record:
            old_status = query_record.status
            query_record.status = status
            self.db.commit()
            self.db.refresh(query_record)
            logger.info(
                f"Updated ResearchQuery {query_id} status: {old_status} -> {status}"
            )
        else:
            logger.warning(f"Cannot update status: ResearchQuery {query_id} not found")
        return query_record

    def update_category(self, query_id: int, category: str) -> Optional[ResearchQuery]:
        """Update the topic category of a research query"""
        query_record = self.get_by_id(query_id)
        if query_record:
            query_record.topic_category = category
            self.db.commit()
            self.db.refresh(query_record)
            logger.info(f"Updated ResearchQuery {query_id} category: {category}")
        else:
            logger.warning(
                f"Cannot update category: ResearchQuery {query_id} not found"
            )
        return query_record

    def list_queries(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[ResearchQuery]:
        """List research queries with pagination and optional status filter"""
        stmt = select(ResearchQuery).offset(skip).limit(limit)

        if status:
            stmt = stmt.where(ResearchQuery.status == status)

        stmt = stmt.order_by(ResearchQuery.created_at.desc())

        result = self.db.execute(stmt)
        queries = list(result.scalars().all())
        logger.debug(
            f"Listed {len(queries)} ResearchQueries (skip={skip}, limit={limit}, status={status})"
        )
        return queries

    def delete(self, query_id: int) -> bool:
        """Delete a research query by ID"""
        query_record = self.get_by_id(query_id)
        if query_record:
            self.db.delete(query_record)
            self.db.commit()
            logger.info(f"Deleted ResearchQuery with id: {query_id}")
            return True
        logger.warning(f"Cannot delete: ResearchQuery {query_id} not found")
        return False

    def flush(self) -> None:
        """Flush pending changes without committing"""
        self.db.flush()
        logger.debug("Flushed pending changes")

    def commit(self) -> None:
        """Commit the current transaction"""
        self.db.commit()
        logger.debug("Committed transaction")

    def rollback(self) -> None:
        """Rollback the current transaction"""
        self.db.rollback()
        logger.warning("Rolled back transaction")


class ResearchResultRepository:
    """Repository for ResearchResult database operations"""

    def __init__(self, db: Session):
        self.db = db
        logger.debug("ResearchResultRepository initialized")

    def create(self, result_record: ResearchResult) -> ResearchResult:
        """Create a new research result record"""
        self.db.add(result_record)
        self.db.commit()
        self.db.refresh(result_record)
        logger.info(
            f"Created ResearchResult with id: {result_record.id} for query: {result_record.query_id}"
        )
        return result_record

    def get_by_id(self, result_id: int) -> Optional[ResearchResult]:
        """Get research result by ID"""
        result_record = self.db.get(ResearchResult, result_id)
        if result_record:
            logger.debug(f"Found ResearchResult with id: {result_id}")
        else:
            logger.debug(f"ResearchResult not found with id: {result_id}")
        return result_record

    def get_by_query_id(self, query_id: int) -> Optional[ResearchResult]:
        """Get research result by query ID"""
        result_record = self.db.scalar(
            select(ResearchResult).where(ResearchResult.query_id == query_id)
        )
        if result_record:
            logger.debug(f"Found ResearchResult for query_id: {query_id}")
        else:
            logger.debug(f"ResearchResult not found for query_id: {query_id}")
        return result_record

    def update(self, result_record: ResearchResult) -> ResearchResult:
        """Update an existing research result record"""
        self.db.commit()
        self.db.refresh(result_record)
        logger.info(f"Updated ResearchResult with id: {result_record.id}")
        return result_record

    def delete(self, result_id: int) -> bool:
        """Delete a research result by ID"""
        result_record = self.get_by_id(result_id)
        if result_record:
            self.db.delete(result_record)
            self.db.commit()
            logger.info(f"Deleted ResearchResult with id: {result_id}")
            return True
        logger.warning(f"Cannot delete: ResearchResult {result_id} not found")
        return False

    def add_without_commit(self, result_record: ResearchResult) -> None:
        """Add a result record without committing (for transaction management)"""
        self.db.add(result_record)
        logger.debug(
            f"Added ResearchResult for query_id: {result_record.query_id} (not committed)"
        )

    def commit(self) -> None:
        """Commit the current transaction"""
        self.db.commit()
        logger.debug("Committed transaction")

    def refresh(self, result_record: ResearchResult) -> ResearchResult:
        """Refresh a result record from the database"""
        self.db.refresh(result_record)
        logger.debug(f"Refreshed ResearchResult with id: {result_record.id}")
        return result_record
