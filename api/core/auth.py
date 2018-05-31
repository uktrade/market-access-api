from django.conf import settings
from rest_framework.permissions import BasePermission


class IsServer(BasePermission):
    """ Abstract class to check if request is from expected server


    Child classes just need to inherit and specify `server_name` attribute
    """

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        return request.server_name == self.server_name


class IsMAServer(IsServer):
    server_name = 'ma'


class IsMAUser(BasePermission):
    """ Allows access only to Market Access users """

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        return request.user and request.user.is_authenticated
