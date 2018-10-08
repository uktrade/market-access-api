from rest_framework.reverse import reverse
from django.utils.http import urlencode

from api.barriers.models import BarrierInstance


class TestUtils():
    def add_report(self):
        list_report_url = reverse("list-reports")
        list_report_response = self.api_client.post(list_report_url, format="json", data={
            "problem_status": 2,
            "is_resolved": True,
            "resolved_date": "2018-09-10",
            "export_country": "66b795e0-ad71-4a65-9fa6-9f1e97e86d67",
            "sectors_affected": True,
            "sectors": [
                "af959812-6095-e211-a939-e4115bead28a",
                "9538cecc-5f95-e211-a939-e4115bead28a"
            ],
            "product": "Some product",
            "source": "OTHER",
            "other_source": "Other source",
            "barrier_title": "Some title",
            "problem_description": "Some problem_description",
        })

        assert list_report_response.status_code == status.HTTP_201_CREATED

    def reverse_querystring(view, urlconf=None, args=None, kwargs=None, current_app=None, query_kwargs=None):
        '''Custom reverse to handle query strings.
        Usage:
            reverse('app.views.my_view', kwargs={'pk': 123}, query_kwargs={'search', 'Bob'})
        '''
        base_url = reverse(view, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app)
        if query_kwargs:
            return '{}?{}'.format(base_url, urlencode(query_kwargs))
        return base_url
