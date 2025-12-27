import contextvars
import time
import uuid
from typing import Any

from fastapi import Request, Response

from app.core.logging.logger import logger

# Single context variable to hold all request context data
request_context_var = contextvars.ContextVar('request_context', default=None)


def get_request_context() -> dict[str, Any] | None:
    """Get the complete request context dictionary."""
    return request_context_var.get()


async def request_context_middleware(request: Request, call_next):
    # Generate or get request ID
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    # Get client IP (considering proxy headers)
    client_ip = (
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        or request.headers.get('X-Real-IP')
        or request.client.host
        if request.client
        else None
    )

    # Create context dictionary with all request data
    context_data = {
        'request_id': request_id,
        'original_url': str(request.url),
        'method': request.method,
        'user_agent': request.headers.get('User-Agent'),
        'host': request.headers.get('Host'),
        'client_ip': client_ip,
        'start_time': time.time(),
    }

    # Set the context variable
    request_context_var.set(context_data)

    try:
        response: Response = await call_next(request)
        return response

    except Exception as e:
        # Log error with context
        logger.error(f'Request failed - ID: {request_id}, Error: {str(e)}')
        raise
