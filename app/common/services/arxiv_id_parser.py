"""
ArXiv ID Parser and Validator Service
"""
import re
from dataclasses import dataclass
from typing import Optional

from app.common.exceptions.research_exceptions import InvalidArXivIdError


@dataclass
class ArXivIdComponents:
    """Parsed components of an ArXiv ID"""

    base_id: str
    version: Optional[int] = None
    normalized: str = ''

    def __post_init__(self):
        if not self.normalized:
            if self.version:
                self.normalized = f'{self.base_id}v{self.version}'
            else:
                self.normalized = self.base_id

    def __str__(self) -> str:
        return self.normalized


# Regex patterns
NEW_FORMAT_PATTERN = r'(\d{4}\.\d{4,5})'
OLD_FORMAT_PATTERN = r'([a-z\-]+/\d{7})'
VERSION_PATTERN = r'v(\d+)'
ABS_URL_PATTERN = r'arxiv\.org/abs/(.+?)(?:/|$|\?)'
PDF_URL_PATTERN = r'arxiv\.org/pdf/(.+?)(?:\.pdf)?(?:/|$|\?)'
PREFIX_PATTERN = r'^(?:arxiv:|arXiv:)'


def parse_arxiv_id(arxiv_input: Optional[str]) -> ArXivIdComponents:
    """Parse an ArXiv ID from various input formats."""
    if not arxiv_input or not isinstance(arxiv_input, str):
        raise InvalidArXivIdError(str(arxiv_input) if arxiv_input else '')

    cleaned = arxiv_input.strip()

    if not cleaned:
        raise InvalidArXivIdError('')

    extracted_id = _extract_from_url(cleaned)
    if extracted_id:
        cleaned = extracted_id

    cleaned = re.sub(PREFIX_PATTERN, '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.rstrip('/')

    return _parse_id_string(cleaned, arxiv_input)


def _extract_from_url(url: str) -> Optional[str]:
    """Extract ArXiv ID from URL if present."""
    match = re.search(ABS_URL_PATTERN, url, re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(PDF_URL_PATTERN, url, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def _parse_id_string(id_string: str, original_input: str) -> ArXivIdComponents:
    """Parse the ID string after URL/prefix extraction."""
    new_match = re.match(
        rf'^{NEW_FORMAT_PATTERN}(?:v(\d+))?$', id_string, re.IGNORECASE
    )
    if new_match:
        base_id = new_match.group(1)
        version_str = new_match.group(2)
        version = int(version_str) if version_str else None
        return ArXivIdComponents(base_id=base_id, version=version)

    old_match = re.match(
        rf'^{OLD_FORMAT_PATTERN}(?:v(\d+))?$', id_string, re.IGNORECASE
    )
    if old_match:
        base_id = old_match.group(1)
        version_str = old_match.group(2)
        version = int(version_str) if version_str else None
        return ArXivIdComponents(base_id=base_id, version=version)

    raise InvalidArXivIdError(original_input)


def validate_arxiv_id(arxiv_input: Optional[str]) -> bool:
    """Check if the input is a valid ArXiv ID format."""
    if not arxiv_input or not isinstance(arxiv_input, str):
        return False

    try:
        parse_arxiv_id(arxiv_input)
        return True
    except InvalidArXivIdError:
        return False


def normalize_arxiv_id(arxiv_input: str) -> str:
    """Normalize an ArXiv ID to standard format."""
    components = parse_arxiv_id(arxiv_input)
    return components.normalized


def extract_version(arxiv_input: str) -> Optional[int]:
    """Extract version number from ArXiv ID if present."""
    if not arxiv_input:
        return None

    try:
        components = parse_arxiv_id(arxiv_input)
        return components.version
    except InvalidArXivIdError:
        return None


def get_base_id(arxiv_input: str) -> str:
    """Get the base ArXiv ID without version suffix."""
    components = parse_arxiv_id(arxiv_input)
    return components.base_id


def format_arxiv_url(arxiv_id: str, url_type: str = 'abs') -> str:
    """Format an ArXiv ID into a full URL."""
    components = parse_arxiv_id(arxiv_id)

    if url_type == 'pdf':
        return f'https://arxiv.org/pdf/{components.normalized}.pdf'
    else:
        return f'https://arxiv.org/abs/{components.normalized}'


