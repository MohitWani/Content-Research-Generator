"""
Prompt classes for AI Research Agent System
"""
from dataclasses import dataclass

from app.core.llm.prompts.base import BasePrompt
from app.core.llm.prompts.blog import BlogPrompt
from app.core.llm.prompts.branding import BrandingPrompt
from app.core.llm.prompts.paper import PaperBlogPrompt, PaperResearchPrompt
from app.core.llm.prompts.research import ResearchPrompt, SynthesisPrompt
from app.core.llm.prompts.social import LinkedInPostPrompt, TwitterThreadPrompt
from app.core.llm.prompts.topic import TopicCategorizationPrompt


@dataclass
class PromptRegistry:
    """Registry of all available prompts"""

    research: ResearchPrompt = None
    synthesis: SynthesisPrompt = None
    topic: TopicCategorizationPrompt = None
    blog: BlogPrompt = None
    linkedin: LinkedInPostPrompt = None
    twitter: TwitterThreadPrompt = None
    branding: BrandingPrompt = None
    paper: PaperResearchPrompt = None
    paper_blog: PaperBlogPrompt = None

    def __post_init__(self):
        self.research = ResearchPrompt()
        self.synthesis = SynthesisPrompt()
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
    'SynthesisPrompt',
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


