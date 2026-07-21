from rest_framework.views import exception_handler
from rest_framework.exceptions import ErrorDetail

def format_error(value):
    if isinstance(value, dict):
        return {k: format_error(v) for k, v in value.items()}

    if isinstance(value, list):
        if len(value) == 1:
            return format_error(value[0])
        return [format_error(v) for v in value]

    if isinstance(value, ErrorDetail):
        return str(value)

    return value


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data = {
            "error": format_error(response.data)
        }

    return response