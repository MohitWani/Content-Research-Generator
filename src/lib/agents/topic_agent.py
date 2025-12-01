"""
Topic Agent for query categorization
Categorizes user queries as core AI or practical implementation topics
Maps to: spec.md → Story 2, FR1
"""
from typing import Optional

from src.lib.llm.model import BedrockLLM
from src.lib.llm.prompt_loader import load_prompt
from src.lib.models.research import TopicCategory
from src.lib.models.schemas import TopicCategorizationResult
from src.lib.models.exceptions import QueryCategorizationError
from src.common.logger import setup_logger

logger = setup_logger(__name__)


class TopicAgent:
    """
    Agent for categorizing research queries
    Determines if a query is about core AI concepts or practical implementation
    """
    
    def __init__(self, llm: Optional[BedrockLLM] = None):
        """
        Initialize topic agent
        
        Args:
            llm: LLM instance (creates default if not provided)
        """
        self.llm = llm or BedrockLLM()
        logger.info("Initialized TopicAgent")
    
    async def categorize_query(self, query: str) -> TopicCategorizationResult:
        """
        Categorize a research query
        
        Args:
            query: User's research query
        
        Returns:
            TopicCategorizationResult with category, confidence, and reasoning
        
        Raises:
            QueryCategorizationError: If categorization fails
        """
        # Validate input
        if not query or not query.strip():
            raise QueryCategorizationError("Query cannot be empty")
        
        query = query.strip()
        
        try:
            # Load and format prompt
            prompt = load_prompt("topic_categorization", query=query)
            
            # Invoke LLM for categorization
            logger.debug(f"Categorizing query: {query[:100]}...")
            
            response = await self.llm.ainvoke(
                prompt=prompt,
                system_prompt="You are an expert AI topic classifier. Respond only with valid JSON.",
                parse_json=True,
            )
            
            # Validate response structure
            if not isinstance(response, dict):
                raise QueryCategorizationError(f"Invalid response format: expected dict, got {type(response)}")
            
            # Check if AI-related
            is_ai_related = response.get("is_ai_related", True)
            if not is_ai_related:
                raise QueryCategorizationError(
                    f"Query is not AI related: {response.get('reasoning', 'No reasoning provided')}"
                )
            
            # Parse category
            category_str = response.get("category")
            if category_str is None:
                raise QueryCategorizationError(
                    f"Invalid response: missing category field. Response: {response}"
                )
            
            # Convert to enum
            try:
                if category_str == "core_ai":
                    category = TopicCategory.CORE_AI
                elif category_str == "practical_implementation":
                    category = TopicCategory.PRACTICAL_IMPLEMENTATION
                else:
                    # Default to practical for unknown categories
                    logger.warning(f"Unknown category '{category_str}', defaulting to practical")
                    category = TopicCategory.PRACTICAL_IMPLEMENTATION
            except Exception as e:
                logger.warning(f"Category conversion error: {e}, defaulting to practical")
                category = TopicCategory.PRACTICAL_IMPLEMENTATION
            
            # Extract confidence and reasoning
            confidence = float(response.get("confidence", 0.5))
            reasoning = response.get("reasoning", "")
            
            result = TopicCategorizationResult(
                category=category.value,
                confidence=confidence,
                reasoning=reasoning,
                is_ai_related=is_ai_related,
            )
            
            logger.info(f"Query categorized as {category.value} with confidence {confidence:.2f}")
            
            return result
            
        except QueryCategorizationError:
            raise
        except Exception as e:
            logger.error(f"Categorization error: {e}")
            raise QueryCategorizationError(f"Failed to categorize query: {e}")
    
    async def is_ai_related(self, query: str) -> bool:
        """
        Check if a query is AI-related
        
        Args:
            query: User query
        
        Returns:
            True if query is AI-related
        """
        try:
            result = await self.categorize_query(query)
            return result.is_ai_related
        except QueryCategorizationError as e:
            if "not ai related" in str(e).lower():
                return False
            raise
    
    def categorize_by_keywords(self, query: str) -> TopicCategory:
        """
        Quick keyword-based categorization (fallback method)
        Used when LLM is unavailable or for quick checks
        
        Args:
            query: User query
        
        Returns:
            TopicCategory based on keyword matching
        """
        query_lower = query.lower()
        
        # Core AI keywords
        core_ai_keywords = [
            "transformer", "attention mechanism", "neural network",
            "backpropagation", "gradient descent", "loss function",
            "activation function", "convolution", "recurrent",
            "lstm", "gru", "bert", "gpt architecture",
            "self-attention", "multi-head attention",
            "embedding", "tokenization", "research paper",
            "mathematical", "theorem", "proof", "algorithm",
            "complexity", "optimization", "convergence",
        ]
        
        # Practical implementation keywords
        practical_keywords = [
            "how to", "step by step", "tutorial", "guide",
            "implement", "build", "create", "deploy",
            "langchain", "llamaindex", "openai api",
            "huggingface", "pytorch tutorial", "tensorflow tutorial",
            "rag", "retrieval augmented", "vector database",
            "pinecone", "chromadb", "faiss", "weaviate",
            "fine-tune", "fine-tuning", "prompt engineering",
            "api integration", "sdk", "library",
        ]
        
        # Count keyword matches
        core_count = sum(1 for kw in core_ai_keywords if kw in query_lower)
        practical_count = sum(1 for kw in practical_keywords if kw in query_lower)
        
        if core_count > practical_count:
            return TopicCategory.CORE_AI
        elif practical_count > core_count:
            return TopicCategory.PRACTICAL_IMPLEMENTATION
        else:
            # Default to practical for ambiguous queries
            return TopicCategory.PRACTICAL_IMPLEMENTATION


def get_topic_agent(llm: Optional[BedrockLLM] = None) -> TopicAgent:
    """Factory function to create TopicAgent"""
    return TopicAgent(llm=llm)

