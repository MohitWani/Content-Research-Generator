"""
AI Agents for research and content generation
"""
from src.lib.agents.topic_agent import TopicAgent, get_topic_agent
from src.lib.agents.agentic_researcher import (
    AgenticResearcher,
    ResearchOutput,
    get_agentic_researcher,
)
from src.lib.agents.blog_writer_agent import (
    BlogWriterAgent,
    BlogOutput,
    get_blog_writer_agent,
)
from src.lib.agents.shortform_agent import (
    ShortformAgent,
    LinkedInPost,
    SocialThread,
    get_shortform_agent,
)
from src.lib.agents.branding_agent import (
    BrandingAgent,
    VoiceProfile,
    BrandingResult,
    get_branding_agent,
)
from src.lib.agents.arxiv_paper_research_agent import (
    ArXivPaperResearchAgent,
    PaperResearchOutput,
    PaperMetadata,
    get_arxiv_paper_research_agent,
)

# Backward compatibility aliases
ResearchAgent = AgenticResearcher
ReActResearchAgent = AgenticResearcher
get_research_agent = get_agentic_researcher
get_react_research_agent = get_agentic_researcher

__all__ = [
    # Topic Agent
    "TopicAgent",
    "get_topic_agent",
    # Agentic Researcher (Modern)
    "AgenticResearcher",
    "ResearchOutput",
    "get_agentic_researcher",
    # Backward compatibility aliases
    "ReActResearchAgent",
    "ResearchAgent",
    "get_react_research_agent",
    "get_research_agent",
    # Blog Writer Agent
    "BlogWriterAgent",
    "BlogOutput",
    "get_blog_writer_agent",
    # Shortform Agent
    "ShortformAgent",
    "LinkedInPost",
    "SocialThread",
    "get_shortform_agent",
    # Branding Agent
    "BrandingAgent",
    "VoiceProfile",
    "BrandingResult",
    "get_branding_agent",
    # ArXiv Paper Research Agent
    "ArXivPaperResearchAgent",
    "PaperResearchOutput",
    "PaperMetadata",
    "get_arxiv_paper_research_agent",
]
