from django.db.models import F
from rest_framework import viewsets

from api.feature_flags.models import FlagStatus
from api.feature_flags.serializers import FlagSerializer


class UserFeatureFlagView(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    serializer_class = FlagSerializer

    def get_queryset(self):
        return self.request.user.flags.filter(flag__status=FlagStatus.ACTIVE).values(name=F("flag__name"))
