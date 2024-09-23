import json
from fnmatch import fnmatch

import inflection
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from rest_framework.request import Request

# List of views where case conversion should be applied
apply_case_conversion_views = [
    "/users/",
    "/users/*/",
    "/titles/",
    "/titles/*/",
    "/reviews/",
    "/reviews/*/",
    "/genres/",
    "/genres/*/",
    "/create-user/",
    "/get-tmdb-search/",
    "/password-reset/",
    "/validation/",
    "/validation-confirm/",
]


def adjust_urls_for_script_name(urls):
    """
    Adjust URLs based on the FORCE_SCRIPT_NAME setting.

    """
    # Adjust URLs based on FORCE_SCRIPT_NAME setting
    if hasattr(settings, "FORCE_SCRIPT_NAME") and settings.FORCE_SCRIPT_NAME:
        script_name = settings.FORCE_SCRIPT_NAME.rstrip(
            "/"
        )  # Remove trailing slash if any
        return [script_name + url for url in urls]
    return urls


apply_case_conversion_views = adjust_urls_for_script_name(apply_case_conversion_views)


def camel_to_snake(data):
    """
    Convert keys in a dictionary from camel case to snake case.

    """
    # Convert keys in a dictionary from camel case to snake case
    if isinstance(data, dict):
        return {inflection.underscore(k): camel_to_snake(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [camel_to_snake(item) for item in data]
    return data


def snake_to_camel(data):
    """
    Convert keys in a dictionary from snake case to camel case.
    """
    # Convert keys in a dictionary from snake case to camel case
    if isinstance(data, dict):
        return {
            inflection.camelize(k, False): snake_to_camel(v) for k, v in data.items()
        }
    elif isinstance(data, list):
        return [snake_to_camel(item) for item in data]
    return data


class CaseConversionMiddleware(MiddlewareMixin):
    """
    Middleware that applies case conversion to the request and response data.
    This middleware is responsible for converting the case of specific fields within the request and response data. It applies snake_case to camelCase fields in the request data and camelCase to snake_case fields in the response data.

    Attributes:
        None
    Methods:
        process_request(request): Applies case conversion to the request data.
        process_response(request, response): Applies case conversion to the response data.
    """

    def process_request(self, request):
        if any(
            fnmatch(request.path, pattern) for pattern in apply_case_conversion_views
        ):
            # Handle GET parameters
            if request.method == "GET":
                query_params = request.GET.copy()  # Create a mutable copy
                snake_case_params = camel_to_snake(query_params)
                # Apply case conversion to specific fields within the JSON data
                selected_columns = snake_case_params.get("selected_columns")
                if selected_columns:
                    snake_case_params["selected_columns"] = ",".join(
                        [
                            inflection.underscore(column)
                            for column in selected_columns.split(",")
                        ]
                    )

                order_by = snake_case_params.get("order_by")
                if order_by:
                    if order_by.startswith("-"):
                        snake_case_params["order_by"] = "-" + inflection.underscore(
                            order_by[1:]
                        )
                    else:
                        snake_case_params["order_by"] = inflection.underscore(order_by)
                request.GET = snake_case_params  # Update the request's GET dictionary

            # Handle POST data (JSON)
            elif request.content_type == "application/json":
                try:
                    data = json.loads(request.body)
                    snake_case_data = camel_to_snake(data)

                    # Apply case conversion to specific fields within the JSON data
                    selected_columns = snake_case_data.get("selected_columns")
                    if selected_columns:
                        snake_case_data["selected_columns"] = [
                            inflection.underscore(column) for column in selected_columns
                        ]

                    order_by = snake_case_data.get("order_by")
                    if order_by:
                        snake_case_data["order_by"] = inflection.underscore(order_by)

                    type = snake_case_data.get("type")
                    # Convert 'type' value to snake case
                    if type:
                        snake_case_data["type"] = inflection.underscore(type)

                    request._body = json.dumps(snake_case_data).encode("utf-8")
                    if isinstance(request, Request):
                        request._full_data = snake_case_data

                except (ValueError, json.JSONDecodeError):
                    pass

        return None

    def process_response(self, request, response):
        if any(
            fnmatch(request.path, pattern) for pattern in apply_case_conversion_views
        ):
            if hasattr(response, "data"):
                try:
                    # Parse the response content manually
                    data = response.data
                    camel_case_data = snake_to_camel(data)
                    # Convert the JSON data back to bytes
                    response.data = camel_case_data
                    response._is_rendered = False
                    response.render()

                except (ValueError, json.JSONDecodeError):
                    pass

        return response
