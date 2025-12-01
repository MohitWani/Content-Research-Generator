"""
Branding Agent for maintaining consistent voice and style
Applies brand guidelines and voice profile to content
Maps to: spec.md → FR5 (Brand Voice Consistency)
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json

from src.lib.llm.model import BedrockLLM
from src.lib.models.exceptions import ContentGenerationError
from src.common.config import config
from src.common.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class VoiceProfile:
    """Brand voice profile configuration"""
    brand_name: str
    tone: str
    style: str
    target_audiences: Dict[str, str]
    voice_characteristics: Dict[str, Any]
    do_list: list
    dont_list: list
    
    @classmethod
    def from_file(cls, filepath: str | Path) -> "VoiceProfile":
        """Load voice profile from JSON file"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Voice profile not found: {filepath}")
        
        with open(path) as f:
            data = json.load(f)
        
        return cls(
            brand_name=data.get("brand_name", "AI Insights"),
            tone=data.get("tone", "professional"),
            style=data.get("style", "informative"),
            target_audiences=data.get("target_audience_description", {}),
            voice_characteristics=data.get("voice_characteristics", {}),
            do_list=data.get("do", []),
            dont_list=data.get("dont", []),
        )
    
    def to_guidelines(self, audience: str = "practitioner") -> str:
        """Convert profile to text guidelines"""
        audience_desc = self.target_audiences.get(
            audience, 
            self.target_audiences.get("practitioner", "")
        )
        
        guidelines = f"""Brand: {self.brand_name}
Tone: {self.tone}
Style: {self.style}
Audience: {audience} - {audience_desc}

Voice Characteristics:
"""
        for key, value in self.voice_characteristics.items():
            guidelines += f"- {key}: {value}\n"
        
        if self.do_list:
            guidelines += "\nDo:\n"
            for item in self.do_list:
                guidelines += f"- {item}\n"
        
        if self.dont_list:
            guidelines += "\nDon't:\n"
            for item in self.dont_list:
                guidelines += f"- {item}\n"
        
        return guidelines


@dataclass
class BrandingResult:
    """Result from branding agent"""
    original_content: str
    branded_content: str
    changes_made: list
    voice_score: float  # 0-1 alignment with voice profile
    suggestions: list


class BrandingAgent:
    """
    Agent for applying brand voice and style to content
    Ensures consistency across all generated content
    """
    
    def __init__(
        self,
        llm: Optional[BedrockLLM] = None,
        voice_profile_path: Optional[str] = None,
    ):
        """
        Initialize branding agent
        
        Args:
            llm: LLM instance
            voice_profile_path: Path to voice.json profile
        """
        self.llm = llm or BedrockLLM()
        
        # Load voice profile
        profile_path = voice_profile_path or config.VOICE_PROFILE_PATH
        try:
            self.voice_profile = VoiceProfile.from_file(profile_path)
            logger.info(f"Loaded voice profile: {self.voice_profile.brand_name}")
        except FileNotFoundError:
            logger.warning(f"Voice profile not found at {profile_path}, using defaults")
            self.voice_profile = self._default_profile()
    
    def _default_profile(self) -> VoiceProfile:
        """Create default voice profile"""
        return VoiceProfile(
            brand_name="AI Insights",
            tone="professional, informative, slightly enthusiastic",
            style="clear, concise, technically accurate",
            target_audiences={
                "beginner": "Simple explanations, many analogies",
                "practitioner": "Practical focus, code examples",
                "expert": "Deep technical details",
            },
            voice_characteristics={
                "formality": "medium",
                "technical_depth": "adaptable",
                "humor": "minimal",
            },
            do_list=["Use active voice", "Include examples", "Be specific"],
            dont_list=["Use jargon without explanation", "Be condescending"],
        )
    
    async def apply_branding(
        self,
        content: str,
        target_audience: str = "practitioner",
        content_type: str = "blog",
    ) -> BrandingResult:
        """
        Apply brand voice and style to content
        
        Args:
            content: Content to brand
            target_audience: Target audience
            content_type: Type of content (blog, post, etc.)
        
        Returns:
            BrandingResult with branded content
        """
        guidelines = self.voice_profile.to_guidelines(target_audience)
        
        try:
            prompt = f"""Review and refine this {content_type} to match our brand voice.

Brand Guidelines:
{guidelines}

Original Content:
{content}

Tasks:
1. Adjust tone to match brand voice
2. Ensure style consistency
3. Adapt for {target_audience} audience
4. Keep the core message intact

Respond with JSON:
{{
    "branded_content": "The refined content...",
    "changes_made": ["Changed X to Y", "Adjusted tone in..."],
    "voice_score": 0.85,
    "suggestions": ["Consider adding...", "Could improve..."]
}}"""
            
            response = await self.llm.ainvoke(
                prompt=prompt,
                system_prompt="You are a brand voice expert. Refine content to match brand guidelines.",
                parse_json=True,
            )
            
            return BrandingResult(
                original_content=content,
                branded_content=response.get("branded_content", content),
                changes_made=response.get("changes_made", []),
                voice_score=float(response.get("voice_score", 0.5)),
                suggestions=response.get("suggestions", []),
            )
            
        except Exception as e:
            logger.error(f"Branding error: {e}")
            # Return original content on error
            return BrandingResult(
                original_content=content,
                branded_content=content,
                changes_made=[],
                voice_score=0.5,
                suggestions=[f"Branding failed: {e}"],
            )
    
    async def check_voice_alignment(
        self,
        content: str,
        target_audience: str = "practitioner",
    ) -> Dict[str, Any]:
        """
        Check how well content aligns with brand voice
        
        Args:
            content: Content to check
            target_audience: Target audience
        
        Returns:
            Dictionary with alignment score and feedback
        """
        guidelines = self.voice_profile.to_guidelines(target_audience)
        
        try:
            prompt = f"""Analyze this content's alignment with our brand voice.

Brand Guidelines:
{guidelines}

Content to Analyze:
{content[:3000]}

Respond with JSON:
{{
    "alignment_score": 0.85,
    "tone_match": true,
    "style_match": true,
    "audience_appropriate": true,
    "issues": ["Issue 1", "Issue 2"],
    "strengths": ["Strength 1"],
    "recommendations": ["Recommendation 1"]
}}"""
            
            response = await self.llm.ainvoke(
                prompt=prompt,
                system_prompt="You analyze content for brand voice alignment.",
                parse_json=True,
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Voice check error: {e}")
            return {
                "alignment_score": 0.5,
                "error": str(e),
            }
    
    async def generate_style_suggestions(
        self,
        content: str,
    ) -> list:
        """
        Generate style improvement suggestions
        
        Args:
            content: Content to analyze
        
        Returns:
            List of suggestions
        """
        try:
            prompt = f"""Provide style improvement suggestions for this content.

Content:
{content[:2000]}

Focus on:
- Clarity and readability
- Engagement and flow
- Technical accuracy
- Audience appropriateness

Provide 3-5 specific, actionable suggestions."""
            
            response = await self.llm.ainvoke(
                prompt=prompt,
                system_prompt="You are a content style expert.",
            )
            
            # Parse suggestions from response
            suggestions = [
                line.strip().lstrip("- ").lstrip("• ")
                for line in response.split("\n")
                if line.strip() and len(line.strip()) > 10
            ]
            
            return suggestions[:5]
            
        except Exception as e:
            logger.error(f"Style suggestions error: {e}")
            return []
    
    def get_guidelines_for_audience(self, audience: str) -> str:
        """Get text guidelines for specific audience"""
        return self.voice_profile.to_guidelines(audience)


def get_branding_agent(
    llm: Optional[BedrockLLM] = None,
    voice_profile_path: Optional[str] = None,
) -> BrandingAgent:
    """Factory function to create BrandingAgent"""
    return BrandingAgent(llm=llm, voice_profile_path=voice_profile_path)

