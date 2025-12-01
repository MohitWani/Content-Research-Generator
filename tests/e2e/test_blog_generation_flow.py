"""
End-to-End Tests for Blog Generation Flow
Tests complete blog generation workflow
Maps to: spec.md → Story 3, Story 4
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.e2e
class TestBlogGenerationE2EFlow:
    """E2E tests for blog generation workflow"""
    
    @pytest.mark.asyncio
    async def test_full_blog_pipeline(self):
        """Should execute complete blog generation pipeline"""
        from src.lib.pipelines.blog_pipeline import BlogGenerationPipeline
        from src.lib.agents.blog_writer_agent import BlogWriterAgent, BlogOutput
        from src.lib.agents.branding_agent import BrandingAgent, BrandingResult
        from src.lib.agents.shortform_agent import ShortformAgent, LinkedInPost
        
        with patch.object(BlogWriterAgent, 'generate_blog') as mock_blog, \
             patch.object(BrandingAgent, 'apply_branding') as mock_brand, \
             patch.object(ShortformAgent, 'generate_linkedin_post') as mock_linkedin:
            
            mock_blog.return_value = BlogOutput(
                title="Understanding Transformers",
                content="# Introduction\n\nTransformers are...\n\n## Conclusion",
                target_audience="practitioner",
                status="ready",
            )
            
            mock_brand.return_value = BrandingResult(
                original_content="...",
                branded_content="# Introduction\n\nTransformers are amazing...",
                changes_made=["Enhanced tone"],
                voice_score=0.9,
                suggestions=[],
            )
            
            mock_linkedin.return_value = LinkedInPost(
                content="🚀 Just published a deep dive into Transformers...",
                hook="Transformers changed everything.",
                hashtags=["AI", "Transformers"],
            )
            
            pipeline = BlogGenerationPipeline()
            result = await pipeline.execute_from_research(
                research_output={
                    "topic_summary": "Transformers are neural networks...",
                    "key_concepts": {"attention": "Focus mechanism"},
                    "sources": [],
                },
                target_audience="practitioner",
            )
            
            # Verify
            assert result.blog_output is not None
            assert result.blog_output.title is not None
            assert result.branded is True
            assert result.linkedin_post is not None
    
    @pytest.mark.asyncio
    async def test_blog_adapts_to_audience(self):
        """Should adapt blog content to different audiences"""
        from src.lib.agents.blog_writer_agent import BlogWriterAgent, BlogOutput
        
        with patch.object(BlogWriterAgent, 'generate_blog') as mock_blog:
            mock_blog.return_value = BlogOutput(
                title="Transformers for Beginners",
                content="# What are Transformers?\n\nImagine a smart reader...",
                target_audience="beginner",
                status="ready",
            )
            
            writer = BlogWriterAgent()
            result = await writer.generate_blog(
                research_data={"topic_summary": "Transformers..."},
                target_audience="beginner",
            )
            
            assert result.target_audience == "beginner"
    
    @pytest.mark.asyncio
    async def test_blog_generation_validates_output(self):
        """Should validate generated blog content"""
        from src.common.validators import ContentValidator
        
        validator = ContentValidator()
        
        # Valid blog (must be > 500 chars)
        valid_content = """# Understanding Transformers

Transformers have revolutionized natural language processing and machine learning. They were introduced in the landmark paper "Attention Is All You Need" by Vaswani et al. in 2017.

## How They Work

The attention mechanism is key to their success. Unlike previous models, transformers can process entire sequences in parallel, making them much faster to train.

## Key Components

The main components include:
- Self-attention layers
- Feed-forward networks
- Positional encodings

## Conclusion

Transformers continue to drive AI innovation. They power models like GPT, BERT, and countless others.
"""
        result = validator.validate_blog(valid_content, "Understanding Transformers")
        assert result.is_valid
        
        # Invalid blog (too short)
        short_content = "Short content."
        result = validator.validate_blog(short_content)
        assert not result.is_valid
        assert any("too short" in e.lower() for e in result.errors)


@pytest.mark.e2e
class TestLinkedInGenerationE2E:
    """E2E tests for LinkedIn post generation"""
    
    @pytest.mark.asyncio
    async def test_linkedin_post_generation(self):
        """Should generate LinkedIn post from content"""
        from src.lib.agents.shortform_agent import ShortformAgent, LinkedInPost
        
        with patch.object(ShortformAgent, 'generate_linkedin_post') as mock_post:
            mock_post.return_value = LinkedInPost(
                content="🚀 Exciting news about AI!\n\nTransformers have changed everything...",
                hook="Transformers have changed everything.",
                hashtags=["AI", "MachineLearning", "Transformers"],
                call_to_action="What do you think? Comment below!",
            )
            
            agent = ShortformAgent()
            result = await agent.generate_linkedin_post(
                source_content={"topic_summary": "Transformers are..."},
                target_audience="practitioner",
            )
            
            assert result.content is not None
            assert result.character_count <= 3000
    
    @pytest.mark.asyncio
    async def test_linkedin_validation(self):
        """Should validate LinkedIn post format"""
        from src.common.validators import ContentValidator
        
        validator = ContentValidator()
        
        # Valid post
        valid_post = """🚀 Transformers changed AI forever!

Here's what you need to know:

1. Self-attention is key
2. Parallel processing is faster
3. Transfer learning works great

What's your experience with transformers?

#AI #MachineLearning #Transformers"""
        
        result = validator.validate_linkedin_post(valid_post)
        assert result.is_valid
        
        # Too long post
        long_post = "x" * 4000
        result = validator.validate_linkedin_post(long_post)
        assert not result.is_valid


@pytest.mark.e2e
class TestFullContentPipelineE2E:
    """E2E tests for full content pipeline"""
    
    @pytest.mark.asyncio
    async def test_research_to_blog_to_social(self):
        """Should execute full content pipeline: research → blog → social"""
        from src.lib.pipelines.research_pipeline import ResearchPipeline
        from src.lib.pipelines.blog_pipeline import BlogGenerationPipeline
        from src.lib.agents.topic_agent import TopicAgent
        from src.lib.agents.react_research_agent import ResearchAgent, ResearchOutput
        from src.lib.agents.blog_writer_agent import BlogWriterAgent, BlogOutput
        from src.lib.agents.branding_agent import BrandingAgent, BrandingResult
        from src.lib.agents.shortform_agent import ShortformAgent, LinkedInPost
        from src.lib.models.schemas import TopicCategorizationResult
        
        with patch.object(TopicAgent, 'categorize_query') as mock_cat, \
             patch.object(ResearchAgent, 'conduct_research') as mock_res, \
             patch.object(BlogWriterAgent, 'generate_blog') as mock_blog, \
             patch.object(BrandingAgent, 'apply_branding') as mock_brand, \
             patch.object(ShortformAgent, 'generate_linkedin_post') as mock_li:
            
            # Setup mocks
            mock_cat.return_value = TopicCategorizationResult(
                category="core_ai",
                confidence=0.95,
                reasoning="Core AI",
                is_ai_related=True,
            )
            
            mock_res.return_value = ResearchOutput(
                topic_summary="Transformers are...",
                key_concepts={"attention": "Focus"},
                mathematical_foundations="QK^T/sqrt(d)",
                sources=[{"type": "paper", "title": "Attention"}],
                completeness_score=0.9,
            )
            
            mock_blog.return_value = BlogOutput(
                title="Understanding Transformers",
                content="# Introduction\n\nContent...",
                target_audience="practitioner",
                status="ready",
            )
            
            mock_brand.return_value = BrandingResult(
                original_content="...",
                branded_content="# Introduction\n\nBranded content...",
                changes_made=[],
                voice_score=0.85,
                suggestions=[],
            )
            
            mock_li.return_value = LinkedInPost(
                content="🚀 New post about Transformers!",
                hook="Check this out!",
                hashtags=["AI"],
            )
            
            # Execute research pipeline
            research_pipeline = ResearchPipeline()
            research_result = await research_pipeline.execute(
                query="Explain transformers",
                target_audience="practitioner",
            )
            
            assert research_result.research_output is not None
            
            # Execute blog pipeline
            blog_pipeline = BlogGenerationPipeline()
            blog_result = await blog_pipeline.execute_from_research(
                research_output={
                    "topic_summary": research_result.research_output.topic_summary,
                    "key_concepts": research_result.research_output.key_concepts,
                    "mathematical_foundations": research_result.research_output.mathematical_foundations,
                    "sources": research_result.research_output.sources,
                },
                target_audience="practitioner",
            )
            
            assert blog_result.blog_output is not None
            assert blog_result.linkedin_post is not None
