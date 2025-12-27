"""
Social media content prompts
"""
from app.core.llm.prompts.base import BasePrompt


class LinkedInPostPrompt(BasePrompt):
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

## Output Format
Respond with ONLY valid JSON:
{
    "hook": "Attention-grabbing first line",
    "content": "Full post content including hook",
    "hashtags": ["hashtag1", "hashtag2"],
    "call_to_action": "CTA text"
}"""

    USER_TEMPLATE = """Create a LinkedIn post about:

Topic: {topic}
Source Content: {content}
Target Audience: {target_audience}

Return ONLY valid JSON."""

    def system_prompt(self, **kwargs) -> str:
        return self.SYSTEM_TEMPLATE

    def user_prompt(
        self,
        topic: str,
        content: str,
        target_audience: str = 'practitioner',
        **kwargs,
    ) -> str:
        return self.format(
            self.USER_TEMPLATE,
            topic=topic,
            content=content,
            target_audience=target_audience,
        )


class TwitterThreadPrompt(BasePrompt):
    """Prompts for Twitter/X thread generation"""

    SYSTEM_TEMPLATE = """You are an expert Twitter/X thread creator.

## Your Task
Create engaging thread from research or blog content.

## Thread Best Practices
- Each tweet under 280 characters
- Number tweets (1/, 2/, etc.)
- First tweet hooks the reader
- Last tweet wraps up with takeaway
- 5-10 tweets ideal

## Output Format
Respond with ONLY valid JSON:
{
    "posts": [
        {"position": 1, "content": "1/ First tweet..."},
        {"position": 2, "content": "2/ Second tweet..."}
    ]
}"""

    USER_TEMPLATE = """Create a {max_posts}-post thread about:

Topic: {topic}
Source Content: {content}

Return ONLY valid JSON."""

    def system_prompt(self, **kwargs) -> str:
        return self.SYSTEM_TEMPLATE

    def user_prompt(
        self,
        topic: str,
        content: str,
        max_posts: int = 5,
        **kwargs,
    ) -> str:
        return self.format(
            self.USER_TEMPLATE,
            topic=topic,
            content=content,
            max_posts=max_posts,
        )


