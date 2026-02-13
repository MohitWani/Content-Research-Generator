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
from app.core.logging.logger import logger
from app.modules.research.services.prompts import research_prompts
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
        logger.info("[AGENT_NODE] Initializing ResearchAgentNode...")
        
        self.llm = llm or BedrockLLM()
        self.tools = tools or create_research_tools()
        self.config = config or AgentConfig()
        self.parser = ResearchOutputParser()

        logger.debug(f"[AGENT_NODE] Creating agent with {len(self.tools)} tools")
        
        # Create the agent
        self.agent = create_agent(
            model=self.llm.llm,
            tools=self.tools,
        )

        logger.info(
            f"[AGENT_NODE] Initialized: {len(self.tools)} tools, "
            f"max_iterations={self.config.max_iterations}"
        )

    def build_messages(
        self,
        query: str,
        category: str,
        target_audience: str,
        content_type: str = "blog",
    ) -> List[Any]:
        """
        Build messages for agent execution.
        
        Args:
            query: Research query
            category: Topic category
            target_audience: Target audience
            content_type: Type of content (blog or linkedin)
            
        Returns:
            List of messages for the agent
        """
        logger.debug(
            f"[AGENT_NODE] Building messages: category={category}, "
            f"audience={target_audience}, content_type={content_type}"
        )
        
        messages = [
            SystemMessage(content=research_prompts.research.system_prompt()),
            HumanMessage(
                content=research_prompts.research.user_prompt(
                    query=query,
                    category=category,
                    category_guidelines=get_react_category_guidelines(category),
                    target_audience=target_audience,
                    content_type=content_type,
                    max_iterations=self.config.max_iterations,
                )
            ),
        ]
        
        logger.debug(f"[AGENT_NODE] Built {len(messages)} messages for agent")
        return messages

    async def execute(
        self,
        query: str,
        category: TopicCategory,
        target_audience: str = "practitioner",
        content_type: str = "blog",
    ) -> ResearchOutput:
        """
        Execute the research agent.
        
        Args:
            query: Research query
            category: Topic category
            target_audience: Target audience
            content_type: Type of content (blog or linkedin)
            
        Returns:
            ResearchOutput with research results
        """
        logger.info(
            f"[AGENT_NODE] Starting execution: query='{query[:60]}...', "
            f"category={category.value}, audience={target_audience}, content_type={content_type}"
        )

        # Build messages
        logger.debug("[AGENT_NODE] Building messages for agent...")
        messages = self.build_messages(
            query=query,
            category=category.value,
            target_audience=target_audience,
            content_type=content_type,
        )

        # Configure agent execution
        agent_config = {
            "recursion_limit": self.config.max_iterations * 2 + 5,
        }

        try:
            logger.info(
                f"[AGENT_NODE] Invoking agent (recursion_limit={agent_config['recursion_limit']})"
            )

            # Execute agent
            result = await self.agent.ainvoke(
                {"messages": messages},
                config=agent_config,
            )

            logger.info(f"[AGENT_NODE] Agent returned {len(result['messages'])} messages")

            # Parse response - BEFORE
            logger.info("[AGENT_NODE] Starting message parsing...")
            logger.debug(
                f"[AGENT_NODE] Raw messages count: {len(result['messages'])}"
            )
            
            parsed_response = self.parser.extract_from_messages(result["messages"])
            
            # Parse response - AFTER
            logger.info(
                f"[AGENT_NODE] Message parsing complete: "
                f"tool_calls={len(parsed_response.tool_calls)}, "
                f"tool_results={len(parsed_response.tool_results)}, "
                f"final_content_length={len(parsed_response.final_content)}"
            )

            # Parse output - BEFORE
            logger.info("[AGENT_NODE] Starting output parsing...")
            logger.debug(
                f"[AGENT_NODE] Parsing output with {len(parsed_response.tool_calls)} tool calls"
            )
            
            output = self.parser.parse_output(
                parsed_response=parsed_response,
                query=query,
                category=category,
            )
            
            # Parse output - AFTER
            logger.info(
                f"[AGENT_NODE] Output parsing complete: "
                f"summary_length={len(output.topic_summary)}, "
                f"concepts={len(output.key_concepts)}, "
                f"sources={len(output.sources)}, "
                f"score={output.completeness_score:.2f}"
            )

            logger.info(
                f"[AGENT_NODE] Execution complete: score={output.completeness_score:.2f}"
            )
            return output

        except Exception as e:
            logger.error(f"[AGENT_NODE] Execution failed: {e}", exc_info=True)
            return ResearchOutput(
                topic_summary=f"Research failed: {str(e)}",
                key_concepts={"error": str(e)},
            )

    @property
    def tool_count(self) -> int:
        """Return the number of tools available."""
        return len(self.tools)
