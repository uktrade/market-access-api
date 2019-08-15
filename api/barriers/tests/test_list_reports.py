import datetime
import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from freezegun import freeze_time
from factory.fuzzy import FuzzyChoice, FuzzyDate

from api.core.test_utils import APITestMixin, create_test_user
from ..models import BarrierInstance
from .test_utils import TestUtils


class TestListReports(APITestMixin):
    def test_no_reports(self):
        """Test there are no reports using list"""
        url = reverse("list-reports")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_reports_get_one_report(self):
        a_user = create_test_user(
            first_name="", last_name="", email="Testo@Useri.com", username=""
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)

        response = self.api_client.post(
            list_report_url,
            format="json",
            data={"problem_status": 1}
        )
        assert response.status_code == status.HTTP_201_CREATED

        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_reports_archived_report(self):
        a_user = create_test_user(
            first_name="", last_name="", email="Testo@Useri.com", username=""
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)

        response = self.api_client.post(
            list_report_url,
            format="json",
            data={"problem_status": 1}
        )
        assert response.status_code == status.HTTP_201_CREATED

        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        sample_user = create_test_user()
        report = BarrierInstance.objects.first()
        report.archive(user=sample_user)
        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_reports_archived_with_reason_report(self):
        a_user = create_test_user(
            first_name="", last_name="", email="Testo@Useri.com", username=""
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)

        response = self.api_client.post(
            list_report_url,
            format="json",
            data={"problem_status": 1}
        )
        assert response.status_code == status.HTTP_201_CREATED

        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK

        assert response.data["count"] == 1
        sample_user = create_test_user()
        report = BarrierInstance.objects.first()
        report.archive(user=sample_user, reason="not a barrier")
        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_reports_get_multiple_reports(self):
        a_user = create_test_user(
            first_name="", last_name="", email="Testo@Useri.com", username=""
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)

        response = self.api_client.post(
            list_report_url,
            format="json",
            data={"problem_status": 1}
        )
        assert response.status_code == status.HTTP_201_CREATED

        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK

        response = self.api_client.post(
            list_report_url,
            format="json",
            data={"problem_status": 2}
        )
        assert response.status_code == status.HTTP_201_CREATED

        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_reports_post_problem_status_validation(self):
        url = reverse("list-reports")
        response = self.api_client.post(url, format="json", data={"problem_status": 3})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reports_post_stage_1_in_progress_1(self):
        url = reverse("list-reports")
        response = self.api_client.post(url, format="json", data={"problem_status": 1})

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 1
        assert detail_response.data["is_resolved"] is None
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_in_progress_2(self):
        url = reverse("list-reports")
        response = self.api_client.post(url, format="json", data={"problem_status": 2})

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is None
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_is_resolved_validation(self):
        url = reverse("list-reports")
        response = self.api_client.post(url, format="json", data={"is_resolved": 3})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reports_post_stage_1_in_progress_is_resolved_false(self):
        url = reverse("list-reports")
        response = self.api_client.post(url, format="json", data={"is_resolved": False})

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] is None
        assert detail_response.data["is_resolved"] is False
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_in_progress_is_resolved_true(self):
        url = reverse("list-reports")
        response = self.api_client.post(url, format="json", data={"is_resolved": True})

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] is None
        assert detail_response.data["is_resolved"] is True
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_in_progress_is_resolved_true_no_date(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url, format="json", data={"problem_status": 2, "is_resolved": True}
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is True
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_completed_1(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url, format="json", data={"problem_status": 2, "is_resolved": False}
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is False
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "COMPLETED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_completed_2(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is True
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "COMPLETED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_export_country_validation(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url, format="json", data={"export_country": "China"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reports_post_stage_2_completed(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={"export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] is None
        assert (
            detail_response.data["export_country"]
            == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        )
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "NOT STARTED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "COMPLETED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_in_progress_and_2_completed(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "problem_status": 2,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is None
        assert (
            detail_response.data["export_country"]
            == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        )
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "COMPLETED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_and_2_completed(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is False
        assert (
            detail_response.data["export_country"]
            == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        )
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "COMPLETED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "COMPLETED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_sectors_affected_validation(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url, format="json", data={"sectors_affected": 3}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reports_post_sectors_validation_1(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url, format="json", data={"sectors": "Aerospace"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reports_post_sectors_validation_2(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url, format="json", data={"sectors": ["Aerospace"]}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reports_post_stage_3_in_progress(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url, format="json", data={"sectors_affected": True}
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] is None
        assert detail_response.data["sectors_affected"] is True
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "NOT STARTED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "COMPLETED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_2_completed_3_in_progress_1(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is False
        assert detail_response.data["sectors_affected"] is True
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "COMPLETED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "COMPLETED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "COMPLETED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_2_completed_3_in_progress_2(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is True
        assert detail_response.data["resolved_date"] == "2018-09-10"
        assert detail_response.data["resolved_status"] == 4
        assert detail_response.data["sectors_affected"] is True
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "COMPLETED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "COMPLETED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "COMPLETED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_in_progress_2_completed_3_in_progress_1(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "problem_status": 2,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["sectors_affected"] is True
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "COMPLETED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "COMPLETED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_in_progress_2_completed_3_in_progress_2(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is True
        assert detail_response.data["sectors_affected"] is True
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "COMPLETED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "COMPLETED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_3_completed_option_1(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url, format="json", data={"sectors_affected": False}
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] is None
        assert detail_response.data["sectors_affected"] is False
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "NOT STARTED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "COMPLETED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_3_completed_option_2(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] is None
        assert detail_response.data["sectors_affected"] is True
        assert detail_response.data["sectors"]
        assert detail_response.data["progress"]
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "NOT STARTED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "COMPLETED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"

    def test_list_reports_post_stage_1_in_progress_2_completed_3_completed_1(self):
        pass

    def test_list_reports_post_stage_1_in_progress_2_completed_3_completed_2(self):
        pass

    def test_list_reports_post_stage_1_2_completed_3_completed_1(self):
        pass

    def test_list_reports_post_stage_1_2_completed_3_completed_2(self):
        pass

    def test_list_reports_post_source_validation_1(self):
        url = reverse("list-reports")
        response = self.api_client.post(url, format="json", data={"source": 1})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reports_post_source_validation_2(self):
        url = reverse("list-reports")
        response = self.api_client.post(url, format="json", data={"source": "ANYTHING"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_reports_post_stage_4_in_progress_product(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url, format="json", data={"product": "Some product"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] is None
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] is None
        assert detail_response.data["problem_description"] is None
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "NOT STARTED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_stage_4_in_progress_source(self):
        url = reverse("list-reports")
        response = self.api_client.post(url, format="json", data={"source": "GOVT"})

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] is None
        assert detail_response.data["source"] == "GOVT"
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] is None
        assert detail_response.data["problem_description"] is None
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "NOT STARTED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_stage_4_in_progress_other_source(self):
        url = reverse("list-reports")
        response = self.api_client.post(url, format="json", data={"source": "OTHER"})

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] is None
        assert detail_response.data["source"] == "OTHER"
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] is None
        assert detail_response.data["problem_description"] is None
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "NOT STARTED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_stage_4_in_progress_barrier_title(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url, format="json", data={"barrier_title": "Some title"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] is None
        assert detail_response.data["source"] is None
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] is None
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "NOT STARTED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_stage_4_in_progress_problem_description(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "is_resolved": True,
                "problem_description": "Some problem_description",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] is None
        assert detail_response.data["source"] is None
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] is None
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "NOT STARTED"
        stage_5 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.5"
        ]
        assert stage_5[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_stage_4_not_completed(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "product": "Some product",
                "source": "OTHER",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] == "OTHER"
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "NOT STARTED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_stage_4_completed_1(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "is_resolved": False,
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Not sure",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] == "OTHER"
        assert detail_response.data["other_source"] == "Not sure"
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "COMPLETED"

    def test_list_reports_post_stage_4_completed_2(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Not sure",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "status_summary": "some status summary",
                "eu_exit_related": 1,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] == "OTHER"
        assert detail_response.data["other_source"] == "Not sure"
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "COMPLETED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "COMPLETED"

    def test_list_reports_post_stage_4_in_progress_eu_exit(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "is_resolved": True,
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] == "GOVT"
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "IN PROGRESS"
        stage_5 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.5"
        ]
        assert stage_5[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_stage_4_complete_eu_exit_yes(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "is_resolved": True,
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] == "GOVT"
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "COMPLETED"
        stage_5 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.5"
        ]
        assert stage_5[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_stage_4_complete_eu_exit_no(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "is_resolved": True,
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 2,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] == "GOVT"
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "COMPLETED"
        stage_5 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.5"
        ]
        assert stage_5[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_stage_4_complete_eu_exit_dont_know(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "is_resolved": True,
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 3,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] == "GOVT"
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "COMPLETED"
        stage_5 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.5"
        ]
        assert stage_5[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_stage_5_in_progress_status_summary(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "is_resolved": True,
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] == "GOVT"
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "IN PROGRESS"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "NOT STARTED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "NOT STARTED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "COMPLETED"
        stage_5 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.5"
        ]
        assert stage_5[0]["status_desc"] == "IN PROGRESS"

    def test_list_reports_post_all_stages_completed_1(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is False
        assert (
            detail_response.data["export_country"]
            == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        )
        assert detail_response.data["sectors_affected"] is True
        assert detail_response.data["sectors"] == [
            "af959812-6095-e211-a939-e4115bead28a",
            "9538cecc-5f95-e211-a939-e4115bead28a",
        ]
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] == "GOVT"
        assert detail_response.data["other_source"] is None
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "COMPLETED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "COMPLETED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "COMPLETED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "COMPLETED"

    def test_list_reports_post_all_stages_completed_2(self):
        url = reverse("list-reports")
        response = self.api_client.post(
            url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert response.data["id"] == str(instance.id)

        detail_url = reverse("get-report", kwargs={"pk": instance.id})
        detail_response = self.api_client.get(detail_url)
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["problem_status"] == 2
        assert detail_response.data["is_resolved"] is False
        assert (
            detail_response.data["export_country"]
            == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        )
        assert detail_response.data["sectors_affected"] is True
        assert detail_response.data["sectors"] == [
            "af959812-6095-e211-a939-e4115bead28a",
            "9538cecc-5f95-e211-a939-e4115bead28a",
        ]
        assert detail_response.data["product"] == "Some product"
        assert detail_response.data["source"] == "OTHER"
        assert detail_response.data["other_source"] == "Other source"
        assert detail_response.data["barrier_title"] == "Some title"
        assert detail_response.data["problem_description"] == "Some problem_description"
        stage_1 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.1"
        ]
        assert stage_1[0]["status_desc"] == "COMPLETED"
        stage_2 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.2"
        ]
        assert stage_2[0]["status_desc"] == "COMPLETED"
        stage_3 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.3"
        ]
        assert stage_3[0]["status_desc"] == "COMPLETED"
        stage_4 = [
            d for d in detail_response.data["progress"] if d["stage_code"] == "1.4"
        ]
        assert stage_4[0]["status_desc"] == "COMPLETED"

    def test_list_reports_get_one_barrier_with_sso_kind_user(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED

        response = self.api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["created_by"]["name"] == f"{self.user.first_name} {self.user.last_name}"

    def test_list_reports_get_one_barrier_with_user_empty_username(self):
        a_user = create_test_user(
            first_name="", last_name="", email="Testo@Useri.com", username=""
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED

        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["created_by"]["name"] == "Testo"

    def test_list_reports_get_one_barrier_with_user_email_as_username(self):
        a_user = create_test_user(
            first_name="", last_name="", email="", username="Testo@Useri.com"
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED

        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["created_by"]["name"] == "Testo"

    def test_list_reports_get_one_barrier_with_user_normal_username(self):
        a_user = create_test_user(
            first_name="", last_name="", email="", username="Test.User"
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED

        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["created_by"]["name"] == "Test User"

    def test_list_reports_get_one_barrier_with_user_normal_username_and_email(self):
        a_user = create_test_user(
            first_name="", last_name="", email="Testo@Useri.com", username="Test.User"
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)
        list_report_response = new_api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "OTHER",
                "other_source": "Other source",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED

        response = new_api_client.get(list_report_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["created_by"]["name"] == "Test User"

    def add_multiple_reports(self, count, api_client=None):
        if not api_client:
            api_client = self.api_client
        sectors = [
            "af959812-6095-e211-a939-e4115bead28a",
            "75debee7-a182-410e-bde0-3098e4f7b822",
            "9538cecc-5f95-e211-a939-e4115bead28a",
        ]
        countries = [
            "aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc",
            "985f66a0-5d95-e211-a939-e4115bead28a",
            "1f0be5c4-5d95-e211-a939-e4115bead28a",
        ]
        for _ in range(count):
            date = FuzzyDate(
                start_date=datetime.date.today() - datetime.timedelta(days=45),
                end_date=datetime.date.today(),
            ).evaluate(2, None, False)
            with freeze_time(date):
                list_report_url = reverse("list-reports")
                list_report_response = api_client.post(
                    list_report_url,
                    format="json",
                    data={
                        "problem_status": FuzzyChoice([1, 2]).fuzz(),
                        "is_resolved": FuzzyChoice([True, False]).fuzz(),
                        "resolved_date": date.strftime("%Y-%m-%d"),
                        "resolved_status": 4,
                        "export_country": FuzzyChoice(countries).fuzz(),
                        "sectors_affected": True,
                        "sectors": [FuzzyChoice(sectors).fuzz()],
                        "product": "Some product",
                        "source": "OTHER",
                        "other_source": "Other source",
                        "barrier_title": "Some title",
                        "problem_description": "Some problem_description",
                        "status_summary": "some status summary",
                        "eu_exit_related": 1,
                    },
                )

                assert list_report_response.status_code == status.HTTP_201_CREATED

    @pytest.mark.parametrize("order_by", ["created_on"])
    def test_list_reports_order_by_reported_on(self, order_by):
        a_user = create_test_user(
            first_name="", last_name="", email="Testo@Useri.com", username="Test.User"
        )
        list_report_url = reverse("list-reports")
        new_api_client = self.create_api_client(user=a_user)

        count = 10
        sector_id = "af959812-6095-e211-a939-e4115bead28a"
        self.add_multiple_reports(count, new_api_client)
        url = reverse("list-reports")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-reports", query_kwargs={"ordering": order_by}
        )

        status_response = new_api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        reports = BarrierInstance.reports.all().order_by(order_by)
        assert status_response.data["count"] == reports.count()
        response_list = [b["id"] for b in status_response.data["results"]]
        db_list = [str(b.id) for b in reports]
        assert response_list == db_list
