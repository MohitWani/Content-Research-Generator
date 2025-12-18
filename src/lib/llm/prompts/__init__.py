"""
Prompt classes for AI Research Agent System
Clean, modular prompt structure with system_prompt and user_prompt methods
"""
from dataclasses import dataclass

# Import all prompt classes from modules
from src.lib.llm.prompts.base import BasePrompt
from src.lib.llm.prompts.research import ResearchPrompt, SynthesisPrompt
from src.lib.llm.prompts.topic import TopicCategorizationPrompt
from src.lib.llm.prompts.blog import BlogPrompt
from src.lib.llm.prompts.social import LinkedInPostPrompt, TwitterThreadPrompt
from src.lib.llm.prompts.branding import BrandingPrompt
from src.lib.llm.prompts.paper import PaperResearchPrompt, PaperBlogPrompt


@dataclass
class PromptRegistry:
    """
    Registry of all available prompts
    Provides factory access to prompt instances
    """
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
    # Base
    "BasePrompt",
    # Research
    "ResearchPrompt",
    "SynthesisPrompt",
    # Topic
    "TopicCategorizationPrompt",
    # Blog
    "BlogPrompt",
    # Social
    "LinkedInPostPrompt",
    "TwitterThreadPrompt",
    # Branding
    "BrandingPrompt",
    # Paper
    "PaperResearchPrompt",
    "PaperBlogPrompt",
    # Registry
    "PromptRegistry",
    "prompts",
]
