"""
Repository classes for Research database operations.
Provides abstraction layer between service and database.
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.research.models.research_model import ResearchQuery, ResearchResult


class ResearchQueryRepository:
    """Repository for ResearchQuery database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, query_record: ResearchQuery) -> ResearchQuery:
        """Create a new research query record"""
        self.db.add(query_record)
        self.db.commit()
        self.db.refresh(query_record)
        return query_record

    def get_by_id(self, query_id: int) -> Optional[ResearchQuery]:
        """Get research query by ID"""
        return self.db.get(ResearchQuery, query_id)

    def update(self, query_record: ResearchQuery) -> ResearchQuery:
        """Update an existing research query record"""
        self.db.commit()
        self.db.refresh(query_record)
        return query_record

    def update_status(self, query_id: int, status: str) -> Optional[ResearchQuery]:
        """Update the status of a research query"""
        query_record = self.get_by_id(query_id)
        if query_record:
            query_record.status = status
            self.db.commit()
            self.db.refresh(query_record)
        return query_record

    def update_category(self, query_id: int, category: str) -> Optional[ResearchQuery]:
        """Update the topic category of a research query"""
        query_record = self.get_by_id(query_id)
        if query_record:
            query_record.topic_category = category
            self.db.commit()
            self.db.refresh(query_record)
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
        return list(result.scalars().all())

    def delete(self, query_id: int) -> bool:
        """Delete a research query by ID"""
        query_record = self.get_by_id(query_id)
        if query_record:
            self.db.delete(query_record)
            self.db.commit()
            return True
        return False

    def flush(self) -> None:
        """Flush pending changes without committing"""
        self.db.flush()

    def commit(self) -> None:
        """Commit the current transaction"""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback the current transaction"""
        self.db.rollback()


class ResearchResultRepository:
    """Repository for ResearchResult database operations"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, result_record: ResearchResult) -> ResearchResult:
        """Create a new research result record"""
        self.db.add(result_record)
        self.db.commit()
        self.db.refresh(result_record)
        return result_record

    def get_by_id(self, result_id: int) -> Optional[ResearchResult]:
        """Get research result by ID"""
        return self.db.get(ResearchResult, result_id)

    def get_by_query_id(self, query_id: int) -> Optional[ResearchResult]:
        """Get research result by query ID"""
        return self.db.scalar(
            select(ResearchResult).where(ResearchResult.query_id == query_id)
        )

    def update(self, result_record: ResearchResult) -> ResearchResult:
        """Update an existing research result record"""
        self.db.commit()
        self.db.refresh(result_record)
        return result_record

    def delete(self, result_id: int) -> bool:
        """Delete a research result by ID"""
        result_record = self.get_by_id(result_id)
        if result_record:
            self.db.delete(result_record)
            self.db.commit()
            return True
        return False

    def add_without_commit(self, result_record: ResearchResult) -> None:
        """Add a result record without committing (for transaction management)"""
        self.db.add(result_record)

    def commit(self) -> None:
        """Commit the current transaction"""
        self.db.commit()

    def refresh(self, result_record: ResearchResult) -> ResearchResult:
        """Refresh a result record from the database"""
        self.db.refresh(result_record)
        return result_record
