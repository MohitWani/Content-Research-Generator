"""
Base prompt class for research prompts
"""
from abc import ABC, abstractmethod


class BasePrompt(ABC):
    """
    Base class for all prompts.
    Provides structure for system_prompt and user_prompt separation.
    """

    @abstractmethod
    def system_prompt(self, **kwargs) -> str:
        """Return the system prompt with optional formatting"""
        pass

    @abstractmethod
    def user_prompt(self, **kwargs) -> str:
        """Return the user prompt with optional formatting"""
        pass

    def format(self, template: str, **kwargs) -> str:
        """Safely format a template with kwargs"""
        try:
            return template.format(**kwargs)
        except KeyError:
            return template
