import ast

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.common.constants.app_constant import description, title, version
from app.common.middleware import auth_middleware
from app.common.middleware.log_requests import log_requests
from app.common.middleware.rate_limiter import rate_limiter
from app.common.middleware.request_context import request_context_middleware
from app.core.config.environment_config import settings
from app.core.exception.app_exception import AppException
from app.core.exception.global_handlers import GlobalExceptionHandlers
from app.core.lifecycle import lifecycle_manager
from app.core.logging.logger import logger
from app.modules import v1_router
from app.modules.health.routers.endpoints import health_router
from app.modules.well_known.endpoints import well_known_router


# Print routes when app starts
def print_routes(app: FastAPI):
    for route in app.routes:
        methods = ','.join(route.methods or [])
        logger.info(f'Methods: {methods} | Endpoint: {route.path}')

    logger.info(f'Swagger URL: http://{settings.APP_HOST}:{settings.APP_PORT}/docs')


app = FastAPI(
    title=title,
    version=version,
    description=description,
    lifespan=lifecycle_manager.lifespan,
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title='Secured API',
        version='1.0',
        description='API with global Bearer token security',
        routes=app.routes,
    )
    schema['components']['securitySchemes'] = {
        'BearerAuth': {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'}
    }

    # Add security to endpoints that are not public
    public_endpoints_list = ast.literal_eval(settings.PUBLIC_ENDPOINTS)
    public_endpoints = {
        (item['endpoint'], item['method']) for item in public_endpoints_list
    }

    for path, methods in schema['paths'].items():
        for method, op in methods.items():
            if (path, method.upper()) not in public_endpoints:
                op.update({'security': [{'BearerAuth': []}]})

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi


def create_app():
    app.middleware('http')(auth_middleware)
    app.middleware('http')(log_requests)
    app.middleware('http')(request_context_middleware)
    app.middleware('http')(rate_limiter)

    exception_handlers = GlobalExceptionHandlers()
    app.add_exception_handler(AppException, exception_handlers.app_error_handler)
    app.add_exception_handler(Exception, exception_handlers.generic_exception_handler)

    # Mount router with versioning prefix `v1`
    # Uncomment/comment the below line to enable/disable **versioning**
    app.include_router(v1_router.register_routes_based_on_config(), prefix='/api/v1')

    # Mount well-known endpoints
    app.include_router(well_known_router, prefix='/.well-known')

    # Mount health check router
    app.include_router(health_router, prefix='/api')

    print_routes(app)
    return app
