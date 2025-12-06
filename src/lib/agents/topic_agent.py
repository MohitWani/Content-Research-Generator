"""
Topic Agent for query categorization
Categorizes user queries into AI, software development, and tech topics
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

# Category mapping for string to enum conversion
CATEGORY_MAP = {
    "core_ai": TopicCategory.CORE_AI,
    "practical_implementation": TopicCategory.PRACTICAL_IMPLEMENTATION,
    "software_development": TopicCategory.SOFTWARE_DEVELOPMENT,
    "web_development": TopicCategory.WEB_DEVELOPMENT,
    "devops": TopicCategory.DEVOPS,
    "general_tech": TopicCategory.GENERAL_TECH,
}


class TopicAgent:
    """
    Agent for categorizing research queries
    Handles AI, software development, and general tech topics
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
            # Build categorization prompt
            prompt = f"""Analyze this research query and categorize it.

Query: {query}

Categories:
1. core_ai - Core AI/ML concepts, algorithms, research papers, mathematical foundations
   Examples: transformer architecture, attention mechanism, neural networks, backpropagation
   
2. practical_implementation - Practical AI implementation, tools, frameworks, tutorials
   Examples: how to use LangChain, RAG implementation, fine-tuning models, prompt engineering
   
3. software_development - General software development, programming, system design
   Examples: design patterns, clean code, testing, API design, microservices
   
4. web_development - Web technologies, frontend, backend, databases
   Examples: React, Node.js, REST APIs, GraphQL, SQL, MongoDB
   
5. devops - DevOps, cloud, infrastructure, deployment
   Examples: Docker, Kubernetes, CI/CD, AWS, Azure, monitoring
   
6. general_tech - Other technology topics
   Examples: blockchain, IoT, cybersecurity, general tech news

Respond with JSON:
{{
    "category": "one of the category keys above",
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of categorization",
    "is_ai_related": true/false (whether this is an AI/ML topic)
}}"""
            
            logger.debug(f"Categorizing query: {query[:100]}...")
            
            response = await self.llm.ainvoke(
                prompt=prompt,
                system_prompt="You are an expert tech topic classifier. Categorize queries accurately. Respond only with valid JSON.",
                parse_json=True,
            )
            
            # Validate response structure
            if not isinstance(response, dict):
                raise QueryCategorizationError(f"Invalid response format: expected dict, got {type(response)}")
            
            # Parse category - no longer reject non-AI queries
            category_str = response.get("category", "general_tech")
            is_ai_related = response.get("is_ai_related", False)
            
            # Convert to enum
            category = CATEGORY_MAP.get(category_str)
            if category is None:
                logger.warning(f"Unknown category '{category_str}', defaulting to general_tech")
                category = TopicCategory.GENERAL_TECH
            
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
            # Fallback to keyword-based categorization
            logger.info("Falling back to keyword-based categorization")
            category = self.categorize_by_keywords(query)
            return TopicCategorizationResult(
                category=category.value,
                confidence=0.5,
                reasoning="Fallback keyword-based categorization",
                is_ai_related=category in [TopicCategory.CORE_AI, TopicCategory.PRACTICAL_IMPLEMENTATION],
            )
    
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
        except Exception:
            return False
    
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
            "mathematical", "theorem", "proof", "algorithm complexity",
            "optimization", "convergence", "deep learning",
        ]
        
        # Practical AI implementation keywords
        practical_ai_keywords = [
            "langchain", "llamaindex", "openai api",
            "huggingface", "pytorch", "tensorflow",
            "rag", "retrieval augmented", "vector database",
            "pinecone", "chromadb", "faiss", "weaviate",
            "fine-tune", "fine-tuning", "prompt engineering",
            "llm", "large language model", "chatgpt",
            "claude", "gemini", "ai agent", "ai tool",
        ]
        
        # Software development keywords
        software_dev_keywords = [
            "design pattern", "clean code", "solid principles",
            "unit test", "integration test", "tdd", "bdd",
            "refactor", "architecture", "microservice",
            "api design", "data structure", "algorithm",
            "git", "version control", "code review",
        ]
        
        # Web development keywords
        web_dev_keywords = [
            "react", "vue", "angular", "javascript", "typescript",
            "node.js", "express", "fastapi", "django", "flask",
            "html", "css", "frontend", "backend", "fullstack",
            "rest api", "graphql", "websocket",
            "sql", "postgresql", "mongodb", "redis",
        ]
        
        # DevOps keywords
        devops_keywords = [
            "docker", "kubernetes", "k8s", "container",
            "ci/cd", "jenkins", "github actions", "gitlab",
            "aws", "azure", "gcp", "cloud",
            "terraform", "ansible", "helm",
            "monitoring", "prometheus", "grafana",
            "deployment", "infrastructure",
        ]
        
        # Count keyword matches
        scores = {
            TopicCategory.CORE_AI: sum(1 for kw in core_ai_keywords if kw in query_lower),
            TopicCategory.PRACTICAL_IMPLEMENTATION: sum(1 for kw in practical_ai_keywords if kw in query_lower),
            TopicCategory.SOFTWARE_DEVELOPMENT: sum(1 for kw in software_dev_keywords if kw in query_lower),
            TopicCategory.WEB_DEVELOPMENT: sum(1 for kw in web_dev_keywords if kw in query_lower),
            TopicCategory.DEVOPS: sum(1 for kw in devops_keywords if kw in query_lower),
        }
        
        # Find category with highest score
        max_score = max(scores.values())
        if max_score > 0:
            for category, score in scores.items():
                if score == max_score:
                    return category
        
        # Default to general_tech for unknown queries
        return TopicCategory.GENERAL_TECH


def get_topic_agent(llm: Optional[BedrockLLM] = None) -> TopicAgent:
    """Factory function to create TopicAgent"""
    return TopicAgent(llm=llm)
