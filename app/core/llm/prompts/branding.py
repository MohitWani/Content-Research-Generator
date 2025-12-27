"""
Branding prompts for brand voice application
"""
from app.core.llm.prompts.base import BasePrompt


class BrandingPrompt(BasePrompt):
    """Prompts for applying brand voice to content"""

    SYSTEM_TEMPLATE = """You are a brand voice expert.

## Your Task
Refine content to match brand guidelines while preserving core message.

## Output Format
Respond with ONLY valid JSON:
{
    "branded_content": "The refined content...",
    "changes_made": ["Changed X to Y", "Adjusted tone in..."],
    "voice_score": 0.85,
    "suggestions": ["Consider adding...", "Could improve..."]
}"""

    USER_TEMPLATE = """## Branding Task

Apply brand voice to this {content_type}:

## Brand Guidelines
{guidelines}

## Original Content
{content}

Target Audience: {target_audience}

Return ONLY valid JSON."""

    def system_prompt(self, **kwargs) -> str:
        return self.SYSTEM_TEMPLATE

    def user_prompt(
        self,
        content: str,
        guidelines: str,
        target_audience: str = 'practitioner',
        content_type: str = 'blog',
        **kwargs,
    ) -> str:
        return self.format(
            self.USER_TEMPLATE,
            content=content,
            guidelines=guidelines,
            target_audience=target_audience,
            content_type=content_type,
        )


