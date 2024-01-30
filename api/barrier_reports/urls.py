from django.urls import path
from rest_framework.routers import DefaultRouter

from api.barrier_reports.views import BarrierReportsView, BarrierReportDetailView, BarrierReportPresignedUrlView

router = DefaultRouter(trailing_slash=False)


urlpatterns = router.urls + [
    path(
        "barrier-reports",
        BarrierReportsView.as_view(),
        name="get-barrier-reports",
    ),
    path("barrier-reports/<uuid:pk>", BarrierReportDetailView.as_view(), name="get-barrier-report"),
    path(
        "barrier-reports/<uuid:pk>/presigned-url",
        BarrierReportPresignedUrlView.as_view(),
        name="get-barrier-report"
    ),
]
