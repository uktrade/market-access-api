from datetime import datetime

from pytz import UTC
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.core.test_utils import APITestMixin, create_test_user
from api.barriers.models import BarrierInstance
from tests.barriers.factories import ReportFactory


class TestListReports(APITestMixin, APITestCase):

    def setUp(self):
        self.url = reverse("list-reports")

    def test_create_report(self):
        assert not BarrierInstance.objects.count()
        payload = {"problem_status": 1}
        response = self.api_client.post(self.url, format="json", data=payload)
        assert status.HTTP_201_CREATED == response.status_code

    def test_list_reports__no_results(self):
        assert not BarrierInstance.objects.filter(draft=True)
        response = self.api_client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["count"]

    def test_list_reports_are_ordered_by_created_on(self):
        user = create_test_user(sso_user_id=self.sso_creator["user_id"])
        r1 = ReportFactory(
            created_on=datetime(2020, 1, 1, tzinfo=UTC),
            created_by=user
        )
        r2 = ReportFactory(
            created_on=datetime(2020, 2, 2, tzinfo=UTC),
            created_by=user
        )
        r3 = ReportFactory(
            created_on=datetime(2020, 3, 3, tzinfo=UTC),
            created_by=user
        )

        order_by = "created_on"
        url = f'{reverse("list-reports")}?order_by={order_by}'
        client = self.create_api_client(user=user)
        response = client.get(url)

        assert status.HTTP_200_OK == response.status_code
        reports = BarrierInstance.reports.all().order_by(order_by)
        assert reports.count() == response.data["count"]
        report_ids = [b["id"] for b in response.data["results"]]
        db_report_ids = [str(b.id) for b in reports]
        assert db_report_ids == report_ids

    def test_list_reports__cannot_see_others_reports(self):
        """
        Users are only allowed to see their own draft barriers.
        """
        creator = create_test_user(sso_user_id=self.sso_creator["user_id"])
        ReportFactory(
            created_on=datetime(2020, 1, 1, tzinfo=UTC),
            created_by=creator
        )
        user1 = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        assert 1 == BarrierInstance.objects.count()

        url = f'{reverse("list-reports")}'
        client = self.create_api_client(user=user1)
        response = client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["count"]

    def test_list_reports__can_only_see_own_reports(self):
        """
        List reports should only return reports that were created by the requesting user.
        """
        user = create_test_user(
            first_name="", last_name="", email="billy@wibble.com", username=""
        )
        report = ReportFactory(created_by=user)
        client = self.create_api_client(user=user)

        _another_user = create_test_user()
        _another_report = ReportFactory(created_by=_another_user)

        assert 2 == BarrierInstance.objects.count()

        response = client.get(self.url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(report.id) == response.data["results"][0]["id"]

    def test_cannot_see_archived_reports(self):
        user = create_test_user(
            first_name="", last_name="", email="billy@wibble.com", username=""
        )
        report = ReportFactory(created_by=user)
        client = self.create_api_client(user=user)

        response = client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]

        report.archive(user=user, reason="it wobbles!")
        response = client.get(self.url)
        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["count"]

    def test_post_invalid_problem_status_gives_400(self):
        response = self.api_client.post(
            self.url, format="json", data={"problem_status": 3}
        )
        assert status.HTTP_400_BAD_REQUEST == response.status_code

    def test_post_invalid_status_gives_400(self):
        response = self.api_client.post(
            self.url, format="json", data={"status": 33}
        )
        assert status.HTTP_400_BAD_REQUEST == response.status_code

    def test_post_export_country_name_gives_400(self):
        response = self.api_client.post(
            self.url, format="json", data={"country": "China"}
        )
        assert status.HTTP_400_BAD_REQUEST == response.status_code

    def test_post_sectors_affected_alone_gives_400(self):
        response = self.api_client.post(
            self.url, format="json", data={"sectors_affected": 3}
        )
        assert status.HTTP_400_BAD_REQUEST == response.status_code

    def test_post_sectors_alone_gives_400(self):
        response = self.api_client.post(
            self.url, format="json", data={"sectors": "Aerospace"}
        )
        assert status.HTTP_400_BAD_REQUEST == response.status_code

    def test_post_source_alone_gives_400(self):
        response = self.api_client.post(
            self.url, format="json", data={"source": 1}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_invalid_source_gives_400(self):
        response = self.api_client.post(
            self.url, format="json", data={"source": "ANYTHING"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
