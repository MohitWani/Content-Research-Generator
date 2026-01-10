"""
Shortform Agent
Generates LinkedIn posts and Twitter/X threads from content
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from app.core.config.environment_config import settings
from app.core.llm.bedrock_llm import BedrockLLM
from app.core.llm.prompts import prompts
from app.core.logging.logger import logger
from app.modules.content.services.blog_writer_agent import BlogOutput


class LinkedInOutput(BaseModel):
    """Structured output for LinkedIn post"""

    hook: str = Field(default='', description='Attention-grabbing first line')
    content: str = Field(default='', description='Full post content')
    hashtags: List[str] = Field(default_factory=list, description='Relevant hashtags')
    call_to_action: str = Field(default='', description='Call-to-action text')
    character_count: int = Field(default=0, description='Post character count')
    file_path: Optional[str] = Field(None, description='Saved file path')


class ThreadPost(BaseModel):
    """Single post in a Twitter/X thread"""

    position: int = Field(..., description='Post position (1-indexed)')
    content: str = Field(..., description='Post content (max 280 chars)')
    character_count: int = Field(default=0, description='Character count')


class ThreadOutput(BaseModel):
    """Structured output for Twitter/X thread"""

    posts: List[ThreadPost] = Field(default_factory=list, description='Thread posts')
    topic: str = Field(default='', description='Thread topic')
    total_posts: int = Field(default=0, description='Total number of posts')
    file_path: Optional[str] = Field(None, description='Saved file path')


class ShortformAgent:
    """
    Agent for generating short-form social media content
    Supports LinkedIn posts and Twitter/X threads
    """

    def __init__(self, llm: Optional[BedrockLLM] = None):
        """
        Initialize shortform agent

        Args:
            llm: LLM instance (creates default if not provided)
        """
        self.llm = llm or BedrockLLM()
        logger.info('ShortformAgent initialized')

    async def generate_linkedin_post(
        self,
        topic: str,
        content: str,
        target_audience: str = 'practitioner',
    ) -> LinkedInOutput:
        """
        Generate a LinkedIn post from content

        Args:
            topic: Post topic
            content: Source content to transform
            target_audience: Target audience

        Returns:
            LinkedInOutput with generated post
        """
        logger.info(f"[LINKEDIN] Generating for: '{topic[:50]}...'")

        try:
            # Build prompts
            system_prompt = prompts.linkedin.system_prompt()
            user_prompt = prompts.linkedin.user_prompt(
                topic=topic,
                content=content[:4000],  # Limit content length
                target_audience=target_audience,
            )

            # Generate post
            response = await self.llm.ainvoke(
                prompt=user_prompt,
                system_prompt=system_prompt,
                parse_json=True,
            )

            logger.info('[LINKEDIN] LLM response received')

            # Parse response
            output = self._parse_linkedin_response(response, topic)

            # Save to file
            output.file_path = await self._save_linkedin(topic, output)

            logger.info(f'[LINKEDIN] Generated: {output.character_count} chars')
            return output

        except Exception as e:
            logger.error(f'[LINKEDIN] Generation failed: {e}', exc_info=True)
            return LinkedInOutput(
                hook=f'Thoughts on {topic}',
                content=f'Failed to generate: {str(e)}',
            )

    async def generate_twitter_thread(
        self,
        topic: str,
        content: str,
        max_posts: int = 5,
    ) -> ThreadOutput:
        """
        Generate a Twitter/X thread from content

        Args:
            topic: Thread topic
            content: Source content to transform
            max_posts: Maximum number of posts (5-15)

        Returns:
            ThreadOutput with generated thread
        """
        max_posts = max(5, min(15, max_posts))
        logger.info(f"[THREAD] Generating {max_posts} posts for: '{topic[:50]}...'")

        try:
            # Build prompts
            system_prompt = prompts.twitter.system_prompt()
            user_prompt = prompts.twitter.user_prompt(
                topic=topic,
                content=content[:4000],
                max_posts=max_posts,
            )

            # Generate thread
            response = await self.llm.ainvoke(
                prompt=user_prompt,
                system_prompt=system_prompt,
                parse_json=True,
            )

            logger.info('[THREAD] LLM response received')

            # Parse response
            output = self._parse_thread_response(response, topic)

            # Save to file
            output.file_path = await self._save_thread(topic, output)

            logger.info(f'[THREAD] Generated: {output.total_posts} posts')
            return output

        except Exception as e:
            logger.error(f'[THREAD] Generation failed: {e}', exc_info=True)
            return ThreadOutput(
                posts=[ThreadPost(position=1, content=f'1/ {topic[:200]}')],
                topic=topic,
                total_posts=1,
            )

    def _parse_linkedin_response(
        self, response: Dict[str, Any], topic: str
    ) -> LinkedInOutput:
        """Parse LLM response into LinkedInOutput"""
        if not isinstance(response, dict):
            logger.warning('[LINKEDIN] Response not a dict')
            content = str(response) if response else ''
            return LinkedInOutput(
                hook=topic,
                content=content,
                character_count=len(content),
            )

        content = response.get('content', '')
        return LinkedInOutput(
            hook=response.get('hook', topic),
            content=content,
            hashtags=response.get('hashtags', [])[:5],
            call_to_action=response.get('call_to_action', ''),
            character_count=len(content),
        )

    def _parse_thread_response(
        self, response: Dict[str, Any], topic: str
    ) -> ThreadOutput:
        """Parse LLM response into ThreadOutput"""
        if not isinstance(response, dict):
            logger.warning('[THREAD] Response not a dict')
            return ThreadOutput(
                posts=[ThreadPost(position=1, content=f'1/ {topic[:250]}', character_count=len(topic) + 3)],
                topic=topic,
                total_posts=1,
            )

        raw_posts = response.get('posts', [])
        posts = []
        for p in raw_posts:
            if isinstance(p, dict):
                content = p.get('content', '')
                posts.append(
                    ThreadPost(
                        position=p.get('position', len(posts) + 1),
                        content=content[:280],  # Enforce 280 char limit
                        character_count=len(content[:280]),
                    )
                )

        return ThreadOutput(
            posts=posts,
            topic=topic,
            total_posts=len(posts),
        )

    async def _save_linkedin(self, topic: str, output: LinkedInOutput) -> str:
        """Save LinkedIn post to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_topic = ''.join(c if c.isalnum() else '_' for c in topic[:40])
            filename = f'{timestamp}_linkedin_{safe_topic}.txt'

            social_dir = Path(settings.DATA_DIR) / 'content' / 'social' / 'linkedin'
            social_dir.mkdir(parents=True, exist_ok=True)

            filepath = social_dir / filename
            
            hashtag_str = ' '.join([f'#{h}' for h in output.hashtags])
            full_content = f'''{output.content}

{hashtag_str}
---
Character Count: {output.character_count}
Generated: {datetime.now().isoformat()}
'''
            filepath.write_text(full_content)

            logger.info(f'[LINKEDIN] Saved: {filepath}')
            return str(filepath)

        except Exception as e:
            logger.error(f'[LINKEDIN] Save failed: {e}')
            return ''

    async def _save_thread(self, topic: str, output: ThreadOutput) -> str:
        """Save Twitter thread to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_topic = ''.join(c if c.isalnum() else '_' for c in topic[:40])
            filename = f'{timestamp}_thread_{safe_topic}.txt'

            social_dir = Path(settings.DATA_DIR) / 'content' / 'social' / 'twitter'
            social_dir.mkdir(parents=True, exist_ok=True)

            filepath = social_dir / filename

            thread_content = f'# Thread: {topic}\n\n'
            for post in output.posts:
                thread_content += f'{post.content}\n[{post.character_count} chars]\n\n'

            thread_content += f'''---
Total Posts: {output.total_posts}
Generated: {datetime.now().isoformat()}
'''
            filepath.write_text(thread_content)

            logger.info(f'[THREAD] Saved: {filepath}')
            return str(filepath)

        except Exception as e:
            logger.error(f'[THREAD] Save failed: {e}')
            return ''

    async def generate_from_blog(
        self,
        blog: BlogOutput,
        platforms: List[str] = None,
    ) -> Dict[str, Union[LinkedInOutput, ThreadOutput]]:
        """
        Generate social content from a blog post

        Args:
            blog: Blog output to transform
            platforms: List of platforms ('linkedin', 'twitter')

        Returns:
            Dict with platform -> output mappings
        """
        platforms = platforms or ['linkedin', 'twitter']
        results = {}

        if 'linkedin' in platforms:
            results['linkedin'] = await self.generate_linkedin_post(
                topic=blog.title,
                content=blog.content[:4000],
            )

        if 'twitter' in platforms:
            results['twitter'] = await self.generate_twitter_thread(
                topic=blog.title,
                content=blog.content[:4000],
            )

        return results


def get_shortform_agent(llm: Optional[BedrockLLM] = None) -> ShortformAgent:
    """Factory function to create ShortformAgent"""
    return ShortformAgent(llm=llm)
