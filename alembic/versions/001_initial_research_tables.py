"""Initial research tables

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create research_queries table - using VARCHAR for topic_category for flexibility
    op.create_table(
        'research_queries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('topic_category', sa.String(length=50), nullable=True),
        sa.Column('target_audience', sa.String(length=50), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for research_queries
    op.create_index(
        'idx_research_queries_status', 
        'research_queries', 
        ['status']
    )
    op.create_index(
        'idx_research_queries_created_at', 
        'research_queries', 
        ['created_at']
    )
    
    # Create research_results table
    op.create_table(
        'research_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=False),
        sa.Column('topic_summary', sa.Text(), nullable=True),
        sa.Column('key_concepts', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('mathematical_foundations', sa.Text(), nullable=True),
        sa.Column('historical_context', sa.Text(), nullable=True),
        sa.Column('implementation_examples', sa.Text(), nullable=True),
        sa.Column('sources', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('research_data_path', sa.String(length=500), nullable=True),
        sa.Column('completeness_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['query_id'], ['research_queries.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for research_results
    op.create_index(
        'idx_research_results_query_id', 
        'research_results', 
        ['query_id']
    )
    
    # Create content_items table
    op.create_table(
        'content_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('research_query_id', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('target_audience', sa.String(length=50), nullable=True),
        sa.Column('tone', sa.String(length=50), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['research_query_id'], ['research_queries.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for content_items
    op.create_index(
        'idx_content_items_research_query_id', 
        'content_items', 
        ['research_query_id']
    )
    
    # Create pipeline_executions table
    op.create_table(
        'pipeline_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pipeline_type', sa.String(length=100), nullable=False),
        sa.Column('research_query_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['research_query_id'], ['research_queries.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for pipeline_executions
    op.create_index(
        'idx_pipeline_executions_status', 
        'pipeline_executions', 
        ['status']
    )


def downgrade() -> None:
    # Drop tables
    op.drop_index('idx_pipeline_executions_status', table_name='pipeline_executions')
    op.drop_table('pipeline_executions')
    
    op.drop_index('idx_content_items_research_query_id', table_name='content_items')
    op.drop_table('content_items')
    
    op.drop_index('idx_research_results_query_id', table_name='research_results')
    op.drop_table('research_results')
    
    op.drop_index('idx_research_queries_created_at', table_name='research_queries')
    op.drop_index('idx_research_queries_status', table_name='research_queries')
    op.drop_table('research_queries')

