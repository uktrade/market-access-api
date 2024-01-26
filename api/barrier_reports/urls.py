from django.urls import path
from rest_framework.routers import DefaultRouter

from api.barrier_reports.views import BarrierListS3EmailFile

router = DefaultRouter(trailing_slash=False)


def view(): pass


urlpatterns = router.urls + [
    # path("barrier-reports", view, name="barrier-reports"),
    path(
        "barrier-reports",
        BarrierListS3EmailFile.as_view(),
        name="barriers-reports",
    ),
    path(
        "barriers/s3-email",
        BarrierListS3EmailFile.as_view(),
        name="barriers-s3-email",
    ),
]
