from rest_framework import serializers

from api.feedback.models import Feedback
from api.metadata.constants import FEEDBACK_FORM_SATISFACTION_ANSWERS


class FeedbackSerializer(serializers.ModelSerializer):
    satisfaction = serializers.ChoiceField(
        choices=FEEDBACK_FORM_SATISFACTION_ANSWERS,
        required=True,
        error_messages={
            "required": "You must express a level of satisfaction",
        },
    )
    attempted_actions = serializers.ListField(
        child=serializers.CharField(max_length=30),
        required=True,
        error_messages={
            "required": 'You must specify what you were trying to do, or select "Don\'t Know"'
        },
    )
    experienced_issues = serializers.ListField(
        child=serializers.CharField(max_length=30),
        required=True,
        error_messages={
            "required": 'Select the type of issue you experienced, or select "I did not experience any issues"'
        },
    )
    other_detail = serializers.CharField(required=False, allow_blank=True)
    feedback_text = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Feedback
        fields = (
            "id",
            "created_on",
            "satisfaction",
            "attempted_actions",
            "experienced_issues",
            "other_detail",
            "feedback_text",
        )
        read_only_fields = ("id",)
