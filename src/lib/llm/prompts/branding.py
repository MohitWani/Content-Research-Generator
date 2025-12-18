"""
Branding and voice prompts
Following prompting best practices
"""
from src.lib.llm.prompts.base import BasePrompt


class BrandingPrompt(BasePrompt):
    """
    Prompts for branding and voice alignment
    System prompt defines role and transformation guidelines
    User prompt provides content and brand context
    """
    
    SYSTEM_TEMPLATE = """You are a brand voice specialist.

## Your Role
Transform content to align with a specific brand voice while preserving the core message and value.

## Transformation Guidelines
1. **Preserve Meaning**: Never change the factual content or key messages
2. **Adapt Tone**: Match vocabulary, sentence structure, and style to brand voice
3. **Maintain Quality**: Output should be publication-ready
4. **Be Consistent**: Apply brand voice uniformly throughout

## Voice Elements to Consider
- **Vocabulary**: Formal vs casual, technical vs accessible
- **Sentence Structure**: Short and punchy vs flowing and detailed
- **Perspective**: First person, second person, third person
- **Emotion**: Enthusiastic, professional, empathetic, authoritative

## Output Format

Respond with JSON:
```json
{
    "branded_content": "Rewritten content matching brand voice",
    "changes_made": [
        "Specific change 1",
        "Specific change 2"
    ],
    "voice_alignment_score": 0.0-1.0
}
```"""

    USER_TEMPLATE = """Apply brand voice to this content:

**Voice Profile**:
{voice_profile}

**Style Guidelines**:
{style_guidelines}

**Content to Transform**:
{content}"""

    def system_prompt(self, **kwargs) -> str:
        return self.SYSTEM_TEMPLATE
    
    def user_prompt(
        self,
        content: str,
        voice_profile: str = "",
        style_guidelines: str = "",
        **kwargs
    ) -> str:
        return self.format(
            self.USER_TEMPLATE,
            content=content,
            voice_profile=voice_profile,
            style_guidelines=style_guidelines,
        )
