"""
Unit tests for Topic Agent
Tests query categorization logic (core AI vs practical implementation)
Maps to: spec.md → Story 2, Acceptance Criteria
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.lib.agents.topic_agent import TopicAgent
from src.lib.models.research import TopicCategory
from src.lib.models.exceptions import QueryCategorizationError


@pytest.fixture
def mock_llm():
    """Mock LLM for topic agent testing"""
    llm = AsyncMock()
    return llm


@pytest.fixture
def topic_agent(mock_llm):
    """Topic agent instance with mocked LLM"""
    return TopicAgent(llm=mock_llm)


@pytest.mark.asyncio
class TestTopicAgentCategorization:
    """Test topic categorization functionality"""
    
    async def test_categorize_core_ai_topic(self, topic_agent, mock_llm):
        """Should categorize transformer-related query as core AI"""
        # Arrange
        query = "Explain the attention mechanism in transformers"
        mock_llm.ainvoke.return_value = {
            "category": "core_ai",
            "confidence": 0.95,
            "reasoning": "Query is about transformer architecture, a core AI concept",
            "is_ai_related": True,
        }
        
        # Act
        result = await topic_agent.categorize_query(query)
        
        # Assert
        assert result.category == "core_ai"
        assert result.confidence > 0.8
        mock_llm.ainvoke.assert_called_once()
    
    async def test_categorize_practical_implementation_topic(self, topic_agent, mock_llm):
        """Should categorize framework-related query as practical implementation"""
        # Arrange
        query = "How to use LangChain for building RAG applications?"
        mock_llm.ainvoke.return_value = {
            "category": "practical_implementation",
            "confidence": 0.92,
            "reasoning": "Query is about using a framework/tool",
            "is_ai_related": True,
        }
        
        # Act
        result = await topic_agent.categorize_query(query)
        
        # Assert
        assert result.category == "practical_implementation"
        assert result.confidence > 0.8
    
    async def test_categorize_research_paper_query(self, topic_agent, mock_llm):
        """Should categorize research paper query as core AI"""
        # Arrange
        query = "What are the latest developments in neural architecture search?"
        mock_llm.ainvoke.return_value = {
            "category": "core_ai",
            "confidence": 0.88,
            "reasoning": "Query is about research and core AI concepts",
            "is_ai_related": True,
        }
        
        # Act
        result = await topic_agent.categorize_query(query)
        
        # Assert
        assert result.category == "core_ai"
    
    async def test_categorize_tool_query(self, topic_agent, mock_llm):
        """Should categorize tool/framework query as practical implementation"""
        # Arrange
        query = "Step-by-step guide to implement RAG with Pinecone and OpenAI"
        mock_llm.ainvoke.return_value = {
            "category": "practical_implementation",
            "confidence": 0.90,
            "reasoning": "Query is about implementation using tools",
            "is_ai_related": True,
        }
        
        # Act
        result = await topic_agent.categorize_query(query)
        
        # Assert
        assert result.category == "practical_implementation"
    
    async def test_categorize_ambiguous_query(self, topic_agent, mock_llm):
        """Should handle ambiguous queries and default appropriately"""
        # Arrange
        query = "AI"
        mock_llm.ainvoke.return_value = {
            "category": "practical_implementation",
            "confidence": 0.5,
            "reasoning": "Query is too broad, defaulting to practical",
            "is_ai_related": True,
        }
        
        # Act
        result = await topic_agent.categorize_query(query)
        
        # Assert
        assert result.category == "practical_implementation"
        assert result.confidence < 0.7
    
    async def test_categorize_with_llm_error(self, topic_agent, mock_llm):
        """Should handle LLM API errors gracefully"""
        # Arrange
        query = "What are transformers?"
        mock_llm.ainvoke.side_effect = Exception("LLM API error")
        
        # Act & Assert
        with pytest.raises(QueryCategorizationError) as exc:
            await topic_agent.categorize_query(query)
        assert "failed to categorize" in str(exc.value).lower()
    
    async def test_categorize_with_invalid_response(self, topic_agent, mock_llm):
        """Should handle invalid LLM response format"""
        # Arrange
        query = "What are transformers?"
        mock_llm.ainvoke.return_value = {"invalid": "response"}
        
        # Act & Assert
        with pytest.raises(QueryCategorizationError) as exc:
            await topic_agent.categorize_query(query)
        assert "missing category" in str(exc.value).lower()


@pytest.mark.asyncio
class TestTopicAgentEdgeCases:
    """Test edge cases and error scenarios"""
    
    async def test_empty_query(self, topic_agent):
        """Should raise error for empty query"""
        # Act & Assert
        with pytest.raises(QueryCategorizationError) as exc:
            await topic_agent.categorize_query("")
        assert "empty" in str(exc.value).lower()
    
    async def test_whitespace_only_query(self, topic_agent):
        """Should raise error for whitespace-only query"""
        # Act & Assert
        with pytest.raises(QueryCategorizationError) as exc:
            await topic_agent.categorize_query("   ")
        assert "empty" in str(exc.value).lower()
    
    async def test_very_long_query(self, topic_agent, mock_llm):
        """Should handle very long queries"""
        # Arrange
        query = "What are transformers? " * 100
        mock_llm.ainvoke.return_value = {
            "category": "core_ai",
            "confidence": 0.85,
            "is_ai_related": True,
        }
        
        # Act
        result = await topic_agent.categorize_query(query)
        
        # Assert
        assert result.category in ["core_ai", "practical_implementation"]
    
    async def test_non_ai_query_detection(self, topic_agent, mock_llm):
        """Should detect non-AI topics"""
        # Arrange
        query = "How to cook pasta?"
        mock_llm.ainvoke.return_value = {
            "category": None,
            "is_ai_related": False,
            "reasoning": "Query is not related to AI",
        }
        
        # Act & Assert
        with pytest.raises(QueryCategorizationError) as exc:
            await topic_agent.categorize_query(query)
        assert "not ai related" in str(exc.value).lower()


class TestTopicAgentKeywordCategorization:
    """Test keyword-based categorization fallback"""
    
    def test_keyword_core_ai(self, topic_agent):
        """Should categorize core AI keywords correctly"""
        query = "Explain the transformer attention mechanism and self-attention"
        result = topic_agent.categorize_by_keywords(query)
        assert result == TopicCategory.CORE_AI
    
    def test_keyword_practical(self, topic_agent):
        """Should categorize practical keywords correctly"""
        query = "How to build a RAG application with LangChain step by step"
        result = topic_agent.categorize_by_keywords(query)
        assert result == TopicCategory.PRACTICAL_IMPLEMENTATION
    
    def test_keyword_ambiguous(self, topic_agent):
        """Should default to practical for ambiguous queries"""
        query = "AI systems"
        result = topic_agent.categorize_by_keywords(query)
        assert result == TopicCategory.PRACTICAL_IMPLEMENTATION
