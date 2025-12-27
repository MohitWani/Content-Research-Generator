import ast

from fastapi import APIRouter

from app.common.constants.error_constant import ErrorConstant
from app.common.constants.service_constant import ModulesEnum
from app.core.config.environment_config import settings
from app.core.exception.app_exception import AppException
from app.core.logging.logger import logger


# Registered module based on the configuration
def register_routes_based_on_config() -> APIRouter:
    # Add `tags=["API Version V1"]` in APIRouter argument to see all v1 endpoints in the swagger UI
    v1_router_internal = APIRouter()

    try:
        module_names = ast.literal_eval(settings.MODULE_NAMES)
    except (ValueError, SyntaxError):
        # Handle comma-separated format
        module_names = [m.strip() for m in settings.MODULE_NAMES.split(',') if m.strip()]

    logger.info(f'Registering modules: {module_names}')

    # Register auth router (always enabled)
    try:
        from app.modules.auth.routers.endpoints import auth_router

        v1_router_internal.include_router(auth_router, prefix='/auth', tags=['Auth'])
    except ImportError:
        logger.warning('Auth module not available')

    # Register user router
    if 'user' in module_names or 'USER' in module_names:
        try:
            from app.modules.user.routers.v1.endpoints import user_router

            v1_router_internal.include_router(user_router, prefix='/user', tags=['User'])
        except ImportError:
            logger.warning('User module not available')

    # Register research router
    if 'research' in module_names or 'RESEARCH' in module_names:
        try:
            from app.modules.research.routers.v1.endpoints import research_router

            v1_router_internal.include_router(
                research_router, prefix='/research', tags=['Research']
            )
            logger.info('Research module registered')
        except ImportError as e:
            logger.warning(f'Research module not available: {e}')

    # Register paper router
    if 'paper' in module_names or 'PAPER' in module_names:
        try:
            from app.modules.paper.routers.v1.endpoints import paper_router

            v1_router_internal.include_router(
                paper_router, prefix='/paper', tags=['Paper']
            )
            logger.info('Paper module registered')
        except ImportError as e:
            logger.warning(f'Paper module not available: {e}')

    return v1_router_internal
