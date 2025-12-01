"""
Unit tests for ReAct Research Agent
Tests LangGraph-based research with LangChain tools
Maps to: spec.md → Story 1, Story 8, Story 9, FR2
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime

from src.lib.agents.react_research_agent import (
    ReActResearchAgent,
    ResearchOutput,
    create_langchain_tools,
)
from src.lib.models.research import TopicCategory


@pytest.fixture
def mock_llm():
    """Mock LLM for research agent"""
    llm = MagicMock()
    llm.llm = MagicMock()
    llm.llm.bind_tools = MagicMock(return_value=AsyncMock())
    llm.llm.ainvoke = AsyncMock()
    return llm


class TestResearchOutput:
    """Tests for ResearchOutput dataclass"""
    
    def test_research_output_creation(self):
        """Test creating ResearchOutput with all fields"""
        output = ResearchOutput(
            topic_summary="Test summary of the topic",
            key_concepts={"concept1": "explanation1", "concept2": "explanation2"},
            mathematical_foundations="E = mc^2",
            historical_context="Developed in 1905",
            implementation_examples="import torch",
            sources=[{"type": "paper", "title": "Test Paper"}],
            research_data_path="/path/to/data.json",
            completeness_score=0.85,
        )
        
        assert output.topic_summary == "Test summary of the topic"
        assert len(output.key_concepts) == 2
        assert output.mathematical_foundations == "E = mc^2"
        assert output.completeness_score == 0.85
    
    def test_research_output_minimal(self):
        """Test creating ResearchOutput with minimal fields"""
        output = ResearchOutput(
            topic_summary="Minimal summary",
            key_concepts={},
        )
        
        assert output.topic_summary == "Minimal summary"
        assert output.key_concepts == {}
        assert output.mathematical_foundations is None
        assert output.sources == []
        assert output.completeness_score == 0.0


class TestReActResearchAgent:
    """Tests for ReActResearchAgent"""
    
    def test_agent_initialization(self, mock_llm):
        """Test agent initializes with LangChain tools"""
        with patch('src.lib.agents.react_research_agent.create_langchain_tools') as mock_tools:
            mock_tools.return_value = [MagicMock(name="tool1"), MagicMock(name="tool2")]
            
            agent = ReActResearchAgent(llm=mock_llm, max_iterations=5)
            
            assert agent.max_iterations == 5
            assert len(agent.tools) == 2
    
    def test_agent_default_iterations(self, mock_llm):
        """Test agent uses default max iterations"""
        with patch('src.lib.agents.react_research_agent.create_langchain_tools') as mock_tools:
            mock_tools.return_value = []
            
            agent = ReActResearchAgent(llm=mock_llm)
            
            assert agent.max_iterations == 10


class TestLangChainTools:
    """Tests for LangChain tool creation"""
    
    def test_tools_created_with_tavily_key(self):
        """Test tools are created when Tavily API key is set"""
        with patch('src.lib.agents.react_research_agent.config') as mock_config:
            mock_config.TAVILY_API_KEY = "test-key"
            mock_config.GITHUB_TOKEN = None
            
            # Mock the tool classes to avoid actual initialization
            with patch('src.lib.agents.react_research_agent.TavilySearchResults'):
                with patch('src.lib.agents.react_research_agent.ArxivAPIWrapper'):
                    with patch('src.lib.agents.react_research_agent.ArxivQueryRun'):
                        with patch('src.lib.agents.react_research_agent.WikipediaAPIWrapper'):
                            with patch('src.lib.agents.react_research_agent.WikipediaQueryRun'):
                                tools = create_langchain_tools()
                                
                                # Should have at least scrape_webpage, github_search, web_search
                                assert len(tools) >= 3
    
    def test_tools_created_without_tavily_key(self):
        """Test tools are created even without Tavily API key"""
        with patch('src.lib.agents.react_research_agent.config') as mock_config:
            mock_config.TAVILY_API_KEY = None
            mock_config.GITHUB_TOKEN = None
            
            with patch('src.lib.agents.react_research_agent.ArxivAPIWrapper'):
                with patch('src.lib.agents.react_research_agent.ArxivQueryRun'):
                    with patch('src.lib.agents.react_research_agent.WikipediaAPIWrapper'):
                        with patch('src.lib.agents.react_research_agent.WikipediaQueryRun'):
                            tools = create_langchain_tools()
                            
                            # Should still have other tools
                            assert len(tools) >= 3


class TestCompletenessScore:
    """Tests for completeness score calculation"""
    
    def test_high_completeness_core_ai(self, mock_llm):
        """Test high completeness score for complete core AI research"""
        with patch('src.lib.agents.react_research_agent.create_langchain_tools') as mock_tools:
            mock_tools.return_value = []
            
            agent = ReActResearchAgent(llm=mock_llm)
            
            research = ResearchOutput(
                topic_summary="A" * 200,  # Long summary
                key_concepts={"a": "1", "b": "2", "c": "3"},  # 3 concepts
                mathematical_foundations="x" * 100,  # Has math
                historical_context="y" * 100,  # Has history
                implementation_examples="z" * 100,  # Has examples
                sources=[{}, {}, {}, {}, {}],  # 5 sources
            )
            
            score = agent._calculate_completeness(research, TopicCategory.CORE_AI)
            
            assert score == 1.0
    
    def test_low_completeness(self, mock_llm):
        """Test low completeness score for minimal research"""
        with patch('src.lib.agents.react_research_agent.create_langchain_tools') as mock_tools:
            mock_tools.return_value = []
            
            agent = ReActResearchAgent(llm=mock_llm)
            
            research = ResearchOutput(
                topic_summary="Short",
                key_concepts={},
                sources=[],
            )
            
            score = agent._calculate_completeness(research, TopicCategory.CORE_AI)
            
            assert score < 0.5


class TestResearchOutputParsing:
    """Tests for parsing research output from agent state"""
    
    def test_parse_valid_json(self, mock_llm):
        """Test parsing valid JSON synthesis output"""
        with patch('src.lib.agents.react_research_agent.create_langchain_tools') as mock_tools:
            mock_tools.return_value = []
            
            agent = ReActResearchAgent(llm=mock_llm)
            
            # Create mock state with JSON content
            mock_msg = MagicMock()
            mock_msg.content = '{"topic_summary": "Test summary", "key_concepts": {"a": "1"}}'
            
            final_state = {
                "synthesize": {
                    "messages": [mock_msg],
                    "sources": [{"tool": "arxiv", "query": "test"}],
                }
            }
            
            output = agent._parse_final_output(
                final_state, 
                "test query", 
                TopicCategory.CORE_AI
            )
            
            assert output.topic_summary == "Test summary"
            assert "a" in output.key_concepts
            assert len(output.sources) == 1
    
    def test_parse_invalid_json_fallback(self, mock_llm):
        """Test fallback when JSON parsing fails"""
        with patch('src.lib.agents.react_research_agent.create_langchain_tools') as mock_tools:
            mock_tools.return_value = []
            
            agent = ReActResearchAgent(llm=mock_llm)
            
            # Create mock state with invalid JSON
            mock_msg = MagicMock()
            mock_msg.content = "This is not valid JSON but has some content"
            
            final_state = {
                "synthesize": {
                    "messages": [mock_msg],
                    "sources": [],
                }
            }
            
            output = agent._parse_final_output(
                final_state, 
                "test query", 
                TopicCategory.CORE_AI
            )
            
            # Should have fallback content
            assert "test query" in output.topic_summary or len(output.topic_summary) > 0
