from django.urls import path

from api.assessment.views import (
    BarrierAssessmentDetail,
)

urlpatterns = [
    path(
        "barriers/<uuid:pk>/assessment",
        BarrierAssessmentDetail.as_view(),
        name="get-assessment",
    ),
]
