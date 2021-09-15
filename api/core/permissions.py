from django.conf import settings
from rest_framework.permissions import BasePermission


class IsAuthenticated(BasePermission):
    """
    Allows access when DEBUG else only to authenticated users.
    """

    def has_permission(self, request, view):
        """Ignore usual authentication and autherization if SSO is not enabled"""
        if not settings.SSO_ENABLED:
            return True
        return request.user and request.user.is_authenticated
