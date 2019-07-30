import datetime
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from django.utils.timezone import now

from freezegun import freeze_time
from factory.fuzzy import FuzzyChoice, FuzzyDate

from api.core.test_utils import APITestMixin, create_test_user
from api.barriers.models import BarrierInstance
from api.metadata.models import BarrierType
from api.metadata.constants import PROBLEM_STATUS_TYPES
from .test_utils import TestUtils


class TestListBarriers(APITestMixin):
    def test_no_reports(self):
        """Test there are no reports using list"""
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_no_reports_counts(self):
        """Test there are no reports using list"""
        url = reverse("barrier-count")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barriers"]["total"] == 0
        assert response.data["barriers"]["open"] == 0
        assert response.data["barriers"]["paused"] == 0
        assert response.data["barriers"]["resolved"] == 0
        assert response.data["reports"] == 0
        assert response.data["user"]["barriers"] == 0
        assert response.data["user"]["reports"] == 0

    def test_list_barriers_report_is_not_barrier(self):
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
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_report_is_not_barrier_counts(self):
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
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        url = reverse("barrier-count")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barriers"]["total"] == 0
        assert response.data["barriers"]["open"] == 0
        assert response.data["barriers"]["resolved"] == 0
        assert response.data["reports"] == 1
        assert response.data["user"]["barriers"] == 0
        assert response.data["user"]["reports"] == 1

    def test_list_barriers_get_one_barrier(self):
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

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_barrier_with_user_empty_username(self):
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
                "status_summary": "some status summary",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["reported_by"] == "Testo"

    def test_barrier_with_user_email_as_username(self):
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
                "status_summary": "some status summary",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["reported_by"] == "Testo"

    def test_barrier_with_user_normal_username(self):
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
                "status_summary": "some status summary",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["reported_by"] == "Test.User"

    def test_barrier_with_user_normal_username_and_email(self):
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
                "status_summary": "some status summary",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["reported_by"] == "Test.User"

    def test_list_barriers_get_archived_barrier(self):
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

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        sample_user = create_test_user()
        instance.archive(user=sample_user)
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_get_one_barrier_counts(self):
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

        url = reverse("barrier-count")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["barriers"]["total"] == 1
        assert response.data["barriers"]["open"] == 0
        assert response.data["barriers"]["resolved"] == 1
        assert response.data["reports"] == 0
        assert response.data["user"]["barriers"] == 1
        assert response.data["user"]["reports"] == 0

    def test_list_barriers_get_multiple_barriers(self):
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

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 1,
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

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def add_multiple_barriers(self, count):
        sectors = [
            "af959812-6095-e211-a939-e4115bead28a",
            "75debee7-a182-410e-bde0-3098e4f7b822",
            "9538cecc-5f95-e211-a939-e4115bead28a",
        ]
        countries = [
            "a05f66a0-5d95-e211-a939-e4115bead28a",
            "a75f66a0-5d95-e211-a939-e4115bead28a",
            "ad5f66a0-5d95-e211-a939-e4115bead28a",
        ]
        for _ in range(count):
            date = FuzzyDate(
                start_date=datetime.date.today() - datetime.timedelta(days=45),
                end_date=datetime.date.today(),
            ).evaluate(2, None, False)
            with freeze_time(date):
                list_report_url = reverse("list-reports")
                list_report_response = self.api_client.post(
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
                        "barrier_title": "Some test title",
                        "problem_description": "Some test problem_description",
                        "status_summary": "some status summary",
                        "eu_exit_related": 1,
                    },
                )

                assert list_report_response.status_code == status.HTTP_201_CREATED

                instance_id = list_report_response.data["id"]
                submit_url = reverse("submit-report", kwargs={"pk": instance_id})
                submit_response = self.api_client.put(
                    submit_url, format="json", data={}
                )
                assert submit_response.status_code == status.HTTP_200_OK

                get_url = reverse("get-barrier", kwargs={"pk": instance_id})
                barrier_type = FuzzyChoice(BarrierType.objects.all()).fuzz()
                edit_type_response = self.api_client.put(
                    get_url,
                    format="json",
                    data={
                        "barrier_type": barrier_type.id,
                        "barrier_type_category": barrier_type.category,
                    },
                )
                assert edit_type_response.status_code == status.HTTP_200_OK

    def test_list_barriers_get_multiple_barriers_country_filter(self):
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"location": "a05f66a0-5d95-e211-a939-e4115bead28a"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(
            export_country="a05f66a0-5d95-e211-a939-e4115bead28a"
        )
        assert response.data["count"] == barriers.count()

    def test_list_barriers_get_multiple_barriers_country_filter_all(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "resolved_status": 4,
                "export_country": "a05f66a0-5d95-e211-a939-e4115bead28a",
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

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 1,
                "is_resolved": False,
                "export_country": "a05f66a0-5d95-e211-a939-e4115bead28a",
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

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"location": "a05f66a0-5d95-e211-a939-e4115bead28a"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_barriers_get_multiple_barriers_country_filter_no_results(self):
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

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 1,
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

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"location": "a05f66a0-5d95-e211-a939-e4115bead28a"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_status_2_filter(self):
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring("list-barriers", query_kwargs={"status": 2})

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status=2)
        assert status_response.data["count"] == barriers.count()

    def test_list_barriers_status_4_filter(self):
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring("list-barriers", query_kwargs={"status": 4})

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status=4)
        assert 0 < status_response.data["count"] < count
        assert status_response.data["count"] == barriers.count()

    def test_list_barriers_status_2_4_filter(self):
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers", query_kwargs={"status": "2,4"}
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status__in=[2, 4])
        assert status_response.data["count"] == barriers.count()

    def test_list_barriers_barrier_type_filter(self):
        count = 10
        barrier_type = FuzzyChoice(BarrierType.objects.all()).fuzz()
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers", query_kwargs={"barrier_type": barrier_type.id}
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(barrier_type=barrier_type.id)
        assert status_response.data["count"] == barriers.count()

    def test_list_barriers_sector_filter(self):
        count = 10
        sector_id = "af959812-6095-e211-a939-e4115bead28a"
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers", query_kwargs={"sector": sector_id}
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(sectors__contains=[sector_id])
        assert status_response.data["count"] == barriers.count()

    def test_list_barriers_start_date_filter(self):
        count = 10
        date = FuzzyDate(
            start_date=datetime.date.today() - datetime.timedelta(days=45),
            end_date=datetime.date.today(),
        ).evaluate(2, None, False)
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"reported_on_after": date.strftime("%Y-%m-%d")},
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status_date__gte=date)
        assert status_response.data["count"] == barriers.count()

    def test_list_barriers_end_date_filter(self):
        count = 10
        date = FuzzyDate(
            start_date=datetime.date.today() - datetime.timedelta(days=45),
            end_date=datetime.date.today(),
        ).evaluate(2, None, False)
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"reported_on_before": date.strftime("%Y-%m-%d")},
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status_date__lte=date)
        assert status_response.data["count"] == barriers.count()

    def test_list_barriers_date_range_filter(self):
        count = 10
        start_date = FuzzyDate(
            start_date=datetime.date.today() - datetime.timedelta(days=45),
            end_date=datetime.date.today(),
        ).evaluate(2, None, False)
        end_date = start_date - datetime.timedelta(days=10)
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={
                "reported_on_after": start_date.strftime("%Y-%m-%d"),
                "reported_on_before": end_date.strftime("%Y-%m-%d"),
            },
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(
            status_date__range=[start_date, end_date]
        )
        assert status_response.data["count"] == barriers.count()

    @pytest.mark.parametrize("order_by", [
        "reported_on", "-reported_on",
        "modified_on", "-modified_on",
        "status", "-status",
        "priority", "-priority",
        "export_country", "-export_country"
    ])
    def test_list_barriers_order_by(self, order_by):
        count = 10
        sector_id = "af959812-6095-e211-a939-e4115bead28a"
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers", query_kwargs={"ordering": order_by}
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.all().order_by(order_by)
        assert status_response.data["count"] == barriers.count()
        response_list = [b["id"] for b in status_response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert response_list == db_list

    @pytest.mark.parametrize("order_by", [
        "reported_on", "-reported_on",
        "modified_on", "-modified_on",
        "status", "-status",
        "priority", "-priority",
        "export_country", "-export_country"
    ])
    def test_list_barriers_country_filter_order_by(self, order_by):
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={
                "location": "a05f66a0-5d95-e211-a939-e4115bead28a",
                "ordering": order_by,
            },
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(
            export_country="a05f66a0-5d95-e211-a939-e4115bead28a"
        ).order_by(order_by)
        assert response.data["count"] == barriers.count()
        response_list = [b["id"] for b in response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert response_list == db_list

    @pytest.mark.parametrize("order_by", [
        "reported_on", "-reported_on",
        "modified_on", "-modified_on",
        "status", "-status",
        "priority", "-priority",
        "export_country", "-export_country"
    ])
    def test_list_barriers_status_filter_order_by_reported_on(self, order_by):
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers", query_kwargs={"status": 2, "ordering": order_by}
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status=2).order_by(order_by)
        assert status_response.data["count"] == barriers.count()
        response_list = [b["id"] for b in status_response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert response_list == db_list

    @pytest.mark.parametrize("order_by", [
        "reported_on", "-reported_on",
        "modified_on", "-modified_on",
        "status", "-status",
        "priority", "-priority",
        "export_country", "-export_country"
    ])
    def test_list_barriers_barrier_type_filter_order_by_reported_on(self, order_by):
        count = 10
        barrier_type = FuzzyChoice(BarrierType.objects.all()).fuzz()
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"barrier_type": barrier_type.id, "ordering": order_by},
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(
            barrier_type=barrier_type.id
        ).order_by(order_by)
        assert status_response.data["count"] == barriers.count()
        response_list = [b["id"] for b in status_response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert response_list == db_list

    @pytest.mark.parametrize("order_by", [
        "reported_on", "-reported_on",
        "modified_on", "-modified_on",
        "status", "-status",
        "priority", "-priority",
        "export_country", "-export_country"
    ])
    def test_list_barriers_sector_filter_order_by_reported_on(self, order_by):
        count = 10
        sector_id = "af959812-6095-e211-a939-e4115bead28a"
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers", query_kwargs={"sector": sector_id, "ordering": order_by}
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(
            sectors__contains=[sector_id]
        ).order_by(order_by)
        assert status_response.data["count"] == barriers.count()
        response_list = [b["id"] for b in status_response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert response_list == db_list

    @pytest.mark.parametrize("order_by", [
        "reported_on", "-reported_on",
        "modified_on", "-modified_on",
        "status", "-status",
        "priority", "-priority",
        "export_country", "-export_country"
    ])
    def _test_list_barriers_start_date_filter_order_by_reported_on(self, order_by):
        count = 10
        date = FuzzyDate(
            start_date=datetime.date.today() - datetime.timedelta(days=45),
            end_date=datetime.date.today(),
        ).evaluate(2, None, False)
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={
                "reported_on_after": date.strftime("%Y-%m-%d"),
                "ordering": order_by,
            },
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status_date__gte=date).order_by(
            order_by
        )
        assert status_response.data["count"] == barriers.count()
        response_list = [b["id"] for b in status_response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert response_list == db_list

    @pytest.mark.parametrize("order_by", [
        "reported_on", "-reported_on",
        "modified_on", "-modified_on",
        "status", "-status",
        "priority", "-priority",
        "export_country", "-export_country"
    ])
    def _test_list_barriers_end_date_filter_order_by_reported_on(self, order_by):
        count = 10
        date = FuzzyDate(
            start_date=datetime.date.today() - datetime.timedelta(days=45),
            end_date=datetime.date.today(),
        ).evaluate(2, None, False)
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={
                "reported_on_before": date.strftime("%Y-%m-%d"),
                "ordering": order_by,
            },
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status_date__lte=date).order_by(
            order_by
        )
        assert status_response.data["count"] == barriers.count()
        response_list = [b["id"] for b in status_response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert response_list == db_list

    @pytest.mark.parametrize("order_by", [
        "reported_on", "-reported_on",
        "modified_on", "-modified_on",
        "status", "-status",
        "priority", "-priority",
        "export_country", "-export_country"
    ])
    def _test_list_barriers_date_range_filter_order_by_reported_on(self, order_by):
        count = 10
        start_date = FuzzyDate(
            start_date=datetime.date.today() - datetime.timedelta(days=45),
            end_date=datetime.date.today(),
        ).evaluate(2, None, False)
        end_date = start_date - datetime.timedelta(days=10)
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={
                "reported_on_after": start_date.strftime("%Y-%m-%d"),
                "reported_on_before": end_date.strftime("%Y-%m-%d"),
                "ordering": order_by,
            },
        )

        status_response = self.api_client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(
            status_date__range=[start_date, end_date]
        ).order_by(order_by)
        assert status_response.data["count"] == barriers.count()
        response_list = [b["id"] for b in status_response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert response_list == db_list

    def test_check_all_fields_after_report_submit_1(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": False,
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 1,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["id"] is not None
        assert barrier["code"] is not None
        assert barrier["reported_on"] is not None
        assert barrier["reported_by"] is not None
        assert barrier["problem_status"] == 2
        assert barrier["is_resolved"] == False
        assert barrier["resolved_date"] is None
        assert barrier["barrier_title"] == "Some title"
        assert barrier["sectors_affected"] == False
        assert barrier["sectors"] is None
        assert barrier["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        assert barrier["status"]["id"] == 7
        assert barrier["status"]["date"] is not None
        assert barrier["status"]["summary"] is None
        assert barrier["priority"]["code"] == "UNKNOWN"
        assert len(barrier["barrier_types"]) == 0
        assert barrier["created_on"] is not None
        assert barrier["eu_exit_related"] == 1

    def test_check_all_fields_after_report_submit_2(self):
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
                "sectors_affected": False,
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "status_summary": "some status summary",
                "eu_exit_related": 2,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["id"] is not None
        assert barrier["code"] is not None
        assert barrier["reported_on"] is not None
        assert barrier["reported_by"] is not None
        assert barrier["problem_status"] == 2
        assert barrier["is_resolved"] == True
        assert barrier["resolved_date"] is not None
        assert barrier["barrier_title"] == "Some title"
        assert barrier["sectors_affected"] == False
        assert barrier["sectors"] is None
        assert barrier["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        assert barrier["status"]["id"] == 4
        assert barrier["status"]["date"] is not None
        assert barrier["status"]["summary"] is not None
        assert barrier["priority"]["code"] == "UNKNOWN"
        assert len(barrier["barrier_types"]) == 0
        assert barrier["created_on"] is not None
        assert barrier["eu_exit_related"] == 2

    def test_check_all_fields_after_report_submit_3(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
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
                "eu_exit_related": 3,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        assert response.data["count"] == 1
        barrier = response.data["results"][0]
        assert barrier["id"] is not None
        assert barrier["code"] is not None
        assert barrier["reported_on"] is not None
        assert barrier["reported_by"] is not None
        assert barrier["problem_status"] == 2
        assert barrier["is_resolved"] == False
        assert barrier["barrier_title"] == "Some title"
        assert barrier["sectors_affected"] == True
        assert barrier["sectors"] == [
            "af959812-6095-e211-a939-e4115bead28a",
            "9538cecc-5f95-e211-a939-e4115bead28a",
        ]
        assert barrier["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        assert barrier["status"]["id"] == 7
        assert barrier["status"]["date"] is not None
        assert barrier["status"]["summary"] is None
        assert barrier["priority"]["code"] == "UNKNOWN"
        assert len(barrier["barrier_types"]) == 0
        assert barrier["created_on"] is not None
        assert barrier["eu_exit_related"] == 3

    def test_list_barriers_get_multiple_barriers_overseas_region_filter_1(self):
        """
        Test all barriers in Europe
        """
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"location": "3e6809d6-89f6-4590-8458-1d0dab73ad1a"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def test_list_barriers_get_multiple_barriers_overseas_region_filter_2(self):
        """
        Test all except one in Europe
        """
        count = 10
        self.add_multiple_barriers(count)

        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "ab5f66a0-5d95-e211-a939-e4115bead28a",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 3,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"location": "3e6809d6-89f6-4590-8458-1d0dab73ad1a"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def test_list_barriers_get_multiple_barriers_overseas_region_filter_3(self):
        """
        Test all in South Asia
        """
        count = 10
        self.add_multiple_barriers(count)

        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "ab5f66a0-5d95-e211-a939-e4115bead28a",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 3,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"location": "12ed13cf-4b2c-4a46-b2f9-068e397d8c84"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_barriers_get_barriers_multiple_overseas_region_filter(self):
        """
        Test all in Europe and South Asia
        """
        count = 10
        self.add_multiple_barriers(count)

        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "ab5f66a0-5d95-e211-a939-e4115bead28a",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 3,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={
                "location": "3e6809d6-89f6-4590-8458-1d0dab73ad1a,12ed13cf-4b2c-4a46-b2f9-068e397d8c84"
            },
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11

    def test_list_barriers_get_barriers_multiple_overseas_region_filter_2(self):
        """
        Test all in Europe and South Asia, except one
        """
        count = 10
        self.add_multiple_barriers(count)

        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "ab5f66a0-5d95-e211-a939-e4115bead28a",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 3,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": False,
                "export_country": "0809e385-9e9f-4a55-b121-e85cf865ca99",
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                    "9538cecc-5f95-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "eu_exit_related": 3,
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 12

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={
                "location": "3e6809d6-89f6-4590-8458-1d0dab73ad1a,12ed13cf-4b2c-4a46-b2f9-068e397d8c84"
            },
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11

    def test_list_barriers_text_filter_based_on_title(self):
        """
        Test all barriers in Europe
        """
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "Some"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def _test_list_barriers_text_filter_based_on_title_no_fuzzy_1(self):
        """
        Test all barriers in Europe
        """
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "testing"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_text_filter_based_on_title_no_fuzzy_2(self):
        """
        Test all barriers in Europe
        """
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "test2"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_text_filter_based_on_title_case_insensitive(self):
        """
        Test all barriers in Europe
        """
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "SOME"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def test_list_barriers_text_filter_based_on_summary(self):
        """
        Test all barriers in Europe
        """
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "problem_description"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def _test_list_barriers_text_filter_based_on_summary_no_fuzzy(self):
        """
        Test all barriers in Europe
        """
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "testing"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_text_filter_based_on_summary_case_insensitive(self):
        """
        Test all barriers in Europe
        """
        count = 10
        self.add_multiple_barriers(count)
        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "Problem_Description"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10
