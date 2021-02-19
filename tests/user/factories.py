from django.contrib.auth.models import Group

from api.core.test_utils import create_test_user
from api.user.constants import UserRoles


class UserFactoryMixin:
    """
    Used to provide helper functions in test cases
    where various users with different permissions are needed to be created.
    """

    def __create_user(
        self,
        role=None,
        is_superuser=False,
        is_staff=False,
    ):
        """
        Creates a user for testing purposes.
        :param role: Role based user group.
        :return: User object
        """
        user_kwargs = {
            "is_superuser": is_superuser,
            "is_staff": is_staff,
        }
        user = create_test_user(**user_kwargs)

        if role:
            try:
                role_group = Group.objects.get(name=role)
                user.groups.add(role_group)
            except Group.DoesNotExist:
                pass

        return user

    def create_standard_user(self, **kwargs):
        return self.__create_user(**kwargs)

    def create_sifter(self, **kwargs):
        return self.__create_user(role=UserRoles.SIFTER, **kwargs)

    def create_editor(self, **kwargs):
        return self.__create_user(role=UserRoles.EDITOR, **kwargs)

    def create_publisher(self, **kwargs):
        return self.__create_user(role=UserRoles.PUBLISHER, **kwargs)

    def create_admin(self, **kwargs):
        return self.__create_user(role=UserRoles.ADMIN, **kwargs)
