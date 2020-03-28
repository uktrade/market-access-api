import datetime

from django.utils.http import urlencode
from factory.fuzzy import FuzzyChoice, FuzzyDate
from freezegun import freeze_time
from rest_framework import status
from rest_framework.reverse import reverse

from api.metadata.models import Category


def add_multiple_barriers(count, client):
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
            list_report_response = client.post(
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
                    "status_summary": "some status summary"
                },
            )

            assert list_report_response.status_code == status.HTTP_201_CREATED

            instance_id = list_report_response.data["id"]
            submit_url = reverse("submit-report", kwargs={"pk": instance_id})
            submit_response = client.put(
                submit_url, format="json", data={}
            )
            assert submit_response.status_code == status.HTTP_200_OK

            get_url = reverse("get-barrier", kwargs={"pk": instance_id})
            category = FuzzyChoice(Category.objects.all()).fuzz()
            edit_type_response = client.put(
                get_url,
                format="json",
                data={
                    "barrier_type": category.id,
                    "barrier_type_category": category.category,
                },
            )
            assert edit_type_response.status_code == status.HTTP_200_OK


class TestUtils:
    def add_report(self):
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

    def reverse_querystring(
        view, urlconf=None, args=None, kwargs=None, current_app=None, query_kwargs=None
    ):
        """Custom reverse to handle query strings.
        Usage:
            reverse('app.views.my_view', kwargs={'pk': 123}, query_kwargs={'search', 'Bob'})
        """
        base_url = reverse(
            view, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app
        )
        if query_kwargs:
            return "{}?{}".format(base_url, urlencode(query_kwargs))
        return base_url
