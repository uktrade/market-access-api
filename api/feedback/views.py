from rest_framework.viewsets import ModelViewSet

from api.feedback.serializers import FeedbackSerializer


class AddFeedbackViewSet(ModelViewSet):
    serializer_class = FeedbackSerializer
    allowed_methods = ("post",)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
