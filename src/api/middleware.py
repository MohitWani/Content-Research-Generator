"""
API Middleware for error handling, logging, and request processing
"""
import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.lib.models.exceptions import (
    AIResearchAgentError,
    QueryCategorizationError,
    ResearchDataInsufficientError,
    ExternalAPIError,
    RateLimitExceededError,
    LLMError,
)
from src.common.logger import setup_logger

logger = setup_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handling middleware
    Catches exceptions and returns consistent error responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        
        except QueryCategorizationError as e:
            logger.warning(f"Query categorization error: {e.message}")
            return JSONResponse(
                status_code=400,
                content=e.to_dict(),
            )
        
        except ResearchDataInsufficientError as e:
            logger.warning(f"Insufficient research data: {e.message}")
            return JSONResponse(
                status_code=422,
                content=e.to_dict(),
            )
        
        except RateLimitExceededError as e:
            logger.warning(f"Rate limit exceeded: {e.message}")
            headers = {}
            if e.retry_after:
                headers["Retry-After"] = str(e.retry_after)
            return JSONResponse(
                status_code=429,
                content=e.to_dict(),
                headers=headers,
            )
        
        except ExternalAPIError as e:
            logger.error(f"External API error: {e.message}")
            return JSONResponse(
                status_code=502,
                content=e.to_dict(),
            )
        
        except LLMError as e:
            logger.error(f"LLM error: {e.message}")
            return JSONResponse(
                status_code=503,
                content=e.to_dict(),
            )
        
        except AIResearchAgentError as e:
            logger.error(f"Application error: {e.message}")
            return JSONResponse(
                status_code=500,
                content=e.to_dict(),
            )
        
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"error_type": type(e).__name__},
                },
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware
    Logs request/response details and timing
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = f"{duration:.3f}"
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Request validation middleware
    Validates content type and request size
    """
    
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "REQUEST_TOO_LARGE",
                    "message": f"Request body too large (max: {self.MAX_CONTENT_LENGTH} bytes)",
                },
            )
        
        return await call_next(request)

