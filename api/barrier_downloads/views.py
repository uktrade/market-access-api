from django.db.models import Count
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.response import Response

from api.barrier_downloads.models import BarrierDownload
from api.barrier_downloads.serializers import (
    BarrierCsvExportSerializer,
    BarrierDownloadPatchSerializer,
    BarrierDownloadPresignedUrlSerializer,
    BarrierDownloadSerializer,
)
from api.barrier_downloads.service import create_barrier_download, get_presigned_url
from api.barriers.models import Barrier, BarrierFilterSet


class BarrierDownloadsView(generics.ListCreateAPIView):
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

        barrier_download = create_barrier_download(
            user=request.user, barrier_ids=barrier_ids
        )

        return JsonResponse(
            status=status.HTTP_201_CREATED,
            data={"barrier_download_id": barrier_download.id},
        )

    def list(self, request, *args, **kwargs):
        return Response(
            status=status.HTTP_200_OK,
            data=BarrierDownloadSerializer(
                BarrierDownload.objects.filter(user=request.user)
                .order_by("-created_on")
                .values("id", "name", "status", "created_on", "modified_on", "user"),
                many=True,
            ).data,
        )


class BarrierDownloadDetailView(generics.RetrieveUpdateAPIView):
    lookup_field = "pk"
    serializer_class = BarrierDownloadSerializer
    queryset = BarrierDownload.objects.all()

    def check_object_permissions(self, request, obj):
        if obj.user != request.user:
            self.permission_denied(request, message="Unauthorized")

    def patch(self, request, *args, **kwargs):
        """Only update name"""
        obj = self.get_object()
        serializer = BarrierDownloadPatchSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            obj.name = serializer.data["name"]
            obj.save()
        return Response(
            status=status.HTTP_200_OK, data=BarrierDownloadSerializer(obj).data
        )


class BarrierDownloadPresignedUrlView(generics.RetrieveAPIView):
    lookup_field = "pk"
    serializer_class = BarrierDownloadPresignedUrlSerializer
    queryset = BarrierDownload.objects.all()

    def check_object_permissions(self, request, obj):
        if obj.user != request.user:
            self.permission_denied(request, message="Unauthorized")

    def get(self, request, *args, **kwargs):
        barrier_download = self.get_object()
        presigned_url = get_presigned_url(barrier_download)
        return Response(
            status=status.HTTP_200_OK,
            data=BarrierDownloadPresignedUrlSerializer(
                {"presigned_url": presigned_url}
            ).data,
        )
