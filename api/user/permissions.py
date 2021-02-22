from django.contrib.auth.models import Group
from rest_framework import permissions

from api.user.constants import UserRoles


def _is_in_group(user, group_name):
    """
    Takes a user and a group name, and returns `True` if the user is in that group.
    """
    try:
        return Group.objects.get(name=group_name).user_set.filter(id=user.id).exists()
    except Group.DoesNotExist:
        return None


def _has_group_permission(user, required_groups):
    return any([_is_in_group(user, group_name) for group_name in required_groups])


class BasePermission(permissions.BasePermission):
    required_groups = ()
    allowed_actions = ()

    def has_permission(self, request, view):
        allowed_action = view.action in self.allowed_actions
        user_has_group_permission = _has_group_permission(
            request.user, self.required_groups
        )
        authenticated_user = request.user and request.user.is_authenticated
        return bool(
            authenticated_user and (allowed_action or user_has_group_permission)
        )


class AllRetrieveAndEditorUpdateOnly(BasePermission):
    """
    Allow GET to all authenticated users
    Allow PATCH to authenticated editors, publishers and admins
    """

    allowed_actions = (
        "list",
        "retrieve",
    )
    required_groups = (
        UserRoles.EDITOR,
        UserRoles.PUBLISHER,
        UserRoles.ADMIN,
    )


class IsSifter(BasePermission):
    """
    Roles that have Sifter permissions.
    """

    required_groups = (
        UserRoles.SIFTER,
        UserRoles.EDITOR,
        UserRoles.PUBLISHER,
        UserRoles.ADMIN,
    )


class IsEditor(BasePermission):
    """
    Roles that have Editor permissions.
    """

    required_groups = (
        UserRoles.EDITOR,
        UserRoles.PUBLISHER,
        UserRoles.ADMIN,
    )


class IsPublisher(BasePermission):
    """
    Roles that have Publisher permissions.
    """

    required_groups = (
        UserRoles.PUBLISHER,
        UserRoles.ADMIN,
    )


class IsAdmin(BasePermission):
    """
    Roles that have Publisher permissions.
    """

    required_groups = (UserRoles.ADMIN,)
