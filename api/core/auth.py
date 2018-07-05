from django.conf import settings
from rest_framework.permissions import BasePermission


class IsMAServer(BasePermission):
    server_name = 'ma'

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        # return request.server_name == self.server_name
        return True


class IsMAUser(BasePermission):
    """ Allows access only to Market Access users """

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        print(request.user)
        return request.user and request.user.is_authenticated
