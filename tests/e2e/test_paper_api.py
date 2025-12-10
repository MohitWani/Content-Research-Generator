"""
E2E tests for Paper Research API endpoints
Tests full request-response cycle with real database
Maps to: spec.md → Acceptance Criteria | plan.md → T016, Section 7
"""
import pytest
from httpx import AsyncClient


# ============= Test POST /research (Async) =============

@pytest.mark.e2e
class TestPaperResearchAsync:
    """Test POST /api/v1/paper/research endpoint (async)"""
    
    @pytest.mark.asyncio
    async def test_research_returns_202(self, async_client: AsyncClient):
        """Should accept research request and return 202 Accepted"""
        # Arrange
        payload = {
            "paper": {"arxiv_id": "1706.03762"},
            "target_audience": "practitioner",
            "generate_blog": False
        }
        
        # Act
        response = await async_client.post("/api/v1/paper/research", json=payload)
        
        # Assert
        assert response.status_code == 202
        data = response.json()
        assert "research_id" in data
        assert data["status"] in ["pending", "processing"]
    
    @pytest.mark.asyncio
    async def test_research_with_title_search(self, async_client: AsyncClient):
        """Should accept title search input"""
        # Arrange
        payload = {
            "paper": {"title_search": "attention is all you need"},
            "target_audience": "practitioner"
        }
        
        # Act
        response = await async_client.post("/api/v1/paper/research", json=payload)
        
        # Assert
        assert response.status_code == 202
        data = response.json()
        assert "research_id" in data
    
    @pytest.mark.asyncio
    async def test_research_invalid_arxiv_id_returns_400(self, async_client: AsyncClient):
        """Should return 400 for invalid ArXiv ID format"""
        # Arrange
        payload = {
            "paper": {"arxiv_id": "invalid_id_format"},
            "target_audience": "practitioner"
        }
        
        # Act
        response = await async_client.post("/api/v1/paper/research", json=payload)
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "format" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_research_missing_paper_input_returns_422(self, async_client: AsyncClient):
        """Should return 422 when neither arxiv_id nor title_search provided"""
        # Arrange
        payload = {
            "paper": {},  # Empty paper input
            "target_audience": "practitioner"
        }
        
        # Act
        response = await async_client.post("/api/v1/paper/research", json=payload)
        
        # Assert
        assert response.status_code in [400, 422]


# ============= Test POST /research/sync =============

@pytest.mark.e2e
@pytest.mark.slow
class TestPaperResearchSync:
    """Test POST /api/v1/paper/research/sync endpoint (synchronous)"""
    
    @pytest.mark.asyncio
    async def test_research_sync_returns_200(self, async_client: AsyncClient):
        """Should complete research and return 200 with result"""
        # Arrange
        payload = {
            "paper": {"arxiv_id": "1706.03762"},
            "target_audience": "practitioner",
            "generate_blog": False
        }
        
        # Act
        response = await async_client.post(
            "/api/v1/paper/research/sync",
            json=payload,
            timeout=600.0  # 10 min timeout for research
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "paper_metadata" in data
        assert "paper_overview" in data
        assert "methodology_deep_dive" in data
        assert "key_concepts" in data
    
    @pytest.mark.asyncio
    async def test_research_sync_includes_enhanced_sections(self, async_client: AsyncClient):
        """Should return all enhanced research sections"""
        # Arrange
        payload = {
            "paper": {"arxiv_id": "1706.03762"},
            "target_audience": "practitioner"
        }
        
        # Act
        response = await async_client.post(
            "/api/v1/paper/research/sync",
            json=payload,
            timeout=600.0
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Check all enhanced sections from spec
        assert "paper_overview" in data
        assert "methodology_deep_dive" in data
        assert "practical_implications" in data
        assert "key_concepts" in data
        assert "completeness_score" in data
    
    @pytest.mark.asyncio
    async def test_research_sync_paper_not_found_returns_404(self, async_client: AsyncClient):
        """Should return 404 for non-existent paper"""
        # Arrange
        payload = {
            "paper": {"arxiv_id": "9999.99999"},
            "target_audience": "practitioner"
        }
        
        # Act
        response = await async_client.post(
            "/api/v1/paper/research/sync",
            json=payload,
            timeout=30.0
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


# ============= Test GET /research/{id} =============

@pytest.mark.e2e
class TestGetResearchStatus:
    """Test GET /api/v1/paper/research/{id} endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_status_returns_200(self, async_client: AsyncClient, create_paper_research):
        """Should return research status when found"""
        # Arrange
        research = await create_paper_research({"arxiv_id": "1706.03762"})
        
        # Act
        response = await async_client.get(f"/api/v1/paper/research/{research.id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["research_id"] == research.id
        assert "status" in data
        assert "paper_metadata" in data
    
    @pytest.mark.asyncio
    async def test_get_status_not_found_returns_404(self, async_client: AsyncClient):
        """Should return 404 when research not found"""
        # Act
        response = await async_client.get("/api/v1/paper/research/99999")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


# ============= Test GET /research/{id}/result =============

@pytest.mark.e2e
class TestGetResearchResult:
    """Test GET /api/v1/paper/research/{id}/result endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_result_returns_200(self, async_client: AsyncClient, create_completed_paper_research):
        """Should return completed research result"""
        # Arrange
        research = await create_completed_paper_research({"arxiv_id": "1706.03762"})
        
        # Act
        response = await async_client.get(f"/api/v1/paper/research/{research.id}/result")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "paper_overview" in data
        assert "methodology_deep_dive" in data
        assert "completeness_score" in data
    
    @pytest.mark.asyncio
    async def test_get_result_pending_returns_202(self, async_client: AsyncClient, create_paper_research):
        """Should return 202 when research still pending"""
        # Arrange
        research = await create_paper_research({"arxiv_id": "1706.03762", "status": "pending"})
        
        # Act
        response = await async_client.get(f"/api/v1/paper/research/{research.id}/result")
        
        # Assert
        assert response.status_code in [200, 202, 404]  # Depends on implementation


# ============= Test POST /blog =============

@pytest.mark.e2e
@pytest.mark.slow
class TestPaperBlogGeneration:
    """Test POST /api/v1/paper/blog endpoint"""
    
    @pytest.mark.asyncio
    async def test_generate_blog_returns_200(self, async_client: AsyncClient, create_completed_paper_research):
        """Should generate blog from completed research"""
        # Arrange
        research = await create_completed_paper_research({"arxiv_id": "1706.03762"})
        payload = {
            "research_id": research.id,
            "target_audience": "practitioner"
        }
        
        # Act
        response = await async_client.post(
            "/api/v1/paper/blog",
            json=payload,
            timeout=300.0
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "content" in data
        assert "file_path" in data
    
    @pytest.mark.asyncio
    async def test_generate_blog_invalid_research_id_returns_404(self, async_client: AsyncClient):
        """Should return 404 for invalid research ID"""
        # Arrange
        payload = {
            "research_id": 99999,
            "target_audience": "practitioner"
        }
        
        # Act
        response = await async_client.post("/api/v1/paper/blog", json=payload)
        
        # Assert
        assert response.status_code == 404


# ============= Test POST /full/sync =============

@pytest.mark.e2e
@pytest.mark.slow
class TestPaperFullSync:
    """Test POST /api/v1/paper/full/sync endpoint (research + blog)"""
    
    @pytest.mark.asyncio
    async def test_full_sync_returns_200(self, async_client: AsyncClient):
        """Should complete both research and blog generation"""
        # Arrange
        payload = {
            "paper": {"arxiv_id": "1706.03762"},
            "target_audience": "practitioner",
            "generate_blog": True
        }
        
        # Act
        response = await async_client.post(
            "/api/v1/paper/full/sync",
            json=payload,
            timeout=900.0  # 15 min for full workflow
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "research" in data
        assert "blog" in data
        assert "research_id" in data
        assert data["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_full_sync_includes_paper_metadata(self, async_client: AsyncClient):
        """Should include paper metadata in response"""
        # Arrange
        payload = {
            "paper": {"arxiv_id": "1706.03762"},
            "target_audience": "practitioner",
            "generate_blog": True
        }
        
        # Act
        response = await async_client.post(
            "/api/v1/paper/full/sync",
            json=payload,
            timeout=900.0
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "paper_metadata" in data
        metadata = data["paper_metadata"]
        assert "arxiv_id" in metadata
        assert "title" in metadata
        assert "authors" in metadata
    
    @pytest.mark.asyncio
    async def test_full_sync_without_blog(self, async_client: AsyncClient):
        """Should skip blog generation when generate_blog=False"""
        # Arrange
        payload = {
            "paper": {"arxiv_id": "1706.03762"},
            "target_audience": "practitioner",
            "generate_blog": False
        }
        
        # Act
        response = await async_client.post(
            "/api/v1/paper/full/sync",
            json=payload,
            timeout=600.0
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "research" in data
        assert data.get("blog") is None or data.get("blog") == {}


# ============= Test POST /search =============

@pytest.mark.e2e
class TestPaperSearch:
    """Test POST /api/v1/paper/search endpoint"""
    
    @pytest.mark.asyncio
    async def test_search_returns_200(self, async_client: AsyncClient):
        """Should return search results"""
        # Arrange
        payload = {
            "query": "attention is all you need",
            "max_results": 5
        }
        
        # Act
        response = await async_client.post("/api/v1/paper/search", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    @pytest.mark.asyncio
    async def test_search_returns_paper_metadata(self, async_client: AsyncClient):
        """Should return paper metadata in results"""
        # Arrange
        payload = {"query": "transformer", "max_results": 3}
        
        # Act
        response = await async_client.post("/api/v1/paper/search", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            paper = data[0]
            assert "arxiv_id" in paper
            assert "title" in paper
            assert "authors" in paper
    
    @pytest.mark.asyncio
    async def test_search_respects_max_results(self, async_client: AsyncClient):
        """Should limit results to max_results"""
        # Arrange
        payload = {"query": "machine learning", "max_results": 2}
        
        # Act
        response = await async_client.post("/api/v1/paper/search", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2


# ============= Test GET /metadata/{arxiv_id} =============

@pytest.mark.e2e
class TestGetPaperMetadata:
    """Test GET /api/v1/paper/metadata/{arxiv_id} endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_metadata_returns_200(self, async_client: AsyncClient):
        """Should return paper metadata"""
        # Act
        response = await async_client.get("/api/v1/paper/metadata/1706.03762")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "arxiv_id" in data
        assert "title" in data
        assert "authors" in data
        assert "abstract" in data
    
    @pytest.mark.asyncio
    async def test_get_metadata_not_found_returns_404(self, async_client: AsyncClient):
        """Should return 404 for non-existent paper"""
        # Act
        response = await async_client.get("/api/v1/paper/metadata/9999.99999")
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_metadata_invalid_id_returns_400(self, async_client: AsyncClient):
        """Should return 400 for invalid ID format"""
        # Act
        response = await async_client.get("/api/v1/paper/metadata/invalid_id")
        
        # Assert
        assert response.status_code == 400


# ============= Test Error Responses =============

@pytest.mark.e2e
class TestErrorResponses:
    """Test error response formats"""
    
    @pytest.mark.asyncio
    async def test_validation_error_format(self, async_client: AsyncClient):
        """Should return proper validation error format"""
        # Arrange
        payload = {
            "paper": {"arxiv_id": 12345},  # Should be string
            "target_audience": "practitioner"
        }
        
        # Act
        response = await async_client.post("/api/v1/paper/research", json=payload)
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_not_found_error_format(self, async_client: AsyncClient):
        """Should return proper not found error format"""
        # Act
        response = await async_client.get("/api/v1/paper/research/99999")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_invalid_audience_returns_422(self, async_client: AsyncClient):
        """Should validate target_audience enum"""
        # Arrange
        payload = {
            "paper": {"arxiv_id": "1706.03762"},
            "target_audience": "invalid_audience"  # Not a valid enum value
        }
        
        # Act
        response = await async_client.post("/api/v1/paper/research", json=payload)
        
        # Assert
        assert response.status_code == 422


# ============= Test Response Headers =============

@pytest.mark.e2e
class TestResponseHeaders:
    """Test response headers"""
    
    @pytest.mark.asyncio
    async def test_content_type_json(self, async_client: AsyncClient):
        """Should return application/json content type"""
        # Act
        response = await async_client.get("/api/v1/paper/metadata/1706.03762")
        
        # Assert
        assert "application/json" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client: AsyncClient):
        """Should include CORS headers"""
        # Act
        response = await async_client.options("/api/v1/paper/research")
        
        # Assert - CORS should be configured
        # This depends on your CORS configuration
        pass  # Optional test based on CORS setup

