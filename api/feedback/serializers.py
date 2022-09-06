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
    feedback_text = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Feedback
        fields = (
            "id",
            "satisfaction",
            "attempted_actions",
            "feedback_text",
        )
        read_only_fields = ("id",)
