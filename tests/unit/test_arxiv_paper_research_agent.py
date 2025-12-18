"""
Unit tests for ArXiv Paper Research Agent
Tests paper research logic, output parsing, and completeness scoring
Maps to: spec.md → Story 1, 4, 5, FR3, FR4 | plan.md → T008, T009
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

# Import directly to avoid circular imports
from importlib import import_module
_agent_module = import_module('src.lib.agents.arxiv_paper_research_agent')
ArXivPaperResearchAgent = _agent_module.ArXivPaperResearchAgent
PaperResearchOutput = _agent_module.PaperResearchOutput
PaperMetadata = _agent_module.PaperMetadata

from src.lib.models.exceptions import (
    PaperNotFoundError,
    PaperContentInsufficientError,
    MultiplePapersLimitError,
    InvalidArXivIdError,
)


# ============= Fixtures =============

@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock()
    return llm


@pytest.fixture
def mock_arxiv_client():
    """Mock ArXiv client for testing"""
    client = AsyncMock()
    return client


@pytest.fixture
def sample_paper_metadata():
    """Sample paper metadata for testing (ArXiv API format)"""
    return {
        "arxiv_id": "2508.07407",
        "title": "A Comprehensive Survey of Self-Evolving AI Agents",
        "authors": ["Jinyuan Fang", "Yanwen Peng", "Xi Zhang"],
        "summary": "Recent advances in large language models have sparked growing interest in AI agents capable of solving complex, real-world tasks. This survey provides a comprehensive review of self-evolving agentic systems.",
        "published": "2025-08-31",
        "updated": "2025-09-15",
        "categories": ["cs.AI", "cs.LG"],
        "pdf_url": "https://arxiv.org/pdf/2508.07407.pdf",
        "abs_url": "https://arxiv.org/abs/2508.07407",
    }


@pytest.fixture
def paper_metadata_dataclass(sample_paper_metadata):
    """Sample paper metadata as dataclass"""
    return PaperMetadata.from_arxiv_response(sample_paper_metadata)


@pytest.fixture
def sample_research_output():
    """Sample research output JSON from LLM"""
    return {
        "paper_overview": "This paper presents a comprehensive survey of self-evolving AI agents...",
        "methodology_deep_dive": "The paper introduces a unified conceptual framework with four key components: System Inputs, Agent System, Environment, and Optimizers...",
        "experimental_results": "The survey analyzes multiple benchmarks and evaluation metrics...",
        "practical_implications": "Self-evolving agents have significant applications in robotics, autonomous systems, and adaptive AI...",
        "limitations_future_work": "Current limitations include scalability challenges and the need for better evaluation frameworks...",
        "related_work_summary": "The paper builds upon prior work in reinforcement learning, meta-learning, and agent architectures...",
        "key_concepts": {
            "Self-Evolution": "The ability of AI agents to autonomously improve their capabilities",
            "Agent System": "The core component that processes inputs and generates actions",
            "Optimizers": "Components that update agent parameters based on feedback",
            "Feedback Loop": "The mechanism for continuous improvement",
        },
        "mathematical_foundations": "The framework uses optimization theory with objective functions...",
        "topic_summary": "A comprehensive 500-word summary of the paper...",
        "implementation_examples": "Example code using LangChain for building self-evolving agents...",
    }


@pytest.fixture
def agent(mock_llm, mock_arxiv_client):
    """Paper research agent with mocked dependencies"""
    agent = ArXivPaperResearchAgent(llm=mock_llm)
    agent.arxiv_client = mock_arxiv_client
    return agent


# ============= Test Build Research Context =============

class TestBuildResearchContext:
    """Test building research context from paper metadata"""
    
    def test_build_context_includes_title(self, agent, sample_paper_metadata):
        """Should include paper title in context"""
        # Act
        context = agent._build_research_context(sample_paper_metadata)
        
        # Assert
        assert "A Comprehensive Survey of Self-Evolving AI Agents" in context
    
    def test_build_context_includes_authors(self, agent, sample_paper_metadata):
        """Should include authors in context"""
        # Act
        context = agent._build_research_context(sample_paper_metadata)
        
        # Assert
        assert "Jinyuan Fang" in context
    
    def test_build_context_includes_abstract(self, agent, sample_paper_metadata):
        """Should include abstract/summary in context"""
        # Act
        context = agent._build_research_context(sample_paper_metadata)
        
        # Assert
        assert "Recent advances" in context
        assert "self-evolving" in context.lower()
    
    def test_build_context_includes_arxiv_id(self, agent, sample_paper_metadata):
        """Should include ArXiv ID in context"""
        # Act
        context = agent._build_research_context(sample_paper_metadata)
        
        # Assert
        assert "2508.07407" in context
    
    def test_build_context_includes_categories(self, agent, sample_paper_metadata):
        """Should include paper categories"""
        # Act
        context = agent._build_research_context(sample_paper_metadata)
        
        # Assert
        assert "cs.AI" in context or "AI" in context
    
    def test_build_context_includes_publication_date(self, agent, sample_paper_metadata):
        """Should include publication date"""
        # Act
        context = agent._build_research_context(sample_paper_metadata)
        
        # Assert
        assert "2025" in context


# ============= Test Parse Research Output =============

class TestParseResearchOutput:
    """Test parsing LLM response into PaperResearchOutput"""
    
    def test_parse_valid_json_response(self, agent, sample_research_output, sample_paper_metadata):
        """Should parse valid JSON response correctly"""
        # Arrange
        llm_response = str(sample_research_output).replace("'", '"')
        
        # Act
        result = agent._parse_research_output(
            llm_response=sample_research_output,
            paper_metadata=sample_paper_metadata
        )
        
        # Assert
        assert isinstance(result, PaperResearchOutput)
        assert result.paper_overview is not None
        assert result.methodology_deep_dive is not None
    
    def test_parse_extracts_all_enhanced_sections(self, agent, sample_research_output, sample_paper_metadata):
        """Should extract all 7 enhanced sections"""
        # Act
        result = agent._parse_research_output(
            llm_response=sample_research_output,
            paper_metadata=sample_paper_metadata
        )
        
        # Assert - All enhanced sections present
        assert result.paper_overview is not None
        assert result.methodology_deep_dive is not None
        assert result.experimental_results is not None
        assert result.practical_implications is not None
        assert result.limitations_future_work is not None
        assert result.related_work_summary is not None
        assert result.key_concepts is not None
    
    def test_parse_extracts_key_concepts(self, agent, sample_research_output, sample_paper_metadata):
        """Should extract key concepts dictionary"""
        # Act
        result = agent._parse_research_output(
            llm_response=sample_research_output,
            paper_metadata=sample_paper_metadata
        )
        
        # Assert
        assert isinstance(result.key_concepts, dict)
        assert len(result.key_concepts) >= 1
    
    def test_parse_includes_paper_metadata(self, agent, sample_research_output, paper_metadata_dataclass):
        """Should include paper metadata in output"""
        # Act
        result = agent._parse_research_output(
            llm_response=sample_research_output,
            paper_metadata=paper_metadata_dataclass
        )
        
        # Assert
        assert result.paper_metadata is not None
        assert result.paper_metadata.arxiv_id == "2508.07407"
        assert result.paper_metadata.title == "A Comprehensive Survey of Self-Evolving AI Agents"
    
    def test_parse_handles_missing_optional_fields(self, agent, sample_paper_metadata):
        """Should handle missing optional fields gracefully"""
        # Arrange - Minimal response
        minimal_response = {
            "paper_overview": "Overview text",
            "methodology_deep_dive": "Methodology text",
            "practical_implications": "Implications text",
            "key_concepts": {"key1": "value1"},
            "topic_summary": "Summary text",
        }
        
        # Act
        result = agent._parse_research_output(
            llm_response=minimal_response,
            paper_metadata=sample_paper_metadata
        )
        
        # Assert - Should not raise, optional fields can be None
        assert result.paper_overview == "Overview text"
        assert result.experimental_results is None or result.experimental_results == ""


# ============= Test Calculate Completeness Score =============

class TestCalculateCompletenessScore:
    """Test research completeness scoring"""
    
    def test_completeness_score_full_output(self, agent, paper_metadata_dataclass):
        """Should return high score for complete output"""
        # Arrange - create a more complete research output
        full_output = PaperResearchOutput(
            paper_overview="This paper presents a comprehensive survey " * 20,  # 100+ chars
            methodology_deep_dive="The methodology involves " * 50,  # 200+ chars
            practical_implications="Practical implications include " * 20,
            topic_summary="A comprehensive summary " * 50,  # 200+ chars
            experimental_results="Results show significant " * 20,
            limitations_future_work="Limitations include " * 10,
            related_work_summary="Related work includes " * 10,
            mathematical_foundations="Mathematical foundations " * 10,
            implementation_examples="Implementation code " * 20,
            historical_context="Historical context shows " * 10,
            key_concepts={f"concept_{i}": f"explanation_{i}" * 5 for i in range(12)},  # 12 concepts
            paper_metadata=paper_metadata_dataclass,
            citation="Citation text",
        )
        
        # Act
        score = agent._calculate_completeness_score(full_output)
        
        # Assert
        assert score >= 0.85  # Spec requirement
    
    def test_completeness_score_range(self, agent, sample_research_output, paper_metadata_dataclass):
        """Should return score between 0 and 1"""
        # Arrange
        output = agent._parse_research_output(
            llm_response=sample_research_output,
            paper_metadata=paper_metadata_dataclass
        )
        
        # Act
        score = agent._calculate_completeness_score(output)
        
        # Assert
        assert 0.0 <= score <= 1.0
    
    def test_completeness_score_low_for_minimal_output(self, agent, paper_metadata_dataclass):
        """Should return low score for minimal output"""
        # Arrange
        minimal_output = PaperResearchOutput(
            paper_overview="Short overview",
            methodology_deep_dive="",
            practical_implications="",
            key_concepts={},
            topic_summary="Short summary",
            paper_metadata=paper_metadata_dataclass,
            citation="Citation",
        )
        
        # Act
        score = agent._calculate_completeness_score(minimal_output)
        
        # Assert
        assert score < 0.5
    
    def test_completeness_checks_key_concepts_count(self, agent, paper_metadata_dataclass):
        """Should consider number of key concepts"""
        # Arrange
        output_few_concepts = PaperResearchOutput(
            paper_overview="Overview " * 50,
            methodology_deep_dive="Methodology " * 100,
            practical_implications="Implications " * 50,
            key_concepts={"one": "concept"},  # Only 1 concept
            topic_summary="Summary " * 100,
            paper_metadata=paper_metadata_dataclass,
            citation="Citation",
        )
        
        output_many_concepts = PaperResearchOutput(
            paper_overview="Overview " * 50,
            methodology_deep_dive="Methodology " * 100,
            practical_implications="Implications " * 50,
            key_concepts={f"concept_{i}": f"explanation_{i}" for i in range(10)},  # 10 concepts
            topic_summary="Summary " * 100,
            paper_metadata=paper_metadata_dataclass,
            citation="Citation",
        )
        
        # Act
        score_few = agent._calculate_completeness_score(output_few_concepts)
        score_many = agent._calculate_completeness_score(output_many_concepts)
        
        # Assert
        assert score_many > score_few


# ============= Test Generate Citation =============

class TestGenerateCitation:
    """Test academic citation generation"""
    
    def test_generate_citation_format(self, agent, sample_paper_metadata):
        """Should generate proper academic citation format"""
        # Act
        citation = agent._generate_citation(sample_paper_metadata)
        
        # Assert
        assert "A Comprehensive Survey of Self-Evolving AI Agents" in citation
        assert "2508.07407" in citation
        assert "2025" in citation
    
    def test_generate_citation_includes_authors(self, agent, sample_paper_metadata):
        """Should include authors in citation"""
        # Act
        citation = agent._generate_citation(sample_paper_metadata)
        
        # Assert
        assert "Fang" in citation or "Jinyuan" in citation
    
    def test_generate_citation_includes_arxiv_link(self, agent, sample_paper_metadata):
        """Should include ArXiv URL in citation"""
        # Act
        citation = agent._generate_citation(sample_paper_metadata)
        
        # Assert
        assert "arxiv" in citation.lower()


# ============= Test Validate Paper Content =============

class TestValidatePaperContent:
    """Test paper content validation"""
    
    def test_validate_sufficient_abstract(self, agent, sample_paper_metadata):
        """Should pass validation for sufficient abstract"""
        # Act & Assert - Should not raise
        agent._validate_paper_content(sample_paper_metadata)
    
    def test_validate_short_abstract_logs_warning(self, agent, sample_paper_metadata, caplog):
        """Should log warning for abstract < 50 words"""
        # Arrange
        sample_paper_metadata["summary"] = "Too short abstract."
        
        # Act - now just warns but doesn't raise
        agent._validate_paper_content(sample_paper_metadata)
        
        # Assert - check that warning was logged
        assert "short" in caplog.text.lower()
    
    def test_validate_missing_abstract_raises_error(self, agent, sample_paper_metadata):
        """Should raise error for missing abstract"""
        # Arrange
        sample_paper_metadata["summary"] = ""
        
        # Act & Assert
        with pytest.raises(PaperContentInsufficientError):
            agent._validate_paper_content(sample_paper_metadata)


# ============= Test Format for Blog =============

class TestFormatForBlog:
    """Test formatting research output for blog generation"""
    
    def test_format_includes_paper_overview(self, agent, sample_research_output, sample_paper_metadata):
        """Should include paper overview in blog format"""
        # Arrange
        output = agent._parse_research_output(
            llm_response=sample_research_output,
            paper_metadata=sample_paper_metadata
        )
        
        # Act
        blog_input = agent._format_for_blog(output)
        
        # Assert
        assert "paper_overview" in blog_input or output.paper_overview in str(blog_input)
    
    def test_format_includes_key_findings(self, agent, sample_research_output, sample_paper_metadata):
        """Should include key findings for blog"""
        # Arrange
        output = agent._parse_research_output(
            llm_response=sample_research_output,
            paper_metadata=sample_paper_metadata
        )
        
        # Act
        blog_input = agent._format_for_blog(output)
        
        # Assert
        assert isinstance(blog_input, (dict, str))


# ============= Test Research Paper by ID =============

class TestResearchPaperById:
    """Test main research_paper_by_id method"""
    
    @pytest.mark.asyncio
    async def test_research_paper_success(self, agent, mock_arxiv_client, mock_llm, sample_paper_metadata, sample_research_output):
        """Should successfully research a paper by ID"""
        # Arrange
        mock_arxiv_client.get_paper.return_value = sample_paper_metadata
        mock_llm.ainvoke.return_value = sample_research_output  # Return dict directly
        
        # Act
        result = await agent.research_paper_by_id(
            arxiv_id="2508.07407",
            target_audience="practitioner"
        )
        
        # Assert
        assert isinstance(result, PaperResearchOutput)
        assert result.paper_metadata.arxiv_id == "2508.07407"
    
    @pytest.mark.asyncio
    async def test_research_paper_not_found(self, agent, mock_arxiv_client):
        """Should raise PaperNotFoundError when paper doesn't exist"""
        # Arrange
        mock_arxiv_client.get_paper.return_value = None
        
        # Act & Assert
        with pytest.raises(PaperNotFoundError) as exc_info:
            await agent.research_paper_by_id("9999.99999")
        
        assert "9999.99999" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_research_paper_invalid_id(self, agent):
        """Should raise InvalidArXivIdError for invalid ID format"""
        # Act & Assert
        with pytest.raises(InvalidArXivIdError):
            await agent.research_paper_by_id("invalid_id")


# ============= Test Research Paper by Title =============

class TestResearchPaperByTitle:
    """Test research_paper_by_title method"""
    
    @pytest.mark.asyncio
    async def test_research_by_title_success(self, agent, mock_arxiv_client, mock_llm, sample_paper_metadata, sample_research_output):
        """Should find and research paper by title"""
        # Arrange
        mock_arxiv_client.search.return_value = [sample_paper_metadata]
        mock_arxiv_client.get_paper.return_value = sample_paper_metadata
        mock_llm.ainvoke.return_value = sample_research_output  # Return dict directly
        
        # Act
        result = await agent.research_paper_by_title(
            title="self-evolving agents",
            target_audience="practitioner"
        )
        
        # Assert
        assert isinstance(result, PaperResearchOutput)
    
    @pytest.mark.asyncio
    async def test_research_by_title_no_results(self, agent, mock_arxiv_client):
        """Should raise error when no papers found"""
        # Arrange
        mock_arxiv_client.search.return_value = []
        
        # Act & Assert
        with pytest.raises(PaperNotFoundError):
            await agent.research_paper_by_title("nonexistent paper title xyz123")


# ============= Test Multiple Paper Research =============

class TestResearchMultiplePapers:
    """Test researching multiple papers"""
    
    @pytest.mark.asyncio
    async def test_research_multiple_papers_success(self, agent, mock_arxiv_client, mock_llm, sample_paper_metadata, sample_research_output):
        """Should research multiple papers and synthesize"""
        # Arrange
        mock_arxiv_client.get_paper.return_value = sample_paper_metadata
        mock_llm.ainvoke.return_value = sample_research_output  # Return dict directly
        
        # Act
        result = await agent.research_multiple_papers(
            arxiv_ids=["2508.07407", "1706.03762"],
            target_audience="practitioner"
        )
        
        # Assert
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_research_multiple_papers_limit_exceeded(self, agent):
        """Should raise error when more than 5 papers requested"""
        # Arrange
        arxiv_ids = [f"2508.0740{i}" for i in range(6)]  # 6 papers
        
        # Act & Assert
        with pytest.raises(MultiplePapersLimitError) as exc_info:
            await agent.research_multiple_papers(arxiv_ids=arxiv_ids)
        
        assert "5" in str(exc_info.value)  # Should mention limit
        assert "6" in str(exc_info.value)  # Should mention requested count
    
    @pytest.mark.asyncio
    async def test_research_single_paper_in_list(self, agent, mock_arxiv_client, mock_llm, sample_paper_metadata, sample_research_output):
        """Should handle list with single paper"""
        # Arrange
        mock_arxiv_client.get_paper.return_value = sample_paper_metadata
        mock_llm.ainvoke.return_value = sample_research_output  # Return dict directly
        
        # Act
        result = await agent.research_multiple_papers(
            arxiv_ids=["2508.07407"],
            target_audience="practitioner"
        )
        
        # Assert
        assert result is not None


# ============= Test PaperResearchOutput Dataclass =============

class TestPaperResearchOutput:
    """Test PaperResearchOutput dataclass"""
    
    def test_output_has_all_required_fields(self, paper_metadata_dataclass):
        """Should have all required fields"""
        # Arrange & Act
        output = PaperResearchOutput(
            paper_overview="Overview",
            methodology_deep_dive="Methodology",
            practical_implications="Implications",
            key_concepts={"key": "value"},
            topic_summary="Summary",
            paper_metadata=paper_metadata_dataclass,
            citation="Citation text",
            completeness_score=0.9,
        )
        
        # Assert
        assert output.paper_overview == "Overview"
        assert output.methodology_deep_dive == "Methodology"
        assert output.completeness_score == 0.9
    
    def test_output_optional_fields_default_none(self, paper_metadata_dataclass):
        """Should allow None for optional fields"""
        # Arrange & Act
        output = PaperResearchOutput(
            paper_overview="Overview",
            methodology_deep_dive="Methodology",
            practical_implications="Implications",
            key_concepts={},
            topic_summary="Summary",
            paper_metadata=paper_metadata_dataclass,
            citation="Citation",
            experimental_results=None,
            limitations_future_work=None,
            related_work_summary=None,
            mathematical_foundations=None,
        )
        
        # Assert
        assert output.experimental_results is None
        assert output.limitations_future_work is None


# ============= Test PaperMetadata Dataclass =============

class TestPaperMetadata:
    """Test PaperMetadata dataclass"""
    
    def test_metadata_from_arxiv_response(self, sample_paper_metadata):
        """Should create metadata from ArXiv response"""
        # Act
        metadata = PaperMetadata.from_arxiv_response(sample_paper_metadata)
        
        # Assert
        assert metadata.arxiv_id == "2508.07407"
        assert metadata.title == "A Comprehensive Survey of Self-Evolving AI Agents"
        assert len(metadata.authors) == 3
    
    def test_metadata_categories_list(self, sample_paper_metadata):
        """Should store categories as list"""
        # Act
        metadata = PaperMetadata.from_arxiv_response(sample_paper_metadata)
        
        # Assert
        assert isinstance(metadata.categories, list)
        assert "cs.AI" in metadata.categories

