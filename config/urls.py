from django.contrib import admin
from django.urls import path, include

from api.metadata.views import MetadataView
from api.ping.views import ping
from api.barriers.views import (
    barrier_count,
    BarrierList,
    BarrierDetail,
    BarrierInstanceCompany,
    BarrierInstanceInteraction,
    BarrierInstanceContributor,
    BarrierResolve,
    BarrierHibernate,
    BarrierOpen,
    BarrierReportList,
    BarrierReportDetail,
    BarrierReportSubmit,
    BarrierInstanceHistory
)
from api.user.views import who_am_i
from api.core.views import admin_override

urlpatterns = [
    path("admin/login/", admin_override, name="override"),
    path("admin/", admin.site.urls),
    path('auth/', include('authbroker_client.urls', namespace='authbroker')),
    path("ping.xml", ping, name="ping"),
    path("whoami", who_am_i, name="who_am_i"),

    path("reports", BarrierReportList.as_view(), name="list-reports"),
    path("reports/<uuid:pk>", BarrierReportDetail.as_view(), name="get-report"),
    path("reports/<uuid:pk>/submit", BarrierReportSubmit.as_view(), name="submit-report"),

    path("metadata", MetadataView.as_view(), name="metadata"),

    path("barriers", BarrierList.as_view(), name="list-barriers"),
    path("barriers/count", barrier_count),
    path("barriers/<uuid:pk>", BarrierDetail.as_view()),
    path("barriers/<uuid:barrier_pk>/companies", BarrierInstanceCompany.as_view()),
    path("barriers/<uuid:barrier_pk>/contributors", BarrierInstanceContributor.as_view()),
    path("barriers/<uuid:barrier_pk>/interactions", BarrierInstanceInteraction.as_view()),
    path("barriers/<uuid:barrier_pk>/history", BarrierInstanceHistory.as_view()),
    path("barriers/<uuid:pk>/resolve", BarrierResolve.as_view()),
    path("barriers/<uuid:pk>/hibernate", BarrierHibernate.as_view()),
    path("barriers/<uuid:pk>/open", BarrierOpen.as_view()),
]
