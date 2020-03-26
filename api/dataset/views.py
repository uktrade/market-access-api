from django.conf import settings
from hawkrest import HawkAuthentication
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from api.barriers.models import BarrierInstance
from api.dataset.pagination import MarketAccessDatasetViewCursorPagination
from api.dataset.serializers import BarrierDataSetSerializer


class BarrierListDataWorkspaceView(generics.ListAPIView):
    """
    Return a list of all the BarrierInstances
    for Dataset to be consumed by Data-flow periodically
    """

    if settings.HAWK_ENABLED:
        authentication_classes = (HawkAuthentication,)
        permission_classes = (IsAuthenticated,)
    else:
        authentication_classes = ()
        permission_classes = ()
    pagination_class = MarketAccessDatasetViewCursorPagination

    queryset = BarrierInstance.barriers.all().select_related('priority').order_by('reported_on')
    serializer_class = BarrierDataSetSerializer
