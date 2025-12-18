"""
LLM module for AWS Bedrock integration and prompt management
"""
from src.lib.llm.model import BedrockLLM, get_llm

# Import prompt classes
from src.lib.llm.prompts import (
    prompts,
    BasePrompt,
    ResearchPrompt,
    SynthesisPrompt,
    TopicCategorizationPrompt,
    BlogPrompt,
    LinkedInPostPrompt,
    TwitterThreadPrompt,
    BrandingPrompt,
    PaperResearchPrompt,
    PaperBlogPrompt,
    PromptRegistry,
)

# Import prompt utilities
from src.lib.llm.prompt_loader import (
    # Prompt class getters
    get_research_prompts,
    get_synthesis_prompts,
    get_topic_prompts,
    get_blog_prompts,
    get_linkedin_prompts,
    get_twitter_prompts,
    get_branding_prompts,
    get_paper_prompts,
    get_paper_blog_prompts,
    # Guidelines
    get_category_requirements,
    get_audience_guidelines,
    get_react_category_guidelines,
    CORE_AI_REQUIREMENTS,
    PRACTICAL_REQUIREMENTS,
    AUDIENCE_GUIDELINES,
    REACT_CATEGORY_GUIDELINES,
)

__all__ = [
    # LLM
    "BedrockLLM",
    "get_llm",
    # Prompt Classes (new)
    "prompts",
    "BasePrompt",
    "ResearchPrompt",
    "SynthesisPrompt",
    "TopicCategorizationPrompt",
    "BlogPrompt",
    "LinkedInPostPrompt",
    "TwitterThreadPrompt",
    "BrandingPrompt",
    "PaperResearchPrompt",
    "PaperBlogPrompt",
    "PromptRegistry",
    # Prompt getters
    "get_research_prompts",
    "get_synthesis_prompts",
    "get_topic_prompts",
    "get_blog_prompts",
    "get_linkedin_prompts",
    "get_twitter_prompts",
    "get_branding_prompts",
    "get_paper_prompts",
    "get_paper_blog_prompts",
    # Guidelines
    "get_category_requirements",
    "get_audience_guidelines",
    "get_react_category_guidelines",
    "CORE_AI_REQUIREMENTS",
    "PRACTICAL_REQUIREMENTS",
    "AUDIENCE_GUIDELINES",
    "REACT_CATEGORY_GUIDELINES",
]
