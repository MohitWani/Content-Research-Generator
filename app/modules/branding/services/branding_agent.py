"""
Branding Agent
Applies brand voice and style to content
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.config.environment_config import settings
from app.core.llm.bedrock_llm import BedrockLLM
from app.core.llm.prompts import prompts
from app.core.logging.logger import logger


class VoiceProfile(BaseModel):
    """Brand voice profile configuration"""

    brand_name: str = Field(default='AI Research Agent', description='Brand name')
    tone: str = Field(default='professional', description='Primary tone')
    style: str = Field(default='technical-accessible', description='Writing style')
    target_audiences: Dict[str, str] = Field(
        default_factory=lambda: {
            'beginner': 'Simple explanations with analogies',
            'practitioner': 'Balance of theory and practice',
            'expert': 'Deep technical details',
        },
        description='Audience-specific guidelines',
    )
    voice_characteristics: Dict[str, str] = Field(
        default_factory=lambda: {
            'clarity': 'high',
            'technical_depth': 'medium-high',
            'formality': 'professional but approachable',
        },
        description='Voice characteristics',
    )
    do_list: List[str] = Field(
        default_factory=lambda: [
            'Use examples and analogies',
            'Cite authoritative sources',
            'Be concise and direct',
            'Include code examples when relevant',
            'Use active voice',
        ],
        description='Things to do',
    )
    dont_list: List[str] = Field(
        default_factory=lambda: [
            'Use jargon without explanation',
            'Be overly verbose',
            'Make unsupported claims',
            'Use passive voice excessively',
        ],
        description='Things to avoid',
    )


class BrandingOutput(BaseModel):
    """Output from branding agent"""

    original_content: str = Field(default='', description='Original content')
    branded_content: str = Field(default='', description='Branded content')
    changes_made: List[str] = Field(default_factory=list, description='Changes made')
    voice_score: float = Field(default=0.0, ge=0.0, le=1.0, description='Voice alignment score')
    suggestions: List[str] = Field(default_factory=list, description='Improvement suggestions')
    file_path: Optional[str] = Field(None, description='Saved file path')


class BrandingAgent:
    """
    Agent for applying brand voice to content
    Uses voice profile to ensure consistent branding
    """

    def __init__(
        self,
        llm: Optional[BedrockLLM] = None,
        voice_profile: Optional[VoiceProfile] = None,
    ):
        """
        Initialize branding agent

        Args:
            llm: LLM instance (creates default if not provided)
            voice_profile: Voice profile (uses default if not provided)
        """
        self.llm = llm or BedrockLLM()
        self.voice_profile = voice_profile or self._load_voice_profile()
        logger.info('BrandingAgent initialized')

    def _load_voice_profile(self) -> VoiceProfile:
        """Load voice profile from file or use defaults"""
        try:
            voice_path = settings.VOICE_PROFILE_PATH
            if voice_path.exists():
                data = json.loads(voice_path.read_text())
                return VoiceProfile(**data)
        except Exception as e:
            logger.warning(f'[BRANDING] Failed to load voice profile: {e}')

        return VoiceProfile()

    def get_guidelines(self, target_audience: str = 'practitioner') -> str:
        """Generate brand guidelines string for prompts"""
        vp = self.voice_profile

        guidelines = f'''## Brand Voice: {vp.brand_name}

**Tone**: {vp.tone}
**Style**: {vp.style}

### Audience: {target_audience}
{vp.target_audiences.get(target_audience, vp.target_audiences.get('practitioner', ''))}

### Voice Characteristics
'''
        for key, value in vp.voice_characteristics.items():
            guidelines += f'- {key}: {value}\n'

        guidelines += '\n### Do:\n'
        for item in vp.do_list:
            guidelines += f'- {item}\n'

        guidelines += '\n### Don\'t:\n'
        for item in vp.dont_list:
            guidelines += f'- {item}\n'

        return guidelines

    async def apply_branding(
        self,
        content: str,
        target_audience: str = 'practitioner',
        content_type: str = 'blog',
    ) -> BrandingOutput:
        """
        Apply brand voice to content

        Args:
            content: Content to brand
            target_audience: Target audience
            content_type: Type of content (blog, linkedin, etc.)

        Returns:
            BrandingOutput with branded content
        """
        logger.info(f'[BRANDING] Applying to {content_type} ({len(content)} chars)')

        try:
            # Get brand guidelines
            guidelines = self.get_guidelines(target_audience)

            # Build prompts
            system_prompt = prompts.branding.system_prompt()
            user_prompt = prompts.branding.user_prompt(
                content=content[:8000],  # Limit content length
                guidelines=guidelines,
                target_audience=target_audience,
                content_type=content_type,
            )

            # Apply branding
            response = await self.llm.ainvoke(
                prompt=user_prompt,
                system_prompt=system_prompt,
                parse_json=True,
            )

            logger.info('[BRANDING] LLM response received')

            # Parse response
            output = self._parse_response(response, content)

            # Save branded content
            output.file_path = await self._save_branded(content_type, output)

            logger.info(f'[BRANDING] Complete: score={output.voice_score:.2f}')
            return output

        except Exception as e:
            logger.error(f'[BRANDING] Failed: {e}', exc_info=True)
            return BrandingOutput(
                original_content=content,
                branded_content=content,  # Return original on failure
                changes_made=[f'Error: {str(e)}'],
            )

    def _parse_response(self, response: Dict[str, Any], original: str) -> BrandingOutput:
        """Parse LLM response into BrandingOutput"""
        if not isinstance(response, dict):
            logger.warning('[BRANDING] Response not a dict')
            return BrandingOutput(
                original_content=original,
                branded_content=str(response) if response else original,
            )

        return BrandingOutput(
            original_content=original,
            branded_content=response.get('branded_content', original),
            changes_made=response.get('changes_made', []),
            voice_score=float(response.get('voice_score', 0.0)),
            suggestions=response.get('suggestions', []),
        )

    async def _save_branded(self, content_type: str, output: BrandingOutput) -> str:
        """Save branded content to file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{timestamp}_branded_{content_type}.md'

            brand_dir = Path(settings.DATA_DIR) / 'content' / 'branded'
            brand_dir.mkdir(parents=True, exist_ok=True)

            filepath = brand_dir / filename

            metadata = f'''---
content_type: {content_type}
voice_score: {output.voice_score}
changes_count: {len(output.changes_made)}
generated_at: {datetime.now().isoformat()}
---

## Changes Made
'''
            for change in output.changes_made:
                metadata += f'- {change}\n'

            metadata += '\n## Suggestions\n'
            for suggestion in output.suggestions:
                metadata += f'- {suggestion}\n'

            metadata += '\n---\n\n'

            filepath.write_text(metadata + output.branded_content)

            logger.info(f'[BRANDING] Saved: {filepath}')
            return str(filepath)

        except Exception as e:
            logger.error(f'[BRANDING] Save failed: {e}')
            return ''

    async def check_alignment(
        self,
        content: str,
        target_audience: str = 'practitioner',
    ) -> Dict[str, Any]:
        """
        Check content alignment with brand voice (without modifying)

        Args:
            content: Content to check
            target_audience: Target audience

        Returns:
            Dict with alignment analysis
        """
        logger.info(f'[BRANDING] Checking alignment ({len(content)} chars)')

        result = await self.apply_branding(content, target_audience)

        return {
            'alignment_score': result.voice_score,
            'is_aligned': result.voice_score >= 0.7,
            'issues': [s for s in result.suggestions if 'issue' in s.lower() or 'improve' in s.lower()],
            'strengths': [s for s in result.suggestions if 'good' in s.lower() or 'strong' in s.lower()],
            'suggestions': result.suggestions,
            'changes_needed': result.changes_made,
        }

    def save_voice_profile(self) -> bool:
        """Save current voice profile to file"""
        try:
            voice_path = settings.VOICE_PROFILE_PATH
            voice_path.parent.mkdir(parents=True, exist_ok=True)
            voice_path.write_text(self.voice_profile.model_dump_json(indent=2))
            logger.info(f'[BRANDING] Voice profile saved: {voice_path}')
            return True
        except Exception as e:
            logger.error(f'[BRANDING] Failed to save voice profile: {e}')
            return False


def get_branding_agent(
    llm: Optional[BedrockLLM] = None,
    voice_profile: Optional[VoiceProfile] = None,
) -> BrandingAgent:
    """Factory function to create BrandingAgent"""
    return BrandingAgent(llm=llm, voice_profile=voice_profile)
