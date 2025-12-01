"""
Shared test fixtures for all test types
Uses real PostgreSQL database and real AWS Bedrock LLM (with rate limiting)
"""
import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import os
from pathlib import Path

# Import models and database
from src.common.database import Base
from src.lib.models.research import (
    ResearchQuery,
    ResearchResult,
    ContentItem,
    PipelineExecution,
    TopicCategory,
)


# Database fixtures
@pytest.fixture(scope="session")
def db_url():
    """Test database URL - uses real PostgreSQL"""
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_research_db"
    )


@pytest_asyncio.fixture(scope="session")
async def engine(db_url):
    """Create test database engine"""
    engine = create_async_engine(db_url, poolclass=NullPool, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session with transaction rollback"""
    async_session = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


# LLM fixtures
@pytest.fixture
def llm_config():
    """LLM configuration for testing"""
    return {
        "model_id": os.getenv(
            "BEDROCK_MODEL_ID",
            "anthropic.claude-3-5-sonnet-20241022-v2:0"
        ),
        "region": os.getenv("AWS_REGION", "us-east-1"),
        "max_tokens": 4096,
        "temperature": 0.7,
    }


@pytest_asyncio.fixture
async def llm(llm_config):
    """Real AWS Bedrock LLM instance (with rate limiting for tests)"""
    from src.lib.llm.model import BedrockLLM
    return BedrockLLM(**llm_config)


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# Helper fixtures for test data
@pytest.fixture
def sample_research_query():
    """Sample research query data"""
    return {
        "query_text": "What are transformers in deep learning?",
        "target_audience": "practitioner",
        "content_type": "blog",
    }


@pytest.fixture
def sample_core_ai_query():
    """Sample core AI topic query"""
    return {
        "query_text": "Explain the attention mechanism in transformers",
        "target_audience": "expert",
        "content_type": "blog",
    }


@pytest.fixture
def sample_practical_query():
    """Sample practical implementation query"""
    return {
        "query_text": "How to use LangChain for building RAG applications?",
        "target_audience": "practitioner",
        "content_type": "blog",
    }


@pytest.fixture
def sample_research_result():
    """Sample research result data"""
    return {
        "topic_summary": "Transformers are a type of neural network architecture...",
        "key_concepts": {
            "attention": "Mechanism for focusing on relevant parts of input",
            "self-attention": "Attention mechanism applied to same sequence",
        },
        "mathematical_foundations": "The attention mechanism computes...",
        "historical_context": "Transformers were introduced in 2017...",
        "implementation_examples": "```python\nimport torch\n...\n```",
        "sources": [
            {"type": "paper", "title": "Attention Is All You Need", "url": "https://arxiv.org/abs/1706.03762"},
            {"type": "web", "title": "Transformer Architecture", "url": "https://example.com"},
        ],
        "completeness_score": 0.92,
    }


@pytest.fixture
def sample_blog_content():
    """Sample blog post content"""
    return {
        "title": "Understanding Transformers: A Deep Dive",
        "content": "# Introduction\n\nTransformers have revolutionized...",
        "target_audience": "practitioner",
        "tone": "professional",
        "status": "draft",
    }


@pytest.fixture
def mock_arxiv_response():
    """Mock ArXiv API response"""
    return {
        "feed": {
            "entry": [
                {
                    "id": "http://arxiv.org/abs/1706.03762v1",
                    "title": "Attention Is All You Need",
                    "summary": "We propose a new simple network architecture...",
                    "authors": [{"name": "Vaswani, Ashish"}],
                    "published": "2017-06-12",
                }
            ]
        }
    }


@pytest.fixture
def mock_github_response():
    """Mock GitHub API response"""
    return {
        "items": [
            {
                "id": 123456,
                "name": "awesome-transformer",
                "full_name": "user/awesome-transformer",
                "description": "A collection of transformer implementations",
                "stargazers_count": 1000,
                "html_url": "https://github.com/user/awesome-transformer",
            }
        ]
    }


@pytest.fixture
def voice_profile_path(tmp_path):
    """Create temporary voice.json profile for testing"""
    voice_data = {
        "tone": "professional",
        "style": "technical",
        "voice_characteristics": {
            "formality": "high",
            "technical_depth": "medium",
            "humor": "low",
        }
    }
    
    import json
    voice_file = tmp_path / "voice.json"
    voice_file.write_text(json.dumps(voice_data))
    return str(voice_file)


# Factory fixtures for creating test entities
@pytest_asyncio.fixture
async def create_test_research_query(db_session):
    """Factory fixture for creating test research queries"""
    async def _create(data: dict = None) -> ResearchQuery:
        default_data = {
            "query_text": "Test query",
            "target_audience": "practitioner",
            "status": "pending",
        }
        if data:
            default_data.update(data)
        
        query = ResearchQuery(**default_data)
        db_session.add(query)
        await db_session.flush()
        await db_session.refresh(query)
        return query
    return _create


@pytest_asyncio.fixture
async def create_test_research_result(db_session, create_test_research_query):
    """Factory fixture for creating test research results"""
    async def _create(query_id: int = None, data: dict = None) -> ResearchResult:
        if query_id is None:
            query = await create_test_research_query()
            query_id = query.id
        
        default_data = {
            "query_id": query_id,
            "topic_summary": "Test summary",
            "key_concepts": {"concept": "explanation"},
            "sources": [],
            "research_data_path": "/data/research/test",
        }
        if data:
            default_data.update(data)
        
        result = ResearchResult(**default_data)
        db_session.add(result)
        await db_session.flush()
        await db_session.refresh(result)
        return result
    return _create


@pytest_asyncio.fixture
async def create_test_content_item(db_session, create_test_research_query):
    """Factory fixture for creating test content items"""
    async def _create(query_id: int = None, data: dict = None) -> ContentItem:
        if query_id is None:
            query = await create_test_research_query()
            query_id = query.id
        
        default_data = {
            "research_query_id": query_id,
            "content_type": "blog",
            "title": "Test Blog",
            "content": "Test content",
            "file_path": "/data/content/test.md",
            "status": "draft",
        }
        if data:
            default_data.update(data)
        
        content = ContentItem(**default_data)
        db_session.add(content)
        await db_session.flush()
        await db_session.refresh(content)
        return content
    return _create
