from datetime import datetime

from django.db.models import Case, F, FloatField, Q, Value, When
from django_filters.rest_framework import CharFilter, Filter, FilterSet
from rest_framework import filters

from ..models import Genre, Review, Title


class CustomOrdering(filters.OrderingFilter):
    """
    Custom ordering filter for search results.
    This filter extends the `OrderingFilter` class and provides custom ordering based on search results.
    It overrides the `filter_queryset` method to implement best match ordering for search results.
    Parameters:
    - ordering_param (str): The name of the ordering parameter in the request.
    Methods:
    - filter_queryset(request, queryset, view): Filters the queryset based on the ordering parameter and search term.
    Usage:
    1. Create an instance of `CustomOrdering` and add it to the filter backends in your view.
    2. Set the `ordering_param` attribute to specify the name of the ordering parameter in the request.
    3. When the ordering parameter is set to "best_match" and a search term is provided, the queryset will be annotated with match ranks based on the search term and ordered by the rank.
    4. If no specific ordering or search term is provided, the default ordering will be used.
    Example:
    ```
    class MyView(generics.ListAPIView):
        filter_backends = [CustomOrdering]
    ```
    """

    ordering_param = "order_by"

    # Implement best match ordering based for search results
    def filter_queryset(self, request, queryset, view):
        # Retrieve the ordering parameter and search term from the request
        ordering = request.query_params.get(self.ordering_param)
        search_term = request.query_params.get("search")

        # Determine the ordering direction
        order_direction = ""
        if ordering:
            if ordering[0] == "-":
                order_direction = "-"
                ordering = ordering[1:]

        if ordering == "best_match" and search_term:
            # Annotate the queryset with match ranks based on the search term
            queryset = queryset.annotate(
                k1=Case(
                    When(title__iexact=search_term, then=Value(2.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                k2=Case(
                    When(title__istartswith=search_term, then=Value(2.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                k3=Case(
                    When(title__icontains=search_term, then=Value(1.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                k4=Case(
                    When(title__iendswith=search_term, then=Value(1.0)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                rank=F("k1") + F("k2") + F("k3") + F("k4"),
            ).order_by(f"{order_direction}rank")

            return queryset

        # If no specific ordering or search term is provided, fallback to default ordering
        return super().filter_queryset(request, queryset, view)


class YearRangeFilter(Filter):
    """
    Filter the queryset based on a range of years.

    Args:
        qs (QuerySet): The queryset to be filtered.
        value (str): The range of years in the format "start_year,end_year".

    Returns:
        QuerySet: The filtered queryset.

    Example:
        >>> filter = YearRangeFilter()
        >>> queryset = filter.filter(queryset, "2000,2020")
    """

    def filter(self, qs, value):
        if value:
            start_year, end_year = value.split(",")
            start_date = datetime(int(start_year), 1, 1)
            end_date = datetime(int(end_year), 12, 31, 23, 59, 59)
            return qs.filter(
                Q(**{f"{self.field_name}__gte": start_date})
                & Q(**{f"{self.field_name}__lte": end_date})
            )
        return qs


class RangeFilter(Filter):
    """
    Filter the queryset `qs` based on the range of values specified in `value`.

    Args:
        qs (QuerySet): The queryset to be filtered.
        value (str): The range of values to filter by, in the format "min_value,max_value".

    Returns:
        QuerySet: The filtered queryset.

    Example:
        >>> qs = Movie.objects.all()
        >>> filter = RangeFilter(field_name="rating")
        >>> filtered_qs = filter.filter(qs, "4,8")
    """

    def filter(self, qs, value):
        if value:
            min_value, max_value = value.split(",")
            return qs.filter(**{f"{self.field_name}__gte": min_value}) & qs.filter(
                **{f"{self.field_name}__lte": max_value}
            )
        return qs


class TitleFilter(FilterSet):
    """
    Filter class for filtering Title objects.
    Available filters:
    - search: Filter titles that contain the search term in the title and sort by closest match.
    - movie_or_tv: Filter titles by movie or TV show.
    - year_range: Filter titles by release year range.
    - rating_range: Filter titles by rating range.
    - genres: Filter titles by genre.
    Note: The `search` filter searches for titles that contain the search term in the title and sorts the results by closest match.
    Example usage:
    ```
    filter = TitleFilter(data=request.GET)
    queryset = filter.qs
    ```
    """

    search = CharFilter(method="filter_search")
    movie_or_tv = CharFilter(method="filter_movie_or_tv")
    year_range = YearRangeFilter(
        field_name="release_date", label="Year Range (YYYY,YYYY)"
    )
    rating_range = RangeFilter(field_name="rating")
    genres = CharFilter(method="filter_genres")

    class Meta:
        model = Title
        fields = []  # You can add fields if there are any default fields to include

    def filter_search(self, queryset, name, value):
        """
        Filter titles that contain the search term in the title and sort by closest match.
        Args:
            queryset (QuerySet): The queryset to filter.
            name (str): The name of the filter.
            value (str): The search term.
        Returns:
            QuerySet: The filtered queryset.
        """
        # Search for titles that contain the search term in the title and sort by closest match

        return queryset.filter(title__icontains=value)

    def filter_movie_or_tv(self, queryset, name, value):
        """
        Filter titles by movie or TV show.
        Args:
            queryset (QuerySet): The queryset to filter.
            name (str): The name of the filter.
            value (str): The filter value.
        Returns:
            QuerySet: The filtered queryset.
        """
        if value == "all":
            return queryset
        return queryset.filter(movie_or_tv=value).distinct()

    def filter_genres(self, queryset, name, value):
        """
        Filter titles by genre.
        Args:
            queryset (QuerySet): The queryset to filter.
            name (str): The name of the filter.
            value (str): The filter value (a list of genre ids separated by commas).
        Returns:
            QuerySet: The filtered queryset.
        """
        # value is a list of genre ids separated by commas
        genre_ids = value.split(",")
        return queryset.filter(genres__id__in=genre_ids).distinct()


class ReviewFilter(FilterSet):
    """
    Filter class for filtering Review objects based on title.
    """

    title = CharFilter(method="filter_title")

    class Meta:
        model = Review
        fields = []  # You can add fields if there are any default fields to include

    def filter_title(self, queryset, name, value):
        """
        Filter method for filtering Review objects based on title.
        Parameters:
            queryset (QuerySet): The queryset to filter.
            name (str): The name of the filter field.
            value (str): The value to filter by.
        Returns:
            QuerySet: The filtered queryset.
        """
        return queryset.filter(title=value)


class GenreFilter(FilterSet):
    """
    Filter class for Genre model.
    Attributes:
        ids: A comma-separated string of genre IDs to filter by.
    Methods:
        filter_ids: Filter method to filter queryset by genre IDs.
    Meta:
        model: The Genre model.
        fields: An empty list. Additional fields can be added if needed.
    """

    ids = CharFilter(method="filter_ids")

    class Meta:
        model = Genre
        fields = []  # You can add fields if there are any default fields to include

    def filter_ids(self, queryset, name, value):
        """
        Filter method to filter queryset by genre IDs.
        Args:
            queryset: The queryset to filter.
            name: The name of the filter field.
            value: The comma-separated string of genre IDs.
        Returns:
            The filtered queryset based on the genre IDs.
        """
        return queryset.filter(id__in=value.split(","))
