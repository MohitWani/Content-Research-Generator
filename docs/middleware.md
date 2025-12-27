# Request Context Middleware

This middleware uses Python's `contextvar` to store request context information that can be accessed throughout the application, including in services, repositories, and utility functions.

The middleware uses a **single context variable** that holds a dictionary with all request context data, making it easy to add new fields in the future.

## Features

The middleware captures the following request information:

- **requestId**: Generated UUID or extracted from `X-Request-ID` header
- **originalUrl**: Complete request URL
- **method**: HTTP method (GET, POST, etc.)
- **userAgent**: User agent string from request headers
- **host**: Host header value
- **clientIp**: Client IP address (supports proxy headers)
- **startTime**: Request start timestamp

## Usage

### Direct Access

Use functions from `app.common.middleware` directly for context access:

```python
from app.common.middleware import get_request_context

# Get all context as dictionary
context = get_request_context()
```

### Example in Service Layer

```python
from app.common.middleware import get_request_context
from app.core.logging.logger import logger

class UserService:
    def list_users(self, db: Session) -> list[User]:
        # Direct access for context information
        context = get_request_context()

        logger.info(f"Fetch users - Request ID: {context['request_id']}")
        logger.info(f"Request context: {context}")

        users = self.repository.list_users(db=db)

        logger.info(f"Found users: {len(users)} - Request ID: {context['request_id']}")
        return users
```

## Adding New Context Fields

To add new fields to the request context, simply update the `context_data` dictionary in the middleware:

```python
# In request_context_middleware function
context_data = {
    'request_id': request_id,
    'original_url': str(request.url),
    'method': request.method,
    'user_agent': request.headers.get('User-Agent'),
    'host': request.headers.get('Host'),
    'client_ip': client_ip,
    'start_time': time.time(),
    # Add new fields here
    'new_field': request.headers.get('X-Custom-Header'),
}
```

## Logging

All logs automatically include request context information when available. The middleware also logs request start/completion with timing information.

## Benefits

1. **Request Tracing**: Track requests across all layers of your application
2. **Debugging**: Easily correlate logs from different parts of the application
3. **Performance Monitoring**: Track request duration and performance
4. **Audit Trail**: Maintain context for security and compliance
5. **Distributed Tracing**: Support for distributed systems with request IDs
6. **Easy Extension**: Simple to add new context fields
7. **Simple Architecture**: Single context variable with direct access functions

## Thread Safety

The middleware uses `contextvar` which is thread-safe and designed for async applications. Each request gets its own isolated context that doesn't interfere with other requests.
