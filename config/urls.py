from django.contrib import admin
from django.urls import path, include

from api.metadata.views import MetadataView
from api.ping.views import ping
from api.barriers.views import (
    barrier_count,
    BarrierList,
    BarrierDetail,
    BarrierInstanceContributor,
    BarrierResolve,
    BarrierHibernate,
    BarrierOpen,
    BarrierReportList,
    BarrierReportDetail,
    BarrierReportSubmit,
    BarrierInstanceHistory,
    BarrierStatuseHistory,
)
from api.interactions.views import BarrierInteractionList, BarrierIneractionDetail
from api.user.views import who_am_i
from api.core.views import admin_override

from api.interactions.urls import urlpatterns

urlpatterns = [
    path("admin/login/", admin_override, name="override"),
    path("admin/", admin.site.urls),
    path("auth/", include("authbroker_client.urls", namespace="authbroker")),
    path("counts", barrier_count, name="barrier-count"),
    path("ping.xml", ping, name="ping"),
    path("whoami", who_am_i, name="who_am_i"),
    path("reports", BarrierReportList.as_view(), name="list-reports"),
    path("reports/<uuid:pk>", BarrierReportDetail.as_view(), name="get-report"),
    path(
        "reports/<uuid:pk>/submit", BarrierReportSubmit.as_view(), name="submit-report"
    ),
    path("metadata", MetadataView.as_view(), name="metadata"),
    path("barriers", BarrierList.as_view(), name="list-barriers"),
    path("barriers/<uuid:pk>", BarrierDetail.as_view(), name="get-barrier"),
    path("barriers/<uuid:pk>/contributors", BarrierInstanceContributor.as_view()),
    path(
        "barriers/<uuid:pk>/history", BarrierInstanceHistory.as_view(), name="history"
    ),
    path(
        "barriers/<uuid:pk>/status_history",
        BarrierStatuseHistory.as_view(),
        name="status-history",
    ),
    path(
        "barriers/<uuid:pk>/resolve", BarrierResolve.as_view(), name="resolve-barrier"
    ),
    path(
        "barriers/<uuid:pk>/hibernate",
        BarrierHibernate.as_view(),
        name="hibernate-barrier",
    ),
    path("barriers/<uuid:pk>/open", BarrierOpen.as_view(), name="open-barrier"),
] + urlpatterns
