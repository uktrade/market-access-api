import freezegun
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.barriers.models import Barrier
from api.core.test_utils import APITestMixin, create_test_user
from api.interactions.models import Interaction
from tests.barriers.factories import MinReportFactory, ReportFactory

freezegun.configure(extend_ignore_list=["transformers"])


class TestSubmitReport(APITestMixin, APITestCase):
    def test_reported_as_resolved_in_full(self):
        resolved_in_full = 4
        report = ReportFactory(
            status=resolved_in_full, status_date="2020-02-02", status_summary="wibble"
        )
        report.submit_report()

        barrier = Barrier.objects.get(id=report.id)
        assert resolved_in_full == barrier.status

    def test_submit_report_creates_default_members(self):
        """
        When a user submits the report the user should be added as reporter and owner as well.
        The members are reverse ordered by their role in the response.
        """
        reporter = "Reporter"
        owner = "Owner"
        user = create_test_user(
            first_name="Marty",
            last_name="Bloggs",
            email="marty@wibble.com",
            username="marty.bloggs",
        )
        api_client = self.create_api_client(user=user)
        report = ReportFactory(created_by=user)
        members_url = reverse("list-members", kwargs={"pk": report.id})
        submit_url = reverse("submit-report", kwargs={"pk": report.id})

        response = api_client.get(members_url)
        assert status.HTTP_200_OK == response.status_code
        assert 0 == response.data["count"]

        response = api_client.put(submit_url)
        assert status.HTTP_200_OK == response.status_code

        response = api_client.get(members_url)
        assert status.HTTP_200_OK == response.status_code
        assert 2 == response.data["count"]
        # Assert Reporter
        member = response.data["results"][0]
        assert user.email == member["user"]["email"]
        assert user.first_name == member["user"]["first_name"]
        assert user.last_name == member["user"]["last_name"]
        assert reporter == member["role"]
        # Assert Owner
        member = response.data["results"][1]
        assert user.email == member["user"]["email"]
        assert user.first_name == member["user"]["first_name"]
        assert user.last_name == member["user"]["last_name"]
        assert owner == member["role"]

    @freezegun.freeze_time("2020-02-22")
    def test_submit_report_as_half_baked_user(self):
        user1 = create_test_user(
            first_name="", last_name="", email="billy@wibble.com", username=""
        )
        user2 = create_test_user(
            first_name="", last_name="", email="", username="WENDY@wobble.com"
        )
        user3 = create_test_user(
            first_name="", last_name="", email="", username="marty.bloggs"
        )
        user4 = create_test_user(
            first_name="", last_name="", email="Joe@wibble.com", username="joe.bloggs"
        )

        test_parameters = [
            {"user": user1, "expected_modified_user": "Billy"},
            {"user": user2, "expected_modified_user": "Wendy"},
            {"user": user3, "expected_modified_user": "Marty Bloggs"},
            {"user": user4, "expected_modified_user": "Joe Bloggs"},
        ]

        for tp in test_parameters:
            with self.subTest(tp=tp):
                report = ReportFactory()
                url = reverse("submit-report", kwargs={"pk": report.id})

                self.client.force_authenticate(user=tp["user"])
                submit_response = self.client.put(url, format="json", data={})

                assert submit_response.status_code == status.HTTP_200_OK
                report.refresh_from_db()
                assert not report.draft
                assert tp["user"] == report.modified_by
                assert tp["user"].id == report.modified_by_id
                assert "2020-02-22" == report.modified_on.strftime("%Y-%m-%d")
                assert tp["expected_modified_user"] == report.modified_user

    def test_submit_report_creates_an_interaction(self):
        report = ReportFactory()

        assert not Interaction.objects.filter(barrier=report)

        submit_url = reverse("submit-report", kwargs={"pk": report.id})
        response = self.api_client.put(submit_url)
        assert status.HTTP_200_OK == response.status_code

        assert 1 == Interaction.objects.filter(barrier=report).count()

    def test_no_interaction_is_created_when_submit_report_fails(self):
        report = ReportFactory(trade_direction=None)

        assert not Interaction.objects.filter(barrier=report)

        submit_url = reverse("submit-report", kwargs={"pk": report.id})
        response = self.api_client.put(submit_url)
        assert status.HTTP_400_BAD_REQUEST == response.status_code

        assert not Interaction.objects.filter(barrier=report)

    @freezegun.freeze_time("2020-02-02")
    def test_check_all_fields_after_report_submit_1(self):
        report = MinReportFactory(
            **{
                "term": 2,
                "status": 2,
                "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                "trade_direction": 1,
                "sectors_affected": False,
                "product": "Some product",
                "source": "GOVT",
                "title": "Some title",
                "summary": "Some summary",
            }
        )
        report.submit_report()

        url = reverse("get-barrier", kwargs={"pk": report.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"]
        assert response.data["code"]
        assert 2 == response.data["term"]["id"]
        assert "2020-02-02" == response.data["status_date"]
        assert "Some title" == response.data["title"]
        assert response.data["sectors_affected"] is False
        assert [] == response.data["sectors"]
        assert "82756b9a-5d95-e211-a939-e4115bead28a" == response.data["country"]["id"]
        assert response.data["status"]["id"] == 2
        assert response.data["status_date"]
        assert not response.data["status_summary"]
        assert response.data["created_on"]

    def test_check_all_fields_after_report_submit_2(self):
        report = MinReportFactory(
            **{
                "term": 2,
                "status_date": "2020-02-02",
                "status": 2,
                "status_summary": "some status summary",
                "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                "trade_direction": 2,
                "sectors_affected": True,
                "sectors": [
                    "af959812-6095-e211-a939-e4115bead28a",
                ],
                "product": "Some product",
                "source": "GOVT",
                "title": "Some title",
                "summary": "Some summary",
            }
        )
        report.submit_report()

        url = reverse("get-barrier", kwargs={"pk": report.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"]
        assert response.data["code"]
        assert 2 == response.data["term"]["id"]
        assert "2020-02-02" == response.data["status_date"]
        assert "Some title" == response.data["title"]
        assert response.data["sectors_affected"] is True
        assert ["af959812-6095-e211-a939-e4115bead28a"] == [
            sector["id"] for sector in response.data["sectors"]
        ]
        assert "82756b9a-5d95-e211-a939-e4115bead28a" == response.data["country"]["id"]
        assert response.data["status"]["id"] == 2
        assert response.data["status_date"]
        assert "some status summary" == response.data["status_summary"]
        assert response.data["created_on"]

    @freezegun.freeze_time("2020-02-02")
    def test_report_submit_for_eu_barrier(self):
        report = MinReportFactory(
            **{
                "term": 2,
                "status": 2,
                "country": None,
                "trading_bloc": "TB00016",
                "trade_direction": 1,
                "sectors_affected": False,
                "product": "Some product",
                "source": "GOVT",
                "title": "Some title",
                "summary": "Some summary",
            }
        )
        report.submit_report()

        url = reverse("get-barrier", kwargs={"pk": report.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"]
        assert "TB00016" == response.data["trading_bloc"]["code"]
        assert response.data["country"] is None

    @freezegun.freeze_time("2020-02-02")
    def test_report_submit_for_country_within_eu_barrier(self):
        report = MinReportFactory(
            **{
                "term": 2,
                "status": 2,
                "country": "82756b9a-5d95-e211-a939-e4115bead28a",
                "trading_bloc": "",
                "caused_by_trading_bloc": True,
                "trade_direction": 1,
                "sectors_affected": False,
                "product": "Some product",
                "source": "GOVT",
                "title": "Some title",
                "summary": "Some summary",
            }
        )
        report.submit_report()

        url = reverse("get-barrier", kwargs={"pk": report.id})
        response = self.api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"]
        assert response.data["trading_bloc"] is None
        assert response.data["country"]["id"] == "82756b9a-5d95-e211-a939-e4115bead28a"
        assert response.data["caused_by_trading_bloc"] is True
