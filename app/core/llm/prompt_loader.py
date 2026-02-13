"""
Prompt loading and management utilities
"""
from app.core.llm.prompts import (
    BlogPrompt,
    BrandingPrompt,
    LinkedInPostPrompt,
    PaperBlogPrompt,
    PaperResearchPrompt,
    ResearchPrompt,
    TopicCategorizationPrompt,
    TwitterThreadPrompt,
    prompts,
)


# ============= Category Guidelines =============

REACT_CATEGORY_GUIDELINES = {
    'core_ai': """- Use arxiv_search to find foundational papers
- Use wikipedia_search for historical context
- Use web_search for explanations and tutorials
- Use github_search for canonical implementations
- Focus on mathematical formulations and theoretical foundations""",
    'practical_implementation': """- Use github_search to find working code examples
- Use web_search for tutorials and best practices
- Use arxiv_search for recent applied research
- Focus on production-ready implementations
- Include deployment and scaling considerations""",
    'software_development': """- Use github_search for best practices and design patterns
- Use web_search for tutorials and documentation
- Focus on code quality, testing, and maintainability
- Include architectural considerations""",
    'web_development': """- Use web_search for modern frameworks and libraries
- Use github_search for popular implementations
- Focus on frontend/backend integration
- Include performance and security best practices""",
    'devops': """- Use web_search for tooling and automation
- Use github_search for infrastructure-as-code examples
- Focus on CI/CD, containerization, and cloud services
- Include monitoring and observability practices""",
    'general_tech': """- Use web_search for general information
- Use wikipedia for background context
- Use github_search for practical examples
- Balance breadth and depth of coverage""",
}


AUDIENCE_GUIDELINES = {
    'beginner': """## Beginner Audience Guidelines
- Use simple, clear language
- Include analogies to familiar concepts
- Define technical terms when first used
- Keep code examples simple and well-commented
- Focus on "why" before "how"
""",
    'practitioner': """## Practitioner Audience Guidelines
- Balance theory with practical application
- Include production-ready code examples
- Reference industry best practices
- Assume familiarity with basic concepts
- Focus on implementation details
""",
    'expert': """## Expert Audience Guidelines
- Include advanced technical details
- Reference academic literature
- Discuss edge cases and optimizations
- Assume deep domain knowledge
- Focus on cutting-edge developments
""",
}


CORE_AI_REQUIREMENTS = """
For this CORE AI topic, ensure your research includes:
1. **Mathematical Foundations**: Include relevant formulas, equations, and mathematical explanations
2. **Historical Context**: Trace the evolution of this concept and key milestones
3. **Simple Explanation**: Provide an accessible explanation for learning purposes
4. **Python Implementation**: Include working code examples demonstrating the concepts
5. **Academic Sources**: Reference relevant research papers and academic resources
"""

PRACTICAL_REQUIREMENTS = """
For this PRACTICAL IMPLEMENTATION topic, ensure your research includes:
1. **Step-by-Step Guide**: Provide clear, actionable instructions
2. **Deep Technical Information**: Include comprehensive technical details
3. **Code Examples**: Include working, production-ready code snippets
4. **Best Practices**: Highlight common patterns and recommendations
5. **Troubleshooting**: Address common issues and their solutions
"""


# ============= Helper Functions =============


def get_react_category_guidelines(category: str) -> str:
    """Get ReAct agent research guidelines based on topic category"""
    return REACT_CATEGORY_GUIDELINES.get(
        category, REACT_CATEGORY_GUIDELINES.get('general_tech', '')
    )


def get_audience_guidelines(audience: str) -> str:
    """Get audience-specific guidelines"""
    return AUDIENCE_GUIDELINES.get(audience, AUDIENCE_GUIDELINES['practitioner'])


def get_category_requirements(category: str) -> str:
    """Get research requirements based on topic category"""
    if category == 'core_ai':
        return CORE_AI_REQUIREMENTS
    return PRACTICAL_REQUIREMENTS


# ============= Prompt Access Functions =============


def get_research_prompts() -> ResearchPrompt:
    """Get the research prompt class instance"""
    return prompts.research


def get_topic_prompts() -> TopicCategorizationPrompt:
    """Get the topic categorization prompt class instance"""
    return prompts.topic


def get_blog_prompts() -> BlogPrompt:
    """Get the blog prompt class instance"""
    return prompts.blog


def get_linkedin_prompts() -> LinkedInPostPrompt:
    """Get the LinkedIn prompt class instance"""
    return prompts.linkedin


def get_twitter_prompts() -> TwitterThreadPrompt:
    """Get the Twitter prompt class instance"""
    return prompts.twitter


def get_branding_prompts() -> BrandingPrompt:
    """Get the branding prompt class instance"""
    return prompts.branding


def get_paper_prompts() -> PaperResearchPrompt:
    """Get the paper research prompt class instance"""
    return prompts.paper


def get_paper_blog_prompts() -> PaperBlogPrompt:
    """Get the paper blog prompt class instance"""
    return prompts.paper_blog


