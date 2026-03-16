"""
LinkedIn Agent

Orchestrates LinkedIn post generation using LinkedInAgentNode.
"""
from typing import Optional

from app.core.llm.bedrock_llm import BedrockLLM
from app.core.logging.logger import logger
from app.modules.social.services.nodes.linkedin_agent_node import LinkedInAgentNode, LinkedInOutput


class LinkedInAgent:
    """
    Agent for generating LinkedIn posts from content.
    Orchestrates the LinkedInAgentNode for execution.
    """

    def __init__(self, llm: Optional[BedrockLLM] = None):
        """
        Initialize LinkedIn agent.

        Args:
            llm: LLM instance (creates default if not provided)
        """
        self.node = LinkedInAgentNode(llm=llm)
        logger.info('LinkedInAgent initialized')

    async def generate_post(
        self,
        topic: str,
        content: str,
        target_audience: str = 'practitioner',
        user_instructions: str = '',
    ) -> LinkedInOutput:
        """
        Generate a LinkedIn post from content.

        Args:
            topic: Post topic
            content: Source content to transform
            target_audience: Target audience (beginner, practitioner, expert)
            user_instructions: Custom instructions from user on how post should look

        Returns:
            LinkedInOutput with generated post
        """
        logger.info(f"[LINKEDIN] Generating for: '{topic[:50]}...'")

        output = await self.node.execute(
            topic=topic,
            content=content,
            target_audience=target_audience,
            user_instructions=user_instructions,
        )

        logger.info(f'[LINKEDIN] Generated: {output.character_count} chars')
        return output

    async def generate_from_blog(
        self,
        blog_title: str,
        blog_content: str,
        target_audience: str = 'practitioner',
        user_instructions: str = '',
    ) -> LinkedInOutput:
        """
        Generate a LinkedIn post from a blog post.

        Args:
            blog_title: Blog title
            blog_content: Blog content
            target_audience: Target audience
            user_instructions: Custom instructions from user on how post should look

        Returns:
            LinkedInOutput with generated post
        """
        return await self.generate_post(
            topic=blog_title,
            content=blog_content[:4000],
            target_audience=target_audience,
            user_instructions=user_instructions,
        )


def get_linkedin_agent(llm: Optional[BedrockLLM] = None) -> LinkedInAgent:
    """Factory function to create LinkedInAgent"""
    return LinkedInAgent(llm=llm)


# Re-export LinkedInOutput for backward compatibility
__all__ = ['LinkedInAgent', 'LinkedInOutput', 'get_linkedin_agent']
