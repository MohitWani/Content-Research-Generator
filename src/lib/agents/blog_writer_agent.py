"""
Blog Writer Agent for generating Medium blog posts
Transforms research data into publication-ready content
Maps to: spec.md → Story 3, Story 4, FR4
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

from src.lib.llm.model import BedrockLLM
from src.lib.llm.prompt_loader import load_prompt, get_audience_guidelines
from src.lib.agents.react_research_agent import ResearchOutput
from src.lib.models.exceptions import (
    BlogGenerationError,
    ResearchDataInsufficientError,
)
from src.common.config import config
from src.common.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class BlogOutput:
    """Output from blog writer agent"""
    title: str
    content: str
    meta_description: Optional[str] = None
    tags: list = None
    estimated_reading_time: Optional[str] = None
    target_audience: str = "practitioner"
    tone: str = "professional"
    status: str = "ready"
    file_path: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class BlogWriterAgent:
    """
    Agent for generating Medium blog posts from research data
    Adapts tone and style based on target audience
    """
    
    def __init__(self, llm: Optional[BedrockLLM] = None):
        """
        Initialize blog writer agent
        
        Args:
            llm: LLM instance for content generation
        """
        self.llm = llm or BedrockLLM()
        logger.info("Initialized BlogWriterAgent")
    
    async def generate_blog(
        self,
        research_data: Dict[str, Any] | ResearchOutput,
        target_audience: str = "practitioner",
        tone: str = "professional",
    ) -> BlogOutput:
        """
        Generate a blog post from research data
        
        Args:
            research_data: Research output (dict or ResearchOutput)
            target_audience: beginner, practitioner, or expert
            tone: Writing tone (professional, conversational, technical)
        
        Returns:
            BlogOutput with complete blog post
        
        Raises:
            ResearchDataInsufficientError: If research data is insufficient
            BlogGenerationError: If blog generation fails
        """
        # Convert ResearchOutput to dict if needed
        if isinstance(research_data, ResearchOutput):
            research_dict = {
                "topic_summary": research_data.topic_summary,
                "key_concepts": research_data.key_concepts,
                "mathematical_foundations": research_data.mathematical_foundations,
                "historical_context": research_data.historical_context,
                "implementation_examples": research_data.implementation_examples,
                "sources": research_data.sources,
            }
        else:
            research_dict = research_data
        
        # Validate research data
        self._validate_research_data(research_dict)
        
        try:
            # Format research data for prompt
            research_text = self._format_research_for_prompt(research_dict)
            
            # Get audience-specific guidelines
            audience_guidelines = get_audience_guidelines(target_audience)
            
            # Extract topic for title generation
            topic = research_dict.get("topic_summary", "")[:200]
            
            # Load and format blog prompt
            prompt = load_prompt(
                "blog_prompt",
                topic=topic,
                target_audience=target_audience,
                tone=tone,
                research_data=research_text,
                audience_guidelines=audience_guidelines,
            )
            
            # Generate blog content
            logger.debug(f"Generating blog for audience: {target_audience}")
            
            response = await self.llm.ainvoke(
                prompt=prompt,
                system_prompt=(
                    "You are an expert technical writer creating blog posts for Medium. "
                    "Write engaging, well-structured content. Respond only with valid JSON."
                ),
                parse_json=True,
            )
            
            # Create blog output
            blog_output = BlogOutput(
                title=response.get("title", "Untitled"),
                content=response.get("content", ""),
                meta_description=response.get("meta_description"),
                tags=response.get("tags", []),
                estimated_reading_time=response.get("estimated_reading_time"),
                target_audience=target_audience,
                tone=tone,
                status="ready",
            )
            
            # Validate generated content
            self._validate_blog_output(blog_output)
            
            # Save blog to file
            blog_output.file_path = await self._save_blog(blog_output)
            
            logger.info(f"Generated blog: {blog_output.title}")
            
            return blog_output
            
        except ResearchDataInsufficientError:
            raise
        except Exception as e:
            logger.error(f"Blog generation error: {e}")
            raise BlogGenerationError(f"Failed to generate blog: {e}")
    
    def _validate_research_data(self, research_data: Dict[str, Any]) -> None:
        """Validate that research data is sufficient for blog generation"""
        if not research_data:
            raise ResearchDataInsufficientError("Research data is empty")
        
        topic_summary = research_data.get("topic_summary", "")
        if isinstance(topic_summary, str):
            topic_summary = topic_summary.strip()
        if not topic_summary or len(topic_summary) < 30:
            raise ResearchDataInsufficientError(
                "Insufficient topic summary for blog generation"
            )
        
        sources = research_data.get("sources", [])
        if not sources:
            logger.warning("No sources in research data")
    
    def _format_research_for_prompt(self, research_data: Dict[str, Any]) -> str:
        """Format research data for blog prompt"""
        sections = []
        
        # Topic summary
        if research_data.get("topic_summary"):
            sections.append(f"## Summary\n{research_data['topic_summary']}")
        
        # Key concepts
        if research_data.get("key_concepts"):
            concepts_text = "\n".join([
                f"- **{k}**: {v}"
                for k, v in research_data["key_concepts"].items()
            ])
            sections.append(f"## Key Concepts\n{concepts_text}")
        
        # Mathematical foundations
        if research_data.get("mathematical_foundations"):
            sections.append(
                f"## Mathematical Foundations\n{research_data['mathematical_foundations']}"
            )
        
        # Historical context
        if research_data.get("historical_context"):
            sections.append(
                f"## Historical Context\n{research_data['historical_context']}"
            )
        
        # Implementation examples
        if research_data.get("implementation_examples"):
            sections.append(
                f"## Implementation\n{research_data['implementation_examples']}"
            )
        
        # Sources
        if research_data.get("sources"):
            sources_text = "\n".join([
                f"- [{s.get('title', 'Source')}]({s.get('url', '')})"
                for s in research_data["sources"][:10]
            ])
            sections.append(f"## Sources\n{sources_text}")
        
        return "\n\n".join(sections)
    
    def _validate_blog_output(self, blog: BlogOutput) -> None:
        """Validate generated blog content"""
        # Check for placeholders
        content = blog.content
        placeholders = ["[PLACEHOLDER]", "[TODO]", "[INSERT", "[[", "]]"]
        for placeholder in placeholders:
            if placeholder in content:
                logger.warning(f"Placeholder found in content: {placeholder}")
        
        # Check minimum length
        if len(content) < 500:
            logger.warning("Generated blog is quite short")
        
        # Check for structure
        if "#" not in content:
            logger.warning("No headers found in blog content")
    
    async def _save_blog(self, blog: BlogOutput) -> str:
        """Save blog to file"""
        try:
            # Create timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(
                c if c.isalnum() else "_" 
                for c in blog.title[:50]
            )
            filename = f"{timestamp}_{safe_title}.md"
            
            # Ensure blog directory exists
            blog_dir = config.CONTENT_DIR / "blogs"
            blog_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = blog_dir / filename
            
            # Add metadata as frontmatter
            frontmatter = f"""---
title: "{blog.title}"
target_audience: {blog.target_audience}
tone: {blog.tone}
tags: {json.dumps(blog.tags)}
reading_time: "{blog.estimated_reading_time or 'Unknown'}"
created_at: "{datetime.now().isoformat()}"
status: {blog.status}
---

"""
            
            filepath.write_text(frontmatter + blog.content)
            
            logger.debug(f"Saved blog to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save blog: {e}")
            return ""
    
    async def adapt_tone(
        self,
        content: str,
        original_audience: str,
        new_audience: str,
    ) -> str:
        """
        Adapt existing content for a different audience
        
        Args:
            content: Original blog content
            original_audience: Original target audience
            new_audience: New target audience
        
        Returns:
            Adapted content
        """
        if original_audience == new_audience:
            return content
        
        try:
            prompt = f"""
Adapt the following blog post from {original_audience} audience to {new_audience} audience.

{get_audience_guidelines(new_audience)}

Original content:
{content}

Provide the adapted content only, maintaining the same structure but adjusting:
- Language complexity
- Technical depth
- Examples and analogies
- Assumed knowledge level
"""
            
            response = await self.llm.ainvoke(
                prompt=prompt,
                system_prompt="You are an expert content adapter.",
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Tone adaptation error: {e}")
            return content


def get_blog_writer_agent(llm: Optional[BedrockLLM] = None) -> BlogWriterAgent:
    """Factory function to create BlogWriterAgent"""
    return BlogWriterAgent(llm=llm)

