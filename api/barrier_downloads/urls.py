from django.urls import path
from rest_framework.routers import DefaultRouter

from api.barrier_downloads.views import (
    BarrierDownloadDetailView,
    BarrierDownloadPresignedUrlView,
    BarrierDownloadsView,
)

router = DefaultRouter(trailing_slash=False)


urlpatterns = router.urls + [
    path(
        "barrier-downloads",
        BarrierDownloadsView.as_view(),
        name="barrier-downloads",
    ),
    path(
        "barrier-downloads/<uuid:pk>",
        BarrierDownloadDetailView.as_view(),
        name="barrier-download",
    ),
    path(
        "barrier-downloads/<uuid:pk>/presigned-url",
        BarrierDownloadPresignedUrlView.as_view(),
        name="get-barrier-download-presigned-url",
    ),
]
