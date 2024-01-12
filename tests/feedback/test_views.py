from django.urls import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)
from rest_framework.test import APITestCase

from api.core.test_utils import APITestMixin, create_test_user
from api.feedback.models import Feedback
from api.metadata.constants import (
    FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS,
    FEEDBACK_FORM_EXPERIENCED_ISSUES_ANSWERS,
    FEEDBACK_FORM_SATISFACTION_ANSWERS,
)


class FeedbackTestCase(APITestMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.user1 = create_test_user(sso_user_id=self.sso_user_data_1["user_id"])
        self.api_client1 = self.create_api_client(user=self.user1)

    def test_empty_feedback_fails_validation(self):
        url = reverse("feedback:add")
        data = {}
        response = self.api_client.post(url, data=data)
        assert response.status_code == HTTP_400_BAD_REQUEST
        assert "attempted_actions" in response.data
        assert "satisfaction" in response.data
        assert "feedback_text" not in response.data

    def test_valid_feedback_is_saved(self):
        url = reverse("feedback:add")
        attempted_actions = [
            FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS.REPORT_BARRIER,
        ]
        satisfaction = FEEDBACK_FORM_SATISFACTION_ANSWERS.VERY_SATISFIED
        feedback_text = "test please delete"
        experienced_issues = [
            FEEDBACK_FORM_EXPERIENCED_ISSUES_ANSWERS.NO_ISSUE,
        ]
        other_detail = "test other details"
        data = {
            "attempted_actions": attempted_actions,
            "satisfaction": satisfaction,
            "feedback_text": feedback_text,
            "experienced_issues": experienced_issues,
            "other_detail": other_detail,
        }
        response = self.api_client.post(url, data=data)
        assert response.status_code == HTTP_201_CREATED
        assert "attempted_actions" in response.data
        assert response.data["attempted_actions"] == attempted_actions
        assert "satisfaction" in response.data
        assert response.data["satisfaction"] == satisfaction
        assert "feedback_text" in response.data
        assert response.data["feedback_text"] == feedback_text
        assert "experienced_issues" in response.data
        assert response.data["experienced_issues"] == experienced_issues
        assert "other_detail" in response.data
        assert response.data["other_detail"] == other_detail
        assert "id" in response.data
        instance = Feedback.objects.get(id=response.data["id"])
        assert instance.attempted_actions == attempted_actions
        assert instance.satisfaction == satisfaction
        assert instance.feedback_text == feedback_text
        assert instance.experienced_issues == experienced_issues
        assert instance.other_detail == other_detail

    def test_multiple_actions_are_saved(self):
        url = reverse("feedback:add")
        attempted_actions = [
            FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS.REPORT_BARRIER,
            FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS.EXPORT_BARRIER_CSV,
            FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS.ACTION_PLAN,
        ]
        experienced_issues = [
            FEEDBACK_FORM_EXPERIENCED_ISSUES_ANSWERS.UNABLE_TO_FIND,
            FEEDBACK_FORM_EXPERIENCED_ISSUES_ANSWERS.DIFFICULT_TO_NAVIGATE,
        ]
        satisfaction = FEEDBACK_FORM_SATISFACTION_ANSWERS.NEITHER
        feedback_text = "test please delete"
        data = {
            "attempted_actions": attempted_actions,
            "satisfaction": satisfaction,
            "feedback_text": feedback_text,
            "experienced_issues": experienced_issues,
        }
        response = self.api_client.post(url, data=data)
        assert response.status_code == HTTP_201_CREATED
        assert "id" in response.data
        instance = Feedback.objects.get(id=response.data["id"])
        assert instance.attempted_actions == attempted_actions

    def test_csat_and_update(self):
        url = reverse("feedback:add")

        attempted_actions = [
            FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS.REPORT_BARRIER,
        ]
        satisfaction = FEEDBACK_FORM_SATISFACTION_ANSWERS.VERY_SATISFIED
        feedback_text = "test please delete"
        experienced_issues = [
            FEEDBACK_FORM_EXPERIENCED_ISSUES_ANSWERS.NO_ISSUE,
        ]
        other_detail = "test other details"
        data = {
            "attempted_actions": attempted_actions,
            "satisfaction": satisfaction,
            "experienced_issues": experienced_issues,
        }
        response = self.api_client.post(url, data=data)
        assert response.status_code == HTTP_201_CREATED
        assert "id" in response.data
        instance = Feedback.objects.get(id=response.data["id"])
        assert instance.attempted_actions == attempted_actions
        data = {
            "attempted_actions": attempted_actions,
            "satisfaction": satisfaction,
            "feedback_text": feedback_text,
            "experienced_issues": experienced_issues,
            "other_detail": other_detail,
        }
        url_update = reverse("feedback:update", kwargs={"pk": instance.id})
        response = self.api_client.patch(url_update, data=data)
        assert response.status_code == HTTP_200_OK
        # Get the original instance and check that it has been updated
        instance_updated = Feedback.objects.get(id=instance.id)
        assert instance_updated.other_detail == other_detail
        # test that another user can't update the original instance
        url_update = reverse("feedback:update", kwargs={"pk": instance.id})
        response = self.api_client1.patch(url_update, data=data)
        assert response.status_code == HTTP_403_FORBIDDEN
