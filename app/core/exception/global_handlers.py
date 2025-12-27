import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.exception.app_exception import AppException


class GlobalExceptionHandlers:
    async def app_error_handler(self, request: Request, exc: AppException):
        """
        Handles our custom application-wide AppError.
        Provides a consistent JSON error response based on the AppError details.
        """
        print(
            f'AppError caught: Code={exc.http_code}, Type={exc.error_constant.name}, Message={exc.message}'
        )
        return JSONResponse(
            status_code=exc.http_code,
            content={
                'message': exc.message,
                'code': exc.http_code,
                'error_type': exc.error_constant.name,
            },
        )

    async def generic_exception_handler(self, request: Request, exc: Exception):
        """
        Catches any other unhandled Python exceptions not covered by AppError.
        Returns a generic 500 Internal Server Error and logs the full traceback server-side.
        """
        # Log the full exception details for debugging purposes (server-side only).
        # This traceback is NOT sent to the client.
        print(f'An unhandled generic exception occurred: {type(exc).__name__}: {exc}')
        traceback.print_exc()  # Prints the stack trace to the server logs

        # Always return a generic 500 for unhandled exceptions to prevent information leakage.
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                'message': 'An unexpected internal server error occurred. Please try again later.',
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'error_type': 'Internal Server Error',
            },
        )
