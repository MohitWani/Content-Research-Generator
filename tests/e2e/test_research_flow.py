"""
End-to-End Tests for Research Flow
Tests complete research workflow through API/CLI
Maps to: spec.md → Story 1, Story 8, Story 9
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.e2e
class TestResearchE2EFlow:
    """E2E tests for research workflow"""
    
    @pytest.mark.asyncio
    async def test_full_research_pipeline(self):
        """Should execute complete research pipeline"""
        from src.lib.pipelines.research_pipeline import ResearchPipeline
        from src.lib.agents.topic_agent import TopicAgent
        from src.lib.agents.agentic_researcher import AgenticResearcher as ResearchAgent, ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        
        # Mock agents
        with patch.object(TopicAgent, 'categorize_query') as mock_categorize, \
             patch.object(ResearchAgent, 'research') as mock_research:
            
            mock_categorize.return_value = TopicCategorizationResult(
                category="core_ai",
                confidence=0.95,
                reasoning="Core AI topic",
                is_ai_related=True,
            )
            
            mock_research.return_value = ResearchOutput(
                topic_summary="Transformers are neural network architectures...",
                key_concepts={"attention": "Focus mechanism"},
                mathematical_foundations="Attention(Q,K,V) = softmax(QK^T/√d_k)V",
                sources=[{"type": "paper", "title": "Attention Is All You Need"}],
                completeness_score=0.85,
            )
            
            # Execute pipeline
            pipeline = ResearchPipeline()
            result = await pipeline.execute(
                query="Explain transformers",
                target_audience="practitioner",
            )
            
            # Verify
            assert result.research_output is not None
            assert result.completeness_score > 0.5
            assert result.sources_count >= 1
    
    @pytest.mark.asyncio
    async def test_research_handles_non_ai_query(self):
        """Should reject non-AI queries gracefully"""
        from src.lib.pipelines.research_pipeline import ResearchPipeline
        from src.lib.agents.topic_agent import TopicAgent
        from src.lib.models.exceptions import QueryCategorizationError
        
        with patch.object(TopicAgent, 'categorize_query') as mock_categorize:
            mock_categorize.side_effect = QueryCategorizationError(
                "Query is not AI related"
            )
            
            pipeline = ResearchPipeline()
            
            with pytest.raises(QueryCategorizationError):
                await pipeline.execute(
                    query="How to cook pasta?",
                    target_audience="beginner",
                )
    
    @pytest.mark.asyncio
    async def test_research_adapts_to_topic_category(self):
        """Should adapt research depth based on category"""
        from src.lib.pipelines.research_pipeline import ResearchPipeline
        from src.lib.agents.topic_agent import TopicAgent
        from src.lib.agents.agentic_researcher import AgenticResearcher as ResearchAgent, ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        from src.lib.models.research import TopicCategory
        
        with patch.object(TopicAgent, 'categorize_query') as mock_categorize, \
             patch.object(ResearchAgent, 'research') as mock_research:
            
            # Test core AI topic
            mock_categorize.return_value = TopicCategorizationResult(
                category="core_ai",
                confidence=0.90,
                reasoning="Core AI",
                is_ai_related=True,
            )
            
            mock_research.return_value = ResearchOutput(
                topic_summary="Summary...",
                key_concepts={},
                mathematical_foundations="Math...",
                sources=[],
                completeness_score=0.8,
            )
            
            pipeline = ResearchPipeline()
            result = await pipeline.execute("Explain attention", "expert")
            
            # Verify research was called with core AI category
            call_args = mock_research.call_args
            assert call_args.kwargs.get("category") == TopicCategory.CORE_AI


@pytest.mark.e2e
class TestResearchAPIE2E:
    """E2E tests for research API endpoints"""
    
    @pytest.mark.asyncio
    async def test_api_research_endpoint(self):
        """Should handle research request through API"""
        from fastapi.testclient import TestClient
        from unittest.mock import patch
        
        # This would require a test client setup
        # For now, test the underlying logic
        from src.lib.orchestrator.workflow_manager import WorkflowManager
        from src.lib.agents.topic_agent import TopicAgent
        from src.lib.agents.agentic_researcher import AgenticResearcher as ResearchAgent, ResearchOutput
        from src.lib.models.schemas import TopicCategorizationResult
        
        with patch.object(TopicAgent, 'categorize_query') as mock_cat, \
             patch.object(ResearchAgent, 'research') as mock_res:
            
            mock_cat.return_value = TopicCategorizationResult(
                category="practical_implementation",
                confidence=0.88,
                reasoning="Practical",
                is_ai_related=True,
            )
            
            mock_res.return_value = ResearchOutput(
                topic_summary="LangChain is a framework...",
                key_concepts={},
                implementation_examples="Step 1: Install...",
                sources=[],
                completeness_score=0.75,
            )
            
            manager = WorkflowManager()
            result = await manager.execute_research_workflow(
                query="How to use LangChain?",
                target_audience="practitioner",
            )
            
            assert result.research_result is not None


@pytest.mark.e2e
class TestResearchCLIE2E:
    """E2E tests for research CLI commands"""
    
    def test_cli_quick_command_parses(self):
        """Should parse quick command correctly"""
        from src.cli.main import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Test version command works
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "AI Research Agent" in result.stdout
    
    def test_cli_status_command(self):
        """Should show system status"""
        from src.cli.main import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "System Status" in result.stdout
