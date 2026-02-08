"""
Research Service - Business logic layer for research CRUD operations.
Handles basic operations and delegates workflow to ResearchWorkflowService.
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.research.models.research_model import (
    ResearchQuery,
    ResearchResult,
)
from app.modules.research.repositories.research_repository import (
    ResearchQueryRepository,
    ResearchResultRepository,
)
from app.modules.research.schemas.research_schemas import (
    ResearchQueryRequest,
    ResearchQueryResponse,
    ResearchResultResponse,
    ResearchStatusResponse,
)
from app.modules.research.services.research_workflow_service import (
    ResearchWorkflowService,
)


class ResearchService:
    """
    Service class for research CRUD operations.
    Delegates complex workflow operations to ResearchWorkflowService.
    """

    def __init__(self, db: Session):
        self.db = db
        self.query_repository = ResearchQueryRepository(db)
        self.result_repository = ResearchResultRepository(db)
        self.workflow_service = ResearchWorkflowService(db)

    # ==================== CRUD Operations ====================

    def create_research_query(
        self,
        request: ResearchQueryRequest,
    ) -> ResearchQuery:
        """
        Create a new research query record.
        
        Args:
            request: The research query request data
            
        Returns:
            The created ResearchQuery record
        """
        target_audience = (
            request.target_audience.value if request.target_audience else "practitioner"
        )
        content_type = request.content_type.value if request.content_type else "blog"

        query_record = ResearchQuery(
            query_text=request.query,
            target_audience=target_audience,
            content_type=content_type,
            status="pending",
        )

        created_query = self.query_repository.create(query_record)
        logger.info(f"Created research query: {created_query.id}")

        return created_query

    def get_research_query(self, query_id: int) -> Optional[ResearchQuery]:
        """
        Get a research query by ID.
        
        Args:
            query_id: The ID of the query to retrieve
            
        Returns:
            The ResearchQuery if found, None otherwise
        """
        return self.query_repository.get_by_id(query_id)

    def get_research_result(self, query_id: int) -> Optional[ResearchResult]:
        """
        Get research result for a query.
        
        Args:
            query_id: The ID of the query
            
        Returns:
            The ResearchResult if found, None otherwise
        """
        return self.result_repository.get_by_query_id(query_id)

    def list_research_queries(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[ResearchQuery]:
        """
        List research queries with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional status filter
            
        Returns:
            List of ResearchQuery records
        """
        return self.query_repository.list_queries(skip=skip, limit=limit, status=status)

    def update_query_status(self, query_id: int, status: str) -> Optional[ResearchQuery]:
        """
        Update the status of a research query.
        
        Args:
            query_id: The ID of the query
            status: The new status
            
        Returns:
            The updated ResearchQuery if found, None otherwise
        """
        return self.query_repository.update_status(query_id, status)

    def delete_research_query(self, query_id: int) -> bool:
        """
        Delete a research query by ID.
        
        Args:
            query_id: The ID of the query to delete
            
        Returns:
            True if deleted, False if not found
        """
        return self.query_repository.delete(query_id)

    # ==================== Workflow Operations ====================

    async def execute_sync_research(
        self,
        request: ResearchQueryRequest,
    ) -> ResearchResult:
        """
        Execute research synchronously and return the result.
        
        Args:
            request: The research query request data
            
        Returns:
            The created ResearchResult
        """
        target_audience = (
            request.target_audience.value if request.target_audience else "practitioner"
        )
        content_type = request.content_type.value if request.content_type else "blog"

        # Step 1: Categorize the query
        topic_category = await self.workflow_service.categorize_query(request.query)

        # Step 2: Create query record with category
        query_record = ResearchQuery(
            query_text=request.query,
            target_audience=target_audience,
            topic_category=topic_category.value,
            content_type=content_type,
            status="processing",
        )
        self.db.add(query_record)
        self.query_repository.flush()

        # Step 3: Execute full workflow
        research_result = await self.workflow_service.execute_full_workflow(
            query_record=query_record,
            query_text=request.query,
            target_audience=target_audience,
        )

        return research_result

    # ==================== Response Mappers ====================

    @staticmethod
    def to_query_response(query: ResearchQuery) -> ResearchQueryResponse:
        """Convert ResearchQuery model to response schema"""
        return ResearchQueryResponse(
            query_id=query.id,
            status=query.status,
            created_at=query.created_at,
        )

    @staticmethod
    def to_status_response(query: ResearchQuery) -> ResearchStatusResponse:
        """Convert ResearchQuery model to status response schema"""
        return ResearchStatusResponse(
            id=query.id,
            query_text=query.query_text,
            target_audience=query.target_audience,
            topic_category=query.topic_category if query.topic_category else None,
            status=query.status,
            created_at=query.created_at,
            updated_at=query.updated_at or query.created_at,
        )

    @staticmethod
    def to_result_response(result: ResearchResult) -> ResearchResultResponse:
        """Convert ResearchResult model to response schema"""
        return ResearchResultResponse(
            query_id=result.query_id,
            topic_summary=result.topic_summary,
            key_concepts=result.key_concepts,
            mathematical_foundations=result.mathematical_foundations,
            historical_context=result.historical_context,
            implementation_examples=result.implementation_examples,
            sources=result.sources,
            completeness_score=result.completeness_score,
            created_at=result.created_at,
        )
