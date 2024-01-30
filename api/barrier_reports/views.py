from django.db.models import Count
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response

from api.barrier_reports.models import BarrierReport
from api.barrier_reports.serializers import (
    BarrierCsvExportSerializer,
    BarrierReportPresignedUrlSerializer,
    BarrierReportSerializer,
)
from api.barrier_reports.service import create_barrier_report, get_presigned_url
from api.barriers.models import Barrier, BarrierFilterSet


class BarrierReportsView(generics.ListCreateAPIView):
    queryset = Barrier.barriers.annotate(team_count=Count("barrier_team")).all()
    serializer_class = BarrierCsvExportSerializer
    filterset_class = BarrierFilterSet
    filter_backends = (DjangoFilterBackend,)

    def post(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).values_list("id")
        barrier_ids = list(map(str, queryset.values_list("id", flat=True)))

        if not barrier_ids:
            return JsonResponse(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "No barriers matching filterset"},
            )

        barrier_report = create_barrier_report(
            user=request.user, barrier_ids=barrier_ids
        )

        return JsonResponse(
            status=status.HTTP_201_CREATED,
            data={"barrier_report_id": barrier_report.id},
        )

    def list(self, request, *args, **kwargs):
        return Response(
            status=status.HTTP_200_OK,
            data=BarrierReportSerializer(
                BarrierReport.objects.filter(user=request.user)
                .order_by("-created_on")
                .values("id", "name", "status", "created_on", "modified_on", "user"),
                many=True,
            ).data,
        )


class BarrierReportDetailView(generics.RetrieveAPIView):
    lookup_field = "pk"
    serializer_class = BarrierReportSerializer
    queryset = BarrierReport.objects.all()

    def check_object_permissions(self, request, obj):
        if obj.user != request.user:
            self.permission_denied(request, message="Unauthorized")


class BarrierReportPresignedUrlView(generics.RetrieveAPIView):
    lookup_field = "pk"
    serializer_class = BarrierReportPresignedUrlSerializer
    queryset = BarrierReport.objects.all()

    def check_object_permissions(self, request, obj):
        if obj.user != request.user:
            self.permission_denied(request, message="Unauthorized")

    def get(self, request, *args, **kwargs):
        barrier_report = self.get_object()
        presigned_url = get_presigned_url(barrier_report)
        return Response(
            status=status.HTTP_200_OK,
            data=BarrierReportPresignedUrlSerializer(
                {"presigned_url": presigned_url}
            ).data,
        )
