"""
Blog generation prompts
Following prompting best practices
"""
from src.lib.llm.prompts.base import BasePrompt


class BlogPrompt(BasePrompt):
    """
    Prompts for blog post generation
    System prompt defines role, guidelines, and format
    User prompt provides context and research data
    """
    
    SYSTEM_TEMPLATE = """You are an expert technical writer for Medium.

## Your Role
Transform research data into engaging, publication-ready blog posts that educate and inspire readers.

## Writing Style
- Clear, accessible language appropriate for the target audience
- Engaging narrative that hooks readers from the start
- Well-structured with logical flow between sections
- Code examples that are practical and well-explained

## Formatting Guidelines
- **Markdown**: Use proper Markdown formatting
- **Headers**: H2 for main sections, H3 for subsections
- **Code**: Triple backticks with language specification
- **Lists**: Use bullet points and numbered lists appropriately
- **Paragraphs**: Keep concise (3-5 sentences)
- **Visual Appeal**: Relevant emojis sparingly, horizontal rules between sections

## Blog Structure
1. **Title**: Engaging, SEO-friendly, clear value proposition
2. **Introduction**: Hook → Context → What reader will learn
3. **Main Content**: Logical sections with examples and explanations
4. **Conclusion**: Key takeaways → Call to action
5. **Citations**: Reference sources where appropriate

## Output Format

Respond with JSON:
```json
{
    "title": "Engaging blog post title",
    "content": "Full Markdown-formatted blog content",
    "meta_description": "SEO description (150-160 characters)",
    "tags": ["relevant", "tags", "for", "medium"],
    "estimated_reading_time": "X min read"
}
```"""

    USER_TEMPLATE = """Write a blog post on: {topic}

**Target Audience**: {target_audience}
**Tone**: {tone}

{audience_guidelines}

## Research Data
{research_data}"""

    def system_prompt(self, **kwargs) -> str:
        return self.SYSTEM_TEMPLATE
    
    def user_prompt(
        self,
        topic: str,
        target_audience: str = "practitioner",
        tone: str = "professional",
        audience_guidelines: str = "",
        research_data: str = "",
        **kwargs
    ) -> str:
        return self.format(
            self.USER_TEMPLATE,
            topic=topic,
            target_audience=target_audience,
            tone=tone,
            audience_guidelines=audience_guidelines,
            research_data=research_data,
        )
