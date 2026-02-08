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
from app.modules.research.services.agentic_researcher import AgenticResearcher
from app.modules.research.services.topic_agent import TopicAgent


# Category mapping for topic categorization
CATEGORY_MAP = {
    "core_ai": TopicCategory.CORE_AI,
    "practical_implementation": TopicCategory.PRACTICAL_IMPLEMENTATION,
    "software_development": TopicCategory.SOFTWARE_DEVELOPMENT,
    "web_development": TopicCategory.WEB_DEVELOPMENT,
    "devops": TopicCategory.DEVOPS,
    "general_tech": TopicCategory.GENERAL_TECH,
}


class ResearchWorkflowService:
    """
    Service for orchestrating the research workflow.
    Handles topic categorization and research execution.
    """

    def __init__(self, db: Session):
        self.db = db
        self.query_repository = ResearchQueryRepository(db)
        self.result_repository = ResearchResultRepository(db)
        self.topic_agent = TopicAgent()

    async def categorize_query(self, query_text: str) -> TopicCategory:
        """
        Categorize a research query using the topic agent.
        
        Args:
            query_text: The query text to categorize
            
        Returns:
            The determined TopicCategory
        """
        categorization = await self.topic_agent.categorize_query(query_text)
        topic_category = CATEGORY_MAP.get(
            categorization.category, TopicCategory.GENERAL_TECH
        )
        logger.info(f"Query categorized as: {topic_category.value}")
        return topic_category

    async def execute_research(
        self,
        query_text: str,
        topic_category: TopicCategory,
        target_audience: str,
        max_iterations: int = 5,
    ) -> "ResearchOutput":
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
        researcher = AgenticResearcher(max_iterations=max_iterations)
        return await researcher.research(
            query=query_text,
            category=topic_category,
            target_audience=target_audience,
        )

    def create_research_result(
        self,
        query_id: int,
        research_output: "ResearchOutput",
    ) -> ResearchResult:
        """
        Create a ResearchResult from research output.
        
        Args:
            query_id: The associated query ID
            research_output: Output from the agentic researcher
            
        Returns:
            The created ResearchResult (not yet committed)
        """
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
        # Step 1: Categorize the query
        topic_category = await self.categorize_query(query_text)

        # Step 2: Update query with category
        query_record.topic_category = topic_category.value
        self.query_repository.commit()

        logger.info(f"Query {query_record.id} categorized as: {topic_category.value}")

        # Step 3: Execute research
        research_output = await self.execute_research(
            query_text=query_text,
            topic_category=topic_category,
            target_audience=target_audience,
        )

        # Step 4: Create and persist research result
        research_result = self.create_research_result(
            query_id=query_record.id,
            research_output=research_output,
        )
        self.result_repository.add_without_commit(research_result)

        # Step 5: Update query status and commit
        query_record.status = "completed"
        self.query_repository.commit()
        self.result_repository.refresh(research_result)

        logger.info(f"Research workflow completed: query_id={query_record.id}")

        return research_result


# Import for type hints
from app.modules.research.services.agentic_researcher import ResearchOutput  # noqa: E402
