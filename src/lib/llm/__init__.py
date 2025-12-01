"""
LLM module for AWS Bedrock integration and prompt management
"""
from src.lib.llm.model import BedrockLLM, get_llm
from src.lib.llm.prompt_loader import (
    PromptLoader,
    get_prompt_loader,
    load_prompt,
    get_category_requirements,
    get_audience_guidelines,
    CORE_AI_REQUIREMENTS,
    PRACTICAL_REQUIREMENTS,
    AUDIENCE_GUIDELINES,
)

__all__ = [
    # LLM
    "BedrockLLM",
    "get_llm",
    # Prompt loading
    "PromptLoader",
    "get_prompt_loader",
    "load_prompt",
    "get_category_requirements",
    "get_audience_guidelines",
    "CORE_AI_REQUIREMENTS",
    "PRACTICAL_REQUIREMENTS",
    "AUDIENCE_GUIDELINES",
]
