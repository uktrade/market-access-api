from rest_framework.viewsets import ModelViewSet

from api.feedback.serializers import FeedbackSerializer
from .models import Feedback


class AddFeedbackViewSet(ModelViewSet):
    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.all()

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
