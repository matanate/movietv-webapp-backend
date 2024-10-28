from http import HTTPStatus
from typing import Any

from rest_framework.exceptions import ErrorDetail
from rest_framework.views import Response, exception_handler


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    """Custom API exception handler."""

    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Using the description's of the HTTPStatus class as error message.
        http_code_to_message = {v.value: v.description for v in HTTPStatus}

        error_payload = {"error": ""}

        # if data contain details and the value is an ErrorDetail deconstruct to strings
        if isinstance(response.data, str):
            error_payload["error"] = response.data
        elif isinstance(response.data, list):
            for details in response.data:
                if isinstance(details, list):
                    error_payload["error"] = ", ".join(
                        [detail.title() for detail in details]
                    )
                elif isinstance(details, ErrorDetail):
                    error_payload["error"] = details.title()
                elif isinstance(details, str):
                    error_payload["error"] = details.title()
        else:
            for key, details in response.data.items():
                if isinstance(details, list):
                    error_payload["error"] = ", ".join(
                        [detail.title() for detail in details]
                    )
                elif isinstance(details, ErrorDetail):
                    error_payload["error"] = details.title()
                elif isinstance(details, str):
                    error_payload["error"] = details.title()

                # check if the error contains "Field" in it and if so replace with the key

                if "This Field" in error_payload["error"]:
                    error_payload["error"] = error_payload["error"].replace(
                        "This Field", key.title().replace("_", " ")
                    )
                elif "Field" in error_payload["error"]:
                    error_payload["error"] = error_payload["error"].replace(
                        "Field", key.title().replace("_", " ")
                    )
        response.data = error_payload
    return response
