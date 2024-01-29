from django.db.models import Count
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.response import Response

from api.barrier_reports.models import BarrierReport
from api.barrier_reports.serializers import BarrierReportSerializer
from api.barrier_reports.service import create_barrier_report
from api.barriers.models import Barrier, BarrierFilterSet
from api.barriers.serializers import BarrierCsvExportSerializer


class BarrierReportsView(generics.ListCreateAPIView):
    queryset = Barrier.barriers.annotate(team_count=Count("barrier_team")).all()
    serializer_class = BarrierCsvExportSerializer
    filterset_class = BarrierFilterSet
    filter_backends = (DjangoFilterBackend,)

    def post(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).values_list("id")
        barrier_ids = list(map(str, queryset.values_list("id", flat=True)))

        barrier_report = create_barrier_report(user=request.user, barrier_ids=barrier_ids)

        return JsonResponse({"success": True, "barrier_report_id": barrier_report.id})

    def list(self, request, *args, **kwargs):
        return Response(
            BarrierReportSerializer(
                BarrierReport.objects.filter(user=request.user).values(
                    'id', 'name', 'status', 'created_on', 'modified_on', 'user'
                ),
                many=True
            ).data
        )


class BarrierReportDetailView(generics.RetrieveAPIView):
    lookup_field = "pk"
    serializer_class = BarrierReportSerializer
    queryset = BarrierReport.objects.all()

    def check_object_permissions(self, request, obj):
        if obj.user != request.user:
            self.permission_denied(
                request, message="Unauthorized"
            )
