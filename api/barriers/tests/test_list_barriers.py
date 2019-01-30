import datetime
from rest_framework import status
from rest_framework.reverse import reverse

from django.utils.timezone import now
from freezegun import freeze_time
from factory.fuzzy import FuzzyChoice

from api.core.test_utils import APITestMixin, create_test_user
from api.barriers.models import BarrierInstance
from api.metadata.models import BarrierType
from api.metadata.constants import (
    PROBLEM_STATUS_TYPES
)
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
                "status_summary": "some status summary"
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
                "status_summary": "some status summary"
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
                "status_summary": "some status summary"
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
                "status_summary": "some status summary"
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
                "status_summary": "some status summary"
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
                "status_summary": "some status summary"
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
                "status_summary": "some status summary"
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
                "status_summary": "some status summary"
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
                "status_summary": "some status summary"
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
                "status_summary": "some status summary"
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

    def add_multiple_barriers(self):
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
        dates = ["2018-08-14", "2018-08-21", "2018-09-01", "2018-09-17", "2018-10-12", "2018-10-26"]
        for date in dates:
            with freeze_time(date):
                list_report_url = reverse("list-reports")
                list_report_response = self.api_client.post(
                    list_report_url,
                    format="json",
                    data={
                        "problem_status": FuzzyChoice[PROBLEM_STATUS_TYPES],
                        "is_resolved": FuzzyChoice([True, False]),
                        "export_country": FuzzyChoice(countries),
                        "sectors_affected": True,
                        "sectors": [
                            FuzzyChoice(sectors)
                        ],
                        "product": "Some product",
                        "source": "OTHER",
                        "other_source": "Other source",
                        "barrier_title": "Some title",
                        "problem_description": "Some problem_description",
                    },
                )

                assert list_report_response.status_code == status.HTTP_201_CREATED

                instance_id = list_report_response.data["id"]
                submit_url = reverse("submit-report", kwargs={"pk": instance_id})
                submit_response = self.api_client.put(submit_url, format="json", data={})
                assert submit_response.status_code == status.HTTP_200_OK

                get_url = reverse("get-barrier", kwargs={"pk": instance_id})
                barrier_type = FuzzyChoice(BarrierType.objects.all())
                edit_type_response = self.api_client.put(
                    get_url,
                    format="json",
                    data={
                        "barrier_type":barrier_type.id,
                        "barrier_type_category":barrier_type.category
                    }
                )
                assert edit_type_response.status_code == status.HTTP_200_OK

        with freeze_time("2018-09-12"):
            list_report_url = reverse("list-reports")
            list_report_response = self.api_client.post(
                list_report_url,
                format="json",
                data={
                    "problem_status": 1,
                    "is_resolved": True,
                    "resolved_date": "2018-09-01",
                    "export_country": "985f66a0-5d95-e211-a939-e4115bead28a",
                    "sectors_affected": True,
                    "sectors": [
                        "75debee7-a182-410e-bde0-3098e4f7b822",
                    ],
                    "product": "Some product",
                    "source": "OTHER",
                    "other_source": "Other source",
                    "barrier_title": "Some title",
                    "problem_description": "Some problem_description",
                    "status_summary": "some status summary"
                },
            )

            assert list_report_response.status_code == status.HTTP_201_CREATED

            instance_id = list_report_response.data["id"]
            submit_url = reverse("submit-report", kwargs={"pk": instance_id})
            submit_response = self.api_client.put(submit_url, format="json", data={})
            assert submit_response.status_code == status.HTTP_200_OK

            get_url = reverse("get-barrier", kwargs={"pk": instance_id})
            barrier_type = BarrierType.objects.all()[:1].get()
            edit_type_response = self.api_client.put(
                get_url,
                format="json",
                data={
                    "barrier_type":barrier_type.id,
                    "barrier_type_category":barrier_type.category
                }
            )
            assert edit_type_response.status_code == status.HTTP_200_OK

        with freeze_time("2018-09-27"):
            list_report_url = reverse("list-reports")
            list_report_response = self.api_client.post(
                list_report_url,
                format="json",
                data={
                    "problem_status": 1,
                    "is_resolved": False,
                    "export_country": "aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc",
                    "sectors_affected": True,
                    "sectors": [
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

            instance_id = list_report_response.data["id"]
            submit_url = reverse("submit-report", kwargs={"pk": instance_id})
            submit_response = self.api_client.put(submit_url, format="json", data={})
            assert submit_response.status_code == status.HTTP_200_OK

            get_url = reverse("get-barrier", kwargs={"pk": instance_id})
            barrier_type = BarrierType.objects.all()[:1].get()
            edit_type_response = self.api_client.put(
                get_url,
                format="json",
                data={
                    "barrier_type":barrier_type.id,
                    "barrier_type_category":barrier_type.category
                }
            )
            assert edit_type_response.status_code == status.HTTP_200_OK

        with freeze_time("2018-10-11"):
            list_report_url = reverse("list-reports")
            list_report_response = self.api_client.post(
                list_report_url,
                format="json",
                data={
                    "problem_status": 1,
                    "is_resolved": False,
                    "export_country": "aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc",
                    "sectors_affected": True,
                    "sectors": [
                        "af959812-6095-e211-a939-e4115bead28a",
                    ],
                    "product": "Some product",
                    "source": "OTHER",
                    "other_source": "Other source",
                    "barrier_title": "Some title",
                    "problem_description": "Some problem_description",
                },
            )

            assert list_report_response.status_code == status.HTTP_201_CREATED

            instance_id = list_report_response.data["id"]
            submit_url = reverse("submit-report", kwargs={"pk": instance_id})
            submit_response = self.api_client.put(submit_url, format="json", data={})
            assert submit_response.status_code == status.HTTP_200_OK

            get_url = reverse("get-barrier", kwargs={"pk": instance_id})
            barrier_type = BarrierType.objects.all()[:1].get()
            edit_type_response = self.api_client.put(
                get_url,
                format="json",
                data={
                    "barrier_type":barrier_type.id,
                    "barrier_type_category":barrier_type.category
                }
            )
            assert edit_type_response.status_code == status.HTTP_200_OK

        with freeze_time("2018-12-04"):
            list_report_url = reverse("list-reports")
            list_report_response = self.api_client.post(
                list_report_url,
                format="json",
                data={
                    "problem_status": 1,
                    "is_resolved": False,
                    "export_country": "aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc",
                    "sectors_affected": True,
                    "sectors": [
                        "af959812-6095-e211-a939-e4115bead28a",
                    ],
                    "product": "Some product",
                    "source": "OTHER",
                    "other_source": "Other source",
                    "barrier_title": "Some title",
                    "problem_description": "Some problem_description",
                },
            )

            assert list_report_response.status_code == status.HTTP_201_CREATED

            instance_id = list_report_response.data["id"]
            submit_url = reverse("submit-report", kwargs={"pk": instance_id})
            submit_response = self.api_client.put(submit_url, format="json", data={})
            assert submit_response.status_code == status.HTTP_200_OK

            get_url = reverse("get-barrier", kwargs={"pk": instance_id})
            barrier_type = BarrierType.objects.all()[:1].get()
            edit_type_response = self.api_client.put(
                get_url,
                format="json",
                data={
                    "barrier_type":barrier_type.id,
                    "barrier_type_category":barrier_type.category
                }
            )
            assert edit_type_response.status_code == status.HTTP_200_OK

    def test_list_barriers_get_multiple_barriers_country_filter(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
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
                "status_summary": "some status summary"
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
                "export_country": "af959812-6095-e211-a939-e4115bead28a",
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
            query_kwargs={"export_country": "af959812-6095-e211-a939-e4115bead28a"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_barriers_get_multiple_barriers_country_filter_all(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "export_country": "af959812-6095-e211-a939-e4115bead28a",
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
                "status_summary": "some status summary"
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
                "export_country": "af959812-6095-e211-a939-e4115bead28a",
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
            query_kwargs={"export_country": "af959812-6095-e211-a939-e4115bead28a"},
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
                "status_summary": "some status summary"
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
            query_kwargs={"export_country": "af959812-6095-e211-a939-e4115bead28a"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_status_filter(self):
        pass

    def test_list_barriers_barrier_type_filter(self):
        pass

    def test_list_barriers_sector_filter(self):
        pass
    
    def test_list_barriers_date_range_filter(self):
        pass

    def test_list_barriers_order_by_reported_on(self):
        pass

    def test_list_barriers_country_filter_order_by_reported_on(self):
        pass

    def test_list_barriers_status_filter_order_by_reported_on(self):
        pass

    def test_list_barriers_barrier_type_filter_order_by_reported_on(self):
        pass

    def test_list_barriers_sector_filter_order_by_reported_on(self):
        pass
    
    def test_list_barriers_date_range_filter_order_by_reported_on(self):
        pass

    def test_list_barriers_order_by_reported_on_order_by_reported_on(self):
        pass

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
        assert barrier["current_status"]["status"] == 2
        assert barrier["current_status"]["status_date"] is not None
        assert barrier["current_status"]["status_summary"] is None
        assert barrier["priority"]["code"] == "UNKNOWN"
        assert barrier["barrier_type"] is None
        assert barrier["barrier_type_category"] is None
        assert barrier["created_on"] is not None

    def test_check_all_fields_after_report_submit_2(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "is_resolved": True,
                "resolved_date": "2018-09-10",
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": False,
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "status_summary": "some status summary"
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
        assert barrier["current_status"]["status"] == 4
        assert barrier["current_status"]["status_date"] is not None
        assert barrier["current_status"]["status_summary"] is not None
        assert barrier["priority"]["code"] == "UNKNOWN"
        assert barrier["barrier_type"] is None
        assert barrier["barrier_type_category"] is None
        assert barrier["created_on"] is not None

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
        assert barrier["sectors_affected"] == True
        assert barrier["sectors"] == [
            "af959812-6095-e211-a939-e4115bead28a",
            "9538cecc-5f95-e211-a939-e4115bead28a",
            ]
        assert barrier["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        assert barrier["current_status"]["status"] == 2
        assert barrier["current_status"]["status_date"] is not None
        assert barrier["current_status"]["status_summary"] is None
        assert barrier["priority"]["code"] == "UNKNOWN"
        assert barrier["barrier_type"] is None
        assert barrier["barrier_type_category"] is None
        assert barrier["created_on"] is not None
