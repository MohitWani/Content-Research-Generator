"""
Research Prompts Module

Contains all prompts related to research operations:
- ResearchPrompt: For agentic research agent
- TopicCategorizationPrompt: For query categorization
"""
from dataclasses import dataclass

from app.modules.research.services.prompts.research_prompts import ResearchPrompt
from app.modules.research.services.prompts.topic_prompts import (
    TopicCategorizationPrompt,
)


@dataclass
class ResearchPromptRegistry:
    """Registry of research-related prompts"""

    research: ResearchPrompt = None
    topic: TopicCategorizationPrompt = None

    def __post_init__(self):
        self.research = ResearchPrompt()
        self.topic = TopicCategorizationPrompt()


# Singleton instance for research prompts
research_prompts = ResearchPromptRegistry()


__all__ = [
    "ResearchPrompt",
    "TopicCategorizationPrompt",
    "ResearchPromptRegistry",
    "research_prompts",
]
