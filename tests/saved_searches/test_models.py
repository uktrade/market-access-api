from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from api.core.test_utils import APITestMixin, create_test_user
from api.metadata.models import BarrierPriority
from api.user.models import SavedSearch

from tests.barriers.factories import BarrierFactory, ReportFactory


class SavedSearchModelTestCase(APITestMixin, APITestCase):

    def test_barriers(self):
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")
        barrier3 = BarrierFactory(priority="HIGH")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )

        assert barrier1 not in saved_search.barriers
        assert barrier2 in saved_search.barriers
        assert barrier3 not in saved_search.barriers

    def test_new_barrier_ids_other_user(self):
        """
        Changes made by other users should be included in new_barrier_ids
        """
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")
        barrier3 = BarrierFactory(priority="HIGH")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )
        saved_search.mark_as_seen()

        assert saved_search.new_barrier_ids == []

        # Newly created barriers should be in the list
        barrier4 = BarrierFactory(priority="MEDIUM")
        barrier5 = BarrierFactory(priority="UNKNOWN")
        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert saved_search.new_barrier_ids == [barrier4.id]

        # Existing barriers should be in the list
        barrier1.priority = BarrierPriority.objects.get(code="MEDIUM")
        barrier1.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert barrier1.pk in saved_search.new_barrier_ids

    def test_new_barrier_ids_current_user(self):
        """
        Changes made by the current user should not be included in new_barrier_ids
        """
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")
        barrier3 = BarrierFactory(priority="HIGH")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )
        saved_search.mark_as_seen()

        assert saved_search.new_barrier_ids == []

        # Barriers created by current user should be ignored
        api_client = self.create_api_client(user=user)
        report = ReportFactory(priority="MEDIUM", created_by=user)
        submit_url = reverse("submit-report", kwargs={"pk": report.id})
        response = api_client.put(submit_url)
        assert status.HTTP_200_OK == response.status_code

        report.history.update(history_user=user)
        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert report.pk not in saved_search.new_barrier_ids
        assert saved_search.new_barrier_ids == []

        # Barriers changed by current user should be ignored
        barrier1.priority = BarrierPriority.objects.get(code="MEDIUM")
        barrier1.save()

        history_item = barrier1.history.latest("history_date")
        history_item.history_user = user
        history_item.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert barrier1.pk not in saved_search.new_barrier_ids
        assert saved_search.new_barrier_ids == []

    def test_updated_barrier_ids_other_user(self):
        """
        Changes made by the other users should be included in updated_barrier_ids
        """
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")
        barrier3 = BarrierFactory(priority="HIGH")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )
        saved_search.mark_as_seen()

        assert saved_search.updated_barrier_ids == []

        barrier1.summary = "New summary"
        barrier1.save()

        barrier2.summary = "New summary"
        barrier2.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert saved_search.updated_barrier_ids == [barrier2.id]

    def test_updated_barrier_ids_current_user(self):
        """
        Changes made by the current user should not be included in updated_barrier_ids
        """
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")
        barrier3 = BarrierFactory(priority="HIGH")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )
        saved_search.mark_as_seen()

        assert saved_search.updated_barrier_ids == []

        barrier2.summary = "New summary"
        barrier2.save()

        history_item = barrier2.history.latest("history_date")
        history_item.history_user = user
        history_item.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert barrier2.pk not in saved_search.updated_barrier_ids
        assert saved_search.updated_barrier_ids == []

    def test_new_barriers_since_notified_other_user(self):
        """
        Changes made by other users should be included in new_barriers_since_notified
        """
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")
        barrier3 = BarrierFactory(priority="HIGH")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )
        saved_search.mark_as_notified()

        assert saved_search.new_barriers_since_notified == []

        # Newly created barriers should be in the list
        barrier4 = BarrierFactory(priority="MEDIUM")
        barrier5 = BarrierFactory(priority="UNKNOWN")
        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert saved_search.new_barriers_since_notified == [barrier4]

        # Existing barriers should be in the list
        barrier1.priority = BarrierPriority.objects.get(code="MEDIUM")
        barrier1.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert barrier1 in saved_search.new_barriers_since_notified

    def test_new_barriers_since_notified_current_user(self):
        """
        Changes made by the current user should not be included in new_barriers_since_notified
        """
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")
        barrier3 = BarrierFactory(priority="HIGH")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )
        saved_search.mark_as_notified()

        assert saved_search.new_barriers_since_notified == []

        # Barriers created by current user should be ignored
        api_client = self.create_api_client(user=user)
        report = ReportFactory(priority="MEDIUM", created_by=user)
        submit_url = reverse("submit-report", kwargs={"pk": report.id})
        response = api_client.put(submit_url)
        assert status.HTTP_200_OK == response.status_code

        report.history.update(history_user=user)
        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert report not in saved_search.new_barriers_since_notified
        assert saved_search.new_barriers_since_notified == []

        # Barriers changed by current user should be ignored
        barrier1.priority = BarrierPriority.objects.get(code="MEDIUM")
        barrier1.save()

        history_item = barrier1.history.latest("history_date")
        history_item.history_user = user
        history_item.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert barrier1 not in saved_search.new_barriers_since_notified
        assert saved_search.new_barriers_since_notified == []

    def test_updated_barriers_since_notified_other_user(self):
        """
        Changes made by the other users should be included in updated_barriers_since_notified
        """
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")
        barrier3 = BarrierFactory(priority="HIGH")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )
        saved_search.mark_as_notified()

        assert saved_search.updated_barriers_since_notified == []

        barrier1.summary = "New summary"
        barrier1.save()

        barrier2.summary = "New summary"
        barrier2.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert saved_search.updated_barriers_since_notified == [barrier2]

    def test_updated_barriers_since_notified_current_user(self):
        """
        Changes made by the current user should not be included in updated_barriers_since_notified
        """
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")
        barrier3 = BarrierFactory(priority="HIGH")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )
        saved_search.mark_as_notified()

        assert saved_search.updated_barriers_since_notified == []

        barrier2.summary = "New summary"
        barrier2.save()

        history_item = barrier2.history.latest("history_date")
        history_item.history_user = user
        history_item.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert barrier2 not in saved_search.updated_barriers_since_notified
        assert saved_search.updated_barriers_since_notified == []

    def test_are_api_parameters_equal(self):
        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])
        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM", "LOW"], "search": "test"}
        )
        query_dict = {
            "search": "test",
            "priority": "LOW,MEDIUM",
            "archived": "0",
            "ordering": "-reported_on",
            "offset": "0",
            "limit": "100",
            "search_id": saved_search.id,
        }
        assert saved_search.are_api_parameters_equal(query_dict) is True
        query_dict["priority"] = "HIGH,LOW,MEDIUM"
        assert saved_search.are_api_parameters_equal(query_dict) is False

    def test_mark_as_notified(self):
        """
        Calling mark_as_notified should reset updated and new barriers
        """
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )
        saved_search.mark_as_notified()
        assert saved_search.new_barriers_since_notified == []
        assert saved_search.updated_barriers_since_notified == []

        barrier1.priority = BarrierPriority.objects.get(code="MEDIUM")
        barrier1.save()

        barrier2.summary = "New summary"
        barrier2.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert saved_search.new_barriers_since_notified == [barrier1]
        assert barrier1 in saved_search.updated_barriers_since_notified
        assert barrier2 in saved_search.updated_barriers_since_notified

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        saved_search.mark_as_notified()
        assert saved_search.new_barriers_since_notified == []
        assert saved_search.updated_barriers_since_notified == []

    def test_mark_as_seen(self):
        """
        Calling mark_as_seen should reset updated and new barrier ids
        """
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]}
        )
        saved_search.mark_as_seen()
        assert saved_search.new_barrier_ids == []
        assert saved_search.updated_barrier_ids == []

        barrier1.priority = BarrierPriority.objects.get(code="MEDIUM")
        barrier1.save()

        barrier2.summary = "New summary"
        barrier2.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert saved_search.new_barrier_ids == [barrier1.pk]
        assert barrier1.pk in saved_search.updated_barrier_ids
        assert barrier2.pk in saved_search.updated_barrier_ids

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        saved_search.mark_as_seen()
        assert saved_search.new_barrier_ids == []
        assert saved_search.updated_barrier_ids == []

    def test_get_api_parameters(self):
        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={
                "priority": ["MEDIUM", "LOW"],
                "search": "test",
                "country": ["5061b8be-5d95-e211-a939-e4115bead28a"],
                "region": ["5616ccf5-ab4a-4c2c-9624-13c69be3c46b"],
            }
        )
        assert saved_search.get_api_parameters() == {
            "priority": ["MEDIUM", "LOW"],
            "search": "test",
            "location": [
                "5061b8be-5d95-e211-a939-e4115bead28a",
                "5616ccf5-ab4a-4c2c-9624-13c69be3c46b",
            ],
            "archived": "0",
        }

    def test_should_notify(self):
        barrier1 = BarrierFactory(priority="LOW")
        barrier2 = BarrierFactory(priority="MEDIUM")

        user = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])

        saved_search = SavedSearch.objects.create(
            user=user,
            name="Medium",
            filters={"priority": ["MEDIUM"]},
        )
        saved_search.mark_as_notified()

        assert saved_search.should_notify() is False

        saved_search.notify_about_additions = True
        saved_search.save()
        assert saved_search.should_notify() is False

        # An addition to the saved search
        barrier1.priority = BarrierPriority.objects.get(code="MEDIUM")
        barrier1.save()

        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert saved_search.should_notify() is True

        saved_search.notify_about_additions = False
        saved_search.notify_about_updates = True
        saved_search.save()
        assert saved_search.should_notify() is True

        # An update to a barrier in search search
        barrier2.summary = "New summary"
        barrier2.save()
        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert saved_search.should_notify() is True

        saved_search.notify_about_additions = True
        saved_search.mark_as_notified()
        saved_search = SavedSearch.objects.get(pk=saved_search.pk)
        assert saved_search.should_notify() is False
