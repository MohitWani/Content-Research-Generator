"""
Blog generation prompts for the Blog Writer Agent
"""


class BasePrompt:
    """Base class for prompts with formatting support"""

    def format(self, template: str, **kwargs) -> str:
        """Safely format a template with kwargs"""
        try:
            return template.format(**kwargs)
        except KeyError:
            return template


class BlogPrompt(BasePrompt):
    """Prompts for blog generation from research data"""

    SYSTEM_TEMPLATE = """You are an expert technical writer for Medium.

## Your Task
Transform research data into an engaging, well-structured blog post.

## Blog Requirements
1. **Engaging Hook** - Start with a compelling opening
2. **Clear Structure** - Use headers, sections, bullet points
3. **Accessible Language** - Adapt to target audience
4. **Code Examples** - Include where appropriate
5. **Sources** - Reference research sources

## Output Format
Respond with ONLY valid JSON:
{
    "title": "Engaging blog title",
    "content": "Full markdown-formatted blog content",
    "meta_description": "SEO-friendly description (150-160 chars)",
    "tags": ["tag1", "tag2", "tag3"],
    "estimated_reading_time": "X min read"
}

IMPORTANT: Return ONLY the JSON object."""

    USER_TEMPLATE = """## Blog Generation Task

**Topic**: {topic}
**Target Audience**: {target_audience}
**Tone**: {tone}

## Research Data
{research_data}

## Audience Guidelines
{audience_guidelines}

Generate an engaging blog post. Return ONLY valid JSON."""

    def system_prompt(self, **kwargs) -> str:
        """Return the system prompt for blog generation"""
        return self.SYSTEM_TEMPLATE

    def user_prompt(
        self,
        topic: str,
        target_audience: str = 'practitioner',
        tone: str = 'professional',
        research_data: str = '',
        audience_guidelines: str = '',
        **kwargs,
    ) -> str:
        """
        Return the user prompt for blog generation.
        
        Args:
            topic: The blog topic
            target_audience: Target audience level
            tone: Writing tone
            research_data: Formatted research data
            audience_guidelines: Audience-specific guidelines
            
        Returns:
            Formatted user prompt
        """
        return self.format(
            self.USER_TEMPLATE,
            topic=topic,
            target_audience=target_audience,
            tone=tone,
            research_data=research_data,
            audience_guidelines=audience_guidelines,
        )
