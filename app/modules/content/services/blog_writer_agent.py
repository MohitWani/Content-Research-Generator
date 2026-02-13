"""
Blog Writer Agent

Orchestrates blog generation using BlogWriterNode.
"""
from typing import Optional

from app.core.llm.bedrock_llm import BedrockLLM
from app.core.logging.logger import logger
from app.modules.content.services.nodes.blog_writer_node import BlogOutput, BlogWriterNode
from app.modules.research.services.agentic_researcher import ResearchOutput


class BlogWriterAgent:
    """
    Agent for generating blog posts from research data.
    Orchestrates the BlogWriterNode for execution.
    """

    def __init__(self, llm: Optional[BedrockLLM] = None):
        """
        Initialize blog writer agent.

        Args:
            llm: LLM instance (creates default if not provided)
        """
        self.node = BlogWriterNode(llm=llm)
        logger.info('BlogWriterAgent initialized')

    async def generate_blog(
        self,
        topic: str,
        research_data: ResearchOutput,
        target_audience: str = 'practitioner',
        tone: str = 'professional',
    ) -> BlogOutput:
        """
        Generate a blog post from research data.

        Args:
            topic: Blog topic/title
            research_data: Research output to transform
            target_audience: Target audience (beginner, practitioner, expert)
            tone: Writing tone (professional, conversational, technical)

        Returns:
            BlogOutput with generated content
        """
        logger.info(f"[BLOG] Generating for: '{topic[:50]}...' | Audience: {target_audience}")

        output = await self.node.execute(
            topic=topic,
            research_data=research_data,
            target_audience=target_audience,
            tone=tone,
        )

        logger.info(f'[BLOG] Generated: {len(output.content)} chars, {len(output.tags)} tags')
        return output


def get_blog_writer_agent(llm: Optional[BedrockLLM] = None) -> BlogWriterAgent:
    """Factory function to create BlogWriterAgent"""
    return BlogWriterAgent(llm=llm)


# Re-export BlogOutput for backward compatibility
__all__ = ['BlogWriterAgent', 'BlogOutput', 'get_blog_writer_agent']
