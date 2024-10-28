from rest_framework import pagination
from rest_framework.exceptions import ValidationError


class CustomPagination(pagination.PageNumberPagination):
    """
    Custom pagination class for API views.

    Attributes:
        page_size (int): The number of items to include on each page.
        max_page_size (int): The maximum number of items that can be requested per page.
        page_query_param (str): The query parameter name for specifying the page number.
        page_size_query_param (str): The query parameter name for specifying the page size.

    Note:
        If `page_size` is set to "all", it will return all items without pagination.
    """

    # Default values
    page_size = 10
    max_page_size = 100
    page_query_param = "page"
    page_size_query_param = "page_size"

    def get_page_size(self, request):
        page_size = request.query_params.get(self.page_size_query_param, self.page_size)

        # Convert page_size to int if it's a string number
        if isinstance(page_size, str):
            if page_size.isdigit():
                page_size = int(page_size)
            elif page_size.lower() == "all":
                return None  # Return all items without pagination
            else:
                raise ValidationError('page size must be an integer or "all"')

        # Ensure page_size does not exceed max_page_size
        if page_size is not None:
            return min(page_size, self.max_page_size)
        return self.page_size
