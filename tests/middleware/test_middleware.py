from unittest.mock import Mock

from django.test import TestCase
from sentry_sdk import set_user
from sentry_sdk.hub import Hub

from api.core.middleware import SentryUserContextMiddleware


class TestUserSentryContextMiddleware(TestCase):

    """
    Test SentryUserContextMiddleware Middleware
    """

    def setUp(self):
        super().setUp()
        self.middleware = SentryUserContextMiddleware(Mock())
        self.request = Mock()
        set_user(None)

    def test_middleware_authenticated_user_sentry_context_added(self):
        assert Hub.current.scope._user is None
        mock_user = Mock()
        mock_user.id = 1
        self.mock_user = mock_user
        self.request.user = mock_user
        self.middleware(self.request)
        assert Hub.current.scope._user
        assert Hub.current.scope._user == {
            "id": str(mock_user.id),
        }

    def test_middleware_unauthenticated_user_sentry_context_added(self):
        self.request.user.is_authenticated = False
        assert Hub.current.scope._user is None
        self.middleware(self.request)
        assert Hub.current.scope._user is None
