"""
CLI tests for Paper Research Commands
Tests Typer CLI commands for paper research
Maps to: spec.md → CLI requirements | plan.md → T018, T020
"""
import pytest
from typer.testing import CliRunner
from unittest.mock import AsyncMock, patch, MagicMock
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# ============= Fixtures =============

@pytest.fixture
def cli_runner():
    """Typer CLI test runner"""
    return CliRunner()


@pytest.fixture
def paper_app():
    """Import the paper CLI app"""
    from src.cli.commands.paper import app
    return app


@dataclass
class MockPaperMetadata:
    """Mock paper metadata for testing"""
    arxiv_id: str = "1706.03762"
    title: str = "Attention Is All You Need"
    authors: List[str] = field(default_factory=lambda: ["Vaswani et al."])
    abstract: str = "Test abstract"
    published: str = "2017-06-12"
    updated: Optional[str] = None
    categories: List[str] = field(default_factory=lambda: ["cs.CL"])
    pdf_url: Optional[str] = None
    abs_url: Optional[str] = None


@dataclass
class MockResearchOutput:
    """Mock research output for testing"""
    paper_metadata: MockPaperMetadata = field(default_factory=MockPaperMetadata)
    paper_overview: str = "Overview of the paper"
    methodology_deep_dive: str = "Detailed methodology"
    topic_summary: str = "Summary"
    practical_implications: str = "Implications"
    experimental_results: Optional[str] = "Results"
    limitations_future_work: Optional[str] = "Limitations"
    related_work_summary: Optional[str] = "Related work"
    key_concepts: Dict[str, str] = field(default_factory=lambda: {"Attention": "Mechanism"})
    citation: str = "Citation text"
    completeness_score: float = 0.9
    sources: List[Dict[str, Any]] = field(default_factory=list)
    research_data_path: Optional[str] = "/tmp/research.json"
    
    def to_dict(self):
        return {
            "paper_metadata": {
                "arxiv_id": self.paper_metadata.arxiv_id,
                "title": self.paper_metadata.title,
            },
            "paper_overview": self.paper_overview,
            "completeness_score": self.completeness_score,
        }


@dataclass
class MockBlogOutput:
    """Mock blog output for testing"""
    title: str = "Blog Title"
    content: str = "Blog content..."
    estimated_reading_time: Optional[str] = "5 min"
    tags: List[str] = field(default_factory=lambda: ["AI", "ML"])
    file_path: Optional[str] = "/tmp/blog.md"


@pytest.fixture
def sample_research_output():
    """Sample research output for CLI tests"""
    return MockResearchOutput()


@pytest.fixture
def sample_blog_output():
    """Sample blog output for CLI tests"""
    return MockBlogOutput()


@pytest.fixture
def sample_paper_metadata():
    """Sample paper metadata dict"""
    return {
        "arxiv_id": "1706.03762",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani", "Shazeer", "Parmar"],
        "summary": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
        "published": "2017-06-12",
        "updated": "2017-12-06",
        "categories": ["cs.CL", "cs.LG"],
        "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
        "abs_url": "https://arxiv.org/abs/1706.03762",
    }


# ============= Test Research Command =============

class TestResearchCommand:
    """Test 'paper research' command"""
    
    def test_research_with_arxiv_id(self, cli_runner, paper_app, sample_research_output):
        """Should research paper by ArXiv ID"""
        with patch('src.lib.agents.arxiv_paper_research_agent.ArXivPaperResearchAgent') as MockAgent:
            agent = MagicMock()
            agent.research_paper_by_id = AsyncMock(return_value=sample_research_output)
            agent.close = AsyncMock()
            MockAgent.return_value = agent
            
            result = cli_runner.invoke(paper_app, [
                "research",
                "--arxiv-id", "1706.03762",
                "--audience", "practitioner"
            ])
            
            assert result.exit_code == 0
    
    def test_research_with_title(self, cli_runner, paper_app, sample_research_output):
        """Should research paper by title search"""
        with patch('src.lib.agents.arxiv_paper_research_agent.ArXivPaperResearchAgent') as MockAgent:
            agent = MagicMock()
            agent.research_paper_by_title = AsyncMock(return_value=sample_research_output)
            agent.close = AsyncMock()
            MockAgent.return_value = agent
            
            result = cli_runner.invoke(paper_app, [
                "research",
                "--title", "attention is all you need",
                "--audience", "expert"
            ])
            
            assert result.exit_code == 0
    
    def test_research_missing_input_fails(self, cli_runner, paper_app):
        """Should fail when neither arxiv_id nor title provided"""
        result = cli_runner.invoke(paper_app, [
            "research",
            "--audience", "practitioner"
        ])
        
        assert result.exit_code == 1
        assert "Either --arxiv-id or --title must be provided" in result.output
    
    def test_research_with_verbose(self, cli_runner, paper_app, sample_research_output):
        """Should show verbose output when --verbose flag is used"""
        with patch('src.lib.agents.arxiv_paper_research_agent.ArXivPaperResearchAgent') as MockAgent:
            agent = MagicMock()
            agent.research_paper_by_id = AsyncMock(return_value=sample_research_output)
            agent.close = AsyncMock()
            MockAgent.return_value = agent
            
            result = cli_runner.invoke(paper_app, [
                "research",
                "--arxiv-id", "1706.03762",
                "--verbose"
            ])
            
            assert result.exit_code == 0


# ============= Test Full Command =============

class TestFullCommand:
    """Test 'paper full' command"""
    
    def test_full_command_success(self, cli_runner, paper_app, sample_research_output, sample_blog_output):
        """Should run full research + blog workflow"""
        with patch('src.lib.agents.arxiv_paper_research_agent.ArXivPaperResearchAgent') as MockAgent:
            agent = MagicMock()
            agent.research_paper_by_id = AsyncMock(return_value=sample_research_output)
            agent.generate_blog_from_research = AsyncMock(return_value=sample_blog_output)
            agent.close = AsyncMock()
            MockAgent.return_value = agent
            
            result = cli_runner.invoke(paper_app, [
                "full",
                "--arxiv-id", "1706.03762"
            ])
            
            assert result.exit_code == 0
    
    def test_full_command_missing_input(self, cli_runner, paper_app):
        """Should fail when no input provided"""
        result = cli_runner.invoke(paper_app, [
            "full"
        ])
        
        assert result.exit_code == 1


# ============= Test Search Command =============

class TestSearchCommand:
    """Test 'paper search' command"""
    
    def test_search_returns_results(self, cli_runner, paper_app, sample_paper_metadata):
        """Should search and return results"""
        with patch('src.lib.services.arxiv_client.ArXivClient') as MockClient:
            client = MagicMock()
            client.search = AsyncMock(return_value=[sample_paper_metadata])
            client.close = AsyncMock()
            MockClient.return_value = client
            
            result = cli_runner.invoke(paper_app, [
                "search", "attention mechanism"
            ])
            
            assert result.exit_code == 0
    
    def test_search_no_results(self, cli_runner, paper_app):
        """Should handle no results gracefully"""
        with patch('src.lib.services.arxiv_client.ArXivClient') as MockClient:
            client = MagicMock()
            client.search = AsyncMock(return_value=[])
            client.close = AsyncMock()
            MockClient.return_value = client
            
            result = cli_runner.invoke(paper_app, [
                "search", "xyznonexistent123"
            ])
            
            assert result.exit_code == 0
            assert "No papers found" in result.output


# ============= Test Info Command =============

class TestInfoCommand:
    """Test 'paper info' command"""
    
    def test_info_displays_metadata(self, cli_runner, paper_app, sample_paper_metadata):
        """Should display paper metadata"""
        with patch('src.lib.services.arxiv_client.ArXivClient') as MockClient:
            client = MagicMock()
            client.get_paper = AsyncMock(return_value=sample_paper_metadata)
            client.close = AsyncMock()
            MockClient.return_value = client
            
            result = cli_runner.invoke(paper_app, [
                "info", "1706.03762"
            ])
            
            assert result.exit_code == 0
    
    def test_info_not_found(self, cli_runner, paper_app):
        """Should handle paper not found"""
        with patch('src.lib.services.arxiv_client.ArXivClient') as MockClient:
            client = MagicMock()
            client.get_paper = AsyncMock(return_value=None)
            client.close = AsyncMock()
            MockClient.return_value = client
            
            result = cli_runner.invoke(paper_app, [
                "info", "9999.99999"
            ])
            
            assert result.exit_code == 1
            assert "not found" in result.output.lower()
    
    def test_info_invalid_id(self, cli_runner, paper_app):
        """Should reject invalid ArXiv ID"""
        result = cli_runner.invoke(paper_app, [
            "info", "invalid_id"
        ])
        
        assert result.exit_code == 1


# ============= Test Batch Command =============

class TestBatchCommand:
    """Test 'paper batch' command"""
    
    def test_batch_single_paper(self, cli_runner, paper_app, sample_research_output):
        """Should handle batch with single paper"""
        with patch('src.lib.agents.arxiv_paper_research_agent.ArXivPaperResearchAgent') as MockAgent:
            agent = MagicMock()
            agent.research_paper_by_id = AsyncMock(return_value=sample_research_output)
            agent.close = AsyncMock()
            MockAgent.return_value = agent
            
            result = cli_runner.invoke(paper_app, [
                "batch", "1706.03762"
            ])
            
            assert result.exit_code == 0
    
    def test_batch_too_many_papers(self, cli_runner, paper_app):
        """Should reject more than 5 papers"""
        result = cli_runner.invoke(paper_app, [
            "batch", "1,2,3,4,5,6"
        ])
        
        assert result.exit_code == 1
        assert "Maximum 5" in result.output
    
    def test_batch_with_synthesize(self, cli_runner, paper_app, sample_research_output):
        """Should synthesize results when --synthesize flag used"""
        with patch('src.lib.agents.arxiv_paper_research_agent.ArXivPaperResearchAgent') as MockAgent:
            agent = MagicMock()
            agent.research_multiple_papers = AsyncMock(return_value=sample_research_output)
            agent.close = AsyncMock()
            MockAgent.return_value = agent
            
            result = cli_runner.invoke(paper_app, [
                "batch", "1706.03762,2508.07407", "--synthesize"
            ])
            
            assert result.exit_code == 0


# ============= Test CLI Help =============

class TestCLIHelpText:
    """Test CLI help text"""
    
    def test_research_help(self, cli_runner, paper_app):
        """Should show research command help"""
        result = cli_runner.invoke(paper_app, ["research", "--help"])
        
        assert result.exit_code == 0
        assert "--arxiv-id" in result.output
        assert "--title" in result.output
        assert "--audience" in result.output
    
    def test_full_help(self, cli_runner, paper_app):
        """Should show full command help"""
        result = cli_runner.invoke(paper_app, ["full", "--help"])
        
        assert result.exit_code == 0
        assert "--arxiv-id" in result.output
    
    def test_search_help(self, cli_runner, paper_app):
        """Should show search command help"""
        result = cli_runner.invoke(paper_app, ["search", "--help"])
        
        assert result.exit_code == 0
        assert "--max" in result.output
    
    def test_main_help(self, cli_runner, paper_app):
        """Should show main help"""
        result = cli_runner.invoke(paper_app, ["--help"])
        
        assert result.exit_code == 0
        assert "research" in result.output
        assert "full" in result.output
        assert "search" in result.output
        assert "info" in result.output
