"""
Topic Agent Node

Contains the core logic for topic categorization using LLM.
"""
from typing import Optional

from app.common.exceptions.research_exceptions import QueryCategorizationError
from app.core.llm.bedrock_llm import BedrockLLM
from app.core.logging.logger import logger
from app.modules.research.services.prompts import research_prompts
from app.modules.research.models.research_model import TopicCategory


# Category mapping for string to enum conversion
CATEGORY_MAP = {
    "core_ai": TopicCategory.CORE_AI,
    "practical_implementation": TopicCategory.PRACTICAL_IMPLEMENTATION,
    "software_development": TopicCategory.SOFTWARE_DEVELOPMENT,
    "web_development": TopicCategory.WEB_DEVELOPMENT,
    "devops": TopicCategory.DEVOPS,
    "general_tech": TopicCategory.GENERAL_TECH,
}


class TopicAgentNode:
    """
    Topic Agent Node - Core logic for query categorization.
    
    Provides a simple interface to categorize queries using LLM.
    """

    def __init__(self, llm: Optional[BedrockLLM] = None):
        """
        Initialize the topic agent node.
        
        Args:
            llm: Language model instance (defaults to BedrockLLM)
        """
        self.llm = llm or BedrockLLM()
        logger.info("TopicAgentNode initialized")

    async def categorize(self, query: str) -> TopicCategory:
        """
        Categorize a research query using LLM.
        
        Args:
            query: The query to categorize
            
        Returns:
            TopicCategory enum for the query
            
        Raises:
            QueryCategorizationError: If query is empty or categorization fails
        """
        if not query or not query.strip():
            raise QueryCategorizationError("Query cannot be empty")

        query = query.strip()

        try:
            # Build prompts
            system_prompt = research_prompts.topic.system_prompt()
            user_prompt = research_prompts.topic.user_prompt(query=query)

            logger.debug(f"Categorizing query: {query[:100]}...")

            # Invoke LLM
            response = await self.llm.ainvoke(
                prompt=user_prompt,
                system_prompt=system_prompt,
                parse_json=True,
            )

            logger.info(f"LLM response: {str(response)[:100]}...")

            # Parse response
            if not isinstance(response, dict):
                logger.error(
                    f"Invalid response format: expected dict, got {type(response)}"
                )
                raise QueryCategorizationError(
                    f"Invalid response format: expected dict, got {type(response)}"
                )

            # Extract category
            category_str = response.get("category", "general_tech")
            category = CATEGORY_MAP.get(category_str)

            if category is None:
                logger.warning(
                    f"Unknown category '{category_str}', defaulting to general_tech"
                )
                category = TopicCategory.GENERAL_TECH

            logger.info(f"Query categorized as: {category.value}")
            return category

        except QueryCategorizationError:
            raise
        except Exception as e:
            logger.error(f"Categorization error: {e}")
            raise QueryCategorizationError(f"Failed to categorize query: {e}")
