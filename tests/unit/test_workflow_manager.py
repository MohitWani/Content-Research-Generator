"""
Unit tests for Workflow Manager
Tests workflow orchestration logic with mocked agents and database
Maps to: spec.md → FR6 (Multi-Agent Orchestration)
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from dataclasses import dataclass

from src.lib.orchestrator.workflow_manager import (
    WorkflowManager,
    ResearchWorkflowResult,
    BlogWorkflowResult,
)
from src.lib.models.research import TopicCategory
from src.lib.models.exceptions import (
    QueryCategorizationError,
    ResearchDataInsufficientError,
)


@pytest.fixture
def mock_topic_agent():
    """Mock topic agent"""
    agent = AsyncMock()
    return agent


@pytest.fixture
def mock_research_agent():
    """Mock research agent"""
    agent = AsyncMock()
    return agent


@pytest.fixture
def mock_blog_writer_agent():
    """Mock blog writer agent"""
    agent = AsyncMock()
    return agent


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.scalar = AsyncMock(return_value=None)
    return session


@pytest.fixture
def workflow_manager(mock_topic_agent, mock_research_agent, mock_blog_writer_agent, mock_db_session):
    """Workflow manager with all mocked dependencies"""
    return WorkflowManager(
        topic_agent=mock_topic_agent,
        research_agent=mock_research_agent,
        blog_writer_agent=mock_blog_writer_agent,
        db_session=mock_db_session,
    )


@pytest.mark.asyncio
class TestResearchWorkflowExecution:
    """Test research workflow execution"""
    
    async def test_execute_research_workflow_core_ai(
        self,
        workflow_manager,
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should execute research workflow for core AI topic"""
        from src.lib.agents.react_research_agent import ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        query = "Explain transformers"
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.95,
            reasoning="Core AI",
            is_ai_related=True,
        )
        mock_research_agent.conduct_research.return_value = ResearchOutput(
            topic_summary="Transformers are...",
            key_concepts={"attention": "Focus"},
            mathematical_foundations="Q·K^T/√d",
            sources=[],
            completeness_score=0.85,
        )
        
        # Act
        result = await workflow_manager.execute_research_workflow(query, "practitioner")
        
        # Assert
        assert result.topic_category == TopicCategory.CORE_AI
        assert result.research_result is not None
        assert result.research_result.mathematical_foundations is not None
        mock_topic_agent.categorize_query.assert_called_once_with(query)
        mock_research_agent.conduct_research.assert_called_once()
    
    async def test_execute_research_workflow_practical(
        self,
        workflow_manager,
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should execute research workflow for practical topic"""
        from src.lib.agents.react_research_agent import ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        query = "How to use LangChain?"
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="practical_implementation",
            confidence=0.92,
            reasoning="Tool usage",
            is_ai_related=True,
        )
        mock_research_agent.conduct_research.return_value = ResearchOutput(
            topic_summary="LangChain is...",
            key_concepts={},
            implementation_examples="Step 1: Install...",
            sources=[],
            completeness_score=0.80,
        )
        
        # Act
        result = await workflow_manager.execute_research_workflow(query, "practitioner")
        
        # Assert
        assert result.topic_category == TopicCategory.PRACTICAL_IMPLEMENTATION
        assert result.research_result.implementation_examples is not None
    
    async def test_research_workflow_rejects_non_ai(
        self,
        workflow_manager,
        mock_topic_agent,
    ):
        """Should reject non-AI queries"""
        # Arrange
        query = "How to cook pasta?"
        mock_topic_agent.categorize_query.side_effect = QueryCategorizationError(
            "Query is not AI related"
        )
        
        # Act & Assert
        with pytest.raises(QueryCategorizationError) as exc:
            await workflow_manager.execute_research_workflow(query, "beginner")
        assert "not ai related" in str(exc.value).lower()
    
    async def test_research_workflow_calls_agents_in_order(
        self,
        workflow_manager,
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should call agents in correct order: topic → research"""
        from src.lib.agents.react_research_agent import ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        call_order = []
        
        async def track_topic(*args, **kwargs):
            call_order.append("topic")
            return TopicCategorizationResult(
                category="core_ai",
                confidence=0.9,
                is_ai_related=True,
            )
        
        async def track_research(*args, **kwargs):
            call_order.append("research")
            return ResearchOutput(
                topic_summary="...",
                key_concepts={},
                sources=[],
                completeness_score=0.7,
            )
        
        mock_topic_agent.categorize_query.side_effect = track_topic
        mock_research_agent.conduct_research.side_effect = track_research
        
        # Act
        await workflow_manager.execute_research_workflow("query", "practitioner")
        
        # Assert
        assert call_order == ["topic", "research"]


@pytest.mark.asyncio
class TestBlogGenerationWorkflowExecution:
    """Test blog generation workflow execution"""
    
    async def test_execute_blog_workflow(
        self,
        workflow_manager,
        mock_blog_writer_agent,
        mock_db_session,
    ):
        """Should execute blog generation from research data"""
        from src.lib.agents.blog_writer_agent import BlogOutput
        from src.lib.models.research import ResearchResult
        
        # Arrange - mock research result in database
        mock_research_result = Mock(spec=ResearchResult)
        mock_research_result.topic_summary = "Transformers are..."
        mock_research_result.key_concepts = {"attention": "Focus"}
        mock_research_result.mathematical_foundations = None
        mock_research_result.historical_context = None
        mock_research_result.implementation_examples = None
        mock_research_result.sources = []
        
        mock_db_session.scalar.return_value = mock_research_result
        
        mock_blog_writer_agent.generate_blog.return_value = BlogOutput(
            title="Understanding Transformers",
            content="# Introduction\n\nContent here...",
            target_audience="practitioner",
            status="ready",
        )
        
        # Act
        result = await workflow_manager.execute_blog_generation_workflow(1, "practitioner")
        
        # Assert
        assert result.title == "Understanding Transformers"
        assert result.content is not None
        assert result.status == "ready"
        mock_blog_writer_agent.generate_blog.assert_called_once()
    
    async def test_blog_workflow_fails_without_research(
        self,
        workflow_manager,
        mock_db_session,
    ):
        """Should fail if research data doesn't exist"""
        # Arrange - no research result
        mock_db_session.scalar.return_value = None
        
        # Act & Assert
        with pytest.raises(ResearchDataInsufficientError):
            await workflow_manager.execute_blog_generation_workflow(999, "practitioner")
    
    async def test_blog_workflow_passes_audience(
        self,
        workflow_manager,
        mock_blog_writer_agent,
        mock_db_session,
    ):
        """Should pass target audience to blog writer"""
        from src.lib.agents.blog_writer_agent import BlogOutput
        from src.lib.models.research import ResearchResult
        
        # Arrange
        mock_research_result = Mock(spec=ResearchResult)
        mock_research_result.topic_summary = "Summary"
        mock_research_result.key_concepts = {}
        mock_research_result.mathematical_foundations = None
        mock_research_result.historical_context = None
        mock_research_result.implementation_examples = None
        mock_research_result.sources = []
        
        mock_db_session.scalar.return_value = mock_research_result
        
        mock_blog_writer_agent.generate_blog.return_value = BlogOutput(
            title="Title",
            content="Content",
            target_audience="beginner",
            status="ready",
        )
        
        # Act
        await workflow_manager.execute_blog_generation_workflow(1, "beginner", "conversational")
        
        # Assert
        call_kwargs = mock_blog_writer_agent.generate_blog.call_args.kwargs
        assert call_kwargs["target_audience"] == "beginner"
        assert call_kwargs["tone"] == "conversational"


@pytest.mark.asyncio
class TestFullWorkflowExecution:
    """Test full workflow execution"""
    
    async def test_execute_full_workflow(
        self,
        workflow_manager,
        mock_topic_agent,
        mock_research_agent,
        mock_blog_writer_agent,
        mock_db_session,
    ):
        """Should execute complete workflow: query → research → blog"""
        from src.lib.agents.react_research_agent import ResearchOutput
        from src.lib.agents.blog_writer_agent import BlogOutput
        from src.lib.models.schemas import TopicCategorizationResult
        from src.lib.models.research import ResearchResult
        
        # Arrange
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.9,
            is_ai_related=True,
        )
        mock_research_agent.conduct_research.return_value = ResearchOutput(
            topic_summary="Transformers...",
            key_concepts={},
            sources=[],
            completeness_score=0.8,
        )
        
        # Mock research result for blog generation
        mock_research_result = Mock(spec=ResearchResult)
        mock_research_result.topic_summary = "Transformers..."
        mock_research_result.key_concepts = {}
        mock_research_result.mathematical_foundations = None
        mock_research_result.historical_context = None
        mock_research_result.implementation_examples = None
        mock_research_result.sources = []
        mock_db_session.scalar.return_value = mock_research_result
        
        mock_blog_writer_agent.generate_blog.return_value = BlogOutput(
            title="Blog Title",
            content="Blog content...",
            target_audience="practitioner",
            status="ready",
        )
        
        # Act
        research_result, blog_result = await workflow_manager.execute_full_workflow(
            "Explain transformers",
            "practitioner",
        )
        
        # Assert
        assert research_result.research_result is not None
        assert blog_result.title is not None
        assert blog_result.content is not None


@pytest.mark.asyncio
class TestWorkflowErrorHandling:
    """Test workflow error handling"""
    
    async def test_handles_topic_agent_error(
        self,
        workflow_manager,
        mock_topic_agent,
    ):
        """Should propagate topic agent errors"""
        # Arrange
        mock_topic_agent.categorize_query.side_effect = Exception("Topic agent failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc:
            await workflow_manager.execute_research_workflow("query", "practitioner")
        assert "topic agent failed" in str(exc.value).lower()
    
    async def test_handles_research_agent_error(
        self,
        workflow_manager,
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should propagate research agent errors"""
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.9,
            is_ai_related=True,
        )
        mock_research_agent.conduct_research.side_effect = Exception("Research failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc:
            await workflow_manager.execute_research_workflow("query", "practitioner")
        assert "research failed" in str(exc.value).lower()
    
    async def test_handles_blog_writer_error(
        self,
        workflow_manager,
        mock_blog_writer_agent,
        mock_db_session,
    ):
        """Should propagate blog writer errors"""
        from src.lib.models.research import ResearchResult
        
        # Arrange
        mock_research_result = Mock(spec=ResearchResult)
        mock_research_result.topic_summary = "Summary"
        mock_research_result.key_concepts = {}
        mock_research_result.mathematical_foundations = None
        mock_research_result.historical_context = None
        mock_research_result.implementation_examples = None
        mock_research_result.sources = []
        mock_db_session.scalar.return_value = mock_research_result
        
        mock_blog_writer_agent.generate_blog.side_effect = Exception("Blog generation failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc:
            await workflow_manager.execute_blog_generation_workflow(1, "practitioner")
        assert "blog generation failed" in str(exc.value).lower()

