"""
Unit tests for Router
Tests query routing based on topic categorization
Maps to: spec.md → Story 2, FR1
"""
import pytest
from unittest.mock import AsyncMock, Mock

from src.lib.orchestrator.router import (
    Router,
    RoutingDecision,
    WorkflowType,
    get_router,
)
from src.lib.models.research import TopicCategory
from src.lib.models.exceptions import QueryCategorizationError


@pytest.fixture
def mock_topic_agent():
    """Mock topic agent for router testing"""
    agent = AsyncMock()
    return agent


@pytest.fixture
def router(mock_topic_agent):
    """Router with mocked topic agent"""
    return Router(topic_agent=mock_topic_agent)


@pytest.mark.asyncio
class TestRouterRouting:
    """Test routing functionality"""
    
    async def test_route_core_ai_query(self, router, mock_topic_agent):
        """Should route core AI query to correct workflow"""
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        query = "Explain the attention mechanism in transformers"
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.95,
            reasoning="Core AI concept",
            is_ai_related=True,
        )
        
        # Act
        decision = await router.route(query)
        
        # Assert
        assert decision.workflow_type == WorkflowType.RESEARCH_CORE_AI
        assert decision.topic_category == TopicCategory.CORE_AI
        assert decision.confidence == 0.95
        mock_topic_agent.categorize_query.assert_called_once_with(query)
    
    async def test_route_practical_query(self, router, mock_topic_agent):
        """Should route practical query to correct workflow"""
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        query = "How to use LangChain for RAG?"
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="practical_implementation",
            confidence=0.92,
            reasoning="Framework usage",
            is_ai_related=True,
        )
        
        # Act
        decision = await router.route(query)
        
        # Assert
        assert decision.workflow_type == WorkflowType.RESEARCH_PRACTICAL
        assert decision.topic_category == TopicCategory.PRACTICAL_IMPLEMENTATION
        assert decision.confidence == 0.92
    
    async def test_route_includes_metadata(self, router, mock_topic_agent):
        """Should include metadata in routing decision"""
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        query = "What are transformers?"
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.85,
            reasoning="Core concept",
            is_ai_related=True,
        )
        
        # Act
        decision = await router.route(
            query,
            target_audience="expert",
            content_type="blog",
        )
        
        # Assert
        assert decision.metadata["target_audience"] == "expert"
        assert decision.metadata["content_type"] == "blog"
        assert decision.metadata["is_ai_related"] is True
    
    async def test_route_rejects_non_ai_query(self, router, mock_topic_agent):
        """Should reject non-AI queries"""
        # Arrange
        query = "How to cook pasta?"
        mock_topic_agent.categorize_query.side_effect = QueryCategorizationError(
            "Query is not AI related"
        )
        
        # Act & Assert
        with pytest.raises(QueryCategorizationError):
            await router.route(query)


@pytest.mark.asyncio
class TestRouterWorkflowExecution:
    """Test workflow registration and execution"""
    
    async def test_register_and_execute_workflow(self, router, mock_topic_agent):
        """Should register and execute workflow handler"""
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.90,
            reasoning="Core AI",
            is_ai_related=True,
        )
        
        # Mock workflow handler
        mock_handler = AsyncMock(return_value={"result": "success"})
        router.register_workflow(WorkflowType.RESEARCH_CORE_AI, mock_handler)
        
        # Act
        result = await router.route_and_execute("Explain transformers")
        
        # Assert
        assert result == {"result": "success"}
        mock_handler.assert_called_once()
    
    async def test_execute_raises_if_no_handler(self, router, mock_topic_agent):
        """Should raise if no handler registered for workflow type"""
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="core_ai",
            confidence=0.90,
            reasoning="Core AI",
            is_ai_related=True,
        )
        
        # Act & Assert (no handler registered)
        with pytest.raises(ValueError) as exc:
            await router.route_and_execute("Explain transformers")
        assert "no handler" in str(exc.value).lower()
    
    async def test_execute_passes_correct_arguments(self, router, mock_topic_agent):
        """Should pass correct arguments to workflow handler"""
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Arrange
        mock_topic_agent.categorize_query.return_value = TopicCategorizationResult(
            category="practical_implementation",
            confidence=0.88,
            reasoning="Practical",
            is_ai_related=True,
        )
        
        mock_handler = AsyncMock(return_value={})
        router.register_workflow(WorkflowType.RESEARCH_PRACTICAL, mock_handler)
        
        # Act
        await router.route_and_execute(
            "How to use LangChain?",
            target_audience="beginner",
            extra_param="value",
        )
        
        # Assert
        call_kwargs = mock_handler.call_args.kwargs
        assert call_kwargs["query"] == "How to use LangChain?"
        assert call_kwargs["target_audience"] == "beginner"
        assert call_kwargs["topic_category"] == TopicCategory.PRACTICAL_IMPLEMENTATION
        assert call_kwargs["extra_param"] == "value"


class TestRouterRequirements:
    """Test research requirements and guidelines"""
    
    def test_core_ai_requirements(self, router):
        """Should return correct requirements for core AI"""
        # Act
        requirements = router.get_research_requirements(TopicCategory.CORE_AI)
        
        # Assert
        assert "mathematical_foundations" in requirements["required_sections"]
        assert "historical_context" in requirements["required_sections"]
        assert requirements["min_sources"] >= 5
        assert requirements["include_formulas"] is True
        assert requirements["depth"] == "deep"
    
    def test_practical_requirements(self, router):
        """Should return correct requirements for practical topics"""
        # Act
        requirements = router.get_research_requirements(
            TopicCategory.PRACTICAL_IMPLEMENTATION
        )
        
        # Assert
        assert "implementation_examples" in requirements["required_sections"]
        assert requirements["min_sources"] >= 3
        assert requirements["include_formulas"] is False
        assert requirements["depth"] == "practical"
    
    def test_beginner_guidelines(self, router):
        """Should return beginner-friendly guidelines"""
        # Act
        guidelines = router.get_content_guidelines(
            "beginner",
            TopicCategory.CORE_AI,
        )
        
        # Assert
        assert guidelines["complexity"] == "low"
        assert guidelines["jargon"] == "minimal"
        assert guidelines["analogies"] == "many"
    
    def test_expert_guidelines(self, router):
        """Should return expert-level guidelines"""
        # Act
        guidelines = router.get_content_guidelines(
            "expert",
            TopicCategory.CORE_AI,
        )
        
        # Assert
        assert guidelines["complexity"] == "high"
        assert guidelines["jargon"] == "full"
        assert guidelines["include_math"] is True
    
    def test_practical_guidelines_focus(self, router):
        """Should set hands-on focus for practical topics"""
        # Act
        guidelines = router.get_content_guidelines(
            "practitioner",
            TopicCategory.PRACTICAL_IMPLEMENTATION,
        )
        
        # Assert
        assert guidelines["focus"] == "hands-on"
        assert guidelines["include_math"] is False


class TestRouterFactory:
    """Test router factory function"""
    
    def test_get_router_creates_instance(self):
        """Should create router instance"""
        router = get_router()
        assert isinstance(router, Router)
    
    def test_get_router_with_custom_agent(self, mock_topic_agent):
        """Should create router with custom topic agent"""
        router = get_router(topic_agent=mock_topic_agent)
        assert router.topic_agent == mock_topic_agent

