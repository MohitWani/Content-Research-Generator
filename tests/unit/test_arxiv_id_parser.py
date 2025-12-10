"""
Unit tests for ArXiv ID Parser Service
Tests ArXiv paper ID parsing, validation, and normalization
Maps to: spec.md → Story 1, FR1 | plan.md → T001, T002
"""
import pytest
from src.lib.services.arxiv_id_parser import (
    parse_arxiv_id,
    validate_arxiv_id,
    normalize_arxiv_id,
    extract_version,
    is_valid_arxiv_format,
    ArXivIdComponents,
)
from src.lib.models.exceptions import InvalidArXivIdError


class TestParseArxivId:
    """Test ArXiv ID parsing functionality"""
    
    def test_parse_simple_id(self):
        """Should parse simple ArXiv ID format: 2508.07407"""
        # Arrange
        arxiv_id = "2508.07407"
        
        # Act
        result = parse_arxiv_id(arxiv_id)
        
        # Assert
        assert result.base_id == "2508.07407"
        assert result.version is None
        assert result.normalized == "2508.07407"
    
    def test_parse_with_arxiv_prefix_lowercase(self):
        """Should parse ID with lowercase prefix: arxiv:2508.07407"""
        # Arrange
        arxiv_id = "arxiv:2508.07407"
        
        # Act
        result = parse_arxiv_id(arxiv_id)
        
        # Assert
        assert result.base_id == "2508.07407"
        assert result.normalized == "2508.07407"
    
    def test_parse_with_arxiv_prefix_mixed_case(self):
        """Should parse ID with mixed case prefix: ArXiv:2508.07407"""
        # Arrange
        arxiv_id = "ArXiv:2508.07407"
        
        # Act
        result = parse_arxiv_id(arxiv_id)
        
        # Assert
        assert result.base_id == "2508.07407"
    
    def test_parse_with_version_suffix(self):
        """Should parse ID with version: 2508.07407v2"""
        # Arrange
        arxiv_id = "2508.07407v2"
        
        # Act
        result = parse_arxiv_id(arxiv_id)
        
        # Assert
        assert result.base_id == "2508.07407"
        assert result.version == 2
        assert result.normalized == "2508.07407v2"
    
    def test_parse_with_prefix_and_version(self):
        """Should parse ID with both prefix and version: arxiv:2508.07407v3"""
        # Arrange
        arxiv_id = "arxiv:2508.07407v3"
        
        # Act
        result = parse_arxiv_id(arxiv_id)
        
        # Assert
        assert result.base_id == "2508.07407"
        assert result.version == 3
    
    def test_parse_full_abs_url(self):
        """Should parse full ArXiv abstract URL"""
        # Arrange
        url = "https://arxiv.org/abs/2508.07407"
        
        # Act
        result = parse_arxiv_id(url)
        
        # Assert
        assert result.base_id == "2508.07407"
        assert result.version is None
    
    def test_parse_abs_url_with_version(self):
        """Should parse ArXiv abstract URL with version"""
        # Arrange
        url = "https://arxiv.org/abs/2508.07407v2"
        
        # Act
        result = parse_arxiv_id(url)
        
        # Assert
        assert result.base_id == "2508.07407"
        assert result.version == 2
    
    def test_parse_pdf_url(self):
        """Should parse ArXiv PDF URL"""
        # Arrange
        url = "https://arxiv.org/pdf/2508.07407.pdf"
        
        # Act
        result = parse_arxiv_id(url)
        
        # Assert
        assert result.base_id == "2508.07407"
    
    def test_parse_pdf_url_with_version(self):
        """Should parse ArXiv PDF URL with version"""
        # Arrange
        url = "https://arxiv.org/pdf/2508.07407v1.pdf"
        
        # Act
        result = parse_arxiv_id(url)
        
        # Assert
        assert result.base_id == "2508.07407"
        assert result.version == 1
    
    def test_parse_old_format_id(self):
        """Should parse old ArXiv ID format: hep-th/9901001"""
        # Arrange
        arxiv_id = "hep-th/9901001"
        
        # Act
        result = parse_arxiv_id(arxiv_id)
        
        # Assert
        assert result.base_id == "hep-th/9901001"
    
    def test_parse_five_digit_id(self):
        """Should parse 5-digit ArXiv ID: 2508.12345"""
        # Arrange
        arxiv_id = "2508.12345"
        
        # Act
        result = parse_arxiv_id(arxiv_id)
        
        # Assert
        assert result.base_id == "2508.12345"


class TestValidateArxivId:
    """Test ArXiv ID validation"""
    
    def test_valid_simple_id(self):
        """Should validate correct simple ID"""
        # Act & Assert
        assert validate_arxiv_id("2508.07407") is True
    
    def test_valid_id_with_version(self):
        """Should validate ID with version"""
        # Act & Assert
        assert validate_arxiv_id("2508.07407v2") is True
    
    def test_valid_id_with_prefix(self):
        """Should validate ID with prefix"""
        # Act & Assert
        assert validate_arxiv_id("arxiv:2508.07407") is True
    
    def test_invalid_format_letters(self):
        """Should reject invalid format with letters"""
        # Act & Assert
        assert validate_arxiv_id("abc123") is False
    
    def test_invalid_format_short_number(self):
        """Should reject too short number"""
        # Act & Assert
        assert validate_arxiv_id("123") is False
    
    def test_invalid_format_wrong_pattern(self):
        """Should reject wrong pattern"""
        # Act & Assert
        assert validate_arxiv_id("25.07407") is False
    
    def test_invalid_empty_string(self):
        """Should reject empty string"""
        # Act & Assert
        assert validate_arxiv_id("") is False
    
    def test_invalid_none(self):
        """Should reject None input"""
        # Act & Assert
        assert validate_arxiv_id(None) is False
    
    def test_invalid_whitespace_only(self):
        """Should reject whitespace only"""
        # Act & Assert
        assert validate_arxiv_id("   ") is False
    
    def test_invalid_special_characters(self):
        """Should reject special characters"""
        # Act & Assert
        assert validate_arxiv_id("2508@07407") is False


class TestNormalizeArxivId:
    """Test ArXiv ID normalization"""
    
    def test_normalize_strips_whitespace(self):
        """Should strip leading/trailing whitespace"""
        # Act
        result = normalize_arxiv_id("  2508.07407  ")
        
        # Assert
        assert result == "2508.07407"
    
    def test_normalize_removes_prefix(self):
        """Should remove arxiv: prefix for base ID"""
        # Act
        result = normalize_arxiv_id("arxiv:2508.07407")
        
        # Assert
        assert result == "2508.07407"
    
    def test_normalize_preserves_version(self):
        """Should preserve version in normalized output"""
        # Act
        result = normalize_arxiv_id("arxiv:2508.07407v2")
        
        # Assert
        assert result == "2508.07407v2"
    
    def test_normalize_extracts_from_url(self):
        """Should extract ID from full URL"""
        # Act
        result = normalize_arxiv_id("https://arxiv.org/abs/2508.07407")
        
        # Assert
        assert result == "2508.07407"
    
    def test_normalize_invalid_raises_error(self):
        """Should raise error for invalid ID"""
        # Act & Assert
        with pytest.raises(InvalidArXivIdError) as exc_info:
            normalize_arxiv_id("invalid_id")
        
        assert "Invalid ArXiv ID format" in str(exc_info.value)
        assert "invalid_id" in str(exc_info.value)


class TestExtractVersion:
    """Test version extraction from ArXiv ID"""
    
    def test_extract_version_v1(self):
        """Should extract version 1"""
        # Act
        version = extract_version("2508.07407v1")
        
        # Assert
        assert version == 1
    
    def test_extract_version_v10(self):
        """Should extract double-digit version"""
        # Act
        version = extract_version("2508.07407v10")
        
        # Assert
        assert version == 10
    
    def test_extract_version_none(self):
        """Should return None when no version"""
        # Act
        version = extract_version("2508.07407")
        
        # Assert
        assert version is None
    
    def test_extract_version_from_url(self):
        """Should extract version from URL"""
        # Act
        version = extract_version("https://arxiv.org/abs/2508.07407v3")
        
        # Assert
        assert version == 3


class TestIsValidArxivFormat:
    """Test format checking function"""
    
    @pytest.mark.parametrize("arxiv_id,expected", [
        ("2508.07407", True),
        ("2508.07407v2", True),
        ("arxiv:2508.07407", True),
        ("ArXiv:2508.07407v1", True),
        ("https://arxiv.org/abs/2508.07407", True),
        ("https://arxiv.org/pdf/2508.07407.pdf", True),
        ("1706.03762", True),  # Attention Is All You Need
        ("2005.14165", True),  # GPT-3
        ("hep-th/9901001", True),  # Old format
        ("abc123", False),
        ("", False),
        ("123", False),
        ("2508", False),
        (None, False),
    ])
    def test_various_formats(self, arxiv_id, expected):
        """Should correctly identify valid and invalid formats"""
        # Act & Assert
        assert is_valid_arxiv_format(arxiv_id) == expected


class TestArxivIdComponents:
    """Test ArXivIdComponents dataclass"""
    
    def test_components_str_representation(self):
        """Should have meaningful string representation"""
        # Arrange
        components = ArXivIdComponents(
            base_id="2508.07407",
            version=2,
            normalized="2508.07407v2"
        )
        
        # Act
        result = str(components)
        
        # Assert
        assert "2508.07407" in result
    
    def test_components_without_version(self):
        """Should handle missing version"""
        # Arrange
        components = ArXivIdComponents(
            base_id="2508.07407",
            version=None,
            normalized="2508.07407"
        )
        
        # Assert
        assert components.version is None
        assert components.normalized == "2508.07407"


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_parse_raises_for_invalid_id(self):
        """Should raise InvalidArXivIdError for invalid ID"""
        # Act & Assert
        with pytest.raises(InvalidArXivIdError) as exc_info:
            parse_arxiv_id("not_valid")
        
        assert "not_valid" in str(exc_info.value)
        assert "Expected format" in str(exc_info.value)
    
    def test_parse_raises_for_empty_string(self):
        """Should raise InvalidArXivIdError for empty string"""
        # Act & Assert
        with pytest.raises(InvalidArXivIdError):
            parse_arxiv_id("")
    
    def test_parse_raises_for_none(self):
        """Should raise InvalidArXivIdError for None"""
        # Act & Assert
        with pytest.raises(InvalidArXivIdError):
            parse_arxiv_id(None)
    
    def test_parse_handles_http_url(self):
        """Should handle HTTP (non-HTTPS) URLs"""
        # Arrange
        url = "http://arxiv.org/abs/2508.07407"
        
        # Act
        result = parse_arxiv_id(url)
        
        # Assert
        assert result.base_id == "2508.07407"
    
    def test_parse_handles_trailing_slash(self):
        """Should handle URL with trailing slash"""
        # Arrange
        url = "https://arxiv.org/abs/2508.07407/"
        
        # Act
        result = parse_arxiv_id(url)
        
        # Assert
        assert result.base_id == "2508.07407"

