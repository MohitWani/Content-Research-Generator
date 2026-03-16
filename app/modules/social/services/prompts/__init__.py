"""
Social Prompts Module

Contains all prompts related to social content generation:
- LinkedInPrompt: For LinkedIn post generation
"""
from dataclasses import dataclass

from app.modules.social.services.prompts.linkedin_prompts import LinkedInPrompt


@dataclass
class SocialPromptRegistry:
    """Registry of social-related prompts"""

    linkedin: LinkedInPrompt = None

    def __post_init__(self):
        self.linkedin = LinkedInPrompt()


# Singleton instance for social prompts
social_prompts = SocialPromptRegistry()


__all__ = [
    "LinkedInPrompt",
    "SocialPromptRegistry",
    "social_prompts",
]
