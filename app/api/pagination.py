from rest_framework import pagination


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
    # set "all" as non paginated
    if page_size == "all":
        page_size = None
