"""
LinkedIn post generation prompts for the LinkedIn Agent
"""


class BasePrompt:
    """Base class for prompts with formatting support"""

    def format(self, template: str, **kwargs) -> str:
        """Safely format a template with kwargs"""
        try:
            return template.format(**kwargs)
        except KeyError:
            return template


class LinkedInPrompt(BasePrompt):
    """Prompts for LinkedIn post generation"""

    SYSTEM_TEMPLATE = """You are an expert LinkedIn content creator.

## Your Task
Create engaging, professional LinkedIn posts from research or blog content.

## LinkedIn Best Practices
- Start with a strong hook
- Keep paragraphs short (1-2 sentences)
- Use line breaks for readability
- Include 3-5 relevant hashtags
- End with a call-to-action
- Stay under 3000 characters

## User Instructions Handling
If the user provides custom instructions, you MUST follow them as the highest priority.
User instructions may include:
- Specific tone or style preferences (casual, formal, storytelling, etc.)
- Desired post length (short, medium, long)
- Specific points to highlight or emphasize
- Hashtag preferences or restrictions
- Call-to-action preferences
- Formatting preferences (use emojis, bullet points, numbered lists, etc.)
- Language or terminology preferences

Always prioritize user instructions over default best practices when they conflict.

## Output Format
Respond with ONLY valid JSON:
{
    "hook": "Attention-grabbing first line",
    "content": "Full post content including hook",
    "hashtags": ["hashtag1", "hashtag2"],
    "call_to_action": "CTA text"
}

IMPORTANT: Return ONLY the JSON object."""

    USER_TEMPLATE = """## LinkedIn Post Generation Task

**Topic**: {topic}
**Target Audience**: {target_audience}

## Source Content
{content}
{user_instructions_section}
Generate an engaging LinkedIn post. Return ONLY valid JSON."""

    USER_INSTRUCTIONS_TEMPLATE = """
## User Instructions (PRIORITY - Follow these instructions carefully)
{user_instructions}
"""

    def system_prompt(self, **kwargs) -> str:
        """Return the system prompt for LinkedIn post generation"""
        return self.SYSTEM_TEMPLATE

    def user_prompt(
        self,
        topic: str,
        content: str,
        target_audience: str = 'practitioner',
        user_instructions: str = '',
        **kwargs,
    ) -> str:
        """
        Return the user prompt for LinkedIn post generation.
        
        Args:
            topic: The post topic
            content: Source content to transform
            target_audience: Target audience level
            user_instructions: Custom instructions from user on how post should look
            
        Returns:
            Formatted user prompt
        """
        # Build user instructions section if provided
        user_instructions_section = ''
        if user_instructions and user_instructions.strip():
            user_instructions_section = self.format(
                self.USER_INSTRUCTIONS_TEMPLATE,
                user_instructions=user_instructions.strip(),
            )

        return self.format(
            self.USER_TEMPLATE,
            topic=topic,
            content=content,
            target_audience=target_audience,
            user_instructions_section=user_instructions_section,
        )
