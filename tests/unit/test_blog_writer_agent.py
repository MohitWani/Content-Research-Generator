"""
Unit tests for Blog Writer Agent
Tests blog post generation from research data
Maps to: spec.md → Story 3, Story 4, FR4
"""
import pytest
from unittest.mock import AsyncMock, Mock

from src.lib.agents.blog_writer_agent import BlogWriterAgent, BlogOutput
from src.lib.agents.agentic_researcher import ResearchOutput
from src.lib.models.exceptions import BlogGenerationError, ResearchDataInsufficientError


@pytest.fixture
def mock_llm():
    """Mock LLM for blog writer agent"""
    llm = AsyncMock()
    return llm


@pytest.fixture
def blog_writer_agent(mock_llm):
    """Blog writer agent with mocked LLM"""
    return BlogWriterAgent(llm=mock_llm)


@pytest.fixture
def sample_research_data():
    """Sample research data for blog generation"""
    return {
        "topic_summary": "Transformers are a revolutionary neural network architecture that uses self-attention mechanisms to process sequential data in parallel.",
        "key_concepts": {
            "attention": "Mechanism for focusing on relevant parts",
            "self-attention": "Attention applied to same sequence",
        },
        "mathematical_foundations": "The attention mechanism computes QK^T/√d_k",
        "historical_context": "Introduced in 2017 by Vaswani et al.",
        "implementation_examples": "```python\nimport torch\n...\n```",
        "sources": [
            {"type": "paper", "title": "Attention Is All You Need", "url": "https://arxiv.org/abs/1706.03762"},
        ],
    }


@pytest.mark.asyncio
class TestBlogWriterAgentGeneration:
    """Test blog post generation functionality"""
    
    async def test_generate_blog_from_research(self, blog_writer_agent, mock_llm, sample_research_data):
        """Should generate blog post from research data"""
        # Arrange
        target_audience = "practitioner"
        mock_llm.ainvoke.return_value = {
            "title": "Understanding Transformers: A Comprehensive Guide",
            "content": "# Introduction\n\nTransformers have revolutionized...\n\n## Conclusion\n\nKey takeaways...",
            "meta_description": "A guide to understanding transformers",
            "tags": ["AI", "Transformers"],
            "estimated_reading_time": "8 min read",
        }
        
        # Act
        result = await blog_writer_agent.generate_blog(sample_research_data, target_audience)
        
        # Assert
        assert result.title is not None
        assert result.content is not None
        assert len(result.content) > 0
        assert result.status == "ready"
        mock_llm.ainvoke.assert_called_once()
    
    async def test_generate_blog_includes_structure(self, blog_writer_agent, mock_llm, sample_research_data):
        """Should include proper structure: introduction, body, conclusion"""
        # Arrange
        target_audience = "practitioner"
        mock_llm.ainvoke.return_value = {
            "title": "Understanding Transformers",
            "content": "# Introduction\n\nWelcome to this guide.\n\n## Main Content\n\nDetails here.\n\n## Conclusion\n\nIn summary...",
        }
        
        # Act
        result = await blog_writer_agent.generate_blog(sample_research_data, target_audience)
        
        # Assert
        assert "Introduction" in result.content or "introduction" in result.content.lower()
        assert "Conclusion" in result.content or "conclusion" in result.content.lower()
    
    async def test_generate_blog_includes_citations(self, blog_writer_agent, mock_llm, sample_research_data):
        """Should include citations from research sources"""
        # Arrange
        target_audience = "practitioner"
        mock_llm.ainvoke.return_value = {
            "title": "Understanding Transformers",
            "content": "Transformers were introduced [1].\n\n## References\n\n[1] Attention Is All You Need",
        }
        
        # Act
        result = await blog_writer_agent.generate_blog(sample_research_data, target_audience)
        
        # Assert
        assert "Attention Is All You Need" in result.content or "[1]" in result.content
    
    async def test_generate_blog_includes_code_blocks(self, blog_writer_agent, mock_llm, sample_research_data):
        """Should include code blocks from implementation examples"""
        # Arrange
        target_audience = "practitioner"
        mock_llm.ainvoke.return_value = {
            "title": "Understanding Transformers",
            "content": "Here's how to implement:\n```python\nimport torch\nclass Transformer:\n    pass\n```",
        }
        
        # Act
        result = await blog_writer_agent.generate_blog(sample_research_data, target_audience)
        
        # Assert
        assert "```" in result.content


@pytest.mark.asyncio
class TestBlogWriterAgentAudienceAdaptation:
    """Test audience-specific tone and style adaptation"""
    
    async def test_generate_blog_for_beginner_audience(self, blog_writer_agent, mock_llm, sample_research_data):
        """Should adapt tone for beginner audience"""
        # Arrange
        target_audience = "beginner"
        mock_llm.ainvoke.return_value = {
            "title": "Transformers Explained Simply",
            "content": "Let's start with the basics. Think of transformers like a smart reader...",
        }
        
        # Act
        result = await blog_writer_agent.generate_blog(sample_research_data, target_audience)
        
        # Assert
        assert result.target_audience == "beginner"
    
    async def test_generate_blog_for_expert_audience(self, blog_writer_agent, mock_llm, sample_research_data):
        """Should adapt tone for expert audience"""
        # Arrange
        target_audience = "expert"
        mock_llm.ainvoke.return_value = {
            "title": "Deep Dive into Transformer Architecture",
            "content": "The attention mechanism's mathematical formulation involves...",
        }
        
        # Act
        result = await blog_writer_agent.generate_blog(sample_research_data, target_audience)
        
        # Assert
        assert result.target_audience == "expert"
    
    async def test_generate_blog_for_practitioner_audience(self, blog_writer_agent, mock_llm, sample_research_data):
        """Should adapt tone for practitioner audience"""
        # Arrange
        target_audience = "practitioner"
        mock_llm.ainvoke.return_value = {
            "title": "Building with Transformers: A Practical Guide",
            "content": "Here's how to implement transformers in your projects...",
        }
        
        # Act
        result = await blog_writer_agent.generate_blog(sample_research_data, target_audience)
        
        # Assert
        assert result.target_audience == "practitioner"


@pytest.mark.asyncio
class TestBlogWriterAgentFormatting:
    """Test Medium formatting compliance"""
    
    async def test_generate_blog_medium_formatting(self, blog_writer_agent, mock_llm, sample_research_data):
        """Should format content according to Medium standards"""
        # Arrange
        target_audience = "practitioner"
        mock_llm.ainvoke.return_value = {
            "title": "Understanding Transformers",
            "content": "# Title\n\nParagraph with proper formatting.\n\n## Section\n\nMore content.",
        }
        
        # Act
        result = await blog_writer_agent.generate_blog(sample_research_data, target_audience)
        
        # Assert
        assert "\n\n" in result.content  # Paragraph breaks
        assert "#" in result.content  # Headers
    
    async def test_generate_blog_no_placeholders(self, blog_writer_agent, mock_llm, sample_research_data):
        """Should not include placeholders in generated content"""
        # Arrange
        target_audience = "practitioner"
        mock_llm.ainvoke.return_value = {
            "title": "Understanding Transformers",
            "content": "Complete blog post content without any placeholder text.",
        }
        
        # Act
        result = await blog_writer_agent.generate_blog(sample_research_data, target_audience)
        
        # Assert
        assert "[PLACEHOLDER]" not in result.content
        assert "[TODO]" not in result.content


@pytest.mark.asyncio
class TestBlogWriterAgentErrorHandling:
    """Test error handling scenarios"""
    
    async def test_generate_blog_with_insufficient_research(self, blog_writer_agent, mock_llm):
        """Should raise error when research data is insufficient"""
        # Arrange
        insufficient_research = {
            "topic_summary": "Short",  # Too short
            "sources": [],
        }
        target_audience = "practitioner"
        
        # Act & Assert
        with pytest.raises(ResearchDataInsufficientError) as exc:
            await blog_writer_agent.generate_blog(insufficient_research, target_audience)
        assert "insufficient" in str(exc.value).lower()
    
    async def test_generate_blog_with_empty_research(self, blog_writer_agent, mock_llm):
        """Should raise error when research data is empty"""
        # Arrange
        empty_research = {}
        target_audience = "practitioner"
        
        # Act & Assert
        with pytest.raises(ResearchDataInsufficientError) as exc:
            await blog_writer_agent.generate_blog(empty_research, target_audience)
        assert "empty" in str(exc.value).lower()
    
    async def test_generate_blog_handles_llm_error(self, blog_writer_agent, mock_llm, sample_research_data):
        """Should handle LLM API errors"""
        # Arrange
        target_audience = "practitioner"
        mock_llm.ainvoke.side_effect = Exception("LLM API error")
        
        # Act & Assert
        with pytest.raises(BlogGenerationError) as exc:
            await blog_writer_agent.generate_blog(sample_research_data, target_audience)
        assert "failed to generate" in str(exc.value).lower()


class TestBlogWriterAgentResearchOutputConversion:
    """Test conversion of ResearchOutput to dict"""
    
    @pytest.fixture
    def sample_research_output(self):
        """Sample ResearchOutput object"""
        return ResearchOutput(
            topic_summary="Transformers are revolutionary neural networks...",
            key_concepts={"attention": "Focus mechanism"},
            mathematical_foundations="Q·K^T/√d_k",
            historical_context="Introduced in 2017",
            implementation_examples="```python\nimport torch\n```",
            sources=[{"type": "paper", "title": "Attention Is All You Need"}],
            completeness_score=0.85,
        )
    
    @pytest.mark.asyncio
    async def test_generate_from_research_output(
        self, blog_writer_agent, mock_llm, sample_research_output
    ):
        """Should accept ResearchOutput object directly"""
        # Arrange
        mock_llm.ainvoke.return_value = {
            "title": "Understanding Transformers",
            "content": "Blog content here...",
        }
        
        # Act
        result = await blog_writer_agent.generate_blog(sample_research_output, "practitioner")
        
        # Assert
        assert result.title == "Understanding Transformers"
        mock_llm.ainvoke.assert_called_once()
