import json
import time
from collections import defaultdict
from typing import Any

from fastapi import Request

from app.common.constants.error_constant import ErrorConstant
from app.core.config.environment_config import settings
from app.core.exception.app_exception import AppException
from app.core.logging.logger import logger

# Store rate limit data for different keys (IP, IP+endpoint)
# TODO: Add this to redis or any other cache provider
rate_limit_data = defaultdict(lambda: {'count': 0, 'last_reset_time': time.time()})
DEFAULT_RATE_LIMIT_COUNT = 10  # max requests per window
DEFAULT_RATE_LIMIT_TIME = 10  # in seconds


def get_rate_limit_key(client_ip: str, endpoint: str = None) -> str:
    """Generate a unique key for rate limiting based on IP and optionally endpoint"""
    if endpoint:
        return f'{client_ip}:{endpoint}'
    return client_ip


def get_limit_config(endpoint: str) -> dict[str, Any]:
    """Get rate limit configuration for a specific endpoint or global"""
    try:
        config = json.loads(settings.RATE_LIMIT_CONFIG)
        # Check if endpoint-specific config exists
        if endpoint in config:
            return config[endpoint]

        if 'global' in config:
            return config['global']

        # Return default config as fallback
        return {'counts': DEFAULT_RATE_LIMIT_COUNT, 'time': DEFAULT_RATE_LIMIT_TIME}

    except json.JSONDecodeError:
        # Return default config if JSON is invalid
        return {'counts': DEFAULT_RATE_LIMIT_COUNT, 'time': DEFAULT_RATE_LIMIT_TIME}


async def rate_limiter(request: Request, call_next):
    client_ip = request.client.host
    endpoint = request.url.path

    # Get rate limit configuration for this endpoint
    limit_config = get_limit_config(endpoint)
    max_requests = limit_config.get('counts')
    window_time = limit_config.get('time')

    # Create key for rate limiting (IP + endpoint if endpoint-specific, just IP if global)
    rate_limit_key = get_rate_limit_key(client_ip, endpoint)

    current_time = time.time()
    rate_info = rate_limit_data[rate_limit_key]

    # Reset counter if time window has expired
    if current_time - rate_info['last_reset_time'] > window_time:
        rate_info['count'] = 0
        rate_info['last_reset_time'] = current_time

    rate_info['count'] += 1

    logger.info(
        f'Request from {client_ip} to {endpoint} - Count: {rate_info["count"]}/{max_requests}'
    )

    if rate_info['count'] > max_requests:
        raise AppException(ErrorConstant.TOO_MANY_REQUESTS)

    return await call_next(request)
