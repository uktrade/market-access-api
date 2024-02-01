import freezegun
from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import Barrier
from api.core.test_utils import APITestMixin, create_test_user
from tests.barriers.factories import ReportFactory

freezegun.config.configure(extend_ignore_list=["transformers"])


class TestReportDetail(APITestMixin):
    def test_report_gets_reference_code_generated(self):
        report = ReportFactory()
        assert report.code not in ("", None)

    @freezegun.freeze_time("2020-02-02")
    def test_delete_request_archives_report(self):
        creator = create_test_user(sso_user_id=self.sso_creator["user_id"])
        report = ReportFactory(created_by=creator)
        client = self.create_api_client(user=creator)
        url = reverse("get-report", kwargs={"pk": report.id})

        assert 1 == Barrier.objects.count()

        response = client.delete(url)

        assert status.HTTP_204_NO_CONTENT == response.status_code
        report.refresh_from_db()
        assert 1 == Barrier.objects.count()
        assert report.archive, "Expected True."
        assert creator == report.archived_by
        assert "2020-02-02" == report.archived_on.strftime("%Y-%m-%d")
        assert not report.archived_explanation
        assert not report.archived_reason

    def test_report_can_only_be_deleted_by_its_creator(self):
        creator = create_test_user(sso_user_id=self.sso_creator["user_id"])
        report = ReportFactory(created_by=creator)
        user1 = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])
        url = reverse("get-report", kwargs={"pk": report.id})
        client = self.create_api_client(user=user1)

        assert 1 == Barrier.objects.count()

        response = client.delete(url)

        assert status.HTTP_403_FORBIDDEN == response.status_code
        assert 1 == Barrier.objects.count()
