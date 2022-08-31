from rest_framework import serializers

from .models import Feedback


class FeedbackSerializer(serializers.Serializer):
    class Meta:
        model = Feedback
        fields = (
            "id",
            "created_on",
            "satisfaction",
            "attempted_actions",
            "feedback_text",
        )
