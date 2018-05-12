from rest_framework import status
from rest_framework.reverse import reverse
from api.core.test_utils import APITestMixin, create_test_user


class TestUserView(APITestMixin):
    """User view test case."""

    def test_who_am_i_authenticated(self):
        """Who am I."""

        user_test = create_test_user()
        api_client = self.create_api_client(user=user_test)

        url = reverse('who_am_i')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data == {
            'username': user_test.username,
            'last_login': None,
            'first_name': user_test.first_name,
            'last_name': user_test.last_name,
            'email': user_test.email,
        }
