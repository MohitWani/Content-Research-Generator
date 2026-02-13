"""
Research services module.

Contains:
- Agents: AgenticResearcher, TopicAgent
- Services: ResearchService, ResearchWorkflowService, BackgroundTaskService
- Nodes: ResearchAgentNode, TopicAgentNode
- Parsers: ResearchOutputParser
- Tools: Research tools factory
- Data: ResearchDataService
- Prompts: Research prompts
"""
# Agents
from app.modules.research.services.agentic_researcher import (
    AgenticResearcher,
    get_agentic_researcher,
)
from app.modules.research.services.topic_agent import TopicAgent, get_topic_agent

# Services
from app.modules.research.services.background_task_service import BackgroundTaskService
from app.modules.research.services.research_data_service import ResearchDataService
from app.modules.research.services.research_service import ResearchService
from app.modules.research.services.research_workflow_service import (
    ResearchWorkflowService,
)

# Nodes
from app.modules.research.services.nodes import ResearchAgentNode, TopicAgentNode

# Parsers
from app.modules.research.services.parsers import ResearchOutputParser

# Tools
from app.modules.research.services.tools import SOURCE_TYPE_MAPPING, create_research_tools

# Prompts
from app.modules.research.services.prompts import (
    ResearchPrompt,
    TopicCategorizationPrompt,
    research_prompts,
)

# Schemas (re-export for convenience)
from app.modules.research.schemas.agent_schemas import ResearchOutput

__all__ = [
    # Agents
    "AgenticResearcher",
    "get_agentic_researcher",
    "TopicAgent",
    "get_topic_agent",
    # Services
    "ResearchService",
    "ResearchWorkflowService",
    "BackgroundTaskService",
    "ResearchDataService",
    # Nodes
    "ResearchAgentNode",
    "TopicAgentNode",
    # Parsers
    "ResearchOutputParser",
    # Tools
    "create_research_tools",
    "SOURCE_TYPE_MAPPING",
    # Prompts
    "ResearchPrompt",
    "TopicCategorizationPrompt",
    "research_prompts",
    # Schemas
    "ResearchOutput",
]
