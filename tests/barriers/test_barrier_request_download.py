from unittest import mock
from rest_framework.test import APITestCase
from api.core.test_utils import APITestMixin

from tests.barriers.factories import BarrierFactory


class TestBarrierRequestDownload(APITestMixin, APITestCase):
    """Tests for the BarrierRequestDownloadApproval class."""

    def setUp(self):
        super().setUp()
        self.barrier = BarrierFactory()

    @mock.patch("api.barriers.models.settings.SEARCH_DOWNLOAD_APPROVAL_REQUEST_EMAILS")
    def test_request_download_approval(self, mock_email_list):
        """Test that the request download approval endpoint works."""

        mock_email_list.return_value = ["test@test.gov.uk"]

        with mock.patch(
            "api.barriers.models.NotificationsAPIClient"
        ) as mock_send_email_notification:
            mock_send_email_notification.return_value = mock.MagicMock()
            response = self.api_client.post(
                "/barriers/request-download-approval",
                data={"email": self.sso_creator["email"]},
            )
            assert response.status_code == 201
            assert mock_send_email_notification.called
