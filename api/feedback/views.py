from feedback.models import Feedback
from feedback.serializers import FeedbackSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated


class FeedbackDataWorkspaceListView(generics.ListAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]
