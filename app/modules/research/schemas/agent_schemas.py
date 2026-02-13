"""
Pydantic schemas for Research Agent components.
Contains schemas for agent output, tool calls, and internal data structures.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============= Tool Related Schemas =============


class ToolCallSchema(BaseModel):
    """Schema for a tool call made by the agent"""

    tool: str = Field(..., description="Name of the tool called")
    query: str = Field(..., description="Query or arguments passed to the tool")
    type: str = Field(default="web", description="Type of source (web, paper, github, etc.)")


class ToolResultSchema(BaseModel):
    """Schema for a tool result"""

    tool: str = Field(..., description="Name of the tool that produced the result")
    content: str = Field(..., description="Content returned by the tool")


# ============= Agent Output Schemas =============


class ResearchOutput(BaseModel):
    """Structured output from research agent"""

    topic_summary: str = Field(
        default="",
        description="Comprehensive topic summary",
    )
    key_concepts: Dict[str, str] = Field(
        default_factory=dict,
        description="Key concepts with explanations",
    )
    mathematical_foundations: Optional[str] = Field(
        None,
        description="Mathematical foundations and formulas",
    )
    source_descriptions: Optional[str] = Field(
        None,
        description="Synthesized summary of sources",
    )
    implementation_examples: Optional[str] = Field(
        None,
        description="Code examples and implementations",
    )
    sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of sources used in research",
    )
    research_data_path: Optional[str] = Field(
        None,
        description="Path to saved research data file",
    )
    completeness_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Research completeness score (0-1)",
    )


class ParsedAgentResponse(BaseModel):
    """Parsed response from agent messages"""

    tool_calls: List[ToolCallSchema] = Field(
        default_factory=list,
        description="List of tool calls made by the agent",
    )
    tool_results: List[ToolResultSchema] = Field(
        default_factory=list,
        description="List of tool results received",
    )
    final_content: str = Field(
        default="",
        description="Final content from the agent",
    )


# ============= Agent Configuration Schemas =============


class AgentConfig(BaseModel):
    """Configuration for the research agent"""

    max_iterations: int = Field(
        default=5,
        ge=1,
        le=25,
        description="Maximum number of agent iterations",
    )
    recursion_limit: int = Field(
        default=25,
        ge=5,
        le=100,
        description="Recursion limit for agent execution",
    )


class ResearchRequest(BaseModel):
    """Internal request schema for research execution"""

    query: str = Field(..., description="The research query")
    category: str = Field(..., description="Topic category")
    target_audience: str = Field(
        default="practitioner",
        description="Target audience for the research",
    )
    max_iterations: int = Field(
        default=10,
        description="Maximum iterations for the agent",
    )
