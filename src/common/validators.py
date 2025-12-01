"""
Content validation and formatting utilities
Ensures content quality and format compliance
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.common.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ValidationResult:
    """Result of content validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    
    def __bool__(self) -> bool:
        return self.is_valid


class ContentValidator:
    """
    Validates generated content for quality and format
    """
    
    # Placeholder patterns to detect
    PLACEHOLDER_PATTERNS = [
        r'\[PLACEHOLDER\]',
        r'\[TODO\]',
        r'\[INSERT\s+[^\]]+\]',
        r'\[\[.*?\]\]',
        r'\{.*?TBD.*?\}',
        r'<.*?PLACEHOLDER.*?>',
        r'XXX',
        r'FIXME',
    ]
    
    # Minimum content requirements
    MIN_BLOG_LENGTH = 500
    MIN_SUMMARY_LENGTH = 100
    MIN_LINKEDIN_LENGTH = 100
    MAX_LINKEDIN_LENGTH = 3000
    MAX_TWEET_LENGTH = 280
    
    def validate_blog(self, content: str, title: Optional[str] = None) -> ValidationResult:
        """
        Validate blog post content
        
        Args:
            content: Blog content
            title: Optional title
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Check length
        if len(content) < self.MIN_BLOG_LENGTH:
            errors.append(f"Content too short: {len(content)} chars (min: {self.MIN_BLOG_LENGTH})")
        
        # Check for placeholders
        placeholders = self._find_placeholders(content)
        if placeholders:
            errors.append(f"Contains placeholders: {', '.join(placeholders[:3])}")
        
        # Check structure
        if not re.search(r'^#\s+\w+', content, re.MULTILINE):
            warnings.append("No main heading found (# Title)")
        
        if not re.search(r'##\s+\w+', content):
            warnings.append("No section headings found (## Section)")
        
        # Check for code blocks if technical
        if "code" in content.lower() or "example" in content.lower():
            if "```" not in content:
                suggestions.append("Consider adding code blocks for examples")
        
        # Check title
        if title:
            if len(title) > 100:
                warnings.append("Title is quite long (>100 chars)")
            if title.isupper():
                warnings.append("Title is all uppercase")
        
        # Check paragraph structure
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) < 3:
            warnings.append("Very few paragraphs - consider adding more structure")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )
    
    def validate_linkedin_post(self, content: str) -> ValidationResult:
        """
        Validate LinkedIn post content
        
        Args:
            content: Post content
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Check length
        if len(content) < self.MIN_LINKEDIN_LENGTH:
            errors.append(f"Post too short: {len(content)} chars")
        
        if len(content) > self.MAX_LINKEDIN_LENGTH:
            errors.append(f"Post too long: {len(content)} chars (max: {self.MAX_LINKEDIN_LENGTH})")
        
        # Check for placeholders
        placeholders = self._find_placeholders(content)
        if placeholders:
            errors.append(f"Contains placeholders: {', '.join(placeholders[:3])}")
        
        # Check for hook (first line should be attention-grabbing)
        first_line = content.split('\n')[0].strip()
        if len(first_line) < 20:
            suggestions.append("Consider a stronger opening hook")
        
        # Check for hashtags
        hashtags = re.findall(r'#\w+', content)
        if not hashtags:
            suggestions.append("Consider adding relevant hashtags")
        elif len(hashtags) > 10:
            warnings.append("Too many hashtags may reduce engagement")
        
        # Check for CTA
        cta_patterns = ['comment', 'share', 'follow', 'let me know', 'what do you think', 'agree?']
        has_cta = any(pattern in content.lower() for pattern in cta_patterns)
        if not has_cta:
            suggestions.append("Consider adding a call-to-action")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )
    
    def validate_research_summary(self, summary: str) -> ValidationResult:
        """
        Validate research summary
        
        Args:
            summary: Research summary text
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Check length
        if len(summary) < self.MIN_SUMMARY_LENGTH:
            errors.append(f"Summary too short: {len(summary)} chars")
        
        # Check for placeholders
        placeholders = self._find_placeholders(summary)
        if placeholders:
            errors.append(f"Contains placeholders: {', '.join(placeholders[:3])}")
        
        # Check for complete sentences
        if not summary.endswith(('.', '!', '?')):
            warnings.append("Summary doesn't end with proper punctuation")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )
    
    def _find_placeholders(self, content: str) -> List[str]:
        """Find placeholder patterns in content"""
        found = []
        for pattern in self.PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found.extend(matches)
        return list(set(found))


class ContentFormatter:
    """
    Formats and cleans generated content
    """
    
    def format_blog_for_medium(self, content: str) -> str:
        """
        Format blog content for Medium publication
        
        Args:
            content: Raw blog content
        
        Returns:
            Formatted content
        """
        # Ensure proper spacing
        content = self._normalize_whitespace(content)
        
        # Convert code blocks to proper format
        content = self._format_code_blocks(content)
        
        # Ensure proper heading hierarchy
        content = self._fix_heading_hierarchy(content)
        
        # Add proper line breaks
        content = self._add_paragraph_breaks(content)
        
        return content
    
    def format_linkedin_post(self, content: str) -> str:
        """
        Format content for LinkedIn
        
        Args:
            content: Raw post content
        
        Returns:
            Formatted content
        """
        # Normalize whitespace
        content = self._normalize_whitespace(content)
        
        # Add line breaks for readability
        content = self._add_linkedin_breaks(content)
        
        # Ensure hashtags are at the end
        content = self._move_hashtags_to_end(content)
        
        return content
    
    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in content"""
        # Replace multiple newlines with double newline
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove trailing whitespace
        lines = [line.rstrip() for line in content.split('\n')]
        return '\n'.join(lines)
    
    def _format_code_blocks(self, content: str) -> str:
        """Ensure code blocks are properly formatted"""
        # Add language hints if missing
        content = re.sub(r'```\n', '```python\n', content)
        return content
    
    def _fix_heading_hierarchy(self, content: str) -> str:
        """Ensure proper heading hierarchy"""
        lines = content.split('\n')
        result = []
        
        for line in lines:
            # Ensure first heading is H1
            if line.startswith('## ') and not any(l.startswith('# ') for l in result):
                line = line[1:]  # Convert ## to #
            result.append(line)
        
        return '\n'.join(result)
    
    def _add_paragraph_breaks(self, content: str) -> str:
        """Add proper paragraph breaks"""
        # Split into paragraphs
        paragraphs = content.split('\n\n')
        
        # Ensure each paragraph has proper spacing
        return '\n\n'.join(p.strip() for p in paragraphs if p.strip())
    
    def _add_linkedin_breaks(self, content: str) -> str:
        """Add line breaks for LinkedIn readability"""
        # Add breaks after sentences in long paragraphs
        paragraphs = content.split('\n\n')
        result = []
        
        for p in paragraphs:
            if len(p) > 200:
                # Add break after first sentence
                sentences = re.split(r'(?<=[.!?])\s+', p)
                if len(sentences) > 2:
                    p = sentences[0] + '\n\n' + ' '.join(sentences[1:])
            result.append(p)
        
        return '\n\n'.join(result)
    
    def _move_hashtags_to_end(self, content: str) -> str:
        """Move hashtags to end of content"""
        # Find all hashtags
        hashtags = re.findall(r'#\w+', content)
        
        if not hashtags:
            return content
        
        # Remove hashtags from content
        content_without_hashtags = re.sub(r'#\w+\s*', '', content).strip()
        
        # Add hashtags at the end
        return f"{content_without_hashtags}\n\n{' '.join(set(hashtags))}"


def validate_and_format_blog(content: str, title: Optional[str] = None) -> Tuple[str, ValidationResult]:
    """
    Validate and format blog content
    
    Args:
        content: Blog content
        title: Optional title
    
    Returns:
        Tuple of (formatted_content, validation_result)
    """
    validator = ContentValidator()
    formatter = ContentFormatter()
    
    # Format first
    formatted = formatter.format_blog_for_medium(content)
    
    # Then validate
    result = validator.validate_blog(formatted, title)
    
    return formatted, result


def validate_and_format_linkedin(content: str) -> Tuple[str, ValidationResult]:
    """
    Validate and format LinkedIn post
    
    Args:
        content: Post content
    
    Returns:
        Tuple of (formatted_content, validation_result)
    """
    validator = ContentValidator()
    formatter = ContentFormatter()
    
    formatted = formatter.format_linkedin_post(content)
    result = validator.validate_linkedin_post(formatted)
    
    return formatted, result

