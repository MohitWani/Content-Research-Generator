"""
Topic Agent for query categorization.

This is the main interface for topic categorization.
Delegates core logic to TopicAgentNode.
"""
from typing import Optional

from app.core.llm.bedrock_llm import BedrockLLM
from app.core.logging.logger import logger
from app.modules.research.models.research_model import TopicCategory
from app.modules.research.services.nodes import TopicAgentNode


class TopicAgent:
    """
    Agent for categorizing research queries.
    
    Provides a high-level interface for query categorization,
    delegating core logic to TopicAgentNode.
    """

    def __init__(self, llm: Optional[BedrockLLM] = None):
        """
        Initialize the topic agent.
        
        Args:
            llm: Language model instance (defaults to BedrockLLM)
        """
        self.node = TopicAgentNode(llm=llm)
        logger.info("[TOPIC_AGENT] Initialized TopicAgent")

    async def categorize_query(self, query: str) -> TopicCategory:
        """
        Categorize a research query.
        
        Args:
            query: The query to categorize
            
        Returns:
            TopicCategory enum for the query
        """
        logger.info(f"[TOPIC_AGENT] Categorizing query: {query[:50]}...")
        category = await self.node.categorize(query)
        logger.info(f"[TOPIC_AGENT] Query categorized as: {category.value}")
        return category

    async def is_ai_related(self, query: str) -> bool:
        """
        Check if a query is AI-related.
        
        Args:
            query: The query to check
            
        Returns:
            True if the query is AI-related
        """
        logger.debug(f"[TOPIC_AGENT] Checking if query is AI-related: {query[:50]}...")
        try:
            category = await self.categorize_query(query)
            is_ai = category in [
                TopicCategory.CORE_AI,
                TopicCategory.PRACTICAL_IMPLEMENTATION,
            ]
            logger.debug(f"[TOPIC_AGENT] Query is AI-related: {is_ai}")
            return is_ai
        except Exception as e:
            logger.error(f"[TOPIC_AGENT] Error checking if AI-related: {e}")
            return False


def get_topic_agent(llm: Optional[BedrockLLM] = None) -> TopicAgent:
    """
    Factory function to create TopicAgent.
    
    Args:
        llm: Language model instance
        
    Returns:
        Configured TopicAgent instance
    """
    logger.debug("[TOPIC_AGENT] Creating TopicAgent via factory")
    return TopicAgent(llm=llm)
