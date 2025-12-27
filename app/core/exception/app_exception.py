from app.common.constants.error_constant import ErrorConstant


class AppException(Exception):
    """
    Custom application-wide exception.
    It takes an ErrorConstant member and optionally a custom message.
    """

    def __init__(self, error_constant: ErrorConstant, custom_message: str = None):
        self.error_constant = error_constant
        # If a custom message is provided, use it; otherwise, use the default from ErrorConstant.
        self.message = custom_message if custom_message else error_constant.message
        self.http_code = error_constant.http_code
        super().__init__(self.message)  # Call the base Exception constructor
