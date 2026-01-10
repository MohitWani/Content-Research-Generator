"""
Pipeline Service
Orchestrates end-to-end research and content generation workflows
"""
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging.logger import logger
from app.modules.branding.services import BrandingAgent, get_branding_agent
from app.modules.content.services import BlogOutput, BlogWriterAgent, get_blog_writer_agent
from app.modules.research.models.research_model import (
    ContentItem,
    PipelineExecution,
    ResearchQuery,
    ResearchResult,
    TopicCategory,
)
from app.modules.research.services import (
    AgenticResearcher,
    ResearchOutput,
    TopicAgent,
    get_agentic_researcher,
    get_topic_agent,
)
from app.modules.social.services import (
    LinkedInOutput,
    ShortformAgent,
    ThreadOutput,
    get_shortform_agent,
)


class PipelineService:
    """
    Orchestrates full research and content generation pipelines
    Combines research, blog writing, social media, and branding
    """

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        topic_agent: Optional[TopicAgent] = None,
        researcher: Optional[AgenticResearcher] = None,
        blog_writer: Optional[BlogWriterAgent] = None,
        shortform_agent: Optional[ShortformAgent] = None,
        branding_agent: Optional[BrandingAgent] = None,
    ):
        """Initialize pipeline service with agents"""
        self.db = db_session
        self.topic_agent = topic_agent or get_topic_agent()
        self.researcher = researcher or get_agentic_researcher()
        self.blog_writer = blog_writer or get_blog_writer_agent()
        self.shortform_agent = shortform_agent or get_shortform_agent()
        self.branding_agent = branding_agent or get_branding_agent()
        logger.info('PipelineService initialized')

    async def run_full_pipeline(
        self,
        query: str,
        target_audience: str = 'practitioner',
        content_types: list = None,
        apply_branding: bool = True,
        generate_social: bool = False,
    ) -> Dict[str, Any]:
        """
        Run full research -> content generation pipeline

        Args:
            query: Research query
            target_audience: Target audience
            content_types: Content types to generate
            apply_branding: Whether to apply brand voice
            generate_social: Whether to generate social media content

        Returns:
            Dict with all pipeline outputs
        """
        content_types = content_types or ['blog']
        pipeline_id = None
        research_query_id = None

        logger.info(f"[PIPELINE] Starting for: '{query[:50]}...'")

        results = {
            'query': query,
            'status': 'running',
            'steps_completed': 0,
            'total_steps': self._calculate_total_steps(content_types, apply_branding, generate_social),
        }

        try:
            # Create pipeline execution record
            if self.db:
                pipeline = PipelineExecution(
                    pipeline_type='full',
                    status='running',
                    execution_data={'query': query, 'steps': []},
                )
                self.db.add(pipeline)
                await self.db.flush()
                pipeline_id = pipeline.id
                results['pipeline_id'] = pipeline_id

            # Step 1: Categorize
            logger.info('[PIPELINE] Step 1: Categorizing query')
            categorization = await self.topic_agent.categorize_query(query)
            category = TopicCategory(categorization.category)
            results['category'] = category.value
            results['steps_completed'] += 1

            # Create research query record
            if self.db:
                research_query = ResearchQuery(
                    query_text=query,
                    topic_category=category.value,
                    target_audience=target_audience,
                    status='processing',
                )
                self.db.add(research_query)
                await self.db.flush()
                research_query_id = research_query.id
                results['research_query_id'] = research_query_id

                if pipeline_id:
                    pipeline.research_query_id = research_query_id

            # Step 2: Research
            logger.info('[PIPELINE] Step 2: Conducting research')
            research = await self.researcher.research(
                query=query,
                category=category,
                target_audience=target_audience,
            )
            results['research'] = {
                'topic_summary': research.topic_summary[:500] if research.topic_summary else '',
                'concepts_count': len(research.key_concepts),
                'sources_count': len(research.sources),
                'completeness_score': research.completeness_score,
                'data_path': research.research_data_path,
            }
            results['steps_completed'] += 1

            # Save research result
            if self.db and research_query_id:
                research_result = ResearchResult(
                    query_id=research_query_id,
                    topic_summary=research.topic_summary,
                    key_concepts=research.key_concepts,
                    mathematical_foundations=research.mathematical_foundations,
                    historical_context=research.source_descriptions,
                    implementation_examples=research.implementation_examples,
                    sources=research.sources,
                    research_data_path=research.research_data_path,
                    completeness_score=research.completeness_score,
                )
                self.db.add(research_result)
                await self.db.flush()

            # Step 3: Generate content
            if 'blog' in content_types:
                logger.info('[PIPELINE] Step 3: Generating blog')
                blog = await self.blog_writer.generate_blog(
                    topic=query,
                    research_data=research,
                    target_audience=target_audience,
                )

                # Apply branding if requested
                if apply_branding and blog.content:
                    logger.info('[PIPELINE] Applying brand voice')
                    branded = await self.branding_agent.apply_branding(
                        content=blog.content,
                        target_audience=target_audience,
                        content_type='blog',
                    )
                    blog.content = branded.branded_content
                    blog.file_path = branded.file_path or blog.file_path
                    results['branding'] = {
                        'voice_score': branded.voice_score,
                        'changes_count': len(branded.changes_made),
                    }
                    results['steps_completed'] += 1

                results['blog'] = {
                    'title': blog.title,
                    'content_length': len(blog.content),
                    'tags': blog.tags,
                    'reading_time': blog.estimated_reading_time,
                    'file_path': blog.file_path,
                }
                results['steps_completed'] += 1

                # Save content item
                if self.db and research_query_id:
                    content_item = ContentItem(
                        research_query_id=research_query_id,
                        content_type='blog',
                        title=blog.title,
                        content=blog.content,
                        file_path=blog.file_path,
                        target_audience=target_audience,
                        tags=blog.tags,
                        status='published',
                    )
                    self.db.add(content_item)

                # Step 4: Generate social content if requested
                if generate_social:
                    logger.info('[PIPELINE] Step 4: Generating social content')
                    social_results = await self.shortform_agent.generate_from_blog(
                        blog=blog,
                        platforms=['linkedin', 'twitter'],
                    )

                    results['social'] = {}
                    if 'linkedin' in social_results:
                        li = social_results['linkedin']
                        results['social']['linkedin'] = {
                            'character_count': li.character_count,
                            'hashtags': li.hashtags,
                            'file_path': li.file_path,
                        }
                    if 'twitter' in social_results:
                        tw = social_results['twitter']
                        results['social']['twitter'] = {
                            'total_posts': tw.total_posts,
                            'file_path': tw.file_path,
                        }
                    results['steps_completed'] += 1

            # Complete pipeline
            results['status'] = 'completed'
            results['completed_at'] = datetime.now().isoformat()

            if self.db:
                if pipeline_id:
                    pipeline.status = 'completed'
                    pipeline.completed_at = datetime.now()
                    pipeline.execution_data = results

                if research_query_id:
                    research_query.status = 'completed'

                await self.db.commit()

            logger.info(f'[PIPELINE] Completed: {results["steps_completed"]}/{results["total_steps"]} steps')
            return results

        except Exception as e:
            logger.error(f'[PIPELINE] Failed: {e}', exc_info=True)
            results['status'] = 'failed'
            results['error'] = str(e)

            if self.db:
                if pipeline_id:
                    pipeline.status = 'failed'
                    pipeline.error_message = str(e)
                    pipeline.completed_at = datetime.now()

                if research_query_id:
                    research_query.status = 'failed'

                await self.db.commit()

            return results

    def _calculate_total_steps(
        self,
        content_types: list,
        apply_branding: bool,
        generate_social: bool,
    ) -> int:
        """Calculate total pipeline steps"""
        steps = 2  # categorize + research

        if 'blog' in content_types:
            steps += 1  # blog generation
            if apply_branding:
                steps += 1  # branding

        if generate_social:
            steps += 1  # social content

        return steps

    async def run_research_only(
        self,
        query: str,
        target_audience: str = 'practitioner',
    ) -> ResearchOutput:
        """Run research-only pipeline"""
        categorization = await self.topic_agent.categorize_query(query)
        category = TopicCategory(categorization.category)

        return await self.researcher.research(
            query=query,
            category=category,
            target_audience=target_audience,
        )

    async def run_blog_from_research(
        self,
        research: ResearchOutput,
        topic: str,
        target_audience: str = 'practitioner',
        apply_branding: bool = True,
    ) -> BlogOutput:
        """Generate blog from existing research"""
        blog = await self.blog_writer.generate_blog(
            topic=topic,
            research_data=research,
            target_audience=target_audience,
        )

        if apply_branding and blog.content:
            branded = await self.branding_agent.apply_branding(
                content=blog.content,
                target_audience=target_audience,
                content_type='blog',
            )
            blog.content = branded.branded_content
            blog.file_path = branded.file_path or blog.file_path

        return blog


def get_pipeline_service(
    db_session: Optional[AsyncSession] = None,
) -> PipelineService:
    """Factory function to create PipelineService"""
    return PipelineService(db_session=db_session)
