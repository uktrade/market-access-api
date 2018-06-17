from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from api.metadata.constants import REPORT_STATUS
from api.ping.views import ping
from api.user.views import who_am_i
from api.barriers.views import (
    BarrierList,
    BarrierDetail,
    BarrierReportStagesList,
    BarrierReportStageUpdate
)
from api.metadata.views import MetadataView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    path('ping.xml', ping, name='ping'),
    path('whoami/', who_am_i, name='who_am_i'),
    path('barriers/', BarrierList.as_view(), {'status': None}),
    path('barriers/unfinished/', BarrierList.as_view(), {'status': 0}),
    path('barriers/screening/', BarrierList.as_view(), {'status': 1}),
    path('barriers/<int:pk>/', BarrierDetail.as_view()),
    path('barriers/<int:barrier_pk>/stages/', BarrierReportStagesList.as_view()),
    path('barriers/<int:barrier_pk>/stages/<int:pk>/', BarrierReportStageUpdate.as_view()),
    path('metadata/', MetadataView.as_view()),
]
