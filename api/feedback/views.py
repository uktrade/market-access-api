from rest_framework.viewsets import ModelViewSet

from api.core.permissions import IsCreatorOrReadOnly
from api.feedback.serializers import FeedbackSerializer

from .models import Feedback


class AddFeedbackViewSet(ModelViewSet):
    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.all()
    permission_classes = [IsCreatorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
