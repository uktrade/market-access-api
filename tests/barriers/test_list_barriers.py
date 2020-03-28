import datetime
import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from factory.fuzzy import FuzzyChoice, FuzzyDate

from api.core.test_utils import APITestMixin, create_test_user
from api.barriers.models import BarrierInstance
from api.metadata.models import Category
from tests.barriers.factories import BarrierFactory
from tests.metadata.factories import CategoryFactory

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

    def test_list_barriers__country_filter(self):
        country_id = "a05f66a0-5d95-e211-a939-e4115bead28a"
        BarrierFactory.create_batch(2)
        BarrierFactory(export_country=country_id)

        assert 3 == BarrierInstance.objects.count()

        url = f'{reverse("list-barriers")}?location={country_id}'
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(export_country=country_id)
        assert barriers.count() == response.data["count"]

    def test_list_barriers_get_multiple_barriers_country_filter_all(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status_date": "2018-09-10",
                "status": 4,
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
                "status": 2,
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

        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        list_report_response = self.api_client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 1,
                "status": 2,
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
            query_kwargs={"location": "a05f66a0-5d95-e211-a939-e4115bead28a"},
        )

        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

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

    def test_list_barriers_start_date_filter(self):
        client = self.api_client
        count = 3
        date = FuzzyDate(
            start_date=datetime.date.today() - datetime.timedelta(days=45),
            end_date=datetime.date.today(),
        ).evaluate(2, None, False)
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"reported_on_after": date.strftime("%Y-%m-%d")},
        )

        status_response = client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status_date__gte=date)
        assert status_response.data["count"] == barriers.count()

    def test_list_barriers_end_date_filter(self):
        client = self.api_client
        count = 3
        date = FuzzyDate(
            start_date=datetime.date.today() - datetime.timedelta(days=45),
            end_date=datetime.date.today(),
        ).evaluate(2, None, False)
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"reported_on_before": date.strftime("%Y-%m-%d")},
        )

        status_response = client.get(url)
        assert status_response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.filter(status_date__lte=date)
        assert status_response.data["count"] == barriers.count()

    def test_list_barriers_date_range_filter(self):
        client = self.api_client
        count = 3
        start_date = FuzzyDate(
            start_date=datetime.date.today() - datetime.timedelta(days=45),
            end_date=datetime.date.today(),
        ).evaluate(2, None, False)
        end_date = start_date - datetime.timedelta(days=10)
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={
                "reported_on_after": start_date.strftime("%Y-%m-%d"),
                "reported_on_before": end_date.strftime("%Y-%m-%d"),
            },
        )

        status_response = client.get(url)
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
        BarrierFactory.create_batch(3)

        assert 3 == BarrierInstance.objects.count()

        url = TestUtils.reverse_querystring(
            "list-barriers", query_kwargs={"ordering": order_by}
        )
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        barriers = BarrierInstance.objects.all().order_by(order_by)
        assert response.data["count"] == barriers.count()
        response_list = [b["id"] for b in response.data["results"]]
        db_list = [str(b.id) for b in barriers]
        assert response_list == db_list

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

    def test_list_barriers_get_multiple_barriers_overseas_region_filter_1(self):
        """
        Test all barriers in Europe
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"location": "3e6809d6-89f6-4590-8458-1d0dab73ad1a"},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def test_list_barriers_get_multiple_barriers_overseas_region_filter_2(self):
        """
        Test all except one in Europe
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)

        list_report_url = reverse("list-reports")
        list_report_response = client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 2,
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
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"location": "3e6809d6-89f6-4590-8458-1d0dab73ad1a"},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def test_list_barriers_get_multiple_barriers_overseas_region_filter_3(self):
        """
        Test all in South Asia
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)

        list_report_url = reverse("list-reports")
        list_report_response = client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 2,
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
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"location": "12ed13cf-4b2c-4a46-b2f9-068e397d8c84"},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_barriers_get_barriers_multiple_overseas_region_filter(self):
        """
        Test all in Europe and South Asia
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)

        list_report_url = reverse("list-reports")
        list_report_response = client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 2,
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
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={
                "location": "3e6809d6-89f6-4590-8458-1d0dab73ad1a,12ed13cf-4b2c-4a46-b2f9-068e397d8c84"
            },
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11

    def test_list_barriers_get_barriers_multiple_overseas_region_filter_2(self):
        """
        Test all in Europe and South Asia, except one
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)

        list_report_url = reverse("list-reports")
        list_report_response = client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 2,
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
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        list_report_response = client.post(
            list_report_url,
            format="json",
            data={
                "problem_status": 2,
                "status": 2,
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
            },
        )

        assert list_report_response.status_code == status.HTTP_201_CREATED
        instance_id = list_report_response.data["id"]
        submit_url = reverse("submit-report", kwargs={"pk": instance_id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 12

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={
                "location": "3e6809d6-89f6-4590-8458-1d0dab73ad1a,12ed13cf-4b2c-4a46-b2f9-068e397d8c84"
            },
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 11

    def test_list_barriers_text_filter_based_on_title(self):
        """
        Test all barriers in Europe
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "Some"},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def _test_list_barriers_text_filter_based_on_title_no_fuzzy_1(self):
        """
        Test all barriers in Europe
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "testing"},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_text_filter_based_on_title_no_fuzzy_2(self):
        """
        Test all barriers in Europe
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "test2"},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_text_filter_based_on_title_case_insensitive(self):
        """
        Test all barriers in Europe
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "SOME"},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def test_list_barriers_text_filter_based_on_summary(self):
        """
        Test all barriers in Europe
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "problem_description"},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def _test_list_barriers_text_filter_based_on_summary_no_fuzzy(self):
        """
        Test all barriers in Europe
        """
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "testing"},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_barriers_text_filter_based_on_summary_case_insensitive(self):
        client = self.api_client
        count = 3
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"text": "Problem_Description"},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def test_filter_barriers_my_barriers(self):
        creator_user = create_test_user(
            sso_user_id=self.sso_creator["user_id"]
        )
        client = self.create_api_client(creator_user)
        count = 3
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == count

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"user": creator_user.id},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

    def _test_filter_barriers_my_barriers_two_users(self):
        creator_user = create_test_user()
        client = self.create_api_client(creator_user)
        count = 5
        self.add_multiple_barriers(count, client)
        url = reverse("list-barriers")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5

        other_user = create_test_user()
        other_client = self.create_api_client(other_user)
        self.add_multiple_barriers(count, other_client)

        url = reverse("list-barriers")
        response = other_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 10

        url = TestUtils.reverse_querystring(
            "list-barriers",
            query_kwargs={"user": True},
        )

        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5
