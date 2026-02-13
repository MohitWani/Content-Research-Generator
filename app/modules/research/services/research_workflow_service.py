"""
Research Workflow Service - Orchestrates the research workflow.
Handles topic categorization and research execution logic.
"""
from sqlalchemy.orm import Session

from app.core.logging.logger import logger
from app.modules.research.models.research_model import (
    ResearchQuery,
    ResearchResult,
    TopicCategory,
)
from app.modules.research.repositories.research_repository import (
    ResearchQueryRepository,
    ResearchResultRepository,
)
from app.modules.research.schemas.agent_schemas import ResearchOutput
from app.modules.research.services.agentic_researcher import AgenticResearcher
from app.modules.research.services.nodes import TopicAgentNode


class ResearchWorkflowService:
    """
    Service for orchestrating the research workflow.
    Handles topic categorization and research execution.
    """

    def __init__(self, db: Session):
        """
        Initialize the research workflow service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.query_repository = ResearchQueryRepository(db)
        self.result_repository = ResearchResultRepository(db)
        self.topic_agent_node = TopicAgentNode()
        logger.info("ResearchWorkflowService initialized")

    async def categorize_query(self, query_text: str) -> TopicCategory:
        """
        Categorize a research query using the topic agent node.
        
        Args:
            query_text: The query text to categorize
            
        Returns:
            The determined TopicCategory
        """
        logger.info(f"[WORKFLOW] Categorizing query: {query_text[:50]}...")
        topic_category = await self.topic_agent_node.categorize(query_text)
        logger.info(f"[WORKFLOW] Query categorized as: {topic_category.value}")
        return topic_category

    async def execute_research(
        self,
        query_text: str,
        topic_category: TopicCategory,
        target_audience: str,
        max_iterations: int = 5,
    ) -> ResearchOutput:
        """
        Execute the agentic research process.
        
        Args:
            query_text: The research query
            topic_category: The categorized topic
            target_audience: Target audience for the research
            max_iterations: Maximum research iterations
            
        Returns:
            ResearchOutput from the agentic researcher
        """
        logger.info(
            f"[WORKFLOW] Executing research: category={topic_category.value}, "
            f"audience={target_audience}, max_iterations={max_iterations}"
        )
        researcher = AgenticResearcher(max_iterations=max_iterations)
        result = await researcher.research(
            query=query_text,
            category=topic_category,
            target_audience=target_audience,
        )
        logger.info(
            f"[WORKFLOW] Research execution completed: score={result.completeness_score:.2f}"
        )
        return result

    def create_research_result(
        self,
        query_id: int,
        research_output: ResearchOutput,
    ) -> ResearchResult:
        """
        Create a ResearchResult from research output.
        
        Args:
            query_id: The associated query ID
            research_output: Output from the agentic researcher
            
        Returns:
            The created ResearchResult (not yet committed)
        """
        logger.debug(f"[WORKFLOW] Creating ResearchResult for query_id: {query_id}")
        return ResearchResult(
            query_id=query_id,
            topic_summary=research_output.topic_summary,
            key_concepts=research_output.key_concepts,
            mathematical_foundations=research_output.mathematical_foundations,
            historical_context=research_output.source_descriptions,
            implementation_examples=research_output.implementation_examples,
            sources=research_output.sources,
            completeness_score=research_output.completeness_score,
            research_data_path=research_output.research_data_path,
        )

    async def execute_full_workflow(
        self,
        query_record: ResearchQuery,
        query_text: str,
        target_audience: str,
    ) -> ResearchResult:
        """
        Execute the complete research workflow for a query.
        
        Args:
            query_record: The ResearchQuery record
            query_text: The query text
            target_audience: Target audience for research
            
        Returns:
            The created ResearchResult
        """
        logger.info(f"[WORKFLOW] Starting full workflow for query_id: {query_record.id}")

        # Step 1: Categorize the query
        logger.info(f"[WORKFLOW] Step 1: Categorizing query for query_id: {query_record.id}")
        topic_category = await self.categorize_query(query_text)

        # Step 2: Update query with category
        logger.info(f"[WORKFLOW] Step 2: Updating category for query_id: {query_record.id}")
        query_record.topic_category = topic_category.value
        self.query_repository.commit()
        logger.info(f"[WORKFLOW] Query {query_record.id} categorized as: {topic_category.value}")

        # Step 3: Execute research
        logger.info(f"[WORKFLOW] Step 3: Executing research for query_id: {query_record.id}")
        research_output = await self.execute_research(
            query_text=query_text,
            topic_category=topic_category,
            target_audience=target_audience,
        )

        # Step 4: Create and persist research result
        logger.info(f"[WORKFLOW] Step 4: Persisting result for query_id: {query_record.id}")
        research_result = self.create_research_result(
            query_id=query_record.id,
            research_output=research_output,
        )
        self.result_repository.add_without_commit(research_result)

        # Step 5: Update query status and commit
        logger.info(f"[WORKFLOW] Step 5: Finalizing workflow for query_id: {query_record.id}")
        query_record.status = "completed"
        self.query_repository.commit()
        self.result_repository.refresh(research_result)

        logger.info(
            f"[WORKFLOW] Full workflow completed for query_id: {query_record.id}, "
            f"result_id: {research_result.id}"
        )

        return research_result
