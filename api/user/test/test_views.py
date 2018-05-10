import factory
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin, create_test_user


class TestUserView(APITestMixin):
    """User view test case."""

    def _test_who_am_i_authenticated(self):
        """Who am I."""
        content_type = ContentType.objects.first()

        user_test = create_test_user()
        api_client = self.create_api_client(user=user_test)

        url = reverse('who_am_i')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data == {
            'name': user_test.name,
            'last_login': None,
            'first_name': user_test.first_name,
            'last_name': user_test.last_name,
            'email': user_test.email,
            'contact_email': user_test.contact_email,
        }
