from fastapi import Request, Response

from app.core.logging.logger import logger


async def log_requests(request: Request, call_next):
    logger.info(f'Started request path={request.url.path} method={request.method}')
    try:
        response: Response = await call_next(request)
    except Exception as e:
        logger.exception(f'Exception during request: {e}')
        raise
    logger.info(
        f'Completed request path={request.url.path} status_code={response.status_code}'
    )
    return response
