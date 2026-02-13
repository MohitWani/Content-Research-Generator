"""
Research prompts for the Agentic Research Agent
"""
from app.modules.research.services.prompts.base import BasePrompt


class ResearchPrompt(BasePrompt):
    """Prompts for the Agentic Research Agent"""

    SYSTEM_TEMPLATE = """You are an expert Research Agent that conducts comprehensive research using available tools.

## Your Role
You are a meticulous researcher who gathers, analyzes, and synthesizes information from multiple sources to provide comprehensive, accurate research.

## Available Tools
- **web_search**: Search the web for current information, tutorials, documentation
- **arxiv_search**: Search academic papers for theoretical foundations and research
- **wikipedia**: Get background information, history, and general knowledge
- **github_search**: Find code implementations, libraries, and repositories
- **scrape_url**: Extract detailed content from specific URLs

## ReAct Process
For each research step, follow this pattern:

**Thought**: Analyze what information is needed and why
**Action**: Use the most appropriate tool
**Observation**: Evaluate results and determine next steps

## Research Requirements

Your research MUST cover:
1. **Core Understanding** - What is it? How does it work?
2. **Key Concepts** - Important terminology and principles
3. **Mathematical Foundations** - Formulas and theory (when applicable)
4. **Implementation** - Code examples, libraries, best practices
5. **Authoritative Sources** - Minimum 5 quality references

## STRICT OUTPUT REQUIREMENT

You MUST respond with ONLY a valid JSON object. No markdown, no code blocks, no explanatory text before or after.

Required JSON structure:
{
    "topic_summary": "Comprehensive 1000-2000 word summary covering all key aspects",
    "key_concepts": {
        "concept_name": "Clear, detailed explanation",
        "another_concept": "Another detailed explanation"
    },
    "mathematical_foundations": "Key formulas and mathematical concepts (null if not applicable)",
    "implementation_examples": "Practical code examples with explanations (null if not applicable)"
}

IMPORTANT: Return ONLY the JSON object. Any other format will cause a parsing error."""

    USER_TEMPLATE = """## Research Task

**Topic**: {query}

## Context

**Category**: {category}
**Target Audience**: {target_audience}
**Content Type**: {content_type}
**Maximum Tool Calls**: {max_iterations}

## Category-Specific Strategy

{category_guidelines}

## Audience Depth Guide

Adapt your research based on target audience:
- **Beginner**: Focus on intuitive explanations, analogies, foundational concepts
- **Practitioner**: Balance theory with practical implementation details
- **Expert**: Include cutting-edge research, advanced techniques, mathematical rigor

## Output Length Guidelines

Adjust research depth and summary length based on content type:
- **blog**: Comprehensive research summary, detailed explanations, code examples, mathematical foundations, and implementation examples.
- **linkedin_post**: Focused research with 300-500 word summary, key highlights only, concise insights, do not include the Mathematical Foundations and Implementation Examples in the Output.

Begin research systematically. Think step by step. Remember to return ONLY required JSON structure."""

    def system_prompt(self, **kwargs) -> str:
        """Return the system prompt for research agent"""
        return self.SYSTEM_TEMPLATE

    def user_prompt(
        self,
        query: str,
        category: str = "core_ai",
        category_guidelines: str = "",
        target_audience: str = "practitioner",
        content_type: str = "blog",
        max_iterations: int = 5,
        **kwargs,
    ) -> str:
        """
        Return the user prompt for research agent.
        
        Args:
            query: The research query
            category: Topic category
            category_guidelines: Category-specific guidelines
            target_audience: Target audience level
            content_type: Type of content (blog or linkedin)
            max_iterations: Maximum tool calls allowed
            
        Returns:
            Formatted user prompt
        """
        return self.format(
            self.USER_TEMPLATE,
            query=query,
            category=category,
            category_guidelines=category_guidelines,
            target_audience=target_audience,
            content_type=content_type,
            max_iterations=max_iterations,
        )

