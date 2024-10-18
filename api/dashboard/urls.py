from django.urls import path
from rest_framework.routers import DefaultRouter

from api.dashboard.views import BarrierDashboardSummary, UserTasksView

app_name = "dashboard"

router = DefaultRouter(trailing_slash=False)


urlpatterns = router.urls + [
    path(
        "dashboard-summary", BarrierDashboardSummary.as_view(), name="barrier-summary"
    ),
    path(
        "dashboard-tasks",
        UserTasksView.as_view(),
        name="get-dashboard-tasks",
    ),
]
