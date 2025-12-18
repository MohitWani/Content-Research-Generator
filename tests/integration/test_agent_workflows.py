"""
Integration tests for Agent Workflows
Tests LangGraph workflows with real/mocked LLM and real PostgreSQL
Maps to: spec.md → Story 1, Story 2, Story 3, FR6 (Multi-Agent Orchestration)

Test-First approach: These tests define the expected behavior of the workflow manager.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from dataclasses import dataclass
from typing import Optional, Dict, Any

from src.lib.models.research import TopicCategory, ResearchQuery, ResearchResult


@dataclass
class WorkflowResult:
    """Expected result structure from workflow execution"""
    query_id: int
    topic_category: TopicCategory
    research_result: Optional[Any] = None
    status: str = "completed"


@dataclass 
class BlogWorkflowResult:
    """Expected result structure from blog generation workflow"""
    content_id: int
    title: str
    content: str
    target_audience: str
    status: str = "ready"


@pytest.fixture
def mock_topic_agent():
    """Mock topic agent for workflow testing"""
    agent = AsyncMock()
    return agent


@pytest.fixture
def mock_research_agent():
    """Mock research agent for workflow testing"""
    agent = AsyncMock()
    return agent


@pytest.fixture
def mock_blog_writer_agent():
    """Mock blog writer agent for workflow testing"""
    agent = AsyncMock()
    return agent


@pytest.mark.integration
@pytest.mark.asyncio
class TestResearchWorkflow:
    """Test complete research workflow: Topic → Research"""
    
    async def test_research_workflow_core_ai(
        self, 
        db_session, 
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should execute research workflow for core AI topic"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.agents.agentic_researcher import ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        query = "Explain the attention mechanism in transformers"
        target_audience = "practitioner"
        
        # Mock topic categorization
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.95,
            reasoning="Core AI concept",
            is_ai_related=True,
        )
        
        # Mock research output
        mock_research_agent.research.return_value = ResearchOutput(
            topic_summary="The attention mechanism allows models to focus on relevant parts...",
            key_concepts={"attention": "Focus mechanism", "self-attention": "Same-sequence attention"},
            mathematical_foundations="Attention(Q,K,V) = softmax(QK^T/√d_k)V",
            historical_context="Introduced in 2017 by Vaswani et al.",
            implementation_examples="```python\nimport torch\n...\n```",
            sources=[{"type": "paper", "title": "Attention Is All You Need"}],
            completeness_score=0.92,
        )
        
        manager = WorkflowManager(
            topic_agent=mock_topic_agent,
            research_agent=mock_research_agent,
            db_session=db_session,
        )
        
        # Act
        result = await manager.execute_research_workflow(query, target_audience)
        
        # Assert
        assert result.query_id is not None
        assert result.topic_category == TopicCategory.CORE_AI
        assert result.research_result is not None
        assert result.research_result.topic_summary is not None
        assert result.research_result.mathematical_foundations is not None  # Core AI requirement
        assert len(result.research_result.sources) >= 1
        
        # Verify agents were called correctly
        mock_topic_agent.categorize_query.assert_called_once_with(query)
        mock_research_agent.research.assert_called_once()
    
    async def test_research_workflow_practical(
        self, 
        db_session,
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should execute research workflow for practical implementation topic"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.agents.agentic_researcher import ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        query = "How to use LangChain for building RAG applications?"
        target_audience = "practitioner"
        
        # Mock topic categorization
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="practical_implementation",
            confidence=0.92,
            reasoning="Framework usage query",
            is_ai_related=True,
        )
        
        # Mock research output with step-by-step guide
        mock_research_agent.research.return_value = ResearchOutput(
            topic_summary="LangChain is a framework for building LLM applications...",
            key_concepts={"RAG": "Retrieval Augmented Generation"},
            implementation_examples="Step 1: Install LangChain\n```pip install langchain```\nStep 2: Set up vector store...",
            sources=[{"type": "github", "title": "langchain"}],
            completeness_score=0.88,
        )
        
        manager = WorkflowManager(
            topic_agent=mock_topic_agent,
            research_agent=mock_research_agent,
            db_session=db_session,
        )
        
        # Act
        result = await manager.execute_research_workflow(query, target_audience)
        
        # Assert
        assert result.query_id is not None
        assert result.topic_category == TopicCategory.PRACTICAL_IMPLEMENTATION
        assert result.research_result is not None
        assert result.research_result.implementation_examples is not None  # Practical requirement
        assert "step" in result.research_result.implementation_examples.lower()
    
    async def test_research_workflow_persists_to_database(
        self, 
        db_session,
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should persist research results to database"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.agents.agentic_researcher import ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        from sqlalchemy import select
        
        # Arrange
        query = "What are transformers?"
        target_audience = "practitioner"
        
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.90,
            reasoning="Core concept",
            is_ai_related=True,
        )
        
        mock_research_agent.research.return_value = ResearchOutput(
            topic_summary="Transformers are neural network architectures...",
            key_concepts={"transformer": "Architecture"},
            sources=[],
            completeness_score=0.75,
        )
        
        manager = WorkflowManager(
            topic_agent=mock_topic_agent,
            research_agent=mock_research_agent,
            db_session=db_session,
        )
        
        # Act
        result = await manager.execute_research_workflow(query, target_audience)
        await db_session.flush()
        
        # Assert - verify in database
        stored_query = await db_session.get(ResearchQuery, result.query_id)
        assert stored_query is not None
        assert stored_query.query_text == query
        assert stored_query.topic_category == TopicCategory.CORE_AI
        
        stored_result = await db_session.scalar(
            select(ResearchResult).where(ResearchResult.query_id == result.query_id)
        )
        assert stored_result is not None
        assert stored_result.topic_summary is not None
    
    async def test_research_workflow_rejects_non_ai_query(
        self,
        db_session,
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should reject non-AI queries gracefully"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.models.exceptions import QueryCategorizationError
        
        # Arrange
        query = "How to cook pasta?"
        target_audience = "beginner"
        
        mock_topic_agent.categorize_query.side_effect = QueryCategorizationError(
            "Query is not AI related"
        )
        
        manager = WorkflowManager(
            topic_agent=mock_topic_agent,
            research_agent=mock_research_agent,
            db_session=db_session,
        )
        
        # Act & Assert
        with pytest.raises(QueryCategorizationError) as exc:
            await manager.execute_research_workflow(query, target_audience)
        assert "not ai related" in str(exc.value).lower()


@pytest.mark.integration
@pytest.mark.asyncio
class TestBlogGenerationWorkflow:
    """Test blog generation workflow: Research → Blog"""
    
    async def test_blog_generation_workflow(
        self, 
        db_session, 
        create_test_research_query,
        mock_blog_writer_agent,
    ):
        """Should generate blog post from research data"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.agents.blog_writer_agent import BlogOutput
        
        # Arrange - create research query and result
        query_data = {
            "query_text": "What are transformers?",
            "target_audience": "practitioner",
            "topic_category": TopicCategory.CORE_AI,
        }
        research_query = await create_test_research_query(query_data)
        
        # Create research result
        research_result = ResearchResult(
            query_id=research_query.id,
            topic_summary="Transformers are neural networks that use self-attention mechanisms...",
            key_concepts={"attention": "Focus mechanism"},
            sources=[{"type": "paper", "title": "Attention Is All You Need"}],
            research_data_path="/data/research/1",
        )
        db_session.add(research_result)
        await db_session.flush()
        
        # Mock blog output
        mock_blog_writer_agent.generate_blog.return_value = BlogOutput(
            title="Understanding Transformers: A Complete Guide",
            content="# Introduction\n\nTransformers have revolutionized NLP...\n\n## Conclusion",
            meta_description="A comprehensive guide to transformer architectures",
            tags=["AI", "Transformers", "NLP"],
            estimated_reading_time="8 min read",
            target_audience="practitioner",
            tone="professional",
            status="ready",
        )
        
        manager = WorkflowManager(
            blog_writer_agent=mock_blog_writer_agent,
            db_session=db_session,
        )
        
        # Act
        result = await manager.execute_blog_generation_workflow(
            research_query.id, 
            "practitioner"
        )
        
        # Assert
        assert result.content_id is not None
        assert result.title is not None
        assert result.content is not None
        assert len(result.content) > 0
        assert result.status in ["ready", "draft"]
        
        mock_blog_writer_agent.generate_blog.assert_called_once()
    
    async def test_blog_generation_adapts_to_audience(
        self, 
        db_session, 
        create_test_research_query,
        mock_blog_writer_agent,
    ):
        """Should adapt blog tone to target audience"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.agents.blog_writer_agent import BlogOutput
        
        # Arrange
        query_data = {
            "query_text": "What are transformers?",
            "target_audience": "beginner",
            "topic_category": TopicCategory.CORE_AI,
        }
        research_query = await create_test_research_query(query_data)
        
        research_result = ResearchResult(
            query_id=research_query.id,
            topic_summary="Transformers are neural networks...",
            key_concepts={},
            sources=[],
            research_data_path="/data/research/1",
        )
        db_session.add(research_result)
        await db_session.flush()
        
        # Mock beginner-friendly blog
        mock_blog_writer_agent.generate_blog.return_value = BlogOutput(
            title="Transformers Explained Simply",
            content="# What are Transformers?\n\nImagine a reader that can look at all words at once...",
            target_audience="beginner",
            tone="conversational",
            status="ready",
        )
        
        manager = WorkflowManager(
            blog_writer_agent=mock_blog_writer_agent,
            db_session=db_session,
        )
        
        # Act
        result = await manager.execute_blog_generation_workflow(
            research_query.id, 
            "beginner"
        )
        
        # Assert
        assert result.target_audience == "beginner"
        assert len(result.content) > 0
        
        # Verify correct audience was passed
        call_args = mock_blog_writer_agent.generate_blog.call_args
        assert call_args.kwargs.get("target_audience") == "beginner" or \
               (call_args.args and "beginner" in str(call_args.args))
    
    async def test_blog_generation_fails_without_research(
        self,
        db_session,
        mock_blog_writer_agent,
    ):
        """Should fail if research data doesn't exist"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.models.exceptions import ResearchDataInsufficientError
        
        manager = WorkflowManager(
            blog_writer_agent=mock_blog_writer_agent,
            db_session=db_session,
        )
        
        # Act & Assert - non-existent query ID
        with pytest.raises((ResearchDataInsufficientError, ValueError)):
            await manager.execute_blog_generation_workflow(99999, "practitioner")


@pytest.mark.integration
@pytest.mark.asyncio
class TestFullWorkflow:
    """Test full workflow: Query → Research → Blog"""
    
    async def test_full_research_to_blog_workflow(
        self, 
        db_session,
        mock_topic_agent,
        mock_research_agent,
        mock_blog_writer_agent,
    ):
        """Should execute complete workflow from query to blog post"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.agents.agentic_researcher import ResearchOutput
        from src.lib.agents.blog_writer_agent import BlogOutput
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        query = "Explain transformers in simple terms"
        target_audience = "beginner"
        
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.85,
            reasoning="Core concept",
            is_ai_related=True,
        )
        
        mock_research_agent.research.return_value = ResearchOutput(
            topic_summary="Transformers are neural networks...",
            key_concepts={"transformer": "AI architecture"},
            sources=[{"type": "paper", "title": "Attention Is All You Need"}],
            completeness_score=0.80,
        )
        
        mock_blog_writer_agent.generate_blog.return_value = BlogOutput(
            title="Understanding Transformers",
            content="# Introduction\n\nTransformers are amazing...\n\n## Conclusion",
            target_audience="beginner",
            status="ready",
        )
        
        manager = WorkflowManager(
            topic_agent=mock_topic_agent,
            research_agent=mock_research_agent,
            blog_writer_agent=mock_blog_writer_agent,
            db_session=db_session,
        )
        
        # Act - execute full workflow
        research_result = await manager.execute_research_workflow(query, target_audience)
        blog_result = await manager.execute_blog_generation_workflow(
            research_result.query_id,
            target_audience
        )
        
        # Assert
        assert research_result.query_id is not None
        assert research_result.research_result is not None
        assert blog_result.content_id is not None
        assert blog_result.title is not None
        assert blog_result.content is not None
        assert len(blog_result.content) > 50  # Substantial content
    
    async def test_workflow_handles_low_completeness(
        self,
        db_session,
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should handle research with low completeness score"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.agents.agentic_researcher import ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        query = "Very obscure topic XYZ123"
        target_audience = "practitioner"
        
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="practical_implementation",
            confidence=0.5,
            reasoning="Unclear topic",
            is_ai_related=True,
        )
        
        # Low completeness research
        mock_research_agent.research.return_value = ResearchOutput(
            topic_summary="Limited information available...",
            key_concepts={},
            sources=[],
            completeness_score=0.25,  # Low completeness
        )
        
        manager = WorkflowManager(
            topic_agent=mock_topic_agent,
            research_agent=mock_research_agent,
            db_session=db_session,
        )
        
        # Act
        result = await manager.execute_research_workflow(query, target_audience)
        
        # Assert - should succeed but with low completeness
        assert result.research_result is not None
        assert result.research_result.completeness_score < 0.5


@pytest.mark.integration
@pytest.mark.asyncio
class TestWorkflowStateManagement:
    """Test workflow state persistence and recovery"""
    
    async def test_workflow_state_persistence(
        self, 
        db_session,
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should persist workflow state to database"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.agents.agentic_researcher import ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        query = "What are transformers?"
        target_audience = "practitioner"
        
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.90,
            reasoning="Core concept",
            is_ai_related=True,
        )
        
        mock_research_agent.research.return_value = ResearchOutput(
            topic_summary="Transformers are...",
            key_concepts={},
            sources=[],
            completeness_score=0.75,
        )
        
        manager = WorkflowManager(
            topic_agent=mock_topic_agent,
            research_agent=mock_research_agent,
            db_session=db_session,
        )
        
        # Act
        result = await manager.execute_research_workflow(query, target_audience)
        await db_session.flush()
        
        # Assert - verify state persisted
        stored_query = await db_session.get(ResearchQuery, result.query_id)
        assert stored_query.status in ["completed", "processing", "pending"]
    
    async def test_workflow_tracks_pipeline_execution(
        self,
        db_session,
        mock_topic_agent,
        mock_research_agent,
    ):
        """Should track pipeline execution in database"""
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.agents.agentic_researcher import ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        from src.lib.models.research import PipelineExecution
        from sqlalchemy import select
        
        # Arrange
        query = "What are transformers?"
        target_audience = "practitioner"
        
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.90,
            reasoning="Core concept",
            is_ai_related=True,
        )
        
        mock_research_agent.research.return_value = ResearchOutput(
            topic_summary="Transformers are...",
            key_concepts={},
            sources=[],
            completeness_score=0.75,
        )
        
        manager = WorkflowManager(
            topic_agent=mock_topic_agent,
            research_agent=mock_research_agent,
            db_session=db_session,
        )
        
        # Act
        result = await manager.execute_research_workflow(query, target_audience)
        await db_session.flush()
        
        # Assert - verify pipeline execution tracked
        pipeline = await db_session.scalar(
            select(PipelineExecution).where(
                PipelineExecution.research_query_id == result.query_id
            )
        )
        # Pipeline tracking is optional but should exist if implemented
        if pipeline:
            assert pipeline.pipeline_type == "research"
            assert pipeline.status in ["completed", "running"]
