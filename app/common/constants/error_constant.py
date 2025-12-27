# All constants related to error codes
from enum import Enum


class ErrorConstant(Enum):
    TOO_MANY_REQUESTS = (429, 'Too many requests')
    UNAUTHORIZED = (401, 'Unauthorized')
    INTERNAL_SERVER_ERROR = (500, 'Internal server error')
    NOT_FOUND = (404, 'Not found')
    BAD_REQUEST = (400, 'Bad request')
    CONFLICT = (409, 'Conflict')

    @property
    def http_code(self) -> int:
        return self.value[0]

    @property
    def message(self) -> str:
        return self.value[1]
