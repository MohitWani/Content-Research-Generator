"""
Workflow Manager for orchestrating multi-agent workflows
Coordinates Topic Agent → Research Agent → Blog Writer Agent pipelines
Maps to: spec.md → FR6 (Multi-Agent Orchestration)
"""
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.lib.agents.topic_agent import TopicAgent
from src.lib.agents.agentic_researcher import AgenticResearcher, ResearchOutput
from src.lib.agents.blog_writer_agent import BlogWriterAgent, BlogOutput
from src.lib.models.research import (
    ResearchQuery,
    ResearchResult,
    ContentItem,
    PipelineExecution,
    TopicCategory,
)
from src.lib.models.exceptions import (
    ResearchDataInsufficientError,
    QueryCategorizationError,
)
from src.common.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ResearchWorkflowResult:
    """Result from research workflow execution"""
    query_id: int
    topic_category: TopicCategory
    research_result: Optional[ResearchOutput] = None
    status: str = "completed"
    pipeline_id: Optional[int] = None


@dataclass
class BlogWorkflowResult:
    """Result from blog generation workflow execution"""
    content_id: int
    title: str
    content: str
    target_audience: str
    status: str = "ready"
    file_path: Optional[str] = None


class WorkflowManager:
    """
    Orchestrates multi-agent workflows for research and content generation
    Uses AgenticResearcher with LangGraph's create_react_agent
    """
    
    def __init__(
        self,
        topic_agent: Optional[TopicAgent] = None,
        research_agent: Optional[AgenticResearcher] = None,
        blog_writer_agent: Optional[BlogWriterAgent] = None,
        db_session: Optional[AsyncSession] = None,
        llm: Optional[Any] = None,
    ):
        """
        Initialize workflow manager with agents
        
        Args:
            topic_agent: Agent for topic categorization
            research_agent: AgenticResearcher with LangGraph
            blog_writer_agent: Agent for blog generation
            db_session: Database session for persistence
            llm: Optional LLM instance (used to create default agents)
        """
        self.topic_agent = topic_agent or TopicAgent(llm=llm)
        self.research_agent = research_agent or AgenticResearcher(llm=llm, max_iterations=5)
        self.blog_writer_agent = blog_writer_agent or BlogWriterAgent(llm=llm)
        self.db_session = db_session
        
        logger.info("Initialized WorkflowManager with AgenticResearcher")
    
    async def execute_research_workflow(
        self,
        query: str,
        target_audience: str = "practitioner",
    ) -> ResearchWorkflowResult:
        """
        Execute complete research workflow: Categorize → Research → Persist
        
        Args:
            query: User research query
            target_audience: Target audience for content
        
        Returns:
            ResearchWorkflowResult with query ID, category, and research data
        
        Raises:
            QueryCategorizationError: If query cannot be categorized or is non-AI
        """
        logger.info(f"Starting research workflow for: {query[:50]}...")
        
        # Step 1: Create pipeline execution record
        pipeline = await self._create_pipeline_execution("research")
        
        try:
            # Step 2: Categorize the query
            categorization = await self.topic_agent.categorize_query(query)
            
            # Convert category string to enum
            if categorization.category == "core_ai":
                topic_category = TopicCategory.CORE_AI
            else:
                topic_category = TopicCategory.PRACTICAL_IMPLEMENTATION
            
            logger.debug(f"Query categorized as: {topic_category.value}")
            
            # Step 3: Create research query in database
            research_query = await self._create_research_query(
                query=query,
                target_audience=target_audience,
                topic_category=topic_category,
                pipeline_id=pipeline.id if pipeline else None,
            )
            
            # Step 4: Conduct research
            research_output = await self.research_agent.research(
                query=query,
                category=topic_category,
                target_audience=target_audience,
            )
            
            # Step 5: Persist research result
            await self._persist_research_result(
                query_id=research_query.id,
                research_output=research_output,
            )
            
            # Step 6: Update query status
            research_query.status = "completed"
            if self.db_session:
                await self.db_session.flush()
            
            # Step 7: Update pipeline status
            if pipeline:
                await self._update_pipeline_status(pipeline.id, "completed")
            
            logger.info(f"Research workflow completed for query ID: {research_query.id}")
            
            return ResearchWorkflowResult(
                query_id=research_query.id,
                topic_category=topic_category,
                research_result=research_output,
                status="completed",
                pipeline_id=pipeline.id if pipeline else None,
            )
            
        except QueryCategorizationError:
            if pipeline:
                await self._update_pipeline_status(pipeline.id, "failed")
            raise
        except Exception as e:
            logger.error(f"Research workflow error: {e}")
            if pipeline:
                await self._update_pipeline_status(pipeline.id, "failed")
            raise
    
    async def execute_blog_generation_workflow(
        self,
        research_query_id: int,
        target_audience: str = "practitioner",
        tone: str = "professional",
    ) -> BlogWorkflowResult:
        """
        Execute blog generation workflow from existing research
        
        Args:
            research_query_id: ID of the research query
            target_audience: Target audience for blog
            tone: Writing tone
        
        Returns:
            BlogWorkflowResult with content ID and blog data
        
        Raises:
            ResearchDataInsufficientError: If research data doesn't exist
        """
        logger.info(f"Starting blog generation for query ID: {research_query_id}")
        
        # Step 1: Create pipeline execution record
        pipeline = await self._create_pipeline_execution(
            "blog_generation", 
            research_query_id
        )
        
        try:
            # Step 2: Fetch research data
            research_result = await self._get_research_result(research_query_id)
            
            if not research_result:
                raise ResearchDataInsufficientError(
                    f"No research data found for query ID: {research_query_id}"
                )
            
            # Step 3: Convert to dict for blog generation
            research_data = {
                "topic_summary": research_result.topic_summary,
                "key_concepts": research_result.key_concepts or {},
                "mathematical_foundations": research_result.mathematical_foundations,
                "historical_context": research_result.historical_context,
                "implementation_examples": research_result.implementation_examples,
                "sources": research_result.sources or [],
            }
            
            # Step 4: Generate blog
            blog_output = await self.blog_writer_agent.generate_blog(
                research_data=research_data,
                target_audience=target_audience,
                tone=tone,
            )
            
            # Step 5: Persist content item
            content_item = await self._persist_content_item(
                research_query_id=research_query_id,
                blog_output=blog_output,
            )
            
            # Step 6: Update pipeline status
            if pipeline:
                await self._update_pipeline_status(pipeline.id, "completed")
            
            logger.info(f"Blog generation completed: {blog_output.title}")
            
            return BlogWorkflowResult(
                content_id=content_item.id,
                title=blog_output.title,
                content=blog_output.content,
                target_audience=blog_output.target_audience,
                status=blog_output.status,
                file_path=blog_output.file_path,
            )
            
        except ResearchDataInsufficientError:
            if pipeline:
                await self._update_pipeline_status(pipeline.id, "failed")
            raise
        except Exception as e:
            logger.error(f"Blog generation error: {e}")
            if pipeline:
                await self._update_pipeline_status(pipeline.id, "failed")
            raise
    
    async def execute_full_workflow(
        self,
        query: str,
        target_audience: str = "practitioner",
        tone: str = "professional",
    ) -> tuple[ResearchWorkflowResult, BlogWorkflowResult]:
        """
        Execute complete workflow: Query → Research → Blog
        
        Args:
            query: User research query
            target_audience: Target audience
            tone: Writing tone
        
        Returns:
            Tuple of (ResearchWorkflowResult, BlogWorkflowResult)
        """
        # Execute research workflow
        research_result = await self.execute_research_workflow(query, target_audience)
        
        # Execute blog generation
        blog_result = await self.execute_blog_generation_workflow(
            research_result.query_id,
            target_audience,
            tone,
        )
        
        return research_result, blog_result
    
    # Private helper methods
    
    async def _create_pipeline_execution(
        self,
        pipeline_type: str,
        research_query_id: Optional[int] = None,
    ) -> Optional[PipelineExecution]:
        """Create pipeline execution record"""
        if not self.db_session:
            return None
        
        pipeline = PipelineExecution(
            pipeline_type=pipeline_type,
            research_query_id=research_query_id,
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db_session.add(pipeline)
        await self.db_session.flush()
        return pipeline
    
    async def _update_pipeline_status(
        self,
        pipeline_id: int,
        status: str,
    ) -> None:
        """Update pipeline execution status"""
        if not self.db_session:
            return
        
        pipeline = await self.db_session.get(PipelineExecution, pipeline_id)
        if pipeline:
            pipeline.status = status
            if status in ["completed", "failed"]:
                pipeline.completed_at = datetime.utcnow()
            await self.db_session.flush()
    
    async def _create_research_query(
        self,
        query: str,
        target_audience: str,
        topic_category: TopicCategory,
        pipeline_id: Optional[int] = None,
    ) -> ResearchQuery:
        """Create research query in database"""
        research_query = ResearchQuery(
            query_text=query,
            target_audience=target_audience,
            topic_category=topic_category.value if topic_category else None,
            status="processing",
        )
        
        if self.db_session:
            self.db_session.add(research_query)
            await self.db_session.flush()
            await self.db_session.refresh(research_query)
            
            # Link to pipeline if exists
            if pipeline_id:
                pipeline = await self.db_session.get(PipelineExecution, pipeline_id)
                if pipeline:
                    pipeline.research_query_id = research_query.id
                    await self.db_session.flush()
        
        return research_query
    
    async def _persist_research_result(
        self,
        query_id: int,
        research_output: ResearchOutput,
    ) -> Optional[ResearchResult]:
        """Persist research result to database"""
        if not self.db_session:
            return None
        
        result = ResearchResult(
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
        
        self.db_session.add(result)
        await self.db_session.flush()
        return result
    
    async def _get_research_result(
        self,
        query_id: int,
    ) -> Optional[ResearchResult]:
        """Get research result from database"""
        if not self.db_session:
            return None
        
        result = await self.db_session.scalar(
            select(ResearchResult).where(ResearchResult.query_id == query_id)
        )
        return result
    
    async def _persist_content_item(
        self,
        research_query_id: int,
        blog_output: BlogOutput,
    ) -> ContentItem:
        """Persist content item to database"""
        content_item = ContentItem(
            research_query_id=research_query_id,
            content_type="blog",
            title=blog_output.title,
            content=blog_output.content,
            target_audience=blog_output.target_audience,
            tone=blog_output.tone,
            status=blog_output.status,
            file_path=blog_output.file_path,
            meta_description=blog_output.meta_description,
            tags=blog_output.tags,
        )
        
        if self.db_session:
            self.db_session.add(content_item)
            await self.db_session.flush()
            await self.db_session.refresh(content_item)
        
        return content_item

