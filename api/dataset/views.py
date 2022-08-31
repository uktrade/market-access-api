from django.conf import settings
from hawkrest import HawkAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from api.barriers.models import Barrier
from api.barriers.serializers import DataWorkspaceSerializer
from api.dataset.pagination import MarketAccessDatasetViewCursorPagination
from api.feedback.models import Feedback
from api.feedback.serializers import FeedbackSerializer


class BarrierList(generics.ListAPIView):
    if settings.HAWK_ENABLED:
        authentication_classes = (HawkAuthentication,)
        permission_classes = (IsAuthenticated,)
    else:
        authentication_classes = ()
        permission_classes = ()

    pagination_class = MarketAccessDatasetViewCursorPagination

    queryset = (
        Barrier.barriers.all()
        .select_related(
            "priority",
        )
        .prefetch_related(
            "barrier_commodities",
            "categories",
            "economic_assessments",
            "organisations",
            "tags",
        )
        .order_by("reported_on")
    )

    serializer_class = DataWorkspaceSerializer


class FeedbackDataWorkspaceListView(generics.ListAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]
