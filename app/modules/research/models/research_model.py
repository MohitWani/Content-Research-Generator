"""
Database models for Research and Content entities
"""
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class TopicCategory(str, enum.Enum):
    """Topic categorization for research queries"""

    CORE_AI = 'core_ai'
    PRACTICAL_IMPLEMENTATION = 'practical_implementation'
    SOFTWARE_DEVELOPMENT = 'software_development'
    WEB_DEVELOPMENT = 'web_development'
    DEVOPS = 'devops'
    GENERAL_TECH = 'general_tech'


class ResearchQuery(Base):
    """Represents a user's research query"""

    __tablename__ = 'research_queries'

    id: Mapped[int] = mapped_column(primary_key=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    topic_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(
        String(50), default='practitioner'
    )
    content_type: Mapped[Optional[str]] = mapped_column(String(50), default='blog')
    status: Mapped[str] = mapped_column(String(20), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    research_results: Mapped[List['ResearchResult']] = relationship(
        'ResearchResult', back_populates='query', cascade='all, delete-orphan'
    )
    content_items: Mapped[List['ContentItem']] = relationship(
        'ContentItem', back_populates='research_query', cascade='all, delete-orphan'
    )


class ResearchResult(Base):
    """Stores research results from the research agent"""

    __tablename__ = 'research_results'

    id: Mapped[int] = mapped_column(primary_key=True)
    query_id: Mapped[int] = mapped_column(
        ForeignKey('research_queries.id'), nullable=False
    )
    topic_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_concepts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    mathematical_foundations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    historical_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    implementation_examples: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sources: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    research_data_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    completeness_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    query: Mapped['ResearchQuery'] = relationship(
        'ResearchQuery', back_populates='research_results'
    )


class ContentItem(Base):
    """Stores generated content (blogs, posts, etc.)"""

    __tablename__ = 'content_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    research_query_id: Mapped[int] = mapped_column(
        ForeignKey('research_queries.id'), nullable=False
    )
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='draft')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    research_query: Mapped['ResearchQuery'] = relationship(
        'ResearchQuery', back_populates='content_items'
    )


class PipelineExecution(Base):
    """Tracks pipeline execution status and data"""

    __tablename__ = 'pipeline_executions'

    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_type: Mapped[str] = mapped_column(String(100), nullable=False)
    research_query_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('research_queries.id'), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


