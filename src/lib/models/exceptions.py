"""
Custom exceptions for the AI Research Agent System
Provides structured error handling across all components
"""
from typing import Optional, Dict, Any


class AIResearchAgentError(Exception):
    """Base exception for all AI Research Agent errors"""
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


# Query and Categorization Errors
class QueryCategorizationError(AIResearchAgentError):
    """Raised when query categorization fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="QUERY_CATEGORIZATION_ERROR",
            details=details,
        )


class InvalidQueryError(AIResearchAgentError):
    """Raised when query is invalid or malformed"""
    
    def __init__(self, message: str, query: Optional[str] = None):
        super().__init__(
            message=message,
            code="INVALID_QUERY",
            details={"query": query} if query else {},
        )


class NonAITopicError(AIResearchAgentError):
    """Raised when query is not related to AI"""
    
    def __init__(self, message: str, query: Optional[str] = None):
        super().__init__(
            message=message,
            code="NON_AI_TOPIC",
            details={"query": query} if query else {},
        )


# Research Errors
class ResearchDataInsufficientError(AIResearchAgentError):
    """Raised when research data is insufficient for processing"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RESEARCH_DATA_INSUFFICIENT",
            details=details,
        )


class ResearchTimeoutError(AIResearchAgentError):
    """Raised when research operation times out"""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None):
        super().__init__(
            message=message,
            code="RESEARCH_TIMEOUT",
            details={"timeout_seconds": timeout_seconds} if timeout_seconds else {},
        )


# Content Generation Errors
class ContentGenerationError(AIResearchAgentError):
    """Raised when content generation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="CONTENT_GENERATION_ERROR",
            details=details,
        )


class BlogGenerationError(ContentGenerationError):
    """Raised when blog generation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.code = "BLOG_GENERATION_ERROR"


class ShortformGenerationError(ContentGenerationError):
    """Raised when shortform content generation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.code = "SHORTFORM_GENERATION_ERROR"


# External API Errors
class ExternalAPIError(AIResearchAgentError):
    """Raised when external API call fails"""
    
    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        super().__init__(
            message=message,
            code="EXTERNAL_API_ERROR",
            details={
                "service": service,
                "status_code": status_code,
            },
        )
        self.service = service
        self.status_code = status_code


class RateLimitExceededError(ExternalAPIError):
    """Raised when rate limit is exceeded"""
    
    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(message=message, service=service)
        self.code = "RATE_LIMIT_EXCEEDED"
        self.details["retry_after"] = retry_after
        self.retry_after = retry_after


class ServiceUnavailableError(ExternalAPIError):
    """Raised when external service is unavailable"""
    
    def __init__(self, message: str, service: Optional[str] = None):
        super().__init__(message=message, service=service, status_code=503)
        self.code = "SERVICE_UNAVAILABLE"


# LLM Errors
class LLMError(AIResearchAgentError):
    """Base class for LLM-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="LLM_ERROR",
            details=details,
        )


class LLMResponseParseError(LLMError):
    """Raised when LLM response cannot be parsed"""
    
    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(
            message=message,
            details={"raw_response": raw_response[:500] if raw_response else None},
        )
        self.code = "LLM_RESPONSE_PARSE_ERROR"


class LLMQuotaExceededError(LLMError):
    """Raised when LLM quota is exceeded"""
    
    def __init__(self, message: str):
        super().__init__(message=message)
        self.code = "LLM_QUOTA_EXCEEDED"


# Pipeline Errors
class PipelineError(AIResearchAgentError):
    """Raised when pipeline execution fails"""
    
    def __init__(
        self,
        message: str,
        pipeline_type: Optional[str] = None,
        step: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            code="PIPELINE_ERROR",
            details={
                "pipeline_type": pipeline_type,
                "step": step,
            },
        )


class WorkflowStateError(AIResearchAgentError):
    """Raised when workflow state is invalid"""
    
    def __init__(self, message: str, workflow_id: Optional[int] = None):
        super().__init__(
            message=message,
            code="WORKFLOW_STATE_ERROR",
            details={"workflow_id": workflow_id} if workflow_id else {},
        )


# Database Errors
class DatabaseError(AIResearchAgentError):
    """Raised when database operation fails"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details=details,
        )


class RecordNotFoundError(DatabaseError):
    """Raised when database record is not found"""
    
    def __init__(self, message: str, record_type: Optional[str] = None, record_id: Optional[int] = None):
        super().__init__(
            message=message,
            details={"record_type": record_type, "record_id": record_id},
        )
        self.code = "RECORD_NOT_FOUND"


# Configuration Errors
class ConfigurationError(AIResearchAgentError):
    """Raised when configuration is invalid"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={"config_key": config_key} if config_key else {},
        )


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is missing"""
    
    def __init__(self, service: str):
        super().__init__(
            message=f"API key not configured for {service}",
            config_key=f"{service.upper()}_API_KEY",
        )
        self.code = "MISSING_API_KEY"


# ArXiv Paper Errors
class ArXivPaperError(AIResearchAgentError):
    """Base exception for ArXiv paper operations"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ARXIV_PAPER_ERROR",
            details=details,
        )


class InvalidArXivIdError(ArXivPaperError):
    """Raised when ArXiv ID format is invalid"""
    
    def __init__(self, arxiv_id: str):
        self.arxiv_id = arxiv_id
        super().__init__(
            message=(
                f"Invalid ArXiv ID format: '{arxiv_id}'. "
                f"Expected format: '2508.07407' or 'arxiv:2508.07407v2'"
            ),
            details={"arxiv_id": arxiv_id},
        )
        self.code = "INVALID_ARXIV_ID"


class PaperNotFoundError(ArXivPaperError):
    """Raised when paper is not found on ArXiv"""
    
    def __init__(self, arxiv_id: str):
        self.arxiv_id = arxiv_id
        super().__init__(
            message=f"Paper not found on ArXiv: {arxiv_id}",
            details={"arxiv_id": arxiv_id},
        )
        self.code = "PAPER_NOT_FOUND"


class PaperContentInsufficientError(ArXivPaperError):
    """Raised when paper content is insufficient for research"""
    
    def __init__(self, message: str = "Paper content is insufficient for research", arxiv_id: Optional[str] = None):
        super().__init__(
            message=message,
            details={"arxiv_id": arxiv_id} if arxiv_id else {},
        )
        self.code = "PAPER_CONTENT_INSUFFICIENT"


class MultiplePapersLimitError(ArXivPaperError):
    """Raised when too many papers are requested"""
    
    def __init__(self, count: int, limit: int = 5):
        self.count = count
        self.limit = limit
        super().__init__(
            message=f"Maximum {limit} papers allowed, got {count}",
            details={"requested": count, "limit": limit},
        )
        self.code = "MULTIPLE_PAPERS_LIMIT"


# Backwards compatibility aliases
LLMRateLimitError = RateLimitExceededError
ResearchAgentError = AIResearchAgentError
PipelineExecutionError = PipelineError
