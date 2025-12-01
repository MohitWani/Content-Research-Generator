"""
Retry and rate limiting utilities
Provides decorators and helpers for resilient API calls
"""
import asyncio
import functools
import time
from typing import Callable, Any, Type, Tuple, Optional
from dataclasses import dataclass

from src.lib.models.exceptions import (
    ExternalAPIError,
    RateLimitExceededError,
    ServiceUnavailableError,
)
from src.common.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        ExternalAPIError,
        RateLimitExceededError,
        ServiceUnavailableError,
        asyncio.TimeoutError,
        ConnectionError,
    )


def calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool,
) -> float:
    """Calculate delay with exponential backoff and optional jitter"""
    import random
    
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    
    if jitter:
        delay = delay * (0.5 + random.random())
    
    return delay


def retry_async(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = None,
):
    """
    Decorator for async functions with retry logic
    
    Usage:
        @retry_async(max_retries=3)
        async def fetch_data():
            ...
    """
    if retryable_exceptions is None:
        retryable_exceptions = (
            ExternalAPIError,
            RateLimitExceededError,
            ServiceUnavailableError,
            asyncio.TimeoutError,
            ConnectionError,
        )
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = calculate_delay(
                            attempt, base_delay, max_delay, exponential_base, jitter
                        )
                        
                        # Check for retry-after header in rate limit errors
                        if isinstance(e, RateLimitExceededError) and e.retry_after:
                            delay = max(delay, e.retry_after)
                        
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


class RateLimiter:
    """
    Token bucket rate limiter for API calls
    Thread-safe and async-compatible
    """
    
    def __init__(
        self,
        rate: float,  # requests per second
        burst: int = 1,  # maximum burst size
    ):
        """
        Initialize rate limiter
        
        Args:
            rate: Maximum requests per second
            burst: Maximum burst size (tokens in bucket)
        """
        self.rate = rate
        self.burst = burst
        self._tokens = burst
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> float:
        """
        Acquire a token, waiting if necessary
        
        Returns:
            Time waited in seconds
        """
        async with self._lock:
            now = time.monotonic()
            time_passed = now - self._last_update
            self._tokens = min(self.burst, self._tokens + time_passed * self.rate)
            self._last_update = now
            
            if self._tokens >= 1:
                self._tokens -= 1
                return 0.0
            
            # Wait for token to become available
            wait_time = (1 - self._tokens) / self.rate
            await asyncio.sleep(wait_time)
            
            self._tokens = 0
            self._last_update = time.monotonic()
            
            return wait_time
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class ServiceRateLimiters:
    """
    Centralized rate limiters for external services
    """
    
    _limiters: dict = {}
    
    @classmethod
    def get(cls, service: str, rate: float = 1.0, burst: int = 5) -> RateLimiter:
        """
        Get or create a rate limiter for a service
        
        Args:
            service: Service name
            rate: Requests per second
            burst: Maximum burst
        
        Returns:
            RateLimiter instance
        """
        if service not in cls._limiters:
            cls._limiters[service] = RateLimiter(rate=rate, burst=burst)
        return cls._limiters[service]
    
    @classmethod
    def reset(cls, service: Optional[str] = None):
        """Reset rate limiter(s)"""
        if service:
            cls._limiters.pop(service, None)
        else:
            cls._limiters.clear()


def rate_limited(service: str, rate: float = 1.0, burst: int = 5):
    """
    Decorator to apply rate limiting to async functions
    
    Usage:
        @rate_limited("github", rate=5, burst=10)
        async def fetch_repos():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            limiter = ServiceRateLimiters.get(service, rate, burst)
            await limiter.acquire()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def with_timeout(
    coro,
    timeout: float,
    error_message: str = "Operation timed out",
):
    """
    Execute coroutine with timeout
    
    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        error_message: Error message if timeout occurs
    
    Returns:
        Result of coroutine
    
    Raises:
        asyncio.TimeoutError: If timeout occurs
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.error(f"Timeout after {timeout}s: {error_message}")
        raise


class CircuitBreaker:
    """
    Circuit breaker pattern for failing services
    Prevents cascading failures
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_requests: int = 1,
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Failures before opening circuit
            reset_timeout: Seconds before trying again
            half_open_requests: Requests to allow in half-open state
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_requests = half_open_requests
        
        self._failures = 0
        self._last_failure_time = 0.0
        self._state = "closed"  # closed, open, half-open
        self._half_open_count = 0
        self._lock = asyncio.Lock()
    
    @property
    def is_open(self) -> bool:
        return self._state == "open"
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker
        
        Args:
            func: Async function to execute
            *args, **kwargs: Function arguments
        
        Returns:
            Function result
        
        Raises:
            ServiceUnavailableError: If circuit is open
        """
        async with self._lock:
            if self._state == "open":
                if time.monotonic() - self._last_failure_time > self.reset_timeout:
                    self._state = "half-open"
                    self._half_open_count = 0
                else:
                    raise ServiceUnavailableError(
                        "Circuit breaker is open, service temporarily unavailable"
                    )
            
            if self._state == "half-open":
                if self._half_open_count >= self.half_open_requests:
                    raise ServiceUnavailableError(
                        "Circuit breaker is half-open, waiting for test requests"
                    )
                self._half_open_count += 1
        
        try:
            result = await func(*args, **kwargs)
            
            async with self._lock:
                self._failures = 0
                self._state = "closed"
            
            return result
            
        except Exception as e:
            async with self._lock:
                self._failures += 1
                self._last_failure_time = time.monotonic()
                
                if self._failures >= self.failure_threshold:
                    self._state = "open"
                    logger.warning(
                        f"Circuit breaker opened after {self._failures} failures"
                    )
            
            raise

