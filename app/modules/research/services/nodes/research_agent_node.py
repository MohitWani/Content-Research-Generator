"""
Research Agent Node

Contains the core agent logic for executing research workflows.
"""
from typing import Any, Dict, List, Optional

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from app.core.llm.bedrock_llm import BedrockLLM
from app.core.llm.prompt_loader import get_react_category_guidelines
from app.core.llm.prompts import prompts
from app.core.logging.logger import logger
from app.modules.research.models.research_model import TopicCategory
from app.modules.research.schemas.agent_schemas import (
    AgentConfig,
    ParsedAgentResponse,
    ResearchOutput,
)
from app.modules.research.services.parsers import ResearchOutputParser
from app.modules.research.services.tools import create_research_tools


class ResearchAgentNode:
    """
    Research Agent Node - Core agent execution logic.
    
    Handles:
    - Agent initialization with LLM and tools
    - Message construction
    - Agent execution
    - Response parsing
    """

    def __init__(
        self,
        llm: Optional[BedrockLLM] = None,
        tools: Optional[List[BaseTool]] = None,
        config: Optional[AgentConfig] = None,
    ):
        """
        Initialize the research agent node.
        
        Args:
            llm: Language model instance (defaults to BedrockLLM)
            tools: List of tools for the agent (defaults to research tools)
            config: Agent configuration
        """
        self.llm = llm or BedrockLLM()
        self.tools = tools or create_research_tools()
        self.config = config or AgentConfig()
        self.parser = ResearchOutputParser()

        # Create the agent
        self.agent = create_agent(
            model=self.llm.llm,
            tools=self.tools,
        )

        logger.info(
            f"ResearchAgentNode initialized: {len(self.tools)} tools, "
            f"max_iterations={self.config.max_iterations}"
        )

    def build_messages(
        self,
        query: str,
        category: str,
        target_audience: str,
    ) -> List[Any]:
        """
        Build messages for agent execution.
        
        Args:
            query: Research query
            category: Topic category
            target_audience: Target audience
            
        Returns:
            List of messages for the agent
        """
        return [
            SystemMessage(content=prompts.research.system_prompt()),
            HumanMessage(
                content=prompts.research.user_prompt(
                    query=query,
                    category=category,
                    category_guidelines=get_react_category_guidelines(category),
                    target_audience=target_audience,
                    max_iterations=self.config.max_iterations,
                )
            ),
        ]

    async def execute(
        self,
        query: str,
        category: TopicCategory,
        target_audience: str = "practitioner",
    ) -> ResearchOutput:
        """
        Execute the research agent.
        
        Args:
            query: Research query
            category: Topic category
            target_audience: Target audience
            
        Returns:
            ResearchOutput with research results
        """
        logger.info(
            f"[AGENT] Query: '{query[:60]}...' | Category: {category.value}"
        )

        # Build messages
        messages = self.build_messages(
            query=query,
            category=category.value,
            target_audience=target_audience,
        )

        # Configure agent execution
        agent_config = {
            "recursion_limit": self.config.max_iterations * 2 + 5,
        }

        try:
            logger.info(
                f"[AGENT] Starting (recursion_limit={agent_config['recursion_limit']})"
            )

            # Execute agent
            result = await self.agent.ainvoke(
                {"messages": messages},
                config=agent_config,
            )

            logger.info(f"[AGENT] Received {len(result['messages'])} messages")

            # Parse response
            parsed_response = self.parser.extract_from_messages(result["messages"])

            logger.info(
                f"[AGENT] Done: {len(parsed_response.tool_calls)} tool calls, "
                f"{len(parsed_response.tool_results)} results"
            )

            # Parse output
            output = self.parser.parse_output(
                parsed_response=parsed_response,
                query=query,
                category=category,
            )

            logger.info(f"[AGENT] Complete: score={output.completeness_score:.2f}")
            return output

        except Exception as e:
            logger.error(f"[AGENT] Failed: {e}", exc_info=True)
            return ResearchOutput(
                topic_summary=f"Research failed: {str(e)}",
                key_concepts={"error": str(e)},
            )

    @property
    def tool_count(self) -> int:
        """Return the number of tools available."""
        return len(self.tools)
