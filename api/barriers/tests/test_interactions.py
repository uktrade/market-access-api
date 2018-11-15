from rest_framework import status
from rest_framework.reverse import reverse

from api.core.test_utils import APITestMixin, create_test_user
from api.barriers.models import BarrierInstance
from api.barriers.models import BarrierInteraction
from .test_utils import TestUtils


class TestListInteractions(APITestMixin):
    def test_no_interactions(self):
        """Test there are no barrier interactions using list"""
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        response = self.api_client.get(get_url)
        assert response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        response = self.api_client.get(interactions_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_add_interactions_no_pin(self):
        """Test there are no barrier interactions using list"""
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "sample interaction notes"
        })

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

    def test_add_interactions_pinned(self):
        """Test there are no barrier interactions using list"""
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "sample interaction notes",
            "pinned": True
        })

        assert add_int_response.status_code == status.HTTP_201_CREATED
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is True
        assert int_response.data["results"][0]["is_active"] is True

    def test_add_interactions_multiple(self):
        """Test there are no barrier interactions using list"""
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "first interaction notes"
        })
        assert add_int_response.status_code == status.HTTP_201_CREATED
        
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "second interaction notes"
        })
        assert add_int_response.status_code == status.HTTP_201_CREATED
        
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 2

    def test_add_interactions_multiple_mixed_pinning(self):
        """Test there are no barrier interactions using list"""
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "first interaction notes"
        })
        assert add_int_response.status_code == status.HTTP_201_CREATED
        
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "second interaction notes",
            "pinned": True
        })
        assert add_int_response.status_code == status.HTTP_201_CREATED
        
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 2

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "third interaction notes",
            "pinned": False
        })
        assert add_int_response.status_code == status.HTTP_201_CREATED
        
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 3

    def test_get_interaction(self):
        """Test retreiving an interaction """
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "sample interaction notes"
        })
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True

    def test_edit_interaction(self):
        """Test retreiving an interaction """
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "sample interaction notes"
        })
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True

        edit_int_response = self.api_client.put(get_interaction_url, format="json", data={
            "text": "edited interaction notes"
        })
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "edited interaction notes"

    def test_edit_interaction_pin_it(self):
        """Test retreiving an interaction """
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "sample interaction notes"
        })
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is False
        assert int_response.data["results"][0]["is_active"] is True

        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is False
        assert get_int_response.data["is_active"] is True

        edit_int_response = self.api_client.put(get_interaction_url, format="json", data={
            "pinned": True
        })
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["pinned"] is True

    def test_edit_interaction_unpin_it(self):
        """Test retreiving an interaction """
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
        instance = BarrierInstance.objects.first()
        assert list_report_response.data["id"] == str(instance.id)

        submit_url = reverse("submit-report", kwargs={"pk": instance.id})
        submit_response = self.api_client.put(submit_url, format="json", data={})
        assert submit_response.status_code == status.HTTP_200_OK

        get_url = reverse("get-barrier", kwargs={"pk": instance.id})
        get_response = self.api_client.get(get_url)
        assert get_response.status_code == status.HTTP_200_OK

        interactions_url = reverse("list-interactions", kwargs={"pk": instance.id})
        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 0

        add_int_response = self.api_client.post(interactions_url, format="json", data={
            "text": "sample interaction notes",
            "pinned": True
        })
        assert add_int_response.status_code == status.HTTP_201_CREATED

        int_response = self.api_client.get(interactions_url)
        assert int_response.status_code == status.HTTP_200_OK
        assert int_response.data["count"] == 1
        assert int_response.data["results"][0]["text"] == "sample interaction notes"
        assert int_response.data["results"][0]["kind"] == "Comment"
        assert int_response.data["results"][0]["pinned"] is True
        assert int_response.data["results"][0]["is_active"] is True

        int_id = int_response.data["results"][0]["id"]

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["kind"] == "Comment"
        assert get_int_response.data["pinned"] is True
        assert get_int_response.data["is_active"] is True

        edit_int_response = self.api_client.put(get_interaction_url, format="json", data={
            "pinned": False
        })
        assert edit_int_response.status_code == status.HTTP_200_OK

        get_interaction_url = reverse("get-interaction", kwargs={"pk": int_id})
        get_int_response = self.api_client.get(get_interaction_url)
        assert get_int_response.status_code == status.HTTP_200_OK
        assert get_int_response.data["text"] == "sample interaction notes"
        assert get_int_response.data["pinned"] is False
