"""
Agentic Research Agent

Main orchestrator for research operations using LangChain agent.
Delegates to specialized components for tools, parsing, and data persistence.
"""
from typing import Optional

from app.core.llm.bedrock_llm import BedrockLLM
from app.core.logging.logger import logger
from app.modules.research.models.research_model import TopicCategory
from app.modules.research.schemas.agent_schemas import AgentConfig, ResearchOutput
from app.modules.research.services.nodes import ResearchAgentNode
from app.modules.research.services.research_data_service import ResearchDataService


class AgenticResearcher:
    """
    Agentic Researcher - Main orchestrator for research operations.
    
    Coordinates between:
    - ResearchAgentNode: Core agent execution
    - ResearchDataService: Data persistence
    
    Usage:
        researcher = AgenticResearcher(max_iterations=5)
        output = await researcher.research(
            query="Explain attention mechanism",
            category=TopicCategory.CORE_AI,
            target_audience="practitioner",
        )
    """

    def __init__(
        self,
        llm: Optional[BedrockLLM] = None,
        max_iterations: int = 10,
    ):
        """
        Initialize the agentic researcher.
        
        Args:
            llm: Language model instance (defaults to BedrockLLM)
            max_iterations: Maximum agent iterations
        """
        self.config = AgentConfig(
            max_iterations=max_iterations,
            recursion_limit=max_iterations * 2 + 5,
        )

        # Initialize components
        self.agent_node = ResearchAgentNode(
            llm=llm,
            config=self.config,
        )
        self.data_service = ResearchDataService()

        logger.info(
            f"AgenticResearcher initialized: {self.agent_node.tool_count} tools, "
            f"max_iterations={max_iterations}"
        )

    async def research(
        self,
        query: str,
        category: TopicCategory,
        target_audience: str = "practitioner",
    ) -> ResearchOutput:
        """
        Execute research using the agent.
        
        Args:
            query: Research query
            category: Topic category
            target_audience: Target audience for the research
            
        Returns:
            ResearchOutput with research results
        """
        logger.info(
            f"[RESEARCH] Query: '{query[:60]}...' | Category: {category.value}"
        )

        try:
            # Execute agent
            output = await self.agent_node.execute(
                query=query,
                category=category,
                target_audience=target_audience,
            )

            # Save research data
            output.research_data_path = await self.data_service.save(query, output)

            logger.info(f"[RESEARCH] Complete: score={output.completeness_score:.2f}")
            return output

        except Exception as e:
            logger.error(f"[RESEARCH] Failed: {e}", exc_info=True)
            return ResearchOutput(
                topic_summary=f"Research failed: {str(e)}",
                key_concepts={"error": str(e)},
            )

    @property
    def max_iterations(self) -> int:
        """Return the maximum iterations configured."""
        return self.config.max_iterations

    @property
    def tool_count(self) -> int:
        """Return the number of tools available."""
        return self.agent_node.tool_count


# ============= Factory =============


def get_agentic_researcher(
    llm: Optional[BedrockLLM] = None,
    max_iterations: int = 10,
) -> AgenticResearcher:
    """
    Create AgenticResearcher instance.
    
    Args:
        llm: Language model instance
        max_iterations: Maximum agent iterations
        
    Returns:
        Configured AgenticResearcher instance
    """
    return AgenticResearcher(llm=llm, max_iterations=max_iterations)
