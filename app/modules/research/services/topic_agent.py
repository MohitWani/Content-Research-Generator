"""
Topic Agent for query categorization
"""
from typing import Optional

from app.common.exceptions.research_exceptions import QueryCategorizationError
from app.core.llm.bedrock_llm import BedrockLLM
from app.core.llm.prompts import prompts
from app.core.logging.logger import logger
from app.modules.research.models.research_model import TopicCategory
from app.modules.research.schemas.research_schemas import TopicCategorizationResult

# Category mapping for string to enum conversion
CATEGORY_MAP = {
    'core_ai': TopicCategory.CORE_AI,
    'practical_implementation': TopicCategory.PRACTICAL_IMPLEMENTATION,
    'software_development': TopicCategory.SOFTWARE_DEVELOPMENT,
    'web_development': TopicCategory.WEB_DEVELOPMENT,
    'devops': TopicCategory.DEVOPS,
    'general_tech': TopicCategory.GENERAL_TECH,
}


class TopicAgent:
    """Agent for categorizing research queries"""

    def __init__(self, llm: Optional[BedrockLLM] = None):
        self.llm = llm or BedrockLLM()
        logger.info('Initialized TopicAgent')

    async def categorize_query(self, query: str) -> TopicCategorizationResult:
        """Categorize a research query"""
        if not query or not query.strip():
            raise QueryCategorizationError('Query cannot be empty')

        query = query.strip()

        try:
            system_prompt = prompts.topic.system_prompt()
            user_prompt = prompts.topic.user_prompt(query=query)

            logger.debug(f'Categorizing query using Topic agent: {query[:100]}...')

            response = await self.llm.ainvoke(
                prompt=user_prompt,
                system_prompt=system_prompt,
                parse_json=True,
            )

            logger.info(f'Response from Topic agent: {str(response)[:100]}...')

            if not isinstance(response, dict):
                logger.error(
                    f'Invalid response format: expected dict, got {type(response)}'
                )
                raise QueryCategorizationError(
                    f'Invalid response format: expected dict, got {type(response)}'
                )

            category_str = response.get('category', 'general_tech')
            is_ai_related = response.get('is_ai_related', False)

            category = CATEGORY_MAP.get(category_str)
            if category is None:
                logger.warning(
                    f"Unknown category '{category_str}', defaulting to general_tech"
                )
                category = TopicCategory.GENERAL_TECH

            confidence = float(response.get('confidence', 0.5))
            reasoning = response.get('reasoning', '')

            result = TopicCategorizationResult(
                category=category.value,
                confidence=confidence,
                reasoning=reasoning,
                is_ai_related=is_ai_related,
            )

            logger.info(
                f'Query: {query} categorized as {category.value} '
                f'with confidence {confidence:.2f}'
            )

            return result

        except QueryCategorizationError:
            raise
        except Exception as e:
            logger.error(f'Categorization error: {e}')
            logger.info('Falling back to keyword-based categorization')
            category = self.categorize_by_keywords(query)
            return TopicCategorizationResult(
                category=category.value,
                confidence=0.5,
                reasoning='Fallback keyword-based categorization',
                is_ai_related=category
                in [TopicCategory.CORE_AI, TopicCategory.PRACTICAL_IMPLEMENTATION],
            )

    async def is_ai_related(self, query: str) -> bool:
        """Check if a query is AI-related"""
        try:
            result = await self.categorize_query(query)
            return result.is_ai_related
        except Exception:
            return False

    def categorize_by_keywords(self, query: str) -> TopicCategory:
        """Quick keyword-based categorization (fallback method)"""
        query_lower = query.lower()

        core_ai_keywords = [
            'transformer',
            'attention mechanism',
            'neural network',
            'backpropagation',
            'gradient descent',
            'loss function',
            'activation function',
            'convolution',
            'recurrent',
            'lstm',
            'gru',
            'bert',
            'gpt architecture',
            'self-attention',
            'multi-head attention',
            'embedding',
            'tokenization',
            'research paper',
            'mathematical',
            'theorem',
            'proof',
            'algorithm complexity',
            'optimization',
            'convergence',
            'deep learning',
        ]

        practical_ai_keywords = [
            'langchain',
            'llamaindex',
            'openai api',
            'huggingface',
            'pytorch',
            'tensorflow',
            'rag',
            'retrieval augmented',
            'vector database',
            'pinecone',
            'chromadb',
            'faiss',
            'weaviate',
            'fine-tune',
            'fine-tuning',
            'prompt engineering',
            'llm',
            'large language model',
            'chatgpt',
            'claude',
            'gemini',
            'ai agent',
            'ai tool',
        ]

        software_dev_keywords = [
            'design pattern',
            'clean code',
            'solid principles',
            'unit test',
            'integration test',
            'tdd',
            'bdd',
            'refactor',
            'architecture',
            'microservice',
            'api design',
            'data structure',
            'algorithm',
            'git',
            'version control',
            'code review',
        ]

        web_dev_keywords = [
            'react',
            'vue',
            'angular',
            'javascript',
            'typescript',
            'node.js',
            'express',
            'fastapi',
            'django',
            'flask',
            'html',
            'css',
            'frontend',
            'backend',
            'fullstack',
            'rest api',
            'graphql',
            'websocket',
            'sql',
            'postgresql',
            'mongodb',
            'redis',
        ]

        devops_keywords = [
            'docker',
            'kubernetes',
            'k8s',
            'container',
            'ci/cd',
            'jenkins',
            'github actions',
            'gitlab',
            'aws',
            'azure',
            'gcp',
            'cloud',
            'terraform',
            'ansible',
            'helm',
            'monitoring',
            'prometheus',
            'grafana',
            'deployment',
            'infrastructure',
        ]

        scores = {
            TopicCategory.CORE_AI: sum(
                1 for kw in core_ai_keywords if kw in query_lower
            ),
            TopicCategory.PRACTICAL_IMPLEMENTATION: sum(
                1 for kw in practical_ai_keywords if kw in query_lower
            ),
            TopicCategory.SOFTWARE_DEVELOPMENT: sum(
                1 for kw in software_dev_keywords if kw in query_lower
            ),
            TopicCategory.WEB_DEVELOPMENT: sum(
                1 for kw in web_dev_keywords if kw in query_lower
            ),
            TopicCategory.DEVOPS: sum(
                1 for kw in devops_keywords if kw in query_lower
            ),
        }

        max_score = max(scores.values())
        if max_score > 0:
            for category, score in scores.items():
                if score == max_score:
                    return category

        return TopicCategory.GENERAL_TECH


def get_topic_agent(llm: Optional[BedrockLLM] = None) -> TopicAgent:
    """Factory function to create TopicAgent"""
    return TopicAgent(llm=llm)


