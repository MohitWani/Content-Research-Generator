"""
Topic categorization prompts
Following prompting best practices
"""
from src.lib.llm.prompts.base import BasePrompt


class TopicCategorizationPrompt(BasePrompt):
    """
    Prompts for topic categorization agent
    System prompt defines role, categories, and output format
    User prompt is clean query only
    """
    
    SYSTEM_TEMPLATE = """You are an expert technical topic classifier.

## Your Role
Analyze queries and categorize them into the most appropriate technical category.

## Categories

1. **core_ai**
   - Fundamental AI/ML research and theory
   - Neural network architectures
   - Research papers and mathematical foundations
   - Examples: transformers, attention mechanisms, backpropagation

2. **practical_implementation**
   - AI tools, frameworks, and libraries
   - Step-by-step implementation guides
   - Examples: LangChain, RAG, fine-tuning, prompt engineering

3. **software_development**
   - General software engineering
   - Design patterns, testing, system design
   - Examples: clean code, microservices, API design

4. **web_development**
   - Frontend and backend web technologies
   - Databases and web frameworks
   - Examples: React, Node.js, REST APIs, GraphQL

5. **devops**
   - Infrastructure and deployment
   - CI/CD and cloud services
   - Examples: Docker, Kubernetes, AWS, monitoring

6. **general_tech**
   - Other technology topics
   - Examples: blockchain, IoT, cybersecurity

## Classification Guidelines
- Choose the MOST specific matching category
- Consider the primary intent of the query
- If unclear, prefer more specific categories over general_tech

## Output Format

Respond with JSON:
```json
{
    "category": "category_key",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "is_ai_related": true/false
}
```"""

    USER_TEMPLATE = """{query}"""

    def system_prompt(self, **kwargs) -> str:
        return self.SYSTEM_TEMPLATE
    
    def user_prompt(self, query: str, **kwargs) -> str:
        return self.format(self.USER_TEMPLATE, query=query)
