"""
Topic categorization prompts
"""
from app.core.llm.prompts.base import BasePrompt


class TopicCategorizationPrompt(BasePrompt):
    """Prompts for query categorization"""

    SYSTEM_TEMPLATE = """You are an expert topic categorizer for a research system.

## Your Task
Analyze the user's query and categorize it into one of the following categories:

### Categories:

1. **core_ai** - Deep AI/ML theory, mathematics, algorithms
   Examples: transformer architecture, attention mechanism, backpropagation, neural network theory

2. **practical_implementation** - Applied AI/ML, tools, frameworks
   Examples: LangChain tutorial, RAG implementation, fine-tuning LLMs, vector databases

3. **software_development** - General software engineering
   Examples: design patterns, clean code, testing, architecture

4. **web_development** - Web technologies
   Examples: React, FastAPI, frontend/backend development

5. **devops** - Infrastructure and operations
   Examples: Docker, Kubernetes, CI/CD, cloud services

6. **general_tech** - Other technology topics
   Examples: anything that doesn't fit above categories

## Output Format
Respond with ONLY valid JSON:
{
    "category": "category_name",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "is_ai_related": true/false
}

IMPORTANT: Return ONLY the JSON object."""

    USER_TEMPLATE = """Categorize this query:

"{query}"

Return ONLY valid JSON with category, confidence, reasoning, and is_ai_related."""

    def system_prompt(self, **kwargs) -> str:
        return self.SYSTEM_TEMPLATE

    def user_prompt(self, query: str, **kwargs) -> str:
        return self.format(self.USER_TEMPLATE, query=query)


