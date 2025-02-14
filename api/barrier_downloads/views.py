from django.db.models import Count
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from api.barrier_downloads import service
from api.barrier_downloads.models import BarrierDownload
from api.barrier_downloads.serializers import (
    BarrierDownloadPatchSerializer,
    BarrierDownloadPresignedUrlSerializer,
    BarrierDownloadSerializer,
)
from api.barriers.models import Barrier, BarrierFilterSet


class BarrierDownloadFilterBackend(DjangoFilterBackend):
    """
    We want to override DjangoFilterBackend to read the filters
    from request.data instead of request.query_params
    """

    def get_filterset_kwargs(self, request, queryset, view):
        return {
            "data": request.data,
            "queryset": queryset,
            "request": request,
        }


class BarrierDownloadsView(generics.ListCreateAPIView):
    queryset = (
        Barrier.barriers.annotate(
            team_count=Count("barrier_team"),
        )
        .all()
        .select_related(
            "wto_profile__committee_notified",
            "wto_profile__committee_raised_in",
            "priority",
            "public_barrier",
        )
        .prefetch_related(
            "economic_assessments",
            "resolvability_assessments",
            "strategic_assessments",
            "tags",
            "barrier_commodities",
            "public_barrier__notes",
            "organisations",
            "policy_teams",
        )
    )
    serializer_class = BarrierDownloadSerializer
    filterset_class = BarrierFilterSet
    filter_backends = (BarrierDownloadFilterBackend,)
    pagination_class = PageNumberPagination

    def post(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).values_list("id")
        barrier_ids = list(map(str, queryset.values_list("id", flat=True)))
        filters = self.request.data.get("filters", {})

        if not barrier_ids:
            return JsonResponse(
                status=status.HTTP_400_BAD_REQUEST,
                data={"error": "No barriers matching filterset"},
            )

        barrier_download = service.create_barrier_download(
            user=request.user, filters=filters, barrier_ids=barrier_ids
        )

        return JsonResponse(
            status=status.HTTP_201_CREATED,
            data={"id": barrier_download.id},
        )

    def list(self, request, *args, **kwargs):

        queryset = (
            BarrierDownload.objects.filter(created_by=request.user)
            .order_by("-created_on")
            .values(
                "id",
                "name",
                "status",
                "created_on",
                "count",
                "filters",
                "modified_on",
                "created_by",
            )
        )
        page = self.paginate_queryset(queryset)

        serializer = self.serializer_class(
            page,
            many=True,
        )
        return self.get_paginated_response(serializer.data)


class BarrierDownloadDetailView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = "pk"
    serializer_class = BarrierDownloadSerializer
    queryset = BarrierDownload.objects.all()

    def check_object_permissions(self, request, obj):
        if obj.created_by != request.user:
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

    def delete(self, request, *args, **kwargs):
        service.delete_barrier_download(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)


class BarrierDownloadPresignedUrlView(generics.RetrieveAPIView):
    lookup_field = "pk"
    serializer_class = BarrierDownloadPresignedUrlSerializer
    queryset = BarrierDownload.objects.all()

    def check_object_permissions(self, request, obj):
        if obj.created_by != request.user:
            self.permission_denied(request, message="Unauthorized")

    def get(self, request, *args, **kwargs):
        barrier_download = self.get_object()
        presigned_url = service.get_presigned_url(barrier_download)
        return Response(
            status=status.HTTP_200_OK,
            data=BarrierDownloadPresignedUrlSerializer(
                {"presigned_url": presigned_url}
            ).data,
        )
