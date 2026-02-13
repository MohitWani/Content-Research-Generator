"""
Prompt classes for AI Research Agent System

Note: Research-related prompts (ResearchPrompt, TopicCategorizationPrompt)
have been moved to app.modules.research.services.prompts for better module separation.
They are re-exported here for backward compatibility.
"""
from dataclasses import dataclass

from app.core.llm.prompts.base import BasePrompt
from app.core.llm.prompts.blog import BlogPrompt
from app.core.llm.prompts.branding import BrandingPrompt
from app.core.llm.prompts.paper import PaperBlogPrompt, PaperResearchPrompt
from app.core.llm.prompts.social import LinkedInPostPrompt, TwitterThreadPrompt

# Import research prompts from their new location
from app.modules.research.services.prompts import (
    ResearchPrompt,
    TopicCategorizationPrompt,
)


@dataclass
class PromptRegistry:
    """Registry of all available prompts"""

    research: ResearchPrompt = None
    topic: TopicCategorizationPrompt = None
    blog: BlogPrompt = None
    linkedin: LinkedInPostPrompt = None
    twitter: TwitterThreadPrompt = None
    branding: BrandingPrompt = None
    paper: PaperResearchPrompt = None
    paper_blog: PaperBlogPrompt = None

    def __post_init__(self):
        self.research = ResearchPrompt()
        self.topic = TopicCategorizationPrompt()
        self.blog = BlogPrompt()
        self.linkedin = LinkedInPostPrompt()
        self.twitter = TwitterThreadPrompt()
        self.branding = BrandingPrompt()
        self.paper = PaperResearchPrompt()
        self.paper_blog = PaperBlogPrompt()


# Singleton instance
prompts = PromptRegistry()


__all__ = [
    'BasePrompt',
    'ResearchPrompt',
    'TopicCategorizationPrompt',
    'BlogPrompt',
    'LinkedInPostPrompt',
    'TwitterThreadPrompt',
    'BrandingPrompt',
    'PaperResearchPrompt',
    'PaperBlogPrompt',
    'PromptRegistry',
    'prompts',
]


