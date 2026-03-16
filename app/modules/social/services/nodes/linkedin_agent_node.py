"""
LinkedIn Agent Node

Contains the core agent logic for generating LinkedIn posts from content.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.config.environment_config import settings
from app.core.llm.bedrock_llm import BedrockLLM
from app.core.logging.logger import logger
from app.modules.social.services.prompts import social_prompts


class LinkedInOutput(BaseModel):
    """Structured output from LinkedIn agent node"""

    hook: str = Field(default='', description='Attention-grabbing first line')
    content: str = Field(default='', description='Full post content')
    hashtags: List[str] = Field(default_factory=list, description='Relevant hashtags')
    call_to_action: str = Field(default='', description='Call-to-action text')
    character_count: int = Field(default=0, description='Post character count')
    file_path: Optional[str] = Field(None, description='Saved file path')


class LinkedInAgentNode:
    """
    LinkedIn Agent Node - Core agent execution logic.
    
    Handles:
    - LLM initialization
    - Prompt construction
    - LinkedIn post generation execution
    - Response parsing
    - File saving
    """

    def __init__(self, llm: Optional[BedrockLLM] = None):
        """
        Initialize the LinkedIn agent node.
        
        Args:
            llm: Language model instance (defaults to BedrockLLM)
        """
        logger.info("[LINKEDIN_NODE] Initializing LinkedInAgentNode...")
        self.llm = llm or BedrockLLM()
        logger.info("[LINKEDIN_NODE] Initialized successfully")

    async def execute(
        self,
        topic: str,
        content: str,
        target_audience: str = 'practitioner',
        user_instructions: str = '',
    ) -> LinkedInOutput:
        """
        Execute LinkedIn post generation from content.
        
        Args:
            topic: Post topic
            content: Source content to transform
            target_audience: Target audience (beginner, practitioner, expert)
            user_instructions: Custom instructions from user on how post should look
            
        Returns:
            LinkedInOutput with generated post
        """
        logger.info(
            f"[LINKEDIN_NODE] Starting execution: topic='{topic[:50]}...', "
            f"audience={target_audience}, has_instructions={bool(user_instructions)}"
        )

        try:
            # Build prompts
            system_prompt = social_prompts.linkedin.system_prompt()
            user_prompt = social_prompts.linkedin.user_prompt(
                topic=topic,
                content=content[:4000],  # Limit content length
                target_audience=target_audience,
                user_instructions=user_instructions,
            )

            logger.debug("[LINKEDIN_NODE] Invoking LLM...")

            # Generate post
            response = await self.llm.ainvoke(
                prompt=user_prompt,
                system_prompt=system_prompt,
                parse_json=True,
            )

            logger.info("[LINKEDIN_NODE] LLM response received")

            # Parse response
            output = self._parse_response(response, topic)

            # Save to file
            output.file_path = await self._save_post(topic, output)

            logger.info(
                f"[LINKEDIN_NODE] Execution complete: "
                f"character_count={output.character_count}, hashtags={len(output.hashtags)}"
            )
            return output

        except Exception as e:
            logger.error(f"[LINKEDIN_NODE] Execution failed: {e}", exc_info=True)
            return LinkedInOutput(
                hook=f'Thoughts on {topic}',
                content=f'Failed to generate: {str(e)}',
            )

    def _parse_response(self, response: Dict[str, Any], topic: str) -> LinkedInOutput:
        """Parse LLM response into LinkedInOutput"""
        if not isinstance(response, dict):
            logger.warning('[LINKEDIN_NODE] Response not a dict')
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

    async def _save_post(self, topic: str, output: LinkedInOutput) -> str:
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

            logger.info(f'[LINKEDIN_NODE] Saved: {filepath}')
            return str(filepath)

        except Exception as e:
            logger.error(f'[LINKEDIN_NODE] Save failed: {e}')
            return ''
