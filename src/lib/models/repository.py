"""
Repository layer for database interactions
Uses SQLAlchemy 2.0 async session
Maps to: plan.md → Section 5 (Library-First), T017
"""
from __future__ import annotations

from typing import List, Optional, Sequence

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.lib.models.research import (
    ResearchQuery,
    ResearchResult,
    ContentItem,
    PipelineExecution,
    TopicCategory,
)


class ResearchRepository:
    """
    Repository for research queries, results, and content
    Provides CRUD operations with async SQLAlchemy session
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # -----------------------
    # Research Queries
    # -----------------------

    async def create_research_query(self, data: dict) -> ResearchQuery:
        """Create a new research query"""
        query = ResearchQuery(**data)
        self.session.add(query)
        await self.session.flush()
        await self.session.refresh(query)
        return query

    async def get_research_query(self, query_id: int) -> Optional[ResearchQuery]:
        """Get research query by ID"""
        result = await self.session.execute(
            select(ResearchQuery)
            .options(
                selectinload(ResearchQuery.research_results),
                selectinload(ResearchQuery.content_items),
            )
            .where(ResearchQuery.id == query_id)
        )
        return result.scalar_one_or_none()

    async def list_research_queries(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[ResearchQuery]:
        """List research queries with optional status filter"""
        stmt = select(ResearchQuery).order_by(ResearchQuery.created_at.desc())
        if status:
            stmt = stmt.where(ResearchQuery.status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_research_query(
        self,
        query_id: int,
        **updates,
    ) -> Optional[ResearchQuery]:
        """Update research query fields"""
        await self.session.execute(
            update(ResearchQuery)
            .where(ResearchQuery.id == query_id)
            .values(**updates)
        )
        await self.session.flush()
        return await self.get_research_query(query_id)

    async def count_research_queries(self, status: Optional[str] = None) -> int:
        """Count research queries"""
        stmt = select(func.count(ResearchQuery.id))
        if status:
            stmt = stmt.where(ResearchQuery.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # -----------------------
    # Research Results
    # -----------------------

    async def create_research_result(self, data: dict) -> ResearchResult:
        """Create research result for a query"""
        result = ResearchResult(**data)
        self.session.add(result)
        await self.session.flush()
        await self.session.refresh(result)
        return result

    async def get_research_result(self, query_id: int) -> Optional[ResearchResult]:
        """Get latest research result for query"""
        stmt = (
            select(ResearchResult)
            .where(ResearchResult.query_id == query_id)
            .order_by(ResearchResult.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # -----------------------
    # Content Items
    # -----------------------

    async def create_content_item(self, data: dict) -> ContentItem:
        """Create generated content item"""
        content = ContentItem(**data)
        self.session.add(content)
        await self.session.flush()
        await self.session.refresh(content)
        return content

    async def get_content_item(self, content_id: int) -> Optional[ContentItem]:
        """Get content item by ID"""
        result = await self.session.execute(
            select(ContentItem).where(ContentItem.id == content_id)
        )
        return result.scalar_one_or_none()

    async def list_content_items(
        self,
        content_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[ContentItem]:
        """List content items with optional filtering"""
        stmt = select(ContentItem).order_by(ContentItem.created_at.desc())
        if content_type:
            stmt = stmt.where(ContentItem.content_type == content_type)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # -----------------------
    # Pipeline Executions
    # -----------------------

    async def create_pipeline_execution(self, data: dict) -> PipelineExecution:
        """Create pipeline execution record"""
        execution = PipelineExecution(**data)
        self.session.add(execution)
        await self.session.flush()
        await self.session.refresh(execution)
        return execution

    async def update_pipeline_execution(
        self,
        execution_id: int,
        **updates,
    ) -> Optional[PipelineExecution]:
        """Update pipeline execution fields"""
        await self.session.execute(
            update(PipelineExecution)
            .where(PipelineExecution.id == execution_id)
            .values(**updates)
        )
        await self.session.flush()
        result = await self.session.execute(
            select(PipelineExecution).where(PipelineExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

    async def get_pipeline_execution(self, execution_id: int) -> Optional[PipelineExecution]:
        """Get pipeline execution by ID"""
        result = await self.session.execute(
            select(PipelineExecution).where(PipelineExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

