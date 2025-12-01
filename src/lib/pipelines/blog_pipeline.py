"""
Blog Generation Pipeline for automated content creation
Orchestrates: Research → Blog → Branding → Publishing
Maps to: spec.md → Story 6, FR6
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.lib.agents.blog_writer_agent import BlogWriterAgent, BlogOutput
from src.lib.agents.branding_agent import BrandingAgent
from src.lib.agents.shortform_agent import ShortformAgent, LinkedInPost
from src.lib.orchestrator.state_manager import (
    StateManager,
    CheckpointType,
)
from src.lib.models.research import ResearchResult, ContentItem
from src.lib.models.exceptions import ResearchDataInsufficientError
from src.common.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class BlogPipelineResult:
    """Result from blog generation pipeline"""
    content_id: int
    blog_output: BlogOutput
    branded: bool
    linkedin_post: Optional[LinkedInPost] = None
    execution_time_seconds: float = 0.0
    status: str = "completed"


class BlogGenerationPipeline:
    """
    Automated blog generation pipeline
    Handles research → blog → branding → social content
    """
    
    def __init__(
        self,
        blog_writer: Optional[BlogWriterAgent] = None,
        branding_agent: Optional[BrandingAgent] = None,
        shortform_agent: Optional[ShortformAgent] = None,
        state_manager: Optional[StateManager] = None,
        db_session: Optional[AsyncSession] = None,
    ):
        """
        Initialize blog generation pipeline
        
        Args:
            blog_writer: Blog writer agent
            branding_agent: Branding agent
            shortform_agent: Shortform agent for social
            state_manager: State manager
            db_session: Database session
        """
        self.blog_writer = blog_writer or BlogWriterAgent()
        self.branding_agent = branding_agent or BrandingAgent()
        self.shortform_agent = shortform_agent or ShortformAgent()
        self.state_manager = state_manager or StateManager(db_session)
        self.db_session = db_session
        
        logger.info("Initialized BlogGenerationPipeline")
    
    async def execute(
        self,
        research_query_id: int,
        target_audience: str = "practitioner",
        tone: str = "professional",
        apply_branding: bool = True,
        generate_social: bool = True,
    ) -> BlogPipelineResult:
        """
        Execute the blog generation pipeline
        
        Args:
            research_query_id: ID of research query
            target_audience: Target audience
            tone: Writing tone
            apply_branding: Apply brand voice
            generate_social: Generate LinkedIn post
        
        Returns:
            BlogPipelineResult with generated content
        """
        start_time = datetime.utcnow()
        
        # Create workflow context
        context = await self.state_manager.create_workflow(
            "blog_generation",
            query_id=research_query_id,
        )
        await self.state_manager.start_workflow(context.workflow_id)
        
        try:
            # Step 1: Fetch research data
            logger.info(f"Pipeline step 1: Fetching research data")
            research_data = await self._get_research_data(research_query_id)
            
            if not research_data:
                raise ResearchDataInsufficientError(
                    f"No research data for query ID: {research_query_id}"
                )
            
            await self.state_manager.add_checkpoint(
                context.workflow_id,
                CheckpointType.BLOG_STARTED,
            )
            
            # Step 2: Generate blog
            logger.info(f"Pipeline step 2: Generating blog")
            blog_output = await self.blog_writer.generate_blog(
                research_data=research_data,
                target_audience=target_audience,
                tone=tone,
            )
            
            # Step 3: Apply branding (optional)
            if apply_branding:
                logger.info(f"Pipeline step 3: Applying branding")
                branding_result = await self.branding_agent.apply_branding(
                    content=blog_output.content,
                    target_audience=target_audience,
                    content_type="blog",
                )
                blog_output.content = branding_result.branded_content
            
            # Step 4: Persist content
            content_id = await self._persist_content(
                research_query_id,
                blog_output,
            )
            
            # Step 5: Generate LinkedIn post (optional)
            linkedin_post = None
            if generate_social:
                logger.info(f"Pipeline step 4: Generating social content")
                linkedin_post = await self.shortform_agent.generate_linkedin_post(
                    source_content=blog_output,
                    target_audience=target_audience,
                )
            
            await self.state_manager.add_checkpoint(
                context.workflow_id,
                CheckpointType.BLOG_COMPLETED,
                data={"content_id": content_id, "has_social": generate_social},
            )
            
            # Complete workflow
            await self.state_manager.complete_workflow(context.workflow_id)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Blog pipeline completed in {execution_time:.2f}s")
            
            return BlogPipelineResult(
                content_id=content_id,
                blog_output=blog_output,
                branded=apply_branding,
                linkedin_post=linkedin_post,
                execution_time_seconds=execution_time,
            )
            
        except Exception as e:
            await self.state_manager.fail_workflow(context.workflow_id, str(e))
            logger.error(f"Blog pipeline failed: {e}")
            raise
    
    async def execute_from_research(
        self,
        research_output: Dict[str, Any],
        target_audience: str = "practitioner",
        tone: str = "professional",
    ) -> BlogPipelineResult:
        """
        Execute pipeline from research output directly (no DB lookup)
        
        Args:
            research_output: Research output dict
            target_audience: Target audience
            tone: Writing tone
        
        Returns:
            BlogPipelineResult
        """
        start_time = datetime.utcnow()
        
        # Generate blog
        blog_output = await self.blog_writer.generate_blog(
            research_data=research_output,
            target_audience=target_audience,
            tone=tone,
        )
        
        # Apply branding
        branding_result = await self.branding_agent.apply_branding(
            content=blog_output.content,
            target_audience=target_audience,
        )
        blog_output.content = branding_result.branded_content
        
        # Generate social
        linkedin_post = await self.shortform_agent.generate_linkedin_post(
            source_content=blog_output,
            target_audience=target_audience,
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return BlogPipelineResult(
            content_id=0,
            blog_output=blog_output,
            branded=True,
            linkedin_post=linkedin_post,
            execution_time_seconds=execution_time,
        )
    
    async def _get_research_data(self, query_id: int) -> Optional[Dict[str, Any]]:
        """Get research data from database"""
        if not self.db_session:
            return None
        
        result = await self.db_session.scalar(
            select(ResearchResult).where(ResearchResult.query_id == query_id)
        )
        
        if not result:
            return None
        
        return {
            "topic_summary": result.topic_summary,
            "key_concepts": result.key_concepts or {},
            "mathematical_foundations": result.mathematical_foundations,
            "historical_context": result.historical_context,
            "implementation_examples": result.implementation_examples,
            "sources": result.sources or [],
        }
    
    async def _persist_content(
        self,
        research_query_id: int,
        blog_output: BlogOutput,
    ) -> int:
        """Persist content to database"""
        if not self.db_session:
            return 0
        
        content = ContentItem(
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
        self.db_session.add(content)
        await self.db_session.flush()
        return content.id

