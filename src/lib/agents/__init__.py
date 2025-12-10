"""
AI Agents for research and content generation
"""
from src.lib.agents.topic_agent import TopicAgent, get_topic_agent
from src.lib.agents.react_research_agent import (
    ReActResearchAgent,
    ResearchOutput,
    get_react_research_agent,
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

# Alias for backward compatibility
ResearchAgent = ReActResearchAgent
get_research_agent = get_react_research_agent

__all__ = [
    # Topic Agent
    "TopicAgent",
    "get_topic_agent",
    # Research Agent (ReAct)
    "ReActResearchAgent",
    "ResearchAgent",  # Alias
    "ResearchOutput",
    "get_react_research_agent",
    "get_research_agent",  # Alias
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
