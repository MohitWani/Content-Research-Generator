"""
Integration tests for Database Models
Uses REAL PostgreSQL database (no mocking)
Tests model creation, relationships, and database persistence
Maps to: plan.md → Section 6 (Data Models)
"""
import pytest
from datetime import datetime
from sqlalchemy import select
from src.lib.models.research import (
    Base,
    ResearchQuery,
    ResearchResult,
    ContentItem,
    PipelineExecution,
    TopicCategory,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestResearchQueryModel:
    """Test ResearchQuery model with real database"""
    
    async def test_create_research_query(self, db_session):
        """Should create research query in database"""
        # Arrange
        query = ResearchQuery(
            query_text="What are transformers?",
            topic_category=TopicCategory.CORE_AI,
            target_audience="practitioner",
            status="pending",
        )
        
        # Act
        db_session.add(query)
        await db_session.commit()
        await db_session.refresh(query)
        
        # Assert
        assert query.id is not None
        assert query.query_text == "What are transformers?"
        assert query.topic_category == TopicCategory.CORE_AI
        assert query.created_at is not None
        assert query.updated_at is not None
    
    async def test_research_query_timestamps(self, db_session):
        """Should automatically set created_at and updated_at"""
        # Arrange
        query = ResearchQuery(
            query_text="Test query",
            status="pending",
        )
        
        # Act
        db_session.add(query)
        await db_session.commit()
        await db_session.refresh(query)
        
        # Assert
        assert query.created_at is not None
        assert query.updated_at is not None
        assert isinstance(query.created_at, datetime)
        assert isinstance(query.updated_at, datetime)
    
    async def test_research_query_enum_type(self, db_session):
        """Should store enum values correctly"""
        # Arrange
        query = ResearchQuery(
            query_text="Test",
            topic_category=TopicCategory.PRACTICAL_IMPLEMENTATION,
            status="pending",
        )
        
        # Act
        db_session.add(query)
        await db_session.commit()
        await db_session.refresh(query)
        
        # Assert
        assert query.topic_category == TopicCategory.PRACTICAL_IMPLEMENTATION
        assert isinstance(query.topic_category, TopicCategory)


@pytest.mark.integration
@pytest.mark.asyncio
class TestResearchResultModel:
    """Test ResearchResult model with real database"""
    
    async def test_create_research_result(self, db_session):
        """Should create research result linked to query"""
        # Arrange - create query first
        query = ResearchQuery(
            query_text="What are transformers?",
            status="completed",
        )
        db_session.add(query)
        await db_session.commit()
        await db_session.refresh(query)
        
        result = ResearchResult(
            query_id=query.id,
            topic_summary="Transformers are neural networks...",
            key_concepts={"attention": "Mechanism for focusing"},
            sources=[{"type": "paper", "title": "Attention Is All You Need"}],
            research_data_path="/data/research/1",
            completeness_score=0.92,
        )
        
        # Act
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)
        
        # Assert
        assert result.id is not None
        assert result.query_id == query.id
        assert result.completeness_score == 0.92
        assert len(result.sources) == 1
    
    async def test_research_result_relationship(self, db_session):
        """Should have relationship to ResearchQuery"""
        # Arrange
        query = ResearchQuery(
            query_text="Test",
            status="completed",
        )
        db_session.add(query)
        await db_session.commit()
        await db_session.refresh(query)
        
        result = ResearchResult(
            query_id=query.id,
            topic_summary="Summary",
            key_concepts={},
            sources=[],
            research_data_path="/data/research/1",
        )
        db_session.add(result)
        await db_session.commit()
        
        # Act - retrieve via relationship
        await db_session.refresh(query)
        
        # Assert
        assert len(query.research_results) == 1
        assert query.research_results[0].id == result.id
    
    async def test_research_result_json_fields(self, db_session):
        """Should store JSON fields correctly"""
        # Arrange
        query = ResearchQuery(query_text="Test", status="completed")
        db_session.add(query)
        await db_session.commit()
        await db_session.refresh(query)
        
        complex_key_concepts = {
            "attention": {
                "definition": "Mechanism for focusing",
                "importance": "high",
            },
            "self_attention": {
                "definition": "Attention on same sequence",
                "importance": "high",
            },
        }
        
        result = ResearchResult(
            query_id=query.id,
            topic_summary="Summary",
            key_concepts=complex_key_concepts,
            sources=[
                {"type": "paper", "title": "Paper 1", "url": "https://arxiv.org/abs/1"},
                {"type": "web", "title": "Article", "url": "https://example.com"},
            ],
            research_data_path="/data/research/1",
        )
        
        # Act
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)
        
        # Assert
        assert result.key_concepts["attention"]["importance"] == "high"
        assert len(result.sources) == 2


@pytest.mark.integration
@pytest.mark.asyncio
class TestContentItemModel:
    """Test ContentItem model with real database"""
    
    async def test_create_content_item(self, db_session):
        """Should create content item linked to research query"""
        # Arrange - create query first
        query = ResearchQuery(
            query_text="What are transformers?",
            status="completed",
        )
        db_session.add(query)
        await db_session.commit()
        await db_session.refresh(query)
        
        content = ContentItem(
            research_query_id=query.id,
            content_type="blog",
            title="Understanding Transformers",
            content="# Introduction\n\nTransformers are...",
            file_path="/data/content/blog_1.md",
            target_audience="practitioner",
            tone="professional",
            status="draft",
        )
        
        # Act
        db_session.add(content)
        await db_session.commit()
        await db_session.refresh(content)
        
        # Assert
        assert content.id is not None
        assert content.research_query_id == query.id
        assert content.content_type == "blog"
        assert len(content.content) > 0
    
    async def test_content_item_relationship(self, db_session):
        """Should have relationship to ResearchQuery"""
        # Arrange
        query = ResearchQuery(query_text="Test", status="completed")
        db_session.add(query)
        await db_session.commit()
        await db_session.refresh(query)
        
        content = ContentItem(
            research_query_id=query.id,
            content_type="blog",
            title="Test Blog",
            content="Content",
            file_path="/data/content/test.md",
        )
        db_session.add(content)
        await db_session.commit()
        
        # Act - retrieve via relationship
        await db_session.refresh(query)
        
        # Assert
        assert len(query.content_items) == 1
        assert query.content_items[0].id == content.id
    
    async def test_content_item_update_timestamp(self, db_session):
        """Should update updated_at on modification"""
        # Arrange
        query = ResearchQuery(query_text="Test", status="completed")
        db_session.add(query)
        await db_session.commit()
        await db_session.refresh(query)
        
        content = ContentItem(
            research_query_id=query.id,
            content_type="blog",
            title="Original Title",
            content="Original content",
            file_path="/data/content/test.md",
        )
        db_session.add(content)
        await db_session.commit()
        await db_session.refresh(content)
        
        original_updated_at = content.updated_at
        
        # Act - update content
        content.title = "Updated Title"
        await db_session.commit()
        await db_session.refresh(content)
        
        # Assert
        assert content.updated_at > original_updated_at


@pytest.mark.integration
@pytest.mark.asyncio
class TestPipelineExecutionModel:
    """Test PipelineExecution model with real database"""
    
    async def test_create_pipeline_execution(self, db_session):
        """Should create pipeline execution record"""
        # Arrange
        execution = PipelineExecution(
            pipeline_name="daily_research",
            status="running",
            execution_data={"topics": ["AI", "ML"]},
        )
        
        # Act
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)
        
        # Assert
        assert execution.id is not None
        assert execution.pipeline_name == "daily_research"
        assert execution.status == "running"
        assert execution.started_at is not None
        assert execution.execution_data["topics"] == ["AI", "ML"]
    
    async def test_pipeline_execution_completion(self, db_session):
        """Should update status and completion time"""
        # Arrange
        execution = PipelineExecution(
            pipeline_name="daily_research",
            status="running",
        )
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)
        
        # Act - mark as completed
        execution.status = "completed"
        execution.completed_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(execution)
        
        # Assert
        assert execution.status == "completed"
        assert execution.completed_at is not None
    
    async def test_pipeline_execution_error_handling(self, db_session):
        """Should store error messages"""
        # Arrange
        execution = PipelineExecution(
            pipeline_name="daily_research",
            status="failed",
            error_message="API rate limit exceeded",
        )
        
        # Act
        db_session.add(execution)
        await db_session.commit()
        await db_session.refresh(execution)
        
        # Assert
        assert execution.status == "failed"
        assert execution.error_message == "API rate limit exceeded"

