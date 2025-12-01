"""
Shortform Agent for generating LinkedIn posts and social content
Transforms research/blog content into concise social media posts
Maps to: spec.md → FR5 (Multi-format Content)
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

from src.lib.llm.model import BedrockLLM
from src.lib.llm.prompt_loader import load_prompt, get_audience_guidelines
from src.lib.agents.react_research_agent import ResearchOutput
from src.lib.agents.blog_writer_agent import BlogOutput
from src.lib.models.exceptions import ContentGenerationError
from src.common.config import config
from src.common.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class LinkedInPost:
    """Output from shortform agent for LinkedIn"""
    content: str
    hook: str  # Opening line to grab attention
    call_to_action: Optional[str] = None
    hashtags: List[str] = None
    character_count: int = 0
    target_audience: str = "practitioner"
    status: str = "ready"
    file_path: Optional[str] = None
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []
        self.character_count = len(self.content)


@dataclass
class ThreadPost:
    """A single post in a thread"""
    position: int
    content: str
    character_count: int = 0
    
    def __post_init__(self):
        self.character_count = len(self.content)


@dataclass
class SocialThread:
    """Thread of posts (for X/Twitter style)"""
    posts: List[ThreadPost]
    topic: str
    total_posts: int = 0
    
    def __post_init__(self):
        self.total_posts = len(self.posts)


class ShortformAgent:
    """
    Agent for generating short-form social media content
    Optimized for LinkedIn, X/Twitter, and other platforms
    """
    
    # Platform character limits
    LINKEDIN_LIMIT = 3000
    TWITTER_LIMIT = 280
    
    def __init__(self, llm: Optional[BedrockLLM] = None):
        """
        Initialize shortform agent
        
        Args:
            llm: LLM instance for content generation
        """
        self.llm = llm or BedrockLLM()
        logger.info("Initialized ShortformAgent")
    
    async def generate_linkedin_post(
        self,
        source_content: Dict[str, Any] | ResearchOutput | BlogOutput,
        target_audience: str = "practitioner",
        include_hashtags: bool = True,
        include_cta: bool = True,
    ) -> LinkedInPost:
        """
        Generate a LinkedIn post from research or blog content
        
        Args:
            source_content: Research output, blog output, or dict
            target_audience: Target audience
            include_hashtags: Include relevant hashtags
            include_cta: Include call-to-action
        
        Returns:
            LinkedInPost with formatted content
        """
        # Extract content based on type
        content_text = self._extract_content(source_content)
        topic = self._extract_topic(source_content)
        
        try:
            # Get audience guidelines
            audience_guidelines = get_audience_guidelines(target_audience)
            
            # Build prompt for LinkedIn post
            prompt = f"""Create a compelling LinkedIn post about the following topic.

Topic: {topic}

Source Content:
{content_text[:3000]}

Guidelines:
- Target audience: {target_audience}
- {audience_guidelines}
- Start with a strong hook (attention-grabbing first line)
- Keep it under {self.LINKEDIN_LIMIT} characters
- Use short paragraphs and line breaks for readability
- {"Include 3-5 relevant hashtags" if include_hashtags else "No hashtags needed"}
- {"End with a call-to-action" if include_cta else "No CTA needed"}
- Be authentic and conversational
- Share insights, not just information

Respond with JSON:
{{
    "hook": "The attention-grabbing first line",
    "content": "Full post content including hook",
    "hashtags": ["hashtag1", "hashtag2"],
    "call_to_action": "Optional CTA text"
}}"""
            
            response = await self.llm.ainvoke(
                prompt=prompt,
                system_prompt="You are an expert LinkedIn content creator. Write engaging, professional posts.",
                parse_json=True,
            )
            
            # Validate response
            if not isinstance(response, dict) or "content" not in response:
                raise ContentGenerationError("Invalid response format")
            
            post = LinkedInPost(
                content=response.get("content", ""),
                hook=response.get("hook", ""),
                call_to_action=response.get("call_to_action") if include_cta else None,
                hashtags=response.get("hashtags", []) if include_hashtags else [],
                target_audience=target_audience,
            )
            
            # Validate length
            if post.character_count > self.LINKEDIN_LIMIT:
                logger.warning(f"Post exceeds limit: {post.character_count} chars")
            
            # Save post
            post.file_path = await self._save_post(post, "linkedin")
            
            logger.info(f"Generated LinkedIn post: {post.character_count} chars")
            return post
            
        except Exception as e:
            logger.error(f"LinkedIn post generation error: {e}")
            raise ContentGenerationError(f"Failed to generate LinkedIn post: {e}")
    
    async def generate_thread(
        self,
        source_content: Dict[str, Any] | ResearchOutput | BlogOutput,
        max_posts: int = 5,
        platform: str = "twitter",
    ) -> SocialThread:
        """
        Generate a thread of posts for X/Twitter
        
        Args:
            source_content: Source content
            max_posts: Maximum number of posts in thread
            platform: Platform (twitter, threads)
        
        Returns:
            SocialThread with multiple posts
        """
        content_text = self._extract_content(source_content)
        topic = self._extract_topic(source_content)
        
        char_limit = self.TWITTER_LIMIT if platform == "twitter" else 500
        
        try:
            prompt = f"""Create a {max_posts}-post thread about the following topic.

Topic: {topic}

Source Content:
{content_text[:4000]}

Guidelines:
- Each post must be under {char_limit} characters
- First post should hook the reader
- Each post should flow naturally to the next
- Last post should wrap up with a takeaway
- Number each post (1/, 2/, etc.)

Respond with JSON:
{{
    "posts": [
        {{"position": 1, "content": "1/ First post..."}},
        {{"position": 2, "content": "2/ Second post..."}}
    ]
}}"""
            
            response = await self.llm.ainvoke(
                prompt=prompt,
                system_prompt="You are an expert social media thread creator.",
                parse_json=True,
            )
            
            posts = [
                ThreadPost(
                    position=p.get("position", i + 1),
                    content=p.get("content", ""),
                )
                for i, p in enumerate(response.get("posts", []))
            ]
            
            thread = SocialThread(
                posts=posts,
                topic=topic,
            )
            
            logger.info(f"Generated thread with {thread.total_posts} posts")
            return thread
            
        except Exception as e:
            logger.error(f"Thread generation error: {e}")
            raise ContentGenerationError(f"Failed to generate thread: {e}")
    
    async def summarize_for_social(
        self,
        content: str,
        max_length: int = 280,
    ) -> str:
        """
        Create a brief social media summary
        
        Args:
            content: Content to summarize
            max_length: Maximum character length
        
        Returns:
            Summarized content
        """
        try:
            prompt = f"""Summarize this content for social media in under {max_length} characters:

{content[:2000]}

Keep it punchy, informative, and engaging. No hashtags."""
            
            response = await self.llm.ainvoke(
                prompt=prompt,
                system_prompt="You create concise, engaging social media summaries.",
            )
            
            # Ensure within limit
            if len(response) > max_length:
                response = response[:max_length - 3] + "..."
            
            return response
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return content[:max_length - 3] + "..."
    
    def _extract_content(self, source: Any) -> str:
        """Extract text content from various source types"""
        if isinstance(source, ResearchOutput):
            parts = [source.topic_summary or ""]
            if source.key_concepts:
                parts.append("Key concepts: " + ", ".join(source.key_concepts.keys()))
            return "\n\n".join(parts)
        elif isinstance(source, BlogOutput):
            return source.content or ""
        elif isinstance(source, dict):
            return source.get("content") or source.get("topic_summary") or str(source)
        else:
            return str(source)
    
    def _extract_topic(self, source: Any) -> str:
        """Extract topic from source"""
        if isinstance(source, ResearchOutput):
            return (source.topic_summary or "")[:100]
        elif isinstance(source, BlogOutput):
            return source.title or ""
        elif isinstance(source, dict):
            return source.get("title") or source.get("topic") or "AI Topic"
        else:
            return "AI Topic"
    
    async def _save_post(self, post: LinkedInPost, platform: str) -> str:
        """Save post to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{platform}_post.md"
            
            post_dir = config.CONTENT_DIR / "linkedin_posts"
            post_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = post_dir / filename
            
            content = f"""---
platform: {platform}
target_audience: {post.target_audience}
character_count: {post.character_count}
hashtags: {json.dumps(post.hashtags)}
created_at: {datetime.now().isoformat()}
---

{post.content}
"""
            filepath.write_text(content)
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save post: {e}")
            return ""


def get_shortform_agent(llm: Optional[BedrockLLM] = None) -> ShortformAgent:
    """Factory function to create ShortformAgent"""
    return ShortformAgent(llm=llm)

