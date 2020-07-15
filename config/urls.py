from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path

from api.metadata.views import MetadataView
from api.barriers.views import (
    barrier_count,
    BarrierActivity,
    BarrierDetail,
    BarrierHibernate,
    BarrierFullHistory,
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
from api.user.views import who_am_i, UserDetail
from api.core.views import admin_override
from api.dataset.views import BarrierListDataWorkspaceView
from api.hs_codes.views import HSCodeDetail, HSCodeList

from api.assessment.urls import urlpatterns as assessment_urls
from api.collaboration.urls import urlpatterns as team_urls
from api.interactions.urls import urlpatterns as interaction_urls
from api.user.urls import urlpatterns as user_urls

urlpatterns = []

# Allow regular login to admin panel for local development
if settings.DJANGO_ENV != 'local':
    urlpatterns += [
        path("admin/login/", admin_override, name="override"),
    ]

urlpatterns += [
    path("admin/", admin.site.urls),
    path("auth/", include("authbroker_client.urls", namespace="authbroker")),
    path("counts", barrier_count, name="barrier-count"),
    path("", include("api.healthcheck.urls", namespace="healthcheck")),
    path("whoami", who_am_i, name="who_am_i"),
    path("users/<int:pk>", UserDetail.as_view(), name="get-user"),
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
    re_path("barriers/(?P<code>[A-Z]-[0-9]{2}-[A-Z0-9]{3})", BarrierDetail.as_view(), name="barrier_detail_code"),
    path(
        "barriers/<uuid:pk>/full_history",
        BarrierFullHistory.as_view(),
        name="history",
    ),
    path(
        "barriers/<uuid:pk>/history",
        BarrierStatusHistory.as_view(),
        name="status-history",
    ),
    path("barriers/<uuid:pk>/activity", BarrierActivity.as_view(), name="activity"),
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
    path("hs-codes", HSCodeList.as_view(), name="hs-code-list"),
    path("hs-codes/<str:code>", HSCodeDetail.as_view(), name="hs-code-detail"),

] + interaction_urls + team_urls + assessment_urls + user_urls
