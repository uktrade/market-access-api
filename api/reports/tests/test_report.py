from datetime import datetime, timedelta
from secrets import token_hex

import factory
import pytest
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.utils.timezone import now
from oauth2_provider.models import AccessToken, Application
from rest_framework import status
from rest_framework.fields import DateField, DateTimeField
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, RequestsClient

from api.core.test_utils import APITestMixin, create_test_user
from api.reports.tests.factories import Stage1_1ReportFactory


# def get_default_test_user():
#     """Return the test user."""
#     user_model = get_user_model()
#     try:
#         test_user = user_model.objects.get(email='test@user.com')
#     except user_model.DoesNotExist:
#         test_user = create_test_user(
#             first_name='test',
#             last_name='user',
#             email='test@user.com',
#         )
#     return test_user


# def create_test_user(**user_attrs):
#     """
#     :returns: user
#     :param permission_codenames: list of codename permissions to be
#         applied to the user
#     :param user_attrs: any user attribute
#     """
#     user_defaults = {
#         'first_name': factory.Faker('first_name').generate({}),
#         'last_name': factory.Faker('last_name').generate({}),
#         'email': factory.Faker('email').generate({}),
#         'date_joined': now()
#     }
#     user_defaults.update(user_attrs)

#     user_model = get_user_model()
#     user = user_model(**user_defaults)
#     user.save()

#     return user


# class APITestMixin:
#     """All the tests using the DB and accessing end points behind auth should use this class."""

#     pytestmark = pytest.mark.django_db  # use db

#     @property
#     def user(self):
#         """Return the user."""
#         if not hasattr(self, '_user'):
#             self._user = get_default_test_user()
#         return self._user

#     def get_token(self, grant_type=Application.GRANT_PASSWORD, user=None):
#         """Get access token for user test."""
#         if not hasattr(self, '_tokens'):
#             self._tokens = {}

#         if user is None and grant_type != Application.GRANT_CLIENT_CREDENTIALS:
#             user = self.user

#         token_cache_key = (user.email if user else None,)
#         if token_cache_key not in self._tokens:
#             self._tokens[token_cache_key] = AccessToken.objects.create(
#                 user=user,
#                 application=self.get_application(grant_type),
#                 token=token_hex(16),
#                 expires=now() + timedelta(hours=1)
#             )
#         return self._tokens[token_cache_key]

#     @property
#     def api_client(self):
#         """An API client with data-hub:internal-front-end scope."""
#         return self.create_api_client()

#     def create_api_client(self, grant_type=Application.GRANT_PASSWORD, user=None):
#         """Creates an API client associated with an OAuth token with the specified scope."""
#         token = self.get_token(grant_type=grant_type, user=user)
#         client = APIClient()
#         client.credentials(Authorization=f'Bearer {token}')
#         return client

#     def get_application(self, grant_type=Application.GRANT_PASSWORD):
#         """Return a test application with the specified grant type."""
#         if not hasattr(self, '_applications'):
#             self._applications = {}

#         if grant_type not in self._applications:
#             self._applications[grant_type] = Application.objects.create(
#                 client_type=Application.CLIENT_CONFIDENTIAL,
#                 authorization_grant_type=grant_type,
#                 name=f'Test client ({grant_type})'
#             )
#         return self._applications[grant_type]


# class TestListReports(APITestMixin):
#     def test_companies_list_no_permissions(self):
#         """Should return 403"""
#         api_client = self.create_api_client()

#         url = reverse("list-reports")
#         response = api_client.get(url)
#         assert response.status_code == status.HTTP_200_OK
