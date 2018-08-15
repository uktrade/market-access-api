from django.conf import settings
from rest_framework.permissions import BasePermission


class IsAuthenticated(BasePermission):
    """
    Allows access when DEBUG else only to authenticated users.
    """

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        return request.user and request.user.is_authenticated
