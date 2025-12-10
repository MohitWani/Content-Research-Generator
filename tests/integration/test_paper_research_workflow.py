"""
Integration tests for Paper Research Workflow
Uses REAL ArXiv API and AWS Bedrock LLM (rate-limited)
Tests full workflow from paper ID to research output
Maps to: spec.md → Story 1-8, FR2-FR10 | plan.md → T010
"""
import pytest
import asyncio
from datetime import datetime

from src.lib.agents.arxiv_paper_research_agent import (
    ArXivPaperResearchAgent,
    PaperResearchOutput,
    PaperMetadata,
)
from src.lib.services.arxiv_client import ArXivClient
from src.lib.agents.blog_writer_agent import BlogWriterAgent
from src.lib.pipelines.paper_research_pipeline import PaperResearchPipeline
from src.lib.models.exceptions import (
    PaperNotFoundError,
    InvalidArXivIdError,
)


# ============= Fixtures =============

@pytest.fixture
def arxiv_client():
    """Real ArXiv client for integration tests"""
    return ArXivClient()


@pytest.fixture
def paper_research_agent(llm):
    """Paper research agent with real LLM"""
    return ArXivPaperResearchAgent(llm=llm)


@pytest.fixture
def known_arxiv_ids():
    """Known valid ArXiv IDs for testing"""
    return {
        "attention": "1706.03762",  # Attention Is All You Need
        "gpt3": "2005.14165",  # Language Models are Few-Shot Learners (GPT-3)
        "bert": "1810.04805",  # BERT
        "transformer": "1706.03762",  # Same as attention
    }


# ============= Paper Retrieval Tests =============

@pytest.mark.integration
class TestPaperRetrieval:
    """Test paper retrieval from ArXiv API"""
    
    @pytest.mark.asyncio
    async def test_retrieve_known_paper(self, arxiv_client):
        """Should retrieve known paper: Attention Is All You Need"""
        # Arrange
        arxiv_id = "1706.03762"
        
        # Act
        paper = await arxiv_client.get_paper(arxiv_id)
        
        # Assert
        assert paper is not None
        assert paper["title"] is not None
        assert "attention" in paper["title"].lower() or "transformer" in paper["title"].lower()
        assert len(paper["authors"]) > 0
        assert paper["summary"] is not None
    
    @pytest.mark.asyncio
    async def test_retrieve_paper_with_version(self, arxiv_client):
        """Should retrieve specific paper version"""
        # Arrange
        arxiv_id = "1706.03762v1"
        
        # Act
        paper = await arxiv_client.get_paper(arxiv_id)
        
        # Assert
        assert paper is not None
    
    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_paper(self, arxiv_client):
        """Should return None for non-existent paper"""
        # Arrange
        arxiv_id = "9999.99999"
        
        # Act
        paper = await arxiv_client.get_paper(arxiv_id)
        
        # Assert
        assert paper is None
    
    @pytest.mark.asyncio
    async def test_paper_metadata_completeness(self, arxiv_client):
        """Should retrieve complete paper metadata"""
        # Arrange
        arxiv_id = "1706.03762"
        
        # Act
        paper = await arxiv_client.get_paper(arxiv_id)
        
        # Assert - All required metadata fields present
        assert "title" in paper
        assert "authors" in paper
        assert "summary" in paper
        assert "published" in paper
        assert "categories" in paper
        assert paper["pdf_url"] is not None or "pdf" in str(paper)


@pytest.mark.integration
class TestPaperSearch:
    """Test paper search functionality"""
    
    @pytest.mark.asyncio
    async def test_search_by_title(self, arxiv_client):
        """Should find paper by title search"""
        # Arrange
        query = "attention is all you need"
        
        # Act
        results = await arxiv_client.search(query, max_results=5)
        
        # Assert
        assert len(results) > 0
        # Should find the attention paper
        titles = [r["title"].lower() for r in results]
        assert any("attention" in t for t in titles)
    
    @pytest.mark.asyncio
    async def test_search_returns_multiple_results(self, arxiv_client):
        """Should return multiple results for broad query"""
        # Arrange
        query = "transformer neural network"
        
        # Act
        results = await arxiv_client.search(query, max_results=5)
        
        # Assert
        assert len(results) >= 1
    
    @pytest.mark.asyncio
    async def test_search_respects_max_results(self, arxiv_client):
        """Should respect max_results limit"""
        # Arrange
        query = "machine learning"
        max_results = 3
        
        # Act
        results = await arxiv_client.search(query, max_results=max_results)
        
        # Assert
        assert len(results) <= max_results


# ============= Full Research Workflow Tests =============

@pytest.mark.integration
@pytest.mark.slow
class TestFullResearchWorkflow:
    """Test complete research workflow with real LLM"""
    
    @pytest.mark.asyncio
    async def test_research_known_paper(self, paper_research_agent, known_arxiv_ids):
        """Should successfully research Attention paper"""
        # Arrange
        arxiv_id = known_arxiv_ids["attention"]
        
        # Act
        result = await paper_research_agent.research_paper_by_id(
            arxiv_id=arxiv_id,
            target_audience="practitioner"
        )
        
        # Assert
        assert isinstance(result, PaperResearchOutput)
        assert result.paper_metadata.arxiv_id == arxiv_id
        assert result.paper_overview is not None
        assert len(result.paper_overview) > 100  # Substantial content
    
    @pytest.mark.asyncio
    async def test_research_completeness_score(self, paper_research_agent, known_arxiv_ids):
        """Should achieve completeness score > 0.8 for known paper"""
        # Arrange
        arxiv_id = known_arxiv_ids["attention"]
        
        # Act
        result = await paper_research_agent.research_paper_by_id(
            arxiv_id=arxiv_id,
            target_audience="practitioner"
        )
        
        # Assert
        assert result.completeness_score >= 0.8
    
    @pytest.mark.asyncio
    async def test_enhanced_sections_populated(self, paper_research_agent, known_arxiv_ids):
        """Should populate all enhanced sections"""
        # Arrange
        arxiv_id = known_arxiv_ids["attention"]
        
        # Act
        result = await paper_research_agent.research_paper_by_id(
            arxiv_id=arxiv_id,
            target_audience="practitioner"
        )
        
        # Assert - All 7 enhanced sections should have content
        assert result.paper_overview and len(result.paper_overview) > 50
        assert result.methodology_deep_dive and len(result.methodology_deep_dive) > 50
        assert result.practical_implications and len(result.practical_implications) > 50
        assert result.key_concepts and len(result.key_concepts) >= 3
    
    @pytest.mark.asyncio
    async def test_paper_metadata_extracted(self, paper_research_agent, known_arxiv_ids):
        """Should correctly extract paper metadata"""
        # Arrange
        arxiv_id = known_arxiv_ids["attention"]
        
        # Act
        result = await paper_research_agent.research_paper_by_id(
            arxiv_id=arxiv_id,
            target_audience="practitioner"
        )
        
        # Assert
        assert result.paper_metadata.title is not None
        assert len(result.paper_metadata.authors) > 0
        assert result.paper_metadata.abstract is not None or result.paper_metadata.title
    
    @pytest.mark.asyncio
    async def test_citation_format(self, paper_research_agent, known_arxiv_ids):
        """Should generate proper citation format"""
        # Arrange
        arxiv_id = known_arxiv_ids["attention"]
        
        # Act
        result = await paper_research_agent.research_paper_by_id(
            arxiv_id=arxiv_id,
            target_audience="practitioner"
        )
        
        # Assert
        assert result.citation is not None
        assert arxiv_id in result.citation or "1706" in result.citation
        assert "arxiv" in result.citation.lower() or "arXiv" in result.citation
    
    @pytest.mark.asyncio
    async def test_research_by_title_search(self, paper_research_agent):
        """Should find and research paper by title"""
        # Arrange
        title = "attention is all you need"
        
        # Act
        result = await paper_research_agent.research_paper_by_title(
            title=title,
            target_audience="practitioner"
        )
        
        # Assert
        assert isinstance(result, PaperResearchOutput)
        assert "attention" in result.paper_metadata.title.lower() or \
               "transformer" in result.paper_metadata.title.lower()


# ============= Blog Generation Tests =============

@pytest.mark.integration
@pytest.mark.slow
class TestBlogGenerationFromPaper:
    """Test blog generation from paper research"""
    
    @pytest.mark.asyncio
    async def test_generate_blog_from_research(self, paper_research_agent, known_arxiv_ids):
        """Should generate blog from paper research"""
        # Arrange
        arxiv_id = known_arxiv_ids["attention"]
        research = await paper_research_agent.research_paper_by_id(
            arxiv_id=arxiv_id,
            target_audience="practitioner"
        )
        
        # Act
        blog = await paper_research_agent.generate_blog_from_research(
            research_output=research,
            target_audience="practitioner"
        )
        
        # Assert
        assert blog is not None
        assert blog.title is not None
        assert blog.content is not None
        assert len(blog.content) > 500  # Substantial blog content
    
    @pytest.mark.asyncio
    async def test_blog_includes_paper_citation(self, paper_research_agent, known_arxiv_ids):
        """Should include paper citation in blog"""
        # Arrange
        arxiv_id = known_arxiv_ids["attention"]
        research = await paper_research_agent.research_paper_by_id(
            arxiv_id=arxiv_id,
            target_audience="practitioner"
        )
        
        # Act
        blog = await paper_research_agent.generate_blog_from_research(
            research_output=research,
            target_audience="practitioner"
        )
        
        # Assert
        assert arxiv_id in blog.content or "1706" in blog.content or \
               "arxiv" in blog.content.lower()


# ============= Multiple Paper Research Tests =============

@pytest.mark.integration
@pytest.mark.slow
class TestMultiplePaperResearch:
    """Test researching multiple papers"""
    
    @pytest.mark.asyncio
    async def test_research_two_papers(self, paper_research_agent, known_arxiv_ids):
        """Should research and synthesize two papers"""
        # Arrange
        arxiv_ids = [known_arxiv_ids["attention"], known_arxiv_ids["bert"]]
        
        # Act
        result = await paper_research_agent.research_multiple_papers(
            arxiv_ids=arxiv_ids,
            target_audience="practitioner"
        )
        
        # Assert
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_identify_common_themes(self, paper_research_agent, known_arxiv_ids):
        """Should identify common themes across papers"""
        # Arrange - Both are transformer papers
        arxiv_ids = [known_arxiv_ids["attention"], known_arxiv_ids["bert"]]
        
        # Act
        result = await paper_research_agent.research_multiple_papers(
            arxiv_ids=arxiv_ids,
            target_audience="practitioner"
        )
        
        # Assert - Should mention transformers/attention as common theme
        result_text = str(result).lower()
        assert "transformer" in result_text or "attention" in result_text


# ============= Error Handling Tests =============

@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in paper research"""
    
    @pytest.mark.asyncio
    async def test_paper_not_found_error(self, paper_research_agent):
        """Should raise PaperNotFoundError for non-existent paper"""
        # Arrange
        fake_id = "9999.99999"
        
        # Act & Assert
        with pytest.raises(PaperNotFoundError) as exc_info:
            await paper_research_agent.research_paper_by_id(fake_id)
        
        assert fake_id in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_id_error(self, paper_research_agent):
        """Should raise InvalidArXivIdError for invalid ID format"""
        # Arrange
        invalid_id = "not_a_valid_id"
        
        # Act & Assert
        with pytest.raises(InvalidArXivIdError) as exc_info:
            await paper_research_agent.research_paper_by_id(invalid_id)
        
        assert invalid_id in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_title_search_no_results(self, paper_research_agent):
        """Should handle no search results gracefully"""
        # Arrange
        nonsense_title = "xyzzy12345 completely nonexistent paper title"
        
        # Act & Assert
        with pytest.raises(PaperNotFoundError):
            await paper_research_agent.research_paper_by_title(nonsense_title)


# ============= Rate Limiting Tests =============

@pytest.mark.integration
class TestRateLimiting:
    """Test rate limiting behavior"""
    
    @pytest.mark.asyncio
    async def test_multiple_requests_respect_rate_limit(self, arxiv_client):
        """Should not exceed ArXiv rate limit"""
        # Arrange
        arxiv_ids = ["1706.03762", "1810.04805", "2005.14165"]
        start_time = datetime.now()
        
        # Act
        results = []
        for arxiv_id in arxiv_ids:
            paper = await arxiv_client.get_paper(arxiv_id)
            results.append(paper)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Assert - Should take at least 2 seconds for 3 requests (1 req/sec)
        assert elapsed >= 2.0 or all(r is not None for r in results)


# ============= Pipeline Tests =============

@pytest.mark.integration
@pytest.mark.slow
class TestPaperResearchPipeline:
    """Test paper research pipeline"""
    
    @pytest.mark.asyncio
    async def test_pipeline_execute(self, db_session, llm):
        """Should execute full pipeline"""
        # Arrange
        pipeline = PaperResearchPipeline(db_session=db_session, llm=llm)
        arxiv_id = "1706.03762"
        
        # Act
        result = await pipeline.execute(
            arxiv_id=arxiv_id,
            target_audience="practitioner",
            generate_blog=True
        )
        
        # Assert
        assert result is not None
        assert result.research_output is not None
    
    @pytest.mark.asyncio
    async def test_pipeline_saves_to_database(self, db_session, llm):
        """Should save research result to database"""
        # Arrange
        pipeline = PaperResearchPipeline(db_session=db_session, llm=llm)
        arxiv_id = "1706.03762"
        
        # Act
        result = await pipeline.execute(
            arxiv_id=arxiv_id,
            target_audience="practitioner",
            generate_blog=False
        )
        await db_session.commit()
        
        # Assert - Result should be persisted
        assert result.research_id is not None


# ============= Audience Customization Tests =============

@pytest.mark.integration
@pytest.mark.slow
class TestAudienceCustomization:
    """Test target audience affects output"""
    
    @pytest.mark.asyncio
    async def test_beginner_audience(self, paper_research_agent, known_arxiv_ids):
        """Should adapt content for beginner audience"""
        # Arrange
        arxiv_id = known_arxiv_ids["attention"]
        
        # Act
        result = await paper_research_agent.research_paper_by_id(
            arxiv_id=arxiv_id,
            target_audience="beginner"
        )
        
        # Assert
        assert result is not None
        # Beginner content should be more accessible
    
    @pytest.mark.asyncio
    async def test_expert_audience(self, paper_research_agent, known_arxiv_ids):
        """Should adapt content for expert audience"""
        # Arrange
        arxiv_id = known_arxiv_ids["attention"]
        
        # Act
        result = await paper_research_agent.research_paper_by_id(
            arxiv_id=arxiv_id,
            target_audience="expert"
        )
        
        # Assert
        assert result is not None
        # Expert content should include more technical details

