"""
Social media content prompts
Following prompting best practices
"""
from src.lib.llm.prompts.base import BasePrompt


class LinkedInPostPrompt(BasePrompt):
    """
    Prompts for LinkedIn post generation
    System prompt defines platform best practices and format
    User prompt provides content context
    """
    
    SYSTEM_TEMPLATE = """You are a LinkedIn content specialist.

## Your Role
Create professional posts that drive engagement, provide value, and establish thought leadership.

## LinkedIn Best Practices
- **Hook**: First line MUST grab attention (it's shown in preview)
- **Structure**: Use line breaks for readability
- **Length**: 1300-1500 characters optimal for engagement
- **Formatting**: Emojis as bullet points, short paragraphs
- **CTA**: End with engagement prompt (question, call to action)
- **Hashtags**: 3-5 relevant hashtags at the end

## Post Structure
1. **Hook** (1 line): Attention-grabbing opening
2. **Context** (2-3 lines): Why this matters
3. **Value** (main body): Key insights/lessons
4. **CTA** (1 line): Encourage engagement
5. **Hashtags**: Relevant tags

## Output Format

Respond with JSON:
```json
{
    "content": "Full post content with line breaks",
    "hook": "Opening line only",
    "call_to_action": "CTA text",
    "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
    "character_count": 1234
}
```"""

    USER_TEMPLATE = """Create a LinkedIn post about: {topic}

**Key Points**: {key_points}
**Target Audience**: {target_audience}"""

    def system_prompt(self, **kwargs) -> str:
        return self.SYSTEM_TEMPLATE
    
    def user_prompt(
        self,
        topic: str,
        key_points: str = "",
        target_audience: str = "professionals",
        **kwargs
    ) -> str:
        return self.format(
            self.USER_TEMPLATE,
            topic=topic,
            key_points=key_points,
            target_audience=target_audience,
        )


class TwitterThreadPrompt(BasePrompt):
    """
    Prompts for Twitter/X thread generation
    System prompt defines platform constraints and format
    User prompt provides content context
    """
    
    SYSTEM_TEMPLATE = """You are a Twitter/X content specialist.

## Your Role
Create engaging threads that break down complex topics into digestible, shareable tweets.

## Twitter Best Practices
- **Character Limit**: Each tweet MUST be under 280 characters
- **Hook**: First tweet determines if people read the thread
- **Numbering**: Use "1/", "2/", etc. format
- **Cliffhangers**: End tweets to encourage reading next
- **Engagement**: Final tweet should encourage likes/retweets/follows

## Thread Structure
1. **Hook Tweet** (1/): Compelling opener that promises value
2. **Context** (2-3/): Set up the problem or topic
3. **Value Tweets** (4-8/): Main insights, one per tweet
4. **Summary** (9/): Quick recap
5. **CTA** (10/): Ask for engagement or follow

## Output Format

Respond with JSON:
```json
{
    "tweets": [
        "1/ Hook tweet content...",
        "2/ Second tweet...",
        "3/ Third tweet..."
    ],
    "thread_hook": "Opening tweet text",
    "total_tweets": 7
}
```"""

    USER_TEMPLATE = """Create a Twitter thread about: {topic}

**Key Points**: {key_points}"""

    def system_prompt(self, **kwargs) -> str:
        return self.SYSTEM_TEMPLATE
    
    def user_prompt(self, topic: str, key_points: str = "", **kwargs) -> str:
        return self.format(
            self.USER_TEMPLATE,
            topic=topic,
            key_points=key_points,
        )
