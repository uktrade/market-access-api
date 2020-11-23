from django.conf import settings
from hawkrest import HawkAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from api.barriers.models import Barrier
from api.barriers.serializers import DataWorkspaceSerializer
from api.dataset.pagination import MarketAccessDatasetViewCursorPagination


class BarrierList(generics.ListAPIView):
    if settings.HAWK_ENABLED:
        authentication_classes = (HawkAuthentication,)
        permission_classes = (IsAuthenticated,)
    else:
        authentication_classes = ()
        permission_classes = ()

    pagination_class = MarketAccessDatasetViewCursorPagination

    queryset = Barrier.barriers.all().select_related(
        "assessment",
        "priority"
    ).prefetch_related(
        "barrier_commodities",
        "categories",
        "organisations",
        "tags",
    ).order_by('reported_on')

    serializer_class = DataWorkspaceSerializer
