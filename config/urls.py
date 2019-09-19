from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from api.metadata.views import MetadataView
from api.ping.views import ping
from api.barriers.views import (
    barrier_count,
    barriers_export,
    BarrierDetail,
    BarrierHibernate,
    BarrierInstanceHistory,
    BarrierList,
    BarriertListExportView,
    BarrierResolveInFull,
    BarrierResolveInPart,
    BarrierOpenInProgress,
    BarrierOpenActionRequired,
    BarrierReportDetail,
    BarrierReportList,
    BarrierReportSubmit,
    BarrierStatusChangeUnknown,
    BarrierStatusHistory,
)
from api.interactions.views import BarrierInteractionList, BarrierIneractionDetail
from api.user.views import who_am_i, UserDetail
from api.core.views import admin_override
from api.dataset.views import BarrierListDataWorkspaceView

from api.assessment.urls import urlpatterns as assessment_urls
from api.collaboration.urls import urlpatterns as team_urls
from api.interactions.urls import urlpatterns as interaction_urls

urlpatterns = [
    path("admin/login/", admin_override, name="override"),
    path("admin/", admin.site.urls),
    path("auth/", include("authbroker_client.urls", namespace="authbroker")),
    path("counts", barrier_count, name="barrier-count"),
    path("ping.xml", ping, name="ping"),
    path("whoami", who_am_i, name="who_am_i"),
    path("users/<uuid:sso_user_id>", UserDetail.as_view(), name="get-user"),
    path("reports", BarrierReportList.as_view(), name="list-reports"),
    path("reports/<uuid:pk>", BarrierReportDetail.as_view(), name="get-report"),
    path(
        "reports/<uuid:pk>/submit", BarrierReportSubmit.as_view(), name="submit-report"
    ),
    path("metadata", MetadataView.as_view(), name="metadata"),
    path("barriers", BarrierList.as_view(), name="list-barriers"),
    path("barriers/export", BarriertListExportView.as_view(), name="barriers-export"),
    path("barriers/dataset", BarrierListDataWorkspaceView.as_view(), name="dataset-barriers"),
    path("barriers/<uuid:pk>", BarrierDetail.as_view(), name="get-barrier"),
    path(
        "barriers/<uuid:pk>/full_history",
        BarrierInstanceHistory.as_view(),
        name="history",
    ),
    path(
        "barriers/<uuid:pk>/history",
        BarrierStatusHistory.as_view(),
        name="status-history",
    ),
    path(
        "barriers/<uuid:pk>/resolve-in-full", BarrierResolveInFull.as_view(), name="resolve-in-full"
    ),
    path(
        "barriers/<uuid:pk>/resolve-in-part", BarrierResolveInPart.as_view(), name="resolve-in-part"
    ),
    path(
        "barriers/<uuid:pk>/hibernate",
        BarrierHibernate.as_view(),
        name="hibernate-barrier",
    ),
    path(
        "barriers/<uuid:pk>/unknown",
        BarrierStatusChangeUnknown.as_view(),
        name="unknown-barrier",
    ),
    path("barriers/<uuid:pk>/open-in-progress", BarrierOpenInProgress.as_view(), name="open-in-progress"),
    path("barriers/<uuid:pk>/open-action_required", BarrierOpenActionRequired.as_view(), name="open-action"),
] + interaction_urls + team_urls + assessment_urls
