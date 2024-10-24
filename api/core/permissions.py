from logging import getLogger

from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission

from api.user.constants import ADMIN_PROTECTED_USER_FIELDS

logger = getLogger(__name__)


class IsAuthenticated(BasePermission):
    """
    Allows access when DEBUG else only to authenticated users.
    """

    def has_permission(self, request, view):
        """Ignore usual authentication and authorization if SSO is not enabled"""
        if not settings.SSO_ENABLED:
            return True
        return request.user and request.user.is_authenticated


class IsCreatorOrReadOnly(BasePermission):
    """
    Object-level permission to only allow creators of an object to edit it.
    Assumes the model instance has an `created_by` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # Instance must have an attribute named `created_by`.
        return obj.created_by == request.user


class IsUserDetailAdminOrOwner(BasePermission):
    """
    Object-level permission to only allow admins or owners of an object to edit it.
    Field based granularity so Owners cannot edit their own permissions
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in SAFE_METHODS:
            return True

        for field in request.data:
            # Loop through fields in given data, if it is a sensitive field, check
            # the user is an Admin, or return permission denied.
            if field in ADMIN_PROTECTED_USER_FIELDS:
                return request.user.groups.filter(
                    name__in=["Administrator", "Role administrator"]
                ).exists()

        # At this point, we either have no protected fields being changed or are an
        # admin and have already allowed progress. We can now check if the user is the
        # owner of the record and is allowed to change the fields in the request.
        # If the requester is not the owner or an admin and is attempting to
        # perform a restricted method, deny permission.
        return request.user.username == obj.username
