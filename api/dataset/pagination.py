from rest_framework.pagination import CursorPagination


class MarketAccessDatasetViewCursorPagination(CursorPagination):
    """
    Cursor Pagination for MarketAccessDatasetView
    """

    ordering = ("created_on", "pk")
    page_size = 200
