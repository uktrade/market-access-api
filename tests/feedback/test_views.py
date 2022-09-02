from django.urls import reverse
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.test import APITestCase

from api.core.test_utils import APITestMixin
from api.feedback.models import Feedback
from api.metadata.constants import (
    FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS,
    FEEDBACK_FORM_SATISFACTION_ANSWERS,
)


class MyTestCase(APITestMixin, APITestCase):
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
        data = {
            "attempted_actions": attempted_actions,
            "satisfaction": satisfaction,
            "feedback_text": feedback_text,
        }
        response = self.api_client.post(url, data=data)
        assert response.status_code == HTTP_201_CREATED
        assert "attempted_actions" in response.data
        assert response.data["attempted_actions"] == attempted_actions
        assert "satisfaction" in response.data
        assert response.data["satisfaction"] == satisfaction
        assert "feedback_text" in response.data
        assert response.data["feedback_text"] == feedback_text
        assert "id" in response.data
        instance = Feedback.objects.get(id=response.data["id"])
        assert instance.attempted_actions == attempted_actions
        assert instance.satisfaction == satisfaction
        assert instance.feedback_text == feedback_text

    def test_multiple_actions_are_saved(self):
        url = reverse("feedback:add")
        attempted_actions = [
            FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS.REPORT_BARRIER,
            FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS.EXPORT_BARRIER_CSV,
            FEEDBACK_FORM_ATTEMPTED_ACTION_ANSWERS.ACTION_PLAN,
        ]
        satisfaction = FEEDBACK_FORM_SATISFACTION_ANSWERS.NEITHER
        feedback_text = "test please delete"
        data = {
            "attempted_actions": attempted_actions,
            "satisfaction": satisfaction,
            "feedback_text": feedback_text,
        }
        response = self.api_client.post(url, data=data)
        assert response.status_code == HTTP_201_CREATED
        assert "id" in response.data
        instance = Feedback.objects.get(id=response.data["id"])
        assert instance.attempted_actions == attempted_actions
