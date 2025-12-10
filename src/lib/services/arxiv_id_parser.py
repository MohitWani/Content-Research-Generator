"""
ArXiv ID Parser and Validator Service
Parses, validates, and normalizes ArXiv paper identifiers
Maps to: spec.md → Story 1, FR1 | plan.md → T001
"""
import re
from dataclasses import dataclass
from typing import Optional

from src.lib.models.exceptions import InvalidArXivIdError


@dataclass
class ArXivIdComponents:
    """Parsed components of an ArXiv ID"""
    base_id: str
    version: Optional[int] = None
    normalized: str = ""
    
    def __post_init__(self):
        if not self.normalized:
            if self.version:
                self.normalized = f"{self.base_id}v{self.version}"
            else:
                self.normalized = self.base_id
    
    def __str__(self) -> str:
        return self.normalized


# Regex patterns for ArXiv ID formats
# New format (post April 2007): YYMM.NNNNN or YYMM.NNNN
NEW_FORMAT_PATTERN = r"(\d{4}\.\d{4,5})"

# Old format (pre April 2007): category/YYMMNNN
OLD_FORMAT_PATTERN = r"([a-z\-]+/\d{7})"

# Version suffix pattern
VERSION_PATTERN = r"v(\d+)"

# URL patterns
ABS_URL_PATTERN = r"arxiv\.org/abs/(.+?)(?:/|$|\?)"
PDF_URL_PATTERN = r"arxiv\.org/pdf/(.+?)(?:\.pdf)?(?:/|$|\?)"

# Prefix pattern (arxiv:, arXiv:)
PREFIX_PATTERN = r"^(?:arxiv:|arXiv:)"

# Combined ID pattern (either new or old format, with optional version)
ARXIV_ID_PATTERN = re.compile(
    rf"^(?:{NEW_FORMAT_PATTERN}|{OLD_FORMAT_PATTERN})(?:v(\d+))?$",
    re.IGNORECASE
)


def parse_arxiv_id(arxiv_input: Optional[str]) -> ArXivIdComponents:
    """
    Parse an ArXiv ID from various input formats.
    
    Supported formats:
    - Simple ID: "2508.07407"
    - With prefix: "arxiv:2508.07407", "arXiv:2508.07407"
    - With version: "2508.07407v2"
    - Full abstract URL: "https://arxiv.org/abs/2508.07407"
    - Full PDF URL: "https://arxiv.org/pdf/2508.07407.pdf"
    - Old format: "hep-th/9901001"
    
    Args:
        arxiv_input: The ArXiv ID or URL to parse
        
    Returns:
        ArXivIdComponents with parsed base_id, version, and normalized form
        
    Raises:
        InvalidArXivIdError: If the input is not a valid ArXiv ID
    """
    if not arxiv_input or not isinstance(arxiv_input, str):
        raise InvalidArXivIdError(str(arxiv_input) if arxiv_input else "")
    
    # Clean and normalize input
    cleaned = arxiv_input.strip()
    
    if not cleaned:
        raise InvalidArXivIdError("")
    
    # Try to extract ID from URL first
    extracted_id = _extract_from_url(cleaned)
    if extracted_id:
        cleaned = extracted_id
    
    # Remove arxiv: or arXiv: prefix
    cleaned = re.sub(PREFIX_PATTERN, "", cleaned, flags=re.IGNORECASE)
    
    # Remove trailing slashes
    cleaned = cleaned.rstrip("/")
    
    # Try to parse the ID
    return _parse_id_string(cleaned, arxiv_input)


def _extract_from_url(url: str) -> Optional[str]:
    """Extract ArXiv ID from URL if present."""
    # Check for abstract URL
    match = re.search(ABS_URL_PATTERN, url, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Check for PDF URL
    match = re.search(PDF_URL_PATTERN, url, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None


def _parse_id_string(id_string: str, original_input: str) -> ArXivIdComponents:
    """Parse the ID string after URL/prefix extraction."""
    # Try new format with optional version
    new_match = re.match(
        rf"^{NEW_FORMAT_PATTERN}(?:v(\d+))?$",
        id_string,
        re.IGNORECASE
    )
    if new_match:
        base_id = new_match.group(1)
        version_str = new_match.group(2)
        version = int(version_str) if version_str else None
        return ArXivIdComponents(base_id=base_id, version=version)
    
    # Try old format with optional version
    old_match = re.match(
        rf"^{OLD_FORMAT_PATTERN}(?:v(\d+))?$",
        id_string,
        re.IGNORECASE
    )
    if old_match:
        base_id = old_match.group(1)
        version_str = old_match.group(2)
        version = int(version_str) if version_str else None
        return ArXivIdComponents(base_id=base_id, version=version)
    
    # No match found
    raise InvalidArXivIdError(original_input)


def validate_arxiv_id(arxiv_input: Optional[str]) -> bool:
    """
    Check if the input is a valid ArXiv ID format.
    
    Args:
        arxiv_input: The input to validate
        
    Returns:
        True if valid ArXiv ID format, False otherwise
    """
    if not arxiv_input or not isinstance(arxiv_input, str):
        return False
    
    try:
        parse_arxiv_id(arxiv_input)
        return True
    except InvalidArXivIdError:
        return False


def normalize_arxiv_id(arxiv_input: str) -> str:
    """
    Normalize an ArXiv ID to standard format.
    
    Args:
        arxiv_input: The ArXiv ID to normalize
        
    Returns:
        Normalized ArXiv ID (e.g., "2508.07407" or "2508.07407v2")
        
    Raises:
        InvalidArXivIdError: If the input is not a valid ArXiv ID
    """
    components = parse_arxiv_id(arxiv_input)
    return components.normalized


def extract_version(arxiv_input: str) -> Optional[int]:
    """
    Extract version number from ArXiv ID if present.
    
    Args:
        arxiv_input: The ArXiv ID (may include version)
        
    Returns:
        Version number as int, or None if no version specified
    """
    if not arxiv_input:
        return None
    
    try:
        components = parse_arxiv_id(arxiv_input)
        return components.version
    except InvalidArXivIdError:
        return None


def is_valid_arxiv_format(arxiv_input: Optional[str]) -> bool:
    """
    Check if input matches valid ArXiv ID format.
    
    Alias for validate_arxiv_id() for clearer intent in some contexts.
    
    Args:
        arxiv_input: The input to check
        
    Returns:
        True if valid format, False otherwise
    """
    return validate_arxiv_id(arxiv_input)


def get_base_id(arxiv_input: str) -> str:
    """
    Get the base ArXiv ID without version suffix.
    
    Args:
        arxiv_input: The ArXiv ID (may include version)
        
    Returns:
        Base ID without version (e.g., "2508.07407")
        
    Raises:
        InvalidArXivIdError: If the input is not a valid ArXiv ID
    """
    components = parse_arxiv_id(arxiv_input)
    return components.base_id


def format_arxiv_url(arxiv_id: str, url_type: str = "abs") -> str:
    """
    Format an ArXiv ID into a full URL.
    
    Args:
        arxiv_id: The ArXiv ID
        url_type: Type of URL - "abs" for abstract page, "pdf" for PDF
        
    Returns:
        Full ArXiv URL
        
    Raises:
        InvalidArXivIdError: If the input is not a valid ArXiv ID
    """
    components = parse_arxiv_id(arxiv_id)
    
    if url_type == "pdf":
        return f"https://arxiv.org/pdf/{components.normalized}.pdf"
    else:
        return f"https://arxiv.org/abs/{components.normalized}"
