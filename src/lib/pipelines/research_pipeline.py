"""
Research Pipeline for automated research workflows
Orchestrates: Topic Categorization → Data Collection → Synthesis
Maps to: spec.md → Story 6, FR6
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.lib.agents.topic_agent import TopicAgent
from src.lib.agents.react_research_agent import ReActResearchAgent, ResearchOutput
from src.lib.orchestrator.state_manager import (
    StateManager,
    CheckpointType,
    WorkflowState,
)
from src.lib.models.research import TopicCategory, ResearchQuery, ResearchResult
from src.lib.models.exceptions import QueryCategorizationError
from src.common.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ResearchPipelineResult:
    """Result from research pipeline execution"""
    query_id: int
    topic_category: TopicCategory
    research_output: ResearchOutput
    completeness_score: float
    sources_count: int
    execution_time_seconds: float
    status: str = "completed"


class ResearchPipeline:
    """
    Automated research pipeline
    Handles the full research workflow with checkpointing
    Uses LangGraph ReAct agent with LangChain tools
    """
    
    def __init__(
        self,
        topic_agent: Optional[TopicAgent] = None,
        research_agent: Optional[ReActResearchAgent] = None,
        state_manager: Optional[StateManager] = None,
        db_session: Optional[AsyncSession] = None,
    ):
        """
        Initialize research pipeline
        
        Args:
            topic_agent: Topic categorization agent
            research_agent: ReAct research agent with LangChain tools
            state_manager: State manager for checkpoints
            db_session: Database session
        """
        self.topic_agent = topic_agent or TopicAgent()
        self.research_agent = research_agent or ReActResearchAgent(max_iterations=10)
        self.state_manager = state_manager or StateManager(db_session)
        self.db_session = db_session
        
        logger.info("Initialized ResearchPipeline")
    
    async def execute(
        self,
        query: str,
        target_audience: str = "practitioner",
    ) -> ResearchPipelineResult:
        """
        Execute the research pipeline
        
        Args:
            query: Research query
            target_audience: Target audience
        
        Returns:
            ResearchPipelineResult with research output
        """
        start_time = datetime.utcnow()
        
        # Create workflow context
        context = await self.state_manager.create_workflow("research")
        await self.state_manager.start_workflow(context.workflow_id)
        
        try:
            # Step 1: Categorize topic
            logger.info(f"Pipeline step 1: Categorizing query")
            categorization = await self.topic_agent.categorize_query(query)
            
            topic_category = (
                TopicCategory.CORE_AI 
                if categorization.category == "core_ai" 
                else TopicCategory.PRACTICAL_IMPLEMENTATION
            )
            
            await self.state_manager.add_checkpoint(
                context.workflow_id,
                CheckpointType.TOPIC_CATEGORIZED,
                data={"category": topic_category.value, "confidence": categorization.confidence},
            )
            
            # Step 2: Create research query record
            query_id = await self._create_query_record(
                query, target_audience, topic_category
            )
            
            # Step 3: Conduct research
            logger.info(f"Pipeline step 2: Conducting research")
            await self.state_manager.add_checkpoint(
                context.workflow_id,
                CheckpointType.RESEARCH_STARTED,
            )
            
            research_output = await self.research_agent.conduct_research(
                query=query,
                category=topic_category,
                target_audience=target_audience,
            )
            
            await self.state_manager.add_checkpoint(
                context.workflow_id,
                CheckpointType.SOURCES_COLLECTED,
                data={"sources_count": len(research_output.sources)},
            )
            
            # Step 4: Persist research result
            logger.info(f"Pipeline step 3: Persisting results")
            await self._persist_result(query_id, research_output)
            
            await self.state_manager.add_checkpoint(
                context.workflow_id,
                CheckpointType.RESEARCH_COMPLETED,
                data={"completeness": research_output.completeness_score},
            )
            
            # Complete workflow
            await self.state_manager.complete_workflow(context.workflow_id)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Research pipeline completed in {execution_time:.2f}s "
                f"(completeness: {research_output.completeness_score:.2f})"
            )
            
            return ResearchPipelineResult(
                query_id=query_id,
                topic_category=topic_category,
                research_output=research_output,
                completeness_score=research_output.completeness_score,
                sources_count=len(research_output.sources),
                execution_time_seconds=execution_time,
            )
            
        except QueryCategorizationError as e:
            await self.state_manager.fail_workflow(context.workflow_id, str(e))
            raise
        except Exception as e:
            await self.state_manager.fail_workflow(context.workflow_id, str(e))
            logger.error(f"Research pipeline failed: {e}")
            raise
    
    async def execute_batch(
        self,
        queries: List[str],
        target_audience: str = "practitioner",
    ) -> List[ResearchPipelineResult]:
        """
        Execute research pipeline for multiple queries
        
        Args:
            queries: List of research queries
            target_audience: Target audience
        
        Returns:
            List of results
        """
        results = []
        for query in queries:
            try:
                result = await self.execute(query, target_audience)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch query failed: {query[:50]}... - {e}")
        return results
    
    async def _create_query_record(
        self,
        query: str,
        target_audience: str,
        topic_category: TopicCategory,
    ) -> int:
        """Create research query record in database"""
        if not self.db_session:
            return 0
        
        research_query = ResearchQuery(
            query_text=query,
            target_audience=target_audience,
            topic_category=topic_category.value if topic_category else None,
            status="processing",
        )
        self.db_session.add(research_query)
        await self.db_session.flush()
        return research_query.id
    
    async def _persist_result(
        self,
        query_id: int,
        research_output: ResearchOutput,
    ) -> None:
        """Persist research result to database"""
        if not self.db_session or query_id == 0:
            return
        
        result = ResearchResult(
            query_id=query_id,
            topic_summary=research_output.topic_summary,
            key_concepts=research_output.key_concepts,
            mathematical_foundations=research_output.mathematical_foundations,
            historical_context=research_output.historical_context,
            implementation_examples=research_output.implementation_examples,
            sources=research_output.sources,
            completeness_score=research_output.completeness_score,
            research_data_path=research_output.research_data_path,
        )
        self.db_session.add(result)
        
        # Update query status
        query = await self.db_session.get(ResearchQuery, query_id)
        if query:
            query.status = "completed"
        
        await self.db_session.flush()

