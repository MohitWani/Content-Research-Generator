# Rate Limiting Configuration

## Overview

The enhanced rate limiting system supports both global and endpoint-specific rate limits. This allows you to set different limits for different endpoints while maintaining a global limit as a fallback.

## Configuration

Rate limits are configured through the `RATE_LIMIT_CONFIG` environment variable, which accepts a JSON string with the following structure:

```json
{
  "global": {
    "counts": 10,
    "time": 60
  },
  "/api/v1/user": {
    "counts": 5,
    "time": 60
  },
  "/api/v1/health": {
    "counts": 20,
    "time": 30
  }
}
```

### Configuration Parameters

- **global**: Default rate limit applied to all endpoints
- **endpoint-specific**: Rate limits for specific endpoints (e.g., `/api/v1/user`)
- **counts**: Maximum number of requests allowed
- **time**: Time window in seconds for the rate limit

## How It Works

1. **Single Limit Check**: For each request, only one limit is checked:
   - If the endpoint has a specific configuration, use that limit
   - Otherwise, use the global limit
2. **IP-based Tracking**: Limits are tracked per IP address and per IP+endpoint combination
3. **Time Window Management**: Counters automatically reset when time windows expire

## Example Configuration

### .env File

```bash
# Rate limiting with endpoint-specific limits
RATE_LIMIT_CONFIG={"global": {"counts": 10, "time": 60}, "/api/v1/user": {"counts": 5, "time": 60}, "/api/v1/health": {"counts": 20, "time": 30}}
```

### Behavior Examples

1. **Global Limit**: 10 requests per 60 seconds for all endpoints (default)
2. **User Endpoint**: 5 requests per 60 seconds (endpoint-specific)
3. **Health Endpoint**: 20 requests per 30 seconds (endpoint-specific)

## Response Headers

When a rate limit is exceeded, the system returns:

- **Status Code**: 429 (Too Many Requests)
- **Content**: Detailed error message with limit information

## Logging

The system logs rate limit information for each request:

```
Request from 192.168.1.1 to /api/v1/user - Count: 3/5
```

## Implementation Details

- Uses in-memory storage with `defaultdict` for tracking
- Supports both IP-only and IP+endpoint tracking
- Automatically resets counters when time windows expire
- Graceful fallback to default configuration if JSON parsing fails
- Simple logic: one limit check per request (endpoint-specific or global)
