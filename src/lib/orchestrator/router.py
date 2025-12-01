"""
Router for directing queries to appropriate workflows
Routes based on topic category (core AI vs practical implementation)
Maps to: spec.md → Story 2, FR1
"""
from typing import Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum

from src.lib.agents.topic_agent import TopicAgent
from src.lib.models.research import TopicCategory
from src.lib.models.schemas import TopicCategorizationResult
from src.lib.models.exceptions import QueryCategorizationError
from src.common.logger import setup_logger

logger = setup_logger(__name__)


class WorkflowType(str, Enum):
    """Types of workflows that can be executed"""
    RESEARCH_CORE_AI = "research_core_ai"
    RESEARCH_PRACTICAL = "research_practical"
    BLOG_GENERATION = "blog_generation"
    FULL_PIPELINE = "full_pipeline"


@dataclass
class RoutingDecision:
    """Result of routing decision"""
    workflow_type: WorkflowType
    topic_category: TopicCategory
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Router:
    """
    Routes incoming queries to appropriate workflows
    Uses topic categorization to determine research depth and approach
    """
    
    def __init__(self, topic_agent: Optional[TopicAgent] = None):
        """
        Initialize router
        
        Args:
            topic_agent: Agent for topic categorization
        """
        self.topic_agent = topic_agent or TopicAgent()
        self._workflow_handlers: Dict[WorkflowType, Callable] = {}
        logger.info("Initialized Router")
    
    def register_workflow(
        self,
        workflow_type: WorkflowType,
        handler: Callable[..., Awaitable[Any]],
    ) -> None:
        """
        Register a workflow handler
        
        Args:
            workflow_type: Type of workflow
            handler: Async callable to handle the workflow
        """
        self._workflow_handlers[workflow_type] = handler
        logger.debug(f"Registered handler for {workflow_type.value}")
    
    async def route(
        self,
        query: str,
        target_audience: str = "practitioner",
        content_type: str = "blog",
    ) -> RoutingDecision:
        """
        Route a query to the appropriate workflow
        
        Args:
            query: User's research query
            target_audience: Target audience for content
            content_type: Type of content to generate
        
        Returns:
            RoutingDecision with workflow type and category
        
        Raises:
            QueryCategorizationError: If query cannot be categorized
        """
        logger.info(f"Routing query: {query[:50]}...")
        
        # Categorize the query
        categorization = await self.topic_agent.categorize_query(query)
        
        # Determine workflow type based on category
        if categorization.category == "core_ai":
            topic_category = TopicCategory.CORE_AI
            workflow_type = WorkflowType.RESEARCH_CORE_AI
        else:
            topic_category = TopicCategory.PRACTICAL_IMPLEMENTATION
            workflow_type = WorkflowType.RESEARCH_PRACTICAL
        
        decision = RoutingDecision(
            workflow_type=workflow_type,
            topic_category=topic_category,
            confidence=categorization.confidence,
            reasoning=categorization.reasoning,
            metadata={
                "target_audience": target_audience,
                "content_type": content_type,
                "is_ai_related": categorization.is_ai_related,
            },
        )
        
        logger.info(
            f"Routed to {workflow_type.value} "
            f"(confidence: {categorization.confidence:.2f})"
        )
        
        return decision
    
    async def route_and_execute(
        self,
        query: str,
        target_audience: str = "practitioner",
        content_type: str = "blog",
        **kwargs,
    ) -> Any:
        """
        Route query and execute the appropriate workflow
        
        Args:
            query: User's research query
            target_audience: Target audience for content
            content_type: Type of content to generate
            **kwargs: Additional arguments for workflow
        
        Returns:
            Result from workflow execution
        
        Raises:
            QueryCategorizationError: If query cannot be categorized
            ValueError: If no handler registered for workflow type
        """
        decision = await self.route(query, target_audience, content_type)
        
        handler = self._workflow_handlers.get(decision.workflow_type)
        if not handler:
            raise ValueError(f"No handler registered for {decision.workflow_type.value}")
        
        # Execute workflow
        result = await handler(
            query=query,
            target_audience=target_audience,
            topic_category=decision.topic_category,
            **kwargs,
        )
        
        return result
    
    def get_research_requirements(
        self,
        topic_category: TopicCategory,
    ) -> Dict[str, Any]:
        """
        Get research requirements based on topic category
        
        Args:
            topic_category: Category of the topic
        
        Returns:
            Dictionary of research requirements
        """
        if topic_category == TopicCategory.CORE_AI:
            return {
                "required_sections": [
                    "mathematical_foundations",
                    "historical_context",
                    "implementation_examples",
                ],
                "min_sources": 5,
                "source_types": ["paper", "web", "github"],
                "depth": "deep",
                "include_code": True,
                "include_formulas": True,
            }
        else:  # PRACTICAL_IMPLEMENTATION
            return {
                "required_sections": [
                    "implementation_examples",
                    "step_by_step_guide",
                ],
                "min_sources": 3,
                "source_types": ["web", "github", "documentation"],
                "depth": "practical",
                "include_code": True,
                "include_formulas": False,
            }
    
    def get_content_guidelines(
        self,
        target_audience: str,
        topic_category: TopicCategory,
    ) -> Dict[str, Any]:
        """
        Get content generation guidelines
        
        Args:
            target_audience: Target audience
            topic_category: Category of the topic
        
        Returns:
            Dictionary of content guidelines
        """
        audience_guidelines = {
            "beginner": {
                "complexity": "low",
                "jargon": "minimal",
                "analogies": "many",
                "code_examples": "simple",
                "assumed_knowledge": "none",
            },
            "practitioner": {
                "complexity": "medium",
                "jargon": "moderate",
                "analogies": "some",
                "code_examples": "practical",
                "assumed_knowledge": "programming basics",
            },
            "expert": {
                "complexity": "high",
                "jargon": "full",
                "analogies": "minimal",
                "code_examples": "advanced",
                "assumed_knowledge": "domain expertise",
            },
        }
        
        base = audience_guidelines.get(target_audience, audience_guidelines["practitioner"])
        
        # Adjust for topic category
        if topic_category == TopicCategory.CORE_AI:
            base["include_math"] = True
            base["include_theory"] = True
        else:
            base["include_math"] = False
            base["include_theory"] = False
            base["focus"] = "hands-on"
        
        return base


def get_router(topic_agent: Optional[TopicAgent] = None) -> Router:
    """Factory function to create Router"""
    return Router(topic_agent=topic_agent)

