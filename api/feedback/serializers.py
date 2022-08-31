from feedback.models import Feedback
from rest_framework import serializers


class FeedbackSerializer(serializers.Serializer):
    class Meta:
        model = Feedback
        fields = ("id", "created", "satisfaction", "attempted_actions", "feedback_text")
