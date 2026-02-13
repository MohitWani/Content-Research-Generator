"""
Content Prompts Module

Contains all prompts related to content generation:
- BlogPrompt: For blog generation from research data
"""
from dataclasses import dataclass

from app.modules.content.services.prompts.blog_prompts import BlogPrompt


@dataclass
class ContentPromptRegistry:
    """Registry of content-related prompts"""

    blog: BlogPrompt = None

    def __post_init__(self):
        self.blog = BlogPrompt()


# Singleton instance for content prompts
content_prompts = ContentPromptRegistry()


__all__ = [
    "BlogPrompt",
    "ContentPromptRegistry",
    "content_prompts",
]
