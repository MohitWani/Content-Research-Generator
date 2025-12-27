import ast

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from app.common.constants.error_constant import ErrorConstant
from app.core.auth.jwt_handler import jwt_handler
from app.core.config.environment_config import settings
from app.core.exception.app_exception import AppException


def _get_token(request: Request) -> str | None:
    """Extract token from the Authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    return auth_header[7:] if auth_header.startswith('Bearer ') else auth_header


async def auth_middleware(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    """
    Middleware to handle authentication for all incoming requests.
    This middleware enforces authentication by default for all endpoints.
    """

    # Step 1: Check if the path and method is public
    public_endpoints_list = ast.literal_eval(settings.PUBLIC_ENDPOINTS)
    public_endpoints = {
        (item['endpoint'], item['method']) for item in public_endpoints_list
    }
    if (request.url.path, request.method.upper()) in public_endpoints:
        return await call_next(request)

    # Step 1b: Check prefix-based public paths (for routes with path params)
    public_prefixes = ['/api/v1/research/', '/api/v1/paper/']
    if any(request.url.path.startswith(prefix) for prefix in public_prefixes):
        return await call_next(request)

    # Step 2: Get token for protected routes
    token = _get_token(request)

    # Step 3: Handle token verification
    if not token:
        raise AppException(ErrorConstant.UNAUTHORIZED)

    try:
        token_data = jwt_handler.verify_token(token, 'access')
        request.state.user = {'user_id': token_data.user_id}
    except Exception as e:
        raise AppException(ErrorConstant.UNAUTHORIZED) from e

    return await call_next(request)
