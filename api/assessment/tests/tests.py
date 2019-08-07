from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin, create_test_user
from api.barriers.models import BarrierInstance
from api.interactions.models import Document
from api.assessment.models import Assessment
from api.barriers.tests.test_utils import TestUtils


class TestAssessment(APITestMixin):
    def _test_no_assessment(self):
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
                "status_summary": "some status summary",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK

        assessment_url = reverse("get-assessment", kwargs={"pk": instance.id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def _test_add_assessment_step_1(self):
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
                "status_summary": "some status summary",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        assessment_url = reverse("get-assessment", kwargs={"pk": instance.id})
        response = self.api_client.get(assessment_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        add_response = self.api_client.post(
            assessment_url, format="json", data={
                "impact": "MEDIUMHIGH",
                "explanation": "sample assessment notes"
            }
        )

        assert add_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(assessment_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["impact"] == "MEDIUMHIGH"
        assert int_response.data["explanation"] == "sample assessment notes"
        assert int_response.data["value_to_economy"] is None
