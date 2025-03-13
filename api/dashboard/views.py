import logging

from django.core.paginator import Paginator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response

from api.barriers.models import Barrier, BarrierFilterSet
from api.barriers.serializers import BarrierListSerializer
from api.dashboard import service

logger = logging.getLogger(__name__)


class BarrierDashboardSummary(generics.GenericAPIView):
    """
    View to return high level stats to the dashboard
    """

    serializer_class = BarrierListSerializer
    filterset_class = BarrierFilterSet

    filter_backends = (DjangoFilterBackend,)
    ordering_fields = (
        "reported_on",
        "modified_on",
        "estimated_resolution_date",
        "status",
        "priority",
        "country",
    )
    ordering = ("-reported_on",)

    def get(self, request):
        filtered_queryset = self.filter_queryset(
            Barrier.barriers.filter(archived=False)
        )

        counts = service.get_counts(qs=filtered_queryset, user=request.user)

        return Response(counts)


class UserTasksView(generics.ListAPIView):
    """
    Returns list of dashboard next steps, tasks and progress updates
    related to barriers where a given user is either owner or
    collaborator.
    """

    def get(self, request, *args, **kwargs):
        # Get the User information from the request
        task_list = service.get_tasks(request.user)

        # Paginate
        paginator = Paginator(task_list, 3)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        return Response(
            status=status.HTTP_200_OK,
            data={"results": page_obj.object_list, "count": len(task_list)},
        )
