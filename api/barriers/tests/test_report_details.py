from rest_framework import status
from rest_framework.reverse import reverse

from api.barriers.models import BarrierInstance
from api.core.test_utils import APITestMixin, create_test_user


class TestReportDetail(APITestMixin):
    def test_report_flow_stage_1(self):
        BarrierInstance(problem_status=1).save()
        instance = BarrierInstance.objects.first()
        url = reverse("get-report", kwargs={"pk": instance.id})
        response = self.api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert not response.data["progress"]
