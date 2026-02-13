"""
Blog Writer Node

Contains the core agent logic for generating blog posts from research data.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.config.environment_config import settings
from app.core.llm.bedrock_llm import BedrockLLM
from app.core.llm.prompt_loader import get_audience_guidelines
from app.core.logging.logger import logger
from app.modules.content.services.prompts import content_prompts
from app.modules.research.services.agentic_researcher import ResearchOutput


class BlogOutput(BaseModel):
    """Structured output from blog writer node"""

    title: str = Field(default='', description='Blog post title')
    content: str = Field(default='', description='Full markdown content')
    meta_description: str = Field(default='', description='SEO meta description')
    tags: List[str] = Field(default_factory=list, description='Blog tags')
    estimated_reading_time: str = Field(default='5 min read', description='Reading time')
    file_path: Optional[str] = Field(None, description='Saved file path')


class BlogWriterNode:
    """
    Blog Writer Node - Core agent execution logic.
    
    Handles:
    - LLM initialization
    - Prompt construction
    - Blog generation execution
    - Response parsing
    - File saving
    """

    def __init__(self, llm: Optional[BedrockLLM] = None):
        """
        Initialize the blog writer node.
        
        Args:
            llm: Language model instance (defaults to BedrockLLM)
        """
        logger.info("[BLOG_NODE] Initializing BlogWriterNode...")
        self.llm = llm or BedrockLLM()
        logger.info("[BLOG_NODE] Initialized successfully")

    async def execute(
        self,
        topic: str,
        research_data: ResearchOutput,
        target_audience: str = 'practitioner',
        tone: str = 'professional',
    ) -> BlogOutput:
        """
        Execute blog generation from research data.
        
        Args:
            topic: Blog topic/title
            research_data: Research output to transform
            target_audience: Target audience (beginner, practitioner, expert)
            tone: Writing tone (professional, conversational, technical)
            
        Returns:
            BlogOutput with generated content
        """
        logger.info(
            f"[BLOG_NODE] Starting execution: topic='{topic[:50]}...', "
            f"audience={target_audience}, tone={tone}"
        )

        try:
            # Format research data for the prompt
            formatted_research = self._format_research_data(research_data)

            # Get audience guidelines
            audience_guidelines = get_audience_guidelines(target_audience)

            # Build prompts
            system_prompt = content_prompts.blog.system_prompt()
            user_prompt = content_prompts.blog.user_prompt(
                topic=topic,
                target_audience=target_audience,
                tone=tone,
                research_data=formatted_research,
                audience_guidelines=audience_guidelines,
            )

            logger.debug("[BLOG_NODE] Invoking LLM...")
            
            # Generate blog content
            response = await self.llm.ainvoke(
                prompt=user_prompt,
                system_prompt=system_prompt,
                parse_json=True,
            )

            logger.info("[BLOG_NODE] LLM response received")

            # Parse response
            output = self._parse_response(response, topic)

            # Save blog to file
            output.file_path = await self._save_blog(topic, output)

            logger.info(
                f"[BLOG_NODE] Execution complete: "
                f"content_length={len(output.content)}, tags={len(output.tags)}"
            )
            return output

        except Exception as e:
            logger.error(f"[BLOG_NODE] Execution failed: {e}", exc_info=True)
            return BlogOutput(
                title=f'Blog: {topic}',
                content=f'Blog generation failed: {str(e)}',
                meta_description='',
                tags=[],
            )

    def _format_research_data(self, research: ResearchOutput) -> str:
        """Format research output for blog generation prompt"""
        parts = []

        # Topic summary
        if research.topic_summary:
            parts.append(f'## Topic Summary\n{research.topic_summary}')

        # Key concepts
        if research.key_concepts:
            concepts = '\n'.join(
                [f'- **{k}**: {v}' for k, v in research.key_concepts.items()]
            )
            parts.append(f'## Key Concepts\n{concepts}')

        # Mathematical foundations
        if research.mathematical_foundations:
            parts.append(f'## Mathematical Foundations\n{research.mathematical_foundations}')

        # Implementation examples
        if research.implementation_examples:
            parts.append(f'## Implementation Examples\n{research.implementation_examples}')

        # Sources
        if research.sources:
            sources = '\n'.join(
                [f"- {s.get('tool', 'source')}: {s.get('query', '')[:100]}" for s in research.sources[:10]]
            )
            parts.append(f'## Sources Referenced\n{sources}')

        return '\n\n'.join(parts) if parts else 'No research data available'

    def _parse_response(self, response: Dict[str, Any], topic: str) -> BlogOutput:
        """Parse LLM response into BlogOutput"""
        if not isinstance(response, dict):
            logger.warning('[BLOG_NODE] Response not a dict, using fallback')
            return BlogOutput(
                title=f'Blog: {topic}',
                content=str(response) if response else '',
            )

        return BlogOutput(
            title=response.get('title', f'Blog: {topic}'),
            content=response.get('content', ''),
            meta_description=response.get('meta_description', '')[:160],
            tags=response.get('tags', [])[:10],
            estimated_reading_time=response.get('estimated_reading_time', '5 min read'),
        )

    async def _save_blog(self, topic: str, output: BlogOutput) -> str:
        """Save blog to markdown file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_topic = ''.join(c if c.isalnum() else '_' for c in topic[:50])
            filename = f'{timestamp}_{safe_topic}.md'

            content_dir = Path(settings.DATA_DIR) / 'content' / 'blogs'
            content_dir.mkdir(parents=True, exist_ok=True)

            filepath = content_dir / filename

            # Write markdown with frontmatter
            frontmatter = f'''---
title: "{output.title}"
description: "{output.meta_description}"
tags: {json.dumps(output.tags)}
reading_time: "{output.estimated_reading_time}"
created_at: "{datetime.now().isoformat()}"
---

'''
            filepath.write_text(frontmatter + output.content)

            logger.info(f'[BLOG_NODE] Saved: {filepath}')
            return str(filepath)

        except Exception as e:
            logger.error(f'[BLOG_NODE] Save failed: {e}')
            return ''
