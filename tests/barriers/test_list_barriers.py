from datetime import datetime

from django.test import TestCase
from pytz import UTC
from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin, create_test_user
from api.barriers.models import BarrierInstance
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import CategoryFactory, BarrierPriorityFactory


class TestListBarriers(APITestMixin, TestCase):
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

    # TODO: refactor this
    def test_list_barriers_report_is_not_barrier(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status_date": "2018-09-10",
                "status": 4,
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

    # TODO: refactor this
    def test_list_barriers_report_is_not_barrier_counts(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status_date": "2018-09-10",
                "status": 4,
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

    # TODO: refactor this
    def test_list_barriers_get_one_barrier(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status_date": "2018-09-10",
                "status": 4,
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

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    # TODO: refactor this
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
                "status_date": "2018-09-10",
                "status": 4,
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

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    # TODO: refactor this
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
                "status_date": "2018-09-10",
                "status": 4,
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

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    # TODO: refactor this
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
                "status_date": "2018-09-10",
                "status": 4,
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

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    # TODO: refactor this
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
                "status_date": "2018-09-10",
                "status": 4,
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

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = new_api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = new_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    # TODO: refactor this
    def test_list_barriers_get_archived_barrier(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status_date": "2018-09-10",
                "status": 4,
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

    # TODO: refactor this
    def test_list_barriers_get_one_barrier_counts(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status_date": "2018-09-10",
                "status": 4,
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
        count = 2
        BarrierFactory.create_batch(count)

        url = reverse("list-barriers")
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert count == response.data["count"]

    def test_list_barriers_country_filter(self):
        country_id = "a05f66a0-5d95-e211-a939-e4115bead28a"
        BarrierFactory.create_batch(2, export_country=country_id)
        BarrierFactory()

        assert 3 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?location={country_id}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(export_country=country_id)
        assert barriers.count() == response.data["count"]

    def test_list_barriers_country_filter__multivalues(self):
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        germany = "83756b9a-5d95-e211-a939-e4115bead28a"
        spain_barrier = BarrierFactory(export_country=spain)
        germany_barrier = BarrierFactory(export_country=germany)
        BarrierFactory()

        assert 3 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?location={spain},{germany}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(spain_barrier.id), str(germany_barrier.id)} == set(barrier_ids)

    def test_list_barriers_country_filter__no_find(self):
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        germany = "83756b9a-5d95-e211-a939-e4115bead28a"
        BarrierFactory(export_country=spain)
        BarrierFactory()

        assert 2 == BarrierInstance.objects.count()
        assert 0 == BarrierInstance.objects.filter(export_country=germany).count()

        url = f'{reverse("list-barriers")}?location={germany}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 0 == response.data["count"]

    def test_list_barriers_status_filter(self):
        prob_status = 2
        BarrierFactory.create_batch(2, problem_status=1)
        BarrierFactory(problem_status=prob_status)

        assert 3 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?status={prob_status}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status=prob_status)
        assert response.data["count"] == barriers.count()

    def test_list_barriers_status_filter__multivalues(self):
        BarrierFactory(problem_status=1)
        BarrierFactory(problem_status=2)
        BarrierFactory(problem_status=4)

        assert 3 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?status=2,4'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status__in=[2, 4])
        assert response.data["count"] == barriers.count()

    def test_list_barriers_category_filter(self):
        BarrierFactory()
        cat1 = CategoryFactory()
        barrier = BarrierFactory()
        barrier.categories.add(cat1)

        assert 2 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?category={cat1.id}'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier.id) == response.data["results"][0]["id"]

    def test_list_barriers_sector_filter(self):
        sector1 = "75debee7-a182-410e-bde0-3098e4f7b822"
        sector2 = "af959812-6095-e211-a939-e4115bead28a"
        BarrierFactory(sectors=[sector1])
        barrier = BarrierFactory(sectors=[sector2])

        assert 2 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?sector={sector2}'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier.id) == response.data["results"][0]["id"]

    def test_list_barriers_order_by(self):
        test_parameters = [
            "reported_on", "-reported_on",
            "modified_on", "-modified_on",
            "status", "-status",
            "priority", "-priority",
            "export_country", "-export_country"
        ]
        priorities = BarrierPriorityFactory.create_batch(3)
        bahamas = "aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc"
        barrier1 = BarrierFactory(
            reported_on=datetime(2020, 1, 1, tzinfo=UTC),
            modified_on=datetime(2020, 1, 2, tzinfo=UTC),
            status=1,
            priority=priorities[0],
            export_country=bahamas
        )
        bhutan = "ab5f66a0-5d95-e211-a939-e4115bead28a"
        barrier2 = BarrierFactory(
            reported_on=datetime(2020, 2, 2, tzinfo=UTC),
            modified_on=datetime(2020, 2, 3, tzinfo=UTC),
            status=2,
            priority=priorities[1],
            export_country=bhutan
        )
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        barrier3 = BarrierFactory(
            reported_on=datetime(2020, 3, 3, tzinfo=UTC),
            modified_on=datetime(2020, 3, 4, tzinfo=UTC),
            status=7,
            priority=priorities[2],
            export_country=spain
        )

        assert 3 == BarrierInstance.objects.count()

        for order_by in test_parameters:
            with self.subTest(order_by=order_by):
                url = f'{reverse("list-barriers")}?ordering={order_by}'
                response = self.api_client.get(url)

                assert response.status_code == status.HTTP_200_OK
                barriers = BarrierInstance.objects.all().order_by(order_by)
                assert barriers.count() == response.data["count"]
                response_list = [b["id"] for b in response.data["results"]]
                db_list = [str(b.id) for b in barriers]
                assert db_list == response_list

    def test_check_all_fields_after_report_submit_1(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 2,
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
        assert barrier["problem_status"] == 2
        assert barrier["barrier_title"] == "Some title"
        assert barrier["sectors_affected"] == False
        assert barrier["sectors"] == []
        assert barrier["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        assert barrier["status"]["id"] == 2
        assert barrier["status"]["date"] is not None
        assert barrier["status"]["summary"] is None
        assert barrier["priority"]["code"] == "UNKNOWN"
        assert len(barrier["categories"]) == 0
        assert barrier["created_on"] is not None

    def test_check_all_fields_after_report_submit_2(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status_date": "2018-09-10",
                "status": 4,
                "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
                "sectors_affected": False,
                "product": "Some product",
                "source": "GOVT",
                "barrier_title": "Some title",
                "problem_description": "Some problem_description",
                "status_summary": "some status summary",
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
        assert barrier["problem_status"] == 2
        assert barrier["status_date"] is not None
        assert barrier["barrier_title"] == "Some title"
        assert barrier["sectors_affected"] == False
        assert barrier["sectors"] == []
        assert barrier["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        assert barrier["status"]["id"] == 4
        assert barrier["status"]["date"] is not None
        assert barrier["status"]["summary"] is not None
        assert barrier["priority"]["code"] == "UNKNOWN"
        assert len(barrier["categories"]) == 0
        assert barrier["created_on"] is not None

    def test_check_all_fields_after_report_submit_3(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 2,
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
        assert barrier["problem_status"] == 2
        assert barrier["barrier_title"] == "Some title"
        assert barrier["sectors_affected"] == True
        assert barrier["sectors"] == [
            "af959812-6095-e211-a939-e4115bead28a",
            "9538cecc-5f95-e211-a939-e4115bead28a",
        ]
        assert barrier["export_country"] == "66b795e0-ad71-4a65-9fa6-9f1e97e86d67"
        assert barrier["status"]["id"] == 2
        assert barrier["status"]["date"] is not None
        assert barrier["status"]["summary"] is None
        assert barrier["priority"]["code"] == "UNKNOWN"
        assert len(barrier["categories"]) == 0
        assert barrier["created_on"] is not None

    def test_list_barriers_filter_location_europe(self):
        """
        Filter by overseas region - Europe
        Note (as of 2020 Apr) - not all countries are made available for tests
        """
        europe = "3e6809d6-89f6-4590-8458-1d0dab73ad1a"

        bhutan = "ab5f66a0-5d95-e211-a939-e4115bead28a"
        BarrierFactory(export_country=bhutan)
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        spain_barrier = BarrierFactory(export_country=spain)
        bahamas = "aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc"
        BarrierFactory(export_country=bahamas)

        assert 3 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?location={europe}'
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(spain_barrier.id) == response.data["results"][0]["id"]

    def test_list_barriers_filter_location_multiple_regions(self):
        """
        Filter by overseas region - Europe & South Asia
        Note (as of 2020 Apr) - not all countries are made available for tests
        """
        europe = "3e6809d6-89f6-4590-8458-1d0dab73ad1a"
        south_asia = "12ed13cf-4b2c-4a46-b2f9-068e397d8c84"

        bhutan = "ab5f66a0-5d95-e211-a939-e4115bead28a"
        bhutan_barrier = BarrierFactory(export_country=bhutan)
        spain = "86756b9a-5d95-e211-a939-e4115bead28a"
        spain_barrier = BarrierFactory(export_country=spain)
        bahamas = "aaab9c75-bd2a-43b0-a78b-7b5aad03bdbc"
        BarrierFactory(export_country=bahamas)

        assert 3 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?location={europe},{south_asia}'
        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(bhutan_barrier.id), str(spain_barrier.id)} == set(barrier_ids)

    def test_list_barriers_text_filter_based_on_title(self):
        barrier1 = BarrierFactory(barrier_title="Wibble blockade")
        _barrier2 = BarrierFactory(barrier_title="Wobble blockade")
        barrier3 = BarrierFactory(barrier_title="Look wibble in the middle")

        assert 3 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?text=wibble'

        response = self.api_client.get(url)
        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(barrier1.id), str(barrier3.id)} == set(barrier_ids)

    def test_list_barriers_text_filter_based_on_problem_description(self):
        _barrier1 = BarrierFactory(problem_description="Wibble summary about the blockade.")
        barrier2 = BarrierFactory(problem_description="Wobble blockade")
        barrier3 = BarrierFactory(problem_description="Look ma, wibble-wobble in the middle.")

        assert 3 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?text=wobble'
        response = self.api_client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        barrier_ids = [b["id"] for b in response.data["results"]]
        assert {str(barrier2.id), str(barrier3.id)} == set(barrier_ids)

    def test_filter_barriers_my_barriers(self):
        BarrierFactory()
        _user1 = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])
        _barrier1 = BarrierFactory()
        user2 = create_test_user(sso_user_id=self.sso_creator["user_id"])
        barrier2 = BarrierFactory(created_by=user2)

        assert 3 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?user={user2.id}'
        client = self.create_api_client(user=user2)
        response = client.get(url)

        assert status.HTTP_200_OK == response.status_code
        assert 1 == response.data["count"]
        assert str(barrier2.id) == response.data["results"][0]["id"]
