from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

from api.metadata.constants import REPORT_STATUS
from api.metadata.views import MetadataView
from api.ping.views import ping
from api.reports.views import (ReportDetail, ReportList, ReportStagesList,
                               ReportStageUpdate, ReportSubmit)
from api.user.views import who_am_i

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    path('ping.xml', ping, name='ping'),
    path('whoami/', who_am_i, name='who_am_i'),
    path('reports/', ReportList.as_view(), {'status': None}, name='list-reports'),
    path('reports/unfinished/', ReportList.as_view(), {'status': 0}),
    path('reports/awaiting_screening/', ReportList.as_view(), {'status': 1}),
    path('reports/<int:pk>/', ReportDetail.as_view()),
    path('reports/<int:report_pk>/stages/', ReportStagesList.as_view()),
    path('reports/<int:pk>/submit/', ReportSubmit.as_view()),
    path('reports/<int:report_pk>/stages/<int:pk>/', ReportStageUpdate.as_view()),
    path('metadata/', MetadataView.as_view()),
]
