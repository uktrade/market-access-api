import uuid
from datetime import datetime, timedelta
from secrets import token_hex
import factory

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test.client import Client
from django.utils.timezone import now
from oauth2_provider.models import AccessToken, Application
from rest_framework.fields import DateField, DateTimeField
from rest_framework.test import APIClient


def get_default_test_user():
    """Return the test user."""
    user_model = get_user_model()
    try:
        test_user = user_model.objects.get(email="Testo@Useri.com")
    except user_model.DoesNotExist:
        test_user = create_test_user(
            first_name="Testo",
            last_name="Useri",
            email="Testo@Useri.com",
            username="TestoUseri",
        )
    return test_user

def create_simple_user(
    **user_attrs
):
    user_defaults = {
        "first_name": factory.Faker("first_name").generate({}),
        "last_name": factory.Faker("last_name").generate({}),
        "email": factory.Faker("email").generate({}),
        "date_joined": now(),
        "username": factory.Faker("name").generate({}),
    }
    user_defaults.update(user_attrs)

    user_model = get_user_model()
    user = user_model(**user_defaults)
    user.save()

def create_test_user(
    permission_codenames=(),
    location=None,
    internal=False,
    user_profile=None,
    sso_user_id=None,
    **user_attrs
):
    """
    :returns: user
    :param permission_codenames: list of codename permissions to be
        applied to the user
    :param user_attrs: any user attribute
    """
    user_defaults = {
        "first_name": factory.Faker("first_name").generate({}),
        "last_name": factory.Faker("last_name").generate({}),
        "email": factory.Faker("email").generate({}),
        "date_joined": now(),
        "username": factory.Faker("name").generate({}),
    }
    user_defaults.update(user_attrs)

    user_model = get_user_model()
    user = user_model(**user_defaults)
    user.save()

    if location:
        user.profile.location = location
        user.profile.save()
        user.save()

    if internal:
        user.profile.internal = internal
        user.profile.save()
        user.save()

    if user_profile:
        user.profile.user_profile = user_profile
        user.profile.save()
        user.save()
    
    if sso_user_id is None:
        sso_user_id = uuid.uuid4()

    user.profile.sso_user_id = sso_user_id
    user.profile.save()
    user.save()

    permissions = Permission.objects.filter(codename__in=permission_codenames)
    user.user_permissions.set(permissions)

    return user


def get_admin_user(password=None):
    """Return the test admin user."""
    email = "powerfuluser@trade.dit"
    user_model = get_user_model()
    try:
        admin_user = user_model.objects.get(email=email)
    except user_model.DoesNotExist:
        admin_user = user_model.objects.create_superuser(email=email, password=password)
    return admin_user


class AdminTestMixin:
    """All the tests using the DB and accessing admin endpoints should use this class."""

    pytestmark = pytest.mark.django_db  # use db

    PASSWORD = "password"

    @property
    def user(self):
        """Returns admin user."""
        if not hasattr(self, "_user"):
            self._user = get_admin_user(self.PASSWORD)
        return self._user

    @property
    def client(self):
        """Returns an authenticated admin client."""
        return self.create_client()

    def create_client(self, user=None):
        """Creates a client with admin access."""
        if not user:
            user = self.user
        client = Client()
        assert client.login(username=user.email, password=self.PASSWORD)
        return client


class APITestMixin:
    """All the tests using the DB and accessing end points behind auth should use this class."""

    pytestmark = pytest.mark.django_db  # use db
    sso_creator = {
        "email": "barrier.creator@unittest.uk",
        "user_id": "87419484-c6c1-4ab7-b124-a7c0376622c7",
        "first_name": "Barrier",
        "last_name": "Creator",
        "related_emails": [
            "barrier.creator@mocktest.uk"
        ],
        "groups": [],
        "permitted_applications": [
            {
                "key": "app-one",
                "url": "http://undefined",
                "name": "App One"
            },
            {
                "key": "app-two",
                "url": "http://undefined",
                "name": "App Two"
            },
            {
                "key": "app-three",
                "url": "http://undefined",
                "name": "App Three"
            },
        ],
        "access_profiles": [
            "full-access"
        ]
    }
    sso_user_data_1 = {
        "email": "unit1.test1@unittest.uk",
        "user_id": "907a7a2c-b6cd-454f-3764-a4388ec2a42b",
        "first_name": "Unit1",
        "last_name": "Test1",
        "related_emails": [
            "unit1.test1@mocktest.uk"
        ],
        "groups": [],
        "permitted_applications": [
            {
                "key": "app-one",
                "url": "http://undefined",
                "name": "App One"
            },
            {
                "key": "app-two",
                "url": "http://undefined",
                "name": "App Two"
            },
            {
                "key": "app-three",
                "url": "http://undefined",
                "name": "App Three"
            },
        ],
        "access_profiles": [
            "full-access"
        ]
    }

    sso_user_data_2 = {
        "email": "unit2.test2@unittest.uk",
        "user_id": "e5e9394c-daed-498e-b9f3-69228b44fbfa",
        "first_name": "Unit2",
        "last_name": "Test2",
        "related_emails": [
            "unit2.test2@mocktest.uk"
        ],
        "groups": [],
        "permitted_applications": [
            {
                "key": "app-one",
                "url": "http://undefined",
                "name": "App One"
            },
            {
                "key": "app-two",
                "url": "http://undefined",
                "name": "App Two"
            },
            {
                "key": "app-three",
                "url": "http://undefined",
                "name": "App Three"
            },
        ],
        "access_profiles": [
            "full-access"
        ]
    }

    @property
    def user(self):
        """Return the user."""
        if not hasattr(self, "_user"):
            self._user = get_default_test_user()
        return self._user

    def get_token(self, grant_type=Application.GRANT_PASSWORD, user=None):
        """Get access token for user test."""
        if not hasattr(self, "_tokens"):
            self._tokens = {}

        if user is None and grant_type != Application.GRANT_CLIENT_CREDENTIALS:
            user = self.user

        token_cache_key = user.email if user else None
        if token_cache_key not in self._tokens:
            self._tokens[token_cache_key] = AccessToken.objects.create(
                user=user,
                application=self.get_application(grant_type),
                token=token_hex(16),
                expires=now() + timedelta(hours=1),
            )
        return self._tokens[token_cache_key]

    @property
    def api_client(self):
        """An API client with data-hub:internal-front-end scope."""
        return self.create_api_client()

    def create_api_client(self, grant_type=Application.GRANT_PASSWORD, user=None):
        """Creates an API client associated with an OAuth token with the specified scope."""
        token = self.get_token(grant_type=grant_type, user=user)
        client = APIClient()
        client.credentials(Authorization=f"Bearer {token}")
        return client

    def get_application(self, grant_type=Application.GRANT_PASSWORD):
        """Return a test application with the specified grant type."""
        if not hasattr(self, "_applications"):
            self._applications = {}

        if grant_type not in self._applications:
            self._applications[grant_type] = Application.objects.create(
                client_type=Application.CLIENT_CONFIDENTIAL,
                authorization_grant_type=grant_type,
                name=f"Test client ({grant_type})",
            )
        return self._applications[grant_type]


def synchronous_executor_submit(fn, *args, **kwargs):
    """Run everything submitted to thread pools executor in sync."""
    fn(*args, **kwargs)


def synchronous_transaction_on_commit(fn):
    """During a test run a transaction is never committed, so we have to improvise."""
    fn()


def format_date_or_datetime(value):
    """
    Formats a date or datetime using DRF fields.

    This is for use in tests when comparing dates and datetimes with JSON-formatted values.
    """
    if isinstance(value, datetime):
        return DateTimeField().to_representation(value)
    return DateField().to_representation(value)


def random_obj_for_model(model):
    """Returns a random object for a model."""
    return random_obj_for_queryset(model.objects.all())


def random_obj_for_queryset(queryset):
    """Returns a random object for a queryset."""
    return queryset.order_by("?").first()
