"""
Prompt template loading and formatting utilities
"""
from pathlib import Path
from typing import Dict, Optional

from src.common.logger import setup_logger

logger = setup_logger(__name__)


# Directory containing prompt templates
PROMPTS_DIR = Path(__file__).parent / "prompts"


class PromptLoader:
    """
    Loads and formats prompt templates from files
    """
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize prompt loader
        
        Args:
            prompts_dir: Directory containing prompt templates (defaults to prompts/)
        """
        self.prompts_dir = prompts_dir or PROMPTS_DIR
        self._cache: Dict[str, str] = {}
    
    def load(self, prompt_name: str) -> str:
        """
        Load a prompt template by name
        
        Args:
            prompt_name: Name of the prompt file (without .txt extension)
        
        Returns:
            Prompt template string
        
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        # Check cache first
        if prompt_name in self._cache:
            return self._cache[prompt_name]
        
        # Load from file
        prompt_file = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
        
        prompt_content = prompt_file.read_text(encoding="utf-8")
        
        # Cache the prompt
        self._cache[prompt_name] = prompt_content
        
        logger.debug(f"Loaded prompt template: {prompt_name}")
        
        return prompt_content
    
    def format(self, prompt_name: str, **kwargs) -> str:
        """
        Load and format a prompt template with variables
        
        Args:
            prompt_name: Name of the prompt file
            **kwargs: Variables to substitute in the template
        
        Returns:
            Formatted prompt string
        """
        template = self.load(prompt_name)
        
        try:
            formatted = template.format(**kwargs)
            return formatted
        except KeyError as e:
            logger.error(f"Missing variable in prompt {prompt_name}: {e}")
            raise ValueError(f"Missing required variable in prompt: {e}")
    
    def clear_cache(self):
        """Clear the prompt cache"""
        self._cache.clear()
        logger.debug("Prompt cache cleared")


# Singleton instance
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """Get or create the singleton prompt loader instance"""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


def load_prompt(prompt_name: str, **kwargs) -> str:
    """
    Convenience function to load and format a prompt
    
    Args:
        prompt_name: Name of the prompt file (without .txt extension)
        **kwargs: Variables to substitute in the template
    
    Returns:
        Formatted prompt string
    """
    loader = get_prompt_loader()
    if kwargs:
        return loader.format(prompt_name, **kwargs)
    return loader.load(prompt_name)


# Category-specific research requirements
CORE_AI_REQUIREMENTS = """
For this CORE AI topic, ensure your research includes:
1. **Mathematical Foundations**: Include relevant formulas, equations, and mathematical explanations
2. **Historical Context**: Trace the evolution of this concept and key milestones
3. **Simple Explanation**: Provide an accessible explanation for learning purposes
4. **Python Implementation**: Include working code examples demonstrating the concepts
5. **Academic Sources**: Reference relevant research papers and academic resources
"""

PRACTICAL_REQUIREMENTS = """
For this PRACTICAL IMPLEMENTATION topic, ensure your research includes:
1. **Step-by-Step Guide**: Provide clear, actionable instructions
2. **Deep Technical Information**: Include comprehensive technical details
3. **Code Examples**: Include working, production-ready code snippets
4. **Best Practices**: Highlight common patterns and recommendations
5. **Troubleshooting**: Address common issues and their solutions
"""


# Audience-specific guidelines
AUDIENCE_GUIDELINES = {
    "beginner": """
## Beginner Audience Guidelines
- Use simple, clear language
- Include analogies to familiar concepts
- Define technical terms when first used
- Keep code examples simple and well-commented
- Focus on "why" before "how"
""",
    "practitioner": """
## Practitioner Audience Guidelines
- Balance theory with practical application
- Include production-ready code examples
- Reference industry best practices
- Assume familiarity with basic concepts
- Focus on implementation details
""",
    "expert": """
## Expert Audience Guidelines
- Include advanced technical details
- Reference academic literature
- Discuss edge cases and optimizations
- Assume deep domain knowledge
- Focus on cutting-edge developments
""",
}


def get_category_requirements(category: str) -> str:
    """Get research requirements based on topic category"""
    if category == "core_ai":
        return CORE_AI_REQUIREMENTS
    return PRACTICAL_REQUIREMENTS


def get_audience_guidelines(audience: str) -> str:
    """Get audience-specific guidelines"""
    return AUDIENCE_GUIDELINES.get(audience, AUDIENCE_GUIDELINES["practitioner"])

