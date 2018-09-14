from django.contrib import admin
from django.urls import path, include

from api.metadata.views import MetadataView
from api.ping.views import ping
from api.barriers.views import (
    barrier_count,
    BarrierList,
    BarrierDetail,
    BarrierInstanceInteraction,
    BarrierInstanceContributor,
    BarrierResolve,
    BarrierHibernate,
    BarrierOpen,
    BarrierStatusList,
)
from api.reports.views import (
    ReportDetail,
    ReportList,
    ReportStagesList,
    ReportStageUpdate,
    ReportSubmit,
)
from api.user.views import who_am_i
from api.core.views import admin_override

urlpatterns = [
    path("admin/login/", admin_override, name="override"),
    path("admin/", admin.site.urls),
    path('auth/', include('authbroker_client.urls', namespace='authbroker')),
    path("ping.xml", ping, name="ping"),
    path("whoami", who_am_i, name="who_am_i"),
    path("reports", ReportList.as_view(), {"status": None}, name="list-reports"),
    path("reports/unfinished", ReportList.as_view(), {"status": 0}),
    path("reports/awaiting_screening", ReportList.as_view(), {"status": 1}),
    path("reports/accepted", ReportList.as_view(), {"status": 2}),
    path("reports/rejected", ReportList.as_view(), {"status": 3}),
    path("reports/archived", ReportList.as_view(), {"status": 4}),
    path("reports/<int:pk>", ReportDetail.as_view()),
    path("reports/<int:report_pk>/stages", ReportStagesList.as_view()),
    path("reports/<int:pk>/submit", ReportSubmit.as_view()),
    path("reports/<int:report_pk>/stages/<int:pk>", ReportStageUpdate.as_view()),

    path("metadata", MetadataView.as_view()),

    path("barriers", BarrierList.as_view(), name="list-barriers"),
    path("barriers/count", barrier_count),
    path("barriers/<uuid:pk>", BarrierDetail.as_view()),
    path("barriers/<uuid:barrier_pk>/contributors", BarrierInstanceContributor.as_view()),
    path("barriers/<uuid:barrier_pk>/interactions", BarrierInstanceInteraction.as_view()),
    path("barriers/<uuid:pk>/resolve", BarrierResolve.as_view()),
    path("barriers/<uuid:pk>/hibernate", BarrierHibernate.as_view()),
    path("barriers/<uuid:pk>/open", BarrierOpen.as_view()),
    path("barriers/<uuid:barrier_pk>/statuses", BarrierStatusList.as_view()),
]
